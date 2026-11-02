import copy
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAT_DIR = ROOT / "tools" / "route_graph_format"
FIXTURE_DIR = FORMAT_DIR / "fixtures"
sys.path.insert(0, str(FORMAT_DIR))

from validate_route_graph import (  # noqa: E402
    RouteCursor,
    RouteGraphError,
    allocate_progress_spans,
    evaluate_edge,
    load_route_graph,
    progress_at,
    sample_edge_length,
    validate_route_graph,
)


def fixture(name):
    return load_route_graph(FIXTURE_DIR / name)


class RouteGraphFormatTests(unittest.TestCase):
    def test_all_synthetic_fixtures_validate(self):
        for name in (
            "open-bezier.json",
            "uniform-cubic-bspline.json",
            "split-rejoin-unequal-lengths.json",
            "three-branch-decisions.json",
            "closed-loop.json",
        ):
            with self.subTest(fixture=name):
                graph = fixture(name)
                self.assertEqual(graph["format"], "boonta-route-graph-v1")
                self.assertEqual(graph["source"]["platform"], "synthetic")

    def test_validation_is_idempotent_and_json_compatible(self):
        graph = fixture("open-bezier.json")
        normalized = validate_route_graph(graph)
        reparsed = validate_route_graph(normalized)
        self.assertEqual(reparsed, normalized)
        json.dumps(reparsed, allow_nan=False)

    def test_schema_is_draft_2020_12_and_versioned(self):
        schema = json.loads((FORMAT_DIR / "schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["format"]["const"], "boonta-route-graph-v1")
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)

    def test_bezier_known_midpoint_and_unit_frame(self):
        graph = fixture("open-bezier.json")
        sample = evaluate_edge(graph, "start-middle", 0.5)
        self.assertAlmostEqual(sample["position"][0], 1.5, places=8)
        self.assertAlmostEqual(sample["position"][1], 0.0, places=8)
        self.assertAlmostEqual(sample["position"][2], 0.0, places=8)
        self.assertAlmostEqual(math.sqrt(sum(v * v for v in sample["tangent"])), 1.0, places=8)
        self.assertAlmostEqual(math.sqrt(sum(v * v for v in sample["up"])), 1.0, places=8)
        self.assertAlmostEqual(sum(sample["tangent"][i] * sample["up"][i] for i in range(3)), 0.0, places=8)

    def test_bezier_uses_absolute_control_positions(self):
        graph = fixture("open-bezier.json")
        sample = evaluate_edge(graph, "start-middle", 0.5)
        self.assertAlmostEqual(sample["position"][0], 1.5, places=8)
        self.assertNotAlmostEqual(sample["position"][0], 0.75, places=5)

    def test_uniform_cubic_bspline_known_window_values(self):
        graph = fixture("uniform-cubic-bspline.json")
        start = evaluate_edge(graph, "bspline-span", 0.0)
        middle = evaluate_edge(graph, "bspline-span", 0.5)
        end = evaluate_edge(graph, "bspline-span", 1.0)
        self.assertAlmostEqual(start["position"][0], 1.0, places=8)
        self.assertAlmostEqual(start["position"][2], 2.0 / 3.0, places=8)
        self.assertAlmostEqual(middle["position"][0], 1.5, places=8)
        self.assertAlmostEqual(end["position"][0], 2.0, places=8)
        self.assertAlmostEqual(end["position"][2], 0.5, places=8)
        self.assertAlmostEqual(start["tangent"][0], 1.0, places=8)
        self.assertAlmostEqual(end["tangent"][0], 1.0 / math.sqrt(1.25), places=8)
        self.assertAlmostEqual(end["tangent"][2], 0.5 / math.sqrt(1.25), places=8)

    def test_bspline_window_is_independent_from_edge_topology_links(self):
        graph = fixture("uniform-cubic-bspline.json")
        curve = graph["edges"][0]["curve"]
        self.assertNotEqual(graph["edges"][0]["from"], curve["control_node_ids"][1])
        self.assertNotEqual(graph["edges"][0]["to"], curve["control_node_ids"][2])
        normalized = validate_route_graph(graph)
        sample = evaluate_edge(normalized, "bspline-span", 0.5)
        self.assertAlmostEqual(sample["position"][0], 1.5, places=8)

    def test_bspline_curve_must_meet_its_topology_endpoints(self):
        graph = fixture("uniform-cubic-bspline.json")
        invalid = copy.deepcopy(graph)
        start = next(node for node in invalid["nodes"] if node["id"] == "route-start")
        start["position"][0] += 0.25
        with self.assertRaisesRegex(RouteGraphError, "B-spline start does not meet topology node"):
            validate_route_graph(invalid)

    def test_split_rejoin_maps_unequal_physical_branches_to_same_progress_band(self):
        graph = fixture("split-rejoin-unequal-lengths.json")
        left_lengths = [
            sample_edge_length(graph, "left-1", samples=100),
            sample_edge_length(graph, "left-2", samples=100),
        ]
        right_lengths = [
            sample_edge_length(graph, "right-1", samples=100),
            sample_edge_length(graph, "right-2", samples=100),
            sample_edge_length(graph, "right-3", samples=100),
        ]
        left_total = math.fsum(left_lengths)
        right_total = math.fsum(right_lengths)
        self.assertGreater(right_total, left_total * 2.5)

        left_spans = allocate_progress_spans(left_lengths, 0.2, 0.8)
        right_spans = allocate_progress_spans(right_lengths, 0.2, 0.8)
        self.assertAlmostEqual(left_spans[0]["start"], 0.2)
        self.assertAlmostEqual(left_spans[-1]["end"], 0.8)
        self.assertAlmostEqual(right_spans[0]["start"], 0.2)
        self.assertAlmostEqual(right_spans[-1]["end"], 0.8)
        for actual, edge_id in zip(left_spans, ("left-1", "left-2")):
            edge = next(item for item in graph["edges"] if item["id"] == edge_id)
            self.assertAlmostEqual(actual["start"], edge["progress"]["start"], places=8)
            self.assertAlmostEqual(actual["end"], edge["progress"]["end"], places=8)
        for actual, edge_id in zip(right_spans, ("right-1", "right-2", "right-3")):
            edge = next(item for item in graph["edges"] if item["id"] == edge_id)
            self.assertAlmostEqual(actual["start"], edge["progress"]["start"], places=8)
            self.assertAlmostEqual(actual["end"], edge["progress"]["end"], places=8)

        self.assertAlmostEqual(progress_at(graph, "left-1", 0.0), 0.2)
        self.assertAlmostEqual(progress_at(graph, "right-1", 0.0), 0.2)
        self.assertAlmostEqual(progress_at(graph, "left-2", 1.0), 0.8)
        self.assertAlmostEqual(progress_at(graph, "right-3", 1.0), 0.8)

    def test_surface_binding_is_separate_from_width(self):
        graph = fixture("split-rejoin-unequal-lengths.json")
        edge = next(item for item in graph["edges"] if item["id"] == "left-1")
        self.assertEqual(edge["surface_binding"][0], {"t": 0, "surface_id": "road-left-approach"})
        self.assertNotIn("half_width", edge)
        self.assertNotIn("half_width", graph["nodes"][0])

        invalid = copy.deepcopy(graph)
        invalid["edges"][1]["half_width"] = 3.4
        with self.assertRaisesRegex(RouteGraphError, "do not store half_width"):
            validate_route_graph(invalid)

    def test_three_branch_decisions_survive_reverse_and_forward_replay(self):
        graph = fixture("three-branch-decisions.json")
        cursor = RouteCursor(graph)
        state = cursor.move(3.05, {
            "decision-1": "d1-right",
            "decision-2": "d2-left",
            "decision-3": "d3-right",
        })
        expected_path = ("approach", "d1-right", "d2-left", "d3-right")
        self.assertEqual(state["path_history"], expected_path)
        self.assertEqual(state["edge_id"], "d3-right")

        reversed_state = cursor.move(-2.1)
        self.assertEqual(reversed_state["path_index"], 0)
        self.assertEqual(reversed_state["edge_id"], "approach")
        self.assertAlmostEqual(reversed_state["t"], 0.95, places=8)
        self.assertEqual(reversed_state["path_history"], expected_path)

        replayed = cursor.move(2.1)
        self.assertEqual(replayed["path_history"], expected_path)
        self.assertEqual(replayed["edge_id"], "d3-right")

    def test_cursor_requires_explicit_branch_choice_and_rolls_back_on_error(self):
        graph = fixture("three-branch-decisions.json")
        cursor = RouteCursor(graph)
        with self.assertRaisesRegex(RouteGraphError, "branch choice required"):
            cursor.move(1.1)
        self.assertEqual(cursor.path_history, ["approach"])
        self.assertEqual(cursor.path_index, 0)
        self.assertAlmostEqual(cursor.t, 0.0)

    def test_open_endpoint_clamps_and_reverse_motion_does_not_wrap(self):
        graph = fixture("open-bezier.json")
        cursor = RouteCursor(graph)
        state = cursor.move(10.0)
        self.assertTrue(state["finished"])
        self.assertEqual(state["edge_id"], "middle-finish")
        self.assertAlmostEqual(state["t"], 1.0)
        self.assertAlmostEqual(state["progress"], 1.0)

        backwards = cursor.move(-0.25)
        self.assertFalse(backwards["finished"])
        self.assertEqual(backwards["edge_id"], "middle-finish")
        self.assertAlmostEqual(backwards["t"], 0.75)
        self.assertLess(backwards["progress"], 1.0)

    def test_closed_loop_wraps_through_explicit_graph_edge(self):
        graph = fixture("closed-loop.json")
        cursor = RouteCursor(graph)
        state = cursor.move(3.2)
        self.assertFalse(state["finished"])
        self.assertEqual(state["edge_id"], "a-b")
        self.assertEqual(state["path_history"], ("a-b", "b-c", "c-a", "a-b"))
        self.assertAlmostEqual(state["t"], 0.2, places=8)

    def test_rejects_missing_edges_and_duplicate_ids(self):
        graph = fixture("open-bezier.json")
        missing = copy.deepcopy(graph)
        missing["edges"][0]["to"] = "does-not-exist"
        with self.assertRaisesRegex(RouteGraphError, "missing node"):
            validate_route_graph(missing)

        duplicate_node = copy.deepcopy(graph)
        duplicate_node["nodes"][1]["id"] = duplicate_node["nodes"][0]["id"]
        with self.assertRaisesRegex(RouteGraphError, "duplicate node"):
            validate_route_graph(duplicate_node)

        duplicate_edge = copy.deepcopy(graph)
        duplicate_edge["edges"][1]["id"] = duplicate_edge["edges"][0]["id"]
        with self.assertRaisesRegex(RouteGraphError, "duplicate edge"):
            validate_route_graph(duplicate_edge)

    def test_rejects_discontinuous_rejoin_progress(self):
        graph = fixture("split-rejoin-unequal-lengths.json")
        invalid = copy.deepcopy(graph)
        edge = next(item for item in invalid["edges"] if item["id"] == "right-3")
        edge["progress"]["end"] = 0.79
        with self.assertRaisesRegex(RouteGraphError, "inconsistent incoming progress"):
            validate_route_graph(invalid)

    def test_rejects_invalid_bspline_window_and_non_finite_coordinates(self):
        graph = fixture("uniform-cubic-bspline.json")
        invalid_window = copy.deepcopy(graph)
        invalid_window["edges"][0]["curve"]["control_node_ids"] = ["p0", "p1", "missing", "p3"]
        with self.assertRaisesRegex(RouteGraphError, "references missing node"):
            validate_route_graph(invalid_window)

        invalid_coordinate = copy.deepcopy(graph)
        invalid_coordinate["nodes"][0]["position"][0] = math.inf
        with self.assertRaisesRegex(RouteGraphError, "finite"):
            validate_route_graph(invalid_coordinate)

    def test_rejects_unsorted_surface_binding_samples(self):
        graph = fixture("split-rejoin-unequal-lengths.json")
        invalid = copy.deepcopy(graph)
        edge = next(item for item in invalid["edges"] if item["id"] == "left-1")
        edge["surface_binding"][1]["t"] = 0.0
        with self.assertRaisesRegex(RouteGraphError, "strictly increasing"):
            validate_route_graph(invalid)

    def test_progress_allocator_rejects_zero_or_invalid_lengths(self):
        with self.assertRaises(RouteGraphError):
            allocate_progress_spans([10.0, 0.0], 0.2, 0.8)
        with self.assertRaises(RouteGraphError):
            allocate_progress_spans([10.0, math.nan], 0.2, 0.8)

    def test_cli_accepts_synthetic_example(self):
        path = FIXTURE_DIR / "open-bezier.json"
        result = subprocess.run(
            [sys.executable, str(FORMAT_DIR / "validate_route_graph.py"), str(path)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("boonta-route-graph-v1", result.stdout)


if __name__ == "__main__":
    unittest.main()
