#!/usr/bin/env python3
"""Validate the trusted main checkout while allowing only a regenerated summary cache."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from check_task_ledger_summary import build_summary

LEDGER = "docs/automation/task-ledger.json"
SUMMARY = "docs/automation/task-ledger-summary.json"
POLICY = "docs/automation/patch-path-allowlist.json"
TRUSTED_PATHS = (LEDGER, SUMMARY, POLICY)


class TrustedMainCheckoutError(ValueError):
    """Raised when main task or write-path authority is not committed/trusted."""


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
        raise TrustedMainCheckoutError("Could not verify trusted main Git state") from exc
    if result.returncode != 0:
        raise TrustedMainCheckoutError("Trusted main Git verification failed")
    return result.stdout.strip()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise TrustedMainCheckoutError("Trusted main task summary contains duplicate JSON properties")
        value[key] = item
    return value


def validate_trusted_main_checkout(root: Path, expected_sha: str) -> Path:
    root = root.resolve()
    if not root.is_dir():
        raise TrustedMainCheckoutError("Trusted main checkout does not exist")
    if len(expected_sha) != 40 or any(char not in "0123456789abcdef" for char in expected_sha):
        raise TrustedMainCheckoutError("Trusted main policy SHA must be a lowercase 40-character commit")
    top = Path(_git(root, "rev-parse", "--show-toplevel")).resolve()
    if top != root:
        raise TrustedMainCheckoutError("Trusted main path must be the exact Git checkout root")
    if _git(root, "rev-parse", "HEAD") != expected_sha:
        raise TrustedMainCheckoutError("Trusted main checkout HEAD differs from the policy SHA")

    # Check object type and tracking before status so a missing/symlinked path
    # is reported as such, not hidden behind Git's generic modified-path state.
    for relative in TRUSTED_PATHS:
        target = root / relative
        if target.is_symlink() or not target.is_file():
            raise TrustedMainCheckoutError("Trusted main authority file is missing or symlinked: " + relative)
        entries = _git(root, "ls-files", "-s", "--", relative).splitlines()
        if len(entries) != 1 or entries[0].split()[0] not in {"100644", "100755"}:
            raise TrustedMainCheckoutError("Trusted main authority file must be one regular tracked file: " + relative)

    # The compact summary is a derived cache and may be regenerated in the
    # runner checkout. The canonical ledger and owner path policy may never
    # have working-tree changes, staged changes or untracked replacements.
    authority_status = _git(
        root, "status", "--porcelain=v1", "--untracked-files=all", "--", LEDGER, POLICY
    )
    if authority_status:
        raise TrustedMainCheckoutError(
            "Trusted main task ledger/path policy has local changes; only the derived summary cache may be regenerated"
        )

    try:
        ledger = json.loads((root / LEDGER).read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
        summary = json.loads((root / SUMMARY).read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TrustedMainCheckoutError("Trusted main task ledger or compact summary is not valid UTF-8 JSON") from exc
    if not isinstance(ledger, dict) or not isinstance(summary, dict):
        raise TrustedMainCheckoutError("Trusted main task ledger and summary must be JSON objects")
    try:
        expected_summary = build_summary(ledger)
    except (KeyError, TypeError, ValueError) as exc:
        raise TrustedMainCheckoutError("Trusted main canonical task ledger cannot produce a compact summary") from exc

    summary_status = _git(
        root, "status", "--porcelain=v1", "--untracked-files=all", "--", SUMMARY
    )
    if summary_status and summary_status.splitlines() != [f" M {SUMMARY}"]:
        raise TrustedMainCheckoutError(
            "Trusted main derived summary has an unexpected staged, added, deleted or renamed state"
        )

    if summary != expected_summary:
        expected_task_ids = [item.get("task_id") for item in expected_summary.get("tasks", [])]
        summary_tasks = summary.get("tasks")
        summary_task_ids = [
            item.get("task_id") for item in summary_tasks if isinstance(item, dict)
        ] if isinstance(summary_tasks, list) else []
        cache_shape_matches = (
            summary.get("schema_version") == 2
            and summary.get("source") == LEDGER
            and isinstance(summary_tasks, list)
            and summary_task_ids == expected_task_ids
            and len(summary_task_ids) == len(summary_tasks)
        )
        if not summary_status or not cache_shape_matches:
            raise TrustedMainCheckoutError(
                "Trusted main compact task summary does not match the committed canonical task ledger"
            )

        temporary = root / (SUMMARY + ".refresh.tmp")
        if temporary.exists() or temporary.is_symlink():
            raise TrustedMainCheckoutError("Trusted main summary refresh temporary file already exists")
        try:
            with temporary.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(expected_summary, indent=2, ensure_ascii=False) + "\\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, root / SUMMARY)
        except OSError as exc:
            temporary.unlink(missing_ok=True)
            raise TrustedMainCheckoutError("Trusted main compact task summary could not be safely regenerated") from exc
        summary = json.loads((root / SUMMARY).read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
        if summary != expected_summary:
            raise TrustedMainCheckoutError("Regenerated trusted main compact summary does not match the canonical ledger")

    return root
