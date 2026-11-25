"""The published files: one XMLTV guide and one JSON guide per country and per UTC day.

GitHub Pages (the window, 7 days before today to 7 days after):
- `<cc>/<YYYY-MM-DD>.xml.gz`: XMLTV guide of a country for one day, for IPTV players;
- `<cc>/<YYYY-MM-DD>.json`: the same guide in JSON, for applications;
- `index.json`: countries, days and channels published, and the source chosen for each channel;
- `status.json`: state of each source at the last run (written by the command line).

Releases (one per UTC day, tag `<YYYY-MM-DD>`, kept 30 days by the workflow): `<cc>.xml.gz` and `<cc>.json.gz`, the same
guides; they are also the archives read back for the past days of the window (pipeline/window.py)."""
import gzip
import json
from collections import defaultdict
from datetime import UTC, date, datetime
from pathlib import Path

from worldwide_tv_epg import config
from worldwide_tv_epg.model import Programme
from worldwide_tv_epg.pipeline.mapping import Registry
from worldwide_tv_epg.publish.guide_json import guide_json
from worldwide_tv_epg.publish.xmltv import xmltv


def by_country(registry: Registry, per_channel: dict[str, list[Programme]]) -> dict[str, list[dict]]:
    """Registry channels with programmes, by country (sorted by name), unknown channels left out."""
    out: dict[str, list[dict]] = defaultdict(list)
    for cid, progs in per_channel.items():
        c = registry.channels.get(cid)
        if c and progs and c.get('country'):
            out[c['country']].append(c)
    return {cc: sorted(chans, key=lambda c: (c.get('name', '').casefold(), c['id']))
            for cc, chans in sorted(out.items())}


def write(out: Path, releases: Path, registry: Registry, days: dict[date, dict[str, list[Programme]]],
          chosen: dict[str, str], generated: datetime) -> dict:
    """Writes the site in `out` and the release files in `releases/<YYYY-MM-DD>/`; returns the index."""
    countries: dict[str, dict] = defaultdict(lambda: {'days': []})
    channels: dict[str, dict] = {}
    for day, per_channel in sorted(days.items()):
        progs = {cid: sorted(p, key=lambda p: p.start) for cid, p in per_channel.items()}
        for cc, chans in by_country(registry, progs).items():
            xml = gzip.compress(xmltv(chans, progs), mtime=0)
            js = guide_json(cc, day, chans, progs)
            site, rel = out / cc, releases / day.isoformat()
            site.mkdir(parents=True, exist_ok=True)
            rel.mkdir(parents=True, exist_ok=True)
            (site / f'{day.isoformat()}.xml.gz').write_bytes(xml)
            (site / f'{day.isoformat()}.json').write_bytes(js)
            (rel / f'{cc}.xml.gz').write_bytes(xml)
            (rel / f'{cc}.json.gz').write_bytes(gzip.compress(js, mtime=0))
            countries[cc]['days'].append(day.isoformat())
            for c in chans:
                ch = channels.setdefault(c['id'], {'country': cc, 'name': c.get('name', c['id']),
                                                   'source': chosen.get(c['id'], 'archive'), 'days': []})
                ch['days'].append(day.isoformat())
    for cc in countries:
        countries[cc]['channels'] = sum(c['country'] == cc for c in channels.values())
    index = {
        'generated': generated.astimezone(UTC).isoformat().replace('+00:00', 'Z'),
        'files': {'xmltv': f'{config.PUBLIC_URL}/{{country}}/{{date}}.xml.gz',
                  'json': f'{config.PUBLIC_URL}/{{country}}/{{date}}.json'},
        'days': [d.isoformat() for d in sorted(days)],
        'countries': dict(sorted(countries.items())),
        'channels': dict(sorted(channels.items())),
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / 'index.json').write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding='utf-8')
    return index


def size(folder: Path) -> int:
    return sum(f.stat().st_size for f in folder.rglob('*') if f.is_file())
