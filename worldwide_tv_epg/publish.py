"""The published files: one XMLTV guide and one JSON guide per country and per UTC day.

GitHub Pages (the window, 7 days before today to 7 days after):
- `<cc>/<YYYY-MM-DD>.xml.gz`: XMLTV guide of a country for one day, for IPTV players;
- `<cc>/<YYYY-MM-DD>.json`: the same guide in JSON, for applications;
- `index.json`: countries, days and channels published, and the source chosen for each channel;
- `status.json`: state of each source at the last run (written by the command line).

Releases (one per UTC day, tag `<YYYY-MM-DD>`, kept 30 days by the workflow): `<cc>.xml.gz` and `<cc>.json.gz`, the same
guides; they are also the archives read back for the past days of the window (window.py)."""
import gzip
import json
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import UTC, date, datetime
from pathlib import Path

from worldwide_tv_epg import config
from worldwide_tv_epg.registry import Registry
from worldwide_tv_epg.xmltv import Programme


def _xmltv_time(when: datetime) -> str:
    return when.astimezone(UTC).strftime('%Y%m%d%H%M%S +0000')


def _logo(channel: dict) -> str:
    return channel.get('logo_white') or channel.get('logo') or ''


def xmltv(channels: list[dict], programmes: dict[str, list[Programme]]) -> bytes:
    tv = ET.Element('tv', {'generator-info-name': 'worldwide-tv-epg'})
    for c in channels:
        ch = ET.SubElement(tv, 'channel', {'id': c['id']})
        ET.SubElement(ch, 'display-name').text = c.get('name', c['id'])
        if _logo(c):
            ET.SubElement(ch, 'icon', {'src': _logo(c)})
    for c in channels:
        for p in programmes.get(c['id'], []):
            attrs = {'start': _xmltv_time(p.start), 'channel': c['id']}
            if p.stop:
                attrs['stop'] = _xmltv_time(p.stop)
            el = ET.SubElement(tv, 'programme', attrs)
            ET.SubElement(el, 'title').text = p.title
            if p.subtitle:
                ET.SubElement(el, 'sub-title').text = p.subtitle
            if p.desc:
                ET.SubElement(el, 'desc').text = p.desc
            for cat in p.categories:
                ET.SubElement(el, 'category').text = cat
            if p.episode:
                ET.SubElement(el, 'episode-num', {'system': 'onscreen'}).text = p.episode
            if p.icon:
                ET.SubElement(el, 'icon', {'src': p.icon})
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(tv, encoding='utf-8')


def guide_json(country: str, day: date, channels: list[dict], programmes: dict[str, list[Programme]]) -> bytes:
    data = {'country': country, 'date': day.isoformat(), 'channels': [
        {'id': c['id'], 'name': c.get('name', c['id']), **({'logo': _logo(c)} if _logo(c) else {}),
         'programmes': [p.to_dict() for p in programmes[c['id']]]} for c in channels]}
    return json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


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
