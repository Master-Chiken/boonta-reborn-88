#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${TMPDIR:-/tmp}/swe1r_vehicles_$$"
trap 'rm -f "$BIN"' EXIT
cc -std=c99 -Wall -Wextra -Werror -pedantic -I"$ROOT/source" \
  "$ROOT/source/vehicle_catalog.c" "$ROOT/source/racer_physics.c" \
  "$ROOT/tests/test_vehicle_catalog.c" -lm -o "$BIN"
"$BIN"
