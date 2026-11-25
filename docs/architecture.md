# Architecture

worldwide-tv-epg is one of the aggregators of the organisation:

| Repository | Role |
|---|---|
| [database](https://github.com/worldwide-tv-logos/database) | channel registry (the only source of `ch_` IDs) and logos |
| **epg** (this one) | TV guides of the registry channels |
| [website](https://github.com/worldwide-tv-logos/website) | website and API, on Vercel, under a single domain |

This repository never changes the registry: it reads `channels.json` and `guides.json` published by `database`.

## One pass (every 6 hours, `.github/workflows/run.yml`)

1. **Collect**: every source of `sources.toml`, one after the other. A source that fails is skipped and reported;
   its channels keep their archived programmes.
2. **Map** each guide channel to a registry channel: its guide ID in `guides.json` (score of at least 0.9, one best
   channel), else its guide ID when it is the iptv-org ID of a registry channel, else a name (or alias, country
   prefix such as "UK - " dropped) unique among the registry channels of the source's countries. An ambiguous
   name maps to nothing: nothing is guessed.
3. **Archives**: the guides already published for the window are downloaded from the daily releases (the sources
   do not give the past days back).
4. **Merge**, per channel: the source covering the most hours of the next 7 days; ties go to the first source of
   `sources.toml`. For each day, a channel's fresh programmes replace its archived ones; a channel missing from
   today's sources keeps its archived programmes (last good version).
5. **Publish** from 7 days ago to 7 days ahead, one XMLTV guide and one JSON guide per country and per UTC day
   (`<cc>/<YYYY-MM-DD>.xml.gz`, `<cc>/<YYYY-MM-DD>.json`), `index.json`, `status.json`; **check** (channels with
   programmes today, today's file of each country, published size under the alert threshold before the 1 GB limit
   of GitHub Pages).
6. **Release** each day (tag `<YYYY-MM-DD>`, `<cc>.xml.gz` and `<cc>.json.gz`): only the country guides that
   changed are uploaded; releases older than 30 days are deleted. Then **deploy** on GitHub Pages.

Nothing is committed: each deployment replaces the previous site and the archives are the daily releases, so the
repository holds only the code.

## Modules

| Module | Role |
|---|---|
| `sources.py` | `sources.toml`, in order of preference |
| `registry.py` | channels and guide IDs of the registry, mapping of a guide channel |
| `xmltv.py` | reading XMLTV (plain, gzip, xz), the `Programme` record |
| `merge.py` | one guide per channel |
| `window.py` | window of days, past days read back from the daily releases |
| `publish.py` | guides per country and per day (site and releases), `index.json` |
| `cli.py` | `epg sources`, `epg run`, `epg check` |
