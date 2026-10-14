#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${TMPDIR:-/tmp}/swe1r_draft_assist_test"
cc -std=c99 -Wall -Wextra -Werror -I"$ROOT/source" \
  "$ROOT/source/draft_assist.c" "$ROOT/tests/test_draft_assist.c" \
  -lm -o "$BIN"
"$BIN"
rm -f "$BIN"
