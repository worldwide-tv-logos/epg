"""The guide sources, declared as data: one TOML file per provider in `sources/` (see docs/adding-a-source.md).

    [provider]
    name = "IPTV-EPG.org"
    kind = "xmltv"           # the reader of its files (sources/__init__.py)
    rank = 1                 # preference between providers when two cover a channel equally well (1 first)
    role = "main"            # "main", or "fallback": used for a channel only when no main feed gives it
    language = "fr"          # default language of titles and descriptions, a feed can set its own
    time_offset = 0          # hours to add to the times of its files (a source whose times are wrong), default 0

    [[feed]]
    id = "iptv-epg-fr"       # the source name of the registry's guides.json, so that its guide IDs are mapped
    url = "https://iptv-epg.org/files/epg-fr.xml.gz"
    countries = ["fr"]       # where its channels are looked for when matching by name
    language = "fr"          # optional

Feeds are used in order: by rank, then provider file name, then their order in the file."""
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

KINDS = ('xmltv',)
ROLES = ('main', 'fallback')
_ID = re.compile(r'^[a-z0-9][a-z0-9-]*$')
_CC = re.compile(r'^[a-z]{2}$')


@dataclass(frozen=True)
class Feed:
    id: str
    url: str
    countries: tuple[str, ...]
    language: str
    provider: str          # provider file name, without .toml
    name: str              # provider name
    kind: str
    rank: int
    role: str
    time_offset: float     # hours


class SourceError(ValueError):
    pass


def _provider(path: Path) -> list[Feed]:
    key = path.stem
    try:
        data = tomllib.loads(path.read_text(encoding='utf-8'))
    except tomllib.TOMLDecodeError as exc:
        raise SourceError(f'{path.name}: {exc}') from None
    p = data.get('provider')
    if not isinstance(p, dict):
        raise SourceError(f'{path.name}: missing [provider]')
    unknown = set(p) - {'name', 'kind', 'rank', 'role', 'language', 'time_offset'}
    if unknown:
        raise SourceError(f'{path.name}: unknown provider setting {sorted(unknown)}')
    if not p.get('name'):
        raise SourceError(f'{path.name}: missing provider name')
    if p.get('kind') not in KINDS:
        raise SourceError(f'{path.name}: kind must be one of {KINDS}')
    rank, role, offset = p.get('rank'), p.get('role', 'main'), p.get('time_offset', 0)
    if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
        raise SourceError(f'{path.name}: rank must be a whole number from 1')
    if role not in ROLES:
        raise SourceError(f'{path.name}: role must be one of {ROLES}')
    if not isinstance(offset, int | float) or isinstance(offset, bool) or abs(offset) > 24:
        raise SourceError(f'{path.name}: time_offset must be a number of hours between -24 and 24')
    feeds = []
    for i, f in enumerate(data.get('feed', []), 1):
        unknown = set(f) - {'id', 'url', 'countries', 'language'}
        if unknown:
            raise SourceError(f'{path.name}: feed #{i}: unknown setting {sorted(unknown)}')
        fid, url, countries = f.get('id', ''), f.get('url', ''), f.get('countries', [])
        if not _ID.match(fid):
            raise SourceError(f'{path.name}: feed #{i}: invalid id {fid!r}')
        if not url.startswith('https://'):
            raise SourceError(f'{fid}: the URL must use https')
        if not countries or not all(isinstance(c, str) and _CC.match(c) for c in countries):
            raise SourceError(f'{fid}: countries must be lowercase two-letter codes')
        feeds.append(Feed(id=fid, url=url, countries=tuple(countries),
                          language=f.get('language', p.get('language', '')), provider=key, name=p['name'],
                          kind=p['kind'], rank=rank, role=role, time_offset=float(offset)))
    if not feeds:
        raise SourceError(f'{path.name}: no feed ([[feed]])')
    return feeds


def load(folder: Path) -> list[Feed]:
    feeds: list[Feed] = []
    files = sorted(Path(folder).glob('*.toml'))
    if not files:
        raise SourceError(f'no provider file in {folder}')
    for path in files:
        for f in _provider(path):
            if any(o.id == f.id for o in feeds):
                raise SourceError(f'{f.id}: duplicate feed id')
            feeds.append(f)
    order = {path.stem: i for i, path in enumerate(files)}
    return sorted(feeds, key=lambda f: (f.rank, order[f.provider]))      # stable: file order kept within a provider
