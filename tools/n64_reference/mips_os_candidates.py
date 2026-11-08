#!/usr/bin/env python3
"""Report MIPS/N64 OS and hardware signature hints from local function symbols.

Inspired by the pattern-analysis passes in sp00nznet/racer/tools/libultra_identify.py
at 694c5663b3a7c30e2862fc240344f34683f99a9c (MIT); see LICENSE.sp00nznet.

The report preserves instruction evidence and deliberately does not rename
functions. COP0, MMIO and floating-point patterns are candidates for manual
verification, not proof that a function implements a particular libultra API.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from n64_reference.mips_function_inspector import (
    FunctionSymbol,
    load_symbol_map,
    normalize_n64_rom,
)

MMIO_HIGH_HALVES = {
    0xA404: "SP",
    0xA410: "DP",
    0xA430: "MI",
    0xA440: "VI",
    0xA450: "AI",
    0xA460: "PI",
    0xA480: "SI",
}


def analyze_function(rom_data: bytes, symbol: FunctionSymbol) -> dict[str, Any]:
    """Collect observable instruction features for one declared function."""
    start = symbol.rom_offset
    end = start + symbol.size
    if start < 0 or symbol.size <= 0 or symbol.size % 4 or end > len(rom_data):
        raise ValueError(
            f"{symbol.name} has an invalid ROM range "
            f"0x{start:X}..0x{end:X} for input length 0x{len(rom_data):X}"
        )

    mfc0: dict[int, int] = {}
    mtc0: dict[int, int] = {}
    cfc1 = 0
    ctc1 = 0
    cop1 = 0
    fp_loads = 0
    fp_stores = 0
    mmio_sites: list[dict[str, Any]] = []
    frame_size = None
    jr_ra_sites: list[int] = []

    for offset in range(0, symbol.size, 4):
        word = int.from_bytes(rom_data[start + offset : start + offset + 4], "big")
        pc = symbol.vram + offset
        opcode = (word >> 26) & 0x3F
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F

        if offset == 0 and opcode == 0x09 and rs == 29 and rt == 29:
            immediate = word & 0xFFFF
            signed = immediate if immediate < 0x8000 else immediate - 0x10000
            if signed < 0:
                frame_size = -signed

        if opcode == 0x10:  # COP0 transfers
            if rs == 0:
                mfc0[rd] = mfc0.get(rd, 0) + 1
            elif rs == 4:
                mtc0[rd] = mtc0.get(rd, 0) + 1

        if opcode == 0x11:  # COP1 operation/control transfer
            cop1 += 1
            if rs == 2:  # CFC1
                cfc1 += 1
            elif rs == 6:  # CTC1
                ctc1 += 1

        if opcode in (0x31, 0x35):
            fp_loads += 1
        elif opcode in (0x39, 0x3D):
            fp_stores += 1

        if opcode == 0x0F:
            high = word & 0xFFFF
            if high in MMIO_HIGH_HALVES:
                mmio_sites.append(
                    {"pc": pc, "register": rt, "high_half": f"0x{high:04X}",
                     "hardware_candidate": MMIO_HIGH_HALVES[high]}
                )

        if word == 0x03E00008:  # jr ra
            jr_ra_sites.append(pc)

    tags: list[str] = []
    if mfc0.get(9):
        tags.append("COP0_COUNT_READ")
    if mfc0.get(12):
        tags.append("COP0_STATUS_READ")
    if mtc0.get(12):
        tags.append("COP0_STATUS_WRITE")
    if mfc0.get(13):
        tags.append("COP0_CAUSE_READ")
    if cfc1:
        tags.append("COP1_CONTROL_READ")
    if ctc1:
        tags.append("COP1_CONTROL_WRITE")
    if mmio_sites:
        tags.append("N64_MMIO_BASE_CANDIDATE")
    if fp_loads or fp_stores or cop1:
        tags.append("FLOATING_POINT_ACTIVITY")

    return {
        "name": symbol.name,
        "vram": f"0x{symbol.vram:08X}",
        "rom_offset": f"0x{symbol.rom_offset:X}",
        "size_bytes": symbol.size,
        "instruction_count": symbol.size // 4,
        "stack_frame_bytes_candidate": frame_size,
        "cop0_mfc0_register_counts": {str(key): value for key, value in sorted(mfc0.items())},
        "cop0_mtc0_register_counts": {str(key): value for key, value in sorted(mtc0.items())},
        "cop1_instructions": cop1,
        "cop1_control_reads": cfc1,
        "cop1_control_writes": ctc1,
        "floating_point_loads": fp_loads,
        "floating_point_stores": fp_stores,
        "mmio_lui_candidates": mmio_sites,
        "jr_ra_return_sites": [f"0x{pc:08X}" for pc in jr_ra_sites],
        "evidence_tags": tags,
        "interpretation": (
            "evidence hints only; verify full data flow, callers/callees and exact ROM revision"
        ),
    }


def analyze_symbols(
    rom_data: bytes,
    functions: dict[str, FunctionSymbol],
) -> list[dict[str, Any]]:
    return [
        analyze_function(rom_data, symbol)
        for symbol in sorted(functions.values(), key=lambda item: (item.vram, item.name.casefold()))
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", required=True, type=Path, help="local N64 ROM (z64/v64/n64)")
    parser.add_argument("--symbols", required=True, type=Path, help="local symbols.toml")
    parser.add_argument("--function", help="optional function name or 0x-prefixed VRAM")
    args = parser.parse_args(argv)

    try:
        rom = normalize_n64_rom(args.rom.read_bytes())
        symbols = load_symbol_map(args.symbols)
        if args.function:
            matches = [
                item for item in symbols.values()
                if item.name.casefold() == args.function.casefold()
                or f"0x{item.vram:08X}".casefold() == args.function.casefold()
            ]
            if len(matches) != 1:
                raise ValueError(f"expected one matching function for {args.function!r}")
            results = [analyze_function(rom, matches[0])]
        else:
            results = analyze_symbols(rom, symbols)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
