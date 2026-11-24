"""The published files (GitHub Pages):

- `<cc>.xml.gz`: XMLTV guide of a country (its registry channels), whole window;
- `all.xml.gz`: every channel;
- `<channel id>/<YYYY-MM-DD>.json`: programmes of one channel for one UTC day;
- `index.json`: what was published (countries, channels, days, sources, counts)."""
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


def xmltv(channels: list[dict], programmes: dict[str, list[Programme]]) -> bytes:
    tv = ET.Element('tv', {'generator-info-name': 'worldwide-tv-epg'})
    for c in channels:
        ch = ET.SubElement(tv, 'channel', {'id': c['id']})
        ET.SubElement(ch, 'display-name').text = c.get('name', c['id'])
        logo = c.get('logo_white') or c.get('logo')
        if logo:
            ET.SubElement(ch, 'icon', {'src': logo})
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


def write(out: Path, registry: Registry, days: dict[date, dict[str, list[Programme]]], chosen: dict[str, str],
          generated: datetime) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    whole: dict[str, list[Programme]] = defaultdict(list)
    for day, per_channel in sorted(days.items()):
        for cid, progs in per_channel.items():
            if cid not in registry.channels or not progs:
                continue
            progs = sorted(progs, key=lambda p: p.start)
            whole[cid] += progs
            folder = out / cid
            folder.mkdir(exist_ok=True)
            (folder / f'{day.isoformat()}.json').write_text(json.dumps(
                {'channel': cid, 'date': day.isoformat(), 'programmes': [p.to_dict() for p in progs]},
                ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    by_country: dict[str, list[dict]] = defaultdict(list)
    for cid in sorted(whole):
        c = registry.channels[cid]
        by_country[c.get('country', '')].append(c)
    for cc, chans in sorted(by_country.items()):
        (out / f'{cc}.xml.gz').write_bytes(gzip.compress(xmltv(chans, whole), mtime=0))
    every = [c for cc in sorted(by_country) for c in by_country[cc]]
    (out / 'all.xml.gz').write_bytes(gzip.compress(xmltv(every, whole), mtime=0))
    index = {
        'generated': generated.astimezone(UTC).isoformat().replace('+00:00', 'Z'),
        'days': [d.isoformat() for d in sorted(days)],
        'countries': {cc: {'url': f'{config.PUBLIC_URL}/{cc}.xml.gz', 'channels': len(chans)}
                      for cc, chans in sorted(by_country.items())},
        'channels': {cid: {'country': registry.channels[cid].get('country', ''), 'source': chosen.get(cid, 'archive'),
                           'days': sorted({p.start.date().isoformat() for p in whole[cid]})} for cid in sorted(whole)},
    }
    (out / 'index.json').write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding='utf-8')
    return index


def size(folder: Path) -> int:
    return sum(f.stat().st_size for f in folder.rglob('*') if f.is_file())
