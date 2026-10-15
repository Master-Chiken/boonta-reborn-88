#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${TMPDIR:-/tmp}/swe1r_item_layouts_$$"
trap 'rm -f "$BIN"' EXIT
cc -std=c99 -Wall -Wextra -Werror -pedantic -I"$ROOT/source" \
  "$ROOT/source/racer_physics.c" "$ROOT/source/track_catalog.c" "$ROOT/source/race_items.c" "$ROOT/tests/test_track_item_layouts.c" -lm -o "$BIN"
"$BIN"
