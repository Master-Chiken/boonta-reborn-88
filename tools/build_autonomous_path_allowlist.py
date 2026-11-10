#!/usr/bin/env python3
"""Build the owner-approved exact-path allowlist for one active task.

The model never chooses paths. A reviewed repository policy maps an exact task
ID to exact, pre-existing tracked files. No network or GitHub API access.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = Path("docs/automation/task-ledger-summary.json")
DEFAULT_POLICY = Path("docs/automation/patch-path-allowlist.json")
TASK_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,63}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
MAX_PATHS = 20
PROTECTED_EXACT = {
    ".gitignore",
    ".gitattributes",
    ".gitmodules",
    "AGENTS.md",
    "CODEOWNERS",
    ".github/CODEOWNERS",
    "docs/automation/task-ledger.json",
    "docs/automation/task-ledger-summary.json",
    "docs/automation/patch-path-allowlist.json",
    "tools/autonomous_patch_proposal.py",
    "tools/build_autonomous_path_allowlist.py",
    "tools/run_autonomous_patch_tests.py",
    "tools/test_autonomous_patch_proposal.py",
    "tools/test_autonomous_patch_test_runner.py",
    "tools/test_autonomous_path_allowlist.py",
    "tools/test_autonomous_task_preflight.py",
    "tools/check_autonomous_provider_handoff.py",
    "tools/check_task_ledger.py",
}
PROTECTED_PREFIXES = (".github/", ".git/")


class AllowlistError(ValueError):
    """Raised when trusted task/path inputs cannot be proven safe."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise AllowlistError(f"Duplicate JSON property: {key}")
        value[key] = item
    return value


def load_json(path: Path) -> Any:
    try:
        raw = path.read_text(encoding="utf-8")
        return json.loads(raw, object_pairs_hook=_unique_object)
    except AllowlistError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AllowlistError(f"Cannot read valid UTF-8 JSON from {path}") from exc


def _git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            stdin=subprocess.DEVNULL,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AllowlistError("Git verification could not be completed") from exc


def _safe_path(value: Any) -> str:
    if not isinstance(value, str) or not value or not PATH_RE.fullmatch(value):
        raise AllowlistError("Every approved path must use a simple exact repository-relative path")
    if value.startswith("/") or "\\" in value:
        raise AllowlistError("Absolute paths and backslashes are forbidden")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise AllowlistError("Path traversal and ambiguous path components are forbidden")
    if (
        value in PROTECTED_EXACT
        or any(value.startswith(prefix) for prefix in PROTECTED_PREFIXES)
        or value.lower().startswith(".env")
        or value.lower().endswith((".pem", ".key", ".p12", ".pfx"))
        or any(part.lower() in {"secrets", "credentials"} for part in parts)
    ):
        raise AllowlistError(f"Path is protected and cannot be approved for model writes: {value}")
    return value


def _verify_checkout(root: Path, expected_base_sha: str) -> Path:
    root = root.resolve()
    if not root.is_dir():
        raise AllowlistError("Repository checkout does not exist")
    if not SHA_RE.fullmatch(expected_base_sha):
        raise AllowlistError("expected_base_sha must be a lowercase 40-character SHA")
    top = _git(root, ["rev-parse", "--show-toplevel"])
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != root:
        raise AllowlistError("repo_root must be the exact Git checkout root")
    head = _git(root, ["rev-parse", "HEAD"])
    if head.returncode != 0 or head.stdout.strip() != expected_base_sha:
        raise AllowlistError("Checkout HEAD differs from the trusted preflight base SHA")
    status = _git(root, ["status", "--porcelain=v1", "--untracked-files=all"])
    if status.returncode != 0 or status.stdout.strip():
        raise AllowlistError("Checkout must be clean before building an autonomous path allowlist")
    return root


def _validate_tracked_regular_file(root: Path, path: str) -> None:
    indexed = _git(root, ["ls-files", "-s", "--", path])
    if indexed.returncode != 0:
        raise AllowlistError("Could not inspect Git index for approved path")
    entries = [line for line in indexed.stdout.splitlines() if line.strip()]
    if len(entries) != 1:
        raise AllowlistError(f"Approved path must identify exactly one tracked file: {path}")
    mode = entries[0].split(None, 1)[0]
    if mode not in {"100644", "100755"}:
        raise AllowlistError(f"Approved path is not a regular tracked file: {path}")
    target = root / path
    if target.is_symlink() or not target.is_file():
        raise AllowlistError(f"Approved path is not a regular file: {path}")
    parent = target.parent
    while parent != root:
        if parent.is_symlink():
            raise AllowlistError(f"Approved path contains a symlink parent: {path}")
        parent = parent.parent


def build_allowlist(
    root: Path,
    *,
    expected_base_sha: str,
    requested_task_id: str,
    ledger_path: Path = DEFAULT_LEDGER,
    policy_path: Path = DEFAULT_POLICY,
) -> dict[str, Any]:
    if not isinstance(requested_task_id, str) or not TASK_ID_RE.fullmatch(requested_task_id):
        raise AllowlistError("Requested task ID is invalid")
    root = _verify_checkout(root, expected_base_sha)
    ledger_file = root / ledger_path
    policy_file = root / policy_path
    if ledger_file.is_symlink() or policy_file.is_symlink():
        raise AllowlistError("Ledger and path policy must not be symlinks")

    ledger = load_json(ledger_file)
    policy = load_json(policy_file)
    if not isinstance(ledger, dict) or ledger.get("schema_version") != 2:
        raise AllowlistError("Canonical task summary must use schema version 2")
    if not isinstance(ledger.get("tasks"), list):
        raise AllowlistError("Canonical task summary tasks must be an array")
    if not isinstance(policy, dict) or set(policy) != {"schema_version", "policy", "tasks"}:
        raise AllowlistError("Path policy must contain exactly schema_version, policy and tasks")
    if type(policy.get("schema_version")) is not int or policy["schema_version"] != 1:
        raise AllowlistError("Path policy schema_version must equal integer 1")
    policy_meta = policy.get("policy")
    if not isinstance(policy_meta, dict):
        raise AllowlistError("Path policy metadata must be an object")
    if policy_meta.get("owner_review_required") is not True or policy_meta.get("path_mode") != "exact":
        raise AllowlistError("Path policy must require owner review and exact-file paths")
    if policy_meta.get("max_paths_per_task") != MAX_PATHS:
        raise AllowlistError(f"Path policy max_paths_per_task must equal {MAX_PATHS}")
    entries = policy.get("tasks")
    if not isinstance(entries, list):
        raise AllowlistError("Path policy tasks must be an array")

    task_map: dict[str, dict[str, Any]] = {}
    for item in ledger["tasks"]:
        if not isinstance(item, dict):
            raise AllowlistError("Every canonical task entry must be an object")
        task_id = item.get("task_id")
        if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
            raise AllowlistError("Canonical task contains an invalid ID")
        if task_id in task_map:
            raise AllowlistError(f"Canonical ledger has duplicate task ID: {task_id}")
        task_map[task_id] = item
    active = [item for item in task_map.values() if item.get("status") == "active"]
    if len(active) > 1:
        raise AllowlistError("Canonical ledger violates the one-active-task policy")
    if not active:
        return {
            "status": "NO_ACTIVE_TASK",
            "task_id": requested_task_id,
            "base_sha": expected_base_sha,
            "allowed_paths": [],
            "reason": "No canonical task is active; no model write path is available.",
        }
    selected = active[0]
    if selected.get("task_id") != requested_task_id:
        raise AllowlistError("Requested task ID does not match the unique canonical active task")

    policy_map: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"task_id", "purpose", "approval_ref", "allowed_paths"}:
            raise AllowlistError("Each path-policy task must contain exactly task_id, purpose, approval_ref and allowed_paths")
        task_id = entry["task_id"]
        if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
            raise AllowlistError("Path policy contains an invalid task ID")
        if task_id in policy_map:
            raise AllowlistError(f"Path policy contains duplicate task ID: {task_id}")
        if task_id not in task_map:
            raise AllowlistError(f"Path policy refers to an unknown canonical task: {task_id}")
        purpose = entry["purpose"]
        approval_ref = entry["approval_ref"]
        if not isinstance(purpose, str) or not purpose.strip() or len(purpose) > 240:
            raise AllowlistError(f"Path policy purpose must be a short explanation: {task_id}")
        if (
            not isinstance(approval_ref, str)
            or not approval_ref.startswith("https://github.com/Master-Chiken/boonta-reborn-88/")
        ):
            raise AllowlistError(f"Path policy requires an owner-review evidence URL: {task_id}")
        paths = entry["allowed_paths"]
        if not isinstance(paths, list) or not 1 <= len(paths) <= MAX_PATHS:
            raise AllowlistError(f"Task must have between one and {MAX_PATHS} exact allowed paths: {task_id}")
        checked = [_safe_path(path) for path in paths]
        if len(set(checked)) != len(checked):
            raise AllowlistError(f"Path policy contains duplicate paths for task: {task_id}")
        policy_map[task_id] = {**entry, "allowed_paths": checked}

    owner_entry = policy_map.get(requested_task_id)
    if owner_entry is None:
        return {
            "status": "WAITING_FOR_OWNER_APPROVED_PATHS",
            "task_id": requested_task_id,
            "base_sha": expected_base_sha,
            "allowed_paths": [],
            "reason": "The active task has no owner-reviewed exact-path entry.",
        }
    for path in owner_entry["allowed_paths"]:
        _validate_tracked_regular_file(root, path)

    return {
        "status": "READY",
        "task_id": requested_task_id,
        "base_sha": expected_base_sha,
        "approval_ref": owner_entry["approval_ref"],
        "purpose": owner_entry["purpose"],
        "allowed_paths": owner_entry["allowed_paths"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--expected-base-sha", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args()
    try:
        report = build_allowlist(
            args.repo_root,
            expected_base_sha=args.expected_base_sha,
            requested_task_id=args.task_id,
            ledger_path=args.ledger,
            policy_path=args.policy,
        )
    except AllowlistError as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "READY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
