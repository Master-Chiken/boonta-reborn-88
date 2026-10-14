#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CC_BIN="${CC:-cc}"
TMP="${TMPDIR:-/tmp}/swe1r_career_save_$$"
trap 'rm -f "$TMP"' EXIT
"$CC_BIN" -std=c99 -Wall -Wextra -Werror -pedantic \
  -fsanitize=address,undefined -fno-omit-frame-pointer \
  -I"$ROOT/source" "$ROOT/source/career_save.c" "$ROOT/tests/test_career_save.c" \
  -lm -o "$TMP"
ASAN_OPTIONS=detect_leaks=0 "$TMP"
