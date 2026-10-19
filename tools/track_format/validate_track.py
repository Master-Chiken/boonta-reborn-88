#!/usr/bin/env python3
"""Validate original, engine-neutral Boonta track spline JSON files."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

FORMAT = "boonta-track-v1"
MAX_POINTS = 4096
MAX_ABS_COORDINATE = 1_000_000.0
MIN_HALF_WIDTH = 0.5
MAX_HALF_WIDTH = 100.0
MIN_SEGMENT_LENGTH = 0.01


class TrackValidationError(ValueError):
    """Raised when a track file is structurally or numerically invalid."""


def _number(value: Any, label: str, low: float, high: float) -> float:
    # bool is a subclass of int in Python, but is never a valid coordinate.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TrackValidationError(f"{label} must be a number")
    number = float(value)
    if not math.isfinite(number):
        raise TrackValidationError(f"{label} must be finite")
    if number < low or number > high:
        raise TrackValidationError(f"{label} must be between {low} and {high}")
    return number


def validate_track(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise TrackValidationError("track root must be an object")
    if data.get("format") != FORMAT:
        raise TrackValidationError(f"format must equal {FORMAT!r}")
    name = data.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 80:
        raise TrackValidationError("name must be a non-empty string of at most 80 characters")
    closed_loop = data.get("closed_loop")
    if not isinstance(closed_loop, bool):
        raise TrackValidationError("closed_loop must be a boolean")
    points = data.get("points")
    if not isinstance(points, list):
        raise TrackValidationError("points must be an array")
    minimum = 3 if closed_loop else 2
    if len(points) < minimum:
        raise TrackValidationError(f"at least {minimum} points are required")
    if len(points) > MAX_POINTS:
        raise TrackValidationError(f"point count exceeds limit ({MAX_POINTS})")

    normalized = []
    for index, point in enumerate(points):
        if not isinstance(point, dict):
            raise TrackValidationError(f"points[{index}] must be an object")
        x = _number(point.get("x"), f"points[{index}].x",
                    -MAX_ABS_COORDINATE, MAX_ABS_COORDINATE)
        y = _number(point.get("y"), f"points[{index}].y",
                    -MAX_ABS_COORDINATE, MAX_ABS_COORDINATE)
        z = _number(point.get("z"), f"points[{index}].z",
                    -MAX_ABS_COORDINATE, MAX_ABS_COORDINATE)
        half_width = _number(point.get("half_width"), f"points[{index}].half_width",
                             MIN_HALF_WIDTH, MAX_HALF_WIDTH)
        checkpoint = point.get("checkpoint", False)
        if not isinstance(checkpoint, bool):
            raise TrackValidationError(f"points[{index}].checkpoint must be a boolean")
        normalized.append({
            "x": x, "y": y, "z": z,
            "half_width": half_width, "checkpoint": checkpoint,
        })

    segment_count = len(normalized) if closed_loop else len(normalized) - 1
    for index in range(segment_count):
        following = (index + 1) % len(normalized)
        a, b = normalized[index], normalized[following]
        distance = math.sqrt(
            (b["x"] - a["x"]) ** 2
            + (b["y"] - a["y"]) ** 2
            + (b["z"] - a["z"]) ** 2
        )
        if not math.isfinite(distance) or distance < MIN_SEGMENT_LENGTH:
            raise TrackValidationError(
                f"segment {index}->{following} is zero-length or too short"
            )

    return {
        "format": FORMAT,
        "name": name,
        "closed_loop": closed_loop,
        "points": normalized,
    }


def load_track(path: str | Path) -> dict[str, Any]:
    try:
        with Path(path).open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise TrackValidationError(f"cannot read valid JSON: {exc}") from exc
    return validate_track(data)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} TRACK.json", file=sys.stderr)
        return 2
    try:
        track = load_track(argv[1])
    except TrackValidationError as exc:
        print(f"invalid track: {exc}", file=sys.stderr)
        return 1
    print(
        f"valid {track['format']}: {track['name']} "
        f"({len(track['points'])} points, "
        f"{'closed loop' if track['closed_loop'] else 'point-to-point'})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
