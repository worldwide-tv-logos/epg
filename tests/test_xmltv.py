import gzip
import lzma
from datetime import UTC, datetime

from worldwide_tv_epg.model import Programme
from worldwide_tv_epg.sources import xmltv

SAMPLE = b'''<?xml version="1.0" encoding="UTF-8"?>
<tv>
  <channel id="TF1.fr"><display-name>TF1</display-name><display-name>TF1 HD</display-name></channel>
  <programme start="20261124200000 +0100" stop="20261124210000 +0100" channel="TF1.fr">
    <title lang="en">News</title><title lang="fr">Le journal</title>
    <desc lang="fr">Informations.</desc><category lang="fr">Info</category><category lang="fr">Info</category>
    <episode-num system="onscreen">S01E02</episode-num><icon src="https://x/i.jpg"/>
  </programme>
  <programme start="2026112421" channel="TF1.fr"><title>Film</title></programme>
  <programme start="bad" channel="TF1.fr"><title>Ignored</title></programme>
</tv>'''


def test_parse_prefers_the_language_and_reads_utc_times():
    g = xmltv.parse(SAMPLE, 'fr')
    assert g.names == {'TF1.fr': ['TF1', 'TF1 HD']}
    first, second = g.programmes['TF1.fr']
    assert first.title == 'Le journal' and first.desc == 'Informations.'
    assert first.start == datetime(2026, 11, 24, 19, 0, tzinfo=UTC)
    assert first.categories == ('Info',) and first.episode == 'S01E02' and first.icon == 'https://x/i.jpg'
    assert second.start == datetime(2026, 11, 24, 21, 0, tzinfo=UTC) and second.stop is None


def test_compressed_files():
    assert xmltv.parse(gzip.compress(SAMPLE)).names == xmltv.parse(lzma.compress(SAMPLE)).names


def test_programme_round_trip():
    p = xmltv.parse(SAMPLE, 'fr').programmes['TF1.fr'][0]
    assert Programme.from_dict(p.to_dict()) == p
    assert p.to_dict()['start'] == '2026-11-24T19:00:00Z'
