#!/usr/bin/env python3
"""Validate the original engine-neutral boonta-rgb565-v1 texture format."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

FORMAT = "boonta-rgb565-v1"
TILE_SIZE = 4
MAX_DIMENSION = 256


class TextureValidationError(ValueError):
    """Raised when a source texture is structurally or numerically invalid."""


def _integer(value: Any, label: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TextureValidationError(f"{label} must be an integer")
    if value < low or value > high:
        raise TextureValidationError(f"{label} must be between {low} and {high}")
    return value


def validate_texture(data: Any) -> dict[str, Any]:
    """Validate and normalize one RGB8 source texture for GX RGB565 export."""
    if not isinstance(data, dict):
        raise TextureValidationError("texture root must be an object")
    if data.get("format") != FORMAT:
        raise TextureValidationError(f"format must equal {FORMAT!r}")
    name = data.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 80:
        raise TextureValidationError("name must be a non-empty string of at most 80 characters")

    width = _integer(data.get("width"), "width", TILE_SIZE, MAX_DIMENSION)
    height = _integer(data.get("height"), "height", TILE_SIZE, MAX_DIMENSION)
    for label, dimension in (("width", width), ("height", height)):
        if dimension % TILE_SIZE != 0 or dimension & (dimension - 1):
            raise TextureValidationError(
                f"{label} must be a power of two and a multiple of {TILE_SIZE}"
            )

    pixels = data.get("pixels")
    if not isinstance(pixels, list) or len(pixels) != width * height:
        raise TextureValidationError("pixels must contain exactly width * height RGB triples")
    normalized_pixels = []
    for index, pixel in enumerate(pixels):
        if not isinstance(pixel, list) or len(pixel) != 3:
            raise TextureValidationError(f"pixels[{index}] must contain exactly 3 RGB channels")
        normalized_pixels.append([
            _integer(pixel[channel], f"pixels[{index}][{channel}]", 0, 255)
            for channel in range(3)
        ])

    return {
        "format": FORMAT,
        "name": name,
        "width": width,
        "height": height,
        "pixels": normalized_pixels,
    }


def load_texture(path: str | Path) -> dict[str, Any]:
    """Read JSON and wrap file/JSON/encoding errors consistently."""
    try:
        with Path(path).open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise TextureValidationError(f"cannot read valid JSON: {exc}") from exc
    return validate_texture(data)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} TEXTURE.json", file=sys.stderr)
        return 2
    try:
        texture = load_texture(argv[1])
    except TextureValidationError as exc:
        print(f"invalid texture: {exc}", file=sys.stderr)
        return 1
    print(
        f"valid {texture['format']}: {texture['name']} "
        f"({texture['width']}x{texture['height']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
