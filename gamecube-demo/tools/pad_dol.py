#!/usr/bin/env python3
"""Pad GameCube DOL files for 32-byte-aligned section reads used by loaders."""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

DOL_HEADER_SIZE = 0x100


class DolPaddingError(ValueError):
    """Raised when a DOL section table is malformed."""


def _u32_array(data: bytes, start: int, count: int) -> tuple[int, ...]:
    end = start + count * 4
    if end > len(data):
        raise DolPaddingError("DOL header is truncated")
    return struct.unpack(f">{count}I", data[start:end])


def required_file_size(data: bytes) -> int:
    """Return the minimum file length for all 32-byte-rounded DOL sections."""
    if len(data) < DOL_HEADER_SIZE:
        raise DolPaddingError("DOL is shorter than its 0x100-byte header")

    sections: list[tuple[int, int, str, int]] = []
    for kind, offsets, sizes in (
        ("text", _u32_array(data, 0x00, 7), _u32_array(data, 0x90, 7)),
        ("data", _u32_array(data, 0x1C, 11), _u32_array(data, 0xAC, 11)),
    ):
        for index, (offset, size) in enumerate(zip(offsets, sizes)):
            if size == 0:
                continue
            if offset < DOL_HEADER_SIZE:
                raise DolPaddingError(f"{kind}[{index}] starts inside the DOL header")
            raw_end = offset + size
            if raw_end > len(data):
                raise DolPaddingError(f"{kind}[{index}] extends beyond end of file")
            aligned_size = (size + 31) & ~31
            sections.append((offset, offset + aligned_size, kind, index))

    # Dolphin and other loaders may read each section rounded up to 32 bytes.
    # Such a rounded read must not reach into the next section.
    ordered = sorted(sections)
    for current, following in zip(ordered, ordered[1:]):
        if current[1] > following[0]:
            raise DolPaddingError(
                f"{current[2]}[{current[3]}] overlaps {following[2]}[{following[3]}] "
                "after 32-byte alignment"
            )

    return max((end for _, end, _, _ in sections), default=len(data))


def pad_dol_file(path: Path) -> tuple[int, int]:
    """Append zero padding when a section's aligned read would exceed the file."""
    original = path.read_bytes()
    target_size = required_file_size(original)
    if target_size > len(original):
        path.write_bytes(original + bytes(target_size - len(original)))
    return len(original), max(len(original), target_size)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dol", type=Path, help="built GameCube .dol file")
    args = parser.parse_args()
    try:
        before, after = pad_dol_file(args.dol)
    except (OSError, DolPaddingError, struct.error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"DOL section padding OK: {before} -> {after} bytes (+{after - before})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
