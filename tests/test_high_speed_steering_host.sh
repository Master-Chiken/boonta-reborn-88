#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OUT="${TMPDIR:-/tmp}/swe1r_high_speed_steering_test"
${CC:-cc} -std=c99 -Wall -Wextra -Werror -pedantic -Isource tests/test_high_speed_steering.c source/racer_physics.c -lm -o "$OUT"
"$OUT"
rm -f "$OUT"
