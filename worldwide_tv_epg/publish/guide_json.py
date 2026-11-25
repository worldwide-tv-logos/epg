"""JSON writer: the same guide as the XMLTV one, for applications."""
import json
from datetime import date

from worldwide_tv_epg.model import Programme
from worldwide_tv_epg.publish.xmltv import logo


def guide_json(country: str, day: date, channels: list[dict], programmes: dict[str, list[Programme]]) -> bytes:
    data = {'country': country, 'date': day.isoformat(), 'channels': [
        {'id': c['id'], 'name': c.get('name', c['id']), **({'logo': logo(c)} if logo(c) else {}),
         'programmes': [p.to_dict() for p in programmes[c['id']]]} for c in channels]}
    return json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
