#!/usr/bin/env python3
"""Smoke-test pinned decomp-toolkit against a synthetic GameCube DOL only.

The fixture contains no retail game code, symbols, assets, or extracted data.
It validates the DOL reader/info path; it does not establish Racer compatibility.
"""
from __future__ import annotations

import argparse
import struct
import subprocess
import tempfile
from pathlib import Path

DOL_HEADER_SIZE = 0x100
TEXT_FILE_OFFSET = DOL_HEADER_SIZE
TEXT_ADDRESS = 0x80003100
TEXT_SIZE = 0x200
DATA_FILE_OFFSET = TEXT_FILE_OFFSET + TEXT_SIZE
DATA_ADDRESS = 0x80004000
BSS_ADDRESS = 0x80005000
BSS_SIZE = 0x10
ENTRY_POINT = TEXT_ADDRESS

# Mirrors the bounded metadata scan used by decomp-toolkit's DOL reader.
ROM_COPY_INFO_SIZE = (7 + 11 + 1) * 3 * 4
BSS_INIT_INFO_SIZE = (11 + 1) * 2 * 4


def put_be_u32(buffer: bytearray, offset: int, value: int) -> None:
    struct.pack_into(">I", buffer, offset, value)


def make_synthetic_dol() -> bytes:
    """Create a minimal, deterministic DOL with .init, .data and BSS sections."""
    header = bytearray(DOL_HEADER_SIZE)

    # First text section: file offset, runtime address and byte size.
    put_be_u32(header, 0x00, TEXT_FILE_OFFSET)
    put_be_u32(header, 0x48, TEXT_ADDRESS)
    put_be_u32(header, 0x90, TEXT_SIZE)

    # First data section is required by the DOL analyser's normal path.
    put_be_u32(header, 0x1C, DATA_FILE_OFFSET)
    put_be_u32(header, 0x64, DATA_ADDRESS)
    put_be_u32(header, 0xAC, 4)

    # A non-empty BSS range and a valid entry point.
    put_be_u32(header, 0xD8, BSS_ADDRESS)
    put_be_u32(header, 0xDC, BSS_SIZE)
    put_be_u32(header, 0xE0, ENTRY_POINT)

    # Use source-authored PowerPC NOPs and a return instruction as synthetic code.
    text = bytearray(bytes.fromhex("60000000") * (TEXT_SIZE // 4))
    text[0:4] = bytes.fromhex("4e800020")  # blr

    # DOL init metadata: one empty ROM-copy list followed by an empty BSS-init list.
    table_offset = TEXT_SIZE - ROM_COPY_INFO_SIZE - BSS_INIT_INFO_SIZE
    if table_offset < 0 or table_offset + 20 > len(text):
        raise ValueError("Synthetic DOL section is too small for its metadata tables")
    put_be_u32(text, table_offset + 0, TEXT_ADDRESS)
    put_be_u32(text, table_offset + 4, TEXT_ADDRESS)
    put_be_u32(text, table_offset + 8, 0)
    put_be_u32(text, table_offset + 12, BSS_ADDRESS)
    put_be_u32(text, table_offset + 16, 0)

    data = bytes.fromhex("dec0adde")  # synthetic marker only
    return bytes(header) + bytes(text) + data


def run_dtk(dtk: Path, dol_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(dtk), "dol", "info", str(dol_path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dtk", type=Path, help="path to the built dtk executable")
    args = parser.parse_args()

    dtk = args.dtk.resolve()
    if not dtk.is_file():
        parser.error(f"decomp-toolkit executable not found: {dtk}")

    with tempfile.TemporaryDirectory(prefix="boonta-dtk-smoke-") as temp:
        root = Path(temp)
        valid_dol = root / "synthetic-homebrew.dol"
        invalid_dol = root / "invalid-empty-header.dol"
        valid_dol.write_bytes(make_synthetic_dol())
        invalid_dol.write_bytes(bytes(DOL_HEADER_SIZE))

        valid = run_dtk(dtk, valid_dol)
        valid_output = valid.stdout + valid.stderr
        if valid.returncode != 0:
            raise SystemExit(
                "dtk rejected the synthetic DOL (unexpected):\n"
                + valid_output[-8000:]
            )
        for expected in ("Entry point: 0x80003100", "Sections:", ".init"):
            if expected not in valid_output:
                raise SystemExit(
                    f"dtk exited successfully but omitted expected output {expected!r}:\n"
                    + valid_output[-8000:]
                )

        invalid = run_dtk(dtk, invalid_dol)
        if invalid.returncode == 0:
            raise SystemExit("dtk accepted an empty DOL header; malformed-input guard failed")

    print("PASS: pinned decomp-toolkit parsed the synthetic DOL and rejected an empty header.")
    print("Scope: parser/info smoke only; no retail game files or Racer compatibility claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
