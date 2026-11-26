#!/usr/bin/env python3
"""Patch a pinned N64Recomp header for a bounded, local PowerPC compile probe."""

from __future__ import annotations

import argparse
from pathlib import Path

START = "// Implementation of 64-bit multiply and divide instructions\n"
END = "\nstatic inline void DDIV(int64_t"
MEMORY_ANCHOR = "#define MEM_W(offset, reg) \\\n"
BYTE_LANE_EXPRESSION = "(((reg) + (offset)) ^ 3)"
HALF_LANE_EXPRESSION = "(((reg) + (offset)) ^ 2)"
FPR_LITTLE_ENDIAN_LAYOUT = """    struct {
        float fl;
        float fh;
    };
    struct {
        uint32_t u32l;
        uint32_t u32h;
    };"""
FPR_BIG_ENDIAN_LAYOUT = """#if defined(__BYTE_ORDER__) && (__BYTE_ORDER__ == __ORDER_BIG_ENDIAN__)
    /* The high half of each 64-bit FPR occupies the first bytes on BE hosts. */
    struct {
        float fh;
        float fl;
    };
    struct {
        uint32_t u32h;
        uint32_t u32l;
    };
#else
    struct {
        float fl;
        float fh;
    };
    struct {
        uint32_t u32l;
        uint32_t u32h;
    };
#endif"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("header", type=Path)
    args = parser.parse_args()

    source = args.header.read_text(encoding="utf-8")
    if source.count(START) != 1 or source.count(END) != 1:
        raise SystemExit("Pinned N64Recomp multiply-helper block did not match the expected anchors.")

    start = source.index(START)
    end = source.index(END, start)
    if end <= start:
        raise SystemExit("Invalid N64Recomp multiply-helper block boundaries.")

    patched = source[:start] + START + '#include "ppc_int128_compat.h"\n' + source[end + 1:]
    if patched == source or "128-bit integer type not found" in patched:
        raise SystemExit("PPC multiply fallback patch was not applied cleanly.")

    if patched.count(MEMORY_ANCHOR) != 1:
        raise SystemExit("Pinned N64Recomp MEM_W insertion point did not match exactly once.")

    if patched.count(FPR_LITTLE_ENDIAN_LAYOUT) != 1:
        raise SystemExit("Pinned N64Recomp FPR union layout did not match exactly once.")
    patched = patched.replace(
        FPR_LITTLE_ENDIAN_LAYOUT,
        FPR_BIG_ENDIAN_LAYOUT,
        1,
    )

    if patched.count(BYTE_LANE_EXPRESSION) != 2:
        raise SystemExit("Expected exactly two little-endian byte-lane expressions (MEM_B and MEM_BU).")
    if patched.count(HALF_LANE_EXPRESSION) != 2:
        raise SystemExit("Expected exactly two little-endian halfword-lane expressions (MEM_H and MEM_HU).")

    patched = patched.replace(
        MEMORY_ANCHOR,
        '#include "ppc_memory_lane_compat.h"\n' + MEMORY_ANCHOR,
        1,
    )
    patched = patched.replace(
        BYTE_LANE_EXPRESSION,
        "RECOMP_MEM_BYTE_LANE(((reg) + (offset)))",
    )
    patched = patched.replace(
        HALF_LANE_EXPRESSION,
        "RECOMP_MEM_HALF_LANE(((reg) + (offset)))",
    )

    if patched.count("RECOMP_MEM_BYTE_LANE(((reg) + (offset)))") != 2:
        raise SystemExit("Failed to adapt both byte-access macros.")
    if patched.count("RECOMP_MEM_HALF_LANE(((reg) + (offset)))") != 2:
        raise SystemExit("Failed to adapt both halfword-access macros.")

    args.header.write_text(patched, encoding="utf-8")
    print("Applied the local 64-bit multiply fallback and target-endian lane adapter to the pinned header only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
