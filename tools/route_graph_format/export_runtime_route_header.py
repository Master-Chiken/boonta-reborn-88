#!/usr/bin/env python3
"""Generate the native C runtime representation of a clean-room closed route graph.

The generated file contains cubic Bezier control points and sampled surface widths.
Distance lookup tables are built once by the shared C runtime sampler at startup.
Only unbranched closed graphs composed of cubic Bezier edges are accepted.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "track_format"))

from export_closed_loop_track import (  # noqa: E402
    RouteGraphExportError,
    _checked_half_width,
    _ordered_single_loop,
)
from validate_route_graph import (  # noqa: E402
    _evaluate_edge_validated,
    _index_validated_graph,
    validate_route_graph,
)

DEFAULT_DISTANCE_SUBDIVISIONS = 128
WIDTH_SAMPLES_PER_EDGE = 16
EPSILON = 1e-9


class RuntimeRouteExportError(ValueError):
    """Raised when a route cannot be represented by the native curve runtime."""


def _c_float(value: float) -> str:
    if not math.isfinite(value):
        raise RuntimeRouteExportError("generated C values must be finite")
    if abs(value) < 0.0000000005:
        value = 0.0
    return f"{value:.9f}f"


def generate_runtime_route_header(
    graph_data: Any,
    surface_widths: Any,
    *,
    default_half_width: float = 3.6,
    distance_subdivisions: int = DEFAULT_DISTANCE_SUBDIVISIONS,
) -> str:
    """Render one deterministic C header for a closed cubic-Bezier route."""
    graph = validate_route_graph(graph_data)
    if (
        isinstance(distance_subdivisions, bool)
        or not isinstance(distance_subdivisions, int)
        or distance_subdivisions < 16
        or distance_subdivisions > 2048
    ):
        raise RuntimeRouteExportError(
            "distance_subdivisions must be an integer from 16 to 2048"
        )
    default_width = _checked_half_width(default_half_width, "default_half_width")
    if not isinstance(surface_widths, dict):
        raise RuntimeRouteExportError("surface_widths must be an object mapping IDs to widths")

    checked_widths: dict[str, float] = {}
    for surface_id, width in surface_widths.items():
        if not isinstance(surface_id, str) or not surface_id:
            raise RuntimeRouteExportError("surface_widths keys must be non-empty strings")
        checked_widths[surface_id] = _checked_half_width(
            width, f"surface_widths[{surface_id!r}]"
        )

    try:
        ordered_edges = _ordered_single_loop(graph)
    except RouteGraphExportError as exc:
        raise RuntimeRouteExportError(str(exc)) from exc
    nodes_by_id, edges_by_id = _index_validated_graph(graph)
    controls: list[tuple[list[float], list[float], list[float], list[float]]] = []
    route_widths: list[float] = []
    route_length = 0.0

    for edge in ordered_edges:
        curve = edge["curve"]
        if curve.get("type") != "cubic_bezier":
            raise RuntimeRouteExportError(
                f"edge {edge['id']!r} uses {curve.get('type')!r}; "
                "the first native runtime supports cubic_bezier edges only"
            )
        p0 = [float(v) for v in nodes_by_id[edge["from"]]["position"]]
        p3 = [float(v) for v in nodes_by_id[edge["to"]]["position"]]
        c1 = [float(v) for v in curve["control1"]]
        c2 = [float(v) for v in curve["control2"]]
        controls.append((p0, c1, c2, p3))

        previous = _evaluate_edge_validated(
            graph, edge["id"], 0.0, nodes_by_id, edges_by_id
        )["position"]
        edge_length = 0.0
        for step in range(1, distance_subdivisions + 1):
            t = step / distance_subdivisions
            current = _evaluate_edge_validated(
                graph, edge["id"], t, nodes_by_id, edges_by_id
            )["position"]
            edge_length += math.dist(previous, current)
            previous = current
        if not math.isfinite(edge_length) or edge_length <= EPSILON:
            raise RuntimeRouteExportError(
                f"edge {edge['id']!r} has no measurable 3D length"
            )
        route_length += edge_length

        bindings = edge.get("surface_binding", [])
        binding_index = 0
        for sample_index in range(WIDTH_SAMPLES_PER_EDGE):
            t = sample_index / WIDTH_SAMPLES_PER_EDGE
            while (
                bindings
                and binding_index + 1 < len(bindings)
                and t + EPSILON >= bindings[binding_index + 1]["t"]
            ):
                binding_index += 1
            if not bindings:
                route_widths.append(default_width)
                continue
            surface_id = bindings[binding_index]["surface_id"]
            if surface_id not in checked_widths:
                raise RuntimeRouteExportError(
                    f"edge {edge['id']!r} references surface {surface_id!r} "
                    "without an explicit width"
                )
            route_widths.append(checked_widths[surface_id])

    if not math.isfinite(route_length) or route_length <= EPSILON:
        raise RuntimeRouteExportError("closed route must have a finite positive length")

    node_indices = {
        node["id"]: index for index, node in enumerate(graph["nodes"])
    }
    topology_lines = []
    for edge in ordered_edges:
        progress = edge["progress"]
        topology_lines.append(
            f"    /* {edge['id']} */\n"
            f"    {{ {node_indices[edge['from']]}U, {node_indices[edge['to']]}U, "
            f"{_c_float(progress['start'])}, {_c_float(progress['end'])} }}"
        )

    edge_lines = []
    for edge, (p0, c1, c2, p3) in zip(ordered_edges, controls):
        edge_lines.append(
            f"    /* {edge['id']} */\n"
            f"    {{ {{{', '.join(_c_float(v) for v in p0)}}}, "
            f"{{{', '.join(_c_float(v) for v in c1)}}}, "
            f"{{{', '.join(_c_float(v) for v in c2)}}}, "
            f"{{{', '.join(_c_float(v) for v in p3)}}} }}"
        )

    width_lines = []
    for start in range(0, len(route_widths), 8):
        width_lines.append(
            "    " + ", ".join(_c_float(v) for v in route_widths[start:start + 8])
        )

    lines = [
        "/* Generated by tools/route_graph_format/export_runtime_route_header.py. Do not edit. */",
        "#ifndef BOONTA_GENERATED_RUNTIME_ROUTE_GRAPH_H",
        "#define BOONTA_GENERATED_RUNTIME_ROUTE_GRAPH_H",
        "",
        '#include "route_cursor.h"',
        "",
        f"#define BOONTA_RUNTIME_ROUTE_NODE_COUNT {len(graph['nodes'])}U",
        f"#define BOONTA_RUNTIME_ROUTE_EDGE_COUNT {len(ordered_edges)}U",
        f"#define BOONTA_RUNTIME_ROUTE_START_NODE_INDEX {node_indices[graph['start_node_id']]}U",
        f"#define BOONTA_RUNTIME_ROUTE_CLOSED_LOOP {1 if graph['closed_loop'] else 0}",
        f"#define BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS {distance_subdivisions}U",
        f"#define BOONTA_RUNTIME_ROUTE_WIDTH_SAMPLES_PER_EDGE {WIDTH_SAMPLES_PER_EDGE}U",
        "#define BOONTA_RUNTIME_ROUTE_WIDTH_SAMPLE_COUNT \\",
        "    (BOONTA_RUNTIME_ROUTE_EDGE_COUNT * BOONTA_RUNTIME_ROUTE_WIDTH_SAMPLES_PER_EDGE)",
        f"#define BOONTA_RUNTIME_ROUTE_LENGTH {_c_float(route_length)}",
        "",
        "typedef struct {",
        "    float p0[3];",
        "    float control1[3];",
        "    float control2[3];",
        "    float p3[3];",
        "} BoontaRuntimeRouteEdge;",
        "",
        "static const BoontaRouteCursorEdge boonta_runtime_route_topology_edges[BOONTA_RUNTIME_ROUTE_EDGE_COUNT] = {",
        ",\\n".join(topology_lines),
        "};",
        "",
        "static const BoontaRuntimeRouteEdge boonta_runtime_route_edges[BOONTA_RUNTIME_ROUTE_EDGE_COUNT] = {",
        ",\n".join(edge_lines),
        "};",
        "",
        "static const float boonta_runtime_route_width_samples[BOONTA_RUNTIME_ROUTE_WIDTH_SAMPLE_COUNT] = {",
        ",\n".join(width_lines),
        "};",
        "",
        "#endif /* BOONTA_GENERATED_RUNTIME_ROUTE_GRAPH_H */",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", type=Path)
    parser.add_argument("surface_widths", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--default-half-width", type=float, default=3.6)
    parser.add_argument(
        "--distance-subdivisions",
        type=int,
        default=DEFAULT_DISTANCE_SUBDIVISIONS,
    )
    args = parser.parse_args()
    try:
        graph_data = json.loads(args.graph.read_text(encoding="utf-8"))
        widths_data = json.loads(args.surface_widths.read_text(encoding="utf-8"))
        header = generate_runtime_route_header(
            graph_data,
            widths_data,
            default_half_width=args.default_half_width,
            distance_subdivisions=args.distance_subdivisions,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"runtime route export error: {exc}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(header, encoding="utf-8", newline="\n")
    print(
        f"Wrote {args.output}: {len(graph_data['edges'])} edges, "
        f"{args.distance_subdivisions} distance intervals per edge"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
