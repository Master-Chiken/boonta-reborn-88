"""Regression tests for the generated native route-graph header."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTE_TOOLS = ROOT / "tools" / "route_graph_format"
sys.path.insert(0, str(ROUTE_TOOLS))

from export_runtime_route_header import (  # noqa: E402
    RuntimeRouteExportError,
    generate_runtime_route_header,
)


class RuntimeRouteHeaderTests(unittest.TestCase):
    def setUp(self):
        self.graph_path = ROOT / "gamecube-demo/data/original-test-oval-route-graph.json"
        self.widths_path = ROOT / "gamecube-demo/data/original-test-oval-surface-widths.json"
        self.generated_path = ROOT / "gamecube-demo/source/generated_route_graph.h"
        self.graph = json.loads(self.graph_path.read_text(encoding="utf-8"))
        self.widths = json.loads(self.widths_path.read_text(encoding="utf-8"))

    def test_checked_in_runtime_header_is_reproducible(self):
        expected = generate_runtime_route_header(
            self.graph, self.widths, default_half_width=3.6,
            distance_subdivisions=128,
        )
        self.assertEqual(self.generated_path.read_text(encoding="utf-8"), expected)

    def test_runtime_header_exports_branched_topology_in_authored_edge_order(self):
        graph = json.loads(
            (ROUTE_TOOLS / "fixtures/three-branch-decisions.json").read_text(
                encoding="utf-8"
            )
        )
        header = generate_runtime_route_header(
            graph, {}, default_half_width=3.6
        )

        self.assertIn("#define BOONTA_RUNTIME_ROUTE_NODE_COUNT 5U", header)
        self.assertIn("#define BOONTA_RUNTIME_ROUTE_EDGE_COUNT 7U", header)
        self.assertIn("#define BOONTA_RUNTIME_ROUTE_START_NODE_INDEX 0U", header)
        self.assertIn("#define BOONTA_RUNTIME_ROUTE_CLOSED_LOOP 0", header)
        self.assertIn("#define BOONTA_RUNTIME_ROUTE_HAS_BRANCHES 1", header)
        self.assertIn("#define BOONTA_RUNTIME_ROUTE_IS_SINGLE_LOOP 0", header)
        self.assertLess(header.index("/* d1-left */"), header.index("/* d1-right */"))
        self.assertLess(header.index("/* d2-left */"), header.index("/* d2-right */"))
        self.assertLess(header.index("/* d3-left */"), header.index("/* d3-right */"))
        self.assertIn("{ 1U, 2U, 0.100000000f, 0.400000000f }", header)

    def test_runtime_header_exports_open_unbranched_topology(self):
        graph = json.loads(
            (ROUTE_TOOLS / "fixtures/open-bezier.json").read_text(encoding="utf-8")
        )
        header = generate_runtime_route_header(
            graph, {}, default_half_width=3.6
        )
        self.assertIn("#define BOONTA_RUNTIME_ROUTE_CLOSED_LOOP 0", header)
        self.assertIn("#define BOONTA_RUNTIME_ROUTE_HAS_BRANCHES 0", header)
        self.assertIn("#define BOONTA_RUNTIME_ROUTE_IS_SINGLE_LOOP 0", header)

    def test_runtime_header_rejects_unimplemented_curve_type(self):
        graph = copy.deepcopy(self.graph)
        first_edge = graph["edges"][0]
        start = next(node for node in graph["nodes"] if node["id"] == first_edge["from"])
        end = next(node for node in graph["nodes"] if node["id"] == first_edge["to"])
        p0 = [2.0 * a - b for a, b in zip(start["position"], end["position"])]
        p3 = [2.0 * b - a for a, b in zip(start["position"], end["position"])]
        graph["nodes"].extend([
            {"id": "runtime-bspline-p0", "position": p0, "up": [0, 1, 0]},
            {"id": "runtime-bspline-p3", "position": p3, "up": [0, 1, 0]},
        ])
        first_edge["curve"] = {
            "type": "uniform_cubic_bspline",
            "control_node_ids": [
                "runtime-bspline-p0", first_edge["from"],
                first_edge["to"], "runtime-bspline-p3",
            ],
        }
        with self.assertRaisesRegex(RuntimeRouteExportError, "cubic_bezier edges only"):
            generate_runtime_route_header(
                graph, self.widths, default_half_width=3.6
            )


if __name__ == "__main__":
    unittest.main()
