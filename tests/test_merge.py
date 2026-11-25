from datetime import UTC, datetime, timedelta

from worldwide_tv_epg.model import Guide, Programme
from worldwide_tv_epg.pipeline import merge
from worldwide_tv_epg.sources import Feed

NOW = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)


def prog(hours: int, title: str = 'P', length: int = 1) -> Programme:
    start = NOW + timedelta(hours=hours)
    return Programme(start=start, stop=start + timedelta(hours=length), title=title)


def feed(fid: str, role: str = 'main') -> Feed:
    return Feed(fid, 'https://x', ('fr',), 'fr', fid, fid, 'xmltv', 1, role, 0.0)


def tf1(gid: str, title: str, length: int) -> Guide:
    return Guide(names={gid: ['TF1']}, programmes={gid: [prog(0, title, length)]})


def test_the_feed_covering_most_wins_ties_go_to_the_first(reg):
    out = merge.merge([(feed('one'), tf1('a', 'short', 1)), (feed('two'), tf1('b', 'long', 5)),
                       (feed('three'), tf1('c', 'same', 5))], reg, NOW)
    assert out.programmes['ch_tf1'][0].title == 'long' and out.chosen['ch_tf1'] == 'two'
    assert out.mapped == {'one': 1, 'two': 1, 'three': 1}


def test_a_fallback_feed_is_used_only_for_channels_no_main_feed_gives(reg):
    fallback = Guide(names={'x': ['TF1'], 'y': ['France 2']},
                     programmes={'x': [prog(0, 'longer', 9)], 'y': [prog(0, 'only here')]})
    out = merge.merge([(feed('pw', 'fallback'), fallback), (feed('main'), tf1('a', 'main', 1))], reg, NOW)
    assert out.chosen == {'ch_tf1': 'main', 'ch_fr2': 'pw'}
    assert out.programmes['ch_fr2'][0].title == 'only here'
