#!/usr/bin/env python3
"""Validate the declarative agent role registry; no network or model calls."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "docs/automation/agent-roles.json"
REQUIRED_POLICY = {
    "max_active_missions": 1,
    "max_provider_invocations_per_run": 1,
    "repository_writers": ["github_actions"],
    "model_agents_receive_write_credentials": False,
    "paid_fallback": False,
    "auto_merge": False,
    "human_merge_approval_required": True,
    "qa_must_be_independent": True,
}
FORBIDDEN_FOR_MODEL = {
    "merge", "auto_merge", "force_push", "write_protected_branch",
    "change_secrets", "change_permissions", "change_billing",
    "change_branch_protection", "change_provider_order", "change_cooldowns",
    "paid_fallback", "change_governance",
}


def validate_registry(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["registry root must be an object"]
    if data.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    if data.get("status") != "declarative_only":
        errors.append("status must remain declarative_only until separately approved")
    if data.get("execution_plane") != "github_actions":
        errors.append("execution_plane must remain github_actions")
    if data.get("canonical_task_ledger") != "docs/automation/task-ledger.json":
        errors.append("canonical task ledger path must not change")
    if data.get("provider_order") != ["gemini", "openrouter_free", "groq_free"]:
        errors.append("provider order must remain Gemini, OpenRouter Free, Groq Free")
    policy = data.get("policy")
    if not isinstance(policy, dict):
        return errors + ["policy must be an object"]
    for key, expected in REQUIRED_POLICY.items():
        if policy.get(key) != expected:
            errors.append(f"policy.{key} must equal {expected!r}")
    objectives = data.get("objectives")
    if not isinstance(objectives, list) or not objectives:
        errors.append("objectives must be a non-empty array")
    else:
        objective_ids = []
        for index, objective in enumerate(objectives):
            if not isinstance(objective, dict):
                errors.append(f"objectives[{index}] must be an object")
                continue
            objective_id = objective.get("id")
            if not isinstance(objective_id, str) or not objective_id.startswith("BOONTA-"):
                errors.append(f"objectives[{index}].id must be a stable BOONTA identifier")
            else:
                objective_ids.append(objective_id)
            for field in ("title", "description"):
                if not isinstance(objective.get(field), str) or not objective[field].strip():
                    errors.append(f"objectives[{index}].{field} is required")
        if len(objective_ids) != len(set(objective_ids)):
            errors.append("objective IDs must be unique")
    roles = data.get("roles")
    if not isinstance(roles, list) or not roles:
        return errors + ["roles must be a non-empty array"]
    by_id: dict[str, dict[str, Any]] = {}
    for index, role in enumerate(roles):
        prefix = f"roles[{index}]"
        if not isinstance(role, dict):
            errors.append(f"{prefix} must be an object")
            continue
        role_id = role.get("id")
        if not isinstance(role_id, str) or not role_id:
            errors.append(f"{prefix}.id is required")
            continue
        if role_id in by_id:
            errors.append(f"duplicate role id: {role_id}")
        by_id[role_id] = role
        for field in ("title", "kind", "unit"):
            if not isinstance(role.get(field), str) or not role[field].strip():
                errors.append(f"{prefix}.{field} is required")
        for field in ("responsibilities", "allowed_capabilities"):
            values = role.get(field)
            if not isinstance(values, list) or not values or not all(isinstance(v, str) and v.strip() for v in values):
                errors.append(f"{prefix}.{field} must be a non-empty string array")
        forbidden = role.get("forbidden_actions")
        if not isinstance(forbidden, list) or not all(isinstance(v, str) and v.strip() for v in forbidden):
            errors.append(f"{prefix}.forbidden_actions must be a string array")
        if role_id != "human-owner" and not forbidden:
            errors.append(f"{prefix}.forbidden_actions must not be empty")
    if "human-owner" not in by_id:
        errors.append("human-owner root role is required")
        return errors
    roots = [role_id for role_id, role in by_id.items() if role.get("manager_id") is None]
    if roots != ["human-owner"]:
        errors.append("human-owner must be the only root role")
    for role_id, role in by_id.items():
        manager = role.get("manager_id")
        if role_id == "human-owner":
            continue
        if not isinstance(manager, str) or manager not in by_id:
            errors.append(f"{role_id} must have exactly one existing manager_id")
            continue
        if role.get("kind") == "model_role":
            forbidden = set(role.get("forbidden_actions", []))
            missing = FORBIDDEN_FOR_MODEL - forbidden
            if missing:
                errors.append(f"{role_id} missing forbidden actions: {sorted(missing)}")
    # Every manager chain must terminate at the sole human root; cycles fail closed.
    for start in by_id:
        seen: set[str] = set()
        current = start
        while current != "human-owner":
            if current in seen:
                errors.append(f"manager cycle detected from {start}")
                break
            seen.add(current)
            role = by_id.get(current)
            if not role:
                errors.append(f"manager chain from {start} references missing role {current}")
                break
            manager = role.get("manager_id")
            if not isinstance(manager, str) or manager not in by_id:
                errors.append(f"manager chain from {start} does not reach human-owner")
                break
            current = manager
    if by_id.get("qa", {}).get("manager_id") == by_id.get("cto", {}).get("id"):
        errors.append("QA must not report to CTO; preserve independent implementation review")
    if by_id.get("chief-of-staff", {}).get("kind") != "deterministic":
        errors.append("chief-of-staff must be deterministic, not another model role")
    return errors


def main() -> int:
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Agent role registry could not be read: {exc}", file=sys.stderr)
        return 1
    errors = validate_registry(data)
    if errors:
        print("Agent role registry validation FAILED:")
        for error in errors:
            print(f" - {error}")
        return 1
    print(f"Agent role registry valid: {len(data['roles'])} roles; declarative-only; no permissions granted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
