"""Channel names reduced to a key for matching ("TF1 HD" and "tf1" give the same key)."""
import re
import unicodedata

_QUALITY = re.compile(r'\b(hd|fhd|uhd|4k|sd)\b')


def match_key(name: str) -> str:
    s = unicodedata.normalize('NFKD', name or '').encode('ascii', 'ignore').decode().lower()
    s = s.replace('&', ' and ').replace('+', ' plus ')
    s = _QUALITY.sub(' ', s)
    return re.sub(r'[^a-z0-9]', '', s)
