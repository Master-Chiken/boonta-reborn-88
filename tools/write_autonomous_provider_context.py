#!/usr/bin/env python3
"""Create the exact task context consumed by the proposal-only local MCP server."""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any

TASK_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,63}$")
MAX_CONTEXT_FILE_BYTES = 16 * 1024
MAX_VERIFIED_CONTEXT_BYTES = 12 * 1024


class ProviderContextError(ValueError):
    """Raised when a workflow cannot create a safe, task-bound MCP context."""


def write_provider_context(
    workspace: Path,
    *,
    task_id: str,
    task_title: str,
    task_description: str,
    target_branch: str,
    verified_context: str,
) -> dict[str, Any]:
    workspace = workspace.resolve(strict=True)
    if not workspace.is_dir():
        raise ProviderContextError("GitHub workspace must be a real directory")
    if not TASK_ID_RE.fullmatch(task_id):
        raise ProviderContextError("Task ID is invalid")
    if target_branch not in {"main", "dev"}:
        raise ProviderContextError("Target branch must be main or dev")
    if not isinstance(task_title, str) or not task_title.strip() or len(task_title) > 240:
        raise ProviderContextError("Task title must contain 1-240 characters")
    if not isinstance(task_description, str) or not task_description.strip() or len(task_description) > 6000:
        raise ProviderContextError("Task description must contain 1-6000 characters")
    if not isinstance(verified_context, str) or not verified_context.strip():
        raise ProviderContextError("Verified context must be non-empty text")
    context_bytes = verified_context.encode("utf-8")
    if len(context_bytes) > MAX_VERIFIED_CONTEXT_BYTES:
        raise ProviderContextError("Verified context exceeds the 12 KiB MCP limit")

    directory = workspace / ".gemini"
    if directory.is_symlink():
        raise ProviderContextError("Gemini context directory must not be a symlink")
    directory.mkdir(mode=0o700, exist_ok=True)
    if directory.is_symlink() or not directory.is_dir():
        raise ProviderContextError("Gemini context directory is not a safe directory")
    output = directory / "context.json"
    if output.exists() or output.is_symlink():
        raise ProviderContextError("MCP context output already exists; refusing to overwrite")

    payload = {
        "task_id": task_id,
        "task_title": task_title,
        "task_description": task_description,
        "task_target_branch": target_branch,
        "verified_context": verified_context,
    }
    encoded = (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > MAX_CONTEXT_FILE_BYTES:
        raise ProviderContextError("Serialized MCP context exceeds the 16 KiB file limit")

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(output, flags, stat.S_IRUSR | stat.S_IWUSR)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        output.unlink(missing_ok=True)
        raise
    return {
        "status": "READY",
        "context_path": str(output),
        "context_bytes": len(encoded),
        "task_id": task_id,
        "target_branch": target_branch,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--task-title", required=True)
    parser.add_argument("--task-description", required=True)
    parser.add_argument("--target-branch", required=True)
    parser.add_argument("--verified-context-stdin", action="store_true")
    args = parser.parse_args()
    if not args.verified_context_stdin:
        print(json.dumps({"status": "REJECTED", "reason": "verified context must be supplied on stdin"}))
        return 2
    try:
        verified_context = sys.stdin.read()
        result = write_provider_context(
            args.workspace,
            task_id=args.task_id,
            task_title=args.task_title,
            task_description=args.task_description,
            target_branch=args.target_branch,
            verified_context=verified_context,
        )
    except (OSError, ProviderContextError, UnicodeError) as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
