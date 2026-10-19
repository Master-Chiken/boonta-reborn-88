from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from pad_dol import pad_dol_file
from validate_artifacts import ArtifactError, validate_dol


def make_dol(data_size: int = 4, final_length: int | None = None) -> bytes:
    """Create a minimal synthetic DOL with one text section and one data section."""
    length = 0x120 + data_size if final_length is None else final_length
    blob = bytearray(length)
    struct.pack_into(">I", blob, 0x00, 0x100)       # text section file offset
    struct.pack_into(">I", blob, 0x48, 0x80003100)  # text section load address
    struct.pack_into(">I", blob, 0x90, 0x20)        # text section size
    struct.pack_into(">I", blob, 0x1C, 0x120)       # data section file offset
    struct.pack_into(">I", blob, 0x64, 0x80003200)  # data section load address
    struct.pack_into(">I", blob, 0xAC, data_size)   # data section size
    struct.pack_into(">I", blob, 0xE0, 0x80003100)  # entry point
    return bytes(blob)


class PadDolTests(unittest.TestCase):
    def test_adds_zero_padding_for_unaligned_final_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "minimal.dol"
            path.write_bytes(make_dol())
            before, after = pad_dol_file(path)
            self.assertEqual(before, 0x124)
            self.assertEqual(after, 0x140)
            result = path.read_bytes()
            self.assertEqual(len(result), 0x140)
            self.assertEqual(result[0x124:], bytes(0x1C))
            self.assertEqual(validate_dol(path)["size"], 0x140)

    def test_does_not_change_already_padded_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "padded.dol"
            path.write_bytes(make_dol(final_length=0x140))
            before, after = pad_dol_file(path)
            self.assertEqual((before, after), (0x140, 0x140))
            self.assertEqual(len(path.read_bytes()), 0x140)

    def test_rejects_truncated_raw_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "truncated.dol"
            path.write_bytes(make_dol(final_length=0x122))
            with self.assertRaises((ValueError, ArtifactError)):
                pad_dol_file(path)


if __name__ == "__main__":
    unittest.main()
