"""Corrections declared for a provider in its file (never written for one source in code): here, the hours to
add to the times of a source whose times are wrong."""
from dataclasses import replace
from datetime import timedelta

from worldwide_tv_epg.model import Guide


def shift(guide: Guide, hours: float) -> Guide:
    if not hours:
        return guide
    delta = timedelta(hours=hours)
    return Guide(names=guide.names, programmes={
        cid: [replace(p, start=p.start + delta, stop=p.stop + delta if p.stop else None) for p in progs]
        for cid, progs in guide.programmes.items()})
