#!/usr/bin/env python3
"""Read-only reconciliation of task-ledger PR records against GitHub's live API."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "docs/automation/task-ledger.json"
EXPECTED_REPO = "Master-Chiken/boonta-reborn-88"
PR_URL_RE = re.compile(r"^https://github\.com/" + re.escape(EXPECTED_REPO) + r"/pull/(\d+)$")


def reconcile_task(task: dict, pull_request: dict) -> list[str]:
    errors: list[str] = []
    task_id = task.get("task_id", "<unknown>")
    status = task.get("status")
    head = pull_request.get("head") or {}
    live_sha = head.get("sha")
    expected_sha = task.get("head_sha")
    if expected_sha != live_sha:
        errors.append(
            f"{task_id}: ledger head SHA {expected_sha!r} does not match live PR head {live_sha!r}"
        )
    if status == "in_review":
        if pull_request.get("state") != "open" or pull_request.get("merged_at") is not None:
            errors.append(f"{task_id}: in_review task must point to an open, unmerged PR")
    elif status == "completed":
        if pull_request.get("merged_at") is None:
            errors.append(f"{task_id}: completed task must point to a merged PR")
    return errors


def fetch_pull_request(number: int, token: str) -> dict:
    url = f"https://api.github.com/repos/{EXPECTED_REPO}/pulls/{number}"
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "boonta-task-ledger-audit",
        },
    )
    with urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if not token or repository != EXPECTED_REPO:
        print("Live task-ledger audit requires the repository-scoped GitHub token.", file=sys.stderr)
        return 1
    try:
        ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Task ledger could not be read: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    checked = 0
    for task in ledger.get("tasks", []):
        status = task.get("status")
        if status not in {"in_review", "completed"}:
            continue
        match = PR_URL_RE.fullmatch(task.get("pr_url", ""))
        if not match:
            errors.append(f"{task.get('task_id', '<unknown>')}: invalid repository PR URL")
            continue
        number = int(match.group(1))
        try:
            pull_request = fetch_pull_request(number, token)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            errors.append(f"{task.get('task_id', '<unknown>')}: unable to read PR #{number}: {exc}")
            continue
        if pull_request.get("number") != number or pull_request.get("base", {}).get("repo", {}).get("full_name") != EXPECTED_REPO:
            errors.append(f"{task.get('task_id', '<unknown>')}: API returned an unexpected pull request")
            continue
        checked += 1
        errors.extend(reconcile_task(task, pull_request))

    if errors:
        print("Live task-ledger reconciliation FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1
    print(f"Live task-ledger reconciliation passed: {checked} PR records match state and exact head SHA.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
