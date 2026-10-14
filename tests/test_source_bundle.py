"""Source-only import guard tests. These checks make no network calls."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SourceBundlePolicyTests(unittest.TestCase):
    def test_build_defaults_to_procedural_fallback(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("USE_IMPORTED_SPLINE ?= 0", makefile)
        self.assertNotIn("USE_IMPORTED_SPLINE ?= 1", makefile)

    def test_known_pc_derived_headers_are_not_present(self):
        self.assertFalse((ROOT / "source/track_centerlines_pc.generated.h").exists())
        self.assertFalse((ROOT / "source/track_centerline.imported.h").exists())
        self.assertFalse((ROOT / "data/reference/pc_track_import_manifest.json").exists())

    def test_generated_mesh_assets_are_not_present(self):
        self.assertFalse((ROOT / "source/track_mesh.generated.h").exists())
        self.assertFalse((ROOT / "source/track_boundaries.generated.h").exists())
        self.assertFalse((ROOT / "assets").exists())

    def test_core_gameplay_files_are_present(self):
        for relative in (
            "source/main.c",
            "source/racer_physics.c",
            "source/rival_ai.c",
            "source/track_catalog.c",
            "source/track_centerline.generated.h",
            "tests/test_racer_physics.c",
            "tests/test_rival_ai.c",
        ):
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_no_known_binary_or_media_assets_are_included(self):
        blocked = {
            ".iso", ".gcm", ".wbfs", ".nkit.iso", ".rvz", ".wav", ".mp3",
            ".ogg", ".flac", ".obj", ".mtl", ".png", ".jpg", ".jpeg",
            ".bmp", ".tga", ".dds", ".bin", ".rom", ".elf", ".dol", ".map",
        }
        offenders = [
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("*")
            if path.is_file() and any(path.name.lower().endswith(ext) for ext in blocked)
        ]
        self.assertEqual([], offenders, f"unexpected files: {offenders}")


if __name__ == "__main__":
    unittest.main()
