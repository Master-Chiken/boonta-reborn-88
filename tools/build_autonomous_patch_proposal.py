#!/usr/bin/env python3
"""Export a disposable agent workspace diff as a trusted structured proposal.

Task identity, base SHA, approved paths and fixed test IDs are supplied by the
workflow. The model can only change scratch files; it cannot choose metadata,
test commands, GitHub destinations or repository write credentials.
"""
from __future__ import annotations

import argparse
import json
import os
import re
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


def _git(root: Path, args: list[str], *, allowed_codes: tuple[int, ...] = (0,)) -> str:
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
        raise PatchBuildError("Git could not inspect the isolated model workspace") from exc
    if result.returncode not in allowed_codes:
        raise PatchBuildError("Git command failed: " + " ".join(args[:3]))
    return result.stdout


def build_patch_proposal(
    *,
    workspace: Path,
    expected_scratch_base_sha: str,
    expected_task_id: str,
    expected_base_sha: str,
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
    if not isinstance(allowed_paths, list) or not allowed_paths:
        raise PatchBuildError("Trusted owner-approved exact write path list is empty")
    if len(allowed_paths) > MAX_FILES or len(set(allowed_paths)) != len(allowed_paths):
        raise PatchBuildError("Trusted owner-approved exact write path list is duplicated or too large")
    if not isinstance(test_ids, list) or not test_ids or len(set(test_ids)) != len(test_ids):
        raise PatchBuildError("Trusted fixed test ID list is empty or duplicated")
    if not isinstance(summary, str) or not summary.strip() or len(summary) > 240:
        raise PatchBuildError("Trusted patch summary must contain 1-240 characters")
    if limitations is None:
        limitations = []
    if not isinstance(limitations, list) or len(limitations) > 8:
        raise PatchBuildError("Trusted limitations list is malformed")

    try:
        root = workspace.resolve(strict=True)
    except OSError as exc:
        raise PatchBuildError("Isolated model workspace does not exist") from exc
    if not root.is_dir():
        raise PatchBuildError("Isolated model workspace is not a directory")
    top = _git(root, ["rev-parse", "--show-toplevel"]).strip()
    if Path(top).resolve() != root:
        raise PatchBuildError("Workspace must be the exact Git repository root")
    current_head = _git(root, ["rev-parse", "HEAD"]).strip()
    if current_head != expected_scratch_base_sha:
        raise PatchBuildError("Isolated workspace HEAD differs from its trusted initial commit")

    # Models do not stage files; staged changes would bypass the expected
    # worktree-only diff contract. New files also require a separate owner
    # review and are not accepted by this pipeline.
    staged = _git(root, ["diff", "--cached", "--name-only", "-z"])
    if staged:
        raise PatchBuildError("Staged changes are forbidden in the isolated model workspace")
    untracked = _git(root, ["ls-files", "--others", "--exclude-standard", "-z"])
    if untracked:
        raise PatchBuildError("Untracked files are forbidden in the isolated model workspace")

    changed_raw = _git(root, ["diff", "--name-only", "--no-renames", "-z", "HEAD"])
    changed_paths = [item for item in changed_raw.split("\x00") if item]
    if not changed_paths:
        raise PatchBuildError("Model produced no tracked source changes")
    if len(changed_paths) > MAX_FILES or len(set(changed_paths)) != len(changed_paths):
        raise PatchBuildError("Model patch exceeds the five-file unique change limit")

    try:
        validate_tracked_targets(root, tuple(changed_paths))
    except ProposalError as exc:
        raise PatchBuildError(f"Changed target failed regular tracked-file validation: {exc}") from exc

    diff = _git(root, [
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
    if sorted(verified_paths) != sorted(changed_paths):
        raise PatchBuildError("Unified diff file paths differ from Git's exact changed-file inventory")

    encoded = (json.dumps(proposal, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(encoded) > MAX_PROPOSAL_BYTES:
        raise PatchBuildError("Structured patch proposal exceeds the 96 KiB size limit")
    if output_path is not None:
        destination = output_path.expanduser()
        if destination.exists() or destination.is_symlink():
            raise PatchBuildError("Proposal output path must not already exist")
        parent = destination.parent.resolve(strict=True)
        destination = parent / destination.name
        try:
            destination.relative_to(root)
        except ValueError:
            pass
        else:
            raise PatchBuildError("Proposal JSON must be stored outside the model workspace")
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
    parser.add_argument("--expected-scratch-base-sha", required=True)
    parser.add_argument("--expected-task-id", required=True)
    parser.add_argument("--expected-base-sha", required=True)
    parser.add_argument("--allowed-path", action="append", required=True)
    parser.add_argument("--test-id", action="append", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--limitation", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        report = build_patch_proposal(
            workspace=args.workspace,
            expected_scratch_base_sha=args.expected_scratch_base_sha,
            expected_task_id=args.expected_task_id,
            expected_base_sha=args.expected_base_sha,
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
