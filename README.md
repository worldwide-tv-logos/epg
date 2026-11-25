# worldwide-tv-epg

TV guides (EPG) aggregated from public XMLTV sources and published under the channel IDs of
[worldwide-tv-logos](https://github.com/worldwide-tv-logos/database): one ID per channel gives both its logo and
its guide.

Updated every 6 hours, from 7 days ago to 7 days ahead.

## Files

One XMLTV guide and one JSON guide per country and per UTC day, with the same content.

| File | Content |
|---|---|
| `<country>/<YYYY-MM-DD>.xml.gz` | XMLTV guide of a country for one day (e.g. `fr/2026-11-25.xml.gz`), for IPTV players |
| `<country>/<YYYY-MM-DD>.json` | the same guide in JSON, for applications |
| `index.json` | countries, days and channels published, and the source chosen for each channel |
| `status.json` | state of each source at the last run |

Base URL: `https://worldwide-tv-logos.github.io/epg/` (a single public domain later), from 7 days ago to 7 days
ahead. The [releases](https://github.com/worldwide-tv-logos/epg/releases) keep 30 days: one release per day
(`2026-11-25`), with `<country>.xml.gz` and `<country>.json.gz`.

```json
{"country": "fr", "date": "2026-11-25", "channels": [
  {"id": "ch_ccg64xsq5h", "name": "TF1", "logo": "https://worldwide-tv-logos.github.io/database/logos/ch_ccg64xsq5h.png",
   "programmes": [
     {"start": "2026-11-25T19:00:00Z", "stop": "2026-11-25T19:45:00Z", "title": "Le journal", "categories": ["News"]}
   ]}
]}
```

A day is a UTC day: a programme belongs to the day it starts. Times are UTC (ISO 8601). The channel IDs are those
of worldwide-tv-logos (`channels.json`): one ID gives both the logo and the guide.

## How it works

See [docs/architecture.md](docs/architecture.md). In short: every feed declared in [sources/](sources) (one file
per provider) is downloaded, each guide channel is mapped to a registry channel (by its guide ID in the registry's
`guides.json`, else by a name unique in the source's countries), the feed covering the most of the coming days wins
for each channel, and the result is published on GitHub Pages and in the daily releases, which also give back the
past days. To add a source: [docs/adding-a-source.md](docs/adding-a-source.md).

## Development

```bash
uv sync
uv run pytest -q
uv run ruff check .
uv run epg sources                                            # feeds, in the order they are used
uv run epg run --cache cache --archive archive --out public   # a real pass; downloads saved in cache/
uv run epg run --cache cache --archive archive --out public   # again: replayed on the same files, no download
uv run epg check --out public
```
