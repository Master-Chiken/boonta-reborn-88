#!/usr/bin/env python3
"""Validate and exercise the clean-room boonta-route-graph-v1 logical format."""

from __future__ import annotations

import copy
import json
import math
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

FORMAT = "boonta-route-graph-v1"
SCHEMA_VERSION = 1
MAX_NODES = 8192
MAX_EDGES = 16384
MAX_ABS_COORDINATE = 1_000_000.0
EPSILON = 1e-9
DEFAULT_UP = (0.0, 1.0, 0.0)
PLATFORMS = {
    "synthetic", "windows-pc", "n64", "dreamcast",
    "gamecube", "wii", "unknown",
}


class RouteGraphError(ValueError):
    """Raised when a route graph or route operation is invalid."""


def _number(value: Any, label: str, low: float = -MAX_ABS_COORDINATE,
            high: float = MAX_ABS_COORDINATE) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RouteGraphError(f"{label} must be a number")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise RouteGraphError(f"{label} must be finite") from exc
    if not math.isfinite(number) or number < low or number > high:
        raise RouteGraphError(f"{label} must be finite and between {low} and {high}")
    return number


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 64:
        raise RouteGraphError(f"{label} must be a non-empty string of at most 64 characters")
    def ascii_alnum(character: str) -> bool:
        return ("A" <= character <= "Z") or ("a" <= character <= "z") or ("0" <= character <= "9")

    if not (ascii_alnum(value[0]) or value[0] == "_"):
        raise RouteGraphError(f"{label} must start with an ASCII letter, digit or underscore")
    if any(not (ascii_alnum(character) or character in "_.:-") for character in value):
        raise RouteGraphError(f"{label} contains an unsupported character")
    return value


def _vec3(value: Any, label: str) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        raise RouteGraphError(f"{label} must contain exactly three numbers")
    return tuple(_number(component, f"{label}[{index}]")
                 for index, component in enumerate(value))


def _validate_json_value(value: Any, label: str) -> None:
    """Reject Python-only values and non-finite numbers inside opaque JSON metadata."""
    if value is None or isinstance(value, (str, bool)):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise RouteGraphError(f"{label} contains a non-finite JSON number")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{label}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise RouteGraphError(f"{label} contains a non-string object key")
            _validate_json_value(item, f"{label}.{key}")
        return
    raise RouteGraphError(f"{label} contains a value that is not JSON-compatible")


def _metadata(value: Any, label: str) -> None:
    if not isinstance(value, dict):
        raise RouteGraphError(f"{label} must be an object when present")
    _validate_json_value(value, label)


def _same(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=0.0, abs_tol=EPSILON)


def _uniform_cubic_bspline_position(
    points: list[tuple[float, float, float]], t: float
) -> tuple[float, float, float]:
    """Evaluate one uniform cubic B-spline position for four control points."""
    weights = (
        (1.0 - t) ** 3 / 6.0,
        (3.0 * t ** 3 - 6.0 * t ** 2 + 4.0) / 6.0,
        (-3.0 * t ** 3 + 3.0 * t ** 2 + 3.0 * t + 1.0) / 6.0,
        t ** 3 / 6.0,
    )
    return tuple(
        sum(points[index][axis] * weights[index] for index in range(4))
        for axis in range(3)
    )


def validate_route_graph(data: Any) -> dict[str, Any]:
    """Validate structure, graph links, normalized progress and surface bindings."""
    if not isinstance(data, dict):
        raise RouteGraphError("route graph root must be an object")
    allowed_root = {
        "format", "schema_version", "route_id", "name", "source", "units",
        "closed_loop", "start_node_id", "nodes", "edges", "metadata",
    }
    unknown_root = set(data) - allowed_root
    if unknown_root:
        raise RouteGraphError(f"unknown root fields: {sorted(unknown_root)}")
    if data.get("format") != FORMAT:
        raise RouteGraphError(f"format must equal {FORMAT!r}")
    version = data.get("schema_version")
    if isinstance(version, bool) or version != SCHEMA_VERSION:
        raise RouteGraphError(f"schema_version must equal {SCHEMA_VERSION}")
    _identifier(data.get("route_id"), "route_id")
    name = data.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 80:
        raise RouteGraphError("name must be a non-empty string of at most 80 characters")

    source = data.get("source")
    if not isinstance(source, dict):
        raise RouteGraphError("source must be an object")
    if set(source) - {"platform", "release", "revision"}:
        raise RouteGraphError("source contains unsupported fields")
    platform = source.get("platform")
    if not isinstance(platform, str) or platform not in PLATFORMS:
        raise RouteGraphError(f"source.platform must be one of {sorted(PLATFORMS)}")
    for field in ("release", "revision"):
        if field in source and (
            not isinstance(source[field], str) or not source[field].strip()
            or len(source[field]) > 120
        ):
            raise RouteGraphError(f"source.{field} must be a non-empty string when present")

    units = data.get("units")
    expected_units = {
        "distance": "metres",
        "lateral_axis": "x",
        "up_axis": "y",
        "forward_axis": "z",
    }
    if units != expected_units:
        raise RouteGraphError(f"units must equal {expected_units!r}")

    closed_loop = data.get("closed_loop")
    if not isinstance(closed_loop, bool):
        raise RouteGraphError("closed_loop must be a boolean")
    start_node_id = _identifier(data.get("start_node_id"), "start_node_id")
    if "metadata" in data:
        _metadata(data["metadata"], "metadata")

    raw_nodes = data.get("nodes")
    raw_edges = data.get("edges")
    if not isinstance(raw_nodes, list) or not 2 <= len(raw_nodes) <= MAX_NODES:
        raise RouteGraphError(f"nodes must contain between 2 and {MAX_NODES} items")
    if not isinstance(raw_edges, list) or not 1 <= len(raw_edges) <= MAX_EDGES:
        raise RouteGraphError(f"edges must contain between 1 and {MAX_EDGES} items")

    nodes: dict[str, dict[str, Any]] = {}
    allowed_node = {"id", "position", "up", "metadata"}
    for index, raw in enumerate(raw_nodes):
        if not isinstance(raw, dict):
            raise RouteGraphError(f"nodes[{index}] must be an object")
        extra = set(raw) - allowed_node
        if extra:
            if "half_width" in extra:
                raise RouteGraphError("route nodes do not store half_width; surface geometry is separate")
            raise RouteGraphError(f"nodes[{index}] has unsupported fields: {sorted(extra)}")
        node_id = _identifier(raw.get("id"), f"nodes[{index}].id")
        if node_id in nodes:
            raise RouteGraphError(f"duplicate node id: {node_id}")
        node = {
            "id": node_id,
            "position": _vec3(raw.get("position"), f"nodes[{index}].position"),
        }
        if "up" in raw:
            up = _vec3(raw["up"], f"nodes[{index}].up")
            if math.sqrt(sum(component * component for component in up)) <= EPSILON:
                raise RouteGraphError(f"nodes[{index}].up must not be zero")
            node["up"] = up
        if "metadata" in raw:
            _metadata(raw["metadata"], f"nodes[{index}].metadata")
            node["metadata"] = copy.deepcopy(raw["metadata"])
        nodes[node_id] = node

    if start_node_id not in nodes:
        raise RouteGraphError(f"start_node_id references missing node {start_node_id!r}")

    edges: dict[str, dict[str, Any]] = {}
    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming: dict[str, list[str]] = defaultdict(list)
    referenced_control_nodes: set[str] = set()
    allowed_edge = {
        "id", "from", "to", "curve", "progress", "surface_binding", "metadata",
    }

    for index, raw in enumerate(raw_edges):
        if not isinstance(raw, dict):
            raise RouteGraphError(f"edges[{index}] must be an object")
        extra = set(raw) - allowed_edge
        if extra:
            if "half_width" in extra:
                raise RouteGraphError("route edges do not store half_width; surface geometry is separate")
            raise RouteGraphError(f"edges[{index}] has unsupported fields: {sorted(extra)}")
        edge_id = _identifier(raw.get("id"), f"edges[{index}].id")
        if edge_id in edges:
            raise RouteGraphError(f"duplicate edge id: {edge_id}")
        from_id = _identifier(raw.get("from"), f"edges[{index}].from")
        to_id = _identifier(raw.get("to"), f"edges[{index}].to")
        if from_id not in nodes or to_id not in nodes:
            missing = from_id if from_id not in nodes else to_id
            raise RouteGraphError(f"edge {edge_id!r} references missing node {missing!r}")
        if from_id == to_id:
            raise RouteGraphError(f"edge {edge_id!r} cannot connect a node to itself")

        curve = raw.get("curve")
        if not isinstance(curve, dict):
            raise RouteGraphError(f"edge {edge_id!r}.curve must be an object")
        curve_type = curve.get("type")
        if curve_type == "cubic_bezier":
            if set(curve) != {"type", "control1", "control2"}:
                raise RouteGraphError(
                    f"edge {edge_id!r} cubic_bezier curve requires only control1 and control2"
                )
            normalized_curve = {
                "type": curve_type,
                "control1": list(_vec3(curve.get("control1"), f"edge {edge_id}.control1")),
                "control2": list(_vec3(curve.get("control2"), f"edge {edge_id}.control2")),
            }
        elif curve_type == "uniform_cubic_bspline":
            if set(curve) != {"type", "control_node_ids"}:
                raise RouteGraphError(
                    f"edge {edge_id!r} uniform_cubic_bspline requires control_node_ids"
                )
            ids = curve.get("control_node_ids")
            if not isinstance(ids, list) or len(ids) != 4:
                raise RouteGraphError(f"edge {edge_id!r} B-spline requires four control_node_ids")
            normalized_ids = [
                _identifier(value, f"edge {edge_id}.control_node_ids[{slot}]")
                for slot, value in enumerate(ids)
            ]
            missing_ids = [value for value in normalized_ids if value not in nodes]
            if missing_ids:
                raise RouteGraphError(
                    f"edge {edge_id!r} B-spline references missing node {missing_ids[0]!r}"
                )
            # Graph from/to links and the four-point curve window are separate
            # logical fields. The PC cursor shifts its full lookahead window at
            # boundaries; no generic edge-to-control-index mapping is assumed.
            referenced_control_nodes.update(normalized_ids)
            normalized_curve = {
                "type": curve_type,
                "control_node_ids": normalized_ids,
            }
            control_positions = [nodes[item]["position"] for item in normalized_ids]
            curve_start = _uniform_cubic_bspline_position(control_positions, 0.0)
            curve_end = _uniform_cubic_bspline_position(control_positions, 1.0)
            for endpoint_id, curve_position, endpoint_label in (
                (from_id, curve_start, "start"),
                (to_id, curve_end, "end"),
            ):
                endpoint_position = nodes[endpoint_id]["position"]
                if not all(
                    _same(endpoint_position[axis], curve_position[axis])
                    for axis in range(3)
                ):
                    raise RouteGraphError(
                        f"edge {edge_id!r} B-spline {endpoint_label} does not meet "
                        f"topology node {endpoint_id!r}"
                    )
        else:
            raise RouteGraphError(
                f"edge {edge_id!r} curve.type must be cubic_bezier or uniform_cubic_bspline"
            )

        progress = raw.get("progress")
        if not isinstance(progress, dict) or set(progress) != {"start", "end"}:
            raise RouteGraphError(f"edge {edge_id!r}.progress must contain start and end")
        progress_start = _number(progress.get("start"), f"edge {edge_id}.progress.start", 0.0, 1.0)
        progress_end = _number(progress.get("end"), f"edge {edge_id}.progress.end", 0.0, 1.0)
        if progress_end - progress_start <= EPSILON:
            raise RouteGraphError(f"edge {edge_id!r} progress must increase from start to end")

        normalized_edge: dict[str, Any] = {
            "id": edge_id,
            "from": from_id,
            "to": to_id,
            "curve": normalized_curve,
            "progress": {"start": progress_start, "end": progress_end},
        }

        if "surface_binding" in raw:
            bindings = raw["surface_binding"]
            if not isinstance(bindings, list) or len(bindings) < 2:
                raise RouteGraphError(
                    f"edge {edge_id!r}.surface_binding must contain at least two samples"
                )
            normalized_bindings = []
            previous_t = -1.0
            for sample_index, sample in enumerate(bindings):
                if not isinstance(sample, dict) or set(sample) != {"t", "surface_id"}:
                    raise RouteGraphError(
                        f"edge {edge_id!r}.surface_binding[{sample_index}] requires t and surface_id"
                    )
                sample_t = _number(
                    sample.get("t"), f"edge {edge_id}.surface_binding[{sample_index}].t", 0.0, 1.0
                )
                surface_id = _identifier(
                    sample.get("surface_id"),
                    f"edge {edge_id}.surface_binding[{sample_index}].surface_id",
                )
                if sample_t - previous_t <= EPSILON:
                    raise RouteGraphError(
                        f"edge {edge_id!r} surface sample t values must be strictly increasing"
                    )
                previous_t = sample_t
                normalized_bindings.append({"t": sample_t, "surface_id": surface_id})
            if not _same(normalized_bindings[0]["t"], 0.0) or not _same(
                normalized_bindings[-1]["t"], 1.0
            ):
                raise RouteGraphError(
                    f"edge {edge_id!r} surface bindings must include t=0 and t=1"
                )
            normalized_edge["surface_binding"] = normalized_bindings

        if "metadata" in raw:
            _metadata(raw["metadata"], f"edge {edge_id}.metadata")
            normalized_edge["metadata"] = copy.deepcopy(raw["metadata"])

        edges[edge_id] = normalized_edge
        outgoing[from_id].append(edge_id)
        incoming[to_id].append(edge_id)

    topology_nodes = {start_node_id}
    for edge in edges.values():
        topology_nodes.update((edge["from"], edge["to"]))
    control_only = set(nodes) - topology_nodes
    if control_only - referenced_control_nodes:
        unknown = sorted(control_only - referenced_control_nodes)[0]
        raise RouteGraphError(f"node {unknown!r} is neither route topology nor a B-spline control node")

    # Every authored route edge must be reachable from the chosen start node.
    reached_nodes = {start_node_id}
    reached_edges: set[str] = set()
    queue = deque([start_node_id])
    while queue:
        node_id = queue.popleft()
        for edge_id in outgoing.get(node_id, []):
            reached_edges.add(edge_id)
            target = edges[edge_id]["to"]
            if target not in reached_nodes:
                reached_nodes.add(target)
                queue.append(target)
    if reached_edges != set(edges):
        unreachable = sorted(set(edges) - reached_edges)[0]
        raise RouteGraphError(f"edge {unreachable!r} is unreachable from start_node_id")

    # Progress is a graph coordinate: all paths share the same value at a split/rejoin.
    for node_id in topology_nodes:
        in_edges = [edges[item] for item in incoming.get(node_id, [])]
        out_edges = [edges[item] for item in outgoing.get(node_id, [])]
        incoming_values = [edge["progress"]["end"] for edge in in_edges]
        outgoing_values = [edge["progress"]["start"] for edge in out_edges]

        if node_id == start_node_id:
            if not out_edges:
                raise RouteGraphError("start_node_id must have an outgoing edge")
            if closed_loop:
                if not in_edges:
                    raise RouteGraphError("closed loop start node must have an incoming edge")
                if not all(_same(value, 1.0) for value in incoming_values):
                    raise RouteGraphError("closed loop incoming progress at start must end at 1.0")
            elif in_edges:
                raise RouteGraphError("open route start_node_id must not have incoming edges")
            if not all(_same(value, 0.0) for value in outgoing_values):
                raise RouteGraphError("start node outgoing progress must start at 0.0")
            continue

        if not out_edges:
            if closed_loop:
                raise RouteGraphError(f"closed-loop node {node_id!r} has no outgoing edge")
            if not in_edges or not all(_same(value, 1.0) for value in incoming_values):
                raise RouteGraphError(f"open route terminal node {node_id!r} must end at progress 1.0")
            continue

        if not in_edges:
            raise RouteGraphError(f"route node {node_id!r} has outgoing but no incoming edges")
        if not all(_same(value, incoming_values[0]) for value in incoming_values):
            raise RouteGraphError(f"node {node_id!r} has inconsistent incoming progress at rejoin")
        if not all(_same(value, outgoing_values[0]) for value in outgoing_values):
            raise RouteGraphError(f"node {node_id!r} has inconsistent outgoing progress at split")
        if not _same(incoming_values[0], outgoing_values[0]):
            raise RouteGraphError(f"node {node_id!r} progress is discontinuous")

    normalized = copy.deepcopy(data)
    normalized["nodes"] = [
        {"id": node_id, "position": list(node["position"]),
         **({"up": list(node["up"])} if "up" in node else {}),
         **({"metadata": copy.deepcopy(node["metadata"])} if "metadata" in node else {})}
        for node_id, node in nodes.items()
    ]
    normalized["edges"] = list(edges.values())
    return normalized


def _normalise(vector: tuple[float, float, float], label: str) -> tuple[float, float, float]:
    length = math.sqrt(sum(component * component for component in vector))
    if not math.isfinite(length) or length <= EPSILON:
        raise RouteGraphError(f"{label} is degenerate")
    return tuple(component / length for component in vector)


def _add_scaled(a: tuple[float, float, float],
                b: tuple[float, float, float],
                scale: float) -> tuple[float, float, float]:
    return tuple(a[index] + b[index] * scale for index in range(3))


def _evaluate_edge_validated(
    graph: dict[str, Any], edge_id: str, t: float
) -> dict[str, tuple[float, float, float]]:
    """Evaluate one segment from an already validated graph."""
    if edge_id not in {edge["id"] for edge in graph["edges"]}:
        raise RouteGraphError(f"unknown edge id {edge_id!r}")
    t = _number(t, "t", 0.0, 1.0)
    nodes = {node["id"]: node for node in graph["nodes"]}
    edge = next(item for item in graph["edges"] if item["id"] == edge_id)
    curve = edge["curve"]

    if curve["type"] == "cubic_bezier":
        p0 = tuple(nodes[edge["from"]]["position"])
        p1 = tuple(curve["control1"])
        p2 = tuple(curve["control2"])
        p3 = tuple(nodes[edge["to"]]["position"])
        one_minus = 1.0 - t
        weights = (one_minus ** 3, 3.0 * one_minus ** 2 * t,
                   3.0 * one_minus * t ** 2, t ** 3)
        position = tuple(
            p0[axis] * weights[0] + p1[axis] * weights[1]
            + p2[axis] * weights[2] + p3[axis] * weights[3]
            for axis in range(3)
        )
        tangent_raw = tuple(
            3.0 * (
                one_minus ** 2 * (p1[axis] - p0[axis])
                + 2.0 * one_minus * t * (p2[axis] - p1[axis])
                + t ** 2 * (p3[axis] - p2[axis])
            )
            for axis in range(3)
        )
        from_id, to_id = edge["from"], edge["to"]
    else:
        control_nodes = [nodes[item] for item in curve["control_node_ids"]]
        points = [tuple(item["position"]) for item in control_nodes]
        weights = (
            (1.0 - t) ** 3 / 6.0,
            (3.0 * t ** 3 - 6.0 * t ** 2 + 4.0) / 6.0,
            (-3.0 * t ** 3 + 3.0 * t ** 2 + 3.0 * t + 1.0) / 6.0,
            t ** 3 / 6.0,
        )
        derivatives = (
            -0.5 * (1.0 - t) ** 2,
            (9.0 * t ** 2 - 12.0 * t) / 6.0,
            (-9.0 * t ** 2 + 6.0 * t + 3.0) / 6.0,
            0.5 * t ** 2,
        )
        position = tuple(
            sum(points[index][axis] * weights[index] for index in range(4))
            for axis in range(3)
        )
        tangent_raw = tuple(
            sum(points[index][axis] * derivatives[index] for index in range(4))
            for axis in range(3)
        )
        from_id, to_id = edge["from"], edge["to"]

    tangent = _normalise(tangent_raw, f"edge {edge_id!r} tangent")
    from_up = nodes[from_id].get("up", DEFAULT_UP)
    to_up = nodes[to_id].get("up", DEFAULT_UP)
    up_hint = tuple(
        from_up[axis] * (1.0 - t) + to_up[axis] * t for axis in range(3)
    )
    up_hint_length = math.sqrt(sum(component * component for component in up_hint))
    if up_hint_length <= EPSILON:
        up_hint = DEFAULT_UP
    projection = sum(up_hint[axis] * tangent[axis] for axis in range(3))
    up_raw = tuple(up_hint[axis] - projection * tangent[axis] for axis in range(3))
    if math.sqrt(sum(component * component for component in up_raw)) <= EPSILON:
        fallback = (1.0, 0.0, 0.0) if abs(tangent[0]) < 0.9 else (0.0, 0.0, 1.0)
        projection = sum(fallback[axis] * tangent[axis] for axis in range(3))
        up_raw = tuple(fallback[axis] - projection * tangent[axis] for axis in range(3))
    up = _normalise(up_raw, f"edge {edge_id!r} up")
    return {"position": position, "tangent": tangent, "up": up}


def evaluate_edge(
    graph_data: Any, edge_id: str, t: float
) -> dict[str, tuple[float, float, float]]:
    """Validate and evaluate one cubic segment."""
    graph = validate_route_graph(graph_data)
    return _evaluate_edge_validated(graph, edge_id, t)

def progress_at(graph_data: Any, edge_id: str, t: float) -> float:
    graph = validate_route_graph(graph_data)
    t = _number(t, "t", 0.0, 1.0)
    for edge in graph["edges"]:
        if edge["id"] == edge_id:
            start = edge["progress"]["start"]
            end = edge["progress"]["end"]
            return start + (end - start) * t
    raise RouteGraphError(f"unknown edge id {edge_id!r}")


def sample_edge_length(graph_data: Any, edge_id: str, samples: int = 100) -> float:
    if isinstance(samples, bool) or not isinstance(samples, int) or samples < 2 or samples > 10000:
        raise RouteGraphError("samples must be an integer from 2 to 10000")
    graph = validate_route_graph(graph_data)
    previous = _evaluate_edge_validated(graph, edge_id, 0.0)["position"]
    length = 0.0
    for index in range(1, samples + 1):
        current = _evaluate_edge_validated(graph, edge_id, index / samples)["position"]
        length += math.sqrt(sum((current[axis] - previous[axis]) ** 2 for axis in range(3)))
        previous = current
    if not math.isfinite(length) or length <= EPSILON:
        raise RouteGraphError(f"edge {edge_id!r} has zero or invalid sampled length")
    return length


def allocate_progress_spans(
    lengths: list[float], start: float, end: float
) -> list[dict[str, float]]:
    """Split one shared normalized progress band in proportion to sampled edge lengths."""
    if not isinstance(lengths, list) or not lengths:
        raise RouteGraphError("lengths must be a non-empty array")
    start = _number(start, "progress start", 0.0, 1.0)
    end = _number(end, "progress end", 0.0, 1.0)
    if end - start <= EPSILON:
        raise RouteGraphError("progress band must increase")
    normalized = [_number(value, f"lengths[{index}]", 0.0)
                  for index, value in enumerate(lengths)]
    if any(value <= EPSILON for value in normalized):
        raise RouteGraphError("all edge lengths must be greater than zero")
    total = math.fsum(normalized)
    if not math.isfinite(total) or total <= EPSILON:
        raise RouteGraphError("total edge length must be finite and positive")
    span = end - start
    result = []
    cursor = start
    for index, length in enumerate(normalized):
        next_value = end if index == len(normalized) - 1 else cursor + span * (length / total)
        result.append({"start": cursor, "end": next_value})
        cursor = next_value
    return result


class RouteCursor:
    """Host-test cursor with explicit path history and deterministic branch choices."""

    def __init__(self, graph_data: Any, start_edge_id: str | None = None):
        self.graph = validate_route_graph(graph_data)
        self.edges = {edge["id"]: edge for edge in self.graph["edges"]}
        self.outgoing: dict[str, list[str]] = defaultdict(list)
        for edge in self.graph["edges"]:
            self.outgoing[edge["from"]].append(edge["id"])
        candidates = self.outgoing.get(self.graph["start_node_id"], [])
        if start_edge_id is None:
            if len(candidates) != 1:
                raise RouteGraphError("start_edge_id is required when the start node is branched")
            start_edge_id = candidates[0]
        if start_edge_id not in candidates:
            raise RouteGraphError("start_edge_id must leave start_node_id")
        self.path_history = [start_edge_id]
        self.path_index = 0
        self.t = 0.0
        self.finished = False
        self.started = True

    @property
    def edge_id(self) -> str:
        return self.path_history[self.path_index]

    def move(
        self, delta_parameter: float, branch_choices: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Advance by local edge parameter t, not by distance or elapsed time."""
        delta_parameter = _number(delta_parameter, "delta_parameter")
        if branch_choices is None:
            branch_choices = {}
        if not isinstance(branch_choices, dict):
            raise RouteGraphError("branch_choices must be an object keyed by node id")

        old_state = (self.path_history[:], self.path_index, self.t, self.finished, self.started)
        try:
            self.t += delta_parameter
            if delta_parameter < 0.0:
                self.finished = False
            transitions = 0
            while self.t > 1.0 + EPSILON:
                transitions += 1
                if transitions > 10000:
                    raise RouteGraphError("cursor transition limit exceeded")
                current = self.edges[self.edge_id]
                node_id = current["to"]
                candidates = self.outgoing.get(node_id, [])
                if not candidates:
                    if self.graph["closed_loop"] and node_id == self.graph["start_node_id"]:
                        candidates = self.outgoing.get(self.graph["start_node_id"], [])
                    if not candidates:
                        self.t = 1.0
                        self.finished = True
                        break

                requested = branch_choices.get(node_id)
                cached = (
                    self.path_history[self.path_index + 1]
                    if self.path_index + 1 < len(self.path_history) else None
                )
                append_history = False
                if requested is not None:
                    if requested not in candidates:
                        raise RouteGraphError(
                            f"branch choice {requested!r} is not an outgoing edge of node {node_id!r}"
                        )
                    chosen = requested
                    if cached != requested:
                        self.path_history = self.path_history[: self.path_index + 1]
                        append_history = True
                elif cached is not None:
                    if cached not in candidates:
                        raise RouteGraphError("stored branch history no longer matches graph topology")
                    chosen = cached
                elif len(candidates) == 1:
                    chosen = candidates[0]
                    append_history = True
                else:
                    raise RouteGraphError(f"branch choice required at node {node_id!r}")

                if append_history:
                    self.path_history.append(chosen)
                self.path_index += 1
                self.t -= 1.0
                self.finished = False

            while self.t < -EPSILON:
                transitions += 1
                if transitions > 10000:
                    raise RouteGraphError("cursor transition limit exceeded")
                if self.path_index == 0:
                    self.t = 0.0
                    self.started = True
                    break
                current = self.edges[self.edge_id]
                previous_id = self.path_history[self.path_index - 1]
                previous = self.edges[previous_id]
                if previous["to"] != current["from"]:
                    raise RouteGraphError("stored reverse path history is not connected")
                self.path_index -= 1
                self.t += 1.0
                self.finished = False

            if -EPSILON <= self.t < 0.0:
                self.t = 0.0
            if 1.0 < self.t <= 1.0 + EPSILON:
                self.t = 1.0
            if self.t < 0.0 or self.t > 1.0:
                raise RouteGraphError("cursor parameter escaped [0, 1]")
        except Exception:
            (
                self.path_history, self.path_index, self.t,
                self.finished, self.started,
            ) = old_state
            raise

        return {
            "edge_id": self.edge_id,
            "t": self.t,
            "progress": progress_at(self.graph, self.edge_id, self.t),
            "finished": self.finished,
            "at_start": self.path_index == 0 and _same(self.t, 0.0),
            "path_history": tuple(self.path_history),
            "path_index": self.path_index,
        }


def load_route_graph(path: str | Path) -> dict[str, Any]:
    try:
        with Path(path).open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RouteGraphError(f"cannot read valid JSON: {exc}") from exc
    return validate_route_graph(data)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} ROUTE_GRAPH.json", file=sys.stderr)
        return 2
    try:
        graph = load_route_graph(argv[1])
    except RouteGraphError as exc:
        print(f"invalid route graph: {exc}", file=sys.stderr)
        return 1
    print(
        f"valid {graph['format']}: {graph['route_id']} "
        f"({len(graph['nodes'])} nodes, {len(graph['edges'])} edges, "
        f"{'closed loop' if graph['closed_loop'] else 'open route'})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
