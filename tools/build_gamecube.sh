#!/usr/bin/env bash
# Reproducible native GameCube build gate. This does not fabricate a DOL.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODE="${1:-build}"

if [[ "$MODE" != "build" && "$MODE" != "--check-only" ]]; then
  echo "Usage: $0 [--check-only]" >&2
  exit 64
fi

if [[ -z "${DEVKITPPC:-}" ]]; then
  cat >&2 <<'MSG'
ERROR: DEVKITPPC is not set.
Install the devkitPro GameCube/Wii toolchain (devkitPPC + libogc), then set:
  export DEVKITPRO=/opt/devkitpro
  export DEVKITPPC="$DEVKITPRO/devkitPPC"
The exact install path may differ on your computer. See docs/FIRST_BUILD_TEST.md.
MSG
  exit 2
fi

if [[ ! -f "$DEVKITPPC/gamecube_rules" ]]; then
  echo "ERROR: $DEVKITPPC/gamecube_rules was not found; DEVKITPPC is not a valid GameCube toolchain path." >&2
  exit 2
fi

COMPILER=""
for candidate in "$DEVKITPPC/bin/powerpc-eabi-gcc" "$DEVKITPPC/bin/powerpc-gekko-gcc"; do
  if [[ -x "$candidate" ]]; then COMPILER="$candidate"; break; fi
done
if [[ -z "$COMPILER" ]]; then
  COMPILER="$(command -v powerpc-eabi-gcc || command -v powerpc-gekko-gcc || true)"
fi
if [[ -z "$COMPILER" ]]; then
  echo "ERROR: GameCube PowerPC compiler not found in DEVKITPPC/bin or PATH." >&2
  exit 2
fi
if ! command -v make >/dev/null 2>&1; then
  echo "ERROR: make is required to build the project." >&2
  exit 2
fi

printf 'GameCube toolchain preflight passed.\nDEVKITPPC=%s\nCompiler=%s\n' "$DEVKITPPC" "$COMPILER"
cd "$ROOT"
python3 tools/check_native_project.py
if ! python3 tools/native_build_status.py --root "$ROOT"; then
  echo "ERROR: native SDK preflight did not pass. Review build/native-build-report.txt." >&2
  exit 2
fi
if [[ "$MODE" == "--check-only" ]]; then exit 0; fi

mkdir -p build
LOG="$ROOT/build/gamecube-build.log"
set +e
{ make clean && make; } 2>&1 | tee "$LOG"
STATUS=${PIPESTATUS[0]}
set -e
if [[ $STATUS -ne 0 ]]; then
  echo "ERROR: native build failed (exit $STATUS). Log: $LOG" >&2
  exit "$STATUS"
fi
if [[ ! -s "$ROOT/swe1r_gc_port.dol" ]]; then
  echo "ERROR: make returned success but swe1r_gc_port.dol is missing or empty." >&2
  exit 3
fi
printf '\nNative DOL created: %s\nBuild log: %s\n' "$ROOT/swe1r_gc_port.dol" "$LOG"
echo "This confirms compilation only; emulator/Nintendont runtime testing is still required."
