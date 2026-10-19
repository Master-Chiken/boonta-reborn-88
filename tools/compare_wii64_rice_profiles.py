#!/usr/bin/env python3
"""Compare two named profiles in Wii64's RiceVideoLinux.ini.

Read-only: this tool reports differences and never rewrites emulator settings.
It deliberately compares literal values/flags without claiming to interpret them.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from inspect_wii64_rice_ini import Profile, parse_profiles


def settings(profile: Profile) -> dict[str, list[str]]:
    """Group raw setting values by key; preserve flags as standalone entries."""
    result: dict[str, list[str]] = {}
    for raw in profile.lines:
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        key, sep, value = line.partition("=")
        if sep:
            result.setdefault(key.strip(), []).append(value.strip())
        else:
            result.setdefault(f"[flag] {line}", []).append("")
    return result


def find_profile(profiles: list[Profile], query: str) -> Profile | None:
    """Resolve one profile name; return None when missing or ambiguous."""
    folded_query = query.casefold()
    exact = [p for p in profiles if p.name.casefold() == folded_query]
    if exact:
        return exact[0] if len(exact) == 1 else None
    partial = [p for p in profiles if folded_query in p.name.casefold()]
    return partial[0] if len(partial) == 1 else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ini", type=Path, help="path to RiceVideoLinux.ini")
    parser.add_argument("profile_a", help="first profile name (exact or unique substring)")
    parser.add_argument("profile_b", help="second profile name (exact or unique substring)")
    parser.add_argument("--encoding", default="cp932")
    args = parser.parse_args(argv)

    try:
        text = args.ini.read_text(encoding=args.encoding)
    except (OSError, UnicodeError) as exc:
        print(f"error: cannot read {args.ini}: {exc}", file=sys.stderr)
        return 2

    profiles = parse_profiles(text)
    a = find_profile(profiles, args.profile_a)
    b = find_profile(profiles, args.profile_b)
    if a is None:
        print(f"Profile A not found or ambiguous: {args.profile_a!r}", file=sys.stderr)
        return 1
    if b is None:
        print(f"Profile B not found or ambiguous: {args.profile_b!r}", file=sys.stderr)
        return 1

    sa, sb = settings(a), settings(b)
    print(f"A: {a.name} {a.identifier}")
    print(f"B: {b.name} {b.identifier}")
    keys = sorted(set(sa) | set(sb), key=str.casefold)
    differences = 0
    for key in keys:
        av, bv = sa.get(key), sb.get(key)
        if av != bv:
            differences += 1
            print(f"\n{key}")
            print(f"  A: {', '.join(av) if av is not None else '(absent)'}")
            print(f"  B: {', '.join(bv) if bv is not None else '(absent)'}")
    print(f"\n{differences} differing setting/flag keys")
    print("Note: this is a literal comparison; it does not interpret plugin semantics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
