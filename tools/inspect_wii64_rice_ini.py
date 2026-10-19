#!/usr/bin/env python3
"""Inspect Wii64 RiceVideoLinux.ini profiles without rewriting the source file.

Wii64's supplied Rice profile file uses a Japanese Windows/Shift-JIS-compatible
encoding in this archive. The tool defaults to cp932 and preserves unknown keys
and standalone flags as raw lines; it is read-only and never edits the INI.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

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

    def render(self) -> str:
        return "\n".join([self.identifier, *self.lines])


def parse_profiles(text: str) -> list[Profile]:
    """Parse section headers while preserving every profile line verbatim."""
    profiles: list[Profile] = []
    current: Profile | None = None
    for line in text.splitlines():
        match = SECTION_RE.match(line)
        if match:
            current = Profile(identifier=match.group(1))
            profiles.append(current)
        elif current is not None:
            # Keep comments, blank lines, flags without '=', and unknown keys.
            current.lines.append(line)
    return profiles


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ini", type=Path, help="path to RiceVideoLinux.ini")
    parser.add_argument(
        "--encoding", default="cp932",
        help="text encoding (default: cp932; use utf-8 if appropriate)",
    )
    parser.add_argument(
        "--query", default="STAR WARS EP1 RACER",
        help="case-insensitive substring to search in profile names",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="list all profile names and identifiers instead of printing profile bodies",
    )
    args = parser.parse_args(argv)

    try:
        text = args.ini.read_text(encoding=args.encoding)
    except (OSError, UnicodeError) as exc:
        print(f"error: cannot read {args.ini} with encoding {args.encoding}: {exc}", file=sys.stderr)
        return 2

    profiles = parse_profiles(text)
    if args.list:
        for profile in profiles:
            print(f"{profile.identifier}\t{profile.name}")
        return 0

    needle = args.query.casefold()
    matches = [p for p in profiles if needle in p.name.casefold()]
    if not matches:
        print(f"No profile name contains {args.query!r} ({len(profiles)} sections scanned).", file=sys.stderr)
        return 1

    for index, profile in enumerate(matches):
        if index:
            print()
        print(profile.render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
