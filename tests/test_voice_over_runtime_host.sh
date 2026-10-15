#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cc -std=c99 -Wall -Wextra -Werror -I"$ROOT/source" \
  "$ROOT/source/voice_over.c" "$ROOT/source/voice_over_runtime.c" \
  "$ROOT/tests/test_voice_over_runtime.c" -o "$TMP/test_voice_over_runtime"
"$TMP/test_voice_over_runtime"
echo "English VO runtime event tests passed"
