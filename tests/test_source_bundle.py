"""Source-only import guard tests. These checks make no network calls."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
_POLICY_SPEC = spec_from_file_location("source_import_policy", ROOT / "tools/check_source_import_policy.py")
if _POLICY_SPEC is None or _POLICY_SPEC.loader is None:
    raise RuntimeError("Could not load source import policy module")
source_import_policy = module_from_spec(_POLICY_SPEC)
_POLICY_SPEC.loader.exec_module(source_import_policy)


class SourceBundlePolicyTests(unittest.TestCase):
    def test_build_defaults_to_procedural_fallback(self):
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("USE_IMPORTED_SPLINE ?= 0", makefile)
        self.assertNotIn("USE_IMPORTED_SPLINE ?= 1", makefile)

    def test_known_pc_derived_and_generated_geometry_headers_are_not_present(self):
        for relative in (
            "source/track_centerlines_pc.generated.h",
            "source/track_centerline.imported.h",
            "source/track_mesh.generated.h",
            "source/track_boundaries.generated.h",
            "data/reference/pc_track_import_manifest.json",
        ):
            with self.subTest(path=relative):
                self.assertFalse((ROOT / relative).exists(), relative)

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
        blocked = (
            ".iso", ".gcm", ".wbfs", ".nkit.iso", ".rvz", ".wad",
            ".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a", ".aiff", ".mid",
            ".midi", ".bnk", ".sng", ".mp4", ".mov", ".avi", ".webm",
            ".obj", ".mtl", ".png", ".jpg", ".jpeg", ".bmp", ".tga", ".dds",
            ".webp", ".gif", ".tif", ".tiff", ".bin", ".rom", ".elf", ".dol", ".map",
        )
        offenders = [
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("*")
            if path.is_file() and any(path.name.lower().endswith(ext) for ext in blocked)
        ]
        self.assertEqual([], offenders, f"unexpected files: {offenders}")

    def test_import_policy_blocks_known_geometry_anywhere(self):
        for relative in (
            "source/track_mesh.generated.h",
            "source/nested/track_boundaries.generated.h",
            "elsewhere/track_centerlines_pc.generated.h",
            "data/reference/pc_track_import_manifest.json",
        ):
            with self.subTest(path=relative):
                self.assertTrue(source_import_policy.excluded(relative))

    def test_import_policy_blocks_multimedia_and_models_case_insensitively(self):
        for relative in (
            "assets/track/preview.WEBP",
            "audio/race.M4A",
            "models/pod.OBJ",
            "disc-images/game.RVZ",
            "textures/track.PNG",
        ):
            with self.subTest(path=relative):
                self.assertTrue(source_import_policy.excluded(relative))


if __name__ == "__main__":
    unittest.main()
