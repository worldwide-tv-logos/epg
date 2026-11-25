"""One guide per channel. Among the feeds that map to a channel: a main feed before a fallback one, then the one
covering the most hours of the coming days, then the first feed (by rank, see sources/config.py)."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from worldwide_tv_epg import config
from worldwide_tv_epg.model import Guide, Programme
from worldwide_tv_epg.pipeline.mapping import Registry
from worldwide_tv_epg.sources import Feed


@dataclass
class Merged:
    programmes: dict[str, list[Programme]] = field(default_factory=dict)   # channel id -> programmes
    chosen: dict[str, str] = field(default_factory=dict)                   # channel id -> feed id
    mapped: dict[str, int] = field(default_factory=dict)                   # feed id -> its channels mapped


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


def merge(guides: list[tuple[Feed, Guide]], registry: Registry, now: datetime,
          future: int = config.FUTURE_DAYS) -> Merged:
    end = now + timedelta(days=future)
    best: dict[str, tuple[tuple, str, list[Programme]]] = {}
    out = Merged()
    for order, (feed, guide) in enumerate(guides):
        mapped = 0
        for gid, progs in guide.programmes.items():
            cid = registry.resolve(feed.id, gid, guide.names.get(gid, []), feed.countries)
            if not cid:
                continue
            mapped += 1
            progs = clean(progs)
            key = (feed.role == 'main', coverage(progs, now, end), -order)
            if cid not in best or key > best[cid][0]:
                best[cid] = (key, feed.id, progs)
        out.mapped[feed.id] = mapped
    out.programmes = {cid: v[2] for cid, v in best.items()}
    out.chosen = {cid: v[1] for cid, v in best.items()}
    return out
