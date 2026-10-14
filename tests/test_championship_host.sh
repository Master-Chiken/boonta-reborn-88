#!/bin/bash
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cc -std=c99 -Wall -Wextra -Werror "$ROOT/tests/test_championship.c" "$ROOT/source/championship.c" -o "$TMP/test_championship"
"$TMP/test_championship"
echo "Championship tests: PASS"
