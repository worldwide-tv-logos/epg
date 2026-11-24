import gzip
import json
from datetime import UTC, date, datetime, timedelta

from worldwide_tv_epg import merge, publish, sources, window
from worldwide_tv_epg.cli import ROOT
from worldwide_tv_epg.xmltv import Guide, Programme

NOW = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)


def prog(hours: int, title: str = 'P', length: int = 1) -> Programme:
    start = NOW + timedelta(hours=hours)
    return Programme(start=start, stop=start + timedelta(hours=length), title=title)


def src(sid: str) -> sources.Source:
    return sources.Source(sid, sid, 'https://x', ('fr',), 'fr')


def test_the_source_covering_most_wins_ties_go_to_the_first(reg):
    short = Guide(names={'a': ['TF1']}, programmes={'a': [prog(0, 'short')]})
    long = Guide(names={'b': ['TF1']}, programmes={'b': [prog(0, 'long', 5)]})
    same = Guide(names={'c': ['TF1']}, programmes={'c': [prog(0, 'same', 5)]})
    progs, chosen = merge.merge([(src('one'), short), (src('two'), long), (src('three'), same)], reg, NOW)
    assert progs['ch_tf1'][0].title == 'long' and chosen['ch_tf1'] == 'two'


def test_window_and_expired_archives():
    today = date(2026, 11, 24)
    ds = window.days(today)
    assert ds[0] == date(2026, 11, 17) and ds[-1] == date(2026, 12, 1) and len(ds) == 15
    assert window.expired(['2026-11-16.json.gz', '2026-11-17.json.gz', 'x.txt'], today) == ['2026-11-16.json.gz']


def test_archived_programmes_fill_what_the_sources_no_longer_give(tmp_path):
    day = NOW.date()
    window.write_archive(tmp_path / 'a.json.gz', {'ch_tf1': [prog(0, 'old')], 'ch_fr2': [prog(1, 'kept')]})
    archived = window.read_archive(tmp_path / 'a.json.gz')
    out = window.combine({day: {'ch_tf1': [prog(0, 'new')]}}, {day: archived}, [day])
    assert out[day]['ch_tf1'][0].title == 'new' and out[day]['ch_fr2'][0].title == 'kept'


def test_publish_writes_country_files_channel_days_and_index(tmp_path, reg):
    day = NOW.date()
    index = publish.write(tmp_path, reg, {day: {'ch_tf1': [prog(0, 'Le journal')], 'ch_unknown': [prog(0)]}},
                          {'ch_tf1': 'iptv-epg-fr'}, NOW)
    assert list(index['countries']) == ['fr'] and index['channels']['ch_tf1']['source'] == 'iptv-epg-fr'
    data = json.loads((tmp_path / 'ch_tf1' / f'{day}.json').read_text(encoding='utf-8'))
    assert data['programmes'][0]['title'] == 'Le journal'
    xml = gzip.decompress((tmp_path / 'fr.xml.gz').read_bytes()).decode()
    assert 'channel id="ch_tf1"' in xml and 'Le journal' in xml and 'ch_unknown' not in xml


def test_sources_file_is_valid():
    srcs = sources.load(ROOT / 'sources.toml')
    assert srcs and srcs[0].id == 'iptv-epg-fr'
