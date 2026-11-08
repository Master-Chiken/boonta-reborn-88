#!/usr/bin/env python3
"""Scan printable strings in an explicitly supplied local N64 ROM.

Adapted from the scan/categorization idea in sp00nznet/racer/tools/string_dumper.py
at 694c5663b3a7c30e2862fc240344f34683f99a9c (MIT); see LICENSE.sp00nznet.

Strings are printed only to stdout for local analysis. Do not commit ROM-derived
text, save it in the public repository, or send it to hosted AI tools or issues.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys

from n64_reference.mips_function_inspector import normalize_n64_rom

CATEGORIES = ("all", "debug", "files", "menu", "dialogue", "credits", "game", "other")


@dataclass(frozen=True)
class RomString:
    offset: int
    text: str
    category: str


def categorize_string(text: str) -> str:
    """Assign a broad search category; this is a keyword hint, not semantics."""
    lower = text.casefold()

    if any(word in lower for word in (
        ".c", ".h", ".s", "assert", "error", "warning", "panic", "fault", "debug", "trace"
    )):
        return "debug"
    if any(word in lower for word in (
        "data/", "gfx/", "audio/", "texture", ".bin", ".dat", ".raw", ".pal"
    )):
        return "files"
    if any(word in lower for word in ("~f", "~c", "~s", "~o", "~r", "~n")):
        return "menu"
    if any(word in lower for word in (
        "podracer", "anakin", "sebulba", "watto", "tatooine", "qui-gon", "jedi", "force"
    )):
        return "dialogue"
    if any(word in lower for word in (
        "artist", "programmer", "designer", "producer", "director", "lucasarts", "copyright"
    )):
        return "credits"
    if any(word in lower for word in (
        "race", "track", "vehicle", "engine", "boost", "turbo", "player", "planet",
        "level", "racer", "upgrade", "repair", "lap", "finish", "start"
    )):
        return "game"
    return "other"


def extract_strings(
    rom_data: bytes,
    start_offset: int = 0x1000,
    end_offset: int | None = None,
    min_length: int = 6,
    min_alpha: int = 3,
) -> list[RomString]:
    """Extract printable null-terminated ASCII strings in a bounded byte range."""
    if end_offset is None:
        end_offset = len(rom_data)
    if not (0 <= start_offset <= end_offset <= len(rom_data)):
        raise ValueError("string scan range is outside the supplied ROM")
    if min_length < 1 or min_alpha < 0:
        raise ValueError("min_length must be positive and min_alpha nonnegative")

    result: list[RomString] = []
    cursor = start_offset
    while cursor < end_offset:
        if cursor > start_offset and rom_data[cursor - 1] != 0:
            cursor += 1
            continue
        terminator = rom_data.find(b"\x00", cursor, end_offset)
        if terminator < 0:
            break
        if terminator - cursor >= min_length:
            raw = rom_data[cursor:terminator]
            try:
                text = raw.decode("ascii")
            except UnicodeDecodeError:
                text = ""
            if (
                text
                and text.isprintable()
                and sum(character.isalpha() for character in text) >= min_alpha
            ):
                result.append(
                    RomString(cursor, text, categorize_string(text))
                )
        cursor = terminator + 1
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", required=True, type=Path, help="local N64 ROM (z64/v64/n64)")
    parser.add_argument("--start-offset", type=lambda value: int(value, 0), default=0x1000)
    parser.add_argument("--end-offset", type=lambda value: int(value, 0))
    parser.add_argument("--min-length", type=int, default=6)
    parser.add_argument("--category", choices=CATEGORIES, default="all")
    args = parser.parse_args(argv)

    try:
        rom = normalize_n64_rom(args.rom.read_bytes())
        strings = extract_strings(
            rom, args.start_offset, args.end_offset, args.min_length
        )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    filtered = [item for item in strings if args.category == "all" or item.category == args.category]
    counts = {category: sum(item.category == category for item in strings) for category in CATEGORIES[1:]}
    print(f"strings found: {len(strings)}")
    print("categories: " + ", ".join(f"{key}={value}" for key, value in counts.items()))
    for item in filtered:
        print(f"0x{item.offset:08X} [{item.category}] {item.text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
