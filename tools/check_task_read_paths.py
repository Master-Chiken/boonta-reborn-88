#!/usr/bin/env python3
"""Verify exact task-scoped source paths are safe and fit the bounded context budget."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from check_task_ledger import LEDGER_PATH, ROOT, _valid_read_path, validate_ledger

MAX_READ_PATH_BYTES = 96 * 1024
MAX_TOTAL_READ_BYTES = 256 * 1024
MAX_READ_PATH_COUNT = 4


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

    total_bytes = 0
    path_count = 0
    for task_index, task in enumerate(data.get("tasks", [])):
        paths = task.get("read_paths") or []
        if len(paths) > MAX_READ_PATH_COUNT:
            errors.append(f"tasks[{task_index}].read_paths exceeds the {MAX_READ_PATH_COUNT}-file task limit")
            continue
        task_bytes = 0
        for path_index, path in enumerate(paths):
            path_count += 1
            prefix = f"tasks[{task_index}].read_paths[{path_index}]"
            if not _valid_read_path(path):
                errors.append(f"{prefix} is not a safe repository text path")
                continue
            try:
                resolved = (root / path).resolve(strict=True)
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
                payload.decode("utf-8")
            except UnicodeDecodeError:
                errors.append(f"{prefix} is not valid UTF-8 text: {path}")
                continue
            task_bytes += len(payload)
        if task_bytes > max_total_bytes:
            errors.append(
                f"tasks[{task_index}].read_paths total {task_bytes} bytes; "
                f"aggregate source budget is {max_total_bytes}"
            )
        total_bytes += task_bytes
    if path_count == 0:
        errors.append("No task-scoped agent read paths are configured")
    if total_bytes > max_total_bytes:
        errors.append(f"All task read paths total {total_bytes} bytes; aggregate source budget is {max_total_bytes}")
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
        f"Task read paths passed: {count} exact files; "
        f"maximum {MAX_READ_PATH_BYTES} bytes per file and {MAX_TOTAL_READ_BYTES} bytes total."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
