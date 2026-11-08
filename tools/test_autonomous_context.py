#!/usr/bin/env python3
"""Offline tests for the schema-v2 autonomous context builder."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_autonomous_context", ROOT / "tools/build_autonomous_context.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture(root: Path) -> str:
    (root / "docs/automation").mkdir(parents=True)
    (root / "docs/REVERSE_ENGINEERING_FIRST.md").write_text(
        "DISCOVER VERIFY EXTRACT/CONVERT/REUSE GameCube/Wii", encoding="utf-8"
    )
    (root / "docs/automation/AUTONOMOUS_CONTEXT_BUDGET.md").write_text(
        "One model provider invocation at most; €0; 1,500 tokens", encoding="utf-8"
    )
    summary = {
        "schema_version": 2,
        "source": "docs/automation/task-ledger.json",
        "updated_at": "2026-11-08",
        "policy": {"max_active_tasks": 1, "completed_requires_merged_pr": True},
        "tasks": [{
            "task_id": "AUTOMATION-LEDGER-ACTIVATION",
            "title": "Activate and validate persistent autonomous task tracking",
            "status": "blocked",
            "target_branch": "main",
            "platform_scope": ["automation"],
            "question_excerpt": "Does the loop reconcile the task ledger?",
            "acceptance_criteria_total": 2,
            "acceptance_criteria_excerpt": ["One active task maximum", "Exact PR state is recorded"],
            "pr_url": None,
            "head_sha": None,
            "next_action_excerpt": "Complete a verified provider cycle.",
        }],
    }
    (root / "docs/automation/task-ledger-summary.json").write_text(
        json.dumps(summary), encoding="utf-8"
    )
    return (
        "Task ID: AUTOMATION-LEDGER-ACTIVATION\n"
        "Task title: Activate and validate persistent autonomous task tracking\n"
        "Target branch: main\n"
        "Platform scope: automation\nQuestion: reconcile the ledger"
    )


with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    context = fixture(root)
    rendered = MODULE.build_context(
        root, "AUTOMATION-LEDGER-ACTIVATION",
        "Activate and validate persistent autonomous task tracking",
        "main", context,
    )
    assert "schema v2" not in rendered  # the output names the canonical ledger version explicitly
    assert "Canonical ledger v2" in rendered
    assert "One active task maximum" in rendered
    assert "Target branch: main" in rendered

    for kwargs in (
        {"target_branch": "dev"},
        {"task_title": "Wrong title"},
    ):
        params = {
            "root": root,
            "task_id": "AUTOMATION-LEDGER-ACTIVATION",
            "task_title": "Activate and validate persistent autonomous task tracking",
            "target_branch": "main",
            "task_context": context,
        }
        params.update(kwargs)
        try:
            MODULE.build_context(**params)
        except MODULE.ContextBuildError:
            pass
        else:
            raise AssertionError(f"Expected mismatched task metadata to fail: {kwargs}")

    summary_path = root / "docs/automation/task-ledger-summary.json"
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    payload["schema_version"] = 1
    summary_path.write_text(json.dumps(payload), encoding="utf-8")
    try:
        MODULE.build_context(
            root, "AUTOMATION-LEDGER-ACTIVATION",
            "Activate and validate persistent autonomous task tracking",
            "main", context,
        )
    except MODULE.ContextBuildError:
        pass
    else:
        raise AssertionError("Expected a legacy schema to fail closed")

print("PASS: schema-v2 task identity, target branch, task excerpts and fail-closed cases")
