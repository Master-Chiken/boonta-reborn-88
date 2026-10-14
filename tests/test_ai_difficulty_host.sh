#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${TMPDIR:-/tmp}/swe1r_ai_difficulty_$$"
trap 'rm -f "$BIN"' EXIT
cc -std=c99 -Wall -Wextra -Werror -pedantic -Isource \
  "$ROOT/source/racer_physics.c" "$ROOT/source/rival_ai.c" \
  "$ROOT/source/vehicle_catalog.c" "$ROOT/tests/test_ai_difficulty.c" -lm -o "$BIN"
"$BIN"
