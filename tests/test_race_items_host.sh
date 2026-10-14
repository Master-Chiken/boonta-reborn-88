#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${TMPDIR:-/tmp}/swe1r_items_$$"
trap 'rm -f "$BIN"' EXIT
cc -std=c99 -Wall -Wextra -Werror -pedantic -I"$ROOT/source" \
  "$ROOT/source/racer_physics.c" "$ROOT/source/track_catalog.c" "$ROOT/source/race_items.c" \
  "$ROOT/source/vehicle_catalog.c" "$ROOT/tests/test_race_items.c" -lm -o "$BIN"
"$BIN"
