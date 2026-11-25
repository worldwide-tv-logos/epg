"""Guide sources: their declaration (config.py, files of `sources/`), one reader per kind of file, and the
corrections declared for a provider (fixes.py). Every reader takes the downloaded bytes of a feed and its language
and returns a Guide (model.py): adding a kind of source is adding a reader here, nothing else changes."""
from collections.abc import Callable

from worldwide_tv_epg.model import Guide
from worldwide_tv_epg.sources import fixes, xmltv
from worldwide_tv_epg.sources.config import KINDS, Feed, SourceError, load

READERS: dict[str, Callable[[bytes, str], Guide]] = {'xmltv': xmltv.parse}

__all__ = ['KINDS', 'READERS', 'Feed', 'SourceError', 'load', 'read']


def read(feed: Feed, raw: bytes) -> Guide:
    """The guide of a downloaded feed, with the corrections declared for its provider."""
    return fixes.shift(READERS[feed.kind](raw, feed.language), feed.time_offset)
