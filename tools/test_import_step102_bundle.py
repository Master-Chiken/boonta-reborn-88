"""Regression tests for source bundle archive member validation."""

import unittest

import import_step102_bundle as importer


class ValidateMemberTests(unittest.TestCase):
    def test_rejects_parent_traversal(self):
        for path in ("../Makefile", "source/../../outside.c"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    importer.validate_member(path)

    def test_rejects_absolute_and_non_normalized_paths(self):
        for path in ("/source/main.c", "source//main.c", "source/./main.c"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    importer.validate_member(path)

    def test_rejects_unexpected_top_level_directory(self):
        with self.assertRaises(ValueError):
            importer.validate_member("assets/readme.txt")

    def test_rejects_exact_blocked_paths_case_insensitively(self):
        for path in (
            "DATA/REFERENCE/PC_TRACK_IMPORT_MANIFEST.JSON",
            "Source/Track_Centerlines_PC.Generated.H",
            "SOURCE/TRACK_CENTERLINE.IMPORTED.H",
            "SOURCE/TRACK_MESH.GENERATED.H",
            "SOURCE/TRACK_BOUNDARIES.GENERATED.H",
        ):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    importer.validate_member(path)

    def test_rejects_blocked_suffix_case_insensitively(self):
        with self.assertRaises(ValueError):
            importer.validate_member("source/SomeAsset.PNG")

    def test_rejects_case_insensitive_duplicate_archive_members(self):
        seen = set()
        importer.validate_unique_member("source/Main.c", seen)
        with self.assertRaisesRegex(ValueError, "case-insensitive"):
            importer.validate_unique_member("SOURCE/main.C", seen)

    def test_preflight_rejects_existing_file_before_writing(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "already.txt").write_text("keep")
            planned = [("newdir/new.txt", b"new"), ("already.txt", b"overwrite")]
            with self.assertRaisesRegex(ValueError, "overwrite"):
                importer.preflight_destinations(planned, root)
            self.assertFalse((root / "newdir").exists())
            self.assertEqual((root / "already.txt").read_text(), "keep")

    def test_preflight_rejects_symlink_escape(self):
        import os
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp, TemporaryDirectory() as outside:
            root = Path(tmp)
            try:
                os.symlink(outside, root / "source")
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks are not available on this platform")
            with self.assertRaisesRegex(ValueError, "symlinked directory"):
                importer.preflight_destinations([("source/escape.c", b"no")], root)
            self.assertEqual(list(Path(outside).iterdir()), [])

    def test_allows_normal_source_path(self):
        self.assertEqual(importer.validate_member("source/main.c"), "source/main.c")


if __name__ == "__main__":
    unittest.main()
