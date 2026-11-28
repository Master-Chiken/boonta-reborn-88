#!/usr/bin/env python3
"""Extract the exact pinned N64ModernRuntime RSP::r128 union for a PPC probe."""

from __future__ import annotations

import argparse
from pathlib import Path


def extract_union(source: str) -> str:
    anchor = "    union r128 {"
    if source.count(anchor) != 1:
        raise SystemExit("Expected exactly one RSP::r128 union in pinned rsp_vu.hpp")

    start = source.index(anchor) + len("    ")
    brace = source.index("{", start)
    depth = 0
    end = None
    for offset in range(brace, len(source)):
        char = source[offset]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = offset + 1
                break

    if end is None or source[end:].lstrip()[:1] != ";":
        raise SystemExit("Could not find the closing '};' for RSP::r128")

    block = source[start:end + 1]  # include the union's terminating semicolon

    # The pinned desktop runtime reverses byte/halfword indices for LE hosts.
    # Wii/GameCube PPC are BE, so adapt this ephemeral copy to native lane order.
    lane_adapters = (
        ("((uint8_t*)&u128)[15 - index]", "((rsp_u8_alias*)&u128)[index]", 4),
        ("((uint16_t*)&u128)[7 - index]", "((rsp_u16_alias*)&u128)[index]", 4),
        ("((int16_t*)&u128)[7 - index]", "((rsp_s16_alias*)&u128)[index]", 2),
    )
    for old, new, expected in lane_adapters:
        count = block.count(old)
        if count != expected:
            raise SystemExit(
                f"Pinned RSP::r128 lane expression {old!r} changed: "
                f"expected {expected}, found {count}"
            )
        block = block.replace(old, new)

    required = {
        "byte": 2,
        "element": 2,
        "u8": 2,
        "s16": 2,
        "u16": 2,
    }
    for method, count in required.items():
        needle = f"auto {method}(u32 index)"
        if block.count(needle) != count:
            raise SystemExit(
                f"Pinned RSP::r128 accessor {method} changed: "
                f"expected {count} overloads, found {block.count(needle)}"
            )

    return block


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = args.source.read_text(encoding="utf-8")
    union = extract_union(source)
    result = (
        "#ifndef BOONTA_PINNED_RSP_R128_ACCESSOR_HPP\n"
        "#define BOONTA_PINNED_RSP_R128_ACCESSOR_HPP\n\n"
        "#include <stdint.h>\n"
        "using u32 = uint32_t;\n"
        "#if defined(__GNUC__)\n"
        "typedef uint8_t rsp_u8_alias __attribute__((may_alias));\n"
        "typedef uint16_t rsp_u16_alias __attribute__((may_alias));\n"
        "typedef int16_t rsp_s16_alias __attribute__((may_alias));\n"
        "#else\n"
        "typedef uint8_t rsp_u8_alias;\n"
        "typedef uint16_t rsp_u16_alias;\n"
        "typedef int16_t rsp_s16_alias;\n"
        "#endif\n"
        "struct RSP {\n"
        f"{union}\n"
        "};\n\n"
        "#endif\n"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8")
    print(f"Extracted exact pinned RSP::r128 union to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
