"""The internal format, the same for every source: a guide is channels (by the source's own IDs) and programmes."""
from dataclasses import asdict, dataclass, field
from datetime import datetime


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
    names: dict[str, list[str]] = field(default_factory=dict)              # source channel id -> display names
    programmes: dict[str, list[Programme]] = field(default_factory=dict)   # source channel id -> programmes
