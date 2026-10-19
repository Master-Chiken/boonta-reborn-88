#!/usr/bin/env python3
"""Validate basic structural invariants of native GameCube build outputs."""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

DOL_HEADER_SIZE = 0x100
EM_PPC = 20
ET_EXEC = 2


class ArtifactError(ValueError):
    """Raised when an artifact fails a required structural check."""


def u32_array(blob: bytes, start: int, count: int) -> tuple[int, ...]:
    end = start + 4 * count
    if end > len(blob):
        raise ArtifactError("DOL header is truncated")
    return struct.unpack(f">{count}I", blob[start:end])


def validate_dol(path: Path) -> dict[str, int]:
    data = path.read_bytes()
    if len(data) < DOL_HEADER_SIZE:
        raise ArtifactError(f"{path}: DOL is shorter than the 0x100-byte header")

    text_offsets = u32_array(data, 0x00, 7)
    data_offsets = u32_array(data, 0x1C, 11)
    text_addrs = u32_array(data, 0x48, 7)
    data_addrs = u32_array(data, 0x64, 11)
    text_sizes = u32_array(data, 0x90, 7)
    data_sizes = u32_array(data, 0xAC, 11)
    bss_address, bss_size, entry_point = u32_array(data, 0xD8, 3)

    text_sections: list[tuple[int, int, int]] = []
    total_sections = 0
    for section_type, offsets, addresses, sizes in (
        ("text", text_offsets, text_addrs, text_sizes),
        ("data", data_offsets, data_addrs, data_sizes),
    ):
        for index, (offset, address, size) in enumerate(zip(offsets, addresses, sizes)):
            if size == 0:
                if offset != 0:
                    raise ArtifactError(
                        f"{path}: {section_type}[{index}] has an offset but zero size"
                    )
                continue
            if offset < DOL_HEADER_SIZE:
                raise ArtifactError(
                    f"{path}: {section_type}[{index}] begins inside the DOL header"
                )
            if offset + size > len(data):
                raise ArtifactError(
                    f"{path}: {section_type}[{index}] extends beyond end of file"
                )
            # Dolphin's DOL reader rounds section reads up to 32 bytes. A file
            # can have a valid raw section range yet still be rejected at boot
            # if the aligned tail bytes are missing.
            aligned_size = (size + 31) & ~31
            if offset + aligned_size > len(data):
                missing = offset + aligned_size - len(data)
                raise ArtifactError(
                    f"{path}: {section_type}[{index}] lacks {missing} byte(s) "
                    "of trailing 32-byte section padding; run pad_dol.py first"
                )
            if address == 0:
                raise ArtifactError(f"{path}: {section_type}[{index}] has a zero load address")
            total_sections += 1
            if section_type == "text":
                text_sections.append((address, address + size, index))

    if not text_sections:
        raise ArtifactError(f"{path}: no populated text section found")
    if not any(start <= entry_point < end for start, end, _ in text_sections):
        raise ArtifactError(f"{path}: entry point 0x{entry_point:08x} is outside all text sections")

    return {
        "size": len(data),
        "sections": total_sections,
        "text_sections": len(text_sections),
        "entry_point": entry_point,
        "bss_address": bss_address,
        "bss_size": bss_size,
    }


def validate_elf(path: Path) -> dict[str, int]:
    data = path.read_bytes()
    if len(data) < 52 or data[:4] != b"\x7fELF":
        raise ArtifactError(f"{path}: missing or truncated ELF32 header")
    if data[4] != 1:
        raise ArtifactError(f"{path}: expected ELF32 (EI_CLASS=1), got {data[4]}")
    if data[5] != 2:
        raise ArtifactError(f"{path}: expected big-endian ELF (EI_DATA=2), got {data[5]}")

    elf_type, machine = struct.unpack(">HH", data[16:20])
    entry_point = struct.unpack(">I", data[24:28])[0]
    if elf_type != ET_EXEC:
        raise ArtifactError(f"{path}: expected executable ELF (ET_EXEC=2), got {elf_type}")
    if machine != EM_PPC:
        raise ArtifactError(f"{path}: expected PowerPC ELF (EM_PPC=20), got {machine}")
    if entry_point == 0:
        raise ArtifactError(f"{path}: ELF entry point is zero")

    return {"size": len(data), "entry_point": entry_point, "machine": machine}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dol", type=Path, help="built GameCube .dol file")
    parser.add_argument("elf", type=Path, help="built PowerPC .elf file")
    args = parser.parse_args()

    try:
        dol = validate_dol(args.dol)
        elf = validate_elf(args.elf)
    except (OSError, ArtifactError, struct.error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        "DOL OK: "
        f"{dol['size']} bytes, {dol['sections']} loadable sections "
        f"({dol['text_sections']} text), entry=0x{dol['entry_point']:08x}"
    )
    print(
        "ELF OK: "
        f"{elf['size']} bytes, ELF32 big-endian PowerPC, "
        f"entry=0x{elf['entry_point']:08x}"
    )
    print("Artifact structure checks passed; emulator/runtime behavior is not tested here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
