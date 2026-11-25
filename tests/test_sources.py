from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from worldwide_tv_epg import sources
from worldwide_tv_epg.cli import ROOT
from worldwide_tv_epg.model import Guide, Programme
from worldwide_tv_epg.sources import fixes

FIXTURES = Path(__file__).parent / 'fixtures'
PROVIDER = '''[provider]
name = "Example"
kind = "xmltv"
rank = {rank}
role = "{role}"
language = "fr"

[[feed]]
id = "{fid}"
url = "https://example.org/{fid}.xml.gz"
countries = ["fr"]
'''


def write(folder: Path, name: str, rank: int = 1, role: str = 'main', fid: str | None = None, extra: str = '') -> None:
    (folder / f'{name}.toml').write_text(PROVIDER.format(rank=rank, role=role, fid=fid or name) + extra,
                                         encoding='utf-8')


def test_every_provider_file_is_valid_and_has_a_reader():
    feeds = sources.load(ROOT / 'sources')
    assert feeds[0].id == 'iptv-epg-fr' and feeds[-1].id == 'xmltvfr'
    assert set(sources.READERS) == set(sources.KINDS)
    assert all(f.kind in sources.READERS and f.language for f in feeds)


def test_feeds_ordered_by_rank_then_file_and_defaults_of_the_provider(tmp_path):
    write(tmp_path, 'b-second', rank=2, extra='\n[[feed]]\nid = "b-two"\nurl = "https://x.org/2"\n'
                                              'countries = ["be"]\nlanguage = "nl"\n')
    write(tmp_path, 'a-first', rank=3, role='fallback')
    write(tmp_path, 'c-first', rank=1)
    feeds = sources.load(tmp_path)
    assert [f.id for f in feeds] == ['c-first', 'b-second', 'b-two', 'a-first']
    assert feeds[1].language == 'fr' and feeds[2].language == 'nl'
    assert feeds[3].role == 'fallback' and feeds[3].provider == 'a-first' and feeds[3].time_offset == 0


@pytest.mark.parametrize('content, error', [
    ('[provider]\nname = "X"\nkind = "json"\nrank = 1\n[[feed]]\nid = "x"\nurl = "https://x"\ncountries = ["fr"]',
     'kind'),
    ('[provider]\nname = "X"\nkind = "xmltv"\nrank = 0\n[[feed]]\nid = "x"\nurl = "https://x"\ncountries = ["fr"]',
     'rank'),
    ('[provider]\nname = "X"\nkind = "xmltv"\nrank = 1\nrole = "backup"\n[[feed]]\nid = "x"\nurl = "https://x"\n'
     'countries = ["fr"]', 'role'),
    ('[provider]\nname = "X"\nkind = "xmltv"\nrank = 1\ntime_offset = 30\n[[feed]]\nid = "x"\nurl = "https://x"\n'
     'countries = ["fr"]', 'time_offset'),
    ('[provider]\nname = "X"\nkind = "xmltv"\nrank = 1\n[[feed]]\nid = "x"\nurl = "http://x"\ncountries = ["fr"]',
     'https'),
    ('[provider]\nname = "X"\nkind = "xmltv"\nrank = 1\n[[feed]]\nid = "x"\nurl = "https://x"\ncountries = ["FR"]',
     'two-letter'),
    ('[provider]\nname = "X"\nkind = "xmltv"\nrank = 1\n[[feed]]\nid = "x"\nurl = "https://x"\ncountries = ["fr"]\n'
     'priority = 2', 'unknown'),
    ('[provider]\nname = "X"\nkind = "xmltv"\nrank = 1\n', 'no feed'),
])
def test_invalid_provider_files_are_refused(tmp_path, content, error):
    (tmp_path / 'x.toml').write_text(content, encoding='utf-8')
    with pytest.raises(sources.SourceError, match=error):
        sources.load(tmp_path)


def test_a_feed_id_is_unique_across_providers(tmp_path):
    write(tmp_path, 'one', fid='same')
    write(tmp_path, 'two', fid='same')
    with pytest.raises(sources.SourceError, match='duplicate'):
        sources.load(tmp_path)


@pytest.mark.parametrize('fid', ['iptv-epg-fr', 'xmltvfr'])
def test_real_extract_of_each_provider_is_read(fid):
    feed = next(f for f in sources.load(ROOT / 'sources') if f.id == fid)
    guide = sources.read(feed, (FIXTURES / f'{fid}.xml').read_bytes())
    assert set(guide.programmes) == {'TF1.fr', 'France2.fr'}
    assert all(len(progs) == 3 for progs in guide.programmes.values())
    p = guide.programmes['TF1.fr'][0]
    assert p.start.tzinfo == UTC and p.stop > p.start and p.title


def test_declared_time_offset_shifts_every_programme():
    start = datetime(2026, 11, 25, 20, 0, tzinfo=UTC)
    guide = Guide(names={'a': ['A']}, programmes={'a': [Programme(start, start + timedelta(hours=1), 'News'),
                                                        Programme(start, None, 'Open')]})
    shifted = fixes.shift(guide, -8)
    assert shifted.programmes['a'][0].start == start - timedelta(hours=8)
    assert shifted.programmes['a'][0].stop == start - timedelta(hours=7) and shifted.programmes['a'][1].stop is None
    assert fixes.shift(guide, 0) is guide
