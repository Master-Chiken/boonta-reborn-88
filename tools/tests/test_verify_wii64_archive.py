import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from verify_wii64_archive import inspect_archive, sha256_bytes


class VerifyWii64ArchiveTests(unittest.TestCase):
    def test_sha256_bytes(self):
        self.assertEqual(
            sha256_bytes(b"abc"),
            hashlib.sha256(b"abc").hexdigest(),
        )

    def test_reports_missing_expected_members(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("unrelated.txt", "not Wii64")
            checks = inspect_archive(path)
        self.assertEqual(len(checks), 5)
        self.assertTrue(all(check.actual is None for check in checks[1:]))

    def test_reports_present_but_different_members(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("apps/wii64/boot.dol", b"not the reviewed binary")
            checks = inspect_archive(path)
        self.assertIsNotNone(checks[1].actual)
        self.assertFalse(checks[1].matches)
        self.assertTrue(all(check.actual is None for check in checks[2:]))

    def test_rejects_duplicate_expected_member(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("apps/wii64/boot.dol", b"first copy")
                archive.writestr("apps/wii64/boot.dol", b"second copy")
            with self.assertRaisesRegex(ValueError, "duplicate archive member"):
                inspect_archive(path)


if __name__ == "__main__":
    unittest.main()
