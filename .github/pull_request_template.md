<!-- Commit messages in English. A new source is a provider file in sources/ (docs/adding-a-source.md), with its measure. -->

## What

## Checklist

- [ ] `uv run pytest -q` and `uv run ruff check .` pass
- [ ] a new source: public XMLTV file, https, `id` matching the registry source name when it has one
- [ ] `uv run epg run` tried locally on the changed sources (channels mapped, nothing ambiguous guessed)
