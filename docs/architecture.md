# Architecture

worldwide-tv-epg is one of the aggregators of the organisation:

| Repository | Role |
|---|---|
| [database](https://github.com/worldwide-tv-logos/database) | channel registry (the only source of `ch_` IDs) and logos |
| **epg** (this one) | TV guides of the registry channels |
| [website](https://github.com/worldwide-tv-logos/website) | website and API, on Vercel, under a single domain |

This repository never changes the registry: it reads `channels.json` and `guides.json` published by `database`.

## One pass (every 6 hours, `.github/workflows/run.yml`)

1. **Collect**: every feed of `sources/` (one file per provider, see [adding-a-source.md](adding-a-source.md)),
   one after the other with a pause, a busy site or a cut response tried again. Each feed is read by the reader of
   its kind, with the corrections declared for its provider (time offset). A feed that fails is skipped and
   reported; its channels keep their archived programmes.
2. **Map** each guide channel to a registry channel: its guide ID in `guides.json` (score of at least 0.9, one best
   channel), else its guide ID when it is the iptv-org ID of a registry channel, else a name (or alias, country
   prefix such as "UK - " dropped) unique among the registry channels of the source's countries. An ambiguous
   name maps to nothing: nothing is guessed.
3. **Archives**: the guides already published for the window are downloaded from the daily releases (the sources
   do not give the past days back).
4. **Merge**, per channel: a main feed before a fallback one, then the feed covering the most hours of the next
   7 days; ties go to the first feed (by provider rank). For each day, a channel's fresh programmes replace its archived ones; a channel missing from
   today's sources keeps its archived programmes (last good version).
5. **Publish** from 7 days ago to 7 days ahead, one XMLTV guide and one JSON guide per country and per UTC day
   (`<cc>/<YYYY-MM-DD>.xml.gz`, `<cc>/<YYYY-MM-DD>.json`), `index.json`, `status.json`; **check** (channels with
   programmes today, today's file of each country, published size under the alert threshold before the 1 GB limit
   of GitHub Pages).
6. **Release** each day (tag `<YYYY-MM-DD>`, `<cc>.xml.gz` and `<cc>.json.gz`): only the country guides that
   changed are uploaded; releases older than 30 days are deleted. Then **deploy** on GitHub Pages.

Nothing is committed: each deployment replaces the previous site and the archives are the daily releases, so the
repository holds only the code.

## Code

| Module | Role |
|---|---|
| `model.py` | `Programme`, `Guide`: the internal format, the same for every source |
| `net.py` | downloads: sequential with a pause, retries, size limit, cache folder for replays |
| `sources/config.py` | the provider files of `sources/`, checked |
| `sources/xmltv.py` | reader of XMLTV files (plain, gzip, xz) |
| `sources/fixes.py` | corrections declared for a provider (time offset) |
| `sources/__init__.py` | readers by kind (`READERS`), `read(feed, raw)` |
| `pipeline/mapping.py` | channels and guide IDs of the registry, mapping of a guide channel |
| `pipeline/merge.py` | one guide per channel, channels mapped and chosen per feed |
| `pipeline/window.py` | window of days, past days read back from the daily releases |
| `publish/xmltv.py`, `publish/guide_json.py` | writers of a guide |
| `publish/files.py` | guides per country and per day (site and releases), `index.json` |
| `checks.py` | checks of a published folder |
| `cli.py` | `epg sources`, `epg run`, `epg check` |

Tests follow the same split (`tests/test_<module>.py`); `tests/fixtures/` holds a small real extract of each
provider's file.
