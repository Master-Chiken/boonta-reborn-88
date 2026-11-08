#!/usr/bin/env python3
"""Extract a checked RAWM chunk for one model from out_modelblock.bin.

Usage:
    python scripts/extract_raw_model.py <out_modelblock.bin> <model_id> <output.bin>
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path


def be32(data: bytes, offset: int) -> int:
    return struct.unpack_from(">I", data, offset)[0]


def extract_model_bytes(data: bytes, model_id: int) -> tuple[bytes, bytes]:
    """Return (mask, model) bytes after validating the block table and ranges."""
    if len(data) < 4:
        raise ValueError("block is shorter than the model-count header")
    count = be32(data, 0)
    if model_id < 0 or model_id >= count:
        raise ValueError(f"model id {model_id} out of range (block has {count} models)")

    # The table has a count, two offsets per model, and a final end offset.
    table_end = 8 * count + 8
    if table_end > len(data):
        raise ValueError(f"truncated offset table: needs {table_end} bytes, file has {len(data)}")

    offset = 8 * model_id + 4
    mask_offset = be32(data, offset)
    model_offset = be32(data, offset + 4)
    next_offset = be32(data, offset + 8)
    if not (table_end <= mask_offset <= model_offset <= next_offset <= len(data)):
        raise ValueError(
            "invalid model offsets: expected offset-table end <= mask <= model <= next <= file size "
            f"(got {table_end}, {mask_offset}, {model_offset}, {next_offset}, {len(data)})"
        )
    if any(value % 4 for value in (mask_offset, model_offset, next_offset)):
        raise ValueError("model offsets are not four-byte aligned")

    mask = data[mask_offset:model_offset]
    model = data[model_offset:next_offset]
    if len(mask) % 4 or len(model) < 4 or len(model) % 4:
        raise ValueError("selected model has malformed mask/model lengths")
    return mask, model


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__)
        return 1

    block_path = Path(sys.argv[1])
    out_path = Path(sys.argv[3])
    try:
        model_id = int(sys.argv[2], 10)
        data = block_path.read_bytes()
        mask, model = extract_model_bytes(data, model_id)
    except (OSError, ValueError, struct.error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        chunk = b"RAWM" + struct.pack("<II", len(mask), len(model)) + mask + model
        out_path.write_bytes(chunk)
    except OSError as exc:
        print(f"error: cannot write {out_path}: {exc}", file=sys.stderr)
        return 2

    kind = "compressed" if model[:4] == b"Comp" else "uncompressed"
    print(f"wrote {out_path}: mask={len(mask)} bytes, model={len(model)} bytes ({kind})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
