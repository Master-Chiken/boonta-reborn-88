#!/usr/bin/env python3
"""Build a bounded provider context from the canonical v2 task ledger."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


class ContextBuildError(ValueError):
    """Raised when a provider context cannot be proven safe and consistent."""


def _read(root: Path, relative: str) -> str:
    try:
        return (root / relative).read_text(encoding="utf-8")
    except OSError as exc:
        raise ContextBuildError(f"Required context file is unavailable: {relative}") from exc


def _short(value: Any, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def build_context(
    root: Path,
    task_id: str,
    task_title: str,
    target_branch: str,
    task_context: str,
    max_chars: int = 3500,
    max_task_context: int = 2500,
    max_criteria: int = 5,
    max_next_action: int = 420,
) -> str:
    """Validate the selected v2 ledger row and emit compact, preloaded context."""
    root = root.resolve()
    if not task_id.strip() or not task_title.strip() or target_branch not in {"main", "dev"}:
        raise ContextBuildError("Selected task identity or target branch is invalid")
    if not task_context.strip() or len(task_context) > 2500:
        raise ContextBuildError("Global preflight task context is empty or exceeds 2,500 characters")
    for expected in (f"Task ID: {task_id}", f"Title: {task_title}", f"Target branch: {target_branch}"):
        if expected not in task_context:
            raise ContextBuildError(f"Global preflight context does not contain {expected!r}")
    if max_chars < 900 or max_task_context < 250:
        raise ContextBuildError("Context ceilings are below safe minimums")
    if not 1 <= max_criteria <= 5 or not 80 <= max_next_action <= 420:
        raise ContextBuildError("Provider-specific criteria/action limits are outside safe bounds")

    reverse_policy = _read(root, "docs/REVERSE_ENGINEERING_FIRST.md")
    budget_policy = _read(root, "docs/automation/AUTONOMOUS_CONTEXT_BUDGET.md")
    summary_text = _read(root, "docs/automation/task-ledger-summary.json")
    if not all(term in reverse_policy for term in ("DISCOVER", "VERIFY", "REUSE", "GameCube/Wii")):
        raise ContextBuildError("Reverse-engineering policy is incomplete or unexpected")
    if not all(term in budget_policy for term in ("One model provider invocation at most", "€0", "1,500 tokens")):
        raise ContextBuildError("Provider context-budget policy is incomplete or unexpected")
    try:
        summary = json.loads(summary_text)
    except json.JSONDecodeError as exc:
        raise ContextBuildError("Compact task ledger is not valid JSON") from exc
    if summary.get("schema_version") != 2 or summary.get("source") != "docs/automation/task-ledger.json":
        raise ContextBuildError("Expected canonical compact task-ledger schema v2")
    policy = summary.get("policy") or {}
    if policy.get("max_active_tasks") != 1 or policy.get("completed_requires_merged_pr") is not True:
        raise ContextBuildError("Task-ledger single-writer/completion policy is not satisfied")
    tasks = summary.get("tasks")
    if not isinstance(tasks, list):
        raise ContextBuildError("Compact task ledger has no task list")
    matches = [task for task in tasks if isinstance(task, dict) and task.get("task_id") == task_id]
    if len(matches) != 1:
        raise ContextBuildError("Selected task ID is missing or duplicated in the compact ledger")
    task = matches[0]
    if task.get("title") != task_title or task.get("target_branch") != target_branch:
        raise ContextBuildError("Selected task title or target branch differs from the canonical ledger")
    status = str(task.get("status", "")).lower()
    if status not in {"active", "in_progress", "in_review", "ready", "blocked"}:
        raise ContextBuildError("Selected task has a non-executable ledger status")
    if status == "blocked" and task_id != "AUTOMATION-LEDGER-ACTIVATION":
        raise ContextBuildError("Only the explicitly tracked activation bootstrap may be selected while blocked")
    if task.get("pr_url") or task.get("head_sha"):
        raise ContextBuildError("Selected task already has PR/head evidence; refusing a duplicate writer")
    scope = task.get("platform_scope")
    criteria = task.get("acceptance_criteria_excerpt")
    criteria_total = task.get("acceptance_criteria_total")
    if not isinstance(scope, list) or not scope or not all(isinstance(x, str) and x.strip() for x in scope):
        raise ContextBuildError("Selected task has no bounded platform scope")
    if not isinstance(task.get("question_excerpt"), str) or not task["question_excerpt"].strip():
        raise ContextBuildError("Selected task has no question excerpt")
    if not isinstance(task.get("next_action_excerpt"), str) or not task["next_action_excerpt"].strip():
        raise ContextBuildError("Selected task has no next action")
    if not isinstance(criteria, list) or not criteria or not all(isinstance(x, str) and x.strip() for x in criteria):
        raise ContextBuildError("Selected task has no acceptance-criteria excerpts")
    if not isinstance(criteria_total, int) or criteria_total < len(criteria):
        raise ContextBuildError("Selected task acceptance-criteria count is inconsistent")
    read_paths = task.get("read_paths")
    if not (
        isinstance(read_paths, list) and 1 <= len(read_paths) <= 4
        and all(
            isinstance(path, str) and re.fullmatch(r"[A-Za-z0-9._/-]{1,120}", path)
            and not path.startswith("/")
            and all(part and part not in {".", ".."} for part in path.split("/"))
            and Path(path).suffix.lower() in {".py", ".js", ".ts", ".tsx", ".json", ".yaml", ".yml", ".toml", ".md", ".c", ".h", ".cc", ".cpp", ".hpp", ".cmake", ".sh"}
            and path not in {"docs/automation/task-ledger.json", "docs/automation/task-ledger-summary.json"}
            and not any(part.lower() in {"generated", "roms", "private"} for part in path.split("/"))
            for path in read_paths
        )
        and len(set(read_paths)) == len(read_paths)
    ):
        raise ContextBuildError("Selected task has no valid 1-4 path read allow-list")
    read_paths_line = "Read-only source paths (select at most one): " + ", ".join(read_paths)
    required_handoff_text = [task["question_excerpt"], task["next_action_excerpt"], *criteria[:5], read_paths_line]
    if not all(item in task_context for item in required_handoff_text):
        raise ContextBuildError("Global preflight context does not contain the selected ledger excerpts/read paths")

    prefix_lines = [
        "VERIFIED CONTEXT:",
        "€0; no commercial game data; preserve AGPL/MIT and platform provenance.",
        "Canonical ledger v2 verified.",
        "Task:",
    ]
    # Render from verified task fields instead of blindly truncating the global
    # handoff. Providers may choose a smaller excerpt budget to reserve room for
    # one targeted source read.
    available_task_chars = min(max_task_context, max_chars - len("\n".join(prefix_lines)) - 1)
    if available_task_chars < 250:
        raise ContextBuildError("Verified-context ceiling leaves too little room for a safe task handoff")
    selected_criteria = criteria[:max_criteria]
    compact_lines = [
        f"Task ID: {task_id}",
        f"Title: {task_title}",
        f"Target branch: {target_branch}",
        "Platform scope: " + ", ".join(scope),
        read_paths_line,
        "Question: " + task["question_excerpt"],
        f"Acceptance criteria ({criteria_total} total; first {len(selected_criteria)}):",
        *("- " + item for item in selected_criteria),
        "Next: " + _short(task["next_action_excerpt"], max_next_action),
    ]
    bounded_task_context = "\n".join(compact_lines)
    if len(bounded_task_context) > available_task_chars:
        raise ContextBuildError(
            f"Verified task excerpts exceed the configured {available_task_chars}-character budget "
            f"({len(bounded_task_context)} chars); reduce the task excerpt or provider limits"
        )
    lines = [*prefix_lines, bounded_task_context]
    output = "\n".join(lines)
    if len(output) > max_chars:
        raise ContextBuildError(
            f"Verified context exceeds the configured {max_chars}-character limit ({len(output)} chars)"
        )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--task-title", required=True)
    parser.add_argument("--target-branch", required=True)
    parser.add_argument("--task-context", required=True)
    parser.add_argument("--max-chars", type=int, default=3500)
    parser.add_argument("--max-task-context", type=int, default=2500)
    parser.add_argument("--max-criteria", type=int, default=5)
    parser.add_argument("--max-next-action", type=int, default=420)
    args = parser.parse_args()
    try:
        print(build_context(
            args.root, args.task_id, args.task_title, args.target_branch,
            args.task_context, args.max_chars, args.max_task_context,
            args.max_criteria, args.max_next_action,
        ))
    except ContextBuildError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
