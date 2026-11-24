"""The published window (PAST_DAYS before today to FUTURE_DAYS after) and the daily archives.

An archive holds one UTC day: {channel id: [programmes starting that day]}, as `<YYYY-MM-DD>.json.gz`. The sources
only give today and the next days, so the past days of the window come from the archives; a channel a source no
longer gives keeps its last good programmes the same way."""
import gzip
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from worldwide_tv_epg import config
from worldwide_tv_epg.xmltv import Programme


def days(today: date, past: int = config.PAST_DAYS, future: int = config.FUTURE_DAYS) -> list[date]:
    return [today + timedelta(days=i) for i in range(-past, future + 1)]


def by_day(programmes: dict[str, list[Programme]]) -> dict[date, dict[str, list[Programme]]]:
    out: dict[date, dict[str, list[Programme]]] = defaultdict(dict)
    for cid, progs in programmes.items():
        for p in progs:
            out[p.start.date()].setdefault(cid, []).append(p)
    return out


def read_archive(path: Path) -> dict[str, list[Programme]]:
    data = json.loads(gzip.decompress(path.read_bytes()))
    return {cid: [Programme.from_dict(p) for p in progs] for cid, progs in data.items()}


def write_archive(path: Path, day_programmes: dict[str, list[Programme]]) -> None:
    data = {cid: [p.to_dict() for p in sorted(progs, key=lambda p: p.start)]
            for cid, progs in sorted(day_programmes.items())}
    path.write_bytes(gzip.compress(json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode(), mtime=0))


def archive_name(day: date) -> str:
    return f'{day.isoformat()}.json.gz'


def combine(fresh: dict[date, dict[str, list[Programme]]], archives: dict[date, dict[str, list[Programme]]],
            window: list[date]) -> dict[date, dict[str, list[Programme]]]:
    """Each day of the window: the fresh programmes of a channel when there are some, else its archived ones."""
    out = {}
    for day in window:
        merged = dict(archives.get(day, {}))
        merged.update(fresh.get(day, {}))
        out[day] = merged
    return out


def expired(names: list[str], today: date, past: int = config.PAST_DAYS) -> list[str]:
    """Archive files older than the window (to delete)."""
    first = today - timedelta(days=past)
    out = []
    for n in names:
        try:
            if date.fromisoformat(n.split('.')[0]) < first:
                out.append(n)
        except ValueError:
            continue
    return sorted(out)
