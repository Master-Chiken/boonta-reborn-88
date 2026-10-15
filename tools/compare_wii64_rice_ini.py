#!/usr/bin/env python3
"""Compare two Wii64 RiceVideoLinux.ini files without changing either file.

Sections are matched by their brace-delimited identifier. Values and standalone
flags are compared as text: this tool deliberately does not guess what a plugin
setting means or whether one value is better.
"""
from __future__ import annotations

import argparse
import difflib
import sys
from dataclasses import dataclass, field
from pathlib import Path
import re

SECTION_RE = re.compile(r"^\s*(\{[^}]+\})\s*$")


@dataclass
class Profile:
    identifier: str
    lines: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        for line in self.lines:
            key, sep, value = line.partition("=")
            if sep and key.strip().casefold() == "name":
                return value.strip()
        return "(unnamed profile)"


def parse_profiles(text: str) -> dict[str, Profile]:
    profiles: dict[str, Profile] = {}
    current: Profile | None = None
    for line in text.splitlines():
        match = SECTION_RE.match(line)
        if match:
            current = Profile(match.group(1))
            if current.identifier in profiles:
                raise ValueError(f"duplicate profile identifier: {current.identifier}")
            profiles[current.identifier] = current
        elif current is not None:
            # Keep unknown keys, flag-only lines, comments and blank lines.
            current.lines.append(line)
    return profiles


def load(path: Path, encoding: str) -> dict[str, Profile]:
    return parse_profiles(path.read_text(encoding=encoding))


def describe(profile: Profile) -> str:
    return f"{profile.name} [{profile.identifier}]"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path, help="original RiceVideoLinux.ini")
    parser.add_argument("after", type=Path, help="comparison RiceVideoLinux.ini")
    parser.add_argument("--encoding", default="cp932", help="text encoding (default: cp932)")
    parser.add_argument("--query", default="", help="only compare profiles whose name contains this text")
    parser.add_argument("--show-unchanged", action="store_true", help="also print unchanged profiles")
    args = parser.parse_args(argv)

    try:
        before = load(args.before, args.encoding)
        after = load(args.after, args.encoding)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    needle = args.query.casefold()
    before = {k: v for k, v in before.items() if needle in v.name.casefold()}
    after = {k: v for k, v in after.items() if needle in v.name.casefold()}

    added = sorted(after.keys() - before.keys())
    removed = sorted(before.keys() - after.keys())
    shared = sorted(before.keys() & after.keys())
    changed = [key for key in shared if before[key].lines != after[key].lines]
    unchanged = [key for key in shared if before[key].lines == after[key].lines]

    print(f"Profiles: before={len(before)} after={len(after)}")
    print(f"Added: {len(added)} | removed: {len(removed)} | changed: {len(changed)} | unchanged: {len(unchanged)}")

    for key in added:
        print(f"\n+++ ADDED {describe(after[key])}")
        for line in after[key].lines:
            print(f"+ {line}")
    for key in removed:
        print(f"\n--- REMOVED {describe(before[key])}")
        for line in before[key].lines:
            print(f"- {line}")
    for key in changed:
        old, new = before[key], after[key]
        print(f"\n*** CHANGED {describe(new)}")
        diff = difflib.unified_diff(old.lines, new.lines, fromfile="before", tofile="after", lineterm="")
        for line in diff:
            print(line)
    if args.show_unchanged:
        for key in unchanged:
            print(f"= UNCHANGED {describe(after[key])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
