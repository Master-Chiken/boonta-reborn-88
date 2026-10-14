"""Regression tests for the source import path policy."""

import unittest

import check_source_import_policy as policy


class ExcludedPathTests(unittest.TestCase):
    def test_exact_exclusions_ignore_case(self):
        for path in (
            "DATA/REFERENCE/PC_TRACK_IMPORT_MANIFEST.JSON",
            "Source/Track_Centerlines_PC.Generated.H",
            "SOURCE/TRACK_CENTERLINE.IMPORTED.H",
        ):
            with self.subTest(path=path):
                self.assertTrue(policy.excluded(path))

    def test_generated_mesh_and_boundary_files_are_excluded(self):
        for path in (
            "source/track_mesh.generated.h",
            "SOURCE/TRACK_MESH.GENERATED.H",
            "source/track_boundaries.generated.h",
            "SOURCE/TRACK_BOUNDARIES.GENERATED.H",
        ):
            with self.subTest(path=path):
                self.assertTrue(policy.excluded(path))

    def test_prefix_and_suffix_exclusions_ignore_case(self):
        for path in (
            "ASSETS/VOICE_EN/COMMENTARY.WAV",
            "ROMS/BOOT.DOL",
            "PRIVATE-ASSETS/MODEL.OBJ",
        ):
            with self.subTest(path=path):
                self.assertTrue(policy.excluded(path))

    def test_exact_exclusions_normalize_windows_separators(self):
        self.assertTrue(
            policy.excluded("SOURCE\\TRACK_CENTERLINE.IMPORTED.H")
        )

    def test_allowed_unrelated_source_path_is_not_excluded(self):
        self.assertFalse(policy.excluded("source/main.c"))


if __name__ == "__main__":
    unittest.main()
