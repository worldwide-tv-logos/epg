"""Reader of XMLTV files (plain, gzip or xz), the format of most public guide sources."""
import gzip
import lzma
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta, timezone
from io import BytesIO

from worldwide_tv_epg.model import Guide, Programme


def decompress(raw: bytes) -> bytes:
    if raw[:2] == b'\x1f\x8b':
        return gzip.decompress(raw)
    if raw[:6] == b'\xfd7zXZ\x00':
        return lzma.decompress(raw)
    return raw


def parse_time(value: str) -> datetime | None:
    """XMLTV time ("20261124193000 +0100"), returned in UTC; None when unreadable."""
    value = (value or '').strip()
    digits = value.split(' ')[0]
    if len(digits) < 8 or not digits.isdigit():     # XMLTV allows truncated times ("2026112421")
        return None
    try:
        when = datetime.strptime(digits[:14].ljust(14, '0'), '%Y%m%d%H%M%S')
    except ValueError:
        return None
    tz = UTC
    offset = value[len(digits):].strip()
    if len(offset) == 5 and offset[0] in '+-' and offset[1:].isdigit():
        delta = timedelta(hours=int(offset[1:3]), minutes=int(offset[3:5]))
        tz = timezone(delta if offset[0] == '+' else -delta)
    return when.replace(tzinfo=tz).astimezone(UTC)


def _text(elem: ET.Element, tag: str, language: str) -> str:
    found = elem.findall(tag)
    if not found:
        return ''
    best = next((e for e in found if e.get('lang') == language), found[0])
    return (best.text or '').strip()


def parse(raw: bytes, language: str = '') -> Guide:
    guide = Guide()
    for _, elem in ET.iterparse(BytesIO(decompress(raw)), events=('end',)):
        if elem.tag == 'channel':
            cid = elem.get('id')
            if cid:
                guide.names[cid] = [(d.text or '').strip() for d in elem.findall('display-name') if d.text]
            elem.clear()
        elif elem.tag == 'programme':
            cid, start = elem.get('channel'), parse_time(elem.get('start', ''))
            title = _text(elem, 'title', language)
            if cid and start and title:
                icon = elem.find('icon')
                episode = next((e.text or '' for e in elem.findall('episode-num') if e.get('system') == 'onscreen'), '')
                guide.programmes.setdefault(cid, []).append(Programme(
                    start=start, stop=parse_time(elem.get('stop', '')), title=title,
                    subtitle=_text(elem, 'sub-title', language), desc=_text(elem, 'desc', language),
                    categories=tuple(dict.fromkeys((c.text or '').strip() for c in elem.findall('category') if c.text)),
                    episode=episode.strip(), icon=icon.get('src', '') if icon is not None else ''))
            elem.clear()
    return guide
