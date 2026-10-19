"""Regression tests for paths held by the Step 102 source-import policy."""

import unittest

import check_source_import_policy as policy


class ExcludedPathTests(unittest.TestCase):
    def test_exact_exclusions_ignore_case(self):
        for path in (
            "DATA/REFERENCE/PC_TRACK_IMPORT_MANIFEST.JSON",
            "DATA/DEMO_TRACK_POINTS.CSV",
            "Data/Demo_Track_Edges.Csv",
            "Source/Track_Centerlines_PC.Generated.H",
            "SOURCE/TRACK_CENTERLINE.IMPORTED.H",
            "SOURCE/TRACK_CENTERLINE.GENERATED.H",
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

    def test_media_models_roms_archives_and_bytecode_are_excluded(self):
        for path in (
            "ASSETS/VOICE_EN/COMMENTARY.WAV",
            "ROMS/BOOT.DOL",
            "PRIVATE-ASSETS/MODEL.OBJ",
            "course/ship.glb",
            "tests/__pycache__/fixture.pyc",
            "handoff/step102.zip",
        ):
            with self.subTest(path=path):
                self.assertTrue(policy.excluded(path))

    def test_exact_exclusions_normalize_windows_separators(self):
        self.assertTrue(policy.excluded("SOURCE\\TRACK_CENTERLINE.IMPORTED.H"))
        self.assertTrue(policy.excluded("DATA\\DEMO_TRACK_POINTS.CSV"))

    def test_allowed_unrelated_source_path_is_not_excluded(self):
        self.assertFalse(policy.excluded("source/main.c"))
        self.assertFalse(policy.excluded("tests/test_race_logic.c"))
        self.assertFalse(policy.excluded("docs/STEP102_IMPORT_HOLD.md"))


if __name__ == "__main__":
    unittest.main()
