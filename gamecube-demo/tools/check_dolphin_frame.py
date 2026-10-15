#!/usr/bin/env python3
"""Measure camera-follow response and HUD input state; not full playability."""
from __future__ import annotations

import argparse
from pathlib import Path
from statistics import median
from PIL import Image


def scene_signatures(image: Image.Image) -> dict[str, int]:
    pixels = list(image.convert("RGB").getdata())
    return {
        "cyan": sum(1 for r, g, b in pixels if r < 110 and g > 145 and b > 150),
        "orange": sum(1 for r, g, b in pixels if r > 180 and 45 < g < 190 and b < 135),
        "ground_green": sum(1 for r, g, b in pixels if g > 1.25 * r and g > 1.05 * b and g > 25 and r < 100),
        "pod_blue": sum(1 for r, g, b in pixels if b > 145 and b > 1.35 * r and g > 65 and r < 120),
    }


def player_pod_bounds(image: Image.Image) -> tuple[float, int, int, int]:
    """Return (horizontal center, left edge, right edge, pixel count) for pod-top pixels."""
    image = image.convert("RGB")
    pod_x = []
    # The player's bright cyan top is approximately C_POD_TOP = (33, 164, 220).
    # This mask excludes the darker rails and the cyan road-edge markers.
    y_start = int(image.height * 0.65)
    y_end = int(image.height * 0.90)
    for y in range(y_start, y_end):
        for x in range(image.width):
            r, g, b = image.getpixel((x, y))
            if r < 70 and 100 < g < 200 and b > 170 and b > g * 1.15 and b > r * 2:
                pod_x.append(x)
    if len(pod_x) < 50:
        raise ValueError(
            f"No stable player-pod surface pixels in lower viewport; found {len(pod_x)}."
        )
    return sum(pod_x) / len(pod_x), min(pod_x), max(pod_x), len(pod_x)


def road_center_from_ground_bounds(image: Image.Image) -> tuple[float, int]:
    """Estimate road center from the green-ground boundaries on both sides."""
    image = image.convert("RGB")
    row_centers = []
    midpoint = image.width // 2
    # The ground is green (C_GROUND ~= RGB(23, 48, 40)); road asphalt is dark
    # blue-gray. Use a narrow upper/mid viewport above the player pod and HUD.
    y_start = int(image.height * 0.52)
    y_end = int(image.height * 0.60)
    for y in range(y_start, y_end):
        left_ground_edge = None
        right_ground_edge = None
        for x in range(image.width):
            r, g, b = image.getpixel((x, y))
            if g > 1.25 * r and g > 1.05 * b and g > 25 and r < 100:
                if x < midpoint:
                    left_ground_edge = x
                elif right_ground_edge is None:
                    right_ground_edge = x
        # A valid row has green ground on each side of the road.
        if (left_ground_edge is not None and right_ground_edge is not None
                and right_ground_edge > left_ground_edge):
            row_centers.append((left_ground_edge + right_ground_edge) / 2.0)

    # Ignore isolated HUD/aliasing pixels by aggregating many road rows and
    # use the median so rivals and small scene details cannot dominate it.
    if len(row_centers) < 10:
        raise ValueError(
            f"Insufficient road-boundary rows in ROI y=[{y_start},{y_end}); "
            f"found {len(row_centers)}, need 10."
        )
    return float(median(row_centers)), len(row_centers)


def steering_indicator_center(image: Image.Image) -> float:
    image = image.convert("RGB")
    marker_x = []
    # The prototype draws a bright 4-pixel steering-state tick near the bottom
    # of the HUD at x = screen_center + g_player_lateral * 18. This is a HUD/state
    # signal useful for a deterministic scripted-input smoke test. It is NOT a
    # measurement of player-pod displacement, world motion, steering physics, or
    # gameplay feel; those require a separate interactive acceptance test.
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
    parser.add_argument("--direction", choices=("left", "right"), default="right",
                        help="steering direction encoded by the input movie")
    parser.add_argument("--min-shift", type=float, default=2.0,
                        help="minimum HUD-marker response in the requested steering direction")
    parser.add_argument("--max-pod-drift", type=float, default=80.0,
                        help="maximum neutral-to-steered player-pod centroid drift while camera follows")
    parser.add_argument("--min-course-shift", type=float, default=25.0,
                        help="minimum road-edge shift opposite the requested steering direction")
    args = parser.parse_args()
    direction_label = "Right-input" if args.direction == "right" else "Left-input"
    expected_road_direction = "leftward" if args.direction == "right" else "rightward"
    expected_marker_direction = "rightward" if args.direction == "right" else "leftward"

    image = Image.open(args.frame).convert("RGB")
    baseline = Image.open(args.baseline).convert("RGB")
    if image.size != baseline.size:
        raise SystemExit(f"Frame dimensions differ: steered={image.size}, baseline={baseline.size}")
    validate_scene(baseline, "Neutral baseline")
    validate_scene(image, "Steered")
    baseline_pod_x, baseline_left, baseline_right, baseline_pixels = player_pod_bounds(baseline)
    steered_pod_x, steered_left, steered_right, steered_pixels = player_pod_bounds(image)
    pod_delta_x = steered_pod_x - baseline_pod_x
    print(f"Neutral player-pod center x={baseline_pod_x:.1f} "
          f"(bounds {baseline_left}..{baseline_right}, {baseline_pixels} pixels)")
    print(f"{direction_label} player-pod center x={steered_pod_x:.1f} "
          f"(bounds {steered_left}..{steered_right}, {steered_pixels} pixels)")
    print(f"Player-pod screen drift={pod_delta_x:.1f}px "
          f"(maximum {args.max_pod_drift:.1f}px with camera follow)")
    if baseline_left <= 0 or baseline_right >= baseline.width - 1:
        raise SystemExit("Neutral player pod is clipped by the frame border.")
    if steered_left <= 0 or steered_right >= image.width - 1:
        raise SystemExit(f"{direction_label} player pod is clipped by the frame border; camera follow failed.")
    if abs(pod_delta_x) > args.max_pod_drift:
        raise SystemExit("Player pod moved too far across the screen; expected the camera to follow it.")

    baseline_road_x, baseline_road_rows = road_center_from_ground_bounds(baseline)
    steered_road_x, steered_road_rows = road_center_from_ground_bounds(image)
    road_response = (baseline_road_x - steered_road_x
                     if args.direction == "right"
                     else steered_road_x - baseline_road_x)
    print(f"Neutral road center x={baseline_road_x:.1f} ({baseline_road_rows} rows)")
    print(f"{direction_label} road center x={steered_road_x:.1f} ({steered_road_rows} rows)")
    print(f"Road-center {expected_road_direction} response={road_response:.1f}px "
          f"(minimum {args.min_course_shift:.1f}px)")
    if road_response < args.min_course_shift:
        raise SystemExit(
            f"Road silhouette did not shift sufficiently {expected_road_direction} relative to the camera-following player pod."
        )

    # Retain the HUD state marker as an independent input-state diagnostic.
    baseline_x = steering_indicator_center(baseline)
    steered_x = steering_indicator_center(image)
    marker_response = (steered_x - baseline_x
                       if args.direction == "right"
                       else baseline_x - steered_x)
    print(f"Neutral HUD marker center x={baseline_x:.1f}")
    print(f"{direction_label} HUD marker center x={steered_x:.1f}")
    print(f"HUD marker {expected_marker_direction} response={marker_response:.1f}px "
          f"(minimum {args.min_shift:.1f}px)")
    if marker_response < args.min_shift:
        raise SystemExit(
            f"Scripted input did not move the HUD steering-state marker {expected_marker_direction}."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
