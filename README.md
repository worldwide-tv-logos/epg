# worldwide-tv-epg

TV guides (EPG) aggregated from public XMLTV sources and published under the channel IDs of
[worldwide-tv-logos](https://github.com/worldwide-tv-logos/database): one ID per channel gives both its logo and
its guide.

Updated every 6 hours, from 7 days ago to 7 days ahead.

## Files

| File | Content |
|---|---|
| `<country>.xml.gz` | XMLTV guide of a country (e.g. `fr.xml.gz`), for IPTV players |
| `all.xml.gz` | XMLTV guide of every channel |
| `<channel id>/<YYYY-MM-DD>.json` | programmes of one channel for one UTC day, a few KB, for applications |
| `index.json` | countries, channels, published days and the source chosen for each channel |
| `status.json` | state of each source at the last run |

Base URL: `https://worldwide-tv-logos.github.io/epg/` (a single public domain later).

```json
{"channel": "ch_ccg64xsq5h", "date": "2026-11-24", "programmes": [
  {"start": "2026-11-24T19:00:00Z", "stop": "2026-11-24T19:45:00Z", "title": "Le journal", "categories": ["News"]}
]}
```

Times are UTC (ISO 8601). Channel IDs, names, countries and logos: `channels.json` of worldwide-tv-logos.

## How it works

See [docs/architecture.md](docs/architecture.md). In short: every source of [sources.toml](sources.toml) is
downloaded, each guide channel is mapped to a registry channel (by its guide ID in the registry's `guides.json`,
else by a name unique in the source's countries), the source covering the most of the coming days wins for each
channel, and the result is published on GitHub Pages. Past days come from daily archives kept as release assets.

## Development

```bash
uv sync
uv run pytest -q
uv run ruff check .
uv run epg sources
uv run epg run --archive archive --out public   # a real pass (downloads every source)
uv run epg check --out public
```
