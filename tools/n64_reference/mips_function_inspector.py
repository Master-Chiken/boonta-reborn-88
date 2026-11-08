#!/usr/bin/env python3
"""Read-only MIPS function inspector for a local N64 ROM and TOML symbol map.

Adapted from sp00nznet/racer/tools/func_differ.py at
694c5663b3a7c30e2862fc240344f34683f99a9c (MIT); see LICENSE.sp00nznet.

This intentionally implements only a documented subset of MIPS III. Unknown
instructions remain .word directives; output is a lead for manual review,
not authoritative decompilation. The program never writes ROM-derived data.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import struct
import sys
import tomllib
from typing import Any

REG_NAMES = (
    "zero", "at", "v0", "v1", "a0", "a1", "a2", "a3",
    "t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7",
    "s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7",
    "t8", "t9", "k0", "k1", "gp", "sp", "fp", "ra",
)
N64_Z64_MAGIC = bytes.fromhex("80371240")
N64_V64_MAGIC = bytes.fromhex("37804012")
N64_N64_MAGIC = bytes.fromhex("40123780")
MAX_FUNCTION_BYTES = 1 << 20

OPCODES = {
    0x02: "j", 0x03: "jal", 0x04: "beq", 0x05: "bne",
    0x06: "blez", 0x07: "bgtz", 0x08: "addi", 0x09: "addiu",
    0x0A: "slti", 0x0B: "sltiu", 0x0C: "andi", 0x0D: "ori",
    0x0E: "xori", 0x0F: "lui", 0x14: "beql", 0x15: "bnel",
    0x20: "lb", 0x21: "lh", 0x22: "lwl", 0x23: "lw",
    0x24: "lbu", 0x25: "lhu", 0x26: "lwr", 0x28: "sb",
    0x29: "sh", 0x2A: "swl", 0x2B: "sw", 0x2E: "swr",
    0x31: "lwc1", 0x35: "ldc1", 0x39: "swc1", 0x3D: "sdc1",
}
SPECIAL_FUNCS = {
    0x00: "sll", 0x02: "srl", 0x03: "sra", 0x04: "sllv",
    0x06: "srlv", 0x07: "srav", 0x08: "jr", 0x09: "jalr",
    0x0C: "syscall", 0x0D: "break", 0x10: "mfhi", 0x11: "mthi",
    0x12: "mflo", 0x13: "mtlo", 0x18: "mult", 0x19: "multu",
    0x1A: "div", 0x1B: "divu", 0x20: "add", 0x21: "addu",
    0x22: "sub", 0x23: "subu", 0x24: "and", 0x25: "or",
    0x26: "xor", 0x27: "nor", 0x2A: "slt", 0x2B: "sltu",
}


class SymbolMapError(ValueError):
    """Raised when a symbol map is incomplete or internally inconsistent."""


@dataclass(frozen=True)
class FunctionSymbol:
    name: str
    vram: int
    rom_offset: int
    size: int
    section: str


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SymbolMapError(f"{field} must be an integer")
    return value


def load_symbol_map(path: Path) -> dict[str, FunctionSymbol]:
    """Load section-relative function addresses from a symbols.toml file."""
    try:
        document = tomllib.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SymbolMapError(f"Cannot read symbol map: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise SymbolMapError(f"Invalid TOML symbol map: {exc}") from exc

    sections = document.get("section", [])
    if isinstance(sections, dict):
        sections = [sections]
    if not isinstance(sections, list) or not sections:
        raise SymbolMapError("Symbol map has no [[section]] entries")

    functions: dict[str, FunctionSymbol] = {}
    for section_index, section in enumerate(sections):
        if not isinstance(section, dict):
            raise SymbolMapError(f"section[{section_index}] is not a table")
        section_name = str(section.get("name", f"section-{section_index}"))
        rom_base = _integer(section.get("rom"), f"{section_name}.rom")
        vram_base = _integer(section.get("vram"), f"{section_name}.vram")
        section_size = _integer(section.get("size"), f"{section_name}.size")
        if rom_base < 0 or vram_base < 0 or section_size <= 0:
            raise SymbolMapError(f"{section_name} has an invalid ROM/VRAM range")

        entries = section.get("functions", [])
        if not isinstance(entries, list):
            raise SymbolMapError(f"{section_name}.functions must be an array")
        for entry in entries:
            if not isinstance(entry, dict):
                raise SymbolMapError(f"{section_name} contains a non-table function")
            name = entry.get("name")
            if not isinstance(name, str) or not name.strip():
                raise SymbolMapError(f"{section_name} contains a function without a name")
            vram = _integer(entry.get("vram"), f"{name}.vram")
            size = _integer(entry.get("size"), f"{name}.size")
            relative = vram - vram_base
            if size <= 0 or size > MAX_FUNCTION_BYTES or size % 4:
                raise SymbolMapError(f"{name} has an invalid or unaligned size")
            if vram % 4 or relative < 0 or relative + size > section_size:
                raise SymbolMapError(f"{name} lies outside {section_name} or is unaligned")

            symbol = FunctionSymbol(
                name=name,
                vram=vram,
                rom_offset=rom_base + relative,
                size=size,
                section=section_name,
            )
            key = name.casefold()
            if key in functions:
                raise SymbolMapError(f"Duplicate function name: {name}")
            functions[key] = symbol
    if not functions:
        raise SymbolMapError("Symbol map contains no function entries")
    return functions


def normalize_n64_rom(data: bytes) -> bytes:
    """Return canonical big-endian z64 bytes without modifying the input file."""
    if data.startswith(N64_Z64_MAGIC):
        return data
    if data.startswith(N64_V64_MAGIC):
        if len(data) % 2:
            raise ValueError("v64 ROM length must be even")
        output = bytearray(data)
        for offset in range(0, len(output), 2):
            output[offset], output[offset + 1] = output[offset + 1], output[offset]
        return bytes(output)
    if data.startswith(N64_N64_MAGIC):
        if len(data) % 4:
            raise ValueError("n64 ROM length must be divisible by four")
        output = bytearray(data)
        for offset in range(0, len(output), 4):
            output[offset:offset + 4] = output[offset:offset + 4][::-1]
        return bytes(output)
    raise ValueError(
        "Unrecognised N64 ROM byte order; expected z64, v64 or n64 header "
        "(80371240, 37804012 or 40123780)"
    )


def resolve_function(
    functions: dict[str, FunctionSymbol], query: str
) -> FunctionSymbol:
    """Resolve a case-insensitive name or an exact 0x-prefixed VRAM address."""
    named = functions.get(query.casefold())
    if named:
        return named
    if re.fullmatch(r"0[xX][0-9a-fA-F]{1,8}", query):
        address = int(query, 16)
        matches = [item for item in functions.values() if item.vram == address]
        if len(matches) == 1:
            return matches[0]
    raise KeyError(f"No function named or located at {query!r}")


def disassemble_instruction(word: int, pc: int) -> str:
    """Decode a deliberately bounded set of common MIPS III instructions."""
    if word == 0:
        return "nop"

    op = (word >> 26) & 0x3F
    rs = (word >> 21) & 0x1F
    rt = (word >> 16) & 0x1F
    rd = (word >> 11) & 0x1F
    shift = (word >> 6) & 0x1F
    function = word & 0x3F
    immediate = word & 0xFFFF
    signed_immediate = immediate if immediate < 0x8000 else immediate - 0x10000

    if op == 0:
        name = SPECIAL_FUNCS.get(function)
        if name is None:
            return f".word 0x{word:08X}  # SPECIAL funct=0x{function:02X}"
        if function in (0x00, 0x02, 0x03):
            return f"{name} {REG_NAMES[rd]}, {REG_NAMES[rt]}, {shift}"
        if function in (0x04, 0x06, 0x07):
            return f"{name} {REG_NAMES[rd]}, {REG_NAMES[rt]}, {REG_NAMES[rs]}"
        if function in (0x08, 0x0C, 0x0D):
            return f"{name} {REG_NAMES[rs]}" if function == 0x08 else name
        if function == 0x09:
            return f"jalr {REG_NAMES[rd]}, {REG_NAMES[rs]}"
        if function in (0x10, 0x12):
            return f"{name} {REG_NAMES[rd]}"
        if function in (0x11, 0x13):
            return f"{name} {REG_NAMES[rs]}"
        if function in (0x18, 0x19, 0x1A, 0x1B):
            return f"{name} {REG_NAMES[rs]}, {REG_NAMES[rt]}"
        return f"{name} {REG_NAMES[rd]}, {REG_NAMES[rs]}, {REG_NAMES[rt]}"

    if op in (0x02, 0x03):
        target = ((pc + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)
        return f"{OPCODES[op]} 0x{target:08X}"

    if op in (0x04, 0x05, 0x06, 0x07, 0x14, 0x15):
        target = pc + 4 + (signed_immediate << 2)
        name = OPCODES[op]
        if op in (0x06, 0x07):
            return f"{name} {REG_NAMES[rs]}, 0x{target:08X}"
        return f"{name} {REG_NAMES[rs]}, {REG_NAMES[rt]}, 0x{target:08X}"

    if op == 0x0F:
        return f"lui {REG_NAMES[rt]}, 0x{immediate:04X}"
    if op in (0x08, 0x09, 0x0A, 0x0B):
        name = OPCODES[op]
        return f"{name} {REG_NAMES[rt]}, {REG_NAMES[rs]}, {signed_immediate}"
    if op in (0x0C, 0x0D, 0x0E):
        return f"{OPCODES[op]} {REG_NAMES[rt]}, {REG_NAMES[rs]}, 0x{immediate:04X}"
    if op in (0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26,
              0x28, 0x29, 0x2A, 0x2B, 0x2E):
        return f"{OPCODES[op]} {REG_NAMES[rt]}, {signed_immediate}({REG_NAMES[rs]})"
    if op in (0x31, 0x35, 0x39, 0x3D):
        return f"{OPCODES[op]} f{rt}, {signed_immediate}({REG_NAMES[rs]})"
    return f".word 0x{word:08X}  # opcode=0x{op:02X}"


def render_function(
    rom_data: bytes, symbol: FunctionSymbol, max_instructions: int = 8192
) -> str:
    """Render a function after checking its complete ROM range."""
    if max_instructions <= 0:
        raise ValueError("max_instructions must be positive")
    start = symbol.rom_offset
    end = start + symbol.size
    if start < 0 or end > len(rom_data):
        raise ValueError(
            f"{symbol.name} ROM range 0x{start:X}..0x{end:X} "
            f"exceeds input length 0x{len(rom_data):X}"
        )

    available = symbol.size // 4
    count = min(available, max_instructions)
    lines = [
        f"Function: {symbol.name}",
        f"Section: {symbol.section}",
        f"VRAM: 0x{symbol.vram:08X}  ROM: 0x{symbol.rom_offset:X}",
        f"Size: {symbol.size} bytes ({available} instructions)",
        "Decoder: partial MIPS III subset; unknown words are left raw.",
        "",
    ]
    for index in range(count):
        offset = start + index * 4
        word = struct.unpack_from(">I", rom_data, offset)[0]
        pc = symbol.vram + index * 4
        lines.append(
            f"{pc:08X}: {word:08X}  {disassemble_instruction(word, pc)}"
        )
    if count < available:
        lines.extend(("", f"... truncated after {count} of {available} instructions"))
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("function", help="function name or 0x-prefixed VRAM address")
    parser.add_argument("--rom", required=True, type=Path, help="local N64 ROM (z64/v64/n64)")
    parser.add_argument("--symbols", required=True, type=Path, help="local symbols.toml")
    parser.add_argument("--max-instructions", type=int, default=8192)
    args = parser.parse_args(argv)

    try:
        functions = load_symbol_map(args.symbols)
        symbol = resolve_function(functions, args.function)
        raw_rom = args.rom.read_bytes()
        rom = normalize_n64_rom(raw_rom)
        output = render_function(rom, symbol, args.max_instructions)
    except (OSError, ValueError, KeyError, SymbolMapError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
