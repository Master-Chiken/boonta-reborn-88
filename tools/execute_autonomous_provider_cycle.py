#!/usr/bin/env python3
"""Workflow-owned verify/test/deliver pipeline for one provider patch proposal.

The provider never receives a GitHub writer. This process starts only after the
provider invocation ends and only the workflow gives it a scoped GitHub token.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from autonomous_patch_proposal import ProposalError
from build_autonomous_delivery_plan import DeliveryPlanError, build_delivery_plan
from execute_autonomous_github_delivery import (
    DeliveryExecutionError,
    execute_delivery,
)
from verify_autonomous_patch import PipelineError, verify_in_isolated_worktree

TASK_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,63}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
MAX_REPORT_LINE = 240
REPOSITORY = "Master-Chiken/boonta-reborn-88"


class ProviderCycleError(ValueError):
    """Raised when the trusted workflow-owned delivery pipeline cannot complete."""


def _safe_line(value: Any, fallback: str) -> str:
    if not isinstance(value, str):
        value = fallback
    value = " ".join(value.replace("\r", " ").replace("\n", " ").split())
    return (value or fallback)[:MAX_REPORT_LINE]


def _write_cycle_report(report_path: Path, task_id: str, status: str, target_branch: str, *,
                        pr_url: str = "", head_sha: str = "",
                        blocker: str = "", next_action: str = "") -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if status == "PROGRESS":
        lines = [
            f"BOONTA_CYCLE_TASK_ID: {task_id}",
            "BOONTA_CYCLE_STATUS: PROGRESS",
            f"BOONTA_CYCLE_EVIDENCE: {pr_url} @ {head_sha}",
            f"BOONTA_CYCLE_EVIDENCE_BASE: {target_branch}",
        ]
    else:
        lines = [
            f"BOONTA_CYCLE_TASK_ID: {task_id}",
            "BOONTA_CYCLE_STATUS: BLOCKED",
            "BOONTA_CYCLE_BLOCKER: {_safe_line(blocker, 'Patch proposal or verification was unavailable.')}",
            f"BOONTA_CYCLE_NEXT_ACTION: {_safe_line(next_action, 'Inspect the blocker, correct the workflow-owned prerequisite, then start one fresh free-tier cycle.')}",
        ]
    temporary = report_path.with_name(report_path.name + ".tmp")
    if temporary.exists() or temporary.is_symlink():
        raise ProviderCycleError("Temporary cycle report already exists")
    with temporary.open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, report_path)


def execute_provider_cycle(
    *,
    source_root: Path,
    policy_root: Path,
    proposal_path: Path,
    allowlist_report_path: Path,
    verified_report_path: Path,
    plan_path: Path,
    cycle_report_path: Path,
    expected_task_id: str,
    expected_base_sha: str,
    expected_policy_sha: str,
    repository: str,
    preflight_allowed: bool,
) -> dict[str, Any]:
    if repository != REPOSITORY:
        raise ProviderCycleError("Provider delivery is restricted to the canonical Boonta repository")
    if not TASK_ID_RE.fullmatch(expected_task_id):
        raise ProviderCycleError("Selected task ID is invalid")
    if not SHA_RE.fullmatch(expected_base_sha) or not SHA_RE.fullmatch(expected_policy_sha):
        raise ProviderCycleError("Exact target and trusted policy SHAs are required")
    if preflight_allowed is not True:
        raise ProviderCycleError("Independent €0/owner preflight did not pass")

    if proposal_path.is_symlink() or not proposal_path.is_file():
        blocker = "The provider did not submit one bounded patch proposal."
        next_action = "Review the provider invocation log and exact source excerpts, then retry once through the next eligible free route."
        _write_cycle_report(
            cycle_report_path, expected_task_id, "BLOCKED", "",
            blocker=blocker, next_action=next_action,
        )
        return {"status": "BLOCKED", "task_id": expected_task_id, "reason": blocker}

    try:
        verified = verify_in_isolated_worktree(
            source_root,
            proposal_path=proposal_path,
            allowlist_report_path=allowlist_report_path,
            expected_task_id=expected_task_id,
            expected_base_sha=expected_base_sha,
            policy_root=policy_root,
            expected_policy_sha=expected_policy_sha,
        )
        if verified.get("status") != "VERIFIED":
            test_report = verified.get("test_report", {})
            failed = next(
                (item for item in test_report.get("results", [])
                 if item.get("status") != "PASSED"),
                None,
            )
            detail = (
                f"{failed.get('test_id')} returned {failed.get('status')}"
                if failed else "the isolated test pipeline did not return VERIFIED"
            )
            raise ProviderCycleError("Patch verification failed: " + detail)
        verified_report_path.write_text(
            json.dumps(verified, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        plan = build_delivery_plan(
            source_root,
            verified_report_path=verified_report_path,
            allowlist_report_path=allowlist_report_path,
            expected_task_id=expected_task_id,
            expected_base_sha=expected_base_sha,
            policy_root=policy_root,
            expected_policy_sha=expected_policy_sha,
        )
        plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        token = os.environ.get("GITHUB_TOKEN", "")
        if len(token) < 20:
            raise ProviderCycleError("The workflow-owned GitHub writer token is unavailable")
        # These gates are set only after trusted policy, base SHA, isolated
        # application and every required fixed test have passed.
        os.environ["BOONTA_DETERMINISTIC_DELIVERY_ENABLED"] = "true"
        os.environ["BOONTA_DETERMINISTIC_DELIVERY_OWNER_APPROVED"] = "true"
        os.environ["GITHUB_REPOSITORY"] = repository
        delivered = execute_delivery(
            plan,
            repo_root=source_root,
            verified_report_path=verified_report_path,
            allowlist_report_path=allowlist_report_path,
            expected_task_id=expected_task_id,
            expected_base_sha=expected_base_sha,
            repository=repository,
            token=token,
            policy_root=policy_root,
            expected_policy_sha=expected_policy_sha,
        )
        if delivered.get("status") != "PR_CREATED" or delivered.get("draft") is not False or delivered.get("auto_merge") is not False or delivered.get("merge_performed") is not False:
            raise ProviderCycleError("Workflow writer did not confirm the exact non-draft, no-auto-merge PR contract")
        pr_url = delivered.get("pull_request_url")
        head_sha = delivered.get("commit_sha")
        target_branch = plan.get("target_branch")
        if (
            not isinstance(pr_url, str)
            or not re.fullmatch(r"https://github\.com/Master-Chiken/boonta-reborn-88/pull/[1-9][0-9]*", pr_url)
            or not isinstance(head_sha, str)
            or not SHA_RE.fullmatch(head_sha)
            or target_branch not in {"main", "dev"}
        ):
            raise ProviderCycleError("Workflow writer returned incomplete exact PR evidence")
        _write_cycle_report(
            cycle_report_path, expected_task_id, "PROGRESS", target_branch,
            pr_url=pr_url, head_sha=head_sha,
        )
        return {
            "status": "PROGRESS",
            "task_id": expected_task_id,
            "pull_request_url": pr_url,
            "head_sha": head_sha,
            "target_branch": target_branch,
            "executed_test_ids": verified.get("executed_test_ids", []),
            "remote_write_performed": True,
            "auto_merge": False,
            "merge_performed": False,
        }
    except (
        ProviderCycleError,
        PipelineError,
        ProposalError,
        DeliveryPlanError,
        DeliveryExecutionError,
        OSError,
        ValueError,
    ) as exc:
        blocker = _safe_line(str(exc), "Workflow-owned patch verification or delivery failed.")
        next_action = (
            "Use the exact blocker above to correct the source proposal or trusted prerequisite; "
            "do not bypass the fixed tests or owner path policy."
        )
        _write_cycle_report(
            cycle_report_path, expected_task_id, "BLOCKED", "",
            blocker=blocker, next_action=next_action,
        )
        return {"status": "BLOCKED", "task_id": expected_task_id, "reason": blocker}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--policy-root", type=Path, required=True)
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--allowlist-report", type=Path, required=True)
    parser.add_argument("--verified-report", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--cycle-report", type=Path, required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--policy-sha", required=True)
    parser.add_argument("--repository", default=REPOSITORY)
    parser.add_argument("--preflight-allowed", choices=("true", "false"), required=True)
    args = parser.parse_args()
    try:
        result = execute_provider_cycle(
            source_root=args.source_root,
            policy_root=args.policy_root,
            proposal_path=args.proposal,
            allowlist_report_path=args.allowlist_report,
            verified_report_path=args.verified_report,
            plan_path=args.plan,
            cycle_report_path=args.cycle_report,
            expected_task_id=args.task_id,
            expected_base_sha=args.base_sha,
            expected_policy_sha=args.policy_sha,
            repository=args.repository,
            preflight_allowed=args.preflight_allowed == "true",
        )
    except (ProviderCycleError, OSError, ValueError) as exc:
        print(json.dumps({"status": "REJECTED", "reason": _safe_line(str(exc), "Provider cycle rejected.")}, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
