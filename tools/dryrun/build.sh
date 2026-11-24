#!/bin/bash
# Build the dry-run harness (harness.rs) once per target, for the host.
# Needs the same Rust nightly as the plugins (see docs/BUILDING.md).
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
OUT="$HERE/../../build/dryrun"
mkdir -p "$OUT"
for target in suicune hooh lugia snorlax beastfinder; do
  extra=()
  [ "$target" = beastfinder ] && extra=(--cfg 'feature="beasts"')
  rustc +nightly-2024-03-21 --edition 2021 --crate-type cdylib -O \
    --cfg 'feature="celebi_auto"' --cfg 'feature="celebi_natural"' \
    --cfg "feature=\"$target\"" "${extra[@]}" \
    "$HERE/harness.rs" -o "$OUT/lib$target.so"
  echo "built lib$target.so"
done
