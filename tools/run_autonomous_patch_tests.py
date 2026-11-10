#!/usr/bin/env python3
"""Run only repository-owned, fixed test commands named by a patch proposal.

No shell, free-form command, provider call, network request or GitHub mutation is
accepted. The registry is trusted repository code, not model-controlled input.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

TEST_REGISTRY: dict[str, tuple[str, ...]] = {
    "automation.task_preflight": ("tools/test_autonomous_task_preflight.py",),
    "automation.provider_handoff": ("tools/check_autonomous_provider_handoff.py",),
    "automation.task_ledger": ("tools/check_task_ledger.py",),
}
MAX_TESTS = 6
MAX_TEST_TIMEOUT_SECONDS = 120
MAX_OUTPUT_CHARS = 3000


class TestDispatchError(ValueError):
    """Raised when a test request is outside the repository-owned registry."""


def resolve_checkout(root: Path) -> Path:
    root = root.resolve()
    if not root.is_dir():
        raise TestDispatchError("Repository checkout does not exist")
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=root,
            stdin=subprocess.DEVNULL,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise TestDispatchError("Could not verify the Git checkout root") from exc
    if result.returncode != 0 or Path(result.stdout.strip()).resolve() != root:
        raise TestDispatchError("repo_root must be the exact Git checkout root")
    return root


def _test_environment() -> dict[str, str]:
    """Pass only standard execution variables; never forward provider/GitHub secrets."""
    keep = ("PATH", "HOME", "SYSTEMROOT", "WINDIR", "TMP", "TEMP", "TMPDIR")
    env = {key: os.environ[key] for key in keep if key in os.environ}
    env.update({"CI": "true", "PYTHONIOENCODING": "utf-8"})
    return env


def run_test_ids(
    root: Path,
    test_ids: list[str],
    *,
    timeout_seconds: int = MAX_TEST_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    if not isinstance(test_ids, list) or not 1 <= len(test_ids) <= MAX_TESTS:
        raise TestDispatchError("test_ids must contain between one and six identifiers")
    if any(not isinstance(item, str) for item in test_ids):
        raise TestDispatchError("Every test identifier must be a string")
    if len(set(test_ids)) != len(test_ids):
        raise TestDispatchError("Duplicate test identifiers are not allowed")
    unknown = [item for item in test_ids if item not in TEST_REGISTRY]
    if unknown:
        raise TestDispatchError("Unknown test identifier(s): " + ", ".join(map(str, unknown)))
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= MAX_TEST_TIMEOUT_SECONDS:
        raise TestDispatchError("Test timeout must be an integer between one and 120 seconds")

    root = resolve_checkout(root)
    env = _test_environment()
    results: list[dict[str, Any]] = []

    for test_id in test_ids:
        script = TEST_REGISTRY[test_id][0]
        script_path = root / script
        if script_path.is_symlink():
            raise TestDispatchError(f"Registered test script must not be a symlink: {script}")
        resolved_script = script_path.resolve()
        try:
            resolved_script.relative_to(root)
        except ValueError as exc:
            raise TestDispatchError(f"Registered test script escapes the checkout: {script}") from exc
        if not resolved_script.is_file():
            raise TestDispatchError(f"Registered test script is missing: {script}")
        parent = script_path.parent
        while parent != root:
            if parent.is_symlink():
                raise TestDispatchError(f"Registered test script has a symlink parent: {script}")
            parent = parent.parent
        started = time.monotonic()
        try:
            completed = subprocess.run(
                [sys.executable, script],
                cwd=root,
                env=env,
                stdin=subprocess.DEVNULL,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            results.append({
                "test_id": test_id,
                "status": "TIMEOUT",
                "duration_seconds": round(time.monotonic() - started, 3),
                "stdout": stdout[-MAX_OUTPUT_CHARS:],
                "stderr": stderr[-MAX_OUTPUT_CHARS:],
            })
            return {"status": "FAILED", "results": results, "stopped_after_first_failure": True}
        except OSError as exc:
            raise TestDispatchError(f"Could not start registered test {test_id}: {type(exc).__name__}") from exc

        status = "PASSED" if completed.returncode == 0 else "FAILED"
        results.append({
            "test_id": test_id,
            "status": status,
            "exit_code": completed.returncode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout": completed.stdout[-MAX_OUTPUT_CHARS:],
            "stderr": completed.stderr[-MAX_OUTPUT_CHARS:],
        })
        if completed.returncode != 0:
            return {"status": "FAILED", "results": results, "stopped_after_first_failure": True}

    return {"status": "PASSED", "results": results, "stopped_after_first_failure": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--test-id", action="append", choices=sorted(TEST_REGISTRY))
    parser.add_argument("--timeout-seconds", type=int, default=MAX_TEST_TIMEOUT_SECONDS)
    parser.add_argument("--list", action="store_true", help="list fixed test identifiers")
    args = parser.parse_args()

    if args.list:
        print(json.dumps({"test_ids": sorted(TEST_REGISTRY)}, sort_keys=True))
        return 0
    if args.repo_root is None or not args.test_id:
        parser.error("--repo-root and at least one --test-id are required")
    try:
        report = run_test_ids(args.repo_root, args.test_id, timeout_seconds=args.timeout_seconds)
    except TestDispatchError as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
