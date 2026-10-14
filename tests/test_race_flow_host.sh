#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${TMPDIR:-/tmp}/swe1r_race_flow_tests_$$"
trap 'rm -f "$BIN"' EXIT
cc -std=c99 -Wall -Wextra -Werror -pedantic -Isource \
  "$ROOT/source/race_flow.c" "$ROOT/tests/test_race_flow.c" -o "$BIN"
"$BIN"
