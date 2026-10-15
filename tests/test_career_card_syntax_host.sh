#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CC_BIN="${CC:-cc}"
"$CC_BIN" -DGEKKO -std=gnu99 -Wall -Wextra -Werror -fsyntax-only \
  -I"$ROOT/tests/mockogc" -I"$ROOT/source" "$ROOT/source/career_save.c"
echo "PASS: GameCube memory-card adapter passes syntax check against mock libogc declarations (not a native SDK build)."
