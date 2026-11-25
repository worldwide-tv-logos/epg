"""XMLTV writer: a guide of registry channels, for IPTV players."""
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

from worldwide_tv_epg.model import Programme


def logo(channel: dict) -> str:
    """The logo given with a channel: the version for dark screens when the registry has one."""
    return channel.get('logo_white') or channel.get('logo') or ''


def _xmltv_time(when: datetime) -> str:
    return when.astimezone(UTC).strftime('%Y%m%d%H%M%S +0000')


def xmltv(channels: list[dict], programmes: dict[str, list[Programme]]) -> bytes:
    tv = ET.Element('tv', {'generator-info-name': 'worldwide-tv-epg'})
    for c in channels:
        ch = ET.SubElement(tv, 'channel', {'id': c['id']})
        ET.SubElement(ch, 'display-name').text = c.get('name', c['id'])
        if logo(c):
            ET.SubElement(ch, 'icon', {'src': logo(c)})
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
