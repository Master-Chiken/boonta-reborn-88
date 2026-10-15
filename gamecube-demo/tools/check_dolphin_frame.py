#!/usr/bin/env python3
"""Measure scripted-input pod displacement and HUD response; not full playability."""
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
    parser.add_argument("--min-shift", type=float, default=2.0,
                        help="minimum HUD-marker shift for input-path smoke only; not proof of pod/world steering")
    parser.add_argument("--min-pod-shift", type=float, default=12.0,
                        help="minimum rightward player-pod surface displacement in pixels")
    args = parser.parse_args()

    image = Image.open(args.frame).convert("RGB")
    baseline = Image.open(args.baseline).convert("RGB")
    if image.size != baseline.size:
        raise SystemExit(f"Frame dimensions differ: steered={image.size}, baseline={baseline.size}")
    validate_scene(baseline, "Neutral baseline")
    validate_scene(image, "Steered")
    baseline_pod_x, baseline_left, baseline_right, baseline_pixels = player_pod_bounds(baseline)
    steered_pod_x, steered_left, steered_right, steered_pixels = player_pod_bounds(image)
    pod_delta_x = steered_pod_x - baseline_pod_x
    print(f"Neutral player-pod top center x={baseline_pod_x:.1f} "
          f"(bounds {baseline_left}..{baseline_right}, {baseline_pixels} pixels)")
    print(f"Right-steered player-pod top center x={steered_pod_x:.1f} "
          f"(bounds {steered_left}..{steered_right}, {steered_pixels} pixels)")
    print(f"Visible player-pod displacement delta_x={pod_delta_x:.1f}px "
          f"(minimum {args.min_pod_shift:.1f}px)")
    if pod_delta_x < args.min_pod_shift:
        raise SystemExit("Scripted right input did not visibly move the player-pod surface rightward.")

    # If the pod touches the capture border, keep the measurement but flag that
    # the current scripted hold drives it partly out of frame. This is a useful
    # quality warning, not a false claim that the full race is playable.
    if steered_left <= 0 or steered_right >= image.width - 1:
        print("::warning::The right-steered pod touches the capture border; review lateral camera/rail response.")

    # Retain the HUD state marker as an independent input-state diagnostic.
    baseline_x = steering_indicator_center(baseline)
    steered_x = steering_indicator_center(image)
    delta_x = steered_x - baseline_x
    print(f"Neutral HUD marker center x={baseline_x:.1f}")
    print(f"Right-input HUD marker center x={steered_x:.1f}")
    print(f"HUD marker delta_x={delta_x:.1f}px (minimum {args.min_shift:.1f}px)")
    if delta_x < args.min_shift:
        raise SystemExit("Scripted input did not move the HUD steering-state marker.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
