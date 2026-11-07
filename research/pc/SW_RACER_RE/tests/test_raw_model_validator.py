#!/usr/bin/env python3
"""Regression tests for scripts/validate_raw_model.py."""
from __future__ import annotations
import struct
import tempfile
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_raw_model  # noqa: E402
import extract_raw_model  # noqa: E402
import extract_raw_asset  # noqa: E402
import convert_track_pack  # noqa: E402
import gc_content_store  # noqa: E402


def raw_chunk(mask: bytes, model: bytes, magic: bytes = b"RAWM") -> bytes:
    return magic + struct.pack("<II", len(mask), len(model)) + mask + model


class RawModelValidatorTests(unittest.TestCase):
    def test_rejects_truncated_header(self) -> None:
        problems, _ = validate_raw_model.analyze(b"RAWM")
        self.assertTrue(any("smaller than the 12-byte header" in p for p in problems))

    def test_rejects_bad_magic(self) -> None:
        problems, _ = validate_raw_model.analyze(raw_chunk(bytes(4), b"Comp", b"NOPE"))
        self.assertTrue(any("bad magic" in p for p in problems))

    def test_accepts_minimal_compressed_chunk(self) -> None:
        problems, notes = validate_raw_model.analyze(raw_chunk(bytes(4), b"Comp"))
        self.assertEqual(problems, [])
        self.assertTrue(any("compressed" in n for n in notes))

    def test_rejects_declared_size_mismatch(self) -> None:
        chunk = b"RAWM" + struct.pack("<II", 4, 8) + bytes(8)
        problems, _ = validate_raw_model.analyze(chunk)
        self.assertTrue(any("size mismatch" in p for p in problems))

    def test_rejects_misaligned_mask(self) -> None:
        problems, _ = validate_raw_model.analyze(raw_chunk(b"\x00", b"Modl"))
        self.assertTrue(any("not a multiple of 4" in p for p in problems))
        self.assertTrue(any("expected mask_size" in p for p in problems))

    def test_detects_pointer_past_end_of_model(self) -> None:
        mask = b"\x40\x00\x00\x00"
        model = b"Modl" + struct.pack(">I", 0x100)
        problems, _ = validate_raw_model.analyze(raw_chunk(mask, model))
        self.assertTrue(any("point past the end of the model" in p for p in problems))


    def test_extracts_model_from_valid_block(self) -> None:
        block = struct.pack(">IIII", 1, 16, 20, 24) + bytes(4) + b"Comp"
        mask, model = extract_raw_model.extract_model_bytes(block, 0)
        self.assertEqual(mask, bytes(4))
        self.assertEqual(model, b"Comp")

    def test_rejects_extractor_offset_outside_block(self) -> None:
        block = struct.pack(">IIII", 1, 16, 20, 0x100) + bytes(4) + b"Comp"
        with self.assertRaises(ValueError):
            extract_raw_model.extract_model_bytes(block, 0)

    def test_rejects_truncated_stock_offsets(self) -> None:
        with self.assertRaises(ValueError):
            validate_raw_model.inspect_stock_model(bytes(4), 0)


    def test_roundtrips_model_raw_asset(self) -> None:
        block = struct.pack(">IIII", 1, 16, 20, 24) + bytes(4) + b"Modl"
        chunk = extract_raw_asset.carve("model", block, 0)
        self.assertEqual(chunk[:4], b"RAWM")
        self.assertEqual(b"".join(extract_raw_asset.payloads("model", chunk)), bytes(4) + b"Modl")
        self.assertEqual(extract_raw_asset.verify_block("model", block), 0)

    def test_roundtrips_spline_raw_asset(self) -> None:
        block = struct.pack(">III", 1, 12, 16) + b"ABCD"
        chunk = extract_raw_asset.carve("spline", block, 0)
        self.assertEqual(chunk[:4], b"RAWS")
        self.assertEqual(extract_raw_asset.payloads("spline", chunk), [b"ABCD"])
        self.assertEqual(extract_raw_asset.verify_block("spline", block), 0)

    def test_roundtrips_texture_without_palette(self) -> None:
        block = struct.pack(">III", 1, 12, 0) + b"ABCD"
        chunk = extract_raw_asset.carve("texture", block, 0)
        self.assertEqual(chunk[:4], b"RAWT")
        self.assertEqual(extract_raw_asset.payloads("texture", chunk), [b"ABCD", b""])
        self.assertEqual(extract_raw_asset.verify_block("texture", block), 0)

    def test_rejects_out_of_range_asset_offsets(self) -> None:
        block = struct.pack(">IIII", 1, 16, 20, 0x100) + bytes(4) + b"Modl"
        with self.assertRaises(ValueError):
            extract_raw_asset.carve("model", block, 0)


    def test_content_store_ignores_non_sha256_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            store = root / "content"
            referenced = "a" * 64
            orphan = "b" * 64
            (store / "aa").mkdir(parents=True)
            (store / "bb").mkdir(parents=True)
            (store / "zz").mkdir(parents=True)
            (store / "aa" / referenced).write_bytes(b"used")
            (store / "bb" / orphan).write_bytes(b"unused")
            (store / "zz" / "notes.txt").write_text("not a content blob", encoding="utf-8")
            blobs = gc_content_store.stored_blobs(str(root))
            self.assertEqual(set(blobs), {referenced, orphan})

    def test_converter_imports_asset_carver(self) -> None:
        self.assertEqual(convert_track_pack.entry_count(struct.pack(">I", 1) + bytes(12)), 1)


    # Adversarial packed-block tests for the discrete-asset extractor. These use synthetic
    # headers only; no original game files are needed in CI.
    def test_model_rejects_truncated_offset_table(self) -> None:
        block = struct.pack(">I", 2) + struct.pack(">III", 16, 20, 24) + bytes(4)
        with self.assertRaisesRegex(ValueError, "truncated model offset table"):
            extract_raw_asset.carve("model", block, 0)

    def test_model_rejects_reversed_offsets(self) -> None:
        block = struct.pack(">IIII", 1, 16, 24, 20) + bytes(8)
        with self.assertRaisesRegex(ValueError, "invalid model offsets"):
            extract_raw_asset.carve("model", block, 0)

    def test_model_rejects_unaligned_offsets(self) -> None:
        block = struct.pack(">IIII", 1, 17, 20, 24) + bytes(8)
        with self.assertRaisesRegex(ValueError, "four-byte aligned"):
            extract_raw_asset.carve("model", block, 0)

    def test_model_rejects_empty_model_payload(self) -> None:
        block = struct.pack(">IIII", 1, 16, 20, 20) + bytes(4)
        with self.assertRaisesRegex(ValueError, "invalid mask/model sizes"):
            extract_raw_asset.carve("model", block, 0)

    def test_spline_rejects_truncated_offset_table(self) -> None:
        block = struct.pack(">II", 1, 12)
        with self.assertRaisesRegex(ValueError, "truncated spline offset table"):
            extract_raw_asset.carve("spline", block, 0)

    def test_spline_rejects_payload_before_table(self) -> None:
        block = struct.pack(">III", 1, 8, 16) + bytes(4)
        with self.assertRaisesRegex(ValueError, "invalid spline offsets"):
            extract_raw_asset.carve("spline", block, 0)

    def test_spline_rejects_end_past_eof(self) -> None:
        block = struct.pack(">III", 1, 12, 20) + bytes(4)
        with self.assertRaisesRegex(ValueError, "invalid spline offsets"):
            extract_raw_asset.carve("spline", block, 0)

    def test_spline_rejects_unaligned_offsets(self) -> None:
        block = struct.pack(">III", 1, 13, 16) + bytes(4)
        with self.assertRaisesRegex(ValueError, "four-byte aligned"):
            extract_raw_asset.carve("spline", block, 0)

    def test_texture_rejects_truncated_offset_table(self) -> None:
        block = struct.pack(">III", 2, 12, 0)
        with self.assertRaisesRegex(ValueError, "truncated texture offset table"):
            extract_raw_asset.carve("texture", block, 0)

    def test_texture_rejects_pixels_before_table(self) -> None:
        block = struct.pack(">III", 1, 8, 0) + bytes(8)
        with self.assertRaisesRegex(ValueError, "invalid texture offsets"):
            extract_raw_asset.carve("texture", block, 0)

    def test_texture_rejects_palette_before_pixels(self) -> None:
        block = struct.pack(">III", 1, 12, 8) + b"ABCDEFGH"
        with self.assertRaisesRegex(ValueError, "invalid palette offset"):
            extract_raw_asset.carve("texture", block, 0)

    def test_texture_rejects_palette_past_eof(self) -> None:
        block = struct.pack(">III", 1, 12, 20) + b"ABCD"
        with self.assertRaisesRegex(ValueError, "invalid palette offset"):
            extract_raw_asset.carve("texture", block, 0)

    def test_texture_rejects_unaligned_offsets(self) -> None:
        block = struct.pack(">III", 1, 13, 0) + b"ABC"
        with self.assertRaisesRegex(ValueError, "four-byte aligned"):
            extract_raw_asset.carve("texture", block, 0)

    def test_texture_multi_entry_ranges_are_derived_from_next_entry(self) -> None:
        block = struct.pack(">IIIII", 2, 20, 0, 24, 0) + b"ABCDEFGH"
        first = extract_raw_asset.carve("texture", block, 0)
        second = extract_raw_asset.carve("texture", block, 1)
        self.assertEqual(extract_raw_asset.payloads("texture", first), [b"ABCD", b""])
        self.assertEqual(extract_raw_asset.payloads("texture", second), [b"EFGH", b""])
        self.assertEqual(extract_raw_asset.verify_block("texture", block), 0)

    def test_model_multi_entry_offsets_roundtrip(self) -> None:
        header = struct.pack(">I5I", 2, 24, 28, 32, 36, 40)
        first_entry = bytes(4) + b"Modl"
        second_entry = bytes([1, 2, 3, 4]) + b"Mod2"
        block = header + first_entry + second_entry

        first = extract_raw_asset.carve("model", block, 0)
        second = extract_raw_asset.carve("model", block, 1)
        self.assertEqual(extract_raw_asset.payloads("model", first), [bytes(4), b"Modl"])
        self.assertEqual(extract_raw_asset.payloads("model", second), [bytes([1, 2, 3, 4]), b"Mod2"])
        self.assertEqual(extract_raw_asset.verify_block("model", block), 0)

    def test_spline_multi_entry_offsets_roundtrip(self) -> None:
        block = struct.pack(">IIII", 2, 16, 20, 24) + b"SP01SP02"
        first = extract_raw_asset.carve("spline", block, 0)
        second = extract_raw_asset.carve("spline", block, 1)
        self.assertEqual(extract_raw_asset.payloads("spline", first), [b"SP01"])
        self.assertEqual(extract_raw_asset.payloads("spline", second), [b"SP02"])
        self.assertEqual(extract_raw_asset.verify_block("spline", block), 0)

    def test_all_extractors_reject_out_of_range_ids(self) -> None:
        model = struct.pack(">IIII", 1, 16, 20, 24) + bytes(8)
        spline = struct.pack(">III", 1, 12, 16) + b"ABCD"
        texture = struct.pack(">III", 1, 12, 0) + b"ABCD"
        for kind, block in (("model", model), ("spline", spline), ("texture", texture)):
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(ValueError, "out of range"):
                    extract_raw_asset.carve(kind, block, 1)

    def test_unknown_asset_kind_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown asset kind"):
            extract_raw_asset.carve("sprite", b"\x00\x00\x00\x00", 0)


if __name__ == "__main__":
    unittest.main()
