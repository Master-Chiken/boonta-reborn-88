#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${TMPDIR:-/tmp}/swe1r_finish_line_crossing_$$"
trap 'rm -f "$BIN"' EXIT
cc -std=c99 -Wall -Wextra -Werror -pedantic -I"$ROOT/source" \
  "$ROOT/source/racer_physics.c" "$ROOT/tests/test_finish_line_crossing.c" \
  -lm -o "$BIN"
"$BIN"
