#!/usr/bin/env python3
"""Extract and endian-adapt the pinned N64ModernRuntime scalar RSP DMEM helpers."""

from __future__ import annotations

import argparse
from pathlib import Path


START = "#define RSP_MEM_B(offset, addr) \\\n"
END = "#define RSP_ADD32(a, b) \\\n"

REPLACEMENTS = (
    ("(((offset) + (addr)) ^ 3)", "(((offset) + (addr)) ^ RSP_BYTE_XOR)", 2),
    ("reinterpret_cast<uint8_t*>(&out)[i ^ 3]",
     "reinterpret_cast<uint8_t*>(&out)[i ^ RSP_BYTE_XOR]", 1),
    ("reinterpret_cast<uint8_t*>(&val)[i ^ 3]",
     "reinterpret_cast<uint8_t*>(&val)[i ^ RSP_BYTE_XOR]", 1),
    ("reinterpret_cast<uint8_t*>(&out)[(i + 2) ^ 3]",
     "reinterpret_cast<uint8_t*>(&out)[i ^ (RSP_BYTE_XOR & 1)]", 2),
    ("reinterpret_cast<uint8_t*>(&val)[(i + 2) ^ 3]",
     "reinterpret_cast<uint8_t*>(&val)[(i + 2) ^ RSP_BYTE_XOR]", 1),
)


def extract_and_adapt(source: str) -> str:
    if source.count(START) != 1 or source.count(END) != 1:
        raise SystemExit("Pinned rsp.hpp RSP DMEM helper block did not match exactly once")
    start = source.index(START)
    end = source.index(END, start)
    if end <= start:
        raise SystemExit("Invalid pinned rsp.hpp helper block boundaries")

    block = source[start:end]
    for old, new, expected in REPLACEMENTS:
        count = block.count(old)
        if count != expected:
            raise SystemExit(
                f"Unexpected count for RSP endian expression {old!r}: "
                f"expected {expected}, found {count}"
            )
        block = block.replace(old, new)

    expected_helpers = (
        "RSP_MEM_B", "RSP_MEM_BU", "RSP_MEM_W_LOAD",
        "RSP_MEM_W_STORE", "RSP_MEM_HU_LOAD", "RSP_MEM_H_LOAD",
        "RSP_MEM_H_STORE",
    )
    for helper in expected_helpers:
        if block.count(helper) < 1:
            raise SystemExit(f"Missing pinned RSP helper {helper}")

    return block


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = args.source.read_text(encoding="utf-8")
    block = extract_and_adapt(source)
    result = (
        "#ifndef BOONTA_PINNED_RSP_DMEM_ACCESSORS_HPP\n"
        "#define BOONTA_PINNED_RSP_DMEM_ACCESSORS_HPP\n\n"
        "#include <stdint.h>\n"
        "#define RSP_BYTE_XOR 0\n"
        "extern uint8_t dmem[];\n\n"
        + block
        + "\n#endif\n"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8")
    print(f"Extracted and BE-adapted pinned RSP DMEM helpers to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
