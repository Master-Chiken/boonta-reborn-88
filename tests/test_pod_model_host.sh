#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${TMPDIR:-/tmp}/swe1r_pod_model_tests_$$"
trap 'rm -f "$BIN"' EXIT
cc -std=c99 -Wall -Wextra -Werror -pedantic -fsanitize=address,undefined \
  -I"$ROOT/source" "$ROOT/source/pod_model.c" "$ROOT/tests/test_pod_model.c" -lm -o "$BIN"
"$BIN"
