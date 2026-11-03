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
sys.path.insert(0, str(ROOT / "tools" / "route_graph_format"))

from validate_track import TrackValidationError, load_track, validate_track  # noqa: E402
from export_track_header import render_header  # noqa: E402
from export_closed_loop_track import export_closed_loop_track  # noqa: E402


EXAMPLE_PATH = ROOT / "tools" / "track_format" / "example_track.json"
RUNTIME_ROUTE_GRAPH_PATH = ROOT / "gamecube-demo" / "data" / "original-test-oval-route-graph.json"
RUNTIME_SURFACE_WIDTHS_PATH = ROOT / "gamecube-demo" / "data" / "original-test-oval-surface-widths.json"


class TrackFormatTests(unittest.TestCase):
    def setUp(self):
        self.valid = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))

    def test_original_example_is_valid_closed_loop(self):
        track = load_track(EXAMPLE_PATH)
        self.assertTrue(track["closed_loop"])
        self.assertEqual(len(track["points"]), 8)
        self.assertTrue(track["points"][0]["checkpoint"])

    def test_start_finish_tangent_points_forward(self):
        points = self.valid["points"]
        previous = points[-1]
        following = points[1]
        # Catmull-Rom's start tangent is proportional to next - previous.
        # Equal X and increasing Z keep the start line facing down-course.
        self.assertAlmostEqual(following["x"], previous["x"], places=6)
        self.assertGreater(following["z"], previous["z"])
        self.assertTrue(points[0]["checkpoint"])

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

    def test_runtime_oval_route_graph_is_the_canonical_header_source(self):
        graph = json.loads(RUNTIME_ROUTE_GRAPH_PATH.read_text(encoding="utf-8"))
        widths = json.loads(RUNTIME_SURFACE_WIDTHS_PATH.read_text(encoding="utf-8"))
        track = export_closed_loop_track(
            graph,
            default_half_width=3.5,
            samples_per_edge=16,
            surface_widths=widths,
        )
        self.assertTrue(track["closed_loop"])
        self.assertEqual(len(graph["nodes"]), 8)
        self.assertEqual(len(graph["edges"]), 8)
        self.assertEqual(len(track["points"]), 128)
        self.assertTrue(track["points"][0]["checkpoint"])
        self.assertEqual(sum(point["checkpoint"] for point in track["points"]), 1)

        expected = render_header(track, "original test oval")
        checked_in = (ROOT / "gamecube-demo" / "source" / "generated_track.h").read_text(
            encoding="utf-8"
        )
        self.assertEqual(checked_in, expected)


    def test_runtime_oval_spline_length_stays_close_to_lap_polyline_distance(self):
        graph = json.loads(RUNTIME_ROUTE_GRAPH_PATH.read_text(encoding="utf-8"))
        widths = json.loads(RUNTIME_SURFACE_WIDTHS_PATH.read_text(encoding="utf-8"))
        track = export_closed_loop_track(
            graph,
            default_half_width=3.5,
            samples_per_edge=16,
            surface_widths=widths,
        )
        points = track["points"]
        point_count = len(points)

        def position(index):
            point = points[index % point_count]
            return (point["x"], point["y"], point["z"])

        def catmull(index, t):
            p0, p1, p2, p3 = (
                position(index - 1), position(index),
                position(index + 1), position(index + 2),
            )
            t2 = t * t
            t3 = t2 * t
            return tuple(
                0.5 * (
                    2.0 * p1[axis]
                    + (-p0[axis] + p2[axis]) * t
                    + (2.0 * p0[axis] - 5.0 * p1[axis]
                       + 4.0 * p2[axis] - p3[axis]) * t2
                    + (-p0[axis] + 3.0 * p1[axis]
                       - 3.0 * p2[axis] + p3[axis]) * t3
                )
                for axis in range(3)
            )

        polyline_length = sum(
            math.dist(position(index), position(index + 1))
            for index in range(point_count)
        )
        spline_length = 0.0
        subdivisions = 64
        for index in range(point_count):
            previous = catmull(index, 0.0)
            for step in range(1, subdivisions + 1):
                current = catmull(index, step / subdivisions)
                spline_length += math.dist(previous, current)
                previous = current

        relative_error = abs(spline_length - polyline_length) / polyline_length
        self.assertGreater(polyline_length, 0.0)
        self.assertLess(
            relative_error,
            0.0002,
            f"runtime Catmull-Rom length differs from lap distance by "
            f"{relative_error:.5%} ({spline_length - polyline_length:.6f} m)",
        )

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
