"""Regression tests for the generated native route-graph header."""
from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import tempfile
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

    def test_branched_runtime_header_compiles_and_initial_cursor_selects_an_edge(self):
        graph = json.loads(
            (ROUTE_TOOLS / "fixtures/three-branch-decisions.json").read_text(
                encoding="utf-8"
            )
        )
        header = generate_runtime_route_header(
            graph, {}, default_half_width=3.6
        )
        c_source = r"""
#include <assert.h>
#define BOONTA_ROUTE_GRAPH_HEADER "branch_route.h"
#include "route_graph_sampling.h"

int main(void)
{
    static const float edge_lengths[BOONTA_RUNTIME_ROUTE_EDGE_COUNT] = {
        1.0f, 2.0f, 3.0f, 4.0f, 5.0f, 6.0f, 7.0f
    };
    static const BoontaRouteCursorGraph graph = {
        boonta_runtime_route_topology_edges,
        BOONTA_RUNTIME_ROUTE_EDGE_COUNT,
        BOONTA_RUNTIME_ROUTE_NODE_COUNT,
        BOONTA_RUNTIME_ROUTE_START_NODE_INDEX,
        BOONTA_RUNTIME_ROUTE_CLOSED_LOOP
    };
    BoontaRouteCursor cursor;
    BoontaRouteCursorState state;
    unsigned int selected_edge = BOONTA_ROUTE_CURSOR_NO_EDGE;
    BoontaRouteBranchChoice choice;

    assert(BOONTA_RUNTIME_ROUTE_HAS_BRANCHES == 1);
    assert(BOONTA_RUNTIME_ROUTE_IS_SINGLE_LOOP == 0);
    assert(boonta_runtime_route_edges[0].p0[2] == 0.0f);
    assert(boonta_runtime_route_width_samples[0] > 0.0f);

    /* Reach decision-1 without crossing it, then classify its tangent branches. */
    assert(boonta_route_cursor_init(&cursor, &graph, edge_lengths, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_move(&cursor, 1.0f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_graph_choose_outgoing_edge(
        &cursor, 1U, -1, &selected_edge) == BOONTA_ROUTE_CURSOR_OK);
    assert(selected_edge == 1U);
    choice.node = 1U;
    choice.edge = selected_edge;
    assert(boonta_route_cursor_move(&cursor, 0.1f, &choice, 1U) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_get_state(&cursor, &state) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(state.edge == 1U);

    /* Reinitialize and choose the right-turn branch from the same junction. */
    selected_edge = BOONTA_ROUTE_CURSOR_NO_EDGE;
    assert(boonta_route_cursor_init(&cursor, &graph, edge_lengths, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_move(&cursor, 1.0f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_graph_choose_outgoing_edge(
        &cursor, 1U, 1, &selected_edge) == BOONTA_ROUTE_CURSOR_OK);
    assert(selected_edge == 2U);
    choice.node = 1U;
    choice.edge = selected_edge;
    assert(boonta_route_cursor_move(&cursor, 0.1f, &choice, 1U) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_get_state(&cursor, &state) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(state.edge == 2U);

    /* Neutral selects the straightest continuation, with stable edge tie-break. */
    selected_edge = BOONTA_ROUTE_CURSOR_NO_EDGE;
    assert(boonta_route_cursor_init(&cursor, &graph, edge_lengths, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_move(&cursor, 1.0f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_graph_choose_outgoing_edge(
        &cursor, 1U, 0, &selected_edge) == BOONTA_ROUTE_CURSOR_OK);
    assert(selected_edge == 1U);
    return 0;
}
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            header_path = temp / "branch_route.h"
            source_path = temp / "branch_route_test.c"
            binary_path = temp / "branch_route_test"
            header_path.write_text(header, encoding="utf-8")
            source_path.write_text(c_source, encoding="utf-8")
            try:
                subprocess.run(
                    [
                        "cc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-pedantic",
                        "-I", str(temp),
                        "-I", str(ROOT / "gamecube-demo" / "source"),
                        str(source_path), "-lm", "-o", str(binary_path),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as exc:
                self.fail(
                    "generated branched header failed strict C compilation:\\n"
                    + (exc.stdout or "") + (exc.stderr or "")
                )
            try:
                subprocess.run(
                    [str(binary_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as exc:
                self.fail(
                    "generated branched cursor executable failed:\\n"
                    + (exc.stdout or "") + (exc.stderr or "")
                )

    def test_branch_selection_handles_degenerate_endpoint_handles(self):
        graph = json.loads(
            (ROUTE_TOOLS / "fixtures/three-branch-decisions.json").read_text(
                encoding="utf-8"
            )
        )
        nodes = {node["id"]: node for node in graph["nodes"]}
        edges = {edge["id"]: edge for edge in graph["edges"]}

        # The approach ends with a collapsed last handle; d1-left begins with
        # a collapsed first handle. Both curves remain valid cubic Beziers.
        # The route validator rejects zero endpoint derivatives. Generate a
        # valid header first, then mutate only its C geometry table to exercise
        # the runtime's defensive fallback for malformed/legacy generated data.
        header = generate_runtime_route_header(
            graph, {}, default_half_width=3.6
        )
        lines = header.splitlines()
        geometry_start = next(
            index for index, line in enumerate(lines)
            if "boonta_runtime_route_edges[" in line
        )

        def replace_control(edge_id, control_index, point):
            marker = f"/* {edge_id} */"
            marker_index = next(
                index for index in range(geometry_start + 1, len(lines))
                if lines[index].strip() == marker
            )
            vectors = re.findall(r"\{([^{}]+)\}", lines[marker_index + 1])
            self.assertEqual(len(vectors), 4)
            vectors[control_index] = ", ".join(
                f"{component:.9f}f" for component in point
            )
            lines[marker_index + 1] = "    { " + ", ".join(
                "{ " + vector.strip() + " }" for vector in vectors
            ) + " },"

        decision = nodes["decision-1"]["position"]
        decision3 = nodes["decision-3"]["position"]
        finish = nodes["finish"]["position"]
        replace_control("approach", 2, decision)
        replace_control("d1-left", 1, decision)
        replace_control("d3-left", 1, finish)
        replace_control("d3-left", 2, finish)
        replace_control("d3-right", 1, decision3)
        replace_control("d3-right", 2, decision3)
        header = "\n".join(lines) + "\n"
        c_source = r"""
#include <assert.h>
#include <math.h>
#define BOONTA_ROUTE_GRAPH_HEADER "branch_route.h"
#include "route_graph_sampling.h"

int main(void)
{
    static const float edge_lengths[BOONTA_RUNTIME_ROUTE_EDGE_COUNT] = {
        1.0f, 2.0f, 3.0f, 4.0f, 5.0f, 6.0f, 7.0f
    };
    static const BoontaRouteCursorGraph graph = {
        boonta_runtime_route_topology_edges,
        BOONTA_RUNTIME_ROUTE_EDGE_COUNT,
        BOONTA_RUNTIME_ROUTE_NODE_COUNT,
        BOONTA_RUNTIME_ROUTE_START_NODE_INDEX,
        BOONTA_RUNTIME_ROUTE_CLOSED_LOOP
    };
    BoontaRouteCursor cursor;
    unsigned int selected_edge = BOONTA_ROUTE_CURSOR_NO_EDGE;
    float tangent_x = 0.0f;
    float tangent_z = 0.0f;

    assert(boonta_route_cursor_init(&cursor, &graph, edge_lengths, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_move(&cursor, 1.0f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);

    /* The end tangent falls back from P3-P2 to the endpoint chord. */
    assert(boonta_route_graph_edge_horizontal_tangent(
        0U, 1, &tangent_x, &tangent_z) == BOONTA_ROUTE_CURSOR_OK);
    assert(fabsf(tangent_x) < 0.00001f);
    assert(tangent_z > 0.999f);

    /* The left edge's start tangent falls back from P1-P0 to P2-P0. */
    assert(boonta_route_graph_edge_horizontal_tangent(
        1U, 0, &tangent_x, &tangent_z) == BOONTA_ROUTE_CURSOR_OK);
    assert(tangent_x > 0.5f);
    assert(tangent_z > 0.5f);

    /* Fully collapsed handles fall back to the endpoint chord at either end. */
    assert(boonta_route_graph_edge_horizontal_tangent(
        5U, 1, &tangent_x, &tangent_z) == BOONTA_ROUTE_CURSOR_OK);
    assert(fabsf(tangent_x) < 0.00001f);
    assert(tangent_z > 0.999f);
    assert(boonta_route_graph_edge_horizontal_tangent(
        6U, 0, &tangent_x, &tangent_z) == BOONTA_ROUTE_CURSOR_OK);
    assert(fabsf(tangent_x) < 0.00001f);
    assert(tangent_z > 0.999f);

    assert(boonta_route_graph_choose_outgoing_edge(
        &cursor, 1U, -1, &selected_edge) == BOONTA_ROUTE_CURSOR_OK);
    assert(selected_edge == 1U);
    assert(boonta_route_graph_choose_outgoing_edge(
        &cursor, 1U, 1, &selected_edge) == BOONTA_ROUTE_CURSOR_OK);
    assert(selected_edge == 2U);
    return 0;
}
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            header_path = temp / "branch_route.h"
            source_path = temp / "branch_route_test.c"
            binary_path = temp / "branch_route_test"
            header_path.write_text(header, encoding="utf-8")
            source_path.write_text(c_source, encoding="utf-8")
            try:
                subprocess.run(
                    [
                        "cc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-pedantic",
                        "-I", str(temp),
                        "-I", str(ROOT / "gamecube-demo" / "source"),
                        str(source_path), "-lm", "-o", str(binary_path),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    [str(binary_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as exc:
                self.fail(
                    "degenerate-endpoint branch selector regression failed:\\n"
                    + (exc.stdout or "") + (exc.stderr or "")
                )

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
