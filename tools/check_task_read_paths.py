#!/usr/bin/env python3
"""Verify task-scoped source paths and exact bounded line ranges."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from check_task_ledger import LEDGER_PATH, ROOT, _valid_read_path, validate_ledger

MAX_READ_PATH_BYTES = 96 * 1024
MAX_TOTAL_READ_BYTES = 256 * 1024
MAX_READ_PATH_COUNT = 4
MAX_READ_RANGES = 8
MAX_RANGE_LINES = 80
MAX_TOTAL_RANGE_LINES = 240


def validate_read_paths(
    data: Any,
    root: Path = ROOT,
    max_bytes: int = MAX_READ_PATH_BYTES,
    max_total_bytes: int = MAX_TOTAL_READ_BYTES,
) -> list[str]:
    errors = validate_ledger(data)
    if errors:
        return errors
    root = root.resolve()
    if max_bytes <= 0 or max_total_bytes <= 0:
        return ["read byte budgets must be positive"]

    path_count = 0
    for task_index, task in enumerate(data.get("tasks", [])):
        paths = task.get("read_paths") or []
        ranges = task.get("read_ranges") or []
        if len(paths) > MAX_READ_PATH_COUNT:
            errors.append(f"tasks[{task_index}].read_paths exceeds the {MAX_READ_PATH_COUNT}-file task limit")
            continue
        if paths and not isinstance(ranges, list):
            errors.append(f"tasks[{task_index}].read_ranges must be an array for tasks with read_paths")
            continue
        if paths and not 1 <= len(ranges) <= MAX_READ_RANGES:
            errors.append(
                f"tasks[{task_index}].read_ranges must contain 1-{MAX_READ_RANGES} exact ranges "
                "when read_paths are configured"
            )
        if not paths and ranges:
            errors.append(f"tasks[{task_index}].read_ranges cannot exist without read_paths")

        task_bytes = 0
        line_counts: dict[str, int] = {}
        for path_index, path in enumerate(paths):
            path_count += 1
            prefix = f"tasks[{task_index}].read_paths[{path_index}]"
            if not _valid_read_path(path):
                errors.append(f"{prefix} is not a safe repository text path")
                continue
            candidate = root / path
            if candidate.is_symlink():
                errors.append(f"{prefix} must not be a symlink: {path}")
                continue
            try:
                resolved = candidate.resolve(strict=True)
            except OSError:
                errors.append(f"{prefix} does not exist in the repository: {path}")
                continue
            try:
                resolved.relative_to(root)
            except ValueError:
                errors.append(f"{prefix} resolves outside the repository: {path}")
                continue
            if not resolved.is_file():
                errors.append(f"{prefix} is not a regular file: {path}")
                continue
            try:
                payload = resolved.read_bytes()
            except OSError:
                errors.append(f"{prefix} cannot be read: {path}")
                continue
            if len(payload) > max_bytes:
                errors.append(f"{prefix} is {len(payload)} bytes; per-file source budget is {max_bytes}: {path}")
                continue
            if b"\x00" in payload:
                errors.append(f"{prefix} contains binary NUL bytes: {path}")
                continue
            try:
                decoded = payload.decode("utf-8")
            except UnicodeDecodeError:
                errors.append(f"{prefix} is not valid UTF-8 text: {path}")
                continue
            line_counts[path] = len(decoded.splitlines())
            task_bytes += len(payload)

        if task_bytes > max_total_bytes:
            errors.append(
                f"tasks[{task_index}].read_paths total {task_bytes} bytes; "
                f"aggregate source budget is {max_total_bytes}"
            )

        if isinstance(ranges, list) and paths:
            covered_paths: set[str] = set()
            seen_ranges: set[tuple[str, int, int]] = set()
            total_range_lines = 0
            for range_index, item in enumerate(ranges):
                prefix = f"tasks[{task_index}].read_ranges[{range_index}]"
                if not isinstance(item, dict) or set(item) != {"path", "start_line", "end_line"}:
                    errors.append(f"{prefix} must contain exactly path, start_line and end_line")
                    continue
                path = item["path"]
                start = item["start_line"]
                end = item["end_line"]
                if path not in paths:
                    errors.append(f"{prefix}.path is outside the exact read_paths allow-list")
                    continue
                if type(start) is not int or type(end) is not int or start < 1 or end < start:
                    errors.append(f"{prefix} must use positive ordered integer line numbers")
                    continue
                line_count = end - start + 1
                if line_count > MAX_RANGE_LINES:
                    errors.append(
                        f"{prefix} spans {line_count} lines; per-range limit is {MAX_RANGE_LINES}"
                    )
                    continue
                total_range_lines += line_count
                identity = (path, start, end)
                if identity in seen_ranges:
                    errors.append(f"{prefix} duplicates an existing exact source range")
                seen_ranges.add(identity)
                covered_paths.add(path)
                actual_line_count = line_counts.get(path)
                if actual_line_count is not None and end > actual_line_count:
                    errors.append(
                        f"{prefix} ends at line {end}, beyond {path}'s {actual_line_count} lines"
                    )
            if total_range_lines > MAX_TOTAL_RANGE_LINES:
                errors.append(
                    f"tasks[{task_index}].read_ranges span {total_range_lines} lines; "
                    f"aggregate limit is {MAX_TOTAL_RANGE_LINES}"
                )
            missing_paths = sorted(set(paths) - covered_paths)
            if missing_paths:
                errors.append(
                    f"tasks[{task_index}].read_ranges must cover every exact read_paths entry: "
                    + ", ".join(missing_paths)
                )

    if path_count == 0:
        errors.append("No task-scoped agent read paths are configured")
    return errors


def main() -> int:
    try:
        data = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read canonical task ledger: {exc}", file=sys.stderr)
        return 2
    errors = validate_read_paths(data)
    if errors:
        print("Task read-path validation FAILED:")
        for error in errors:
            print(" - " + error)
        return 1
    count = sum(len(task.get("read_paths") or []) for task in data.get("tasks", []))
    print(
        f"Task read paths passed: {count} exact files with complete bounded line ranges; "
        f"maximum {MAX_READ_PATH_BYTES} bytes per file and {MAX_TOTAL_READ_BYTES} bytes per task."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
