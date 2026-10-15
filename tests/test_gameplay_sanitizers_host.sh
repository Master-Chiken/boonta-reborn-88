#!/bin/bash
# Optional deeper host validation of gameplay modules with ASan/UBSan.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CC_BIN="${CC:-cc}"
TMP="${TMPDIR:-/tmp}"
run_one() {
  name="$1"; shift
  bin="$TMP/swe1r_${name}_san_$$"
  trap 'rm -f "$bin"' RETURN
  "$CC_BIN" -std=c99 -Wall -Wextra -Werror -pedantic \
    -fsanitize=address,undefined -fno-omit-frame-pointer \
    -I"$ROOT/source" "$@" -lm -o "$bin"
  ASAN_OPTIONS=detect_leaks=0 "$bin"
  rm -f "$bin"
  trap - RETURN
}
run_one physics "$ROOT/source/racer_physics.c" "$ROOT/tests/test_racer_physics.c"
run_one finish_line_crossing "$ROOT/source/racer_physics.c" "$ROOT/tests/test_finish_line_crossing.c"
run_one track_projection "$ROOT/source/racer_physics.c" "$ROOT/tests/test_track_projection_continuity.c"
run_one track_lateral_boundary "$ROOT/source/racer_physics.c" "$ROOT/tests/test_track_lateral_boundary.c"
run_one collision_mesh "$ROOT/source/collision_mesh.c" "$ROOT/tests/test_collision_mesh.c"
run_one rival "$ROOT/source/racer_physics.c" "$ROOT/source/rival_ai.c" \
  "$ROOT/source/vehicle_catalog.c" "$ROOT/tests/test_rival_ai.c"
run_one track "$ROOT/source/track_catalog.c" "$ROOT/tests/test_track_catalog.c"
run_one vehicle "$ROOT/source/vehicle_catalog.c" "$ROOT/source/racer_physics.c" \
  "$ROOT/tests/test_vehicle_catalog.c"
run_one items "$ROOT/source/racer_physics.c" "$ROOT/source/track_catalog.c" "$ROOT/source/race_items.c" \
  "$ROOT/source/vehicle_catalog.c" "$ROOT/tests/test_race_items.c"
run_one race_feedback "$ROOT/source/racer_physics.c" "$ROOT/source/race_feedback.c" \
  "$ROOT/tests/test_race_feedback.c"
run_one race_flow "$ROOT/source/race_flow.c" "$ROOT/tests/test_race_flow.c"
run_one race_gate_geometry "$ROOT/source/race_gate_geometry.c" "$ROOT/tests/test_race_gate_geometry.c"
run_one voice_over_runtime "$ROOT/source/voice_over.c" "$ROOT/source/voice_over_runtime.c" \
  "$ROOT/tests/test_voice_over_runtime.c"
echo "PASS: gameplay modules run cleanly under AddressSanitizer and UndefinedBehaviorSanitizer."
