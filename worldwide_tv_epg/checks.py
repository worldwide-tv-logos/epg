"""Checks on a published folder: channels with programmes today, today's file of each country, published size,
and the state of each feed (read, mapped, chosen). A failed check fails the run before deployment."""
import json
from datetime import UTC, datetime
from pathlib import Path

from worldwide_tv_epg import config
from worldwide_tv_epg.publish.files import size


def check(out: Path, today: str | None = None) -> tuple[str, bool]:
    """The report (Markdown) and whether a check failed."""
    index = json.loads((out / 'index.json').read_text(encoding='utf-8'))
    status = json.loads((out / 'status.json').read_text(encoding='utf-8'))
    today = today or datetime.now(UTC).date().isoformat()
    lines, failed = ['## Guides', '', '| Country | Channels | With today |', '|---|---|---|'], False
    for cc in index['countries']:
        chans = [c for c in index['channels'].values() if c['country'] == cc]
        if not (out / cc / f'{today}.json').is_file() and any(today in c['days'] for c in chans):
            failed = True
            lines.append(f'| {cc} | missing file {cc}/{today}.json | |')
        lines.append(f'| {cc} | {len(chans)} | {sum(today in c["days"] for c in chans)} |')
    with_today = sum(today in c['days'] for c in index['channels'].values())
    total = size(out)
    lines += ['', f'Channels with programmes today: **{with_today}**', f'Published size: **{total / 1e6:.0f} MB**', '',
              '| Feed | Provider | State |', '|---|---|---|']
    for fid, s in status['sources'].items():
        state = (f'ok, {s["channels"]} channels read, {s.get("mapped", "?")} mapped, {s.get("chosen", "?")} chosen'
                 if s['ok'] else f'FAILED: {s["error"]}')
        lines.append(f'| {fid} | {s.get("provider", "")} | {state} |')
    if not with_today:
        failed = True
        lines.append('\n**No channel has programmes today.**')
    if total > config.SIZE_ALERT:
        failed = True
        lines.append(f'\n**Published size over {config.SIZE_ALERT / 1e6:.0f} MB (GitHub Pages limit: 1 GB).**')
    return '\n'.join(lines) + '\n', failed
