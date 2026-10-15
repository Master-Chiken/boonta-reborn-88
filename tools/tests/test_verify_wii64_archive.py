import hashlib
import io
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from verify_wii64_archive import inspect_archive, main, sha256_bytes


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

    def test_cli_returns_error_for_corrupt_zip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corrupt.zip"
            path.write_bytes(b"not a ZIP archive")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                result = main([str(path)])
        self.assertEqual(result, 2)
        self.assertIn("cannot inspect archive", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
