#!/usr/bin/env python3
"""Prepare a bounded provider tool contract from trusted main and target checkouts."""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

from build_autonomous_path_allowlist import AllowlistError, build_allowlist, load_json
from validate_trusted_main_checkout import TrustedMainCheckoutError, validate_trusted_main_checkout

TASK_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,63}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPO_PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
MAX_READ_PATHS = 5
MAX_READ_RANGES = 10
MAX_RANGE_LINES = 80
MAX_TOTAL_LINES = 240
MAX_SOURCE_FILE_BYTES = 96 * 1024


class AgentInputError(ValueError):
    """Raised when a selected task cannot be turned into a bounded tool contract."""


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            stdin=subprocess.DEVNULL,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AgentInputError("Could not verify an exact source/policy Git checkout") from exc
    if result.returncode != 0:
        raise AgentInputError("Git checkout verification failed")
    return result.stdout.strip()


def _safe_repo_path(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value) > 120 or not REPO_PATH_RE.fullmatch(value):
        raise AgentInputError("Every read path must be a simple exact repository-relative path")
    if value.startswith("/") or "\\" in value:
        raise AgentInputError("Absolute read paths and backslashes are forbidden")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise AgentInputError("Read path traversal and ambiguous path components are forbidden")
    return value


def _validate_read_contract(
    source_root: Path,
    task: dict[str, Any],
) -> tuple[list[str], list[dict[str, int | str]]]:
    read_paths = task.get("read_paths")
    read_ranges = task.get("read_ranges")
    if (
        not isinstance(read_paths, list)
        or not 1 <= len(read_paths) <= MAX_READ_PATHS
        or any(not isinstance(item, str) for item in read_paths)
        or len(set(read_paths)) != len(read_paths)
    ):
        raise AgentInputError("Selected task must have 1-5 unique exact read_paths")
    read_paths = [_safe_repo_path(item) for item in read_paths]

    if not isinstance(read_ranges, list) or not 1 <= len(read_ranges) <= MAX_READ_RANGES:
        raise AgentInputError("Selected task must have 1-10 exact read_ranges")

    clean_ranges: list[dict[str, int | str]] = []
    total_lines = 0
    seen: set[tuple[str, int, int]] = set()
    covered: set[str] = set()
    for item in read_ranges:
        if not isinstance(item, dict) or set(item) != {"path", "start_line", "end_line"}:
            raise AgentInputError("Every read range must contain exactly path, start_line and end_line")
        path = item["path"]
        start = item["start_line"]
        end = item["end_line"]
        if (
            path not in read_paths
            or type(start) is not int
            or type(end) is not int
            or start < 1
            or end < start
            or end - start + 1 > MAX_RANGE_LINES
        ):
            raise AgentInputError("A read range is outside the task's exact bounded source contract")
        key = (path, start, end)
        if key in seen:
            raise AgentInputError("Task contains duplicate exact read ranges")
        seen.add(key)
        covered.add(path)
        total_lines += end - start + 1
        clean_ranges.append({"path": path, "start_line": start, "end_line": end})
    if covered != set(read_paths):
        raise AgentInputError("Every read path must have at least one exact read range")
    if total_lines > MAX_TOTAL_LINES:
        raise AgentInputError("Selected task source ranges exceed the 240-line aggregate cap")

    for item in read_paths:
        target = source_root / item
        # Resolve containment before walking parents. The path has already
        # rejected absolute roots, backslashes and dot/traversal components.
        try:
            target.resolve(strict=True).relative_to(source_root)
        except (OSError, ValueError) as exc:
            raise AgentInputError("Approved read path escapes the target checkout or is missing: " + item) from exc
        if target.is_symlink() or not target.is_file():
            raise AgentInputError("Approved read path is missing or not a regular file: " + item)
        if target.stat().st_size > MAX_SOURCE_FILE_BYTES:
            raise AgentInputError("Approved read path exceeds the 96 KiB cap: " + item)
        current = source_root
        for component in Path(item).parts[:-1]:
            current = current / component
            if current.is_symlink() or not current.is_dir():
                raise AgentInputError("Approved read path has a symlink or non-directory parent: " + item)
    return read_paths, clean_ranges


def prepare_agent_inputs(
    source_root: Path,
    policy_root: Path,
    *,
    expected_base_sha: str,
    expected_policy_sha: str,
    task_id: str,
    allowlist_output: Path,
) -> dict[str, Any]:
    source_root = source_root.resolve()
    policy_root = policy_root.resolve()
    if not TASK_ID_RE.fullmatch(task_id):
        raise AgentInputError("Selected task ID is invalid")
    if not SHA_RE.fullmatch(expected_base_sha) or not SHA_RE.fullmatch(expected_policy_sha):
        raise AgentInputError("Exact target and trusted policy SHAs are required")

    actual_base = _git(source_root, "rev-parse", "HEAD")
    if actual_base != expected_base_sha:
        raise AgentInputError("Target checkout HEAD differs from the selected task base SHA")
    actual_policy = _git(policy_root, "rev-parse", "HEAD")
    if actual_policy != expected_policy_sha:
        raise AgentInputError("Trusted main checkout HEAD differs from the policy SHA")
    if _git(source_root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise AgentInputError("Target source checkout must be clean before provider invocation")
    try:
        validate_trusted_main_checkout(policy_root, expected_policy_sha)
    except TrustedMainCheckoutError as exc:
        raise AgentInputError(str(exc)) from exc

    summary_path = policy_root / "docs/automation/task-ledger-summary.json"
    if summary_path.is_symlink() or not summary_path.is_file():
        raise AgentInputError("Trusted main compact task summary is missing or symlinked")
    summary = load_json(summary_path)
    if (
        not isinstance(summary, dict)
        or type(summary.get("schema_version")) is not int
        or summary.get("schema_version") != 2
        or summary.get("source") != "docs/automation/task-ledger.json"
        or not isinstance(summary.get("tasks"), list)
    ):
        raise AgentInputError("Trusted main compact task summary has an invalid schema")
    matches = [task for task in summary["tasks"] if isinstance(task, dict) and task.get("task_id") == task_id]
    if len(matches) != 1:
        raise AgentInputError("Selected task must appear exactly once in trusted main summary")
    task = matches[0]
    target_branch = task.get("target_branch")
    if target_branch not in {"main", "dev"}:
        raise AgentInputError("Selected task target branch must be main or dev")

    try:
        allowlist = build_allowlist(
            source_root,
            expected_base_sha=expected_base_sha,
            requested_task_id=task_id,
            policy_root=policy_root,
            expected_policy_sha=expected_policy_sha,
        )
    except AllowlistError as exc:
        raise AgentInputError("Owner path policy is not ready: " + str(exc)) from exc
    if allowlist.get("status") != "READY":
        raise AgentInputError(
            "Owner path policy is not READY (" + str(allowlist.get("status")) + "): " +
            str(allowlist.get("reason", "no owner-approved paths"))
        )

    read_paths, read_ranges = _validate_read_contract(source_root, task)
    unreadable_write_paths = sorted(set(allowlist.get("allowed_paths", [])) - set(read_paths))
    if unreadable_write_paths:
        raise AgentInputError(
            "Owner-approved write paths are not covered by the task's exact read_paths/read_ranges; "
            "no provider invocation is allowed until the owner-approved read contract is updated: " +
            ", ".join(unreadable_write_paths)
        )

    if allowlist_output.is_symlink() or allowlist_output.exists():
        raise AgentInputError("Allowlist report output must be a new non-symlink file")
    allowlist_output.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(allowlist_output, flags, stat.S_IRUSR | stat.S_IWUSR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(allowlist, ensure_ascii=False, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        allowlist_output.unlink(missing_ok=True)
        raise

    return {
        "schema_version": 1,
        "task_id": task_id,
        "target_branch": target_branch,
        "base_sha": expected_base_sha,
        "policy_sha": expected_policy_sha,
        "read_paths": read_paths,
        "read_ranges": read_ranges,
        "allowed_paths": allowlist["allowed_paths"],
        "approval_ref": allowlist["approval_ref"],
        "allowlist_report": str(allowlist_output.resolve()),
        "source_checkout_modified": False,
        "policy_checkout_modified": False,
        "model_has_github_write_tools": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--policy-root", type=Path, required=True)
    parser.add_argument("--expected-base-sha", required=True)
    parser.add_argument("--expected-policy-sha", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--allowlist-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = prepare_agent_inputs(
            args.source_root,
            args.policy_root,
            expected_base_sha=args.expected_base_sha,
            expected_policy_sha=args.expected_policy_sha,
            task_id=args.task_id,
            allowlist_output=args.allowlist_output,
        )
    except (AgentInputError, AllowlistError, OSError, ValueError) as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps({"status": "READY", **result}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
