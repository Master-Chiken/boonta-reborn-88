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
            "read_paths": ["tools/check_task_ledger.py", "tools/test_check_task_ledger.py"],
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
        "Title: Activate and validate persistent autonomous task tracking\n"
        "Target branch: main\n"
        "Platform scope: automation\nQuestion: Does the loop reconcile the task ledger?\nAcceptance criteria (2 total; compact index shows up to five):\n- One active task maximum\n- Exact PR state is recorded\nNext action: Complete a verified provider cycle.\nRead-only source paths (select at most one): tools/check_task_ledger.py, tools/test_check_task_ledger.py"
    )


with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    context = fixture(root)
    rendered = MODULE.build_context(
        root, "AUTOMATION-LEDGER-ACTIVATION",
        "Activate and validate persistent autonomous task tracking",
        "main", context,
    )
    assert "Canonical ledger v2" in rendered
    assert "One active task maximum" in rendered
    assert "Target branch: main" in rendered

    # Regression: full activation handoffs must survive beyond the former 1,200-char cap.
    long_handoff = context + "\n" + ("Supplemental verified evidence note. " * 30)
    assert 1200 < len(long_handoff) <= 2200
    long_rendered = MODULE.build_context(
        root, "AUTOMATION-LEDGER-ACTIVATION",
        "Activate and validate persistent autonomous task tracking",
        "main", long_handoff, max_chars=2400, max_task_context=2200,
    )
    assert len(long_rendered) <= 2400
    assert "One active task maximum" in long_rendered
    assert "Exact PR state is recorded" in long_rendered
    assert "Complete a verified provider cycle." in long_rendered

    # Regression for the real activation handoff budget: preserve every
    # required excerpt when the preflight context is about 1.35k characters.
    summary_path = root / "docs/automation/task-ledger-summary.json"
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    task = payload["tasks"][0]
    task["question_excerpt"] = "Q" * 105
    task["next_action_excerpt"] = "N" * 400
    task["acceptance_criteria_total"] = 5
    task["acceptance_criteria_excerpt"] = [
        "A" * 48, "B" * 78, "C" * 35, "D" * 93, "E" * 133,
    ]
    summary_path.write_text(json.dumps(payload), encoding="utf-8")
    full_handoff = " ".join([
        "Task ID: AUTOMATION-LEDGER-ACTIVATION",
        "Title: Activate and validate persistent autonomous task tracking",
        "Target branch: main",
        "Question: " + task["question_excerpt"],
        "Acceptance criteria (5; first 5):",
        *["- " + item for item in task["acceptance_criteria_excerpt"]],
        "Next: " + task["next_action_excerpt"],
        "Read-only source paths (select at most one): " + ", ".join(task["read_paths"]),
        "If criteria exceed these excerpts, read only this task record in the canonical ledger before coding.",
        "PR #327 is integrated at main merge commit 69deb6778f9383887118803428e7014686865a83; PRs #317/#318/#319 are superseded. Do not reopen, replay or recreate that chain.",
    ])
    assert len(full_handoff) <= 1349
    full_handoff += "X" * (1349 - len(full_handoff))
    assert len(full_handoff) == 1349
    bounded = MODULE.build_context(
        root, "AUTOMATION-LEDGER-ACTIVATION",
        "Activate and validate persistent autonomous task tracking",
        "main", full_handoff, max_chars=1500, max_task_context=1400,
    )
    assert len(bounded) <= 1500
    assert task["question_excerpt"] in bounded
    assert task["next_action_excerpt"] in bounded
    assert all(item in bounded for item in task["acceptance_criteria_excerpt"])

    groq_bounded = MODULE.build_context(
        root, "AUTOMATION-LEDGER-ACTIVATION",
        "Activate and validate persistent autonomous task tracking",
        "main", full_handoff, max_chars=1500, max_task_context=1400,
        max_criteria=3, max_next_action=140,
    )
    assert len(groq_bounded) <= 1500
    assert "Read-only source paths (select at most one): tools/check_task_ledger.py, tools/test_check_task_ledger.py" in groq_bounded
    assert all(item in groq_bounded for item in task["acceptance_criteria_excerpt"][:3])
    assert task["acceptance_criteria_excerpt"][3] not in groq_bounded
    assert "Next: " + "N" * 139 + "…" in groq_bounded

    # Unsafe paths are rejected before any model receives the context.
    unsafe_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    for unsafe_path in ("../outside.py", "/absolute/file.py", "docs/automation/task-ledger.json", "assets/model.bin"):
        unsafe_summary["tasks"][0]["read_paths"] = [unsafe_path]
        summary_path.write_text(json.dumps(unsafe_summary), encoding="utf-8")
        try:
            MODULE.build_context(
                root, "AUTOMATION-LEDGER-ACTIVATION",
                "Activate and validate persistent autonomous task tracking",
                "main", context,
            )
        except MODULE.ContextBuildError as exc:
            assert "read allow-list" in str(exc)
        else:
            raise AssertionError(f"Expected unsafe read path to fail closed: {unsafe_path}")
    unsafe_summary["tasks"][0]["read_paths"] = ["tools/check_task_ledger.py", "tools/test_check_task_ledger.py"]
    summary_path.write_text(json.dumps(unsafe_summary), encoding="utf-8")

    # Restore the initial fixture before the independent truncation test below.
    task["question_excerpt"] = "Does the loop reconcile the task ledger?"
    task["next_action_excerpt"] = "Complete a verified provider cycle."
    task["acceptance_criteria_total"] = 2
    task["acceptance_criteria_excerpt"] = [
        "One active task maximum", "Exact PR state is recorded",
    ]
    summary_path.write_text(json.dumps(payload), encoding="utf-8")

    try:
        MODULE.build_context(
            root, "AUTOMATION-LEDGER-ACTIVATION",
            "Activate and validate persistent autonomous task tracking",
            "main", context, max_task_context=250,
        )
    except MODULE.ContextBuildError as exc:
        assert "budget" in str(exc) or "exceed" in str(exc)
    else:
        raise AssertionError("Expected a tight context budget to reject truncated required task excerpts")

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

print("PASS: schema-v2 identity, target branch, required excerpts and truncation fail-closed cases")
