#!/usr/bin/env python3
"""Validate Dolphin scene signatures and compare the visible steering-state indicator."""
from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image


def scene_signatures(image: Image.Image) -> dict[str, int]:
    pixels = list(image.convert("RGB").getdata())
    return {
        "cyan": sum(1 for r, g, b in pixels if r < 110 and g > 145 and b > 150),
        "orange": sum(1 for r, g, b in pixels if r > 180 and 45 < g < 190 and b < 135),
        "ground_green": sum(1 for r, g, b in pixels if g > 1.25 * r and g > 1.05 * b and g > 25 and r < 100),
        "pod_blue": sum(1 for r, g, b in pixels if b > 145 and b > 1.35 * r and g > 65 and r < 120),
    }


def steering_indicator_center(image: Image.Image) -> float:
    image = image.convert("RGB")
    marker_x = []
    # The prototype draws a bright 4-pixel steering-state tick near the bottom
    # of the HUD at x = screen_center + g_player_lateral * 18. This tracks the
    # actual steering state and remains detectable even when the tiny 3D pod's
    # thruster color changes or the curved road occupies different screen areas.
    x_start = int(image.width * 0.35)
    x_end = int(image.width * 0.70)
    y_start = int(image.height * 0.89)
    y_end = int(image.height * 0.96)
    for y in range(y_start, y_end):
        for x in range(x_start, x_end):
            r, g, b = image.getpixel((x, y))
            if r > 215 and g > 215 and b > 215:
                marker_x.append(x)
    if len(marker_x) < 20:
        raise ValueError(
            f"No stable bright steering indicator in ROI x=[{x_start},{x_end}), "
            f"y=[{y_start},{y_end}); found {len(marker_x)} pixels."
        )
    return sum(marker_x) / len(marker_x)


def validate_scene(image: Image.Image, label: str) -> None:
    signatures = scene_signatures(image)
    print(label + " scene color-pixel counts: " +
          ", ".join(f"{name}={count}" for name, count in signatures.items()))
    # The neutral profile can show only distant road markers instead of a large
    # green road surface. Require multiple craft/scene colors, but keep the
    # ground-green count diagnostic rather than rejecting that valid viewpoint.
    if signatures["cyan"] < 30 or signatures["orange"] < 30 or signatures["pod_blue"] < 30:
        raise SystemExit(f"{label} frame is missing expected scene/craft color signatures; DOL may not have booted.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frame", type=Path, help="frame rendered with steering input")
    parser.add_argument("--baseline", required=True, type=Path,
                        help="matching frame rendered with --steering none")
    parser.add_argument("--min-shift", type=float, default=2.0,
                        help="minimum rightward steering-state marker displacement in pixels")
    args = parser.parse_args()

    image = Image.open(args.frame).convert("RGB")
    baseline = Image.open(args.baseline).convert("RGB")
    if image.size != baseline.size:
        raise SystemExit(f"Frame dimensions differ: steered={image.size}, baseline={baseline.size}")
    validate_scene(baseline, "Neutral baseline")
    validate_scene(image, "Steered")
    baseline_x = steering_indicator_center(baseline)
    steered_x = steering_indicator_center(image)
    delta_x = steered_x - baseline_x
    print(f"Neutral steering-state marker center x={baseline_x:.1f}")
    print(f"Right-steered state marker center x={steered_x:.1f}")
    print(f"Visible rightward steering-state response delta_x={delta_x:.1f}px (minimum {args.min_shift:.1f}px)")
    if delta_x < args.min_shift:
        raise SystemExit("DTM playback did not move the visible steering-state indicator sufficiently rightward relative to a neutral-input baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
