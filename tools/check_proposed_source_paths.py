#!/usr/bin/env python3
"""Check proposed GitHub PR file paths using the trusted base branch policy.

The workflow feeds this tool GitHub API file metadata. It deliberately never
checks out, imports, or executes code from the pull request being inspected.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import sys

import check_source_import_policy as policy


def proposed_filenames(payload: object) -> list[str]:
    """Flatten gh api --paginate --slurp responses and validate every filename."""
    filenames: list[str] = []

    def visit(node: object) -> None:
        if isinstance(node, list):
            for item in node:
                visit(item)
            return
        if not isinstance(node, dict):
            raise ValueError("Unexpected GitHub files API payload shape")

        filename = node.get("filename")
        if not isinstance(filename, str) or not filename:
            raise ValueError("GitHub files API entry is missing a filename")
        normalized = filename.replace("\\", "/")
        parsed = PurePosixPath(normalized)
        if (
            parsed.is_absolute()
            or not parsed.parts
            or normalized != parsed.as_posix()
            or any(part in ("", ".", "..") for part in parsed.parts)
        ):
            raise ValueError(f"Unsafe path in GitHub files API response: {filename!r}")
        filenames.append(normalized)

    if not isinstance(payload, list):
        raise ValueError("Expected a JSON array from GitHub's files API")
    visit(payload)
    if not filenames:
        raise ValueError("GitHub files API returned no filenames; refusing to pass empty input")
    return sorted(set(filenames))


def blocked_filenames(payload: object) -> list[str]:
    """Return all held/excluded paths from the proposed change list."""
    return [name for name in proposed_filenames(payload) if policy.excluded(name)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files_json", type=Path, help="JSON from gh api --paginate --slurp pulls/N/files")
    args = parser.parse_args(argv)

    try:
        payload = json.loads(args.files_json.read_text(encoding="utf-8"))
        filenames = proposed_filenames(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Trusted source-import path guard could not validate input: {exc}", file=sys.stderr)
        return 2

    offenders = [name for name in filenames if policy.excluded(name)]
    if offenders:
        print("Trusted source-import path guard failed. These proposed paths are held for provenance review:")
        for name in offenders:
            print(f" - {name}")
        return 1

    print(f"Trusted source-import path guard passed: checked {len(filenames)} proposed path(s).")
    print("This path check does not prove authorship, license, or redistribution permission.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
