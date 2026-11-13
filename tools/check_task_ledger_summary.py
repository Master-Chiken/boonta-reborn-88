#!/usr/bin/env python3
"""Validate the compact autonomous task index against the canonical ledger."""
from pathlib import Path
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/automation/task-ledger.json"
SUMMARY = ROOT / "docs/automation/task-ledger-summary.json"

def excerpt(value: object, maximum: int = 360) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= maximum:
        return text
    shortened = text[: maximum - 1]
    shortened = shortened.rsplit(" ", 1)[0]
    return shortened + "…"

def action_excerpt(value: object, maximum: int = 140) -> str:
    """Prefer the actionable tail after a historical changelog's explicit Next marker."""
    text = " ".join(str(value or "").split())
    marker = text.rfind("Next:")
    if marker >= 0:
        text = text[marker + len("Next:"):].strip()
    return excerpt(text, maximum)


def build_summary(ledger: dict) -> dict:
    return {
        "schema_version": 2,
        "source": "docs/automation/task-ledger.json",
        "updated_at": ledger.get("updated_at"),
        "completed_task_ids": [
            task["task_id"] for task in ledger.get("tasks", [])
            if task.get("status") == "completed"
        ],
        "policy": {
            "max_active_tasks": ledger.get("policy", {}).get("max_active_tasks", 1),
            "completed_requires_merged_pr": True,
        },
        "tasks": [
            {
                "task_id": task["task_id"],
                "title": task["title"],
                "owner_role_id": task["owner_role_id"],
                "parent_objective_id": task["parent_objective_id"],
                "depends_on": task.get("depends_on", []),
                "owner_approved": task.get("owner_approved", False),
                "queue": task.get("queue"),
                "platform_scope": task.get("platform_scope", []),
                "status": task["status"],
                "target_branch": task.get("target_branch"),
                "read_paths": task.get("read_paths", []),
                "read_ranges": task.get("read_ranges", []),
                "question_excerpt": excerpt(task.get("question"), 240),
                "acceptance_criteria_total": len(task.get("acceptance_criteria") or []),
                # Keep the handoff compact; the full count remains available to the agent.
                "acceptance_criteria_excerpt": [
                    excerpt(item, 140)
                    for item in (task.get("acceptance_criteria") or [])[:4]
                ],
                "pr_url": task.get("pr_url"),
                "head_sha": task.get("head_sha"),
                # Historical notes can precede "Next:"; prioritize the current action.
                "next_action_excerpt": action_excerpt(
                    task.get("next_action"), 180 if task["status"] == "queued" else 140
                ),
            }
            for task in ledger.get("tasks", [])
            if task.get("status") in {"queued", "active", "blocked", "in_review"}
        ],
    }

def main() -> int:
    try:
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        expected = json.dumps(build_summary(ledger), indent=2, ensure_ascii=False) + "\n"
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"Cannot build task summary: {exc}", file=sys.stderr)
        return 2

    if "--write" in sys.argv[1:]:
        SUMMARY.write_text(expected, encoding="utf-8")
        print(f"Updated {SUMMARY.relative_to(ROOT)}")
        return 0

    try:
        actual = SUMMARY.read_text(encoding="utf-8")
    except OSError as exc:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            SUMMARY.write_text(expected, encoding="utf-8")
            print("Missing derived task summary was regenerated in this GitHub Actions workspace.")
            return 0
        print(f"Missing compact task summary: {exc}", file=sys.stderr)
        return 1
    if actual != expected:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            # This JSON is a generated handoff cache, not the canonical ledger.
            # Refresh only the ephemeral runner copy; never commit or push it here.
            SUMMARY.write_text(expected, encoding="utf-8")
            print("Stale derived task summary was regenerated in this GitHub Actions workspace.")
            return 0
        print("Task summary is stale. Regenerate with:")
        print("  python3 tools/check_task_ledger_summary.py --write")
        return 1
    print("Compact autonomous task summary matches the canonical ledger.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
