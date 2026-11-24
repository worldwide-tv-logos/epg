"""One guide per channel: among the sources that map to a channel, the one covering the most of the coming days
(ties: the first source of sources.toml)."""
from datetime import datetime, timedelta

from worldwide_tv_epg import config
from worldwide_tv_epg.registry import Registry
from worldwide_tv_epg.sources import Source
from worldwide_tv_epg.xmltv import Guide, Programme


def coverage(programmes: list[Programme], start: datetime, end: datetime) -> float:
    """Hours of [start, end] covered by the programmes (a programme without a stop lasts until the next one)."""
    progs = sorted(programmes, key=lambda p: p.start)
    total = 0.0
    for i, p in enumerate(progs):
        stop = p.stop or (progs[i + 1].start if i + 1 < len(progs) else p.start)
        a, b = max(p.start, start), min(stop, end)
        if b > a:
            total += (b - a).total_seconds() / 3600
    return total


def clean(programmes: list[Programme]) -> list[Programme]:
    """Sorted, one programme per start time."""
    seen: dict[datetime, Programme] = {}
    for p in sorted(programmes, key=lambda p: p.start):
        seen.setdefault(p.start, p)
    return list(seen.values())


def merge(guides: list[tuple[Source, Guide]], registry: Registry, now: datetime,
          future: int = config.FUTURE_DAYS) -> tuple[dict[str, list[Programme]], dict[str, str]]:
    """Programmes of each registry channel, and the source chosen for it."""
    end = now + timedelta(days=future)
    best: dict[str, tuple[float, int, str, list[Programme]]] = {}
    for rank, (source, guide) in enumerate(guides):
        for gid, progs in guide.programmes.items():
            cid = registry.resolve(source.id, gid, guide.names.get(gid, []), source.countries)
            if not cid:
                continue
            progs = clean(progs)
            score = coverage(progs, now, end)
            current = best.get(cid)
            if current is None or (score, -rank) > (current[0], -current[1]):
                best[cid] = (score, rank, source.id, progs)
    return {cid: v[3] for cid, v in best.items()}, {cid: v[2] for cid, v in best.items()}
