#!/usr/bin/env python3
"""Validate and optionally apply a strictly bounded autonomous patch proposal.

This prototype deliberately performs no network access, provider inference,
branch creation, commits, pushes, PR creation, or arbitrary test execution.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Boonta autonomous patch proposal",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version", "task_id", "base_sha", "summary",
        "unified_diff", "test_ids", "limitations",
    ],
    "properties": {
        "schema_version": {"const": 1},
        "task_id": {"type": "string", "pattern": "^[A-Z0-9][A-Z0-9-]{2,63}$"},
        "base_sha": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
        "summary": {"type": "string", "minLength": 1, "maxLength": 240},
        "unified_diff": {"type": "string", "minLength": 1, "maxLength": 32768},
        "test_ids": {
            "type": "array",
            "minItems": 1,
            "maxItems": 6,
            "uniqueItems": True,
            "items": {
                "type": "string",
                "enum": [
                    "automation.task_preflight",
                    "automation.provider_handoff",
                    "automation.task_ledger",
                ],
            },
        },
        "limitations": {
            "type": "array",
            "maxItems": 8,
            "items": {"type": "string", "minLength": 1, "maxLength": 240},
        },
    },
}

TASK_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,63}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIFF_PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
ALLOWED_TEST_IDS = {
    "automation.task_preflight",
    "automation.provider_handoff",
    "automation.task_ledger",
}
MAX_DIFF_BYTES = 32 * 1024
MAX_FILES = 5
MAX_HUNKS = 100
PROTECTED_EXACT = {
    "AGENTS.md",
    "CODEOWNERS",
    ".github/CODEOWNERS",
    "docs/automation/task-ledger.json",
    "docs/automation/task-ledger-summary.json",
    "docs/automation/patch-path-allowlist.json",
    ".gitignore",
    ".gitattributes",
    ".gitmodules",
    "tools/autonomous_patch_proposal.py",
    "tools/build_autonomous_path_allowlist.py",
    "tools/test_autonomous_path_allowlist.py",
    "tools/run_autonomous_patch_tests.py",
    "tools/test_autonomous_patch_proposal.py",
    "tools/test_autonomous_patch_test_runner.py",
    "tools/test_autonomous_task_preflight.py",
    "tools/check_autonomous_provider_handoff.py",
    "tools/check_task_ledger.py",
}
PROTECTED_PREFIXES = (
    ".github/",
    ".git/",
)


class ProposalError(ValueError):
    """Raised when a proposal cannot be proven safe to validate or apply."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProposalError(f"Duplicate JSON property: {key}")
        result[key] = value
    return result


def load_proposal(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ProposalError("Proposal file cannot be read") from exc
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ProposalError("Proposal is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ProposalError("Proposal root must be a JSON object")
    return value


def _validate_string(value: Any, name: str, limit: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ProposalError(f"{name} must be a non-empty string of at most {limit} characters")
    if any(ord(char) < 32 and char not in "\n\t" for char in value):
        raise ProposalError(f"{name} contains a forbidden control character")
    return value


def validate_proposal(
    proposal: dict[str, Any],
    *,
    expected_task_id: str,
    expected_base_sha: str,
    allowed_paths: set[str],
) -> tuple[str, ...]:
    required = set(SCHEMA["required"])
    actual = set(proposal)
    missing = sorted(required - actual)
    extra = sorted(actual - required)
    if missing:
        raise ProposalError("Missing required properties: " + ", ".join(missing))
    if extra:
        raise ProposalError("Unexpected properties: " + ", ".join(extra))
    if type(proposal["schema_version"]) is not int or proposal["schema_version"] != 1:
        raise ProposalError("schema_version must equal integer 1")
    task_id = _validate_string(proposal["task_id"], "task_id", 64)
    if not TASK_ID_RE.fullmatch(task_id) or task_id != expected_task_id:
        raise ProposalError("Proposal task_id does not match the trusted preflight task")
    base_sha = _validate_string(proposal["base_sha"], "base_sha", 40)
    if not SHA_RE.fullmatch(base_sha) or base_sha != expected_base_sha:
        raise ProposalError("Proposal base_sha does not match the trusted preflight SHA")
    _validate_string(proposal["summary"], "summary", 240)

    diff = _validate_string(proposal["unified_diff"], "unified_diff", MAX_DIFF_BYTES)
    if len(diff.encode("utf-8")) > MAX_DIFF_BYTES:
        raise ProposalError("Unified diff exceeds the 32 KiB byte limit")
    if "\x00" in diff:
        raise ProposalError("Unified diff contains a NUL byte")

    tests = proposal["test_ids"]
    if not isinstance(tests, list) or not 1 <= len(tests) <= 6:
        raise ProposalError("test_ids must contain between one and six allow-listed test identifiers")
    if any(not isinstance(item, str) or item not in ALLOWED_TEST_IDS for item in tests):
        raise ProposalError("test_ids contains an unknown test identifier; arbitrary commands are forbidden")
    if len(set(tests)) != len(tests):
        raise ProposalError("test_ids must not contain duplicates")

    limitations = proposal["limitations"]
    if not isinstance(limitations, list) or len(limitations) > 8:
        raise ProposalError("limitations must be an array containing at most eight strings")
    for item in limitations:
        _validate_string(item, "limitations item", 240)

    if not allowed_paths:
        raise ProposalError("Trusted allowed-path list is empty; refusing model-selected paths")
    return validate_diff_paths(diff, allowed_paths)


def _safe_path(path: str) -> str:
    if not path or not DIFF_PATH_RE.fullmatch(path):
        raise ProposalError("Diff contains a path with unsupported characters")
    if path.startswith("/") or "\\" in path:
        raise ProposalError("Diff contains an absolute path or backslash")
    components = path.split("/")
    if any(part in {"", ".", ".."} for part in components):
        raise ProposalError("Diff contains path traversal or ambiguous path components")
    if (
        path in PROTECTED_EXACT
        or any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)
        or path.startswith(".env")
        or path.lower().endswith((".pem", ".key", ".p12", ".pfx"))
        or any(part.lower() in {"secrets", "credentials"} for part in components)
    ):
        raise ProposalError("Diff attempts to change a protected or credential-bearing repository path")
    return path


def validate_diff_paths(diff: str, allowed_paths: set[str]) -> tuple[str, ...]:
    lines = diff.splitlines()
    paths: list[str] = []
    hunks = 0
    current: str | None = None
    saw_hunk = False
    in_hunk = False
    for line in lines:
        if line.startswith("diff --git "):
            if current is not None and not saw_hunk:
                raise ProposalError("Each diff file section must contain at least one text hunk")
            match = re.fullmatch(r"diff --git a/([^ ]+) b/([^ ]+)", line)
            if not match:
                raise ProposalError("Diff header is malformed or uses unsupported quoting")
            old_path = _safe_path(match.group(1))
            new_path = _safe_path(match.group(2))
            if old_path != new_path:
                raise ProposalError("Renames and cross-path patches are not allowed")
            if old_path not in allowed_paths:
                raise ProposalError(f"Diff path is outside the trusted task allowlist: {old_path}")
            if old_path in paths:
                raise ProposalError("Diff contains a duplicate file section")
            paths.append(old_path)
            current = old_path
            saw_hunk = False
            in_hunk = False
            continue
        if line.startswith((
            "new file mode ", "deleted file mode ", "old mode ", "new mode ",
            "rename from ", "rename to ", "copy from ", "copy to ",
            "GIT binary patch", "Binary files ", "Subproject commit ",
        )):
            raise ProposalError("Binary, mode, rename, copy and submodule changes are not allowed")
        if line.startswith("@@ "):
            if current is None:
                raise ProposalError("Hunk appears before a file header")
            hunks += 1
            saw_hunk = True
            in_hunk = True
            if hunks > MAX_HUNKS:
                raise ProposalError("Diff exceeds the 100-hunk safety limit")
            continue
        if in_hunk:
            continue
        if line.startswith("--- "):
            if current is None or line != "--- a/" + current:
                raise ProposalError("Old-file patch header does not match its diff path")
        elif line.startswith("+++ "):
            if current is None or line != "+++ b/" + current:
                raise ProposalError("New-file patch header does not match its diff path")
    if not paths:
        raise ProposalError("Unified diff contains no file sections")
    if not saw_hunk:
        raise ProposalError("Each diff file section must contain at least one text hunk")
    if len(paths) > MAX_FILES:
        raise ProposalError("Diff exceeds the five-file safety limit")
    return tuple(paths)


def _git(root: Path, args: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProposalError("Git validation command could not be completed") from exc


def validate_checkout(root: Path, expected_base_sha: str) -> None:
    root = root.resolve()
    if not root.is_dir():
        raise ProposalError("Repository checkout directory does not exist")
    top = _git(root, ["rev-parse", "--show-toplevel"])
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != root:
        raise ProposalError("repo_root must be the exact Git checkout root")
    head = _git(root, ["rev-parse", "HEAD"])
    if head.returncode != 0 or head.stdout.strip() != expected_base_sha:
        raise ProposalError("Checkout HEAD differs from the trusted base SHA")
    status = _git(root, ["status", "--porcelain=v1", "--untracked-files=all"])
    if status.returncode != 0 or status.stdout.strip():
        raise ProposalError("Checkout is not clean; refusing to mix proposal changes with existing work")



def validate_tracked_targets(root: Path, paths: tuple[str, ...]) -> None:
    """Reject new files, symlinks, submodules and non-regular tracked targets."""
    for path in paths:
        result = _git(root, ["ls-files", "-s", "--", path])
        if result.returncode != 0:
            raise ProposalError("Could not inspect the Git index for a proposed target")
        entries = [line for line in result.stdout.splitlines() if line.strip()]
        if len(entries) != 1:
            raise ProposalError(f"Patch target must be one existing tracked file: {path}")
        mode = entries[0].split(None, 1)[0]
        if mode not in {"100644", "100755"}:
            raise ProposalError(f"Patch target is not a regular tracked file: {path}")
        candidate = root / path
        parent = candidate.parent
        while parent != root:
            if parent.is_symlink():
                raise ProposalError(f"Patch target has a symlink parent directory: {path}")
            parent = parent.parent


def validate_or_apply(
    root: Path,
    proposal: dict[str, Any],
    *,
    expected_task_id: str,
    expected_base_sha: str,
    allowed_paths: set[str],
    apply: bool = False,
) -> dict[str, Any]:
    paths = validate_proposal(
        proposal,
        expected_task_id=expected_task_id,
        expected_base_sha=expected_base_sha,
        allowed_paths=allowed_paths,
    )
    validate_checkout(root, expected_base_sha)
    validate_tracked_targets(root, paths)
    diff = proposal["unified_diff"]
    check = _git(root, ["apply", "--check", "--whitespace=error"], input_text=diff)
    if check.returncode != 0:
        raise ProposalError("git apply --check rejected the patch: " + check.stderr.strip()[:500])
    if apply:
        applied = _git(root, ["apply", "--whitespace=error"], input_text=diff)
        if applied.returncode != 0:
            raise ProposalError("git apply failed after a successful check: " + applied.stderr.strip()[:500])
    return {
        "status": "APPLIED" if apply else "VALID",
        "task_id": expected_task_id,
        "base_sha": expected_base_sha,
        "changed_paths": list(paths),
        "test_ids": list(proposal["test_ids"]),
        "summary": proposal["summary"],
        "applied": apply,
        "git_commit_created": False,
        "network_accessed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--proposal", type=Path)
    parser.add_argument("--expected-task-id")
    parser.add_argument("--expected-base-sha")
    parser.add_argument("--allowed-path", action="append", default=[])
    parser.add_argument("--apply", action="store_true", help="apply only after all validation checks pass")
    parser.add_argument("--print-schema", action="store_true", help="print the strict proposal JSON Schema")
    args = parser.parse_args()

    if args.print_schema:
        print(json.dumps(SCHEMA, indent=2, sort_keys=True))
        return 0
    if not all((args.repo_root, args.proposal, args.expected_task_id, args.expected_base_sha)):
        parser.error("--repo-root, --proposal, --expected-task-id and --expected-base-sha are required")
    try:
        proposal = load_proposal(args.proposal)
        report = validate_or_apply(
            args.repo_root,
            proposal,
            expected_task_id=args.expected_task_id,
            expected_base_sha=args.expected_base_sha,
            allowed_paths=set(args.allowed_path),
            apply=args.apply,
        )
    except ProposalError as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
