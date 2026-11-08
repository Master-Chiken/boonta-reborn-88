#!/usr/bin/env python3
"""Generate a provisional MIPS function-candidate map from a local N64 ROM.

Inspired by sp00nznet/racer/tools/rom_analyzer.py at
694c5663b3a7c30e2862fc240344f34683f99a9c (MIT); see LICENSE.sp00nznet.

Only stack-allocation prologue candidates are detected. The next candidate is
used as a provisional size boundary, which can include gaps/data or split
functions incorrectly. The output is a research aid, not a verified symbol map.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from n64_reference.mips_function_inspector import normalize_n64_rom


class ScanError(ValueError):
    """Raised when the requested scan region cannot be trusted."""


def find_stack_frame_prologues(
    rom: bytes,
    rom_offset: int,
    vram_base: int,
    code_size: int,
) -> list[int]:
    """Return offsets relative to the code section for ADDIU sp,sp,-N candidates."""
    if rom_offset < 0 or code_size <= 0 or code_size % 4:
        raise ScanError("ROM offset must be nonnegative and code size positive/aligned")
    if vram_base < 0 or vram_base % 4 or vram_base + code_size > 0x1_0000_0000:
        raise ScanError("VRAM range must be aligned and fit in 32 bits")
    end = rom_offset + code_size
    if end < rom_offset or end > len(rom):
        raise ScanError(
            f"Requested code range 0x{rom_offset:X}..0x{end:X} "
            f"exceeds ROM length 0x{len(rom):X}"
        )

    candidates: list[int] = []
    for relative in range(0, code_size, 4):
        word = int.from_bytes(rom[rom_offset + relative : rom_offset + relative + 4], "big")
        # addiu $sp, $sp, immediate. A negative signed immediate allocates a frame.
        if (word & 0xFFFF0000) != 0x27BD0000:
            continue
        immediate = word & 0xFFFF
        if immediate < 0x8000:
            continue
        frame_size = 0x10000 - immediate
        # Ignore implausibly tiny/huge frames and retain normal 16-byte stack frames.
        if 16 <= frame_size <= 0x8000 and frame_size % 8 == 0:
            candidates.append(relative)
    return candidates


def build_candidate_symbols_toml(
    offsets: list[int],
    rom_offset: int,
    vram_base: int,
    code_size: int,
) -> str:
    """Render provisional boundaries suitable for the local MIPS inspector."""
    if not offsets:
        raise ScanError("No stack-frame prologue candidates found in the supplied range")
    if offsets != sorted(set(offsets)) or offsets[0] < 0 or offsets[-1] >= code_size:
        raise ScanError("Candidate offsets must be unique, sorted and inside the code range")

    lines = [
        "# PROVISIONAL ONLY: stack-frame prologue scan; verify every boundary manually.",
        "# The next candidate is used as a size boundary and may not be a true function end.",
        "# This file is derived from a local ROM; keep it outside the public repository.",
        "",
        "[[section]]",
        'name = "candidate_code"',
        f"rom = 0x{rom_offset:X}",
        f"vram = 0x{vram_base:08X}",
        f"size = 0x{code_size:X}",
        "",
    ]
    for index, relative in enumerate(offsets):
        next_offset = offsets[index + 1] if index + 1 < len(offsets) else code_size
        size = next_offset - relative
        if size <= 0 or size % 4:
            raise ScanError("Generated candidate function boundary is invalid")
        vram = vram_base + relative
        lines.extend(
            [
                "  [[section.functions]]",
                f'  name = "candidate_{vram:08X}"',
                f"  vram = 0x{vram:08X}",
                f"  size = 0x{size:X}",
                "",
            ]
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", required=True, type=Path, help="local N64 ROM (z64/v64/n64)")
    parser.add_argument("--rom-offset", required=True, type=lambda v: int(v, 0))
    parser.add_argument("--vram-base", required=True, type=lambda v: int(v, 0))
    parser.add_argument("--code-size", required=True, type=lambda v: int(v, 0))
    parser.add_argument("--output", required=True, type=Path, help="local TOML output path")
    args = parser.parse_args(argv)

    try:
        rom = normalize_n64_rom(args.rom.read_bytes())
        offsets = find_stack_frame_prologues(
            rom, args.rom_offset, args.vram_base, args.code_size
        )
        output = build_candidate_symbols_toml(
            offsets, args.rom_offset, args.vram_base, args.code_size
        )
        args.output.write_text(output, encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        f"Wrote {len(offsets)} provisional prologue candidates to {args.output}. "
        "Verify every start/end boundary and symbol identity manually."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
