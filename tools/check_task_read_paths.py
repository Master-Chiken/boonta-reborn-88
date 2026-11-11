#!/usr/bin/env python3
"""Verify every task-scoped agent read path exists and fits the Free-tier context budget."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from check_task_ledger import LEDGER_PATH, ROOT, _valid_read_path, validate_ledger

MAX_READ_PATH_BYTES = 3500


def validate_read_paths(data: Any, root: Path = ROOT, max_bytes: int = MAX_READ_PATH_BYTES) -> list[str]:
    errors = validate_ledger(data)
    if errors:
        return errors
    root = root.resolve()
    if max_bytes <= 0:
        return ["max_bytes must be positive"]

    path_count = 0
    for task_index, task in enumerate(data.get("tasks", [])):
        for path_index, path in enumerate(task.get("read_paths") or []):
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
                errors.append(f"{prefix} is {len(payload)} bytes; agent read budget is {max_bytes}: {path}")
                continue
            if b"\x00" in payload:
                errors.append(f"{prefix} contains binary NUL bytes: {path}")
                continue
            try:
                payload.decode("utf-8")
            except UnicodeDecodeError:
                errors.append(f"{prefix} is not valid UTF-8 text: {path}")
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
    print(f"Task read paths passed: {count} files, maximum {MAX_READ_PATH_BYTES} bytes each.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
