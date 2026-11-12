"""Pillow-free structural detector for the centered post-race results panel."""
from __future__ import annotations

from collections.abc import Callable


RGBReader = Callable[[int, int], tuple[int, int, int]]


def results_panel_visible(
    width: int,
    height: int,
    viewport_top: int,
    pixel_at: RGBReader,
) -> bool:
    """Require the RESULTS title and all three distinctive regions of its panel.

    Orange pixels alone are unsafe evidence: rival exhaust can enter the same
    title region. The actual UI panel is almost opaque and 264x184, unlike the
    shorter RACE READY panel. Requiring both vertical edges and the lower band
    makes this detector structural rather than a color-count heuristic.
    """
    if (
        type(width) is not int or type(height) is not int
        or type(viewport_top) is not int
        or width < 1 or height < 1
        or viewport_top < 0 or viewport_top >= height
    ):
        return False

    viewport_height = max(1, height - viewport_top)
    scale_x = width / 800.0
    scale_y = viewport_height / 480.0
    center_x = width / 2.0
    center_y = viewport_top + viewport_height / 2.0

    x0 = max(0, int(center_x - 33.0 * scale_x))
    x1 = min(width, int(center_x + 33.0 * scale_x))
    y0 = max(0, int(center_y - 81.0 * scale_y))
    y1 = min(height, int(center_y - 66.0 * scale_y))
    orange_pixels = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            red, green, blue = pixel_at(x, y)
            if red >= 220 and 120 <= green <= 190 and blue <= 100:
                orange_pixels += 1

    def text_row_visible(offset: float) -> bool:
        # The RESULTS overlay uses white, amber and orange text. The panel is
        # opaque, so these high-contrast pixels cannot be confused with the
        # moving course behind it. Check each content row, not only the title.
        row_top = max(0, int(center_y + (offset - 1.0) * scale_y))
        row_bottom = min(height, int(center_y + (offset + 8.0) * scale_y))
        row_left = max(0, int(center_x - 112.0 * scale_x))
        row_right = min(width, int(center_x + 112.0 * scale_x))
        hits = 0
        for sample_y in range(row_top, row_bottom):
            for sample_x in range(row_left, row_right):
                red, green, blue = pixel_at(sample_x, sample_y)
                if ((red >= 180 and green >= 120 and blue >= 70)
                        or (red >= 190 and green >= 190 and blue >= 190)):
                    hits += 1
        return hits >= max(18, round(32.0 * scale_x * scale_y))

    # Three lap splits, the total/best row, overtakes, position and restart
    # prompt must all be present. This catches a clipped lower half of RESULTS.
    content_rows_visible = all(
        text_row_visible(offset)
        for offset in (-48.0, -27.0, -6.0, 22.0, 45.0, 65.0, 80.0)
    )

    def dark_fraction(left: float, top: float, right: float, bottom: float) -> float:
        left_edge = max(0, int(left))
        top_edge = max(0, int(top))
        right_edge = min(width, int(right))
        bottom_edge = min(height, int(bottom))
        total = dark = 0
        for sample_y in range(top_edge, bottom_edge):
            for sample_x in range(left_edge, right_edge):
                red, green, blue = pixel_at(sample_x, sample_y)
                total += 1
                if red <= 48 and green <= 58 and blue <= 72:
                    dark += 1
        return dark / max(total, 1)

    left_panel_edge = dark_fraction(
        center_x - 128.0 * scale_x, center_y - 80.0 * scale_y,
        center_x - 116.0 * scale_x, center_y + 80.0 * scale_y,
    )
    right_panel_edge = dark_fraction(
        center_x + 116.0 * scale_x, center_y - 80.0 * scale_y,
        center_x + 128.0 * scale_x, center_y + 80.0 * scale_y,
    )
    lower_panel_band = dark_fraction(
        center_x - 112.0 * scale_x, center_y + 62.0 * scale_y,
        center_x + 112.0 * scale_x, center_y + 84.0 * scale_y,
    )
    # A captured Dolphin window can be shorter than the 480-line game viewport
    # because its toolbar shares the same fixed-height window. The title glyphs
    # are then vertically scaled with the viewport; scale the pixel-count gate
    # by the sampled area so a genuine RESULTS panel is not rejected solely due
    # to the smaller capture. Keep a floor to reject isolated exhaust pixels.
    minimum_orange_pixels = max(40, round(80.0 * scale_x * scale_y))
    return (
        orange_pixels >= minimum_orange_pixels
        and min(left_panel_edge, right_panel_edge, lower_panel_band) >= 0.82
        and content_rows_visible
    )
