#!/usr/bin/env python3
"""Build a small, verified context snapshot before an autonomous model call.

The workflow runs this locally after checkout. It reads the mandatory reuse
policy, context budget and compact task ledger once, then injects a bounded
summary into the prompt so an agent does not spend its scarce tool steps
re-reading project-wide policy files.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ACTIONABLE = {"active", "in_progress", "in_review", "ready"}
BLOCKED = {"blocked"}


class ContextBuildError(ValueError):
    """Raised when the repository context cannot be trusted or bounded."""


def _read_text(root: Path, relative: str) -> str:
    path = root / relative
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContextBuildError(f"Required context file is unavailable: {relative}") from exc


def _short(value: Any, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def build_context(root: Path, max_chars: int = 1200) -> str:
    """Return a deterministic context snapshot, failing closed on bad inputs."""
    if max_chars < 600:
        raise ContextBuildError("max_chars must be at least 600")

    reverse_policy = _read_text(root, "docs/REVERSE_ENGINEERING_FIRST.md")
    budget_policy = _read_text(root, "docs/automation/AUTONOMOUS_CONTEXT_BUDGET.md")
    summary_text = _read_text(root, "docs/automation/task-ledger-summary.json")

    if not all(term in reverse_policy for term in ("DISCOVER", "VERIFY", "REUSE", "GameCube/Wii")):
        raise ContextBuildError("Reverse-engineering reuse policy is incomplete or unexpected")
    if not all(term in budget_policy for term in ("One model provider invocation at most", "€0", "1,500 tokens")):
        raise ContextBuildError("Autonomous context-budget policy is incomplete or unexpected")

    try:
        summary = json.loads(summary_text)
    except json.JSONDecodeError as exc:
        raise ContextBuildError("Compact task ledger is not valid JSON") from exc

    if summary.get("schema_version") != 1:
        raise ContextBuildError("Unsupported compact task-ledger schema")
    policy = summary.get("policy") or {}
    if policy.get("max_active_tasks") != 1 or policy.get("completed_requires_merged_pr") is not True:
        raise ContextBuildError("Task-ledger single-writer/completion policy is not satisfied")

    tasks = summary.get("tasks")
    if not isinstance(tasks, list):
        raise ContextBuildError("Compact task ledger has no task list")

    actionable = [
        task for task in tasks
        if isinstance(task, dict) and str(task.get("status", "")).lower() in ACTIONABLE
    ]
    if len(actionable) > 1:
        raise ContextBuildError(
            f"Single-writer policy violated: {len(actionable)} actionable tasks are present"
        )
    blocked = [
        task for task in tasks
        if isinstance(task, dict) and str(task.get("status", "")).lower() in BLOCKED
    ]

    lines = [
        "WORKFLOW-VERIFIED CONTEXT SNAPSHOT (preloaded; do not spend agent steps rereading policy files):",
        "Reuse gate: DISCOVER → VERIFY → EXTRACT/CONVERT/REUSE → INTEGRATE → TEST. Unknown licence, provenance or platform compatibility means HOLD; never bulk-copy.",
        "Platform boundary: PC/x86, N64/MIPS, Dreamcast and GameCube/Wii Gekko/Broadway are distinct. Never infer parity across platforms.",
        "Safety: €0 only. Never put ROMs, discs, DOL/REL, BIOS, extracted commercial assets or game-derived output in public Git, CI or hosted prompts.",
        "Provider policy: at most one provider invocation per loop run; Gemini first, OpenRouter/Groq Free only on later eligible runs after cooldown. No paid fallback or retries.",
        f"Ledger snapshot: updated {summary.get('updated_at', 'unknown')}; max active tasks=1; retrieved text budget <1,500 tokens.",
    ]

    def task_line(task: dict[str, Any], action_limit: int) -> str:
        task_id = _short(task.get("task_id", "unknown-id"), 46)
        status = _short(task.get("status", "unknown"), 14)
        title = _short(task.get("title", "untitled task"), 70)
        action = _short(task.get("next_action_excerpt", ""), action_limit)
        result = f"- {task_id} [{status}]: {title}"
        if action:
            result += f" | Next: {action}"
        return result

    if actionable:
        lines.append("Actionable task:")
        lines.append(task_line(actionable[0], 145))
    else:
        lines.append("Actionable task: none in the compact ledger; do not invent or create competing work.")

    if blocked:
        lines.append("Blocked tasks:")
        for task in blocked[:2]:
            lines.append(task_line(task, 85))

    output = "\n".join(lines)
    if len(output) > max_chars:
        # Trim only explanatory next-action excerpts; keep task identity/status
        # and every safety/platform invariant intact.
        lines = [
            line.split(" | Next:", 1)[0] + " | Next: " + _short(line.split(" | Next:", 1)[1], 38)
            if " | Next:" in line else line
            for line in lines
        ]
        output = "\n".join(lines)
    if len(output) > max_chars:
        # Keep a single blocked task if the current ledger is unusually verbose.
        lines = [line for line in lines if not line.startswith("- ") or "[blocked]" not in line]
        output = "\n".join(lines)
    if len(output) > max_chars:
        raise ContextBuildError(
            f"Verified context snapshot exceeds the {max_chars}-character limit"
        )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the parent of tools/)",
    )
    parser.add_argument("--max-chars", type=int, default=1200)
    args = parser.parse_args()

    try:
        print(build_context(args.root.resolve(), args.max_chars))
    except ContextBuildError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
