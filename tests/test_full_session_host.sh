#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CC_BIN="${CC:-cc}"
TMP="${TMPDIR:-/tmp}/swe1r_full_session_$$"
trap 'rm -f "$TMP"' EXIT
"$CC_BIN" -std=c99 -Wall -Wextra -Werror -pedantic \
  -fsanitize=address,undefined -fno-omit-frame-pointer \
  -I"$ROOT/source" \
  "$ROOT/source/track_catalog.c" \
  "$ROOT/source/vehicle_catalog.c" \
  "$ROOT/source/racer_physics.c" \
  "$ROOT/source/rival_ai.c" \
  "$ROOT/source/race_items.c" \
  "$ROOT/source/race_flow.c" \
  "$ROOT/source/championship.c" \
  "$ROOT/tests/test_full_session.c" -lm -o "$TMP"
ASAN_OPTIONS=detect_leaks=0 "$TMP"
