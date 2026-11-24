"""The guide sources of sources.toml, in order of preference."""
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

_ID = re.compile(r'^[a-z0-9][a-z0-9-]*$')
_CC = re.compile(r'^[a-z]{2}$')


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    url: str
    countries: tuple[str, ...]
    language: str


class SourceError(ValueError):
    pass


def load(path: Path) -> list[Source]:
    data = tomllib.loads(Path(path).read_text(encoding='utf-8'))
    out: list[Source] = []
    for i, row in enumerate(data.get('source', []), 1):
        try:
            s = Source(id=row['id'], name=row['name'], url=row['url'],
                       countries=tuple(row.get('countries', [])), language=row.get('language', ''))
        except KeyError as exc:
            raise SourceError(f'source #{i}: missing {exc}') from None
        if not _ID.match(s.id):
            raise SourceError(f'source #{i}: invalid id {s.id!r}')
        if not s.url.startswith('https://'):
            raise SourceError(f'{s.id}: the URL must use https')
        if not s.countries or not all(_CC.match(c) for c in s.countries):
            raise SourceError(f'{s.id}: countries must be lowercase two-letter codes')
        if any(o.id == s.id for o in out):
            raise SourceError(f'{s.id}: duplicate id')
        out.append(s)
    return out
