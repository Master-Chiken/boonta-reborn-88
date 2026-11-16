#!/usr/bin/env python3
"""Export a locked model workspace as a trusted structured patch proposal.

The model workspace has no Git metadata and contains only exact read paths.
This trusted post-inference step compares every file with a separate baseline,
rejects edits to read-only context files and copies only owner-approved edits
into the private baseline repository before constructing a unified diff.
"""
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

from autonomous_patch_proposal import (
    ProposalError,
    validate_proposal,
    validate_tracked_targets,
)

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TASK_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,63}$")
PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
READ_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".json", ".yaml", ".yml", ".toml",
    ".md", ".c", ".h", ".cc", ".cpp", ".hpp", ".cmake", ".sh",
}
MAX_READ_PATHS = 4
MAX_FILE_BYTES = 96 * 1024
MAX_TOTAL_BYTES = 256 * 1024
MAX_DIFF_BYTES = 32 * 1024
MAX_PROPOSAL_BYTES = 96 * 1024
MAX_FILES = 5


class PatchBuildError(ValueError):
    """Raised when the model workspace cannot become a safe patch proposal."""


def _git_env() -> dict[str, str]:
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
        raise PatchBuildError("Git could not inspect the private patch baseline") from exc
    if result.returncode != 0:
        raise PatchBuildError("Git command failed: " + " ".join(args[:3]))
    return result.stdout


def _safe_relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value) > 120:
        raise PatchBuildError("Every exact source path must be a short repository-relative string")
    if not PATH_RE.fullmatch(value) or value.startswith("/") or "\\" in value:
        raise PatchBuildError("Source path contains unsupported or absolute path syntax")
    if any(part in {"", ".", ".."} for part in value.split("/")):
        raise PatchBuildError("Source path contains traversal or ambiguous components")
    if Path(value).suffix.lower() not in READ_EXTENSIONS:
        raise PatchBuildError("Source path has an unsupported text-file extension")
    return value


def _workspace_inventory(root: Path, read_paths: list[str]) -> list[tuple[str, bytes]]:
    expected = set(read_paths)
    actual: list[str] = []
    expected_directories: set[str] = set()
    total_bytes = 0

    for relative in read_paths:
        parts = relative.split("/")[:-1]
        for index in range(1, len(parts) + 1):
            expected_directories.add("/".join(parts[:index]))

    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        for directory in dirs:
            candidate = current_path / directory
            if candidate.is_symlink():
                raise PatchBuildError("Model workspace contains a symlink directory")
            relative = candidate.relative_to(root).as_posix()
            if relative not in expected_directories:
                raise PatchBuildError("Model created a directory outside the exact read-path tree")
            if candidate.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
                raise PatchBuildError("Model workspace directories must remain non-writable")
        for filename in files:
            candidate = current_path / filename
            if candidate.is_symlink() or not candidate.is_file():
                raise PatchBuildError("Model workspace contains a non-regular file or symlink")
            relative = candidate.relative_to(root).as_posix()
            if relative not in expected:
                raise PatchBuildError("Model created or retained a file outside the exact read-path list")
            actual.append(relative)
            info = candidate.stat()
            if relative in _active_allowed_paths:
                if not info.st_mode & stat.S_IWUSR:
                    raise PatchBuildError(f"Owner-approved write file lost its owner-write permission: {relative}")
            elif info.st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
                raise PatchBuildError(f"Read-only context file became writable: {relative}")
            try:
                payload = candidate.read_bytes()
                payload.decode("utf-8", errors="strict")
            except (OSError, UnicodeError) as exc:
                raise PatchBuildError(f"Model workspace file is not readable UTF-8 text: {relative}") from exc
            if b"\x00" in payload or len(payload) > MAX_FILE_BYTES:
                raise PatchBuildError(f"Model workspace file exceeds the bounded text-file policy: {relative}")
            total_bytes += len(payload)
            if total_bytes > MAX_TOTAL_BYTES:
                raise PatchBuildError("Model workspace exceeds the 256 KiB aggregate source budget")

    if sorted(actual) != sorted(read_paths):
        raise PatchBuildError("Model workspace file inventory differs from the exact read-path list")
    if root.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
        raise PatchBuildError("Model workspace root must remain non-writable")
    return [
        (relative, (root / relative).read_bytes())
        for relative in read_paths
    ]


# Set only inside build_patch_proposal; kept local to avoid passing write-path
# metadata through filesystem state or reading it from model-controlled files.
_active_allowed_paths: set[str] = set()


def build_patch_proposal(
    *,
    workspace: Path,
    baseline_root: Path,
    expected_scratch_base_sha: str,
    expected_task_id: str,
    expected_base_sha: str,
    read_paths: list[str],
    allowed_paths: list[str],
    test_ids: list[str],
    summary: str,
    limitations: list[str] | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    if not isinstance(expected_scratch_base_sha, str) or not SHA_RE.fullmatch(expected_scratch_base_sha):
        raise PatchBuildError("Trusted scratch base SHA is invalid")
    if not isinstance(expected_base_sha, str) or not SHA_RE.fullmatch(expected_base_sha):
        raise PatchBuildError("Trusted target base SHA is invalid")
    if not isinstance(expected_task_id, str) or not TASK_ID_RE.fullmatch(expected_task_id):
        raise PatchBuildError("Trusted task ID is invalid")
    if not isinstance(read_paths, list) or not 1 <= len(read_paths) <= MAX_READ_PATHS:
        raise PatchBuildError(f"Trusted read path list must contain 1-{MAX_READ_PATHS} paths")
    read_paths = [_safe_relative_path(item) for item in read_paths]
    if len(set(read_paths)) != len(read_paths):
        raise PatchBuildError("Trusted read path list contains duplicates")
    if not isinstance(allowed_paths, list) or not allowed_paths:
        raise PatchBuildError("Trusted owner-approved exact write path list is empty")
    allowed_paths = [_safe_relative_path(item) for item in allowed_paths]
    if len(allowed_paths) > MAX_FILES or len(set(allowed_paths)) != len(allowed_paths):
        raise PatchBuildError("Trusted owner-approved exact write path list is duplicated or too large")
    if not set(allowed_paths).issubset(set(read_paths)):
        raise PatchBuildError("Owner-approved write paths exceed the exact task read-path list")
    if not isinstance(test_ids, list) or not 1 <= len(test_ids) <= 6 or len(set(test_ids)) != len(test_ids):
        raise PatchBuildError("Trusted fixed test ID list is empty, duplicated or too large")
    if not isinstance(summary, str) or not summary.strip() or len(summary) > 240:
        raise PatchBuildError("Trusted patch summary must contain 1-240 characters")
    if limitations is None:
        limitations = []
    if not isinstance(limitations, list) or len(limitations) > 8:
        raise PatchBuildError("Trusted limitations list is malformed")

    try:
        root = workspace.resolve(strict=True)
        baseline = baseline_root.resolve(strict=True)
    except OSError as exc:
        raise PatchBuildError("Model workspace or private baseline does not exist") from exc
    if not root.is_dir() or not baseline.is_dir() or root == baseline:
        raise PatchBuildError("Model workspace and private baseline must be separate directories")
    try:
        root.relative_to(baseline)
    except ValueError:
        pass
    else:
        raise PatchBuildError("Model workspace cannot be inside the private baseline")
    try:
        baseline.relative_to(root)
    except ValueError:
        pass
    else:
        raise PatchBuildError("Private baseline cannot be inside the model workspace")
    if (root / ".git").exists() or (root / ".git").is_symlink():
        raise PatchBuildError("Model workspace must never contain Git metadata")

    top = _git(baseline, ["rev-parse", "--show-toplevel"]).strip()
    if Path(top).resolve() != baseline:
        raise PatchBuildError("Private baseline must be the exact Git repository root")
    current_head = _git(baseline, ["rev-parse", "HEAD"]).strip()
    if current_head != expected_scratch_base_sha:
        raise PatchBuildError("Private baseline HEAD differs from its trusted initial commit")
    if _git(baseline, ["status", "--porcelain=v1", "--untracked-files=all"]):
        raise PatchBuildError("Private baseline must be clean before trusted patch extraction")

    global _active_allowed_paths
    _active_allowed_paths = set(allowed_paths)
    try:
        workspace_files = _workspace_inventory(root, read_paths)
    finally:
        _active_allowed_paths = set()

    changed_paths: list[str] = []
    for relative, payload in workspace_files:
        baseline_file = baseline / relative
        if baseline_file.is_symlink() or not baseline_file.is_file():
            raise PatchBuildError(f"Private baseline file is missing or unsafe: {relative}")
        original = baseline_file.read_bytes()
        if relative not in allowed_paths and payload != original:
            raise PatchBuildError(f"Read-only context file was modified: {relative}")
        if relative in allowed_paths and payload != original:
            changed_paths.append(relative)

    if not changed_paths:
        raise PatchBuildError("Model produced no changes to any owner-approved write path")

    # Copy only authorized file contents into the private Git baseline. The
    # provider never sees this checkout or its .git directory.
    for relative, payload in workspace_files:
        if relative not in allowed_paths or relative not in changed_paths:
            continue
        (baseline / relative).write_bytes(payload)

    if _git(baseline, ["diff", "--cached", "--name-only", "-z"]):
        raise PatchBuildError("Private baseline unexpectedly contains staged changes")
    if _git(baseline, ["ls-files", "--others", "--exclude-standard", "-z"]):
        raise PatchBuildError("Private baseline unexpectedly contains untracked files")
    git_changed_raw = _git(baseline, ["diff", "--name-only", "--no-renames", "-z", "HEAD"])
    git_changed = [item for item in git_changed_raw.split("\x00") if item]
    if sorted(git_changed) != sorted(changed_paths):
        raise PatchBuildError("Private Git diff differs from the independently compared writable-file inventory")
    if len(git_changed) > MAX_FILES:
        raise PatchBuildError("Model patch exceeds the five-file unique change limit")

    try:
        validate_tracked_targets(baseline, tuple(git_changed))
    except ProposalError as exc:
        raise PatchBuildError(f"Changed target failed regular tracked-file validation: {exc}") from exc

    diff = _git(baseline, [
        "diff", "--no-ext-diff", "--no-color", "--full-index",
        "--binary", "--no-renames", "--unified=3", "HEAD",
    ])
    diff_bytes = diff.encode("utf-8")
    if not diff.strip():
        raise PatchBuildError("Git reported changed paths but produced an empty unified diff")
    if len(diff_bytes) > MAX_DIFF_BYTES:
        raise PatchBuildError("Unified patch exceeds the 32 KiB byte limit")

    proposal = {
        "schema_version": 1,
        "task_id": expected_task_id,
        "base_sha": expected_base_sha,
        "summary": summary,
        "unified_diff": diff,
        "test_ids": test_ids,
        "limitations": limitations,
    }
    try:
        verified_paths = validate_proposal(
            proposal,
            expected_task_id=expected_task_id,
            expected_base_sha=expected_base_sha,
            allowed_paths=set(allowed_paths),
        )
    except ProposalError as exc:
        raise PatchBuildError(f"Structured proposal failed exact policy validation: {exc}") from exc
    if sorted(verified_paths) != sorted(git_changed):
        raise PatchBuildError("Unified diff paths differ from the exact authorized changed-file inventory")

    encoded = (json.dumps(proposal, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(encoded) > MAX_PROPOSAL_BYTES:
        raise PatchBuildError("Structured patch proposal exceeds the 96 KiB size limit")
    if output_path is not None:
        destination = output_path.expanduser()
        if destination.exists() or destination.is_symlink():
            raise PatchBuildError("Proposal output path must not already exist")
        parent = destination.parent.resolve(strict=True)
        destination = parent / destination.name
        for root_to_avoid in (root, baseline):
            try:
                destination.relative_to(root_to_avoid)
            except ValueError:
                pass
            else:
                raise PatchBuildError("Proposal JSON must be stored outside both model workspace and private baseline")
        destination.write_bytes(encoded)

    return {
        "status": "PROPOSAL_READY",
        "task_id": expected_task_id,
        "target_base_sha": expected_base_sha,
        "scratch_base_sha": expected_scratch_base_sha,
        "changed_paths": list(verified_paths),
        "test_ids": list(test_ids),
        "proposal_bytes": len(encoded),
        "proposal": proposal,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--baseline-root", type=Path, required=True)
    parser.add_argument("--expected-scratch-base-sha", required=True)
    parser.add_argument("--expected-task-id", required=True)
    parser.add_argument("--expected-base-sha", required=True)
    parser.add_argument("--read-path", action="append", required=True)
    parser.add_argument("--allowed-path", action="append", required=True)
    parser.add_argument("--test-id", action="append", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--limitation", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        report = build_patch_proposal(
            workspace=args.workspace,
            baseline_root=args.baseline_root,
            expected_scratch_base_sha=args.expected_scratch_base_sha,
            expected_task_id=args.expected_task_id,
            expected_base_sha=args.expected_base_sha,
            read_paths=args.read_path,
            allowed_paths=args.allowed_path,
            test_ids=args.test_id,
            summary=args.summary,
            limitations=args.limitation,
            output_path=args.output,
        )
    except (PatchBuildError, ProposalError) as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}, sort_keys=True))
        return 2
    report.pop("proposal", None)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
