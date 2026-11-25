import http.client
import io
import urllib.error

import pytest

from worldwide_tv_epg import net


class Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def opener_of(*answers):
    calls = []

    def opener(req, timeout):
        calls.append(req.full_url)
        answer = answers[len(calls) - 1]
        if isinstance(answer, Exception):
            raise answer
        return Resp(answer)
    return opener, calls


def http_error(code):
    return urllib.error.HTTPError('https://x', code, 'error', {}, None)


def test_a_busy_site_or_a_cut_response_is_tried_again():
    opener, calls = opener_of(http_error(503), http.client.IncompleteRead(b''), b'data')
    pauses = []
    assert net.get('https://x', opener=opener, sleep=pauses.append) == b'data'
    assert len(calls) == 3 and len(pauses) == 2


def test_a_refusal_is_not_tried_again_and_attempts_are_limited():
    opener, calls = opener_of(http_error(403))
    with pytest.raises(net.DownloadError, match='HTTP 403'):
        net.get('https://x', opener=opener, sleep=lambda s: None)
    assert len(calls) == 1
    opener, calls = opener_of(*[http_error(502)] * 3)
    with pytest.raises(net.DownloadError, match='3 attempts'):
        net.get('https://x', opener=opener, sleep=lambda s: None)


def test_size_limit():
    opener, _ = opener_of(b'x' * 11)
    with pytest.raises(net.DownloadError, match='larger'):
        net.get('https://x', opener=opener, max_size=10)


def test_the_cache_replays_without_downloading_and_saves_new_files(tmp_path):
    (tmp_path / 'feeds').mkdir()
    (tmp_path / 'feeds' / 'a').write_bytes(b'cached')
    fetched, pauses = [], []
    d = net.Downloader(tmp_path, fetch=lambda url: fetched.append(url) or b'new', sleep=pauses.append)
    assert d.get('feeds/a', 'https://a') == b'cached' and fetched == []
    assert d.get('feeds/b', 'https://b') == b'new' and d.get('registry/c.json', 'https://c') == b'new'
    assert (tmp_path / 'registry' / 'c.json').read_bytes() == b'new'
    assert fetched == ['https://b', 'https://c'] and len(pauses) == 1     # a pause between two downloads only
