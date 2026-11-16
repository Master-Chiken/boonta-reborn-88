#!/usr/bin/env python3
"""Prepare an exact-path model workspace and a separate trusted Git baseline.

The provider receives only the model workspace: it contains no .git metadata,
credentials or files outside the task's read-path list. Approved write files
are writable; all other files and all directories are read-only. The matching
Git baseline is stored elsewhere for trusted post-inference patch extraction.
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
        raise WorkspaceError("Git verification or trusted baseline setup failed") from exc
    if result.returncode != 0:
        raise WorkspaceError("Git command failed: " + " ".join(args[:2]))
    return result.stdout.strip()


def _remove_tree(path: Path) -> None:
    """Remove a partially-created tree even after its directories were locked."""
    if not path.exists() or path.is_symlink():
        return
    for current, dirs, files in os.walk(path, topdown=False, followlinks=False):
        current_path = Path(current)
        for filename in files:
            item = current_path / filename
            if item.is_symlink():
                item.unlink(missing_ok=True)
            else:
                try:
                    item.chmod(0o600)
                except OSError:
                    pass
        for dirname in dirs:
            item = current_path / dirname
            if item.is_symlink():
                item.unlink(missing_ok=True)
            else:
                try:
                    item.chmod(0o700)
                except OSError:
                    pass
        try:
            current_path.chmod(0o700)
        except OSError:
            pass
    shutil.rmtree(path, ignore_errors=True)


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
    if _git(root, ["status", "--porcelain=v1", "--untracked-files=all"]):
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


def _outside_roots(path: Path, roots: tuple[Path, ...]) -> None:
    for root in roots:
        try:
            path.relative_to(root)
        except ValueError:
            continue
        raise WorkspaceError("Scratch directories must be outside both trusted checkouts")


def prepare_workspace(
    *,
    policy_root: Path,
    policy_base_sha: str,
    source_root: Path,
    target_base_sha: str,
    task_id: str,
    target_branch: str,
    workspace: Path,
    baseline_root: Path,
) -> dict[str, Any]:
    """Validate policy/source checkouts; build a locked model view and private Git baseline."""
    if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
        raise WorkspaceError("Selected task ID is invalid")
    if target_branch not in {"main", "dev"}:
        raise WorkspaceError("Selected task target branch must be main or dev")

    policy_root = _validate_checkout(policy_root, policy_base_sha, "main")
    source_root = _validate_checkout(source_root, target_base_sha, target_branch)

    try:
        owner_scope = build_allowlist(
            source_root,
            expected_base_sha=target_base_sha,
            requested_task_id=task_id,
            policy_root=policy_root,
            policy_base_sha=policy_base_sha,
        )
    except AllowlistError as exc:
        raise WorkspaceError(f"Owner-reviewed exact write scope cannot be validated: {exc}") from exc
    if owner_scope.get("status") != "READY":
        raise WorkspaceError(
            "Owner-reviewed exact write scope is not READY: "
            + str(owner_scope.get("status", "UNKNOWN"))
        )

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
    task = matches[0]
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

    workspace_path = workspace.expanduser()
    baseline_path = baseline_root.expanduser()
    if workspace_path.exists() or workspace_path.is_symlink():
        raise WorkspaceError("Model workspace path must not already exist")
    if baseline_path.exists() or baseline_path.is_symlink():
        raise WorkspaceError("Trusted baseline path must not already exist")
    if workspace_path.absolute() == baseline_path.absolute():
        raise WorkspaceError("Model workspace and trusted baseline must be separate directories")
    try:
        workspace_parent = workspace_path.parent.resolve(strict=True)
        baseline_parent = baseline_path.parent.resolve(strict=True)
    except OSError as exc:
        raise WorkspaceError("Scratch directory parent must already exist") from exc
    workspace_path = workspace_parent / workspace_path.name
    baseline_path = baseline_parent / baseline_path.name
    _outside_roots(workspace_path, (policy_root, source_root))
    _outside_roots(baseline_path, (policy_root, source_root))
    try:
        workspace_path.relative_to(baseline_path)
        raise WorkspaceError("Model workspace must not be inside the trusted baseline")
    except ValueError:
        pass
    try:
        baseline_path.relative_to(workspace_path)
        raise WorkspaceError("Trusted baseline must not be inside the model workspace")
    except ValueError:
        pass

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

    workspace_created = False
    baseline_created = False
    try:
        baseline_path.mkdir(mode=0o700)
        baseline_created = True
        workspace_path.mkdir(mode=0o700)
        workspace_created = True

        # The trusted baseline is the only directory containing Git metadata.
        for relative, payload, mode in selected_files:
            target = baseline_path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            target.chmod(0o755 if mode == "100755" else 0o644)

        _git(baseline_path, ["init", "-q", "-b", "agent-work"])
        _git(baseline_path, ["config", "user.name", "Boonta Trusted Patch Baseline"])
        _git(baseline_path, ["config", "user.email", "boonta-baseline@example.invalid"])
        _git(baseline_path, ["config", "core.autocrlf", "false"])
        _git(baseline_path, ["add", "--", *read_paths])
        _git(baseline_path, ["commit", "-q", "-m", "Create trusted task patch baseline"])
        scratch_sha = _git(baseline_path, ["rev-parse", "HEAD"])
        if _git(baseline_path, ["status", "--porcelain=v1", "--untracked-files=all"]):
            raise WorkspaceError("Trusted baseline is not clean after its initial commit")

        # The model-facing directory contains only exact task source files and
        # no .git directory. Write paths are writable; context-only paths are
        # read-only. All directories are non-writable so the model cannot add
        # new files or directories through file tools.
        for relative, payload, _mode in selected_files:
            target = workspace_path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            target.chmod(0o644 if relative in allowed_paths else 0o444)

        directories = [
            Path(current)
            for current, dirs, _files in os.walk(workspace_path, topdown=True, followlinks=False)
            for _ in [0]
        ]
        for directory in sorted(directories, key=lambda item: len(item.parts), reverse=True):
            directory.chmod(0o555)
        workspace_path.chmod(0o555)

        actual_files: list[str] = []
        for current, dirs, files in os.walk(workspace_path, followlinks=False):
            for name in dirs:
                if (Path(current) / name).is_symlink():
                    raise WorkspaceError("Model workspace contains a symlink directory")
            for name in files:
                candidate = Path(current) / name
                if candidate.is_symlink() or not candidate.is_file():
                    raise WorkspaceError("Model workspace contains a non-regular file")
                actual_files.append(candidate.relative_to(workspace_path).as_posix())
        if sorted(actual_files) != sorted(read_paths):
            raise WorkspaceError("Model workspace inventory differs from the exact read-path allow-list")
        if (workspace_path / ".git").exists():
            raise WorkspaceError("Model workspace must not contain Git metadata")
    except Exception:
        if workspace_created:
            _remove_tree(workspace_path)
        if baseline_created:
            _remove_tree(baseline_path)
        raise

    return {
        "status": "READY",
        "task_id": task_id,
        "target_branch": target_branch,
        "policy_base_sha": policy_base_sha,
        "target_base_sha": target_base_sha,
        "scratch_base_sha": scratch_sha,
        "workspace": str(workspace_path),
        "baseline_root": str(baseline_path),
        "read_paths": read_paths,
        "allowed_write_paths": allowed_paths,
        "source_files": [
            {
                "path": relative,
                "bytes": len(payload),
                "mode": mode,
                "model_writable": relative in allowed_paths,
            }
            for relative, payload, mode in selected_files
        ],
        "git_metadata_exposed_to_model": False,
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
    parser.add_argument("--baseline-root", type=Path, required=True)
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
            baseline_root=args.baseline_root,
        )
    except (WorkspaceError, AllowlistError) as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
