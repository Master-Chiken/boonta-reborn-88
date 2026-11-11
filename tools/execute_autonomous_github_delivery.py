#!/usr/bin/env python3
"""Execute a fully revalidated deterministic GitHub delivery plan.

Dry-run is the default and performs no network access. Live execution requires
--execute plus two exact-true environment gates and a GitHub token. It creates
a commit/ref and a draft PR only; it never merges or enables auto-merge.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from autonomous_patch_proposal import ProposalError
from build_autonomous_delivery_plan import (
    DeliveryPlanError,
    build_delivery_plan,
)

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TASK_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,63}$")
MAX_PLAN_BYTES = 512 * 1024
API_ROOT = "https://api.github.com"


class DeliveryExecutionError(RuntimeError):
    """Raised when a dry-run or guarded GitHub write cannot be trusted."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DeliveryExecutionError(f"Duplicate JSON property: {key}")
        value[key] = item
    return value


def load_plan(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise DeliveryExecutionError("Delivery plan file must not be a symlink")
    try:
        if path.stat().st_size > MAX_PLAN_BYTES:
            raise DeliveryExecutionError("Delivery plan exceeds the 512 KiB input limit")
        raw = path.read_text(encoding="utf-8")
        plan = json.loads(raw, object_pairs_hook=_unique_object)
    except DeliveryExecutionError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DeliveryExecutionError("Delivery plan is not readable valid UTF-8 JSON") from exc
    if len(raw.encode("utf-8")) > MAX_PLAN_BYTES:
        raise DeliveryExecutionError("Delivery plan exceeds the 512 KiB input limit")
    if not isinstance(plan, dict):
        raise DeliveryExecutionError("Delivery plan root must be an object")
    return plan


def validate_plan_against_sources(
    plan: dict[str, Any],
    *,
    repo_root: Path,
    verified_report_path: Path,
    allowlist_report_path: Path,
    expected_task_id: str,
    expected_base_sha: str,
    repository: str,
) -> None:
    if not isinstance(repository, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise DeliveryExecutionError("Repository must use the owner/name form")
    if not isinstance(expected_task_id, str) or not TASK_ID_RE.fullmatch(expected_task_id):
        raise DeliveryExecutionError("Expected task ID is invalid")
    if not isinstance(expected_base_sha, str) or not SHA_RE.fullmatch(expected_base_sha):
        raise DeliveryExecutionError("Expected base SHA is invalid")

    try:
        regenerated = build_delivery_plan(
            repo_root,
            verified_report_path=verified_report_path,
            allowlist_report_path=allowlist_report_path,
            expected_task_id=expected_task_id,
            expected_base_sha=expected_base_sha,
        )
    except (DeliveryPlanError, ProposalError) as exc:
        raise DeliveryExecutionError(f"Source evidence failed revalidation: {exc}") from exc
    if plan != regenerated:
        raise DeliveryExecutionError("Supplied delivery plan differs from the freshly regenerated deterministic plan")

    write_plan = plan.get("github_write_plan")
    if not isinstance(write_plan, dict):
        raise DeliveryExecutionError("Plan is missing the deterministic GitHub write payload")
    if write_plan.get("auto_merge") is not False:
        raise DeliveryExecutionError("Auto-merge must be disabled")
    if write_plan.get("create_pull_request", {}).get("draft") is not True:
        raise DeliveryExecutionError("Only draft pull requests are permitted by this prototype")
    preconditions = write_plan.get("preconditions", {})
    if (
        preconditions.get("target_branch_head_must_equal") != expected_base_sha
        or preconditions.get("branch_must_not_exist") is not True
        or preconditions.get("open_pr_for_task_must_not_exist") is not True
        or preconditions.get("independent_review_required") is not True
    ):
        raise DeliveryExecutionError("GitHub write preconditions are incomplete or weakened")


def _api_request(
    token: str,
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    allowed_404: bool = False,
    timeout: int = 20,
) -> dict[str, Any] | list[Any] | None:
    url = API_ROOT + path
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "boonta-reborn-deterministic-writer",
            **({"Content-Type": "application/json"} if data is not None else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise DeliveryExecutionError("GitHub API response exceeded the 2 MiB limit")
            if response.status == 204 or not raw:
                return {}
    except urllib.error.HTTPError as exc:
        if allowed_404 and exc.code == 404:
            return None
        # Deliberately omit response body and headers; they can contain sensitive
        # repository details and are not needed to diagnose the HTTP status.
        raise DeliveryExecutionError(f"GitHub API {method} failed with HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise DeliveryExecutionError(f"GitHub API {method} transport failed: {type(exc).__name__}") from exc

    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise DeliveryExecutionError("GitHub API returned invalid UTF-8 JSON") from exc
    if not isinstance(value, (dict, list)):
        raise DeliveryExecutionError("GitHub API returned an unexpected response shape")
    return value


def _find_open_task_pr(
    token: str,
    repository: str,
    task_id: str,
    *,
    request=_api_request,
) -> dict[str, Any] | None:
    marker = f"BOONTA_TASK_ID: {task_id}"
    page = 1
    matches: list[dict[str, Any]] = []
    while page <= 10:
        result = request(
            token,
            "GET",
            f"/repos/{repository}/pulls?state=open&per_page=100&page={page}",
        )
        if not isinstance(result, list):
            raise DeliveryExecutionError("GitHub open-PR list returned an unexpected response shape")
        for item in result:
            if not isinstance(item, dict):
                continue
            body = item.get("body")
            if isinstance(body, str) and marker in body:
                matches.append(item)
        if len(result) < 100:
            break
        page += 1
    else:
        raise DeliveryExecutionError("More than 1000 open PRs; duplicate-task check cannot be completed")
    if len(matches) > 1:
        raise DeliveryExecutionError("Multiple open PRs already carry this canonical task marker")
    return matches[0] if matches else None


def execute_delivery(
    plan: dict[str, Any],
    *,
    repository: str,
    token: str,
    request=_api_request,
) -> dict[str, Any]:
    approved_token = require_execution_gates(repository)
    if token != approved_token:
        raise DeliveryExecutionError("The supplied token does not match the explicitly gated execution token")
    write_plan = plan["github_write_plan"]
    preconditions = write_plan["preconditions"]
    target_branch = plan["target_branch"]
    base_sha = plan["base_sha"]
    branch_name = plan["branch_name"]
    task_id = plan["task_id"]
    base_ref = request(
        token, "GET",
        f"/repos/{repository}/git/ref/heads/{urllib.parse.quote(target_branch, safe='/')}",
    )
    base_ref_object = base_ref.get("object") if isinstance(base_ref, dict) else None
    if not isinstance(base_ref_object, dict) or base_ref_object.get("sha") != preconditions["target_branch_head_must_equal"]:
        raise DeliveryExecutionError("Target branch moved since the patch was verified; rebuild and retest")

    existing_branch = request(
        token, "GET",
        f"/repos/{repository}/git/ref/heads/{urllib.parse.quote(branch_name, safe='/')}",
        allowed_404=True,
    )
    if existing_branch is not None:
        raise DeliveryExecutionError("Deterministic delivery branch already exists; reconcile it instead of overwriting")

    existing_pr = _find_open_task_pr(token, repository, task_id, request=request)
    if existing_pr is not None:
        raise DeliveryExecutionError("An open PR already exists for this task; reconcile it instead of duplicating it")

    create_tree_plan = write_plan["create_tree"]
    tree_payload = {
        "base_tree": create_tree_plan["base_tree_sha"],
        "tree": create_tree_plan["tree_elements"],
    }
    tree = request(
        token, "POST", f"/repos/{repository}/git/trees",
        payload=tree_payload,
    )
    tree_sha = tree.get("sha") if isinstance(tree, dict) else None
    if not isinstance(tree_sha, str) or not SHA_RE.fullmatch(tree_sha):
        raise DeliveryExecutionError("GitHub did not return a valid tree SHA")

    commit_payload = dict(write_plan["create_commit"])
    commit_payload["tree"] = tree_sha
    commit_payload["parents"] = [base_sha]
    commit_payload.pop("parent_sha", None)
    commit = request(
        token, "POST", f"/repos/{repository}/git/commits",
        payload=commit_payload,
    )
    commit_sha = commit.get("sha") if isinstance(commit, dict) else None
    commit_tree = commit.get("tree") if isinstance(commit, dict) else None
    commit_parents = commit.get("parents") if isinstance(commit, dict) else None
    if not isinstance(commit_sha, str) or not SHA_RE.fullmatch(commit_sha):
        raise DeliveryExecutionError("GitHub did not return a valid commit SHA")
    if not isinstance(commit_tree, dict) or commit_tree.get("sha") != tree_sha:
        raise DeliveryExecutionError("GitHub commit response does not reference the exact verified tree")
    if (
        not isinstance(commit_parents, list)
        or len(commit_parents) != 1
        or not isinstance(commit_parents[0], dict)
        or commit_parents[0].get("sha") != base_sha
    ):
        raise DeliveryExecutionError("GitHub commit response does not contain the exact single verified parent")

    # Create-ref is atomic. Do not force-update or overwrite an existing ref.
    expected_ref = write_plan["create_ref"]["ref"]
    ref = request(
        token, "POST", f"/repos/{repository}/git/refs",
        payload={"ref": expected_ref, "sha": commit_sha},
    )
    ref_object = ref.get("object") if isinstance(ref, dict) else None
    if (
        not isinstance(ref, dict)
        or ref.get("ref") != expected_ref
        or not isinstance(ref_object, dict)
        or ref_object.get("sha") != commit_sha
    ):
        raise DeliveryExecutionError("GitHub did not confirm the exact new branch ref")

    # Recheck the target immediately before opening the PR. If it moved after
    # branch creation, leave the branch for human reconciliation and do not PR.
    latest_base = request(
        token, "GET",
        f"/repos/{repository}/git/ref/heads/{urllib.parse.quote(target_branch, safe='/')}",
    )
    latest_base_object = latest_base.get("object") if isinstance(latest_base, dict) else None
    if not isinstance(latest_base_object, dict) or latest_base_object.get("sha") != base_sha:
        raise DeliveryExecutionError("Target branch moved after branch creation; no PR was opened")

    # Recheck for a concurrently opened PR for this task just before create.
    if _find_open_task_pr(token, repository, task_id, request=request) is not None:
        raise DeliveryExecutionError("An open PR appeared for this task during delivery; no duplicate PR was opened")

    pr_payload = write_plan["create_pull_request"]
    pr = request(
        token, "POST", f"/repos/{repository}/pulls",
        payload=pr_payload,
    )
    pr_url = pr.get("html_url") if isinstance(pr, dict) else None
    pr_number = pr.get("number") if isinstance(pr, dict) else None
    pr_head = pr.get("head") if isinstance(pr, dict) else None
    pr_base = pr.get("base") if isinstance(pr, dict) else None
    if (
        not isinstance(pr_url, str)
        or not pr_url.startswith(f"https://github.com/{repository}/pull/")
        or type(pr_number) is not int
        or pr_number < 1
        or not isinstance(pr, dict)
        or pr.get("draft") is not True
        or (isinstance(pr_head, dict) and pr_head.get("ref") != branch_name)
        or (isinstance(pr_base, dict) and pr_base.get("ref") != target_branch)
    ):
        raise DeliveryExecutionError("GitHub did not confirm the exact draft pull request")

    return {
        "status": "DRAFT_PR_CREATED",
        "repository": repository,
        "task_id": task_id,
        "base_sha": base_sha,
        "branch_name": branch_name,
        "tree_sha": tree_sha,
        "commit_sha": commit_sha,
        "pull_request_number": pr_number,
        "pull_request_url": pr_url,
        "draft": True,
        "auto_merge": False,
        "merge_performed": False,
        "remote_write_performed": True,
    }


def require_execution_gates(repository: str) -> str:
    if os.environ.get("BOONTA_DETERMINISTIC_DELIVERY_ENABLED") != "true":
        raise DeliveryExecutionError("BOONTA_DETERMINISTIC_DELIVERY_ENABLED must equal exact string true")
    if os.environ.get("BOONTA_DETERMINISTIC_DELIVERY_OWNER_APPROVED") != "true":
        raise DeliveryExecutionError("BOONTA_DETERMINISTIC_DELIVERY_OWNER_APPROVED must equal exact string true")
    expected_repo = os.environ.get("GITHUB_REPOSITORY")
    if expected_repo and expected_repo != repository:
        raise DeliveryExecutionError("GITHUB_REPOSITORY does not match the requested repository")
    token = os.environ.get("GITHUB_TOKEN", "")
    if len(token) < 20:
        raise DeliveryExecutionError("A GitHub token with the required repository permissions is required")
    return token


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--verified-report", type=Path, required=True)
    parser.add_argument("--allowlist-report", type=Path, required=True)
    parser.add_argument("--expected-task-id", required=True)
    parser.add_argument("--expected-base-sha", required=True)
    parser.add_argument("--execute", action="store_true", help="perform GitHub writes; disabled by default")
    args = parser.parse_args()

    try:
        plan = load_plan(args.plan)
        validate_plan_against_sources(
            plan,
            repo_root=args.repo_root,
            verified_report_path=args.verified_report,
            allowlist_report_path=args.allowlist_report,
            expected_task_id=args.expected_task_id,
            expected_base_sha=args.expected_base_sha,
            repository=args.repository,
        )
        if not args.execute:
            print(json.dumps({
                "status": "DRY_RUN_VALIDATED",
                "task_id": args.expected_task_id,
                "base_sha": args.expected_base_sha,
                "branch_name": plan["branch_name"],
                "draft": True,
                "remote_write_performed": False,
                "reason": "Pass --execute and both explicit environment gates to create a draft PR.",
            }, sort_keys=True))
            return 0

        token = require_execution_gates(args.repository)
        outcome = execute_delivery(plan, repository=args.repository, token=token)
    except (DeliveryExecutionError, DeliveryPlanError, ProposalError) as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(outcome, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
