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
        "One model provider invocation at most; €0; 1,550 context tokens", encoding="utf-8"
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
            "depends_on": [],
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
    (root / "tools").mkdir(parents=True)
    (root / "tools/test_check_task_ledger.py").write_text("class FixtureTests: pass\\n", encoding="utf-8")
    (root / "docs/automation/patch-path-allowlist.json").write_text(json.dumps({
        "schema_version": 1,
        "policy": {"owner_review_required": True, "path_mode": "exact", "max_paths_per_task": 20},
        "tasks": [{
            "task_id": "AUTOMATION-LEDGER-ACTIVATION",
            "purpose": "Synthetic owner-reviewed fixture scope",
            "approval_ref": "https://github.com/Master-Chiken/boonta-reborn-88/pull/999",
            "allowed_paths": ["tools/test_check_task_ledger.py"],
        }],
    }), encoding="utf-8")
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
    assert "Exact owner-reviewed write paths (no others): tools/test_check_task_ledger.py" in rendered

    # The blocked bootstrap is executable only when an exact owner-reviewed
    # write-path entry exists; otherwise the context builder fails before inference.
    path_policy = root / "docs/automation/patch-path-allowlist.json"
    original_policy = json.loads(path_policy.read_text(encoding="utf-8"))
    path_policy.write_text(json.dumps({**original_policy, "tasks": []}), encoding="utf-8")
    try:
        MODULE.build_context(
            root, "AUTOMATION-LEDGER-ACTIVATION",
            "Activate and validate persistent autonomous task tracking",
            "main", context,
        )
    except MODULE.ContextBuildError as exc:
        assert "no unique owner-reviewed exact-path entry" in str(exc)
    else:
        raise AssertionError("Blocked activation must not reach inference without owner-reviewed write paths")
    path_policy.write_text(json.dumps(original_policy), encoding="utf-8")

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
    # required excerpt when the preflight context is about 1.5k characters.
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
    assert len(full_handoff) <= 1500
    full_handoff += "X" * (1500 - len(full_handoff))
    assert len(full_handoff) == 1500
    bounded = MODULE.build_context(
        root, "AUTOMATION-LEDGER-ACTIVATION",
        "Activate and validate persistent autonomous task tracking",
        "main", full_handoff, max_chars=1500, max_task_context=1400,
    )
    assert len(bounded) <= 1500
    assert task["question_excerpt"] in bounded
    assert task["next_action_excerpt"] in bounded
    assert all(MODULE._short(item, 140) in bounded for item in task["acceptance_criteria_excerpt"])

    groq_bounded = MODULE.build_context(
        root, "AUTOMATION-LEDGER-ACTIVATION",
        "Activate and validate persistent autonomous task tracking",
        "main", full_handoff, max_chars=1500, max_task_context=1400,
        max_criteria=3, max_next_action=140,
    )
    assert len(groq_bounded) <= 1500
    assert "Read-only source excerpts: disabled for this context build" in groq_bounded
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


# Queue promotion must carry completed dependency evidence and a reviewed exact write scope.
with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    fixture(root)
    summary_path = root / "docs/automation/task-ledger-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    task_id = "GC-RIVAL-ROUTE-PROGRESSION"
    title = "Make rival racers progress through the native route and complete the race"
    queued = {
        "task_id": task_id,
        "title": title,
        "status": "queued",
        "owner_approved": True,
        "depends_on": ["GC-RACE-PROGRESSION"],
        "target_branch": "dev",
        "platform_scope": ["GameCube", "Wii"],
        "read_paths": ["gamecube-demo/source/rival_ai.h"],
        "read_ranges": [{"path": "gamecube-demo/source/rival_ai.h", "start_line": 1, "end_line": 20}],
        "question_excerpt": "Can rivals progress on the native route model?",
        "acceptance_criteria_total": 1,
        "acceptance_criteria_excerpt": ["Rivals share deterministic route and lap progress"],
        "pr_url": None,
        "head_sha": None,
        "next_action_excerpt": "Trace the existing route cursor and rival update before changing code.",
    }
    summary["completed_task_ids"] = ["GC-RACE-PROGRESSION"]
    summary["tasks"] = [queued]
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    policy = {
        "schema_version": 1,
        "policy": {
            "owner_review_required": True,
            "path_mode": "exact",
            "max_paths_per_task": 20,
        },
        "tasks": [{
            "task_id": task_id,
            "purpose": "Offline exact write-path fixture",
            "approval_ref": "https://github.com/Master-Chiken/boonta-reborn-88/pull/400",
            "allowed_paths": ["gamecube-demo/source/rival_ai.h", "gamecube-demo/tests/test_rival_ai.c"],
        }],
    }
    (root / "docs/automation/patch-path-allowlist.json").write_text(json.dumps(policy), encoding="utf-8")
    for allowed_path in policy["tasks"][0]["allowed_paths"]:
        target = root / allowed_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("/* reviewed fixture path */\\n", encoding="utf-8")
    handoff = "\n".join([
        "Task ID: " + task_id,
        "Title: " + title,
        "Target branch: dev",
        "Platform scope: GameCube, Wii",
        "Question: " + queued["question_excerpt"],
        "Acceptance criteria (1 total; first 1):",
        "- " + queued["acceptance_criteria_excerpt"][0],
        "Next: " + queued["next_action_excerpt"],
        "Read-only source paths (select at most one): " + ", ".join(queued["read_paths"]),
    ])
    queued_context = MODULE.build_context(root, task_id, title, "dev", handoff)
    assert "Exact owner-reviewed write paths (no others): gamecube-demo/source/rival_ai.h, gamecube-demo/tests/test_rival_ai.c" in queued_context

    (root / "gamecube-demo/tests/test_rival_ai.c").unlink()
    try:
        MODULE.build_context(root, task_id, title, "dev", handoff)
    except MODULE.ContextBuildError as exc:
        assert "existing regular file" in str(exc)
    else:
        raise AssertionError("Queued context must reject a missing approved write path")
    (root / "gamecube-demo/tests/test_rival_ai.c").write_text("/* restored fixture */\\n", encoding="utf-8")

    summary["completed_task_ids"] = []
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    try:
        MODULE.build_context(root, task_id, title, "dev", handoff)
    except MODULE.ContextBuildError as exc:
        assert "dependency-complete" in str(exc)
    else:
        raise AssertionError("Queued context must fail closed while any dependency is incomplete")

    summary["completed_task_ids"] = ["GC-RACE-PROGRESSION"]
    summary["tasks"][0]["owner_approved"] = False
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    try:
        MODULE.build_context(root, task_id, title, "dev", handoff)
    except MODULE.ContextBuildError as exc:
        assert "owner-approved" in str(exc)
    else:
        raise AssertionError("Queued context must fail closed without explicit owner approval")


# Exact multi-file source excerpts are loaded from the selected target checkout,
# never by asking the model to browse the repository.
with tempfile.TemporaryDirectory() as temp:
    source_root = Path(temp)
    paths = [
        "source/main.c",
        "source/gameplay_state.h",
        "source/pause_state.h",
        "tests/test_gameplay_state.c",
    ]
    for index, path in enumerate(paths):
        target = source_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(
            f"/* {path} line {line} */" for line in range(1, 31)
        ), encoding="utf-8")
    ranges = [
        {"path": paths[0], "start_line": 4, "end_line": 8},
        {"path": paths[1], "start_line": 10, "end_line": 14},
        {"path": paths[2], "start_line": 16, "end_line": 20},
        {"path": paths[3], "start_line": 22, "end_line": 26},
    ]
    excerpt = MODULE._build_source_excerpt(source_root, paths, ranges, 1800)
    assert all(path in excerpt for path in paths)
    assert "line 4" in excerpt and "line 26" in excerpt
    assert len(excerpt) <= 1800

    try:
        MODULE._build_source_excerpt(source_root, paths, [], 1800)
    except MODULE.ContextBuildError as exc:
        assert "non-empty exact source-range allow-list" in str(exc)
    else:
        raise AssertionError("Empty source ranges must fail closed instead of producing an empty excerpt")

    try:
        MODULE._build_source_excerpt(
            source_root, paths, [dict(ranges[0], path="../outside.c"), *ranges[1:]], 1800
        )
    except MODULE.ContextBuildError:
        pass
    else:
        raise AssertionError("Expected source ranges outside the exact allow-list to fail")

    try:
        MODULE._build_source_excerpt(
            source_root, paths, [dict(ranges[0], end_line=31), *ranges[1:]], 1800
        )
    except MODULE.ContextBuildError as exc:
        assert "exceeds the 30-line file" in str(exc)
    else:
        raise AssertionError("Expected source ranges beyond EOF to fail")

    try:
        MODULE._build_source_excerpt(
            source_root, paths, [dict(ranges[0], end_line=1000), *ranges[1:]], 1800
        )
    except MODULE.ContextBuildError:
        pass
    else:
        raise AssertionError("Expected oversized source ranges to fail closed")


# End-to-end context assembly reads the selected target checkout, not the
# policy/ledger checkout, and carries all approved path excerpts into the prompt.
with tempfile.TemporaryDirectory() as temp:
    root = Path(temp) / "policy"
    source_root = Path(temp) / "target"
    root.mkdir()
    task_context = fixture(root)
    summary_path = root / "docs/automation/task-ledger-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    task = summary["tasks"][0]
    paths = task["read_paths"]
    task["read_ranges"] = [
        {"path": paths[0], "start_line": 3, "end_line": 6},
        {"path": paths[1], "start_line": 8, "end_line": 11},
    ]
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    for index, path in enumerate(paths):
        target = source_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(
            f"# {path} line {line}" for line in range(1, 20)
        ), encoding="utf-8")
    context = MODULE.build_context(
        root,
        "AUTOMATION-LEDGER-ACTIVATION",
        "Activate and validate persistent autonomous task tracking",
        "main",
        task_context,
        max_chars=2800,
        max_task_context=1100,
        max_criteria=2,
        max_next_action=100,
        source_root=source_root,
        max_source_chars=1400,
    )
    assert "SOURCE EXCERPTS" in context
    assert "[tools/check_task_ledger.py:" in context
    assert "[tools/test_check_task_ledger.py:" in context
    assert all(path in context for path in paths)
    assert "line 3" in context and "line 11" in context


# Production smoke test: build the actual activation-task context from the
# canonical compact summary and the exact current repository source files.
with (ROOT / "docs/automation/task-ledger-summary.json").open(encoding="utf-8") as handle:
    production_summary = json.load(handle)
activation = next(
    task for task in production_summary["tasks"]
    if task["task_id"] == "AUTOMATION-LEDGER-ACTIVATION"
)
production_handoff = "\n".join([
    "Task ID: " + activation["task_id"],
    "Title: " + activation["title"],
    "Target branch: " + activation["target_branch"],
    "Question: " + activation["question_excerpt"],
    f"Acceptance criteria ({activation['acceptance_criteria_total']}; first 5):",
    *("- " + item for item in activation["acceptance_criteria_excerpt"]),
    "Next: " + activation["next_action_excerpt"],
    "Read-only source paths (select at most one): " + ", ".join(activation["read_paths"]),
])
production_context = MODULE.build_context(
    ROOT,
    activation["task_id"],
    activation["title"],
    activation["target_branch"],
    production_handoff,
    max_chars=3000,
    max_task_context=1100,
    max_criteria=4,
    max_next_action=100,
    source_root=ROOT,
    max_source_chars=1800,
)
assert len(production_context) <= 3000
assert "Read-only source excerpts: exact task path/range excerpts are included below" in production_context
assert all(f"[{path}:" in production_context for path in activation["read_paths"])
assert "BOONTA_TASK_ID" in production_context or "One active task maximum" in production_context

print("PASS: schema-v2 identity, bounded multi-file excerpts and fail-closed cases")
