#!/usr/bin/env python3
"""Summarize local N64 symbol-map coverage to help prioritize manual analysis.

Adapted from the progress-report idea in sp00nznet/racer/tools/progress.py at
694c5663b3a7c30e2862fc240344f34683f99a9c (MIT); see LICENSE.sp00nznet.

A descriptive symbol name is not proof that a function has been understood,
implemented or verified. This report counts names and mapped byte ranges only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

from n64_reference.mips_function_inspector import load_symbol_map

AUTO_NAME = re.compile(
    r"^(?:func_[0-9a-f]{8}|candidate_[0-9a-f]{8}|static_0_[0-9a-f]{8}|"
    r"libultra_split_[0-9a-f]{8})$",
    re.IGNORECASE,
)


def is_automatic_symbol_name(name: str) -> bool:
    return bool(AUTO_NAME.fullmatch(name))


def calculate_progress(symbols: dict[str, Any]) -> dict[str, Any]:
    """Return name/size coverage metrics, not semantic completion metrics."""
    functions = sorted(
        symbols.values(), key=lambda item: (item.vram, item.name.casefold())
    )
    if not functions:
        raise ValueError("symbol map has no functions")

    total_bytes = sum(item.size for item in functions)
    named = [item for item in functions if not is_automatic_symbol_name(item.name)]
    automatic = [item for item in functions if is_automatic_symbol_name(item.name)]
    named_bytes = sum(item.size for item in named)
    size_buckets = {
        "tiny_lt_32": 0,
        "small_32_to_127": 0,
        "medium_128_to_511": 0,
        "large_512_to_2047": 0,
        "huge_ge_2048": 0,
    }
    for item in functions:
        if item.size < 32:
            size_buckets["tiny_lt_32"] += 1
        elif item.size < 128:
            size_buckets["small_32_to_127"] += 1
        elif item.size < 512:
            size_buckets["medium_128_to_511"] += 1
        elif item.size < 2048:
            size_buckets["large_512_to_2047"] += 1
        else:
            size_buckets["huge_ge_2048"] += 1

    largest_automatic = sorted(
        automatic, key=lambda item: (-item.size, item.vram, item.name.casefold())
    )[:20]
    return {
        "scope": "symbol names and mapped byte ranges only; not semantic completion",
        "function_count": len(functions),
        "named_function_count": len(named),
        "automatic_name_count": len(automatic),
        "total_mapped_bytes": total_bytes,
        "named_mapped_bytes": named_bytes,
        "named_byte_ratio": named_bytes / total_bytes if total_bytes else 0.0,
        "size_distribution": size_buckets,
        "largest_automatic_functions": [
            {
                "name": item.name,
                "vram": f"0x{item.vram:08X}",
                "size": item.size,
            }
            for item in largest_automatic
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", required=True, type=Path, help="local symbols.toml")
    parser.add_argument("--top", type=int, default=20, help="largest automatic names to show")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args(argv)
    if not 1 <= args.top <= 20:
        parser.error("--top must be between 1 and 20")

    try:
        report = calculate_progress(load_symbol_map(args.symbols))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    report["largest_automatic_functions"] = report["largest_automatic_functions"][: args.top]
    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print("N64 symbol-map coverage")
    print(report["scope"])
    print(f"Functions: {report['function_count']}")
    print(
        f"Named: {report['named_function_count']} "
        f"({report['named_mapped_bytes']:,} / {report['total_mapped_bytes']:,} mapped bytes)"
    )
    print(f"Automatic names: {report['automatic_name_count']}")
    print(f"Named byte ratio: {report['named_byte_ratio']:.1%}")
    print("Largest automatic-name candidates:")
    for item in report["largest_automatic_functions"]:
        print(f"  {item['name']:32s} {item['size']:7,d} bytes  {item['vram']}")
    print("Reminder: naming does not mean a function's purpose has been verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
