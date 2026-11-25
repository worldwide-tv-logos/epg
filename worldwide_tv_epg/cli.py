"""Command line: `uv run epg <command>`.

  sources            list the feeds of sources/, in the order they are used
  run                one pass: download, map, merge, publish (see docs/architecture.md)
  check              checks on a published folder: freshness, coverage, size, state of each feed
"""
import argparse
import json
import os
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from worldwide_tv_epg import checks, config, sources
from worldwide_tv_epg.net import Downloader
from worldwide_tv_epg.pipeline import mapping, merge, window
from worldwide_tv_epg.publish import files

ROOT = Path(__file__).resolve().parent.parent


def cmd_sources(args) -> int:
    for f in sources.load(args.sources):
        print(f'{f.id:16} {f.provider:12} rank {f.rank} {f.role:8} {",".join(f.countries):12} {f.url}')
    return 0


def cmd_run(args) -> int:
    now = datetime.now(UTC)
    days = window.days(now.date())
    feeds = sources.load(args.sources)
    downloader = Downloader(Path(args.cache) if args.cache else None)
    reg = mapping.load(downloader, args.registry)
    print(f'registry: {len(reg.channels)} channels, {len(reg.by_guide)} guide IDs mapped')
    guides, status = [], {}
    for feed in feeds:
        try:
            guide = sources.read(feed, downloader.get(f'feeds/{feed.id}', feed.url))
        except Exception as exc:    # a feed that fails (download, unreadable file) is skipped and reported:
            status[feed.id] = {'ok': False, 'provider': feed.provider, 'error': str(exc)[:200]}   # its channels
            print(f'{feed.id}: FAILED ({exc})')                                                  # keep their archives
            continue
        guides.append((feed, guide))
        status[feed.id] = {'ok': True, 'provider': feed.provider, 'channels': len(guide.programmes)}
        print(f'{feed.id}: {len(guide.programmes)} channels')
    merged = merge.merge(guides, reg, now)
    chosen = Counter(merged.chosen.values())
    for fid, n in merged.mapped.items():
        status[fid].update(mapped=n, chosen=chosen[fid])
    print(f'merged: {len(merged.programmes)} registry channels with a guide')

    archive = Path(args.archive)
    archived = {day: window.read_day(archive / day.isoformat()) for day in days if (archive / day.isoformat()).is_dir()}
    combined = window.combine(window.by_day(merged.programmes), archived, days)

    index = files.write(Path(args.out), Path(args.releases), reg, combined, merged.chosen, now)
    (Path(args.out) / 'status.json').write_text(json.dumps({'generated': index['generated'], 'sources': status},
                                                           indent=1), encoding='utf-8')
    print(f'published: {len(index["channels"])} channels, {len(index["countries"])} countries, '
          f'{files.size(Path(args.out)) / 1e6:.0f} MB')
    return 0


def cmd_check(args) -> int:
    report, failed = checks.check(Path(args.out))
    print(report)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as fh:
            fh.write(report)
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog='epg', description='TV guides keyed by worldwide-tv-logos channel IDs')
    p.add_argument('--sources', default=str(ROOT / 'sources'), help='folder of the provider files')
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('sources', help='list the feeds').set_defaults(func=cmd_sources)
    r = sub.add_parser('run', help='one pass: download, map, merge, publish')
    r.add_argument('--registry', default=config.REGISTRY_URL)
    r.add_argument('--archive', default='archive', help='past days: the daily releases, downloaded by the workflow')
    r.add_argument('--releases', default='releases', help='files of the daily releases, uploaded by the workflow')
    r.add_argument('--out', default='public', help='folder published on GitHub Pages')
    r.add_argument('--cache', help='folder of downloaded files: reused when present (replay), saved otherwise')
    r.set_defaults(func=cmd_run)
    c = sub.add_parser('check', help='freshness, coverage, size and feeds of a published folder')
    c.add_argument('--out', default='public')
    c.set_defaults(func=cmd_check)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
