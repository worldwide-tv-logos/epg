# Adding a source

A source is data, not code: one TOML file per provider in [`sources/`](../sources). Code is written only for a
new kind of file (a reader) or a new kind of correction, never for one source.

## 1. Declare it

Add a feed to the provider's file, or a new file `sources/<provider>.toml`:

```toml
# What the source is, what it covers, anything special about it (one or two lines).

[provider]
name = "Example EPG"
kind = "xmltv"          # the reader of its files: xmltv (plain, gzip or xz)
rank = 3                # preference between providers when two cover a channel equally well (1 first)
role = "main"           # "fallback": used for a channel only when no main feed gives it
language = "fr"         # default language of titles and descriptions
time_offset = 0         # hours to add to its times, for a source whose times are wrong

[[feed]]
id = "example-fr"       # the source name of the registry's guides.json when the registry maps its guide IDs
url = "https://example.org/epg-fr.xml.gz"
countries = ["fr"]      # where its channels are looked for when matching by name
```

| Setting | Rule |
|---|---|
| `id` | lowercase, unique across all files; equal to the registry's source name (`guides.json` of `database`) when the registry maps its guide IDs, otherwise its channels are mapped by iptv-org ID or by name only |
| `rank` | a provider that is better (longer horizon, more details) gets a smaller rank; feeds of the same rank keep the order of their file names |
| `role` | `fallback` for a copy of another source or a source we only want when the main ones fail (it never replaces a main feed for a channel) |
| `time_offset` | only when the times are measured wrong by a constant offset (compare with another source on the same channels) |

## 2. Measure it

```bash
uv run epg sources                                             # the file is valid, the feed is listed
uv run epg run --cache cache --archive archive --out public    # one real pass, every download saved in cache/
uv run epg check --out public                                  # state of each feed: read, mapped, chosen
```

`--cache` saves every downloaded file: run the pass again with the same `--cache` folder to replay it without
downloading anything (to compare two versions of the code or of the sources, file by file).

In `public/status.json`, the new feed gives its channels read, mapped (to registry channels) and chosen (the best
guide of a channel). A feed that maps few channels needs guide aliases in `database`: mapping is never fixed here.

## 3. Pull request

The description gives the source, what it covers and the measure: channels read, mapped and chosen, and the
countries whose number of channels with a guide changes. Tests and ruff green.

## A new kind of file

A source that does not give XMLTV needs a reader: a module in `worldwide_tv_epg/sources/` with a function
`parse(raw: bytes, language: str) -> Guide` (`model.py`), registered in `READERS` (`sources/__init__.py`) and
`KINDS` (`sources/config.py`), tested on a small real extract in `tests/fixtures/`.
