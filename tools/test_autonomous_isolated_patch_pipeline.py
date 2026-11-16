#!/usr/bin/env python3
"""Run the complete trusted isolated-workspace security regression suite.

This file is the single fixed dispatcher entry used by autonomous patch
verification. It invokes only two repository-owned test modules, without a
shell and with a bounded timeout; no model-provided command is accepted.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = (
    "tools/test_prepare_autonomous_patch_workspace.py",
    "tools/test_build_autonomous_patch_proposal.py",
)
TIMEOUT_SECONDS = 120
MAX_OUTPUT_CHARS = 5000


def main() -> int:
    env = {
        key: os.environ[key]
        for key in ("PATH", "HOME", "SYSTEMROOT", "WINDIR", "TMP", "TEMP", "TMPDIR")
        if key in os.environ
    }
    env.update({"CI": "true", "PYTHONIOENCODING": "utf-8"})
    for script in TESTS:
        path = ROOT / script
        if path.is_symlink() or not path.is_file():
            print(f"FAIL: registered isolated-pipeline test is missing or unsafe: {script}", file=sys.stderr)
            return 2
        try:
            result = subprocess.run(
                [sys.executable, script],
                cwd=ROOT,
                env=env,
                stdin=subprocess.DEVNULL,
                text=True,
                capture_output=True,
                check=False,
                timeout=TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f"FAIL: isolated-pipeline test could not complete: {script}: {type(exc).__name__}", file=sys.stderr)
            return 2
        if result.stdout:
            print(result.stdout[-MAX_OUTPUT_CHARS:], end="")
        if result.stderr:
            print(result.stderr[-MAX_OUTPUT_CHARS:], file=sys.stderr, end="")
        if result.returncode != 0:
            print(f"FAIL: isolated-pipeline test failed: {script}", file=sys.stderr)
            return result.returncode or 1
    print("PASS: all disposable exact-path workspace and patch-export security tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
