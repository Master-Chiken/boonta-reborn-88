#!/usr/bin/env python3
"""Prepare a bounded provider tool contract from trusted main and target checkouts."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

from build_autonomous_path_allowlist import AllowlistError, build_allowlist, load_json
from validate_trusted_main_checkout import TrustedMainCheckoutError, validate_trusted_main_checkout

TASK_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,63}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPO_PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
MAX_READ_PATHS = 6
MAX_READ_RANGES = 13
MAX_RANGE_LINES = 80
MAX_TOTAL_LINES = 432
MAX_SOURCE_FILE_BYTES = 96 * 1024


class AgentInputError(ValueError):
    """Raised when a selected task cannot be turned into a bounded tool contract."""


def _compact_c_source_lines(lines: list[str]) -> list[str]:
    """Mirror the local MCP's comment/blank-line compaction for C and C++ excerpts."""
    compacted: list[str] = []
    in_block_comment = False
    for raw in lines:
        output: list[str] = []
        quote: str | None = None
        escaped = False
        index = 0
        while index < len(raw):
            char = raw[index]
            next_char = raw[index + 1] if index + 1 < len(raw) else ""
            if in_block_comment:
                if char == "*" and next_char == "/":
                    in_block_comment = False
                    index += 2
                    continue
                index += 1
                continue
            if quote:
                output.append(char)
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
                index += 1
                continue
            if char in {'"', "'"}:
                quote = char
                output.append(char)
                index += 1
                continue
            if char == "/" and next_char == "/":
                break
            if char == "/" and next_char == "*":
                in_block_comment = True
                index += 2
                continue
            output.append(char)
            index += 1
        value = "".join(output).strip()
        if value:
            compacted.append(value)
        else:
            compacted.append("")
    return compacted


def _build_preloaded_source_context(
    source_root: Path,
    read_paths: list[str],
    read_ranges: list[dict[str, int | str]],
) -> tuple[str, str, int]:
    """Render the exact bounded target sources and a canonical digest for MCP verification."""
    files: list[dict[str, Any]] = []
    rendered: list[str] = [
        "APPROVED SOURCE EXCERPTS (exact owner-approved target-branch ranges; read-only):"
    ]
    for file_path in sorted(read_paths):
        payload = (source_root / file_path).read_bytes()
        try:
            source_text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AgentInputError("Approved source path is not valid UTF-8: " + file_path) from exc
        lines = source_text.splitlines()
        is_c_source = file_path.lower().endswith((".c", ".h", ".cc", ".cpp", ".hpp"))
        source_lines = _compact_c_source_lines(lines) if is_c_source else lines
        ranges = sorted(
            (item for item in read_ranges if item["path"] == file_path),
            key=lambda item: (int(item["start_line"]), int(item["end_line"])),
        )
        if not ranges:
            raise AgentInputError("Approved source path has no exact ranges: " + file_path)
        range_results: list[dict[str, Any]] = []
        rendered.append("FILE: " + file_path)
        for item in ranges:
            start, end = int(item["start_line"]), int(item["end_line"])
            if end > len(lines):
                raise AgentInputError("Approved source range exceeds file length: " + file_path)
            selected = source_lines[start - 1:end]
            content = (
                "\n".join(line for line in selected if line)
                if is_c_source
                else "\n".join(f"{start + offset}: {line}" for offset, line in enumerate(selected))
            )
            if not content.strip():
                raise AgentInputError("Approved source range contains no usable text: " + file_path)
            range_results.append({
                "start_line": start,
                "end_line": end,
                "content": content,
                "rendered_lines": sum(1 for line in selected if line) if is_c_source else len(selected),
                "comments_and_blank_lines_omitted": is_c_source,
            })
            rendered.append(f"[{start}-{end}]")
            rendered.append(content)
        files.append({
            "file_path": file_path,
            "file_bytes": len(payload),
            "ranges": range_results,
        })
    canonical = json.dumps(files, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    context = "\n".join(rendered)
    return context, digest, len(context)


def _estimate_source_read_chars(
    source_root: Path,
    read_paths: list[str],
    read_ranges: list[dict[str, int | str]],
) -> int:
    """Estimate the actual one-shot MCP read result plus conservative JSON overhead."""
    total = 1200  # task identity, context object, file/range metadata and JSON framing
    for file_path in read_paths:
        payload = (source_root / file_path).read_bytes()
        try:
            source_text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AgentInputError("Approved source path is not valid UTF-8: " + file_path) from exc
        lines = source_text.splitlines()
        is_c_source = file_path.lower().endswith((".c", ".h", ".cc", ".cpp", ".hpp"))
        rendered = _compact_c_source_lines(lines) if is_c_source else lines
        ranges = [item for item in read_ranges if item["path"] == file_path]
        if not ranges:
            raise AgentInputError("Approved source path has no ranges to estimate: " + file_path)
        for item in ranges:
            start, end = int(item["start_line"]), int(item["end_line"])
            selected = rendered[start - 1:end]
            content = (
                "\\n".join(line for line in selected if line)
                if is_c_source
                else "\\n".join(f"{start + offset}: {line}" for offset, line in enumerate(selected))
            )
            if not content.strip():
                raise AgentInputError("Approved source range contains no usable source text: " + file_path)
            total += len(content) + 96  # per-range JSON keys and path metadata
    return total


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            stdin=subprocess.DEVNULL,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AgentInputError("Could not verify an exact source/policy Git checkout") from exc
    if result.returncode != 0:
        raise AgentInputError("Git checkout verification failed")
    return result.stdout.strip()


def _safe_repo_path(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value) > 120 or not REPO_PATH_RE.fullmatch(value):
        raise AgentInputError("Every read path must be a simple exact repository-relative path")
    if value.startswith("/") or "\\" in value:
        raise AgentInputError("Absolute read paths and backslashes are forbidden")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise AgentInputError("Read path traversal and ambiguous path components are forbidden")
    return value


def _validate_read_contract(
    source_root: Path,
    task: dict[str, Any],
) -> tuple[list[str], list[dict[str, int | str]]]:
    read_paths = task.get("read_paths")
    read_ranges = task.get("read_ranges")
    if (
        not isinstance(read_paths, list)
        or not 1 <= len(read_paths) <= MAX_READ_PATHS
        or any(not isinstance(item, str) for item in read_paths)
        or len(set(read_paths)) != len(read_paths)
    ):
        raise AgentInputError("Selected task must have 1-6 unique exact read_paths")
    read_paths = [_safe_repo_path(item) for item in read_paths]

    if not isinstance(read_ranges, list) or not 1 <= len(read_ranges) <= MAX_READ_RANGES:
        raise AgentInputError("Selected task must have 1-13 exact read_ranges")

    clean_ranges: list[dict[str, int | str]] = []
    total_lines = 0
    seen: set[tuple[str, int, int]] = set()
    covered: set[str] = set()
    for item in read_ranges:
        if not isinstance(item, dict) or set(item) != {"path", "start_line", "end_line"}:
            raise AgentInputError("Every read range must contain exactly path, start_line and end_line")
        path = item["path"]
        start = item["start_line"]
        end = item["end_line"]
        if (
            path not in read_paths
            or type(start) is not int
            or type(end) is not int
            or start < 1
            or end < start
            or end - start + 1 > MAX_RANGE_LINES
        ):
            raise AgentInputError("A read range is outside the task's exact bounded source contract")
        key = (path, start, end)
        if key in seen:
            raise AgentInputError("Task contains duplicate exact read ranges")
        seen.add(key)
        covered.add(path)
        total_lines += end - start + 1
        clean_ranges.append({"path": path, "start_line": start, "end_line": end})
    if covered != set(read_paths):
        raise AgentInputError("Every read path must have at least one exact read range")
    if total_lines > MAX_TOTAL_LINES:
        raise AgentInputError("Selected task source ranges exceed the 432-line aggregate cap")

    for item in read_paths:
        target = source_root / item
        # Resolve containment before walking parents. The path has already
        # rejected absolute roots, backslashes and dot/traversal components.
        try:
            target.resolve(strict=True).relative_to(source_root)
        except (OSError, ValueError) as exc:
            raise AgentInputError("Approved read path escapes the target checkout or is missing: " + item) from exc
        if target.is_symlink() or not target.is_file():
            raise AgentInputError("Approved read path is missing or not a regular file: " + item)
        if target.stat().st_size > MAX_SOURCE_FILE_BYTES:
            raise AgentInputError("Approved read path exceeds the 96 KiB cap: " + item)
        current = source_root
        for component in Path(item).parts[:-1]:
            current = current / component
            if current.is_symlink() or not current.is_dir():
                raise AgentInputError("Approved read path has a symlink or non-directory parent: " + item)
    return read_paths, clean_ranges


def prepare_agent_inputs(
    source_root: Path,
    policy_root: Path,
    *,
    expected_base_sha: str,
    expected_policy_sha: str,
    task_id: str,
    allowlist_output: Path,
) -> dict[str, Any]:
    source_root = source_root.resolve()
    policy_root = policy_root.resolve()
    if not TASK_ID_RE.fullmatch(task_id):
        raise AgentInputError("Selected task ID is invalid")
    if not SHA_RE.fullmatch(expected_base_sha) or not SHA_RE.fullmatch(expected_policy_sha):
        raise AgentInputError("Exact target and trusted policy SHAs are required")

    actual_base = _git(source_root, "rev-parse", "HEAD")
    if actual_base != expected_base_sha:
        raise AgentInputError("Target checkout HEAD differs from the selected task base SHA")
    actual_policy = _git(policy_root, "rev-parse", "HEAD")
    if actual_policy != expected_policy_sha:
        raise AgentInputError("Trusted main checkout HEAD differs from the policy SHA")
    if _git(source_root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise AgentInputError("Target source checkout must be clean before provider invocation")
    try:
        validate_trusted_main_checkout(policy_root, expected_policy_sha)
    except TrustedMainCheckoutError as exc:
        raise AgentInputError(str(exc)) from exc

    summary_path = policy_root / "docs/automation/task-ledger-summary.json"
    if summary_path.is_symlink() or not summary_path.is_file():
        raise AgentInputError("Trusted main compact task summary is missing or symlinked")
    summary = load_json(summary_path)
    if (
        not isinstance(summary, dict)
        or type(summary.get("schema_version")) is not int
        or summary.get("schema_version") != 2
        or summary.get("source") != "docs/automation/task-ledger.json"
        or not isinstance(summary.get("tasks"), list)
    ):
        raise AgentInputError("Trusted main compact task summary has an invalid schema")
    matches = [task for task in summary["tasks"] if isinstance(task, dict) and task.get("task_id") == task_id]
    if len(matches) != 1:
        raise AgentInputError("Selected task must appear exactly once in trusted main summary")
    task = matches[0]
    target_branch = task.get("target_branch")
    if target_branch not in {"main", "dev"}:
        raise AgentInputError("Selected task target branch must be main or dev")

    try:
        allowlist = build_allowlist(
            source_root,
            expected_base_sha=expected_base_sha,
            requested_task_id=task_id,
            policy_root=policy_root,
            expected_policy_sha=expected_policy_sha,
        )
    except AllowlistError as exc:
        raise AgentInputError("Owner path policy is not ready: " + str(exc)) from exc
    if allowlist.get("status") != "READY":
        raise AgentInputError(
            "Owner path policy is not READY (" + str(allowlist.get("status")) + "): " +
            str(allowlist.get("reason", "no owner-approved paths"))
        )

    read_paths, read_ranges = _validate_read_contract(source_root, task)
    unreadable_write_paths = sorted(set(allowlist.get("allowed_paths", [])) - set(read_paths))
    if unreadable_write_paths:
        raise AgentInputError(
            "Owner-approved write paths are not covered by the task's exact read_paths/read_ranges; "
            "no provider invocation is allowed until the owner-approved read contract is updated: " +
            ", ".join(unreadable_write_paths)
        )

    source_read_chars = _estimate_source_read_chars(source_root, read_paths, read_ranges)
    source_read_tokens_estimate = (source_read_chars + 3) // 4
    source_context, source_context_sha256, source_context_chars = _build_preloaded_source_context(
        source_root, read_paths, read_ranges
    )
    source_context_tokens_estimate = (source_context_chars + 3) // 4

    if allowlist_output.is_symlink() or allowlist_output.exists():
        raise AgentInputError("Allowlist report output must be a new non-symlink file")
    allowlist_output.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(allowlist_output, flags, stat.S_IRUSR | stat.S_IWUSR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(allowlist, ensure_ascii=False, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        allowlist_output.unlink(missing_ok=True)
        raise

    return {
        "schema_version": 1,
        "task_id": task_id,
        "target_branch": target_branch,
        "base_sha": expected_base_sha,
        "policy_sha": expected_policy_sha,
        "read_paths": read_paths,
        "read_ranges": read_ranges,
        "source_read_chars": source_read_chars,
        "source_read_tokens_estimate": source_read_tokens_estimate,
        "source_context": source_context,
        "source_context_sha256": source_context_sha256,
        "source_context_chars": source_context_chars,
        "source_context_tokens_estimate": source_context_tokens_estimate,
        "allowed_paths": allowlist["allowed_paths"],
        "approval_ref": allowlist["approval_ref"],
        "allowlist_report": str(allowlist_output.resolve()),
        "source_checkout_modified": False,
        "policy_checkout_modified": False,
        "model_has_github_write_tools": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--policy-root", type=Path, required=True)
    parser.add_argument("--expected-base-sha", required=True)
    parser.add_argument("--expected-policy-sha", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--allowlist-output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = prepare_agent_inputs(
            args.source_root,
            args.policy_root,
            expected_base_sha=args.expected_base_sha,
            expected_policy_sha=args.expected_policy_sha,
            task_id=args.task_id,
            allowlist_output=args.allowlist_output,
        )
    except (AgentInputError, AllowlistError, OSError, ValueError) as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps({"status": "READY", **result}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
