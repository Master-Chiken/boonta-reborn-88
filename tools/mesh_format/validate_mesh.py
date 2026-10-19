#!/usr/bin/env python3
"""Validate the original, engine-neutral boonta-mesh-v1 JSON format."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

FORMAT = "boonta-mesh-v1"
MAX_VERTICES = 4096
MAX_INDICES = (MAX_VERTICES // 3) * 3
MAX_ABS_COORDINATE = 1_000_000.0


class MeshValidationError(ValueError):
    """Raised when mesh source data is structurally or numerically invalid."""


def _number(value: Any, label: str) -> float:
    # bool is a subclass of int in Python; it is not a valid coordinate.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MeshValidationError(f"{label} must be a number")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise MeshValidationError(f"{label} must be finite") from exc
    if not math.isfinite(number):
        raise MeshValidationError(f"{label} must be finite")
    if number < -MAX_ABS_COORDINATE or number > MAX_ABS_COORDINATE:
        raise MeshValidationError(
            f"{label} must be between {-MAX_ABS_COORDINATE} and {MAX_ABS_COORDINATE}"
        )
    return number


def validate_mesh(data: Any) -> dict[str, Any]:
    """Validate and normalize one original boonta-mesh-v1 document."""
    if not isinstance(data, dict):
        raise MeshValidationError("mesh root must be an object")
    if data.get("format") != FORMAT:
        raise MeshValidationError(f"format must equal {FORMAT!r}")

    name = data.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 80:
        raise MeshValidationError("name must be a non-empty string of at most 80 characters")

    vertices = data.get("vertices")
    if not isinstance(vertices, list):
        raise MeshValidationError("vertices must be an array")
    if len(vertices) < 3:
        raise MeshValidationError("at least 3 vertices are required")
    if len(vertices) > MAX_VERTICES:
        raise MeshValidationError(f"vertex count exceeds limit ({MAX_VERTICES})")

    normalized_vertices = []
    for index, vertex in enumerate(vertices):
        if not isinstance(vertex, dict):
            raise MeshValidationError(f"vertices[{index}] must be an object")
        position = vertex.get("position")
        if not isinstance(position, list) or len(position) != 3:
            raise MeshValidationError(f"vertices[{index}].position must contain exactly 3 numbers")
        coordinates = [
            _number(position[axis], f"vertices[{index}].position[{axis}]")
            for axis in range(3)
        ]

        color = vertex.get("color")
        if not isinstance(color, list) or len(color) != 4:
            raise MeshValidationError(f"vertices[{index}].color must contain four RGBA8 channels")
        channels = []
        for channel_index, channel in enumerate(color):
            if isinstance(channel, bool) or not isinstance(channel, int):
                raise MeshValidationError(
                    f"vertices[{index}].color[{channel_index}] must be an integer"
                )
            if channel < 0 or channel > 255:
                raise MeshValidationError(
                    f"vertices[{index}].color[{channel_index}] must be between 0 and 255"
                )
            channels.append(channel)

        # UVs are optional in v1 so existing authored meshes remain compatible.
        # Missing coordinates normalize to (0, 0), ready for a later GX texture stage.
        uv = vertex.get("uv", [0.0, 0.0])
        if not isinstance(uv, list) or len(uv) != 2:
            raise MeshValidationError(f"vertices[{index}].uv must contain exactly 2 numbers")
        texture_coordinates = [
            _number(uv[axis], f"vertices[{index}].uv[{axis}]")
            for axis in range(2)
        ]

        normalized_vertices.append({
            "position": coordinates,
            "color": channels,
            "uv": texture_coordinates,
        })

    indices = data.get("indices")
    if not isinstance(indices, list):
        raise MeshValidationError("indices must be an array")
    if len(indices) < 3:
        raise MeshValidationError("at least 3 indices are required")
    if len(indices) > MAX_INDICES:
        raise MeshValidationError(f"index count exceeds limit ({MAX_INDICES})")
    if len(indices) % 3 != 0:
        raise MeshValidationError("index count must be a multiple of three")

    normalized_indices = []
    for index, value in enumerate(indices):
        if isinstance(value, bool) or not isinstance(value, int):
            raise MeshValidationError(f"indices[{index}] must be an integer")
        if value < 0 or value >= len(normalized_vertices):
            raise MeshValidationError(
                f"indices[{index}] references a vertex outside the vertex array"
            )
        normalized_indices.append(value)

    # Match the runtime validator: reject zero-area triangles before export.
    for offset in range(0, len(normalized_indices), 3):
        a = normalized_vertices[normalized_indices[offset]]["position"]
        b = normalized_vertices[normalized_indices[offset + 1]]["position"]
        c = normalized_vertices[normalized_indices[offset + 2]]["position"]
        abx, aby, abz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        acx, acy, acz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx = aby * acz - abz * acy
        ny = abz * acx - abx * acz
        nz = abx * acy - aby * acx
        if nx == 0.0 and ny == 0.0 and nz == 0.0:
            raise MeshValidationError(f"triangle at index offset {offset} is degenerate")

    return {
        "format": FORMAT,
        "name": name,
        "vertices": normalized_vertices,
        "indices": normalized_indices,
    }


def load_mesh(path: str | Path) -> dict[str, Any]:
    """Read JSON and validate it, wrapping file/JSON errors consistently."""
    try:
        with Path(path).open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise MeshValidationError(f"cannot read valid JSON: {exc}") from exc
    return validate_mesh(data)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} MESH.json", file=sys.stderr)
        return 2
    try:
        mesh = load_mesh(argv[1])
    except MeshValidationError as exc:
        print(f"invalid mesh: {exc}", file=sys.stderr)
        return 1
    print(
        f"valid {mesh['format']}: {mesh['name']} "
        f"({len(mesh['vertices'])} vertices, {len(mesh['indices'])} indices)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
