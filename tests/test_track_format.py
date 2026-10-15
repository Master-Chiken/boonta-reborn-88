import copy
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "track_format"))

from validate_track import TrackValidationError, load_track, validate_track  # noqa: E402


EXAMPLE_PATH = ROOT / "tools" / "track_format" / "example_track.json"


class TrackFormatTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))

    def test_original_example_is_valid_closed_loop(self):
        track = load_track(EXAMPLE_PATH)
        self.assertTrue(track["closed_loop"])
        self.assertEqual(len(track["points"]), 8)
        self.assertTrue(track["points"][0]["checkpoint"])

    def test_point_to_point_course_is_valid(self):
        data = copy.deepcopy(self.valid)
        data["closed_loop"] = False
        data["points"] = data["points"][:2]
        track = validate_track(data)
        self.assertFalse(track["closed_loop"])
        self.assertEqual(len(track["points"]), 2)

    def test_rejects_wrong_format_and_non_boolean_loop(self):
        data = copy.deepcopy(self.valid)
        data["format"] = "commercial-game-format"
        with self.assertRaises(TrackValidationError):
            validate_track(data)
        data = copy.deepcopy(self.valid)
        data["closed_loop"] = 1
        with self.assertRaises(TrackValidationError):
            validate_track(data)

    def test_rejects_non_finite_and_boolean_coordinates(self):
        for bad_value in (math.nan, math.inf, -math.inf, True):
            data = copy.deepcopy(self.valid)
            data["points"][1]["x"] = bad_value
            with self.subTest(value=bad_value):
                with self.assertRaises(TrackValidationError):
                    validate_track(data)

    def test_rejects_bad_width_and_checkpoint(self):
        data = copy.deepcopy(self.valid)
        data["points"][0]["half_width"] = 0
        with self.assertRaises(TrackValidationError):
            validate_track(data)
        data = copy.deepcopy(self.valid)
        data["points"][0]["checkpoint"] = "yes"
        with self.assertRaises(TrackValidationError):
            validate_track(data)

    def test_rejects_duplicate_neighbouring_points(self):
        data = copy.deepcopy(self.valid)
        data["points"][1] = copy.deepcopy(data["points"][0])
        with self.assertRaises(TrackValidationError):
            validate_track(data)

    def test_rejects_too_many_points(self):
        data = copy.deepcopy(self.valid)
        data["points"] = data["points"] * 513
        with self.assertRaises(TrackValidationError):
            validate_track(data)

    def test_cli_accepts_example(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "track_format" / "validate_track.py"),
             str(EXAMPLE_PATH)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("8 points", result.stdout)

    def test_cli_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_file = Path(temp_dir) / "bad.json"
            bad_file.write_text("{", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "track_format" / "validate_track.py"),
                 str(bad_file)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("invalid track", result.stderr)


if __name__ == "__main__":
    unittest.main()
