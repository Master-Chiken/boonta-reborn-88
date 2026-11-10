#!/usr/bin/env python3
"""Apply a model patch and verify it in a disposable detached Git worktree.

This orchestration layer is deliberately provider-independent. It never creates
branches/commits, pushes, opens PRs, or executes model-supplied commands.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import run_autonomous_patch_tests
from autonomous_patch_proposal import (
    ProposalError,
    load_allowlist_report,
    load_proposal,
    validate_or_apply,
    validate_checkout,
)

MANDATORY_TEST_IDS = (
    "automation.task_preflight",
    "automation.provider_handoff",
    "automation.task_ledger",
)
MAX_BUNDLE_FILE_BYTES = 128 * 1024
MAX_BUNDLE_TOTAL_BYTES = 256 * 1024


class PipelineError(ValueError):
    """Raised when the isolated patch verification pipeline cannot be trusted."""


def _git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            stdin=subprocess.DEVNULL,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PipelineError("Git worktree operation failed") from exc


def _git_output(root: Path, args: list[str]) -> str:
    result = _git(root, args)
    if result.returncode != 0:
        raise PipelineError("Git command failed: " + " ".join(args[:2]))
    return result.stdout.strip()


def _remove_worktree(root: Path, worktree: Path) -> None:
    result = _git(root, ["worktree", "remove", "--force", str(worktree)])
    if result.returncode != 0:
        raise PipelineError("Could not remove the disposable verification worktree")
    _git(root, ["worktree", "prune", "--expire", "now"])


def _build_delivery_bundle(
    source_root: Path,
    worktree: Path,
    *,
    base_sha: str,
    changed_paths: list[str],
) -> list[dict[str, Any]]:
    bundle: list[dict[str, Any]] = []
    total_bytes = 0
    for path in sorted(changed_paths):
        target = worktree / path
        if target.is_symlink():
            raise PipelineError(f"Verified output is a symlink: {path}")
        try:
            file_stat = target.lstat()
        except OSError as exc:
            raise PipelineError(f"Verified output file cannot be inspected: {path}") from exc
        if not stat.S_ISREG(file_stat.st_mode):
            raise PipelineError(f"Verified output is not a regular file: {path}")
        parent = target.parent
        while parent != worktree:
            if parent.is_symlink():
                raise PipelineError(f"Verified output has a symlink parent: {path}")
            parent = parent.parent

        try:
            data = target.read_bytes()
            data.decode("utf-8", errors="strict")
        except (OSError, UnicodeError) as exc:
            raise PipelineError(f"Verified output must be readable UTF-8 text: {path}") from exc
        if len(data) > MAX_BUNDLE_FILE_BYTES:
            raise PipelineError(f"Verified output exceeds the 128 KiB per-file export limit: {path}")
        total_bytes += len(data)
        if total_bytes > MAX_BUNDLE_TOTAL_BYTES:
            raise PipelineError("Verified output exceeds the 256 KiB total export limit")

        indexed = _git(source_root, ["ls-files", "-s", "--", path])
        if indexed.returncode != 0:
            raise PipelineError("Could not re-read the base Git index")
        entries = [line for line in indexed.stdout.splitlines() if line.strip()]
        if len(entries) != 1:
            raise PipelineError(f"Base path is not one tracked file: {path}")
        fields = entries[0].split()
        mode = fields[0]
        if mode not in {"100644", "100755"}:
            raise PipelineError(f"Base path is not a regular tracked file: {path}")
        base_blob_sha = _git_output(source_root, ["rev-parse", f"{base_sha}:{path}"])
        result_blob_sha = _git_output(worktree, ["hash-object", "--", path])
        bundle.append({
            "path": path,
            "mode": mode,
            "base_blob_sha": base_blob_sha,
            "result_blob_sha": result_blob_sha,
            "content_sha256": hashlib.sha256(data).hexdigest(),
            "content_base64": base64.b64encode(data).decode("ascii"),
        })
    return bundle


def verify_in_isolated_worktree(
    repo_root: Path,
    *,
    proposal_path: Path,
    allowlist_report_path: Path,
    expected_task_id: str,
    expected_base_sha: str,
) -> dict[str, Any]:
    root = repo_root.resolve()
    if not root.is_dir():
        raise PipelineError("Repository checkout does not exist")
    validate_checkout(root, expected_base_sha)

    allowed_paths = load_allowlist_report(
        allowlist_report_path,
        expected_task_id=expected_task_id,
        expected_base_sha=expected_base_sha,
    )
    proposal = load_proposal(proposal_path)

    # Validate the model proposal before allocating a worktree. The validator
    # repeats these checks in the detached checkout before applying the diff.
    from autonomous_patch_proposal import validate_proposal
    changed_paths = validate_proposal(
        proposal,
        expected_task_id=expected_task_id,
        expected_base_sha=expected_base_sha,
        allowed_paths=allowed_paths,
    )

    available_tests = set(run_autonomous_patch_tests.TEST_REGISTRY)
    if not set(MANDATORY_TEST_IDS).issubset(available_tests):
        raise PipelineError("The fixed mandatory test registry is incomplete")
    requested_tests = proposal["test_ids"]
    executed_tests = list(dict.fromkeys([*MANDATORY_TEST_IDS, *requested_tests]))
    if len(executed_tests) > run_autonomous_patch_tests.MAX_TESTS:
        raise PipelineError("Merged mandatory/requested test set exceeds the fixed runner limit")

    # The temporary worktree is a sibling of the source checkout, never inside
    # the directory whose cleanliness and exact HEAD were just validated.
    with tempfile.TemporaryDirectory(prefix="boonta-patch-verify-") as temp_dir:
        worktree = (Path(temp_dir) / "checkout").resolve()
        worktree_added = False
        try:
            temp_parent = Path(temp_dir).resolve()
            if temp_parent == root or root in temp_parent.parents:
                raise PipelineError("Temporary verification directory must be outside the source checkout")
            add = _git(root, ["worktree", "add", "--detach", str(worktree), expected_base_sha])
            if add.returncode != 0:
                raise PipelineError("Could not create a detached verification worktree")
            worktree_added = True

            if _git_output(worktree, ["rev-parse", "HEAD"]) != expected_base_sha:
                raise PipelineError("Disposable worktree did not start at the trusted base SHA")
            if _git_output(worktree, ["rev-parse", "--abbrev-ref", "HEAD"]) != "HEAD":
                raise PipelineError("Disposable worktree is not detached")

            applied = validate_or_apply(
                worktree,
                proposal,
                expected_task_id=expected_task_id,
                expected_base_sha=expected_base_sha,
                allowed_paths=allowed_paths,
                apply=True,
            )

            test_report = run_autonomous_patch_tests.run_test_ids(
                worktree,
                executed_tests,
            )
            if test_report.get("status") != "PASSED":
                return {
                    "status": "FAILED",
                    "task_id": expected_task_id,
                    "base_sha": expected_base_sha,
                    "changed_paths": list(changed_paths),
                    "test_report": test_report,
                    "isolated_worktree": True,
                    "source_checkout_modified": False,
                    "commit_created": False,
                    "branch_created": False,
                    "network_accessed": False,
                }

            if _git_output(worktree, ["rev-parse", "HEAD"]) != expected_base_sha:
                raise PipelineError("Verification tests unexpectedly created a commit")
            if _git_output(worktree, ["rev-parse", "--abbrev-ref", "HEAD"]) != "HEAD":
                raise PipelineError("Verification worktree unexpectedly left detached HEAD state")
            working_paths = _git_output(worktree, ["diff", "--name-only"]).splitlines()
            staged_paths = _git_output(worktree, ["diff", "--cached", "--name-only"]).splitlines()
            untracked_paths = _git_output(
                worktree, ["ls-files", "--others", "--exclude-standard"]
            ).splitlines()
            expected = sorted(changed_paths)
            if sorted(working_paths) != expected or staged_paths or untracked_paths:
                raise PipelineError("Verification changed files outside the exact validated patch")
            # Revalidate targets after test execution, then export exact UTF-8
            # file contents and Git blob identities for a future deterministic
            # writer. The bundle is bounded and contains only approved files.
            from autonomous_patch_proposal import validate_tracked_targets
            validate_tracked_targets(worktree, tuple(expected))
            delivery_bundle = _build_delivery_bundle(
                root,
                worktree,
                base_sha=expected_base_sha,
                changed_paths=expected,
            )
            return {
                "status": "VERIFIED",
                "task_id": expected_task_id,
                "base_sha": expected_base_sha,
                "summary": proposal["summary"],
                "changed_paths": expected,
                "requested_test_ids": requested_tests,
                "executed_test_ids": executed_tests,
                "test_report": test_report,
                "delivery_bundle": delivery_bundle,
                "isolated_worktree": True,
                "source_checkout_modified": False,
                "commit_created": False,
                "branch_created": False,
                "network_accessed": False,
            }
        finally:
            if worktree_added:
                _remove_worktree(root, worktree)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--proposal", type=Path)
    parser.add_argument("--allowlist-report", type=Path)
    parser.add_argument("--expected-task-id")
    parser.add_argument("--expected-base-sha")
    args = parser.parse_args()
    if not all((
        args.repo_root,
        args.proposal,
        args.allowlist_report,
        args.expected_task_id,
        args.expected_base_sha,
    )):
        parser.error("repo root, proposal, allowlist report, task ID and base SHA are required")
    try:
        report = verify_in_isolated_worktree(
            args.repo_root,
            proposal_path=args.proposal,
            allowlist_report_path=args.allowlist_report,
            expected_task_id=args.expected_task_id,
            expected_base_sha=args.expected_base_sha,
        )
    except (PipelineError, ProposalError) as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
