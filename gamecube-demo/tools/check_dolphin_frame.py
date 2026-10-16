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
        "ground_sand": sum(1 for r, g, b in pixels if r > 1.15 * g and g > 1.15 * b and r > 70),
        "pod_blue": sum(
            1 for r, g, b in pixels
            if r < 70 and 100 < g < 200 and b > 170 and b > 1.15 * g and b > 2 * r
        ),
    }


def player_pod_bounds(image: Image.Image) -> tuple[float, int, int, int]:
    """Return robust (center, left edge, right edge, pixel count) for pod-top pixels.

    The camera scene can contain a few unrelated pixels with a similar cyan
    signature. Use trimmed bounds for the pod silhouette, while separately
    rejecting a meaningful number of mask pixels touching the image border.
    This avoids false "clipped pod" failures from one-pixel canyon/rail accents.
    """
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
    pixel_count = len(pod_x)
    if pixel_count < 50:
        raise ValueError(
            f"No stable player-pod surface pixels in lower viewport; found {pixel_count}."
        )

    border_hits = sum(1 for x in pod_x if x <= 1 or x >= image.width - 2)
    border_limit = max(3, int(pixel_count * 0.01))
    if border_hits > border_limit:
        raise ValueError(
            f"Player pod may be clipped: {border_hits} matching pixels touch the frame border "
            f"(limit {border_limit} of {pixel_count})."
        )

    pod_x.sort()
    trim = int(pixel_count * 0.02)
    robust_x = pod_x[trim:pixel_count - trim] if trim else pod_x
    return sum(robust_x) / len(robust_x), robust_x[0], robust_x[-1], pixel_count


def road_center_from_asphalt(image: Image.Image) -> tuple[float, int]:
    """Estimate the road center from its dark blue-grey asphalt, independent of terrain color."""
    image = image.convert("RGB")
    row_centers = []
    # Measure the nearer road, not the horizon: curvature and scroll phase
    # can cancel a steering response near the horizon. This mid-foreground ROI
    # gives a stronger, symmetric left/right signal and excludes the HUD/pod.
    y_start = int(image.height * 0.65)
    y_end = int(image.height * 0.72)
    pixels = image.load()

    for y in range(y_start, y_end):
        asphalt_x = []
        for x in range(image.width):
            r, g, b = pixels[x, y]
            # Match the two procedural road colors; exclude the warm ground,
            # cyan rails, orange/red edge strips, and blue sky.
            if (24 <= r <= 78 and 30 <= g <= 82 and 42 <= b <= 96
                    and g >= r + 3 and b >= g + 8):
                asphalt_x.append(x)

        # One asphalt run may contain a narrow lane marker; the outermost
        # asphalt pixels still give a stable left/right boundary estimate.
        if len(asphalt_x) >= 8:
            left_edge = asphalt_x[0]
            right_edge = asphalt_x[-1]
            if right_edge - left_edge >= 10:
                row_centers.append((left_edge + right_edge) / 2.0)

    # At 800x480, Software Renderer anti-aliasing can leave only a handful
    # of exact asphalt-colored scanlines. Five rows are enough for a median;
    # the separate >=25 px response gate still rejects weak/no-motion captures.
    if len(row_centers) < 5:
        raise ValueError(
            f"Insufficient asphalt-boundary rows in ROI y=[{y_start},{y_end}); "
            f"found {len(row_centers)}, need 5."
        )
    return float(median(row_centers)), len(row_centers)

def steering_indicator_center(image: Image.Image) -> float:
    image = image.convert("RGB")
    # The prototype draws a bright 4-pixel steering-state tick near the bottom
    # of the HUD at x = screen_center + g_player_lateral * 18. This is a HUD/state
    # signal useful for a deterministic scripted-input smoke test. It is NOT a
    # measurement of player-pod displacement, world motion, steering physics, or
    # gameplay feel; those require a separate interactive acceptance test.
    #
    # A Dolphin window capture includes its toolbar, so use the detected viewport
    # to project the logical HUD tick rows into screenshot coordinates. Locate
    # the narrowest vertical cluster of bright pixels instead of averaging every
    # white pixel in the scene (which can include pod highlights or track details).
    viewport_top = detect_game_viewport_top(image)
    viewport_height = max(1, image.height - viewport_top)
    y_start = round(viewport_top + viewport_height * (image.height - 46) / image.height)
    y_end = round(viewport_top + viewport_height * (image.height - 30) / image.height)
    x_start = int(image.width * 0.30)
    x_end = int(image.width * 0.70)
    column_hits = []
    for x in range(x_start, x_end):
        hits = 0
        for y in range(y_start, min(y_end, image.height)):
            r, g, b = image.getpixel((x, y))
            if r > 215 and g > 215 and b > 215:
                hits += 1
        column_hits.append((x, hits))

    peak = max((hits for _, hits in column_hits), default=0)
    if peak < 8:
        raise ValueError(
            f"No stable bright steering tick in projected HUD rows "
            f"y=[{y_start},{y_end}); strongest column had {peak} bright pixels."
        )

    # Keep columns that contain a substantial portion of the strongest tick
    # column; narrow scene highlights then cannot pull the result toward the
    # middle of the screen.
    active = [(x, hits) for x, hits in column_hits if hits >= max(6, int(peak * 0.60))]
    groups = []
    current = []
    for item in active:
        if current and item[0] != current[-1][0] + 1:
            groups.append(current)
            current = []
        current.append(item)
    if current:
        groups.append(current)
    if not groups:
        raise ValueError("No contiguous bright steering-tick columns found.")

    best_group = max(groups, key=lambda group: sum(hits for _, hits in group))
    if len(best_group) > 12:
        raise ValueError(f"Steering-tick candidate is too wide ({len(best_group)} columns).")
    weight = sum(hits for _, hits in best_group)
    return sum(x * hits for x, hits in best_group) / max(1, weight)


def validate_scene(image: Image.Image, label: str) -> None:
    signatures = scene_signatures(image)
    print(label + " scene color-pixel counts: " +
          ", ".join(f"{name}={count}" for name, count in signatures.items()))
    # The neutral profile can show only distant road markers instead of a large
    # green road surface. Require multiple craft/scene colors, but keep the
    # ground-green count diagnostic rather than rejecting that valid viewpoint.
    if signatures["cyan"] < 30 or signatures["orange"] < 30 or signatures["pod_blue"] < 30:
        raise SystemExit(f"{label} frame is missing expected scene/craft color signatures; DOL may not have booted.")


def detect_game_viewport_top(image: Image.Image) -> int:
    """Find the start of the rendered game viewport in a Dolphin window capture.

    A normal Dolphin window screenshot includes a light toolbar above the 3D
    viewport; framebuffer-only images start at row zero. Identify the first
    full-width sky row so HUD coordinates can be scaled into either capture.
    """
    image = image.convert("RGB")
    width, height = image.size
    sample_step = max(1, width // 160)
    sample_x = range(0, width, sample_step)
    threshold = max(1, int(len(sample_x) * 0.72))
    for y in range(min(int(height * 0.30), height)):
        sky_hits = 0
        for x in sample_x:
            r, g, b = image.getpixel((x, y))
            if (65 <= r <= 145 and 125 <= g <= 200 and b >= 190
                    and b > r * 1.2 and b > g * 1.1):
                sky_hits += 1
        if sky_hits >= threshold:
            return y
    return 0


def reset_state_metrics(image: Image.Image) -> dict[str, float]:
    """Measure HUD bars that should be reset to the start-state values.

    The prototype's HUD is authored in the game viewport's own pixel coordinates.
    Dolphin window captures include a toolbar, which reduces and offsets the
    viewport; convert HUD row locations into capture coordinates before sampling.
    """
    image = image.convert("RGB")
    width, height = image.size
    viewport_top = detect_game_viewport_top(image)
    viewport_height = max(1, height - viewport_top)
    bar_left = 24
    bar_width = 130 if width < 500 else 190
    bar_right = min(width, bar_left + bar_width)
    if bar_right - bar_left < max(100, int(bar_width * 0.8)) or height < 100:
        raise ValueError(f"Image too small for reset-state HUD inspection: {image.size}")

    def row_pixels(y_offset: int) -> list[tuple[int, int, int]]:
        logical_y = max(0, min(height - 1, height - y_offset))
        y = round(viewport_top + viewport_height * logical_y / height)
        y = max(0, min(height - 1, y))
        return [image.getpixel((x, y)) for x in range(bar_left, bar_right)]

    speed_row = row_pixels(30)
    boost_row = row_pixels(48)
    heat_row = row_pixels(70)
    progress_row = row_pixels(62)
    lap_marker_row = row_pixels(78)

    speed_fill = sum(1 for r, g, b in speed_row if r < 100 and g > 180 and b > 200)
    boost_fill = sum(1 for r, g, b in boost_row
                     if r > 220 and 110 < g < 190 and b < 100)
    heat_fill = sum(1 for r, g, b in heat_row if r > 200 and b < 160)
    progress_fill = sum(1 for r, g, b in progress_row
                        if g > 180 and r > 100 and b > 100)
    lap_done = sum(1 for r, g, b in lap_marker_row
                   if g > 180 and r > 100 and b > 100)
    steering_marker_offset = abs(steering_indicator_center(image) - width / 2.0)
    row_width = max(1, len(speed_row))
    return {
        "speed_fill_pixels": float(speed_fill),
        "boost_fill_fraction": boost_fill / row_width,
        "heat_fill_pixels": float(heat_fill),
        "lap_progress_pixels": float(progress_fill),
        "completed_lap_marker_pixels": float(lap_done),
        "steering_marker_offset_pixels": steering_marker_offset,
        "game_viewport_top_pixels": float(viewport_top),
    }


def reset_state_visible(image: Image.Image) -> bool:
    """Return true only when the HUD visibly matches the clean start state."""
    metrics = reset_state_metrics(image)
    tolerance = max(3.0, (130.0 if image.width < 500 else 190.0) * 0.02)
    return (
        metrics["speed_fill_pixels"] <= tolerance
        and metrics["boost_fill_fraction"] >= 0.90
        and metrics["heat_fill_pixels"] <= tolerance
        and metrics["lap_progress_pixels"] <= tolerance
        and metrics["completed_lap_marker_pixels"] <= tolerance
        and metrics["steering_marker_offset_pixels"] <= 4.0
    )


def finish_banner_visible(image: Image.Image) -> bool:
    """Detect the demo's centered 4x3 finish-flag checkerboard.

    Dolphin-window captures may include a toolbar, while direct framebuffer
    captures do not. Search both likely vertical centers and small scale/offset
    ranges; the alternating pattern distinguishes the finish banner from pause.
    """
    image = image.convert("RGB")
    width, height = image.size
    pixels = image.load()

    def white_fraction(x0: float, y0: float, x1: float, y1: float) -> float:
        left = max(0, int(x0))
        top = max(0, int(y0))
        right = min(width, int(x1))
        bottom = min(height, int(y1))
        hit = total = 0
        for y in range(top, bottom):
            for x in range(left, right):
                r, g, b = pixels[x, y]
                total += 1
                if r > 205 and g > 215 and b > 220:
                    hit += 1
        return hit / max(total, 1)

    center_x = width / 2.0
    center_y_candidates = (height / 2.0, height * 0.5833333333)
    for tile_width in range(12, 25):
        for tile_height in range(8, 18):
            for x_offset in (-6, -3, 0, 3, 6):
                for center_y_base in center_y_candidates:
                    for y_offset in (-6, -3, 0, 3, 6):
                        cx = center_x + x_offset
                        cy = center_y_base + y_offset
                        left = cx - 2 * tile_width
                        top = cy - 1.5 * tile_height
                        matched = True
                        for row in range(3):
                            for col in range(4):
                                x0 = left + col * tile_width + tile_width * 0.15
                                x1 = left + (col + 1) * tile_width - tile_width * 0.15
                                y0 = top + row * tile_height + tile_height * 0.15
                                y1 = top + (row + 1) * tile_height - tile_height * 0.15
                                bright = white_fraction(x0, y0, x1, y1)
                                if (row + col) % 2 == 0:
                                    if bright < 0.35:
                                        matched = False
                                        break
                                elif bright > 0.15:
                                    matched = False
                                    break
                            if not matched:
                                break
                        if matched:
                            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("frame", type=Path, help="frame rendered with steering input")
    parser.add_argument("--baseline", type=Path,
                        help="matching frame rendered with --steering none")
    parser.add_argument("--expect-finish", action="store_true",
                        help="check for the three-lap finish flag instead of comparing steering frames")
    parser.add_argument("--expect-reset", action="store_true",
                        help="check that speed/lap/heat are empty and boost is refilled after Y reset")
    parser.add_argument("--direction", choices=("left", "right"), default="right",
                        help="steering direction encoded by the input movie")
    parser.add_argument("--min-shift", type=float, default=2.0,
                        help="minimum HUD-marker response in the requested steering direction")
    parser.add_argument("--max-pod-drift", type=float, default=80.0,
                        help="maximum neutral-to-steered player-pod centroid drift while camera follows")
    parser.add_argument("--min-course-shift", type=float, default=25.0,
                        help="minimum road-edge shift opposite the requested steering direction")
    args = parser.parse_args()
    image = Image.open(args.frame).convert("RGB")
    if args.expect_finish and args.expect_reset:
        parser.error("--expect-finish and --expect-reset cannot be used together")
    if args.expect_finish:
        if args.baseline is not None:
            parser.error("--expect-finish cannot be combined with --baseline")
        if not finish_banner_visible(image):
            raise SystemExit("The centered three-lap finish checkerboard was not detected in the Dolphin capture.")
        print("Three-lap finish banner detected in the visible Dolphin frame.")
        return 0
    if args.expect_reset:
        if args.baseline is not None:
            parser.error("--expect-reset cannot be combined with --baseline")
        validate_scene(image, "Reset-state")
        metrics = reset_state_metrics(image)
        print("Reset HUD metrics: " + ", ".join(f"{name}={value:.3f}" for name, value in metrics.items()))
        if not reset_state_visible(image):
            raise SystemExit("The visible HUD does not match reset state (expected zero speed/heat/lap progress and full boost).")
        print("Clean Y-reset HUD state detected in the visible Dolphin frame.")
        return 0
    if args.baseline is None:
        parser.error("--baseline is required unless --expect-finish is set")
    direction_label = "Right-input" if args.direction == "right" else "Left-input"
    expected_road_direction = "leftward" if args.direction == "right" else "rightward"
    expected_marker_direction = "rightward" if args.direction == "right" else "leftward"

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

    baseline_road_x, baseline_road_rows = road_center_from_asphalt(baseline)
    steered_road_x, steered_road_rows = road_center_from_asphalt(image)
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
