"""Command line: `uv run epg <command>`.

  sources            list the sources of sources.toml
  run                one pass: download, map, merge, archive, publish (see docs/architecture.md)
  check              checks on a published folder: freshness, coverage, size
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from worldwide_tv_epg import config, merge, publish, registry, sources, window, xmltv

ROOT = Path(__file__).resolve().parent.parent


def _download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': config.USER_AGENT})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return resp.read()


def cmd_sources(args) -> int:
    for s in sources.load(args.sources):
        print(f'{s.id:16} {",".join(s.countries):12} {s.url}')
    return 0


def cmd_run(args) -> int:
    now = datetime.now(UTC)
    today = now.date()
    days = window.days(today)
    srcs = sources.load(args.sources)
    reg = registry.load(args.registry)
    print(f'registry: {len(reg.channels)} channels, {len(reg.by_guide)} guide IDs mapped')
    guides, status = [], {}
    for i, s in enumerate(srcs):
        if i:
            time.sleep(config.PAUSE)
        try:
            guide = xmltv.parse(_download(s.url), s.language)
        except Exception as exc:   # a source that fails is skipped: its channels keep their archived programmes
            status[s.id] = {'ok': False, 'error': str(exc)[:200]}
            print(f'{s.id}: FAILED ({exc})')
            continue
        guides.append((s, guide))
        status[s.id] = {'ok': True, 'channels': len(guide.programmes)}
        print(f'{s.id}: {len(guide.programmes)} channels')
    fresh, chosen = merge.merge(guides, reg, now)
    print(f'merged: {len(fresh)} registry channels with a guide')

    archive = Path(args.archive)
    archive.mkdir(parents=True, exist_ok=True)
    archived = {}
    for day in days:
        f = archive / window.archive_name(day)
        if f.is_file():
            archived[day] = window.read_archive(f)
    combined = window.combine(window.by_day(fresh), archived, days)
    for day, per_channel in combined.items():
        window.write_archive(archive / window.archive_name(day), per_channel)
    for name in window.expired([f.name for f in archive.glob('*.json.gz')], today):
        (archive / name).unlink()
        print(f'archive removed: {name}')

    index = publish.write(Path(args.out), reg, combined, chosen, now)
    (Path(args.out) / 'status.json').write_text(json.dumps({'generated': index['generated'], 'sources': status},
                                                           indent=1), encoding='utf-8')
    print(f'published: {len(index["channels"])} channels, {len(index["countries"])} countries, '
          f'{publish.size(Path(args.out)) / 1e6:.0f} MB')
    return 0


def cmd_check(args) -> int:
    out = Path(args.out)
    index = json.loads((out / 'index.json').read_text(encoding='utf-8'))
    status = json.loads((out / 'status.json').read_text(encoding='utf-8'))
    today = datetime.now(UTC).date().isoformat()
    lines, failed = ['## Guides', '', '| Country | Channels | With today |', '|---|---|---|'], False
    for cc in index['countries']:
        chans = [c for c in index['channels'].values() if c['country'] == cc]
        lines.append(f'| {cc} | {len(chans)} | {sum(today in c["days"] for c in chans)} |')
    with_today = sum(today in c['days'] for c in index['channels'].values())
    size = publish.size(out)
    lines += ['', f'Channels with programmes today: **{with_today}**', f'Published size: **{size / 1e6:.0f} MB**', '',
              '| Source | State |', '|---|---|']
    lines += [f'| {sid} | {"ok, " + str(s["channels"]) + " channels" if s["ok"] else "FAILED: " + s["error"]} |'
              for sid, s in status['sources'].items()]
    if not with_today:
        failed = True
        lines.append('\n**No channel has programmes today.**')
    if size > config.SIZE_ALERT:
        failed = True
        lines.append(f'\n**Published size over {config.SIZE_ALERT / 1e6:.0f} MB (GitHub Pages limit: 1 GB).**')
    report = '\n'.join(lines) + '\n'
    print(report)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as fh:
            fh.write(report)
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog='epg', description='TV guides keyed by worldwide-tv-logos channel IDs')
    p.add_argument('--sources', default=str(ROOT / 'sources.toml'))
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('sources', help='list the sources').set_defaults(func=cmd_sources)
    r = sub.add_parser('run', help='one pass: download, map, merge, archive, publish')
    r.add_argument('--registry', default=config.REGISTRY_URL)
    r.add_argument('--archive', default='archive', help='daily archives (synced with the release by the workflow)')
    r.add_argument('--out', default='public', help='folder published on GitHub Pages')
    r.set_defaults(func=cmd_run)
    c = sub.add_parser('check', help='freshness, coverage and size of a published folder')
    c.add_argument('--out', default='public')
    c.set_defaults(func=cmd_check)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
