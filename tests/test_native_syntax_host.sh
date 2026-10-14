#!/bin/bash
# Syntax-check the native render code using local declarations that stand in for libogc.
# This catches C errors, but deliberately does not pretend to be a real devkitPPC link.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CC_BIN="${CC:-}"
if [ -z "$CC_BIN" ]; then
  if command -v clang >/dev/null 2>&1; then CC_BIN=clang; else CC_BIN=cc; fi
fi
"$CC_BIN" -std=gnu99 -Wall -Wextra -Werror -fsyntax-only \
  -I"$ROOT/tests/mockogc" -I"$ROOT/source" \
  "$ROOT/source/main.c" "$ROOT/source/race_gate_geometry.c" "$ROOT/source/pod_model.c" "$ROOT/source/collision_mesh.c" \
  "$ROOT/source/racer_physics.c" "$ROOT/source/race_flow.c" \
  "$ROOT/source/rival_ai.c" "$ROOT/source/draft_assist.c" "$ROOT/source/race_feedback.c" \
  "$ROOT/source/track_catalog.c" "$ROOT/source/track_direction.c" "$ROOT/source/vehicle_catalog.c" \
  "$ROOT/source/race_items.c" "$ROOT/source/career_save.c" "$ROOT/source/garage_progression.c" "$ROOT/source/garage_progression.c"
echo "PASS: native game sources pass C syntax checking (mock libogc declarations only)."
