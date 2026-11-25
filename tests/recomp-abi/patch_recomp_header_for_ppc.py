#!/usr/bin/env python3
"""Apply the clean-room PPC wide-multiply fallback to a pinned upstream header."""

from __future__ import annotations

import argparse
from pathlib import Path

START = "// Implementation of 64-bit multiply and divide instructions\n"
END = "\nstatic inline void DDIV(int64_t"
REPLACEMENT = (
    START
    + '#include "ppc_int128_compat.h"\n'
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("header", type=Path)
    args = parser.parse_args()

    source = args.header.read_text(encoding="utf-8")
    if source.count(START) != 1 or source.count(END) != 1:
        raise SystemExit("Pinned N64Recomp header layout did not match the expected patch anchors.")

    start = source.index(START)
    end = source.index(END, start)
    if end <= start:
        raise SystemExit("Invalid N64Recomp multiply-helper block boundaries.")

    patched = source[:start] + REPLACEMENT + source[end + 1:]
    if patched == source or "128-bit integer type not found" in patched:
        raise SystemExit("PPC multiply fallback patch was not applied cleanly.")

    args.header.write_text(patched, encoding="utf-8")
    print("Applied the local 64-bit multiply fallback to the pinned header only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
