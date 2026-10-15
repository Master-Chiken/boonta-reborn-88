#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MAIN="$ROOT/source/main.c"
grep -q '#define OPPONENT_COUNT 7U' "$MAIN"
grep -q '"RIVAL 4", "RIVAL 5", "RIVAL 6", "RIVAL 7"' "$MAIN"
grep -q 'race_racer_label(winner)' "$MAIN"
grep -q 'race_racer_label(racer)' "$MAIN"
grep -q '"YOU %u PTS  LEADER %u"' "$MAIN"
if grep -q 'winner == 2U ? "RIVAL 2" : "RIVAL 3"' "$MAIN"; then
  echo 'Old four-racer-only champion label logic remains.' >&2
  exit 1
fi
echo 'Eight-racer championship UI checks passed.'
