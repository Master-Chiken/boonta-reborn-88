#!/usr/bin/env python3
"""Build a read-only MIPS direct-call graph from a local N64 ROM and symbol map.

Inspired by the call-graph pass in sp00nznet/racer/tools/libultra_identify.py
at 694c5663b3a7c30e2862fc240344f34683f99a9c (MIT); see LICENSE.sp00nznet.

Only static JAL sites are resolved. JALR sites are counted but cannot be
resolved without data-flow or runtime evidence. Static call-site counts are
not execution frequencies. The tool writes nothing.
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

MAX_CALL_SITES_PER_FUNCTION = 1_000_000


def decode_jal_target(word: int, pc: int) -> int:
    """Decode the MIPS J/JAL region using the high nibble of PC + 4."""
    if ((word >> 26) & 0x3F) not in (0x02, 0x03):
        raise ValueError("instruction is not J or JAL")
    return ((pc + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)


def _symbol_index(
    functions: dict[str, FunctionSymbol],
) -> dict[int, list[str]]:
    by_address: dict[int, list[str]] = {}
    for symbol in functions.values():
        by_address.setdefault(symbol.vram, []).append(symbol.name)
    for names in by_address.values():
        names.sort(key=str.casefold)
    return by_address


def build_call_graph(
    rom_data: bytes,
    functions: dict[str, FunctionSymbol],
) -> dict[str, Any]:
    """Return deterministic graph metadata without including raw ROM bytes."""
    by_address = _symbol_index(functions)
    call_sites: list[dict[str, Any]] = []
    indirect_sites: list[dict[str, Any]] = []
    per_function: list[dict[str, Any]] = []
    incoming: dict[int, list[str]] = {}

    for symbol in sorted(functions.values(), key=lambda item: (item.vram, item.name.casefold())):
        start = symbol.rom_offset
        end = start + symbol.size
        if start < 0 or symbol.size <= 0 or symbol.size % 4 or end > len(rom_data):
            raise ValueError(
                f"{symbol.name} has an invalid ROM range "
                f"0x{start:X}..0x{end:X} for input length 0x{len(rom_data):X}"
            )

        direct: list[dict[str, Any]] = []
        indirect: list[int] = []
        for offset in range(0, symbol.size, 4):
            word = int.from_bytes(rom_data[start + offset : start + offset + 4], "big")
            pc = symbol.vram + offset
            opcode = (word >> 26) & 0x3F
            if opcode == 0x03:  # JAL
                target = decode_jal_target(word, pc)
                target_names = by_address.get(target, [])
                site = {
                    "caller": symbol.name,
                    "caller_vram": symbol.vram,
                    "pc": pc,
                    "target_vram": target,
                    "target_names": target_names,
                }
                direct.append(site)
                call_sites.append(site)
                incoming.setdefault(target, []).append(symbol.name)
            elif opcode == 0 and (word & 0x3F) == 0x09:  # JALR
                indirect.append(pc)
                indirect_sites.append(
                    {"caller": symbol.name, "caller_vram": symbol.vram, "pc": pc}
                )
            if len(direct) + len(indirect) > MAX_CALL_SITES_PER_FUNCTION:
                raise ValueError(f"{symbol.name} exceeds the call-site safety limit")

        per_function.append(
            {
                "name": symbol.name,
                "vram": symbol.vram,
                "rom_offset": symbol.rom_offset,
                "size": symbol.size,
                "direct_call_sites": len(direct),
                "unique_direct_targets": len({site["target_vram"] for site in direct}),
                "indirect_call_sites": len(indirect),
                "unresolved_direct_targets": sum(1 for site in direct if not site["target_names"]),
            }
        )

    for sites in incoming.values():
        sites.sort(key=str.casefold)

    resolved_edges = [
        {
            "caller": site["caller"],
            "target": site["target_names"][0],
            "caller_vram": site["caller_vram"],
            "target_vram": site["target_vram"],
            "pc": site["pc"],
        }
        for site in call_sites
        if len(site["target_names"]) == 1
    ]
    unresolved = sorted(
        {
            site["target_vram"]
            for site in call_sites
            if not site["target_names"]
        }
    )
    ambiguous = sorted(
        {
            site["target_vram"]
            for site in call_sites
            if len(site["target_names"]) > 1
        }
    )

    incoming_summary = [
        {
            "target_vram": target,
            "target_names": by_address.get(target, []),
            "static_call_sites": len(sites),
            "callers": sorted(set(sites), key=str.casefold),
        }
        for target, sites in incoming.items()
    ]
    incoming_summary.sort(
        key=lambda item: (-item["static_call_sites"], item["target_vram"])
    )

    return {
        "scope": "static direct-call sites only; not runtime call frequency",
        "function_count": len(per_function),
        "direct_call_site_count": len(call_sites),
        "indirect_call_site_count": len(indirect_sites),
        "resolved_edge_count": len(resolved_edges),
        "unresolved_direct_target_count": len(unresolved),
        "ambiguous_target_count": len(ambiguous),
        "functions": per_function,
        "resolved_edges": sorted(
            resolved_edges,
            key=lambda item: (item["caller_vram"], item["pc"], item["target_vram"]),
        ),
        "direct_call_sites": sorted(
            call_sites,
            key=lambda item: (item["caller_vram"], item["pc"], item["target_vram"]),
        ),
        "incoming_call_sites": incoming_summary,
        "unresolved_target_vrams": [f"0x{address:08X}" for address in unresolved],
        "ambiguous_target_vrams": [f"0x{address:08X}" for address in ambiguous],
        "indirect_call_sites": sorted(
            indirect_sites, key=lambda item: (item["caller_vram"], item["pc"])
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", required=True, type=Path, help="local N64 ROM (z64/v64/n64)")
    parser.add_argument("--symbols", required=True, type=Path, help="local symbols.toml")
    parser.add_argument("--function", help="show one function's direct calls and incoming callers")
    parser.add_argument("--top", type=int, default=25, help="maximum incoming-call summary rows")
    args = parser.parse_args(argv)

    if args.top < 1:
        parser.error("--top must be positive")
    try:
        rom = normalize_n64_rom(args.rom.read_bytes())
        symbols = load_symbol_map(args.symbols)
        graph = build_call_graph(rom, symbols)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.function:
        matching = [
            symbol for symbol in symbols.values()
            if symbol.name.casefold() == args.function.casefold()
            or f"0x{symbol.vram:08X}".casefold() == args.function.casefold()
        ]
        if len(matching) != 1:
            print(f"error: expected one matching function for {args.function!r}", file=sys.stderr)
            return 2
        symbol = matching[0]
        selected = {
            "function": next(item for item in graph["functions"] if item["name"] == symbol.name),
            "outgoing": [
                edge for edge in graph["resolved_edges"] if edge["caller"] == symbol.name
            ],
            "outgoing_unresolved": [
                site for site in graph["direct_call_sites"]
                if site["caller"] == symbol.name and not site["target_names"]
            ],
            "outgoing_ambiguous": [
                site for site in graph["direct_call_sites"]
                if site["caller"] == symbol.name and len(site["target_names"]) > 1
            ],
            "incoming": [
                item for item in graph["incoming_call_sites"]
                if symbol.vram == item["target_vram"]
            ],
            "scope": graph["scope"],
            "global_unresolved_target_vrams": graph["unresolved_target_vrams"],
            "global_ambiguous_target_vrams": graph["ambiguous_target_vrams"],
        }
        print(json.dumps(selected, indent=2))
        return 0

    graph["incoming_call_sites"] = graph["incoming_call_sites"][: args.top]
    print(json.dumps(graph, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
