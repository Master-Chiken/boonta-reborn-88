#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${TMPDIR:-/tmp}/swe1r_collision_mesh_tests_$$"
trap 'rm -f "$BIN"' EXIT
cc -std=c99 -Wall -Wextra -Werror -pedantic -Isource \
  "$ROOT/source/collision_mesh.c" "$ROOT/tests/test_collision_mesh.c" -o "$BIN"
"$BIN"
