import pytest

from worldwide_tv_epg import registry

CHANNELS = {'channels': [
    {'id': 'ch_tf1', 'name': 'TF1', 'country': 'fr', 'status': 'active', 'aliases': ['TF 1'], 'logo': 'https://x/tf1.png'},
    {'id': 'ch_fr2', 'name': 'France 2', 'country': 'fr', 'status': 'active', 'aliases': []},
    {'id': 'ch_la1', 'name': 'La Une', 'country': 'be', 'status': 'active', 'aliases': []},
    {'id': 'ch_bb1', 'name': 'BBC One', 'country': 'uk', 'status': 'active', 'aliases': [], 'iptv': 'BBCOne.uk'},
    {'id': 'ch_bb2', 'name': 'BBC Two', 'country': 'uk', 'status': 'active', 'aliases': []},
    {'id': 'ch_m6a', 'name': 'M6', 'country': 'fr', 'status': 'active', 'aliases': []},
    {'id': 'ch_m6b', 'name': 'M6', 'country': 'fr', 'status': 'active', 'aliases': []},   # same name: ambiguous
    {'id': 'ch_old', 'name': 'Old', 'country': 'fr', 'status': 'closed', 'aliases': []},
]}
GUIDES = {'guides': {'iptv-epg-fr': {
    'TF1.fr': [{'channel': 'ch_tf1', 'score': 0.95, 'how': 'same ID'}],
    'France2.fr': [{'channel': 'ch_fr2', 'score': 0.7, 'how': 'name'}],          # under the minimum score
    'Old.fr': [{'channel': 'ch_old', 'score': 1.0, 'how': 'same ID'}],           # closed channel
}}}


@pytest.fixture
def reg():
    return registry.build(CHANNELS, GUIDES)
