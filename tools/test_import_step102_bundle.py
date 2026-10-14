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

    def test_allows_normal_source_path(self):
        self.assertEqual(importer.validate_member("source/main.c"), "source/main.c")


if __name__ == "__main__":
    unittest.main()
