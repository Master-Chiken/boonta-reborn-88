#!/usr/bin/env python3
"""Prepare a disposable, path-scoped workspace for one autonomous patch.

The provider receives only this scratch directory, never the repository checkout
or a GitHub credential. The model's editable paths must be a subset of the
owner-approved exact write allow-list; all other copied files are read-only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

from build_autonomous_path_allowlist import AllowlistError, build_allowlist

TASK_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,63}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
READ_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".json", ".yaml", ".yml", ".toml",
    ".md", ".c", ".h", ".cc", ".cpp", ".hpp", ".cmake", ".sh",
}
READ_BLOCKED_COMPONENTS = {"generated", "roms", "private"}
MAX_READ_PATHS = 4
MAX_FILE_BYTES = 96 * 1024
MAX_TOTAL_BYTES = 256 * 1024


class WorkspaceError(ValueError):
    """Raised when a safe, task-scoped scratch workspace cannot be proven."""


def _git_env() -> dict[str, str]:
    """Do not forward provider or GitHub credentials into local Git commands."""
    keep = ("PATH", "HOME", "SYSTEMROOT", "WINDIR", "TMP", "TEMP", "TMPDIR")
    env = {key: os.environ[key] for key in keep if key in os.environ}
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
    })
    return env


def _git(root: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            env=_git_env(),
            stdin=subprocess.DEVNULL,
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WorkspaceError("Git verification or scratch repository setup failed") from exc
    if result.returncode != 0:
        raise WorkspaceError("Git command failed: " + " ".join(args[:2]))
    return result.stdout.strip()


def _validate_checkout(root: Path, expected_sha: str, expected_branch: str) -> Path:
    if not isinstance(expected_sha, str) or not SHA_RE.fullmatch(expected_sha):
        raise WorkspaceError("Expected checkout SHA must be a lowercase 40-character commit")
    if expected_branch not in {"main", "dev"}:
        raise WorkspaceError("Expected checkout branch must be main or dev")
    try:
        root = root.resolve(strict=True)
    except OSError as exc:
        raise WorkspaceError("Checkout directory does not exist") from exc
    if not root.is_dir():
        raise WorkspaceError("Checkout path is not a directory")
    top = _git(root, ["rev-parse", "--show-toplevel"])
    if Path(top).resolve() != root:
        raise WorkspaceError("Checkout path must be the exact Git repository root")
    head = _git(root, ["rev-parse", "HEAD"])
    if head != expected_sha:
        raise WorkspaceError("Checkout HEAD differs from the trusted preflight SHA")
    branch = _git(root, ["branch", "--show-current"])
    if branch and branch != expected_branch:
        raise WorkspaceError("Checkout branch differs from the trusted task target branch")
    status = _git(root, ["status", "--porcelain=v1", "--untracked-files=all"])
    if status:
        raise WorkspaceError("Checkout must be clean before scratch workspace preparation")
    return root


def _safe_read_path(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value) > 120:
        raise WorkspaceError("Every task read path must be a short repository-relative string")
    if not PATH_RE.fullmatch(value) or value.startswith("/") or "\\" in value:
        raise WorkspaceError("Task read path contains unsupported or absolute path syntax")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise WorkspaceError("Task read path contains traversal or ambiguous components")
    if value in {
        "docs/automation/task-ledger.json",
        "docs/automation/task-ledger-summary.json",
    } or any(part.lower() in READ_BLOCKED_COMPONENTS for part in parts):
        raise WorkspaceError("Task read path is excluded by repository provenance policy")
    if Path(value).suffix.lower() not in READ_EXTENSIONS:
        raise WorkspaceError("Task read path is not an approved UTF-8 source/document extension")
    return value


def _tracked_regular_file(root: Path, relative: str) -> tuple[Path, str]:
    indexed = _git(root, ["ls-files", "-s", "--", relative])
    entries = [line for line in indexed.splitlines() if line.strip()]
    if len(entries) != 1:
        raise WorkspaceError(f"Exact source path is not one tracked file: {relative}")
    mode = entries[0].split(None, 1)[0]
    if mode not in {"100644", "100755"}:
        raise WorkspaceError(f"Exact source path is not a regular tracked file: {relative}")
    candidate = root / relative
    if candidate.is_symlink():
        raise WorkspaceError(f"Exact source path must not be a symlink: {relative}")
    parent = candidate.parent
    while parent != root:
        if parent.is_symlink():
            raise WorkspaceError(f"Exact source path has a symlink parent: {relative}")
        parent = parent.parent
    try:
        info = candidate.lstat()
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise WorkspaceError(f"Exact source path is missing or escapes the checkout: {relative}") from exc
    if not stat.S_ISREG(info.st_mode) or not resolved.is_file():
        raise WorkspaceError(f"Exact source path is not a regular file: {relative}")
    return resolved, mode


def _load_selected_task(policy_root: Path, task_id: str) -> dict[str, Any]:
    summary_path = policy_root / "docs/automation/task-ledger-summary.json"
    if summary_path.is_symlink() or not summary_path.is_file():
        raise WorkspaceError("Canonical compact task summary is missing or unsafe")
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WorkspaceError("Canonical compact task summary is not valid UTF-8 JSON") from exc
    if (
        not isinstance(summary, dict)
        or summary.get("schema_version") != 2
        or summary.get("source") != "docs/automation/task-ledger.json"
        or not isinstance(summary.get("tasks"), list)
    ):
        raise WorkspaceError("Canonical compact task summary schema is invalid")
    matches = [
        task for task in summary["tasks"]
        if isinstance(task, dict) and task.get("task_id") == task_id
    ]
    if len(matches) != 1:
        raise WorkspaceError("Selected task is missing or duplicated in the canonical compact summary")
    return matches[0]


def prepare_workspace(
    *,
    policy_root: Path,
    policy_base_sha: str,
    source_root: Path,
    target_base_sha: str,
    task_id: str,
    target_branch: str,
    workspace: Path,
) -> dict[str, Any]:
    """Validate policy and source checkouts, then copy only exact read paths."""
    if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
        raise WorkspaceError("Selected task ID is invalid")
    if target_branch not in {"main", "dev"}:
        raise WorkspaceError("Selected task target branch must be main or dev")

    policy_root = _validate_checkout(policy_root, policy_base_sha, "main")
    source_root = _validate_checkout(source_root, target_base_sha, target_branch)
    if policy_root == source_root:
        # Main tasks legitimately use the same checkout for policy and source.
        pass

    try:
        owner_scope = build_allowlist(
            policy_root,
            expected_base_sha=policy_base_sha,
            requested_task_id=task_id,
        )
    except AllowlistError as exc:
        raise WorkspaceError(f"Owner-reviewed exact write scope cannot be validated: {exc}") from exc
    if owner_scope.get("status") != "READY":
        raise WorkspaceError(
            "Owner-reviewed exact write scope is not READY: "
            + str(owner_scope.get("status", "UNKNOWN"))
        )

    task = _load_selected_task(policy_root, task_id)
    if task.get("target_branch") != target_branch:
        raise WorkspaceError("Selected target branch differs from the canonical task summary")
    read_values = task.get("read_paths")
    if not isinstance(read_values, list) or not 1 <= len(read_values) <= MAX_READ_PATHS:
        raise WorkspaceError(f"Selected task must declare 1-{MAX_READ_PATHS} exact read paths")
    read_paths = [_safe_read_path(item) for item in read_values]
    if len(set(read_paths)) != len(read_paths):
        raise WorkspaceError("Selected task read paths contain duplicates")

    allowed_paths = owner_scope.get("allowed_paths")
    if (
        not isinstance(allowed_paths, list)
        or not allowed_paths
        or len(set(allowed_paths)) != len(allowed_paths)
        or not all(isinstance(item, str) for item in allowed_paths)
    ):
        raise WorkspaceError("Owner-reviewed exact write path list is malformed")
    if not set(allowed_paths).issubset(set(read_paths)):
        missing = sorted(set(allowed_paths) - set(read_paths))
        raise WorkspaceError(
            "Every owner-approved write path must also be in the exact task read allow-list; "
            "missing: " + ", ".join(missing)
        )

    destination = workspace.expanduser()
    if destination.exists() or destination.is_symlink():
        raise WorkspaceError("Scratch workspace path must not already exist")
    destination_parent = destination.parent.resolve(strict=True)
    destination = destination_parent / destination.name
    for root in (policy_root, source_root):
        try:
            destination.relative_to(root)
        except ValueError:
            pass
        else:
            raise WorkspaceError("Scratch workspace must be outside both trusted checkouts")
    if destination == Path(destination.anchor):
        raise WorkspaceError("Scratch workspace path is invalid")

    selected_files: list[tuple[str, bytes, str]] = []
    total_bytes = 0
    for relative in read_paths:
        source_file, mode = _tracked_regular_file(source_root, relative)
        try:
            payload = source_file.read_bytes()
            payload.decode("utf-8", errors="strict")
        except (OSError, UnicodeError) as exc:
            raise WorkspaceError(f"Task read source is not readable UTF-8 text: {relative}") from exc
        if b"\x00" in payload or len(payload) > MAX_FILE_BYTES:
            raise WorkspaceError(f"Task read source exceeds the bounded text-file policy: {relative}")
        total_bytes += len(payload)
        if total_bytes > MAX_TOTAL_BYTES:
            raise WorkspaceError("Task read sources exceed the 256 KiB aggregate budget")
        selected_files.append((relative, payload, mode))

    created = False
    try:
        destination.mkdir(mode=0o700)
        created = True
        for relative, payload, mode in selected_files:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_symlink():
                raise WorkspaceError(f"Scratch target unexpectedly became a symlink: {relative}")
            target.write_bytes(payload)
            target.chmod(0o755 if mode == "100755" else 0o644)

        _git(destination, ["init", "-q", "-b", "agent-work"])
        _git(destination, ["config", "user.name", "Boonta Autonomous Workspace"])
        _git(destination, ["config", "user.email", "boonta-workspace@example.invalid"])
        _git(destination, ["config", "core.autocrlf", "false"])
        _git(destination, ["add", "--", *read_paths])
        _git(destination, ["commit", "-q", "-m", "Create isolated task source workspace"])
        scratch_sha = _git(destination, ["rev-parse", "HEAD"])
        tracked = _git(destination, ["ls-files", "-z"]).split("\x00")
        tracked = sorted(item for item in tracked if item)
        if tracked != sorted(read_paths):
            raise WorkspaceError("Scratch repository contains files outside the exact read-path list")
        if _git(destination, ["status", "--porcelain=v1", "--untracked-files=all"]):
            raise WorkspaceError("Scratch repository is not clean after its baseline commit")
    except Exception:
        if created and destination.exists() and not destination.is_symlink():
            shutil.rmtree(destination, ignore_errors=True)
        raise

    return {
        "status": "READY",
        "task_id": task_id,
        "target_branch": target_branch,
        "policy_base_sha": policy_base_sha,
        "target_base_sha": target_base_sha,
        "scratch_base_sha": scratch_sha,
        "workspace": str(destination),
        "read_paths": read_paths,
        "allowed_write_paths": allowed_paths,
        "source_files": [
            {"path": relative, "bytes": len(payload), "mode": mode}
            for relative, payload, mode in selected_files
        ],
        "github_credentials_copied": False,
        "repository_metadata_copied": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy-root", type=Path, required=True)
    parser.add_argument("--policy-base-sha", required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--target-base-sha", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--target-branch", required=True, choices=("main", "dev"))
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()

    try:
        report = prepare_workspace(
            policy_root=args.policy_root,
            policy_base_sha=args.policy_base_sha,
            source_root=args.source_root,
            target_base_sha=args.target_base_sha,
            task_id=args.task_id,
            target_branch=args.target_branch,
            workspace=args.workspace,
        )
    except (WorkspaceError, AllowlistError) as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
