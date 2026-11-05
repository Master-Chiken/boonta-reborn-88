#!/usr/bin/env python3
"""Read-only reconciliation of task-ledger PR records against GitHub's live API."""
from __future__ import annotations

import base64
import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "docs/automation/task-ledger.json"
LEDGER_REPO_PATH = "docs/automation/task-ledger.json"
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


def github_json(url: str, token: str) -> dict | list:
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


def fetch_pull_request_files(number: int, token: str) -> set[str]:
    """Return changed paths for a PR, paging so the ledger-file decision is exact."""
    paths: set[str] = set()
    for page in range(1, 31):
        url = (
            f"https://api.github.com/repos/{EXPECTED_REPO}/pulls/{number}/files"
            f"?per_page=100&page={page}"
        )
        result = github_json(url, token)
        if not isinstance(result, list):
            raise ValueError(f"GitHub returned an invalid changed-file list for PR #{number}")
        paths.update(item.get("filename", "") for item in result if isinstance(item, dict))
        if len(result) < 100:
            return paths
    raise ValueError(f"PR #{number} exceeds the changed-file audit limit")


def fetch_main_ledger(token: str) -> dict:
    """Read the canonical ledger from main, not a potentially stale PR merge ref."""
    url = (
        f"https://api.github.com/repos/{EXPECTED_REPO}/contents/"
        f"{LEDGER_REPO_PATH}?ref=main"
    )
    document = github_json(url, token)
    if not isinstance(document, dict) or document.get("encoding") != "base64":
        raise ValueError("GitHub did not return the main task ledger as base64 content")
    encoded = document.get("content")
    if not isinstance(encoded, str) or not encoded:
        raise ValueError("GitHub returned empty content for the main task ledger")
    raw = base64.b64decode(encoded)
    return json.loads(raw.decode("utf-8"))


def load_ledger(
    token: str,
    event_name: str,
    changed_files: set[str],
    local_path: Path = LEDGER_PATH,
) -> dict:
    """Use a PR's proposed ledger only when that PR actually changes the ledger file."""
    if event_name == "pull_request" and LEDGER_REPO_PATH not in changed_files:
        print(
            "Using the canonical main-branch task ledger; "
            "the pull-request merge ref may lag behind a newer base-branch commit."
        )
        return fetch_main_ledger(token)
    return json.loads(local_path.read_text(encoding="utf-8"))


def fetch_event_changed_files(token: str, event_name: str) -> set[str]:
    if event_name != "pull_request":
        return set()
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not event_path:
        raise ValueError("GITHUB_EVENT_PATH is required for pull_request ledger-source selection")
    payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("GitHub pull_request event payload must be an object")
    pull_request = payload.get("pull_request") or {}
    number = payload.get("number") or pull_request.get("number")
    if not isinstance(number, int) or isinstance(number, bool) or number < 1:
        raise ValueError("GitHub pull_request event did not contain a valid PR number")
    return fetch_pull_request_files(number, token)


def fetch_pull_request(number: int, token: str) -> dict:
    url = f"https://api.github.com/repos/{EXPECTED_REPO}/pulls/{number}"
    result = github_json(url, token)
    if not isinstance(result, dict):
        raise ValueError(f"GitHub returned an invalid response for PR #{number}")
    return result


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    if not token or repository != EXPECTED_REPO:
        print("Live task-ledger audit requires the repository-scoped GitHub token.", file=sys.stderr)
        return 1
    try:
        changed_files = fetch_event_changed_files(token, event_name)
        ledger = load_ledger(token, event_name, changed_files)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"Task ledger could not be read from the correct source: {exc}", file=sys.stderr)
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
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{task.get('task_id', '<unknown>')}: unable to read PR #{number}: {exc}")
            continue
        if (
            pull_request.get("number") != number
            or pull_request.get("base", {}).get("repo", {}).get("full_name") != EXPECTED_REPO
        ):
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
