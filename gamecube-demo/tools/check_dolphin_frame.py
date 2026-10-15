#!/usr/bin/env python3
"""Check that the Dolphin screenshot shows the procedural scene and DTM steering."""
from __future__ import annotations

import sys
from pathlib import Path
from PIL import Image


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_dolphin_frame.py FRAME.png")

    image = Image.open(Path(sys.argv[1])).convert("RGB")
    pixels = list(image.getdata())
    signatures = {
        "cyan": sum(1 for r, g, b in pixels if r < 110 and g > 145 and b > 150),
        "orange": sum(1 for r, g, b in pixels if r > 180 and 45 < g < 190 and b < 135),
        "ground_green": sum(1 for r, g, b in pixels if g > 1.25 * r and g > 1.05 * b and g > 25 and r < 100),
        "pod_blue": sum(1 for r, g, b in pixels if b > 145 and b > 1.35 * r and g > 65 and r < 120),
    }
    print("Scene color-pixel counts: " + ", ".join(f"{name}={count}" for name, count in signatures.items()))
    if (signatures["cyan"] < 30 or signatures["orange"] < 30 or
            signatures["ground_green"] < 100 or signatures["pod_blue"] < 30):
        raise SystemExit("Captured Dolphin window is missing expected scene-color signatures; DOL may not have booted.")

    # Analyze the lower viewport where the player's orange engines are visible.
    # The leftmost orange road-edge pixels are outside this search window.
    player_x = []
    for y in range(int(image.height * 0.72), image.height - 20):
        for x in range(int(image.width * 0.25), int(image.width * 0.90)):
            r, g, b = image.getpixel((x, y))
            if r > 220 and 80 < g < 185 and b < 110:
                player_x.append(x)

    if not player_x:
        raise SystemExit("No player-pod orange pixels found in the lower game viewport.")
    player_center_x = sum(player_x) / len(player_x)
    print(f"DTM-steered player-pod orange-pixel center x={player_center_x:.1f}")
    if player_center_x <= image.width * 0.54:
        raise SystemExit("DTM playback did not produce the expected rightward player response.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
