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
ROLE_REGISTRY_PATH = ROOT / "docs/automation/agent-roles.json"
ROLE_ID_RE = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
OBJECTIVE_ID_RE = re.compile(r"^[A-Z][A-Z0-9-]{2,63}$")
STATUSES = {"queued", "active", "blocked", "in_review", "completed", "superseded"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TASK_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,63}$")
REPO = "Master-Chiken/boonta-reborn-88"
READ_PATH_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".json", ".yaml", ".yml", ".toml", ".md", ".c", ".h", ".cc", ".cpp", ".hpp", ".cmake", ".sh"}
READ_PATH_BLOCKED = {"docs/automation/task-ledger.json", "docs/automation/task-ledger-summary.json"}


def _valid_read_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or len(value) > 120:
        return False
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", value) or "\\" in value:
        return False
    parts = value.split("/")
    if value.startswith("/") or any(part in {"", ".", ".."} for part in parts):
        return False
    if value in READ_PATH_BLOCKED or any(part.lower() in {"generated", "roms", "private"} for part in parts):
        return False
    return Path(value).suffix.lower() in READ_PATH_EXTENSIONS


def _is_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def validate_ledger(data: Any, role_ids: set[str] | None = None, objective_ids: set[str] | None = None) -> list[str]:
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
        owner_role_id = task.get("owner_role_id")
        if not isinstance(owner_role_id, str) or not ROLE_ID_RE.fullmatch(owner_role_id):
            errors.append(f"{prefix}.owner_role_id must be a stable role identifier")
        elif role_ids is not None and owner_role_id not in role_ids:
            errors.append(f"{prefix}.owner_role_id references an unknown role")
        parent_objective_id = task.get("parent_objective_id")
        if not isinstance(parent_objective_id, str) or not OBJECTIVE_ID_RE.fullmatch(parent_objective_id):
            errors.append(f"{prefix}.parent_objective_id must be a stable objective identifier")
        elif objective_ids is not None and parent_objective_id not in objective_ids:
            errors.append(f"{prefix}.parent_objective_id references an unknown objective")
        if not isinstance(task.get("queue"), str) or not task["queue"].startswith("#"):
            errors.append(f"{prefix}.queue must reference a canonical issue")
        scope = task.get("platform_scope")
        if not isinstance(scope, list) or not scope or not all(isinstance(x, str) and x.strip() for x in scope):
            errors.append(f"{prefix}.platform_scope must be a non-empty string array")
        status = task.get("status")
        if not isinstance(status, str) or status not in STATUSES:
            errors.append(f"{prefix}.status must be one of {sorted(STATUSES)}")
        dependencies = task.get("depends_on")
        if not isinstance(dependencies, list) or not all(
            isinstance(value, str) and TASK_ID_RE.fullmatch(value) for value in dependencies
        ):
            errors.append(f"{prefix}.depends_on must be an array of stable task IDs")
        elif len(dependencies) != len(set(dependencies)) or task_id in dependencies:
            errors.append(f"{prefix}.depends_on must be unique and cannot include itself")
        if status == "active":
            active += 1
        read_paths = task.get("read_paths")
        requires_read_paths = status == "active" or (
            task_id == "AUTOMATION-LEDGER-ACTIVATION" and status == "blocked"
        )
        if requires_read_paths and not (
            isinstance(read_paths, list) and 1 <= len(read_paths) <= 4
            and all(_valid_read_path(path) for path in read_paths)
            and len(set(read_paths)) == len(read_paths)
        ):
            errors.append(f"{prefix}.read_paths must contain 1-4 unique safe repository text paths for executable tasks")
        elif read_paths is not None and not (
            isinstance(read_paths, list) and len(read_paths) <= 4
            and all(_valid_read_path(path) for path in read_paths)
            and len(set(read_paths)) == len(read_paths)
        ):
            errors.append(f"{prefix}.read_paths must contain at most four unique safe repository text paths")
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

    task_by_id = {
        task["task_id"]: task for task in tasks
        if isinstance(task, dict) and isinstance(task.get("task_id"), str)
    }
    for task_id, task in task_by_id.items():
        dependencies = task.get("depends_on", [])
        if not isinstance(dependencies, list):
            continue
        for dependency_id in dependencies:
            dependency = task_by_id.get(dependency_id)
            if dependency is None:
                errors.append(f"{task_id} depends_on unknown task {dependency_id}")
            elif task.get("status") in {"active", "in_review", "completed"} and dependency.get("status") != "completed":
                errors.append(
                    f"{task_id} cannot be {task.get('status')} until dependency "
                    f"{dependency_id} is completed"
                )

    # Dependency graph must be acyclic; queued tasks may wait, but never form a loop.
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        if task_id in visiting:
            errors.append(f"task dependency cycle detected at {task_id}")
            return
        if task_id in visited:
            return
        visiting.add(task_id)
        task = task_by_id.get(task_id, {})
        dependencies = task.get("depends_on", [])
        if isinstance(dependencies, list):
            for dependency_id in dependencies:
                if dependency_id in task_by_id:
                    visit(dependency_id)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in task_by_id:
        visit(task_id)
    return errors


def main() -> int:
    try:
        data = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        registry = json.loads(ROLE_REGISTRY_PATH.read_text(encoding="utf-8"))
        roles = registry.get("roles", [])
        objectives = registry.get("objectives", [])
        role_ids = {role["id"] for role in roles if isinstance(role, dict) and isinstance(role.get("id"), str)}
        objective_ids = {objective["id"] for objective in objectives if isinstance(objective, dict) and isinstance(objective.get("id"), str)}
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"Task ledger or role registry could not be read: {exc}", file=sys.stderr)
        return 1
    errors = validate_ledger(data, role_ids, objective_ids)
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
