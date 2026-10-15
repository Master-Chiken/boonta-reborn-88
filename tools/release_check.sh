#!/usr/bin/env bash
# Run the reproducible host-side checks; optionally build the native GameCube DOL.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
for test_script in tests/*_host.sh; do
  echo "==> ${test_script}"
  bash "$test_script"
done
python3 -m unittest discover -s tests -v
if [[ "${1:-}" == "--gamecube" ]]; then
  if [[ -z "${DEVKITPPC:-}" || ! -f "${DEVKITPPC}/gamecube_rules" ]]; then
    echo "ERROR: DEVKITPPC is unset or does not contain gamecube_rules." >&2
    echo "Install devkitPro with the GameCube/Wii toolchain, then export DEVKITPPC=/opt/devkitpro/devkitPPC." >&2
    exit 2
  fi
  python3 tools/native_build_status.py
  make clean
  make
  test -s swe1r_gc_port.dol
  echo "GameCube DOL built: $ROOT/swe1r_gc_port.dol"
else
  echo "HOST CHECKS PASS. For a native DOL build, rerun: $0 --gamecube"
fi
