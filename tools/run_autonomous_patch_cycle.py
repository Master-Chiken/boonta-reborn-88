#!/usr/bin/env python3
"""Run a guarded €0 patch cycle from owner policy to a reviewable PR.

The model only proposes a JSON diff. Repository-owned code validates the exact
task/path policy, tests the diff in a detached worktree, and opens a PR only
when the explicit repository delivery gate is enabled. No merge is possible.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from autonomous_patch_proposal import ProposalError
from build_autonomous_delivery_plan import DeliveryPlanError, build_delivery_plan
from build_autonomous_path_allowlist import AllowlistError, build_allowlist
from execute_autonomous_github_delivery import (
    DeliveryExecutionError,
    execute_delivery,
    require_execution_gates,
    validate_plan_against_sources,
)
from run_autonomous_provider_patch import ProviderPatchError, run_provider_patch
from verify_autonomous_patch import PipelineError, verify_in_isolated_worktree

CANONICAL_REPOSITORY = "Master-Chiken/boonta-reborn-88"
TASK_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,63}$")
BRANCHES = {"main", "dev"}


class CycleError(ValueError):
    """Raised for an unsafe or incomplete cycle setup."""


def _git_sha(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        stdin=subprocess.DEVNULL,
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    sha = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise CycleError("Could not resolve an exact checkout HEAD SHA")
    return sha


def _clean_line(value: str, maximum: int = 240) -> str:
    return " ".join(str(value).replace("\r", " ").replace("\n", " ").split())[:maximum] or "No detail supplied"


def _write_report(path: Path, *, task_id: str, status: str, target_branch: str, evidence: str = "", blocker: str = "", next_action: str = "") -> None:
    if path.is_symlink():
        raise CycleError("Cycle report path must not be a symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists() or temporary.is_symlink():
        raise CycleError("Cycle report temporary path already exists")
    lines = [
        f"BOONTA_CYCLE_TASK_ID: {task_id}",
        f"BOONTA_CYCLE_STATUS: {status}",
    ]
    if status == "PROGRESS":
        if not evidence:
            raise CycleError("PROGRESS requires exact PR URL and head SHA evidence")
        lines.append(f"BOONTA_CYCLE_EVIDENCE: {evidence}")
        lines.append(f"BOONTA_CYCLE_EVIDENCE_BASE: {target_branch}")
    else:
        lines.extend([
            f"BOONTA_CYCLE_BLOCKER: {_clean_line(blocker)}",
            f"BOONTA_CYCLE_NEXT_ACTION: {_clean_line(next_action)}",
        ])
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temporary.replace(path)


def run_cycle(
    *,
    target_root: Path,
    policy_root: Path,
    context_path: Path,
    report_path: Path,
    task_id: str,
    target_branch: str,
    model: str,
) -> dict[str, Any]:
    target = target_root.resolve()
    trusted = policy_root.resolve()
    report = report_path.resolve()
    if not TASK_ID_RE.fullmatch(task_id):
        raise CycleError("Selected task ID is invalid")
    if target_branch not in BRANCHES:
        raise CycleError("Selected target branch must be main or dev")
    if not target.is_dir() or not trusted.is_dir():
        raise CycleError("Target and trusted policy checkouts must both exist")
    if target == trusted or target in trusted.parents or trusted in target.parents:
        raise CycleError("Target source and trusted policy checkouts must be separate")
    if report == target or report == trusted or target in report.parents or trusted in report.parents:
        raise CycleError("Cycle report must be outside both Git checkouts")
    if os.environ.get("BOONTA_DETERMINISTIC_DELIVERY_ENABLED") != "true":
        reason = "The owner-controlled deterministic delivery gate is not enabled."
        action = "The repository owner must explicitly enable BOONTA_DETERMINISTIC_DELIVERY_ENABLED after reviewing the automation changes."
        _write_report(report, task_id=task_id, status="BLOCKED", target_branch=target_branch, blocker=reason, next_action=action)
        return {"status": "BLOCKED", "reason": reason, "provider_request_started": False}

    target_sha = _git_sha(target)
    policy_sha = _git_sha(trusted)
    try:
        allowlist = build_allowlist(
            target,
            expected_base_sha=target_sha,
            requested_task_id=task_id,
            policy_root=trusted,
            expected_policy_sha=policy_sha,
        )
    except (AllowlistError, ProposalError) as exc:
        reason = _clean_line(exc)
        _write_report(
            report, task_id=task_id, status="BLOCKED", target_branch=target_branch,
            blocker="Canonical owner/path preflight rejected the task: " + reason,
            next_action="Keep the task blocked until the canonical ledger and owner-reviewed exact-path policy permit this task.",
        )
        return {"status": "BLOCKED", "reason": reason, "provider_request_started": False}

    if allowlist.get("status") != "READY":
        reason = _clean_line(allowlist.get("reason") or allowlist.get("status") or "Task is not eligible for writing")
        _write_report(
            report, task_id=task_id, status="BLOCKED", target_branch=target_branch,
            blocker="No model request was made: " + reason,
            next_action="Complete the exact dependency or owner-approved path requirement in the canonical policy before retrying.",
        )
        return {"status": "BLOCKED", "reason": reason, "provider_request_started": False}
    if allowlist.get("task_id") != task_id or allowlist.get("base_sha") != target_sha or allowlist.get("policy_base_sha") != policy_sha:
        raise CycleError("Owner allow-list did not bind the exact task and checkout revisions")

    # The second writer gate is derived only from a freshly generated READY
    # report. A pre-set environment value cannot authorize an unapproved task.
    os.environ.pop("BOONTA_DETERMINISTIC_DELIVERY_OWNER_APPROVED", None)
    os.environ["BOONTA_DETERMINISTIC_DELIVERY_OWNER_APPROVED"] = "true"
    try:
        token = require_execution_gates(CANONICAL_REPOSITORY)
    except DeliveryExecutionError as exc:
        reason = _clean_line(exc)
        _write_report(
            report, task_id=task_id, status="BLOCKED", target_branch=target_branch,
            blocker="Delivery preflight rejected before model use: " + reason,
            next_action="Restore the required repository identity and scoped GitHub token; keep the delivery gate owner-controlled.",
        )
        return {"status": "BLOCKED", "reason": reason, "provider_request_started": False}

    context = context_path.read_text(encoding="utf-8")
    if not context.strip():
        raise CycleError("Authoritative task context is empty")

    with tempfile.TemporaryDirectory(prefix="boonta-patch-cycle-") as temporary:
        work = Path(temporary).resolve()
        if target in work.parents or trusted in work.parents:
            raise CycleError("Temporary pipeline workspace must be outside both Git checkouts")
        allowlist_path = work / "allowlist.json"
        proposal_path = work / "proposal.json"
        verified_path = work / "verified.json"
        allowlist_path.write_text(json.dumps(allowlist, sort_keys=True) + "\n", encoding="utf-8")
        context_file = work / "context.txt"
        context_file.write_text(context, encoding="utf-8")

        try:
            provider_report = run_provider_patch(
                repo_root=target,
                policy_root=trusted,
                allowlist_report=allowlist_path,
                prompt_file=context_file,
                output_proposal=proposal_path,
                expected_task_id=task_id,
                expected_base_sha=target_sha,
                expected_policy_sha=policy_sha,
                model=model,
                timeout_seconds=90,
            )
            verified = verify_in_isolated_worktree(
                target,
                proposal_path=proposal_path,
                allowlist_report_path=allowlist_path,
                expected_task_id=task_id,
                expected_base_sha=target_sha,
                policy_root=trusted,
                expected_policy_sha=policy_sha,
            )
            if verified.get("status") != "VERIFIED":
                raise PipelineError("Patch verification did not return VERIFIED")
            verified_path.write_text(json.dumps(verified, sort_keys=True) + "\n", encoding="utf-8")

            plan = build_delivery_plan(
                target,
                verified_report_path=verified_path,
                allowlist_report_path=allowlist_path,
                expected_task_id=task_id,
                expected_base_sha=target_sha,
                policy_root=trusted,
                expected_policy_sha=policy_sha,
            )
            if plan.get("status") != "DELIVERY_PLAN_READY" or plan.get("target_branch") != target_branch:
                raise DeliveryPlanError("Deterministic plan does not match the reserved task target branch")
            validate_plan_against_sources(
                plan,
                repo_root=target,
                verified_report_path=verified_path,
                allowlist_report_path=allowlist_path,
                expected_task_id=task_id,
                expected_base_sha=target_sha,
                repository=CANONICAL_REPOSITORY,
                policy_root=trusted,
                expected_policy_sha=policy_sha,
            )
            result = execute_delivery(
                plan,
                repo_root=target,
                verified_report_path=verified_path,
                allowlist_report_path=allowlist_path,
                expected_task_id=task_id,
                expected_base_sha=target_sha,
                repository=CANONICAL_REPOSITORY,
                token=token,
                policy_root=trusted,
                expected_policy_sha=policy_sha,
            )
        except (ProviderPatchError, ProposalError, PipelineError, DeliveryPlanError, DeliveryExecutionError, OSError, ValueError) as exc:
            reason = _clean_line(exc)
            _write_report(
                report, task_id=task_id, status="BLOCKED", target_branch=target_branch,
                blocker="The patch cycle stopped safely: " + reason,
                next_action="Review the exact failure and keep the task unmerged; retry only after the cause is corrected.",
            )
            return {
                "status": "BLOCKED",
                "reason": reason,
                "provider_request_started": os.environ.get("GITHUB_OUTPUT") is not None,
                "provider_model": model,
            }

        if (
            result.get("status") != "REVIEWABLE_PR_CREATED"
            or result.get("draft") is not False
            or result.get("auto_merge") is not False
            or result.get("merge_performed") is not False
        ):
            raise CycleError("GitHub writer did not confirm a reviewable, non-merged PR")
        pr_url = result.get("pull_request_url")
        head_sha = result.get("commit_sha")
        if not isinstance(pr_url, str) or not re.fullmatch(
            r"https://github\.com/Master-Chiken/boonta-reborn-88/pull/[1-9][0-9]*", pr_url
        ):
            raise CycleError("GitHub writer did not return an exact canonical PR URL")
        if not isinstance(head_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", head_sha):
            raise CycleError("GitHub writer did not return an exact 40-character commit SHA")
        _write_report(
            report,
            task_id=task_id,
            status="PROGRESS",
            target_branch=target_branch,
            evidence=f"{pr_url} @ {head_sha}",
        )
        return {
            "status": "PROGRESS",
            "task_id": task_id,
            "pull_request_url": pr_url,
            "head_sha": head_sha,
            "provider_model": provider_report.get("provider_model"),
            "changed_paths": provider_report.get("changed_paths"),
            "auto_merge": False,
            "merge_performed": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--policy-root", type=Path, required=True)
    parser.add_argument("--context-file", type=Path, required=True)
    parser.add_argument("--report-file", type=Path, required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--target-branch", required=True, choices=sorted(BRANCHES))
    parser.add_argument("--model", required=True, choices=[
        "groq/openai/gpt-oss-20b",
        "openrouter/openrouter/free",
    ])
    args = parser.parse_args()
    try:
        result = run_cycle(
            target_root=args.target_root,
            policy_root=args.policy_root,
            context_path=args.context_file,
            report_path=args.report_file,
            task_id=args.task_id,
            target_branch=args.target_branch,
            model=args.model,
        )
    except (CycleError, OSError, UnicodeError) as exc:
        print(json.dumps({"status": "REJECTED", "reason": _clean_line(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
