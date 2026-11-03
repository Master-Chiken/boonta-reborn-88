#!/usr/bin/env python3
"""Bake a simple closed route graph into the existing boonta-track-v1 runtime format.

This is an offline compatibility bridge, not a runtime graph loader. Branching
routes remain in boonta-route-graph-v1 and are rejected rather than flattened.
"""

from __future__ import annotations

from bisect import bisect_left
import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
TRACK_FORMAT_DIR = HERE.parent / "track_format"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TRACK_FORMAT_DIR))

from validate_route_graph import (  # noqa: E402
    RouteGraphError,
    _evaluate_edge_validated,
    _index_validated_graph,
    validate_route_graph,
)
from validate_track import TrackValidationError, validate_track  # noqa: E402

MAX_TRACK_POINTS = 4096
MIN_HALF_WIDTH = 0.5
MAX_HALF_WIDTH = 100.0
EPSILON = 1e-9
MIN_ARC_LOOKUP_SAMPLES = 128
MAX_ARC_LOOKUP_SAMPLES = 8192


class RouteGraphExportError(ValueError):
    """Raised when a valid logical graph cannot be represented by track v1."""


def _checked_half_width(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RouteGraphExportError(f"{label} must be a number")
    try:
        width = float(value)
    except (OverflowError, ValueError) as exc:
        raise RouteGraphExportError(f"{label} must be finite") from exc
    if not math.isfinite(width) or not MIN_HALF_WIDTH <= width <= MAX_HALF_WIDTH:
        raise RouteGraphExportError(
            f"{label} must be finite and between {MIN_HALF_WIDTH} and {MAX_HALF_WIDTH}"
        )
    return width


def _ordered_single_loop(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Return edges in traversal order, rejecting splits, rejoins and extra cycles."""
    if not graph["closed_loop"]:
        raise RouteGraphExportError(
            "the GameCube/Wii track-v1 bake currently requires closed_loop=true"
        )

    outgoing: dict[str, list[dict[str, Any]]] = {
        node["id"]: [] for node in graph["nodes"]
    }
    incoming: dict[str, list[dict[str, Any]]] = {
        node["id"]: [] for node in graph["nodes"]
    }
    topology_nodes: set[str] = set()
    for edge in graph["edges"]:
        outgoing[edge["from"]].append(edge)
        incoming[edge["to"]].append(edge)
        topology_nodes.update((edge["from"], edge["to"]))

    for node_id in topology_nodes:
        if len(outgoing[node_id]) != 1 or len(incoming[node_id]) != 1:
            raise RouteGraphExportError(
                "the track-v1 runtime bake requires one incoming and one outgoing "
                f"edge per route node; branching/rejoining node {node_id!r} "
                "must remain in route-graph form"
            )

    ordered: list[dict[str, Any]] = []
    visited_nodes: set[str] = set()
    current = graph["start_node_id"]
    while current not in visited_nodes:
        visited_nodes.add(current)
        edge = outgoing[current][0]
        ordered.append(edge)
        current = edge["to"]

    if current != graph["start_node_id"]:
        raise RouteGraphExportError("route traversal enters a cycle that does not return to start")
    if visited_nodes != topology_nodes or len(ordered) != len(graph["edges"]):
        raise RouteGraphExportError("route graph contains topology outside the start/finish loop")
    return ordered



def _arc_length_parameters(
    graph: dict[str, Any],
    edge_id: str,
    samples_per_edge: int,
    nodes_by_id: dict[str, dict[str, Any]],
    edges_by_id: dict[str, dict[str, Any]],
) -> list[float]:
    """Approximate equal-distance curve parameters using a bounded lookup table.

    The lookup is local to one edge. Output still omits t=1 so the next edge
    owns the shared topology node, exactly as in parameter-space sampling.
    """
    lookup_samples = max(
        MIN_ARC_LOOKUP_SAMPLES,
        min(MAX_ARC_LOOKUP_SAMPLES, samples_per_edge * 16),
    )
    previous = _evaluate_edge_validated(
        graph, edge_id, 0.0, nodes_by_id, edges_by_id
    )["position"]
    cumulative_lengths = [0.0]
    total_length = 0.0

    for lookup_index in range(1, lookup_samples + 1):
        t = lookup_index / lookup_samples
        position = _evaluate_edge_validated(
            graph, edge_id, t, nodes_by_id, edges_by_id
        )["position"]
        step_length = math.dist(previous, position)
        if not math.isfinite(step_length):
            raise RouteGraphExportError(
                f"edge {edge_id!r} produced a non-finite arc-length lookup step"
            )
        total_length += step_length
        cumulative_lengths.append(total_length)
        previous = position

    if not math.isfinite(total_length) or total_length <= EPSILON:
        raise RouteGraphExportError(
            f"edge {edge_id!r} has no measurable length for arc-length sampling"
        )

    parameters: list[float] = []
    for sample_index in range(samples_per_edge):
        target_length = total_length * sample_index / samples_per_edge
        upper = bisect_left(cumulative_lengths, target_length)
        if upper <= 0:
            parameters.append(0.0)
            continue
        if upper >= len(cumulative_lengths):
            parameters.append(1.0)
            continue

        lower_length = cumulative_lengths[upper - 1]
        span_length = cumulative_lengths[upper] - lower_length
        if span_length <= EPSILON:
            # A repeated lookup position carries no distance; keep the nearest
            # upper parameter rather than dividing by a degenerate span.
            parameters.append(upper / lookup_samples)
            continue
        fraction = (target_length - lower_length) / span_length
        parameters.append(((upper - 1) + fraction) / lookup_samples)

    return parameters


def export_closed_loop_track(
    graph_data: Any,
    *,
    default_half_width: float,
    samples_per_edge: int = 24,
    surface_widths: dict[str, Any] | None = None,
    sampling_mode: str = "parameter",
) -> dict[str, Any]:
    """Convert a simple closed route into sampled track-v1 control points.

    Parameter-space sampling remains the compatibility default. Arc-length mode
    inverts a bounded per-edge distance lookup so the runtime's chord-based
    sampler receives more evenly spaced points on curved edges. The next edge
    owns the shared topology node; road widths remain separate geometry data.
    """
    graph = validate_route_graph(graph_data)
    default_width = _checked_half_width(default_half_width, "default_half_width")

    if isinstance(samples_per_edge, bool) or not isinstance(samples_per_edge, int):
        raise RouteGraphExportError("samples_per_edge must be an integer")
    if samples_per_edge < 2 or samples_per_edge > 2048:
        raise RouteGraphExportError("samples_per_edge must be between 2 and 2048")
    if sampling_mode not in ("parameter", "arc_length"):
        raise RouteGraphExportError(
            "sampling_mode must be 'parameter' or 'arc_length'"
        )

    ordered_edges = _ordered_single_loop(graph)
    point_count = len(ordered_edges) * samples_per_edge
    if point_count > MAX_TRACK_POINTS:
        raise RouteGraphExportError(
            f"bake would produce {point_count} points; track-v1 limit is {MAX_TRACK_POINTS}"
        )

    if surface_widths is None:
        surface_widths = {}
    if not isinstance(surface_widths, dict):
        raise RouteGraphExportError("surface_widths must be an object mapping surface IDs to widths")

    checked_surface_widths: dict[str, float] = {}
    for surface_id, width in surface_widths.items():
        if not isinstance(surface_id, str) or not surface_id:
            raise RouteGraphExportError("surface_widths keys must be non-empty surface IDs")
        checked_surface_widths[surface_id] = _checked_half_width(
            width, f"surface_widths[{surface_id!r}]"
        )

    nodes_by_id, edges_by_id = _index_validated_graph(graph)
    points: list[dict[str, Any]] = []

    for edge_index, edge in enumerate(ordered_edges):
        edge_id = edge["id"]
        bindings = edge.get("surface_binding", [])
        binding_index = 0
        sample_parameters = (
            [sample_index / samples_per_edge for sample_index in range(samples_per_edge)]
            if sampling_mode == "parameter"
            else _arc_length_parameters(
                graph, edge_id, samples_per_edge, nodes_by_id, edges_by_id
            )
        )

        for sample_index, t in enumerate(sample_parameters):
            while (
                bindings
                and binding_index + 1 < len(bindings)
                and t + EPSILON >= bindings[binding_index + 1]["t"]
            ):
                binding_index += 1

            if bindings:
                surface_id = bindings[binding_index]["surface_id"]
                if surface_id not in checked_surface_widths:
                    raise RouteGraphExportError(
                        f"edge {edge_id!r} uses surface {surface_id!r}; "
                        "provide its width in --surface-widths JSON"
                    )
                half_width = checked_surface_widths[surface_id]
            else:
                half_width = default_width

            evaluated = _evaluate_edge_validated(
                graph, edge_id, t, nodes_by_id, edges_by_id
            )
            x, y, z = evaluated["position"]
            points.append({
                "x": x,
                "y": y,
                "z": z,
                "half_width": half_width,
                # Track-v1/runtime currently has one lap-distance start reference.
                "checkpoint": edge_index == 0 and sample_index == 0,
            })

    track = {
        "format": "boonta-track-v1",
        "name": graph["name"],
        "closed_loop": True,
        "points": points,
    }
    return validate_track(track)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("route_graph", help="input boonta-route-graph-v1 JSON")
    parser.add_argument("output_track", help="output boonta-track-v1 JSON")
    parser.add_argument(
        "--half-width", type=float, required=True,
        help="explicit default road half-width in metres (0.5..100)",
    )
    parser.add_argument(
        "--samples-per-edge", type=int, default=24,
        help="fixed curve samples per edge (default: 24; track limit: 4096 points)",
    )
    parser.add_argument(
        "--sampling-mode", choices=("parameter", "arc_length"),
        default="parameter",
        help="curve sampling: legacy parameter spacing (default) or approximate equal arc length",
    )
    parser.add_argument(
        "--surface-widths",
        help="optional JSON object mapping surface IDs to half-widths in metres",
    )
    args = parser.parse_args(argv)

    try:
        with Path(args.route_graph).open("r", encoding="utf-8") as stream:
            graph = json.load(stream)
        widths = None
        if args.surface_widths:
            with Path(args.surface_widths).open("r", encoding="utf-8") as stream:
                widths = json.load(stream)
        track = export_closed_loop_track(
            graph,
            default_half_width=args.half_width,
            samples_per_edge=args.samples_per_edge,
            surface_widths=widths,
            sampling_mode=args.sampling_mode,
        )
        output = Path(args.output_track)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(track, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except (
        OSError, json.JSONDecodeError, RouteGraphError,
        RouteGraphExportError, TrackValidationError,
    ) as exc:
        print(f"route-graph export failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"exported {len(track['points'])} sampled points from "
        f"{len(graph['edges'])} route edges to {args.output_track}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
