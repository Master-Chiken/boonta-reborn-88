#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CC_BIN="${CC:-cc}"
TMP="${TMPDIR:-/tmp}/swe1r_pause_state_$$"
trap 'rm -f "$TMP"' EXIT
"$CC_BIN" -std=c99 -Wall -Wextra -Werror -pedantic -fsanitize=address,undefined \
  -I"$ROOT/source" "$ROOT/source/pause_state.c" "$ROOT/tests/test_pause_state.c" -o "$TMP"
ASAN_OPTIONS=detect_leaks=0 "$TMP"
