#!/usr/bin/env bash
# Synchronises the release `archive` with the local archive folder: every local file uploaded (replacing the
# asset of the same day), every asset without a local file (older than the window) deleted.
set -euo pipefail
dir="$1"
gh release upload archive "$dir"/*.json.gz --clobber
for asset in $(gh release view archive --json assets --jq '.assets[].name'); do
  if [ ! -f "$dir/$asset" ]; then
    gh release delete-asset archive "$asset" --yes
    echo "deleted $asset"
  fi
done
