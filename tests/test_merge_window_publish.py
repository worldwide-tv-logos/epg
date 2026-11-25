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


def test_window():
    ds = window.days(date(2026, 11, 24))
    assert ds[0] == date(2026, 11, 17) and ds[-1] == date(2026, 12, 1) and len(ds) == 15


def test_publish_writes_one_xmltv_and_one_json_per_country_and_day(tmp_path, reg):
    day, other = NOW.date(), NOW.date() + timedelta(days=1)
    days = {day: {'ch_tf1': [prog(0, 'Le journal')], 'ch_la1': [prog(1, 'JT')], 'ch_unknown': [prog(0)]},
            other: {'ch_tf1': [prog(24, 'Demain')]}}
    index = publish.write(tmp_path / 'public', tmp_path / 'releases', reg, days, {'ch_tf1': 'iptv-epg-fr'}, NOW)
    assert index['countries']['fr'] == {'days': [str(day), str(other)], 'channels': 1}
    assert index['countries']['be']['days'] == [str(day)]
    assert index['channels']['ch_tf1']['source'] == 'iptv-epg-fr' and 'ch_unknown' not in index['channels']
    data = json.loads((tmp_path / 'public' / 'fr' / f'{day}.json').read_text(encoding='utf-8'))
    assert data['country'] == 'fr' and data['date'] == str(day)
    assert data['channels'][0]['id'] == 'ch_tf1' and data['channels'][0]['logo'] == 'https://x/tf1.png'
    assert data['channels'][0]['programmes'][0]['title'] == 'Le journal'
    xml = gzip.decompress((tmp_path / 'public' / 'fr' / f'{day}.xml.gz').read_bytes()).decode()
    assert 'channel id="ch_tf1"' in xml and 'Le journal' in xml and 'Demain' not in xml and 'ch_la1' not in xml
    rel = tmp_path / 'releases' / str(day)
    assert sorted(f.name for f in rel.iterdir()) == ['be.json.gz', 'be.xml.gz', 'fr.json.gz', 'fr.xml.gz']
    assert json.loads(gzip.decompress((rel / 'fr.json.gz').read_bytes())) == data


def test_released_guides_are_read_back_and_fill_what_the_sources_no_longer_give(tmp_path, reg):
    day = NOW.date()
    publish.write(tmp_path / 'public', tmp_path / 'releases', reg,
                  {day: {'ch_tf1': [prog(0, 'old')], 'ch_fr2': [prog(1, 'kept')]}}, {}, NOW)
    archived = window.read_day(tmp_path / 'releases' / str(day))
    assert archived['ch_fr2'][0] == prog(1, 'kept')
    out = window.combine({day: {'ch_tf1': [prog(0, 'new')]}}, {day: archived}, [day])
    assert out[day]['ch_tf1'][0].title == 'new' and out[day]['ch_fr2'][0].title == 'kept'


def test_unchanged_guides_give_the_same_bytes(tmp_path, reg):
    day = NOW.date()
    for run in ('a', 'b'):
        publish.write(tmp_path / run, tmp_path / f'{run}-rel', reg, {day: {'ch_tf1': [prog(0, 'Le journal')]}}, {},
                      NOW + timedelta(hours=6 if run == 'b' else 0))
    a, b = tmp_path / 'a-rel' / str(day), tmp_path / 'b-rel' / str(day)
    assert (a / 'fr.json.gz').read_bytes() == (b / 'fr.json.gz').read_bytes()
    assert (a / 'fr.xml.gz').read_bytes() == (b / 'fr.xml.gz').read_bytes()


def test_sources_file_is_valid():
    srcs = sources.load(ROOT / 'sources.toml')
    assert srcs and srcs[0].id == 'iptv-epg-fr'
