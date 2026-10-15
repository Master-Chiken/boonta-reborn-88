#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
cc -std=c99 -Wall -Wextra -Werror -I"$ROOT/source" \
  "$ROOT/source/game_text.c" "$ROOT/tests/test_game_text.c" -o "$TMP"
"$TMP"
echo "English UI text tests passed."
