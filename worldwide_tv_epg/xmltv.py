"""Reading XMLTV files (plain, gzip or xz) and the programme record used everywhere else."""
import gzip
import lzma
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta, timezone
from io import BytesIO


@dataclass(frozen=True)
class Programme:
    start: datetime                 # always timezone-aware, UTC
    stop: datetime | None
    title: str
    subtitle: str = ''
    desc: str = ''
    categories: tuple[str, ...] = ()
    episode: str = ''               # onscreen numbering when the source gives one ("S02E05")
    icon: str = ''

    def to_dict(self) -> dict:
        d = asdict(self)
        d['start'] = self.start.isoformat().replace('+00:00', 'Z')
        d['stop'] = self.stop.isoformat().replace('+00:00', 'Z') if self.stop else None
        d['categories'] = list(self.categories)
        return {k: v for k, v in d.items() if v not in ('', [], None) or k in ('start', 'title')}

    @classmethod
    def from_dict(cls, d: dict) -> 'Programme':
        def when(v):
            return datetime.fromisoformat(v.replace('Z', '+00:00')) if v else None
        return cls(start=when(d['start']), stop=when(d.get('stop')), title=d.get('title', ''),
                   subtitle=d.get('subtitle', ''), desc=d.get('desc', ''), categories=tuple(d.get('categories', [])),
                   episode=d.get('episode', ''), icon=d.get('icon', ''))


@dataclass
class Guide:
    names: dict[str, list[str]] = field(default_factory=dict)              # guide channel id -> display names
    programmes: dict[str, list[Programme]] = field(default_factory=dict)   # guide channel id -> programmes


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
