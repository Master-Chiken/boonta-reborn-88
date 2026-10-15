#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${TMPDIR:-/tmp}/swe1r_track_direction_$$"
trap 'rm -f "$BIN"' EXIT
cc -std=c99 -Wall -Wextra -Werror -pedantic -I"$ROOT/source" \
  "$ROOT/source/track_direction.c" "$ROOT/tests/test_track_direction.c" -o "$BIN"
"$BIN"
