"""The published window (PAST_DAYS before today to FUTURE_DAYS after) and the archives of past days.

The sources only give today and the next days, so the past days of the window come from the archives: the JSON
guides of the daily releases (`<YYYY-MM-DD>/<cc>.json.gz`, see publish/files.py), downloaded by the workflow.
A channel a source no longer gives keeps its last good programmes the same way."""
import gzip
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from worldwide_tv_epg import config
from worldwide_tv_epg.model import Programme


def days(today: date, past: int = config.PAST_DAYS, future: int = config.FUTURE_DAYS) -> list[date]:
    return [today + timedelta(days=i) for i in range(-past, future + 1)]


def by_day(programmes: dict[str, list[Programme]]) -> dict[date, dict[str, list[Programme]]]:
    out: dict[date, dict[str, list[Programme]]] = defaultdict(dict)
    for cid, progs in programmes.items():
        for p in progs:
            out[p.start.date()].setdefault(cid, []).append(p)
    return out


def read_day(folder: Path) -> dict[str, list[Programme]]:
    """Programmes of one archived day: every country guide `<cc>.json.gz` of its folder."""
    out: dict[str, list[Programme]] = {}
    for f in sorted(folder.glob('*.json.gz')):
        for c in json.loads(gzip.decompress(f.read_bytes()))['channels']:
            out[c['id']] = [Programme.from_dict(p) for p in c['programmes']]
    return out


def combine(fresh: dict[date, dict[str, list[Programme]]], archives: dict[date, dict[str, list[Programme]]],
            window: list[date]) -> dict[date, dict[str, list[Programme]]]:
    """Each day of the window: the fresh programmes of a channel when there are some, else its archived ones."""
    out = {}
    for day in window:
        merged = dict(archives.get(day, {}))
        merged.update(fresh.get(day, {}))
        out[day] = merged
    return out
