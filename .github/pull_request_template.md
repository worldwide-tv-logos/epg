<!-- Commit messages in English. A new source goes in sources.toml, in its order of preference. -->

## What

## Checklist

- [ ] `uv run pytest -q` and `uv run ruff check .` pass
- [ ] a new source: public XMLTV file, https, `id` matching the registry source name when it has one
- [ ] `uv run epg run` tried locally on the changed sources (channels mapped, nothing ambiguous guessed)
