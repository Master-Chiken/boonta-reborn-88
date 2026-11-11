#!/usr/bin/env python3
"""Build bounded provider context from the canonical task ledger and exact source ranges."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


class ContextBuildError(ValueError):
    """Raised when a provider context cannot be proven safe and consistent."""


SAFE_PATH_RE = re.compile(r"^[A-Za-z0-9._/-]{1,120}$")
ALLOWED_SUFFIXES = {
    ".py", ".js", ".ts", ".tsx", ".json", ".yaml", ".yml", ".toml", ".md",
    ".c", ".h", ".cc", ".cpp", ".hpp", ".cmake", ".sh",
}
MAX_SOURCE_PATHS = 4
MAX_SOURCE_RANGES = 8
MAX_RANGE_LINES = 80
MAX_TOTAL_RANGE_LINES = 240
MAX_SOURCE_FILE_BYTES = 96 * 1024


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


def _safe_source_path(path: Any) -> bool:
    if not isinstance(path, str) or not SAFE_PATH_RE.fullmatch(path):
        return False
    parts = path.split("/")
    return (
        not path.startswith("/")
        and all(part and part not in {".", ".."} for part in parts)
        and Path(path).suffix.lower() in ALLOWED_SUFFIXES
        and path not in {"docs/automation/task-ledger.json", "docs/automation/task-ledger-summary.json"}
        and not any(part.lower() in {"generated", "roms", "private", "secrets", "credentials"} for part in parts)
    )


def _build_source_excerpt(
    source_root: Path,
    read_paths: list[str],
    read_ranges: Any,
    max_source_chars: int,
) -> str:
    if not read_ranges:
        return ""
    if not isinstance(read_ranges, list) or not 1 <= len(read_ranges) <= MAX_SOURCE_RANGES:
        raise ContextBuildError("Selected task source ranges must contain 1-8 exact ranges")
    checked: list[tuple[str, int, int]] = []
    total_lines = 0
    for item in read_ranges:
        if not isinstance(item, dict) or set(item) != {"path", "start_line", "end_line"}:
            raise ContextBuildError("Every source range must contain exactly path, start_line and end_line")
        path = item["path"]
        start = item["start_line"]
        end = item["end_line"]
        if path not in read_paths or not _safe_source_path(path):
            raise ContextBuildError("A source range refers to a path outside the exact task read allow-list")
        if type(start) is not int or type(end) is not int or start < 1 or end < start:
            raise ContextBuildError("Source range line numbers must be positive, ordered integers")
        line_count = end - start + 1
        if line_count > MAX_RANGE_LINES:
            raise ContextBuildError(f"Source range exceeds the {MAX_RANGE_LINES}-line per-range limit")
        total_lines += line_count
        checked.append((path, start, end))
    if total_lines > MAX_TOTAL_RANGE_LINES:
        raise ContextBuildError(f"Task source ranges exceed the {MAX_TOTAL_RANGE_LINES}-line aggregate limit")
    if set(path for path, _, _ in checked) != set(read_paths):
        raise ContextBuildError("Every exact task read path must have at least one bounded source range")

    source_root = source_root.resolve()
    per_path_budget = max_source_chars // len(read_paths)
    rendered: list[str] = []
    for path in read_paths:
        path_ranges = [(start, end) for item_path, start, end in checked if item_path == path]
        if not path_ranges:
            raise ContextBuildError(f"No bounded source range is configured for {path}")
        try:
            source_file = (source_root / path).resolve(strict=True)
            source_file.relative_to(source_root)
        except (OSError, ValueError) as exc:
            raise ContextBuildError(f"Exact source path is missing or escapes the selected target checkout: {path}") from exc
        if not source_file.is_file() or source_file.is_symlink():
            raise ContextBuildError(f"Exact source path is not a regular file: {path}")
        try:
            payload = source_file.read_bytes()
        except OSError as exc:
            raise ContextBuildError(f"Exact source path cannot be read: {path}") from exc
        if len(payload) > MAX_SOURCE_FILE_BYTES or b"\x00" in payload:
            raise ContextBuildError(f"Exact source path exceeds the bounded text-file policy: {path}")
        try:
            lines = payload.decode("utf-8").splitlines()
        except UnicodeDecodeError as exc:
            raise ContextBuildError(f"Exact source path is not valid UTF-8: {path}") from exc
        chunks: list[str] = []
        remaining = per_path_budget
        for start, end in path_ranges:
            if end > len(lines):
                raise ContextBuildError(f"Source range {path}:{start}-{end} exceeds the {len(lines)}-line file")
            header = f"[{path}:{start}-{end}]\n"
            body = "\n".join(lines[start - 1:end])
            chunk = header + body + "\n"
            if len(chunk) > remaining:
                if remaining <= len(header) + 24:
                    break
                chunk = header + body[: remaining - len(header) - 2].rstrip() + "…\n"
            chunks.append(chunk)
            remaining -= len(chunk)
            if remaining <= 0:
                break
        rendered.append("".join(chunks).rstrip())
    output = "SOURCE EXCERPTS (read-only; exact task ranges on target branch):\n" + "\n".join(rendered)
    if len(output) > max_source_chars:
        output = output[: max_source_chars - 1].rstrip() + "…"
    return output


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
    source_root: Path | None = None,
    max_source_chars: int = 0,
) -> str:
    """Validate selected v2 task metadata and preload exact, bounded source excerpts."""
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
    if max_source_chars < 0 or max_source_chars > 2200:
        raise ContextBuildError("Source excerpt budget must be between 0 and 2,200 characters")

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
        isinstance(read_paths, list) and 1 <= len(read_paths) <= MAX_SOURCE_PATHS
        and all(_safe_source_path(path) for path in read_paths)
        and len(set(read_paths)) == len(read_paths)
    ):
        raise ContextBuildError("Selected task has no valid 1-4 path read allow-list")
    handoff_paths_line = "Read-only source paths (select at most one): " + ", ".join(read_paths)
    required_handoff_text = [task["question_excerpt"], task["next_action_excerpt"], *criteria[:5], handoff_paths_line]
    if not all(item in task_context for item in required_handoff_text):
        raise ContextBuildError("Global preflight context does not contain the selected ledger excerpts/read paths")

    source_excerpt = _build_source_excerpt(
        source_root or root, read_paths, task.get("read_ranges", []), max_source_chars
    )
    rendered_paths_line = "Exact read-only source paths: " + ", ".join(read_paths)
    prefix_lines = [
        "VERIFIED CONTEXT:",
        "€0; no commercial game data; preserve AGPL/MIT and platform provenance.",
        "Canonical ledger v2 verified.",
        "Task:",
    ]
    source_reserve = len(source_excerpt) + (2 if source_excerpt else 0)
    available_task_chars = min(
        max_task_context,
        max_chars - len("\n".join(prefix_lines)) - source_reserve - 2,
    )
    if available_task_chars < 250:
        raise ContextBuildError("Verified-context ceiling leaves too little room for safe task/source excerpts")
    selected_criteria = criteria[:max_criteria]
    compact_lines = [
        f"Task ID: {task_id}",
        f"Title: {task_title}",
        f"Target branch: {target_branch}",
        "Platform scope: " + ", ".join(scope),
        rendered_paths_line,
        "Question: " + task["question_excerpt"],
        f"Acceptance criteria ({criteria_total} total; first {len(selected_criteria)}):",
        *("- " + item for item in selected_criteria),
        "Next: " + _short(task["next_action_excerpt"], max_next_action),
    ]
    bounded_task_context = "\n".join(compact_lines)
    if len(bounded_task_context) > available_task_chars:
        raise ContextBuildError(
            f"Verified task excerpts exceed the configured {available_task_chars}-character budget "
            f"({len(bounded_task_context)} chars); reduce task excerpts or source ranges"
        )
    lines = [*prefix_lines, bounded_task_context]
    if source_excerpt:
        lines.append(source_excerpt)
    output = "\n".join(lines)
    if len(output) > max_chars:
        raise ContextBuildError(f"Verified context exceeds the configured {max_chars}-character limit ({len(output)} chars)")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--task-title", required=True)
    parser.add_argument("--target-branch", required=True)
    parser.add_argument("--task-context", required=True)
    parser.add_argument("--max-chars", type=int, default=3500)
    parser.add_argument("--max-task-context", type=int, default=2500)
    parser.add_argument("--max-criteria", type=int, default=5)
    parser.add_argument("--max-next-action", type=int, default=420)
    parser.add_argument("--max-source-chars", type=int, default=0)
    args = parser.parse_args()
    try:
        print(build_context(
            args.root, args.task_id, args.task_title, args.target_branch,
            args.task_context, args.max_chars, args.max_task_context,
            args.max_criteria, args.max_next_action, args.source_root,
            args.max_source_chars,
        ))
    except ContextBuildError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
