#!/usr/bin/env python3
"""Execute the production GitHub-script task preflight against offline fixtures."""

from pathlib import Path
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/boonta-autonomous-loop.yml"


def fail(message: str) -> None:
    raise SystemExit(f"Autonomous task preflight test failed: {message}")


if not WORKFLOW.is_file():
    fail("autonomous loop workflow is missing")
node = shutil.which("node")
if not node:
    fail("Node.js is required to execute the production GitHub-script preflight")

lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
try:
    step_index = next(
        index for index, line in enumerate(lines)
        if line.strip() == "- name: Read the three persistent UTC cooldown markers"
    )
    script_index = next(
        index for index in range(step_index, len(lines))
        if lines[index].strip() == "script: |"
    )
except StopIteration:
    fail("could not locate the global provider-cooldown GitHub script")

script_lines = []
for line in lines[script_index + 1:]:
    if line.strip() and len(line) - len(line.lstrip()) < 12:
        break
    script_lines.append(line[12:] if line.startswith("            ") else "")
script = "\n".join(script_lines).rstrip()
if not script or "const taskBlockedActive =" not in script:
    fail("extracted task preflight script is empty or incomplete")


def task(
    task_id: str,
    status: str,
    *,
    complete: bool = True,
    target_branch: str = "main",
) -> dict:
    value = {
        "task_id": task_id,
        "title": "Offline fixture task",
        "status": status,
        "target_branch": target_branch,
        "question_excerpt": "Can the selected task be executed safely?",
        "acceptance_criteria_total": 2,
        "acceptance_criteria_excerpt": [
            "Use the canonical source of truth",
            "Verify the exact target branch",
        ],
        "next_action_excerpt": "Complete one small, source-verified automation task.",
        "platform_scope": ["automation"],
        "owner_approved": status == "queued",
        "depends_on": [],
        "read_paths": ["tools/check_task_ledger.py", "tools/test_check_task_ledger.py"],
        "pr_url": "",
        "head_sha": "",
    }
    if not complete:
        value["next_action_excerpt"] = ""
    return value


activation = task("AUTOMATION-LEDGER-ACTIVATION", "blocked")
valid_queued = task("AUTOMATION-TEST-QUEUED", "queued")
queued_ready_pr = {
    "number": 457,
    "state": "open",
    "draft": False,
    "user": {"login": "Master-Chiken"},
    "head": {
        "repo": {"full_name": "Master-Chiken/boonta-reborn-88"},
        "ref": "automation-test-queued",
        "sha": "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2",
    },
    "base": {
        "repo": {"full_name": "Master-Chiken/boonta-reborn-88"},
        "ref": "main",
    },
    "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/457",
    "body": (
        "BOONTA_TASK_ID: AUTOMATION-TEST-QUEUED\n"
        "BOONTA_TASK_TARGET_BRANCH: main"
    ),
}
queued_draft_pr = {
    **queued_ready_pr,
    "number": 458,
    "draft": True,
    "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/458",
}
rival_queued_task = task("GC-RIVAL-ROUTE-PROGRESSION", "queued", target_branch="dev")
rival_queued_task.update({
    "title": "Make rival racers progress through the native route and complete the race",
    "depends_on": ["GC-RACE-PROGRESSION"],
    "read_paths": [
        "gamecube-demo/source/rival_ai.h",
        "gamecube-demo/source/route_cursor.h",
        "gamecube-demo/source/gameplay_state.h",
    ],
})
rival_draft_pr = {
    **queued_draft_pr,
    "number": 439,
    "head": {
        "repo": {"full_name": "Master-Chiken/boonta-reborn-88"},
        "ref": "gameplay/rival-route-cursors-20261117",
        "sha": "194a323a8a822143c5c83737b8c966c2ee8db5ff",
    },
    "base": {
        "repo": {"full_name": "Master-Chiken/boonta-reborn-88"},
        "ref": "dev",
    },
    "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/439",
    "body": (
        "BOONTA_TASK_ID: GC-RIVAL-ROUTE-PROGRESSION\\n"
        "BOONTA_TASK_TARGET_BRANCH: dev"
    ),
}
activation_ready_pr = {
    **queued_ready_pr,
    "number": 456,
    "head": {
        "repo": {"full_name": "Master-Chiken/boonta-reborn-88"},
        "ref": "automation-ledger-activation",
        "sha": "0123456789abcdef0123456789abcdef01234567",
    },
    "base": {
        "repo": {"full_name": "Master-Chiken/boonta-reborn-88"},
        "ref": "main",
    },
    "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/456",
    "body": (
        "BOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION\n"
        "BOONTA_TASK_TARGET_BRANCH: main"
    ),
}
valid_blocked = task("N64-COMPWOLF-PUPP-T2-PARSE-PROBE", "blocked")
valid_active = task("AUTOMATION-TEST-ACTIVE", "active")
incomplete_active = task("AUTOMATION-TEST-INCOMPLETE", "active", complete=False)
invalid_target = task("AUTOMATION-TEST-INVALID-TARGET", "active", target_branch="feature")
represented_active = task("AUTOMATION-TEST-REPRESENTED", "active")
represented_active["pr_url"] = "https://github.com/Master-Chiken/boonta-reborn-88/pull/999"
represented_active["head_sha"] = "0123456789abcdef0123456789abcdef01234567"
cases = [
    {
        "name": "empty canonical ledger reports EMPTY_QUEUE",
        "tasks": [],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "EMPTY_QUEUE",
    },
    {
        "name": "queued task is visible but not silently promoted until its dependency is completed",
        "tasks": [{**valid_queued, "depends_on": ["TASK-PREREQUISITE"]}],
        "completed_task_ids": [],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "QUEUED_TASKS_WAITING_FOR_PROMOTION",
        "expected_queued_count": 1,
    },
    {
        "name": "first owner-approved queued task is promoted only after every dependency is completed",
        "tasks": [{**valid_queued, "depends_on": ["TASK-PREREQUISITE"]}],
        "completed_task_ids": ["TASK-PREREQUISITE"],
        "marker_day_offset": None,
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-TEST-QUEUED",
        "expected_blocked": False,
        "expected_queue_state": "READY",
    },
    {
        "name": "queued task without explicit owner approval is not promoted",
        "tasks": [{**valid_queued, "owner_approved": False}],
        "completed_task_ids": [],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "QUEUED_TASKS_WAITING_FOR_PROMOTION",
    },
    {
        "name": "queued task with an open matching PR blocks duplicate promotion",
        "tasks": [valid_queued],
        "completed_task_ids": [],
        "open_task_prs": [{
            "number": 457,
            "body": "BOONTA_TASK_ID: AUTOMATION-TEST-QUEUED"
        }],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": False,
        "reason_contains": "queued task AUTOMATION-TEST-QUEUED already has open PR #457",
    },
    {
        "name": "owner-approved queued task resumes only its trusted ready PR after dependencies complete",
        "tasks": [{**valid_queued, "depends_on": ["TASK-PREREQUISITE"]}],
        "completed_task_ids": ["TASK-PREREQUISITE"],
        "open_task_prs": [queued_ready_pr],
        "pr_files": [
            {"filename": "tools/check_task_ledger.py", "status": "modified"},
            {"filename": "tools/test_check_task_ledger.py", "status": "modified"}
        ],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": True,
        "expected_resume_ready": True,
        "expected_resume_pr_number": "457",
        "expected_resume_task_id": "AUTOMATION-TEST-QUEUED",
        "expected_resume_file_paths": [
            "tools/check_task_ledger.py",
            "tools/test_check_task_ledger.py"
        ],
        "expected_resume_target_branch": "main",
        "expected_resume_pr_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/457",
        "expected_resume_branch": "automation-test-queued",
        "expected_resume_head_sha": "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2",
    },
    {
        "name": "queued task PR cannot resume until every dependency is completed",
        "tasks": [{**valid_queued, "depends_on": ["TASK-PREREQUISITE"]}],
        "completed_task_ids": [],
        "open_task_prs": [queued_ready_pr],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": True,
        "expected_resume_ready": False,
        "reason_contains": "not eligible for unattended resume",
    },
    {
        "name": "unapproved queued task PR cannot resume",
        "tasks": [{**valid_queued, "owner_approved": False}],
        "open_task_prs": [queued_ready_pr],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": True,
        "expected_resume_ready": False,
        "reason_contains": "not eligible for unattended resume",
    },
    {
        "name": "activation PR cannot resume while a separate queued task PR exists",
        "tasks": [activation, valid_queued],
        "open_task_prs": [activation_ready_pr, queued_ready_pr],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": True,
        "expected_resume_ready": False,
    },
    {
        "name": "active task PR cannot resume while a separate queued task PR exists",
        "tasks": [valid_active, valid_queued],
        "open_task_prs": [{
            **activation_ready_pr,
            "number": 455,
            "head": {
                "repo": {"full_name": "Master-Chiken/boonta-reborn-88"},
                "ref": "automation-test-active",
                "sha": "fedcba9876543210fedcba9876543210fedcba98",
            },
            "base": {
                "repo": {"full_name": "Master-Chiken/boonta-reborn-88"},
                "ref": "main",
            },
            "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/455",
            "body": (
                "BOONTA_TASK_ID: AUTOMATION-TEST-ACTIVE\n"
                "BOONTA_TASK_TARGET_BRANCH: main"
            ),
        }, queued_ready_pr],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "ACTIVE_TASK_REQUIRES_RECONCILIATION",
        "expected_resume_candidate": True,
        "expected_resume_ready": False,
    },
    {
        "name": "owner-approved queued draft PR resumes in place and remains a draft",
        "tasks": [activation, valid_queued],
        "open_task_prs": [queued_draft_pr],
        "pr_files": [{"filename": "tools/check_task_ledger.py", "status": "modified"}],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": True,
        "expected_resume_ready": True,
        "expected_resume_pr_number": "458",
        "expected_resume_task_id": "AUTOMATION-TEST-QUEUED",
        "expected_resume_file_paths": ["tools/check_task_ledger.py"],
        "expected_resume_target_branch": "main",
        "expected_resume_pr_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/458",
        "expected_resume_branch": "automation-test-queued",
        "expected_resume_head_sha": "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2",
    },
    {
        "name": "unapproved queued draft PR remains blocked",
        "tasks": [activation, {**valid_queued, "owner_approved": False}],
        "open_task_prs": [queued_draft_pr],
        "pr_files": [{"filename": "tools/check_task_ledger.py", "status": "modified"}],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": False,
        "expected_resume_ready": False,
    },
    {
        "name": "real owner-approved GC rival Draft PR resumes after its canonical dependency completes",
        "tasks": [rival_queued_task],
        "completed_task_ids": ["GC-RACE-PROGRESSION"],
        "open_task_prs": [rival_draft_pr],
        "pr_files": [
            {"filename": "gamecube-demo/source/gameplay_state.h", "status": "modified"},
            {"filename": "gamecube-demo/source/main.c", "status": "modified"},
            {"filename": "gamecube-demo/source/rival_ai.h", "status": "modified"},
            {"filename": "gamecube-demo/tests/test_rival_ai.c", "status": "modified"}
        ],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": True,
        "expected_resume_ready": True,
        "expected_resume_pr_number": "439",
        "expected_resume_task_id": "GC-RIVAL-ROUTE-PROGRESSION",
        "expected_resume_file_paths": [
            "gamecube-demo/source/gameplay_state.h",
            "gamecube-demo/source/main.c",
            "gamecube-demo/source/rival_ai.h",
            "gamecube-demo/tests/test_rival_ai.c"
        ],
        "expected_resume_target_branch": "dev",
        "expected_resume_pr_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/439",
        "expected_resume_branch": "gameplay/rival-route-cursors-20261117",
        "expected_resume_head_sha": "194a323a8a822143c5c83737b8c966c2ee8db5ff",
    },
    {
        "name": "multiple queued task PRs fail closed instead of selecting one writer",
        "tasks": [valid_queued, task("AUTOMATION-TEST-SECOND-QUEUED", "queued")],
        "open_task_prs": [queued_ready_pr, {
            **queued_ready_pr,
            "number": 459,
            "body": (
                "BOONTA_TASK_ID: AUTOMATION-TEST-SECOND-QUEUED\n"
                "BOONTA_TASK_TARGET_BRANCH: main"
            ),
            "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/459",
        }],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": False,
        "expected_resume_ready": False,
        "reason_contains": "multiple queued tasks already carry PR or head metadata",
    },
    {
        "name": "recorded queued PR URL without a matching open marker blocks all writers",
        "tasks": [{**valid_queued, "pr_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/499"}],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": False,
        "expected_resume_ready": False,
        "reason_contains": "recorded PR/head metadata without one exact matching open PR marker",
    },
    {
        "name": "blocked non-activation tasks are not auto-unblocked",
        "tasks": [valid_blocked],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "BLOCKED_TASKS_ONLY",
        "expected_blocked_count": 1,
    },
    {
        "name": "blocked activation without an owner-reviewed write scope is not sent to a provider",
        "tasks": [activation],
        "marker_day_offset": None,
        "owner_paths": False,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OWNER_APPROVED_PATHS",
        "reason_contains": "no unique owner-reviewed exact write-path entry",
    },
    {
        "name": "activation same-day backoff is reported separately from empty queue",
        "tasks": [activation],
        "marker_day_offset": 0,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": True,
        "expected_queue_state": "TASK_BACKOFF",
    },
    {
        "name": "open task PR is reported as waiting for reconciliation",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 356,
            "body": "BOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION"
        }],
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": False,
    },
    {
        "name": "trusted owner-authored same-repository task PR is identified as a resume candidate without launching a provider",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 388,
            "state": "open",
            "draft": False,
            "user": {"login": "Master-Chiken"},
            "head": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "AUTOMATION-LEDGER-ACTIVATION", "sha": "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2"},
            "base": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "main"},
            "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/388",
            "body": "BOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION\nBOONTA_TASK_TARGET_BRANCH: main"
        }],
        "pr_files": [
            {"filename": "tools/check_task_ledger.py", "status": "modified"},
            {"filename": "tools/test_check_task_ledger.py", "status": "modified"},
            {"filename": "docs/automation/task-ledger.json", "status": "modified"},
            {"filename": "assets/reference.bin", "status": "modified"},
            {"filename": "../unsafe.py", "status": "modified"},
            {"filename": "roms/synthetic_probe.c", "status": "modified"},
            {"filename": "private/owner-notes.md", "status": "modified"},
        ],
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": True,
        "expected_resume_ready": True,
        "expected_resume_pr_number": "388",
        "expected_resume_task_id": "AUTOMATION-LEDGER-ACTIVATION",
        "expected_resume_file_paths": ["tools/check_task_ledger.py", "tools/test_check_task_ledger.py"],
    },
    {
        "name": "trusted PR without an eligible text file is not resumable",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 388,
            "state": "open",
            "draft": False,
            "user": {"login": "Master-Chiken"},
            "head": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "AUTOMATION-LEDGER-ACTIVATION", "sha": "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2"},
            "base": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "main"},
            "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/388",
            "body": "BOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION\nBOONTA_TASK_TARGET_BRANCH: main"
        }],
        "pr_files": [{"filename": "assets/reference.bin", "status": "modified"}],
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": True,
        "expected_resume_ready": False,
        "expected_resume_file_paths": [],
        "reason_contains": "no eligible safe text file",
    },
    {
        "name": "duplicate exact task markers fail closed for resume discovery",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [
            {
                "number": 388,
                "state": "open",
                "draft": False,
                "user": {"login": "Master-Chiken"},
                "head": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "task-one", "sha": "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2"},
                "base": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "main"},
                "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/388",
                "body": "BOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION"
            },
            {
                "number": 391,
                "state": "open",
                "draft": False,
                "user": {"login": "Master-Chiken"},
                "head": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "task-two", "sha": "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2"},
                "base": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "main"},
                "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/391",
                "body": "BOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION"
            }
        ],
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": False,
    },
    {
        "name": "fork-authored task PR is never marked resumable",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 392,
            "state": "open",
            "draft": False,
            "user": {"login": "Master-Chiken"},
            "head": {"repo": {"full_name": "external-contributor/boonta-reborn-88"}, "ref": "task-branch", "sha": "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2"},
            "base": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "main"},
            "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/392",
            "body": "BOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION"
        }],
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": False,
    },
    {
        "name": "wrong canonical base branch is never marked resumable",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 393,
            "state": "open",
            "draft": False,
            "user": {"login": "Master-Chiken"},
            "head": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "task-branch", "sha": "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2"},
            "base": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "dev"},
            "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/393",
            "body": "BOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION"
        }],
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": False,
    },
    {
        "name": "invalid head SHA is never marked resumable",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 394,
            "state": "open",
            "draft": False,
            "user": {"login": "Master-Chiken"},
            "head": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "task-branch", "sha": "not-a-full-git-sha"},
            "base": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "main"},
            "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/394",
            "body": "BOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION"
        }],
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": False,
    },
    {
        "name": "mismatched canonical PR URL is never marked resumable",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 395,
            "state": "open",
            "draft": False,
            "user": {"login": "Master-Chiken"},
            "head": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "task-branch", "sha": "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2"},
            "base": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "main"},
            "html_url": "https://example.invalid/pull/395",
            "body": "BOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION"
        }],
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": False,
    },
    {
        "name": "draft task PR is never marked resumable",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 396,
            "state": "open",
            "draft": True,
            "user": {"login": "Master-Chiken"},
            "head": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "task-branch", "sha": "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2"},
            "base": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "main"},
            "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/396",
            "body": "BOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION"
        }],
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": False,
    },
    {
        "name": "task PR using the canonical base branch as its head is never marked resumable",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 397,
            "state": "open",
            "draft": False,
            "user": {"login": "Master-Chiken"},
            "head": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "main", "sha": "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2"},
            "base": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "main"},
            "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/397",
            "body": "BOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION"
        }],
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": False,
    },
    {
        "name": "task with an already recorded PR or head SHA is not treated as an unrecorded resume candidate",
        "tasks": [{**activation, "pr_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/999", "head_sha": "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2"}],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 398,
            "state": "open",
            "draft": False,
            "user": {"login": "Master-Chiken"},
            "head": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "task-branch", "sha": "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2"},
            "base": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "main"},
            "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/398",
            "body": "BOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION"
        }],
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": False,
    },
    {
        "name": "non-owner task PR is never marked resumable",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 389,
            "state": "open",
            "draft": False,
            "user": {"login": "external-contributor"},
            "head": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "task-branch", "sha": "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2"},
            "base": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "main"},
            "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/389",
            "body": "BOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION"
        }],
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": False,
    },
    {
        "name": "task PR missing exact target-branch marker is not resumable",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 399,
            "state": "open",
            "draft": False,
            "user": {"login": "Master-Chiken"},
            "head": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "AUTOMATION-LEDGER-ACTIVATION", "sha": "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2"},
            "base": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "main"},
            "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/399",
            "body": "BOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION"
        }],
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": False,
        "expected_resume_ready": False,
    },
    {
        "name": "activation opens after UTC reset with fresh branch guidance",
        "tasks": [activation],
        "marker_day_offset": None,
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-LEDGER-ACTIVATION",
        "expected_blocked": False,
        "expected_queue_state": "READY",
        "expected_context_contains": [
            "UTC branch: create a fresh automation-ledger-activation-",
            "branch from current main; never reuse any earlier attempt branch.",
        ],
        "expected_date_branch": True,
    },
    {
        "name": "open PR with exact task marker blocks duplicate activation",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 356,
            "body": "Existing automation PR\nBOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION\nBOONTA_TASK_TARGET_BRANCH: main"
        }],
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "reason_contains": "open PR #356",
    },
    {
        "name": "open PR for a different task does not block activation",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 123,
            "body": "BOONTA_TASK_ID: AUTOMATION-OTHER-TASK\nBOONTA_TASK_TARGET_BRANCH: main"
        }],
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-LEDGER-ACTIVATION",
        "expected_blocked": False,
    },
    {
        "name": "100 open PRs fail closed at the bounded inventory ceiling",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{"number": number, "body": "Unrelated PR"} for number in range(100)],
        "expected_error": "100-item safety ceiling",
    },
    {
        "name": "same-day blocked marker suppresses activation",
        "tasks": [activation],
        "marker_day_offset": 0,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": True,
    },
    {
        "name": "same-day blocked marker allows owner manual re-evaluation",
        "tasks": [activation],
        "marker_day_offset": 0,
        "event_name": "workflow_dispatch",
        "actor": "Master-Chiken",
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-LEDGER-ACTIVATION",
        "expected_blocked": True,
    },
    {
        "name": "same-day blocked marker allows qualifying owner main push",
        "tasks": [activation],
        "marker_day_offset": 0,
        "event_name": "push",
        "actor": "Master-Chiken",
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-LEDGER-ACTIVATION",
        "expected_blocked": True,
    },
    {
        "name": "same-day blocked marker rejects non-owner manual re-evaluation",
        "tasks": [activation],
        "marker_day_offset": 0,
        "event_name": "workflow_dispatch",
        "actor": "untrusted-contributor",
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": True,
        "reason_contains": "same-day UTC backoff",
    },
    {
        "name": "same-day blocked marker rejects non-owner main push",
        "tasks": [activation],
        "marker_day_offset": 0,
        "event_name": "push",
        "actor": "untrusted-contributor",
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": True,
        "reason_contains": "same-day UTC backoff",
    },
    {
        "name": "same-day blocked marker rejects unrelated pull request event",
        "tasks": [activation],
        "marker_day_offset": 0,
        "event_name": "pull_request",
        "actor": "Master-Chiken",
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": True,
        "reason_contains": "same-day UTC backoff",
    },
    {
        "name": "yesterday marker expires at UTC reset",
        "tasks": [activation],
        "marker_day_offset": -1,
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-LEDGER-ACTIVATION",
        "expected_blocked": False,
    },
    {
        "name": "one complete active task is selected",
        "tasks": [valid_active],
        "marker_day_offset": None,
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-TEST-ACTIVE",
        "expected_blocked": False,
        "expected_queue_state": "READY",
    },
    {
        "name": "activation PR blocks an unrelated active task from becoming a second writer",
        "tasks": [valid_active, activation],
        "open_task_prs": [activation_ready_pr],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "ACTIVE_TASK_REQUIRES_RECONCILIATION",
        "expected_resume_candidate": False,
        "expected_resume_ready": False,
        "reason_contains": "an active ledger task and a separate activation/queued task PR both reserve the single writer slot",
    },
    {
        "name": "queued task PR blocks a separate active task from becoming a second writer",
        "tasks": [valid_active, {
            **valid_queued,
            "owner_approved": True
        }],
        "open_task_prs": [queued_ready_pr],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "ACTIVE_TASK_REQUIRES_RECONCILIATION",
        "expected_resume_candidate": False,
        "expected_resume_ready": False,
        "reason_contains": "an active ledger task and a separate activation/queued task PR both reserve the single writer slot",
    },
    {
        "name": "multiple active tasks fail closed",
        "tasks": [valid_active, task("AUTOMATION-TEST-SECOND", "active")],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "ACTIVE_TASK_REQUIRES_RECONCILIATION",
    },
    {
        "name": "incomplete active task fails closed with precise reason",
        "tasks": [incomplete_active],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "reason_contains": "incomplete",
    },
    {
        "name": "unsupported task target branch fails closed",
        "tasks": [invalid_target],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "reason_contains": "incomplete",
    },
    {
        "name": "three same-day provider cooldowns are detected",
        "tasks": [valid_active],
        "marker_day_offset": None,
        "provider_marker_offsets": {"gemini": 0, "openrouter": 0, "groq": 0},
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-TEST-ACTIVE",
        "expected_blocked": False,
        "expected_provider_cooldowns": {"gemini": True, "openrouter": True, "groq": True},
    },
    {
        "name": "previous-day provider cooldowns expire after UTC reset",
        "tasks": [valid_active],
        "marker_day_offset": None,
        "provider_marker_offsets": {"gemini": -1, "openrouter": -1, "groq": -1},
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-TEST-ACTIVE",
        "expected_blocked": False,
        "expected_provider_cooldowns": {"gemini": False, "openrouter": False, "groq": False},
    },
    {
        "name": "task with an existing PR or head is not re-selected",
        "tasks": [represented_active],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "ACTIVE_TASK_REQUIRES_RECONCILIATION",
        "reason_contains": "PR/head",
    },
    {
        "name": "duplicate task IDs fail closed",
        "tasks": [activation, activation],
        "marker_day_offset": None,
        "expected_error": "duplicate task IDs",
    },
    {
        "name": "legacy summary schema fails closed",
        "tasks": [valid_active],
        "marker_day_offset": None,
        "schema_version": 1,
        "expected_error": "schema or one-active-task policy",
    },
]

node_program = f"""
const fs = require("node:fs");
const script = {json.dumps(script)};
const cases = JSON.parse(fs.readFileSync(0, "utf8"));
const AsyncFunction = Object.getPrototypeOf(async function() {{}}).constructor;

async function runCase(testCase) {{
  const outputs = {{}};
  const todayUtc = new Date().toISOString().slice(0, 10);
  const comments = [];
  if (testCase.marker_day_offset !== null) {{
    const markerDate = new Date(Date.now() + testCase.marker_day_offset * 86400000)
      .toISOString().slice(0, 10);
    comments.push({{
      user: {{ login: "github-actions[bot]" }},
      body: "<!-- BOONTA_TASK_BLOCKED_COOLDOWN: " + markerDate + " abcdef0123456789 -->"
    }});
  }}
  const providerPrefixes = {{
    gemini: "BOONTA_GEMINI_FAILURE_COOLDOWN: ",
    openrouter: "BOONTA_OPENROUTER_FAILURE_COOLDOWN: ",
    groq: "BOONTA_GROQ_FAILURE_COOLDOWN: "
  }};
  for (const [provider, dayOffset] of Object.entries(testCase.provider_marker_offsets || {{}})) {{
    const prefix = providerPrefixes[provider];
    if (!prefix) throw new Error("unknown provider fixture: " + provider);
    const markerDate = new Date(Date.now() + dayOffset * 86400000)
      .toISOString().slice(0, 10);
    comments.push({{
      user: {{ login: "github-actions[bot]" }},
      body: "<!-- " + prefix + markerDate + " -->"
    }});
  }}
  const ledger = {{
    schema_version: testCase.schema_version === undefined ? 2 : testCase.schema_version,
    source: "docs/automation/task-ledger.json",
    updated_at: todayUtc,
    policy: {{ max_active_tasks: 1 }},
    completed_task_ids: testCase.completed_task_ids || [],
    tasks: testCase.tasks
  }};
  const github = {{
    paginate: async (_endpoint, options) => {{
      if (options.issue_number !== 226 || options.since !== todayUtc + "T00:00:00Z") {{
        throw new Error("unexpected issue-comment query");
      }}
      return comments;
    }},
    rest: {{
      issues: {{ listComments: async () => ({{ data: comments }}) }},
      pulls: {{
        list: async (options) => {{
          if (options.state !== "open" || options.per_page !== 100 || options.page !== 1) {{
            throw new Error("unexpected open-PR query");
          }}
          return {{ data: testCase.open_task_prs || [] }};
        }},
        listFiles: async (options) => {{
          const expectedPullNumber = Number(testCase.expected_resume_pr_number || "388");
          if (options.pull_number !== expectedPullNumber || options.per_page !== 100 || options.page !== 1) {{
            throw new Error("unexpected resume changed-file query");
          }}
          return {{ data: testCase.pr_files || [] }};
        }}
      }},
      repos: {{
        getContent: async (options) => {{
          if (options.ref !== "main") throw new Error("unexpected canonical file ref");
          if (options.path === "docs/automation/task-ledger-summary.json") {{
            return {{
              data: {{
                encoding: "base64",
                content: Buffer.from(JSON.stringify(ledger), "utf8").toString("base64")
              }}
            }};
          }}
          if (options.path === "docs/automation/patch-path-allowlist.json") {{
            const entries = testCase.owner_paths === false ? [] :
              (testCase.owner_paths || (testCase.expected_ready ? testCase.tasks.filter((item) =>
                item.status === "active" || item.status === "queued" ||
                item.task_id === "AUTOMATION-LEDGER-ACTIVATION"
              ).map((item) => ({{
                task_id: item.task_id,
                purpose: "Synthetic owner-reviewed exact write scope",
                approval_ref: "https://github.com/Master-Chiken/boonta-reborn-88/pull/999",
                allowed_paths: [item.read_paths[1]]
              }})) : []));
            const policy = {{
              schema_version: 1,
              policy: {{ owner_review_required: true, path_mode: "exact", max_paths_per_task: 20 }},
              tasks: entries
            }};
            return {{
              data: {{
                encoding: "base64",
                content: Buffer.from(JSON.stringify(policy), "utf8").toString("base64")
              }}
            }};
          }}
          throw new Error("unexpected canonical file path: " + options.path);
        }}
      }}
    }}
  }};
  const core = {{
    setOutput: (key, value) => {{ outputs[key] = String(value); }},
    info: () => {{}},
    summary: {{
      addHeading() {{ return this; }},
      addTable() {{ return this; }},
      addRaw() {{ return this; }},
      async write() {{ return this; }}
    }}
  }};
  const context = {{
    repo: {{ owner: "Master-Chiken", repo: "boonta-reborn-88" }},
    eventName: testCase.event_name || "schedule",
    actor: testCase.actor || "github-actions[bot]"
  }};
  let error = "";
  try {{
    await new AsyncFunction("github", "context", "core", script)(github, context, core);
  }} catch (caught) {{
    error = String(caught.message || caught);
  }}
  return {{ outputs, error }};
}}

(async () => {{
  for (const testCase of cases) {{
    const result = await runCase(testCase);
    if (testCase.expected_error) {{
      if (!result.error.includes(testCase.expected_error)) {{
        throw new Error(testCase.name + ": expected error containing " + testCase.expected_error + ", got " + result.error);
      }}
      process.stdout.write("PASS: " + testCase.name + "\\n");
      continue;
    }}
    if (result.error) throw new Error(testCase.name + ": unexpected preflight error: " + result.error);
    const outputs = result.outputs;
    if (outputs.task_ready !== String(testCase.expected_ready)) {{
      throw new Error(testCase.name + ": expected task_ready=" + testCase.expected_ready + ", got " + outputs.task_ready);
    }}
    if (testCase.expected_queue_state !== undefined && outputs.queue_state !== testCase.expected_queue_state) {{
      throw new Error(testCase.name + ": expected queue_state=" + testCase.expected_queue_state + ", got " + outputs.queue_state);
    }}
    if (testCase.expected_queued_count !== undefined && outputs.queued_count !== String(testCase.expected_queued_count)) {{
      throw new Error(testCase.name + ": expected queued_count=" + testCase.expected_queued_count + ", got " + outputs.queued_count);
    }}
    if (testCase.expected_blocked_count !== undefined && outputs.blocked_count !== String(testCase.expected_blocked_count)) {{
      throw new Error(testCase.name + ": expected blocked_count=" + testCase.expected_blocked_count + ", got " + outputs.blocked_count);
    }}
    if (testCase.expected_queue_state === "EMPTY_QUEUE" && (
      outputs.task_ready !== "false" || outputs.task_id !== "" || outputs.task_context !== ""
    )) {{
      throw new Error(testCase.name + ": EMPTY_QUEUE must not expose a provider task handoff");
    }}
    if (outputs.task_id !== testCase.expected_task_id) {{
      throw new Error(testCase.name + ": expected task_id=" + testCase.expected_task_id + ", got " + outputs.task_id);
    }}
    if (testCase.expected_resume_candidate !== undefined &&
      outputs.resume_pr_candidate !== String(testCase.expected_resume_candidate)) {{
      throw new Error(testCase.name + ": expected resume_pr_candidate=" + testCase.expected_resume_candidate + ", got " + outputs.resume_pr_candidate);
    }}
    if (testCase.expected_resume_pr_number !== undefined &&
      outputs.resume_pr_number !== testCase.expected_resume_pr_number) {{
      throw new Error(testCase.name + ": expected resume_pr_number=" + testCase.expected_resume_pr_number + ", got " + outputs.resume_pr_number);
    }}
    if (testCase.expected_resume_ready !== undefined &&
      outputs.resume_ready !== String(testCase.expected_resume_ready)) {{
      throw new Error(testCase.name + ": expected resume_ready=" + testCase.expected_resume_ready + ", got " + outputs.resume_ready);
    }}
    if (testCase.expected_resume_ready === undefined && outputs.resume_ready !== "false") {{
      throw new Error(testCase.name + ": unexpected resume-ready task handoff");
    }}
    if (testCase.expected_resume_task_id !== undefined &&
      outputs.resume_task_id !== testCase.expected_resume_task_id) {{
      throw new Error(testCase.name + ": expected resume_task_id=" + testCase.expected_resume_task_id + ", got " + outputs.resume_task_id);
    }}
    if (testCase.expected_resume_file_paths !== undefined &&
      outputs.resume_file_paths !== JSON.stringify(testCase.expected_resume_file_paths)) {{
      throw new Error(testCase.name + ": expected resume file allow-list " + JSON.stringify(testCase.expected_resume_file_paths) + ", got " + outputs.resume_file_paths);
    }}
    if (outputs.resume_pr_candidate === "true" && outputs.task_ready !== "false") {{
      throw new Error(testCase.name + ": resume must remain separate from normal task readiness");
    }}
    if (outputs.resume_ready === "true" && (
      outputs.task_ready !== "false" ||
      outputs.resume_task_context.indexOf(testCase.expected_resume_task_id) < 0 ||
      outputs.resume_target_branch !== (testCase.expected_resume_target_branch || "main") ||
      outputs.resume_pr_url !== (testCase.expected_resume_pr_url || "https://github.com/Master-Chiken/boonta-reborn-88/pull/388") ||
      outputs.resume_branch !== (testCase.expected_resume_branch || "AUTOMATION-LEDGER-ACTIVATION") ||
      outputs.resume_head_sha !== (testCase.expected_resume_head_sha || "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2") ||
      outputs.resume_file_paths !== JSON.stringify(testCase.expected_resume_file_paths || [])
    )) {{
      throw new Error(testCase.name + ": exact safe-resume metadata/task context was not propagated");
    }}
    if (testCase.expected_ready) {{
      if (String(outputs.task_context).length > 2500) {{
        throw new Error(testCase.name + ": task context exceeds the 2,500-character provider handoff budget");
      }}
      const selected = testCase.tasks.find((item) => item.task_id === testCase.expected_task_id);
      if (outputs.task_title !== selected.title || outputs.task_target_branch !== selected.target_branch) {{
        throw new Error(testCase.name + ": selected task title/target branch were not propagated");
      }}
      for (const expectedText of [selected.task_id, selected.title, selected.question_excerpt,
        ...selected.acceptance_criteria_excerpt, selected.next_action_excerpt,
        "Read-only source paths (select at most one): " + selected.read_paths.join(", "),
        "Exact owner-reviewed write paths (no others): " + selected.read_paths[1]]) {{
        if (!String(outputs.task_context).includes(expectedText)) {{
          throw new Error(testCase.name + ": task context omitted " + expectedText);
        }}
      }}
      for (const expectedText of testCase.expected_context_contains || []) {{
        if (!String(outputs.task_context).includes(expectedText)) {{
          throw new Error(testCase.name + ": task context omitted activation guidance " + expectedText);
        }}
      }}
      if (testCase.expected_date_branch === true) {{
        const expectedBranch = "automation-ledger-activation-" + new Date().toISOString().slice(0, 10).replace(/-/g, "");
        if (!String(outputs.task_context).includes(expectedBranch)) {{
          throw new Error(testCase.name + ": task context omitted the fresh UTC-date branch " + expectedBranch);
        }}
      }}
    }} else if (outputs.task_title !== "" || outputs.task_target_branch !== "" || outputs.task_context !== "") {{
      throw new Error(testCase.name + ": unselected task context must be empty");
    }}
    if (outputs.task_blocked_active !== String(testCase.expected_blocked)) {{
      throw new Error(testCase.name + ": expected task_blocked_active=" + testCase.expected_blocked + ", got " + outputs.task_blocked_active);
    }}
    if (testCase.reason_contains && !String(outputs.task_reason).includes(testCase.reason_contains)) {{
      throw new Error(testCase.name + ": reason did not contain " + testCase.reason_contains);
    }}
    for (const [provider, expected] of Object.entries(testCase.expected_provider_cooldowns || {{}})) {{
      if (outputs[provider + "_active"] !== String(expected)) {{
        throw new Error(testCase.name + ": expected " + provider + "_active=" + expected + ", got " + outputs[provider + "_active"]);
      }}
    }}
    process.stdout.write("PASS: " + testCase.name + "\\n");
  }}
}})().catch((error) => {{
  process.stderr.write(String(error.stack || error) + "\\n");
  process.exitCode = 1;
}});
"""

completed = subprocess.run(
    [node, "-e", node_program],
    input=json.dumps(cases),
    text=True,
    capture_output=True,
    check=False,
    timeout=20,
)
if completed.stdout:
    print(completed.stdout, end="")
if completed.returncode != 0:
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")
    fail(f"production preflight execution returned {completed.returncode}")
print(f"Production task preflight passed all {len(cases)} offline scenarios.")
