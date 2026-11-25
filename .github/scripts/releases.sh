#!/usr/bin/env bash
# Daily releases: one per UTC day (tag YYYY-MM-DD), holding the XMLTV and JSON guide of each country.
#
#   releases.sh download <archive dir> <first day> <last day>   past guides of the window, to archive/<day>/
#   releases.sh upload <releases dir> <archive dir> <keep days>  new or changed guides uploaded, old releases deleted
#
# A country guide is uploaded only when its JSON differs from the one downloaded (files are written with mtime=0,
# so an unchanged guide gives the same bytes); releases older than <keep days> are deleted with their tag.
set -euo pipefail
cmd=$1

day_range() {   # every day from $1 to $2
  local d=$1
  while [[ ! "$d" > "$2" ]]; do echo "$d"; d=$(date -u -d "$d + 1 day" +%F); done
}

if [ "$cmd" = download ]; then
  dir=$2
  for d in $(day_range "$3" "$4"); do
    gh release download "$d" --dir "$dir/$d" --pattern '*.json.gz' --clobber 2>/dev/null || true
  done
  exit 0
fi

rel=$2 archive=$3 keep=$4
for folder in "$rel"/*/; do
  d=$(basename "$folder")
  files=()
  for js in "$folder"*.json.gz; do
    cc=$(basename "$js" .json.gz)
    if ! cmp -s "$js" "$archive/$d/$cc.json.gz"; then
      files+=("$js" "$folder$cc.xml.gz")
    fi
  done
  [ ${#files[@]} -eq 0 ] && continue
  gh release view "$d" >/dev/null 2>&1 || gh release create "$d" --latest=false --title "TV guides of $d" \
    --notes "XMLTV (\`<country>.xml.gz\`) and JSON (\`<country>.json.gz\`) guide of each country for $d (UTC)."
  gh release upload "$d" "${files[@]}" --clobber
  echo "$d: $(( ${#files[@]} / 2 )) country guide(s) uploaded"
done
oldest=$(date -u -d "-$keep days" +%F)
for tag in $(gh release list --limit 200 --json tagName --jq '.[].tagName'); do
  if [[ "$tag" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ && "$tag" < "$oldest" ]]; then
    gh release delete "$tag" --cleanup-tag --yes
    echo "deleted $tag"
  fi
done
