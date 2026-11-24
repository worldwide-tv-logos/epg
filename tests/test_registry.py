def test_guide_id_maps_from_the_minimum_score(reg):
    assert reg.resolve('iptv-epg-fr', 'TF1.fr', [], ('fr',)) == 'ch_tf1'
    assert reg.resolve('iptv-epg-fr', 'France2.fr', [], ('fr',)) is None      # 0.7 < 0.9, no name given


def test_name_unique_in_the_source_countries(reg):
    assert reg.resolve('xmltvfr', 'x1', ['France 2 HD'], ('fr', 'be')) == 'ch_fr2'
    assert reg.resolve('xmltvfr', 'x2', ['TF 1'], ('fr',)) == 'ch_tf1'        # alias
    assert reg.resolve('xmltvfr', 'x3', ['La Une'], ('fr',)) is None          # not in the source's countries


def test_iptv_org_id_and_country_prefix(reg):
    assert reg.resolve('iptv-epg-uk', 'BBCOne.uk', [], ('uk',)) == 'ch_bb1'
    assert reg.resolve('iptv-epg-uk', 'x', ['UK - BBC Two'], ('uk',)) == 'ch_bb2'


def test_ambiguous_or_closed_maps_to_nothing(reg):
    assert reg.resolve('xmltvfr', 'x4', ['M6'], ('fr',)) is None
    assert reg.resolve('iptv-epg-fr', 'Old.fr', ['Old'], ('fr',)) is None
