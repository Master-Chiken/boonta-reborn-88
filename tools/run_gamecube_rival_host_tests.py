#!/usr/bin/env python3
"""Run the fixed GameCube/Wii rival-progress host regression suite.

This is a repository-owned test profile: callers cannot select commands, source
paths, compiler flags or output paths. Build products stay in a temporary folder.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

TESTS = (
    ("test_rival_ai", "gamecube-demo/tests/test_rival_ai.c", True),
    ("test_route_cursor", "gamecube-demo/tests/test_route_cursor.c", True),
    ("test_gameplay_state", "gamecube-demo/tests/test_gameplay_state.c", True),
)
TIMEOUT_SECONDS = 30
OUTPUT_LIMIT = 4000


def run(command: list[str], *, cwd: Path, env: dict[str, str]) -> tuple[int, str]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return 124, (stdout + "\n" + stderr)[-OUTPUT_LIMIT:]
    except OSError as exc:
        return 127, f"could not start fixed host-test command: {type(exc).__name__}"
    output = (result.stdout + "\n" + result.stderr)[-OUTPUT_LIMIT:]
    return result.returncode, output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.source_root.resolve()
    try:
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=root,
            stdin=subprocess.DEVNULL,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        print("Could not verify the GameCube target checkout root.")
        return 2
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != root:
        print("GameCube host tests require the exact target Git checkout root.")
        return 2
    if not root.is_dir():
        print("GameCube host test target root is unavailable.")
        return 2

    env = {
        key: os.environ[key]
        for key in ("PATH", "HOME", "SYSTEMROOT", "WINDIR", "TMP", "TEMP", "TMPDIR")
        if key in os.environ
    }
    env.update({"CI": "true", "LC_ALL": "C"})

    with tempfile.TemporaryDirectory(prefix="boonta-gamecube-host-tests-") as temp:
        output_root = Path(temp)
        for name, source, link_math in TESTS:
            source_path = root / source
            if source_path.is_symlink() or not source_path.is_file():
                print(f"REJECTED: fixed host test source is missing or symlinked: {source}")
                return 2
            output = output_root / name
            compile_command = [
                "cc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-pedantic",
                str(source_path), "-o", str(output),
            ]
            if link_math:
                compile_command.append("-lm")
            code, detail = run(compile_command, cwd=root, env=env)
            if code != 0:
                print(f"FAILED: compile {source} (exit {code})")
                print(detail)
                return 1

            code, detail = run([str(output)], cwd=root, env=env)
            if code != 0:
                print(f"FAILED: execute {name} (exit {code})")
                print(detail)
                return 1
            print(f"PASS: {name}")
            if detail.strip():
                print(detail)

    print(f"GameCube/Wii rival host profile passed: {len(TESTS)} fixed C suites.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
