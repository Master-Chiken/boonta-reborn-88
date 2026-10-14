#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${TMPDIR:-/tmp}/swe1r_physics_tests_$$"
trap 'rm -f "$BIN"' EXIT
cc -std=c99 -Wall -Wextra -Werror -pedantic -Isource \
  "$ROOT/source/racer_physics.c" "$ROOT/tests/test_racer_physics.c" -lm -o "$BIN"
"$BIN"
