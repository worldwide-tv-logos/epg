"""The channel registry of worldwide-tv-logos (channels.json, guides.json): our only source of channel IDs.

A guide channel maps to a registry channel by its guide ID (guides.json, score >= MIN_SCORE, one best channel),
otherwise by a name unique among the registry channels of the source's countries. Nothing is guessed: an
ambiguous name maps to nothing."""
import json
import urllib.request
from collections import defaultdict
from dataclasses import dataclass, field

from worldwide_tv_epg import config
from worldwide_tv_epg.text import match_key


@dataclass
class Registry:
    channels: dict[str, dict] = field(default_factory=dict)                  # ch_ id -> channel record
    by_guide: dict[tuple[str, str], str] = field(default_factory=dict)       # (source, guide id) -> ch_ id
    by_name: dict[tuple[str, str], set[str]] = field(default_factory=dict)   # (country, name key) -> ch_ ids

    def resolve(self, source: str, guide_id: str, names: list[str], countries: tuple[str, ...]) -> str | None:
        found = self.by_guide.get((source, guide_id))
        if found:
            return found
        for name in names:
            ids: set[str] = set()
            for cc in countries:
                ids |= self.by_name.get((cc, match_key(name)), set())
            if len(ids) == 1:
                return next(iter(ids))
        return None


def build(channels_json: dict, guides_json: dict, min_score: float = config.MIN_SCORE) -> Registry:
    reg = Registry()
    by_name: dict[tuple[str, str], set[str]] = defaultdict(set)
    for c in channels_json.get('channels', []):
        if c.get('status') != 'active':
            continue
        reg.channels[c['id']] = c
        for n in [c.get('name', ''), *(c.get('aliases') or [])]:
            k = match_key(n)
            if k:
                by_name[(c.get('country', ''), k)].add(c['id'])
    reg.by_name = dict(by_name)
    for source, ids in guides_json.get('guides', {}).items():
        for guide_id, candidates in ids.items():
            good = [x for x in candidates if x.get('score', 0) >= min_score and x.get('channel') in reg.channels]
            if not good:
                continue
            best = max(x['score'] for x in good)
            top = {x['channel'] for x in good if x['score'] == best}
            if len(top) == 1:
                reg.by_guide[(source, guide_id)] = top.pop()
    return reg


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={'User-Agent': config.USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


def load(base_url: str = config.REGISTRY_URL) -> Registry:
    return build(_get_json(f'{base_url}/channels.json'), _get_json(f'{base_url}/guides.json'))
