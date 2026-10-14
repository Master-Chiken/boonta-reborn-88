#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CC_BIN="${CC:-cc}"
TMP="${TMPDIR:-/tmp}/swe1r_race_mode_$$"
trap 'rm -f "$TMP"' EXIT
"$CC_BIN" -std=c99 -Wall -Wextra -Werror -pedantic -I"$ROOT/source" \
  "$ROOT/source/race_mode_select.c" "$ROOT/tests/test_race_mode_select.c" -o "$TMP"
"$TMP"
