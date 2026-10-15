#!/usr/bin/env python3
"""Check the procedural Dolphin scene and compare neutral vs steered DTM frames."""
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


def player_pod_center(image: Image.Image) -> float:
    image = image.convert("RGB")
    player_x = []
    # Ignore the road-edge strip and look for orange thrusters in the lower view.
    for y in range(int(image.height * 0.72), image.height - 20):
        for x in range(int(image.width * 0.25), int(image.width * 0.90)):
            r, g, b = image.getpixel((x, y))
            if r > 220 and 80 < g < 185 and b < 110:
                player_x.append(x)
    if not player_x:
        raise ValueError("No player-pod orange pixels found in the lower game viewport.")
    return sum(player_x) / len(player_x)


def validate_scene(image: Image.Image, label: str) -> None:
    signatures = scene_signatures(image)
    print(label + " scene color-pixel counts: " +
          ", ".join(f"{name}={count}" for name, count in signatures.items()))
    if (signatures["cyan"] < 30 or signatures["orange"] < 30 or
            signatures["ground_green"] < 100 or signatures["pod_blue"] < 30):
        raise SystemExit(f"{label} frame is missing expected scene-color signatures; DOL may not have booted.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frame", type=Path, help="frame rendered with steering input")
    parser.add_argument("--baseline", required=True, type=Path,
                        help="matching frame rendered with --steering none")
    parser.add_argument("--min-shift", type=float, default=2.0,
                        help="minimum rightward player-pod displacement in pixels")
    args = parser.parse_args()

    image = Image.open(args.frame).convert("RGB")
    baseline = Image.open(args.baseline).convert("RGB")
    if image.size != baseline.size:
        raise SystemExit(f"Frame dimensions differ: steered={image.size}, baseline={baseline.size}")
    validate_scene(baseline, "Neutral baseline")
    validate_scene(image, "Steered")
    baseline_x = player_pod_center(baseline)
    steered_x = player_pod_center(image)
    delta_x = steered_x - baseline_x
    print(f"Neutral player-pod center x={baseline_x:.1f}")
    print(f"Steered player-pod center x={steered_x:.1f}")
    print(f"Visible rightward response delta_x={delta_x:.1f}px (minimum {args.min_shift:.1f}px)")
    if delta_x < args.min_shift:
        raise SystemExit("DTM playback did not move the player pod sufficiently rightward relative to a neutral-input baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
