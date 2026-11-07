#!/usr/bin/env python3
"""Carve a checked asset out of a packed block into a discrete replacement file.

Usage:
    python scripts/extract_raw_asset.py model   <out_modelblock.bin>   <id> <out.bin>
    python scripts/extract_raw_asset.py spline  <out_splineblock.bin>  <id> <out.bin>
    python scripts/extract_raw_asset.py texture <out_textureblock.bin> <id> <out.bin>
    python scripts/extract_raw_asset.py verify <kind> <block.bin>

Sizes in discrete files are little-endian; packed-block offsets and payloads are big-endian.
"""
from __future__ import annotations
import argparse
import struct
import sys
from pathlib import Path

MAGIC = {"model": b"RAWM", "spline": b"RAWS", "texture": b"RAWT"}


def be32(data: bytes, off: int) -> int:
    if off < 0 or off + 4 > len(data):
        raise ValueError(f"32-bit field at offset {off} lies outside the {len(data)}-byte block")
    return struct.unpack_from(">I", data, off)[0]


def entry_count(data: bytes) -> int:
    return be32(data, 0)


def _entry_range(kind: str, data: bytes, asset_id: int) -> tuple[int, int, tuple[int, ...]]:
    if kind not in MAGIC:
        raise ValueError(f"unknown asset kind {kind!r}")
    count = entry_count(data)
    if not (0 <= asset_id < count):
        raise ValueError(f"{kind} id {asset_id} out of range (block has {count} entries)")

    if kind == "model":
        table_end = 8 * count + 8
        if table_end > len(data):
            raise ValueError(f"truncated model offset table (needs {table_end} bytes)")
        mask_off = be32(data, 8 * asset_id + 4)
        model_off = be32(data, 8 * asset_id + 8)
        end = be32(data, 8 * asset_id + 12)
        if not (table_end <= mask_off <= model_off <= end <= len(data)):
            raise ValueError(f"invalid model offsets for id {asset_id}: {mask_off}, {model_off}, {end}")
        if any(v % 4 for v in (mask_off, model_off, end)):
            raise ValueError("model offsets are not four-byte aligned")
        return mask_off, end, (mask_off, model_off, end)

    if kind == "spline":
        table_end = 4 * (count + 2)
        if table_end > len(data):
            raise ValueError(f"truncated spline offset table (needs {table_end} bytes)")
        begin = be32(data, 4 * (asset_id + 1))
        end = be32(data, 4 * (asset_id + 2))
        if not (table_end <= begin <= end <= len(data)):
            raise ValueError(f"invalid spline offsets for id {asset_id}: {begin}, {end}")
        if begin % 4 or end % 4:
            raise ValueError("spline offsets are not four-byte aligned")
        return begin, end, (begin, end)

    table_end = 4 + 8 * count
    if table_end > len(data):
        raise ValueError(f"truncated texture offset table (needs {table_end} bytes)")
    pixels_off = be32(data, 8 * asset_id + 4)
    palette_off = be32(data, 8 * asset_id + 8)
    end = be32(data, 8 * (asset_id + 1) + 4) if asset_id + 1 < count else len(data)
    if not (table_end <= pixels_off <= end <= len(data)):
        raise ValueError(f"invalid texture offsets for id {asset_id}: {pixels_off}, {palette_off}, {end}")
    if palette_off != 0 and not (pixels_off <= palette_off <= end):
        raise ValueError(f"invalid palette offset {palette_off} for texture {asset_id}")
    if pixels_off % 4 or end % 4 or (palette_off and palette_off % 4):
        raise ValueError("texture offsets are not four-byte aligned")
    return pixels_off, end, (pixels_off, palette_off, end)


def carve(kind: str, data: bytes, asset_id: int) -> bytes:
    """Return the discrete-file bytes for one entry of a packed block."""
    begin, end, offsets = _entry_range(kind, data, asset_id)
    payload = data[begin:end]

    if kind == "model":
        _, model_off, _ = offsets
        mask = data[begin:model_off]
        model = data[model_off:end]
        if not payload or len(mask) % 4 or len(model) < 4 or len(model) % 4:
            raise ValueError(f"model entry {asset_id} has invalid mask/model sizes")
        return MAGIC[kind] + struct.pack("<II", len(mask), len(model)) + mask + model

    if kind == "spline":
        return MAGIC[kind] + struct.pack("<I", len(payload)) + payload

    pixels_off, palette_off, _ = offsets
    if palette_off == 0:
        pixels, palette = payload, b""
    else:
        pixels, palette = data[pixels_off:palette_off], data[palette_off:end]
    return MAGIC[kind] + struct.pack("<II", len(pixels), len(palette)) + pixels + palette


def payloads(kind: str, chunk: bytes) -> list[bytes]:
    """Return the payload sections contained in one discrete file."""
    if kind not in MAGIC:
        raise ValueError(f"unknown asset kind {kind!r}")
    if len(chunk) < 4 or chunk[:4] != MAGIC[kind]:
        raise ValueError(f"bad magic {chunk[:4]!r} (expected {MAGIC[kind]!r})")
    if kind == "spline":
        if len(chunk) < 8:
            raise ValueError("spline chunk is shorter than its header")
        (size,) = struct.unpack_from("<I", chunk, 4)
        if 8 + size != len(chunk):
            raise ValueError(f"size mismatch: 8 + {size} != {len(chunk)}")
        return [chunk[8:]]
    if len(chunk) < 12:
        raise ValueError("model/texture chunk is shorter than its header")
    first, second = struct.unpack_from("<II", chunk, 4)
    if 12 + first + second != len(chunk):
        raise ValueError(f"size mismatch: 12 + {first} + {second} != {len(chunk)}")
    return [chunk[12:12 + first], chunk[12 + first:]]


def verify_block(kind: str, data: bytes) -> int:
    """Carve and rebuild every non-empty entry; return nonzero on any mismatch."""
    count = entry_count(data)
    mismatched = []
    empty = 0
    for asset_id in range(count):
        try:
            begin, end, _ = _entry_range(kind, data, asset_id)
            original = data[begin:end]
            if not original:
                empty += 1
                continue
            chunk = carve(kind, data, asset_id)
            if b"".join(payloads(kind, chunk)) != original:
                mismatched.append(asset_id)
        except (ValueError, struct.error) as exc:
            mismatched.append(asset_id)
            if len(mismatched) <= 5:
                print(f"  entry {asset_id}: {exc}", file=sys.stderr)

    print(f"{kind}: {count} entries, {empty} empty, {len(mismatched)} not byte-identical")
    if mismatched:
        print(f"  first problem entries: {mismatched[:10]}")
        return 1
    print(f"  every non-empty entry round-trips through {MAGIC[kind].decode()} unchanged")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if len(args) == 3 and args[0] == "verify":
        kind, block_path = args[1], args[2]
        if kind not in MAGIC:
            print(f"error: unknown asset kind {kind!r}", file=sys.stderr)
            return 1
        try:
            return verify_block(kind, Path(block_path).read_bytes())
        except (OSError, ValueError, struct.error) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    if len(args) != 4 or args[0] not in MAGIC:
        print(__doc__)
        return 1

    kind, block_path, asset_id_text, output_path = args
    try:
        asset_id = int(asset_id_text, 10)
        chunk = carve(kind, Path(block_path).read_bytes(), asset_id)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(chunk)
        sections = payloads(kind, chunk)
    except (OSError, ValueError, struct.error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"wrote {output_path}: {MAGIC[kind].decode()}, "
          f"{' + '.join(str(len(p)) for p in sections)} bytes of payload")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
