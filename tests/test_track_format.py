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
from export_track_header import render_header  # noqa: E402


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

    def test_header_export_contains_all_points_and_closed_loop_flag(self):
        track = load_track(EXAMPLE_PATH)
        header = render_header(track, "original test oval")
        self.assertIn("#define BOONTA_TRACK_CLOSED_LOOP 1", header)
        self.assertIn("#define BOONTA_TRACK_POINT_COUNT 8U", header)
        self.assertIn("boonta_track_points_original_test_oval", header)
        self.assertEqual(header.count("    { "), 8)

    def test_checked_in_gamecube_header_matches_exporter(self):
        track = load_track(EXAMPLE_PATH)
        expected = render_header(track, "original test oval")
        checked_in = (ROOT / "gamecube-demo" / "source" / "generated_track.h").read_text(
            encoding="utf-8"
        )
        self.assertEqual(checked_in, expected)

    def test_header_exports_closed_loop_polyline_length(self):
        track = load_track(EXAMPLE_PATH)
        points = track["points"]
        expected_length = sum(
            math.dist(
                (points[index]["x"], points[index]["y"], points[index]["z"]),
                (points[(index + 1) % len(points)]["x"],
                 points[(index + 1) % len(points)]["y"],
                 points[(index + 1) % len(points)]["z"]),
            )
            for index in range(len(points))
        )
        header = render_header(track, "original test oval")
        self.assertIn(f"#define BOONTA_TRACK_LENGTH {expected_length:.6f}f", header)

    def test_header_export_sanitizes_leading_digit(self):
        track = load_track(EXAMPLE_PATH)
        header = render_header(track, "88 oval")
        self.assertIn("BOONTA_GENERATED_TRACK_TRACK_88_OVAL_H", header)

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
