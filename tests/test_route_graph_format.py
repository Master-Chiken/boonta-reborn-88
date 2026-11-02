import copy
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAT_DIR = ROOT / "tools" / "route_graph_format"
FIXTURE_DIR = FORMAT_DIR / "fixtures"
sys.path.insert(0, str(FORMAT_DIR))

import validate_route_graph as route_graph_module  # noqa: E402
from unittest import mock

from validate_route_graph import (  # noqa: E402
    RouteCursor,
    RouteGraphError,
    allocate_progress_spans,
    evaluate_edge,
    load_route_graph,
    progress_at,
    sample_edge_length,
    sample_route_edge_lengths,
    validate_route_graph,
)

from export_closed_loop_track import (  # noqa: E402
    RouteGraphExportError,
    export_closed_loop_track,
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
        self.assertIn(r"\S", schema["properties"]["name"]["pattern"])
        self.assertIn(r"\S", schema["$defs"]["source"]["properties"]["release"]["pattern"])

    def test_rejects_boolean_schema_version_and_non_json_metadata(self):
        graph = fixture("open-bezier.json")
        invalid_version = copy.deepcopy(graph)
        invalid_version["schema_version"] = True
        with self.assertRaisesRegex(RouteGraphError, "schema_version must equal 1"):
            validate_route_graph(invalid_version)

        invalid_metadata = copy.deepcopy(graph)
        invalid_metadata["metadata"] = {"nested": [math.nan]}
        with self.assertRaisesRegex(RouteGraphError, "non-finite JSON number"):
            validate_route_graph(invalid_metadata)

    def test_rejects_unicode_identifiers_and_null_metadata(self):
        graph = fixture("open-bezier.json")
        invalid_id = copy.deepcopy(graph)
        invalid_id["route_id"] = "circuit-é"
        with self.assertRaisesRegex(RouteGraphError, "unsupported character"):
            validate_route_graph(invalid_id)

        invalid_root_metadata = copy.deepcopy(graph)
        invalid_root_metadata["metadata"] = None
        with self.assertRaisesRegex(RouteGraphError, "metadata must be an object"):
            validate_route_graph(invalid_root_metadata)

        invalid_node_metadata = copy.deepcopy(graph)
        invalid_node_metadata["nodes"][0]["metadata"] = None
        with self.assertRaisesRegex(RouteGraphError, "nodes\\[0\\].metadata must be an object"):
            validate_route_graph(invalid_node_metadata)

        invalid_edge_metadata = copy.deepcopy(graph)
        invalid_edge_metadata["edges"][0]["metadata"] = None
        with self.assertRaisesRegex(RouteGraphError, "metadata must be an object"):
            validate_route_graph(invalid_edge_metadata)

    def test_rejects_coordinates_outside_schema_bounds(self):
        graph = fixture("open-bezier.json")
        invalid = copy.deepcopy(graph)
        invalid["nodes"][0]["position"][0] = 1_000_001.0
        with self.assertRaisesRegex(RouteGraphError, "finite and between"):
            validate_route_graph(invalid)

    def test_rejects_whitespace_only_name_and_source_revision(self):
        graph = fixture("open-bezier.json")
        invalid_name = copy.deepcopy(graph)
        invalid_name["name"] = "   "
        with self.assertRaisesRegex(RouteGraphError, "name must be a non-empty string"):
            validate_route_graph(invalid_name)

        invalid_source = copy.deepcopy(graph)
        invalid_source["source"]["release"] = "  "
        with self.assertRaisesRegex(RouteGraphError, "source.release must be a non-empty string"):
            validate_route_graph(invalid_source)

    def test_adjacent_bspline_windows_share_the_shifted_boundary(self):
        graph = fixture("uniform-cubic-bspline.json")
        controls = [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 1.0],
            [2.0, 0.0, 0.0],
            [3.0, 0.0, 2.0],
            [4.0, 0.0, 1.0],
        ]

        def bspline_point(points, t):
            weights = (
                (1.0 - t) ** 3 / 6.0,
                (3.0 * t ** 3 - 6.0 * t ** 2 + 4.0) / 6.0,
                (-3.0 * t ** 3 + 3.0 * t ** 2 + 3.0 * t + 1.0) / 6.0,
                t ** 3 / 6.0,
            )
            return [
                sum(points[index][axis] * weights[index] for index in range(4))
                for axis in range(3)
            ]

        first_window = controls[:4]
        second_window = controls[1:]
        first_start = bspline_point(first_window, 0.0)
        shared = bspline_point(first_window, 1.0)
        second_end = bspline_point(second_window, 1.0)
        graph["nodes"] = [
            {"id": f"p{index}", "position": point}
            for index, point in enumerate(controls)
        ] + [
            {"id": "route-start", "position": first_start},
            {"id": "route-join", "position": shared},
            {"id": "route-finish", "position": second_end},
        ]
        graph["start_node_id"] = "route-start"
        graph["edges"] = [
            {
                "id": "window-0",
                "from": "route-start",
                "to": "route-join",
                "curve": {
                    "type": "uniform_cubic_bspline",
                    "control_node_ids": ["p0", "p1", "p2", "p3"],
                },
                "progress": {"start": 0.0, "end": 0.5},
            },
            {
                "id": "window-1",
                "from": "route-join",
                "to": "route-finish",
                "curve": {
                    "type": "uniform_cubic_bspline",
                    "control_node_ids": ["p1", "p2", "p3", "p4"],
                },
                "progress": {"start": 0.5, "end": 1.0},
            },
        ]
        normalized = validate_route_graph(graph)
        first_end = evaluate_edge(normalized, "window-0", 1.0)["position"]
        second_start = evaluate_edge(normalized, "window-1", 0.0)["position"]
        for axis in range(3):
            self.assertAlmostEqual(first_end[axis], second_start[axis], places=8)
            self.assertAlmostEqual(first_end[axis], shared[axis], places=8)

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
        sampled_lengths = sample_route_edge_lengths(graph, samples=100)
        left_lengths = [sampled_lengths[edge_id] for edge_id in ("left-1", "left-2")]
        right_lengths = [
            sampled_lengths[edge_id]
            for edge_id in ("right-1", "right-2", "right-3")
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

    def test_cursor_move_uses_local_edge_parameter(self):
        graph = fixture("open-bezier.json")
        cursor = RouteCursor(graph)
        state = cursor.move(delta_parameter=0.25)
        self.assertEqual(state["edge_id"], "start-middle")
        self.assertAlmostEqual(state["t"], 0.25)
        self.assertAlmostEqual(state["progress"], 0.125)

    def test_cursor_move_reuses_its_validated_graph(self):
        graph = fixture("open-bezier.json")
        original_validate = route_graph_module.validate_route_graph
        with mock.patch.object(
            route_graph_module, "validate_route_graph", wraps=original_validate
        ) as validator:
            cursor = RouteCursor(graph)
            self.assertEqual(validator.call_count, 1)
            state = cursor.move(delta_parameter=0.25)
            self.assertEqual(validator.call_count, 1)
        self.assertAlmostEqual(state["progress"], 0.125)

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

        # Exact arrival at the last endpoint must be terminal, without
        # requiring a subsequent frame to move beyond t=1.
        exact_cursor = RouteCursor(graph)
        first_endpoint = exact_cursor.move(1.0)
        self.assertFalse(first_endpoint["finished"])
        self.assertEqual(first_endpoint["edge_id"], "start-middle")
        self.assertAlmostEqual(first_endpoint["t"], 1.0)
        exact_finish = exact_cursor.move(1.0)
        self.assertTrue(exact_finish["finished"])
        self.assertEqual(exact_finish["edge_id"], "middle-finish")
        self.assertAlmostEqual(exact_finish["t"], 1.0)
        self.assertAlmostEqual(exact_finish["progress"], 1.0)

        # A reverse step, even one within the endpoint tolerance, clears finish.
        tiny_reverse = exact_cursor.move(-0.0000000005)
        self.assertFalse(tiny_reverse["finished"])
        self.assertLess(tiny_reverse["t"], 1.0)

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

    def test_sample_edge_length_builds_graph_indexes_only_once(self):
        graph = fixture("open-bezier.json")
        original_validate = route_graph_module.validate_route_graph
        original_index = route_graph_module._index_validated_graph
        with mock.patch.object(
            route_graph_module, "validate_route_graph", wraps=original_validate
        ) as validator:
            with mock.patch.object(
                route_graph_module, "_index_validated_graph", wraps=original_index
            ) as indexer:
                length = sample_edge_length(graph, "start-middle", samples=100)
        self.assertGreater(length, 0.0)
        self.assertEqual(validator.call_count, 1)
        self.assertEqual(indexer.call_count, 1)

    def test_sample_route_edge_lengths_validates_and_indexes_once_for_all_edges(self):
        graph = fixture("split-rejoin-unequal-lengths.json")
        original_validate = route_graph_module.validate_route_graph
        original_index = route_graph_module._index_validated_graph
        with mock.patch.object(
            route_graph_module, "validate_route_graph", wraps=original_validate
        ) as validator:
            with mock.patch.object(
                route_graph_module, "_index_validated_graph", wraps=original_index
            ) as indexer:
                lengths = sample_route_edge_lengths(graph, samples=100)
        self.assertEqual(set(lengths), {edge["id"] for edge in graph["edges"]})
        self.assertTrue(all(length > 0.0 for length in lengths.values()))
        self.assertEqual(validator.call_count, 1)
        self.assertEqual(indexer.call_count, 1)

    def test_progress_allocator_rejects_zero_or_invalid_lengths(self):
        with self.assertRaises(RouteGraphError):
            allocate_progress_spans([10.0, 0.0], 0.2, 0.8)
        with self.assertRaises(RouteGraphError):
            allocate_progress_spans([10.0, math.nan], 0.2, 0.8)

    def test_closed_loop_export_bakes_a_single_ordered_track_v1_path(self):
        graph = fixture("closed-loop.json")
        track = export_closed_loop_track(
            graph, default_half_width=3.6, samples_per_edge=4
        )

        self.assertEqual(track["format"], "boonta-track-v1")
        self.assertTrue(track["closed_loop"])
        self.assertEqual(len(track["points"]), 12)
        self.assertEqual(track["points"][0], {
            "x": 0.0, "y": 0.0, "z": 0.0,
            "half_width": 3.6, "checkpoint": True,
        })
        self.assertEqual(track["points"][4]["x"], 10.0)
        self.assertEqual(track["points"][4]["z"], 0.0)
        self.assertEqual(track["points"][8]["x"], 10.0)
        self.assertEqual(track["points"][8]["z"], 10.0)
        self.assertEqual(sum(point["checkpoint"] for point in track["points"]), 1)
        # The closing node is represented by the first point, not duplicated.
        self.assertNotEqual(track["points"][-1]["x"], track["points"][0]["x"])

    def test_closed_loop_export_maps_surface_ids_to_explicit_road_widths(self):
        graph = fixture("closed-loop.json")
        edge = next(item for item in graph["edges"] if item["id"] == "a-b")
        edge["surface_binding"] = [
            {"t": 0.0, "surface_id": "asphalt"},
            {"t": 0.5, "surface_id": "shoulder"},
            {"t": 1.0, "surface_id": "shoulder"},
        ]
        track = export_closed_loop_track(
            graph,
            default_half_width=3.6,
            samples_per_edge=4,
            surface_widths={"asphalt": 3.6, "shoulder": 3.1},
        )
        self.assertEqual(
            [point["half_width"] for point in track["points"][:4]],
            [3.6, 3.6, 3.1, 3.1],
        )

    def test_closed_loop_export_requires_width_mapping_for_bound_surfaces(self):
        graph = fixture("closed-loop.json")
        edge = graph["edges"][0]
        edge["surface_binding"] = [
            {"t": 0.0, "surface_id": "asphalt"},
            {"t": 1.0, "surface_id": "asphalt"},
        ]
        with self.assertRaisesRegex(RouteGraphExportError, "provide its width"):
            export_closed_loop_track(graph, default_half_width=3.6, samples_per_edge=4)

    def test_closed_loop_export_rejects_branching_even_when_graph_is_valid(self):
        graph = fixture("split-rejoin-unequal-lengths.json")
        graph["closed_loop"] = True
        exit_edge = next(edge for edge in graph["edges"] if edge["id"] == "exit")
        exit_edge["progress"]["end"] = 0.9
        graph["edges"].append({
            "id": "finish-return",
            "from": "finish",
            "to": "start",
            "curve": {
                "type": "cubic_bezier",
                "control1": [0.0, 0.0, 20.0],
                "control2": [0.0, 0.0, 10.0],
            },
            "progress": {"start": 0.9, "end": 1.0},
        })
        validate_route_graph(graph)
        with self.assertRaisesRegex(RouteGraphExportError, "branching/rejoining"):
            export_closed_loop_track(graph, default_half_width=3.6, samples_per_edge=4)

    def test_closed_loop_export_enforces_runtime_point_and_width_limits(self):
        graph = fixture("closed-loop.json")
        with self.assertRaisesRegex(RouteGraphExportError, "half-width"):
            export_closed_loop_track(graph, default_half_width=0.1, samples_per_edge=4)
        with self.assertRaisesRegex(RouteGraphExportError, "4096"):
            export_closed_loop_track(graph, default_half_width=3.6, samples_per_edge=2048)

    def test_closed_loop_export_cli_writes_track_v1_json(self):
        source = FIXTURE_DIR / "closed-loop.json"
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "baked-track.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(FORMAT_DIR / "export_closed_loop_track.py"),
                    str(source),
                    str(output),
                    "--half-width", "3.6",
                    "--samples-per-edge", "4",
                ],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            baked = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(baked["format"], "boonta-track-v1")
            self.assertEqual(len(baked["points"]), 12)

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
