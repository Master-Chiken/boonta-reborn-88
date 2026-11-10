#!/usr/bin/env python3
"""Create deterministic commit/PR metadata from a verified isolated patch report.

This is a read-only planner. It does not create commits/branches, use network
access, push, call GitHub APIs, or merge pull requests.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from autonomous_patch_proposal import ProposalError, load_allowlist_report, validate_checkout
from build_autonomous_path_allowlist import AllowlistError, build_allowlist
from run_autonomous_patch_tests import TEST_REGISTRY
from verify_autonomous_patch import MANDATORY_TEST_IDS

ROOT = Path(__file__).resolve().parents[1]
LEDGER_SUMMARY = Path("docs/automation/task-ledger-summary.json")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TASK_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,63}$")
MAX_REPORT_BYTES = 32 * 1024


class DeliveryPlanError(ValueError):
    """Raised when verified evidence cannot safely produce a delivery plan."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DeliveryPlanError(f"Duplicate JSON property: {key}")
        value[key] = item
    return value


def _load_report(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise DeliveryPlanError("Verified report must not be a symlink")
    try:
        if path.stat().st_size > MAX_REPORT_BYTES:
            raise DeliveryPlanError("Verified report exceeds the 32 KiB input limit")
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except DeliveryPlanError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DeliveryPlanError("Verified report is not readable valid UTF-8 JSON") from exc
    if len(raw.encode("utf-8")) > MAX_REPORT_BYTES:
        raise DeliveryPlanError("Verified report exceeds the 32 KiB input limit")
    if not isinstance(value, dict):
        raise DeliveryPlanError("Verified report must be a JSON object")
    return value


def _load_canonical_task(root: Path, task_id: str) -> dict[str, Any]:
    path = root / LEDGER_SUMMARY
    if path.is_symlink():
        raise DeliveryPlanError("Canonical task summary must not be a symlink")
    indexed = subprocess.run(
        ["git", "ls-files", "-s", "--", LEDGER_SUMMARY.as_posix()],
        cwd=root, stdin=subprocess.DEVNULL, text=True, capture_output=True, check=False,
    )
    if indexed.returncode != 0 or len(indexed.stdout.splitlines()) != 1:
        raise DeliveryPlanError("Canonical task summary must be one tracked file")
    if indexed.stdout.split()[0] not in {"100644", "100755"}:
        raise DeliveryPlanError("Canonical task summary must be a regular tracked file")
    try:
        if path.stat().st_size > MAX_REPORT_BYTES:
            raise DeliveryPlanError("Canonical task summary exceeds the 32 KiB input limit")
        raw = path.read_text(encoding="utf-8")
        ledger = json.loads(raw, object_pairs_hook=_unique_object)
    except DeliveryPlanError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DeliveryPlanError("Canonical task summary cannot be read") from exc
    if (
        not isinstance(ledger, dict)
        or type(ledger.get("schema_version")) is not int
        or ledger["schema_version"] != 2
        or ledger.get("source") != "docs/automation/task-ledger.json"
        or not isinstance(ledger.get("tasks"), list)
    ):
        raise DeliveryPlanError("Canonical task summary schema or source is invalid")
    tasks = ledger["tasks"]
    active = [task for task in tasks if isinstance(task, dict) and task.get("status") == "active"]
    if len(active) != 1:
        raise DeliveryPlanError("Delivery plan requires exactly one canonical active task")
    selected = active[0]
    if selected.get("task_id") != task_id:
        raise DeliveryPlanError("Verified task ID does not match the unique active task")
    if selected.get("target_branch") not in {"main", "dev"}:
        raise DeliveryPlanError("Canonical active task has an unsupported target branch")
    return selected


def build_delivery_plan(
    repo_root: Path,
    *,
    verified_report_path: Path,
    allowlist_report_path: Path,
    expected_task_id: str,
    expected_base_sha: str,
) -> dict[str, Any]:
    root = repo_root.resolve()
    if not isinstance(expected_task_id, str) or not TASK_ID_RE.fullmatch(expected_task_id):
        raise DeliveryPlanError("Expected task ID is invalid")
    if not isinstance(expected_base_sha, str) or not SHA_RE.fullmatch(expected_base_sha):
        raise DeliveryPlanError("Expected base SHA is invalid")
    try:
        validate_checkout(root, expected_base_sha)
        allowed_paths = load_allowlist_report(
            allowlist_report_path,
            expected_task_id=expected_task_id,
            expected_base_sha=expected_base_sha,
        )
        current_scope = build_allowlist(
            root,
            expected_base_sha=expected_base_sha,
            requested_task_id=expected_task_id,
        )
    except (ProposalError, AllowlistError) as exc:
        raise DeliveryPlanError(str(exc)) from exc
    if current_scope.get("status") != "READY":
        raise DeliveryPlanError("Current canonical task/path policy is not READY")
    if set(current_scope.get("allowed_paths", [])) != allowed_paths:
        raise DeliveryPlanError("Supplied allowlist report differs from the current owner-reviewed policy")
    if current_scope.get("approval_ref") != _load_report(allowlist_report_path).get("approval_ref"):
        raise DeliveryPlanError("Supplied allowlist evidence differs from the current owner-reviewed policy")

    report = _load_report(verified_report_path)
    expected_fields = {
        "status", "task_id", "base_sha", "summary", "changed_paths",
        "requested_test_ids", "executed_test_ids", "test_report",
        "isolated_worktree", "source_checkout_modified", "commit_created",
        "branch_created", "network_accessed",
    }
    if set(report) != expected_fields:
        raise DeliveryPlanError("Verified report does not match the exact pipeline report contract")
    if report.get("status") != "VERIFIED":
        raise DeliveryPlanError("Only a VERIFIED patch can enter deterministic delivery planning")
    if report.get("task_id") != expected_task_id or report.get("base_sha") != expected_base_sha:
        raise DeliveryPlanError("Verified report task ID/base SHA does not match preflight")
    if report.get("isolated_worktree") is not True or report.get("source_checkout_modified") is not False:
        raise DeliveryPlanError("Verified report does not prove isolated source-checkout safety")
    if report.get("commit_created") is not False or report.get("branch_created") is not False:
        raise DeliveryPlanError("Verified report must not claim an existing commit or branch")
    if report.get("network_accessed") is not False:
        raise DeliveryPlanError("Verified report must prove no network access")

    summary = report.get("summary")
    if not isinstance(summary, str) or not summary.strip() or len(summary) > 240:
        raise DeliveryPlanError("Verified report summary is invalid")

    changed_paths = report.get("changed_paths")
    if (
        not isinstance(changed_paths, list)
        or not changed_paths
        or any(not isinstance(path, str) for path in changed_paths)
        or len(set(changed_paths)) != len(changed_paths)
    ):
        raise DeliveryPlanError("Verified changed_paths must be a unique non-empty string array")
    if not set(changed_paths).issubset(allowed_paths):
        raise DeliveryPlanError("Verified changed paths exceed the owner-approved path report")

    requested = report.get("requested_test_ids")
    executed = report.get("executed_test_ids")
    if (
        not isinstance(requested, list)
        or not requested
        or any(not isinstance(x, str) for x in requested)
        or len(set(requested)) != len(requested)
    ):
        raise DeliveryPlanError("Verified requested_test_ids are invalid")
    if (
        not isinstance(executed, list)
        or not 1 <= len(executed) <= 6
        or any(not isinstance(x, str) for x in executed)
        or len(set(executed)) != len(executed)
        or any(x not in TEST_REGISTRY for x in executed)
    ):
        raise DeliveryPlanError("Verified executed_test_ids are invalid or outside the fixed registry")
    if not set(MANDATORY_TEST_IDS).issubset(set(executed)):
        raise DeliveryPlanError("Verified report does not include all mandatory test IDs")
    if any(x not in TEST_REGISTRY for x in requested):
        raise DeliveryPlanError("Verified requested_test_ids are outside the fixed registry")
    if not set(requested).issubset(set(executed)):
        raise DeliveryPlanError("One or more requested test IDs were not executed")

    test_report = report.get("test_report")
    if (
        not isinstance(test_report, dict)
        or test_report.get("status") != "PASSED"
        or test_report.get("stopped_after_first_failure") is not False
        or not isinstance(test_report.get("results"), list)
    ):
        raise DeliveryPlanError("Mandatory test report is not fully passed")
    result_ids = []
    for result in test_report["results"]:
        if (
            not isinstance(result, dict)
            or result.get("status") != "PASSED"
            or result.get("exit_code") != 0
            or not isinstance(result.get("test_id"), str)
        ):
            raise DeliveryPlanError("A test result is missing a successful fixed-ID result")
        result_ids.append(result["test_id"])
    if result_ids != executed:
        raise DeliveryPlanError("Test results do not match the exact executed test-ID list")

    task = _load_canonical_task(root, expected_task_id)
    target_branch = task["target_branch"]
    branch_name = f"autonomous/{expected_task_id.lower()}-{expected_base_sha[:12]}"
    commit_subject = f"chore(automation): deliver {expected_task_id}"
    commit_body = "\n".join([
        "Deterministic delivery prepared after isolated patch verification.",
        f"Task-ID: {expected_task_id}",
        f"Base-SHA: {expected_base_sha}",
        "Changed-Paths: " + ", ".join(sorted(changed_paths)),
        "Verified-Tests: " + ", ".join(executed),
    ])
    pr_title = f"Boonta automation: {expected_task_id}"
    pr_body = "\n".join([
        "## Verified autonomous change",
        "",
        f"- Task ID: {expected_task_id}",
        f"- Base commit: {expected_base_sha}",
        f"- Target branch: {target_branch}",
        "- Verification: PASSED in a disposable detached worktree",
        "- Source checkout modified during verification: no",
        "",
        "### Changed files",
        *[f"- {path}" for path in sorted(changed_paths)],
        "",
        "### Mandatory and requested checks",
        *[f"- PASS: {test_id}" for test_id in executed],
        "",
        "This PR is generated from a strict patch proposal and owner-reviewed exact-path scope. It is not auto-merged.",
        "",
        f"BOONTA_TASK_ID: {expected_task_id}",
    ])
    return {
        "status": "DELIVERY_PLAN_READY",
        "task_id": expected_task_id,
        "base_sha": expected_base_sha,
        "target_branch": target_branch,
        "branch_name": branch_name,
        "commit_subject": commit_subject,
        "commit_body": commit_body,
        "pr_title": pr_title,
        "pr_body": pr_body,
        "changed_paths": sorted(changed_paths),
        "executed_test_ids": executed,
        "remote_write_performed": False,
        "commit_created": False,
        "branch_created": False,
        "pull_request_created": False,
        "auto_merge_enabled": False,
        "network_accessed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--verified-report", type=Path)
    parser.add_argument("--allowlist-report", type=Path)
    parser.add_argument("--expected-task-id")
    parser.add_argument("--expected-base-sha")
    args = parser.parse_args()
    if not all((args.repo_root, args.verified_report, args.allowlist_report, args.expected_task_id, args.expected_base_sha)):
        parser.error("repo root, verified report, allowlist report, expected task ID and expected base SHA are required")
    try:
        report = build_delivery_plan(
            args.repo_root,
            verified_report_path=args.verified_report,
            allowlist_report_path=args.allowlist_report,
            expected_task_id=args.expected_task_id,
            expected_base_sha=args.expected_base_sha,
        )
    except (DeliveryPlanError, ProposalError) as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
