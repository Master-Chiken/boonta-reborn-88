#!/usr/bin/env python3
"""Validate Boonta's persistent autonomous task ledger; no network or API calls."""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "docs/automation/task-ledger.json"
STATUSES = {"queued", "active", "blocked", "in_review", "completed", "superseded"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TASK_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,63}$")
REPO = "Master-Chiken/boonta-reborn-88"


def _is_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def validate_ledger(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["ledger root must be a JSON object"]
    if data.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    if not _is_date(data.get("updated_at")):
        errors.append("updated_at must be an ISO date")
    policy = data.get("policy")
    if not isinstance(policy, dict) or policy.get("max_active_tasks") != 1:
        errors.append("policy.max_active_tasks must equal 1")
    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        return errors + ["tasks must be an array"]

    seen: set[str] = set()
    active = 0
    for index, task in enumerate(tasks):
        prefix = f"tasks[{index}]"
        if not isinstance(task, dict):
            errors.append(f"{prefix} must be an object")
            continue
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
            errors.append(f"{prefix}.task_id must be a stable uppercase identifier")
        elif task_id in seen:
            errors.append(f"duplicate task_id: {task_id}")
        else:
            seen.add(task_id)
        if not isinstance(task.get("title"), str) or not task["title"].strip():
            errors.append(f"{prefix}.title is required")
        if not isinstance(task.get("queue"), str) or not task["queue"].startswith("#"):
            errors.append(f"{prefix}.queue must reference a canonical issue")
        scope = task.get("platform_scope")
        if not isinstance(scope, list) or not scope or not all(isinstance(x, str) and x.strip() for x in scope):
            errors.append(f"{prefix}.platform_scope must be a non-empty string array")
        status = task.get("status")
        if not isinstance(status, str) or status not in STATUSES:
            errors.append(f"{prefix}.status must be one of {sorted(STATUSES)}")
        if status == "active":
            active += 1
        if status == "active" or task_id == "AUTOMATION-LEDGER-ACTIVATION":
            if task.get("target_branch") not in {"main", "dev"}:
                errors.append(f"{prefix}.target_branch must be main or dev for an executable task")
        for field in ("question", "next_action"):
            if not isinstance(task.get(field), str) or not task[field].strip():
                errors.append(f"{prefix}.{field} is required")
        criteria = task.get("acceptance_criteria")
        if not isinstance(criteria, list) or not criteria or not all(isinstance(x, str) and x.strip() for x in criteria):
            errors.append(f"{prefix}.acceptance_criteria must be a non-empty string array")
        evidence = task.get("evidence")
        if not isinstance(evidence, list) or not all(isinstance(x, str) and x.strip() for x in evidence):
            errors.append(f"{prefix}.evidence must be a string array")
        if not _is_date(task.get("updated_at")):
            errors.append(f"{prefix}.updated_at must be an ISO date")
        pr_url = task.get("pr_url")
        head_sha = task.get("head_sha")
        if status in {"in_review", "completed"}:
            expected = f"https://github.com/{REPO}/pull/"
            if not isinstance(pr_url, str) or not pr_url.startswith(expected):
                errors.append(f"{prefix} in {status} requires a repository PR URL")
            if not isinstance(head_sha, str) or not SHA_RE.fullmatch(head_sha):
                errors.append(f"{prefix} in {status} requires an exact 40-character head SHA")
        if status == "completed" and not evidence:
            errors.append(f"{prefix} completed task requires evidence")
    if active > 1:
        errors.append("at most one task may have status=active")
    return errors


def main() -> int:
    try:
        data = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Task ledger could not be read: {exc}", file=sys.stderr)
        return 1
    errors = validate_ledger(data)
    if errors:
        print("Boonta task ledger validation FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1
    tasks = data["tasks"]
    counts = {status: sum(task["status"] == status for task in tasks) for status in sorted(STATUSES)}
    print(f"Boonta task ledger valid: {len(tasks)} tasks; " + ", ".join(f"{k}={v}" for k, v in counts.items() if v))
    print("One-active-task limit and exact-head PR requirements are satisfied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
