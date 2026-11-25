"""Downloads: one at a time with a pause between two, a busy site or a cut response tried again, and an optional
cache folder so that a pass can be replayed on the same files without downloading anything."""
import http.client
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

from worldwide_tv_epg import config

_RETRY = (429, 500, 502, 503, 504)


class DownloadError(RuntimeError):
    pass


def get(url: str, *, opener: Callable = urllib.request.urlopen, sleep: Callable = time.sleep,
        attempts: int = config.ATTEMPTS, max_size: int = config.MAX_DOWNLOAD) -> bytes:
    problem = ''
    for attempt in range(attempts):
        if attempt:
            sleep(config.RETRY_PAUSE * attempt)
        try:
            req = urllib.request.Request(url, headers={'User-Agent': config.USER_AGENT})
            with opener(req, timeout=config.TIMEOUT) as resp:
                data = resp.read(max_size + 1)
        except urllib.error.HTTPError as exc:
            if exc.code not in _RETRY:
                raise DownloadError(f'HTTP {exc.code}') from None
            problem = f'HTTP {exc.code}'
            continue
        except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:   # HTTPException: cut response
            problem = f'network error ({getattr(exc, "reason", None) or exc!r})'
            continue
        if len(data) > max_size:
            raise DownloadError(f'larger than {max_size // (1024 * 1024)} MB')
        return data
    raise DownloadError(f'{problem}, {attempts} attempts')


class Downloader:
    """Sequential downloads of one run. With a cache folder, a file already there is reused instead of downloaded
    (replay) and every new download is saved there under its key (`feeds/<feed id>`, `registry/channels.json`)."""

    def __init__(self, cache: Path | None = None, fetch: Callable[[str], bytes] = get,
                 sleep: Callable = time.sleep):
        self.cache, self.fetch, self.sleep = cache, fetch, sleep
        self._downloaded = False

    def get(self, key: str, url: str) -> bytes:
        cached = self.cache / key if self.cache else None
        if cached and cached.is_file():
            return cached.read_bytes()
        if self._downloaded:
            self.sleep(config.PAUSE)
        self._downloaded = True
        data = self.fetch(url)
        if cached:
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_bytes(data)
        return data
