#!/usr/bin/env python3
"""Emit a GitHub Actions output deciding whether a PR needs GameCube CI.

Input is JSON written by:
  gh api --paginate --slurp repos/OWNER/REPO/pulls/NUMBER/files?per_page=100

A malformed response fails the step, so a required detector check blocks the PR.
An empty file list or the GitHub 3,000-file API cap fails conservatively toward
running GameCube CI. This is a CI selector, not a provenance or security guard.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

MAX_PR_FILE_RECORDS = 3000

EXACT_PATHS = {
    "gamecube-demo/Makefile",
    ".github/workflows/gamecube-demo-build.yml",
}
DIRECTORY_PREFIXES = (
    "gamecube-demo/source/",
    "gamecube-demo/tests/",
    "gamecube-demo/include/",
    "gamecube-demo/data/",
    "gamecube-demo/tools/",
    "tools/mesh_format/",
    "tools/track_format/",
    "tests/",
)


def flatten_file_records(payload: object) -> list[dict[str, Any]]:
    """Validate and flatten the nested JSON arrays returned by --paginate --slurp."""
    if not isinstance(payload, list):
        raise ValueError("expected a JSON array from GitHub's pull-request files API")

    records: list[dict[str, Any]] = []

    def visit(node: object) -> None:
        if isinstance(node, list):
            for item in node:
                visit(item)
            return
        if not isinstance(node, dict):
            raise ValueError("unexpected item in GitHub pull-request files payload")
        filename = node.get("filename")
        if not isinstance(filename, str) or not filename:
            raise ValueError("GitHub pull-request file record is missing a valid filename")
        previous = node.get("previous_filename")
        if previous is not None and (not isinstance(previous, str) or not previous):
            raise ValueError("GitHub pull-request file record has an invalid previous_filename")
        records.append(node)

    visit(payload)
    return records


def requires_gamecube_ci(payload: object) -> tuple[bool, list[str], int]:
    """Return (required, matching paths, record count), failing safe on empty/capped results."""
    records = flatten_file_records(payload)
    candidate_paths = {
        path
        for record in records
        for path in (record.get("filename"), record.get("previous_filename"))
        if isinstance(path, str)
    }
    matching = sorted(
        path
        for path in candidate_paths
        if path in EXACT_PATHS or path.startswith(DIRECTORY_PREFIXES)
    )
    # Empty results are unexpected for a real PR. Treat them as relevant rather
    # than allowing a required GameCube check to be skipped on missing metadata.
    # GitHub's files endpoint has a 3,000-file cap; at that boundary, the full
    # list may be truncated, so conservatively run the GameCube jobs.
    relevant = not records or len(records) >= MAX_PR_FILE_RECORDS or bool(matching)
    return relevant, matching, len(records)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1:
        print(f"usage: {Path(sys.argv[0]).name} FILES_JSON", file=sys.stderr)
        return 2

    try:
        payload = json.loads(Path(args[0]).read_text(encoding="utf-8"))
        relevant, matching, count = requires_gamecube_ci(payload)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"GameCube change detector failed closed: {exc}", file=sys.stderr)
        return 2

    print(f"Changed-file records read: {count}", file=sys.stderr)
    print(f"GameCube-relevant paths: {matching[:80]}", file=sys.stderr)
    print(f"GameCube CI required for this PR: {str(relevant).lower()}", file=sys.stderr)
    # stdout is redirected to GITHUB_OUTPUT by the workflow; keep it output-only.
    print(f"gamecube={'true' if relevant else 'false'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
