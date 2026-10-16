from __future__ import annotations

import struct
import unittest

from make_dolphin_dtm import (
    A,
    B,
    NEUTRAL_AXIS,
    RESET_PRESS_FRAME,
    RESET_BOOST_END_FRAME,
    STEERING_HOLD_FRAMES,
    DEFAULT_GAME_ID,
    DPAD_LEFT,
    DPAD_RIGHT,
    HEADER_SIZE,
    IS_CONNECTED,
    START,
    X,
    Y,
    build_dtm,
)

# Pillow is installed in the opt-in Dolphin visual job but isn't required for
# the lightweight host DTM protocol tests.
try:
    from PIL import Image, ImageDraw
    from check_dolphin_frame import (
        finish_banner_visible,
        player_pod_bounds,
        reset_state_visible,
        road_center_from_asphalt,
    )
except ImportError:
    Image = None
    ImageDraw = None
    finish_banner_visible = None
    player_pod_bounds = None
    reset_state_visible = None
    road_center_from_asphalt = None


def record(blob: bytes, frame: int) -> bytes:
    start = HEADER_SIZE + frame * 8
    return blob[start:start + 8]


class DolphinDtmTests(unittest.TestCase):
    def test_header_and_fixed_record_layout(self) -> None:
        frames = 3000
        blob = build_dtm(frames)
        self.assertEqual(blob[:4], b"DTM\x1a")
        self.assertEqual(len(blob), HEADER_SIZE + frames * 8)
        self.assertEqual(blob[4:10], DEFAULT_GAME_ID.encode("ascii"))
        self.assertEqual(blob[0x0A], 0)  # bWii=False
        self.assertEqual(blob[0x0B], 1)  # GameCube controller port 1 connected
        self.assertEqual(blob[0x0C], 0)  # starts from boot, not savestate
        self.assertEqual(struct.unpack_from("<Q", blob, 0x0D)[0], frames)
        self.assertEqual(struct.unpack_from("<Q", blob, 0x15)[0], frames)
        self.assertEqual(struct.unpack_from("<Q", blob, 0xED)[0], frames * 10_000_000)
        self.assertEqual(blob[0x89], 0)  # do not import movie settings

    def test_known_start_boost_brake_and_pause_resume_presses(self) -> None:
        blob = build_dtm(3600)
        first = record(blob, 0)
        self.assertTrue(first[0] & A)
        self.assertTrue(first[0] & Y)
        self.assertTrue(first[1] & IS_CONNECTED)
        self.assertTrue(first[1] & DPAD_RIGHT)
        self.assertEqual(NEUTRAL_AXIS, 128)  # raw DTM analog axes use unsigned center
        self.assertEqual(first[4:], bytes((NEUTRAL_AXIS,) * 4))

        boost = record(blob, 20)
        self.assertTrue(boost[0] & A)
        self.assertTrue(boost[0] & X)
        brake = record(blob, 120)
        self.assertTrue(brake[0] & B)
        self.assertTrue(brake[1] & DPAD_RIGHT)

        pause = record(blob, 220)
        resume = record(blob, 280)
        self.assertTrue(pause[0] & START)
        self.assertTrue(resume[0] & START)
        self.assertFalse(record(blob, 221)[0] & START)
        self.assertFalse(record(blob, 281)[0] & START)

    def test_steering_profiles_are_deterministic_and_do_not_cancel(self) -> None:
        right_blob = build_dtm(3600, steering="right")
        self.assertTrue(record(right_blob, 30)[1] & DPAD_RIGHT)
        self.assertFalse(record(right_blob, 30)[1] & DPAD_LEFT)
        self.assertTrue(record(right_blob, 100)[1] & DPAD_RIGHT)
        self.assertEqual(record(right_blob, 100)[4:], bytes((NEUTRAL_AXIS,) * 4))
        self.assertTrue(record(right_blob, 300)[1] & DPAD_RIGHT)
        self.assertTrue(record(right_blob, STEERING_HOLD_FRAMES - 1)[1] & DPAD_RIGHT)
        self.assertFalse(record(right_blob, STEERING_HOLD_FRAMES)[1] & DPAD_RIGHT)
        self.assertFalse(record(right_blob, 2020)[1] & DPAD_LEFT)
        self.assertFalse(record(right_blob, 2020)[1] & DPAD_RIGHT)

        left_blob = build_dtm(3600, steering="left")
        self.assertTrue(record(left_blob, 30)[1] & DPAD_LEFT)
        self.assertEqual(record(left_blob, 30)[4:], bytes((NEUTRAL_AXIS,) * 4))
        self.assertFalse(record(left_blob, 30)[1] & DPAD_RIGHT)
        self.assertTrue(record(left_blob, 300)[1] & DPAD_LEFT)
        self.assertFalse(record(left_blob, STEERING_HOLD_FRAMES)[1] & DPAD_LEFT)

        neutral_blob = build_dtm(3600, steering="none")
        for frame in (0, 30, 100, 2020, 3000):
            with self.subTest(frame=frame):
                self.assertFalse(record(neutral_blob, frame)[1] & DPAD_LEFT)
                self.assertFalse(record(neutral_blob, frame)[1] & DPAD_RIGHT)
                self.assertEqual(record(neutral_blob, frame)[4:], bytes((NEUTRAL_AXIS,) * 4))

    def test_analog_stick_steering_profiles_encode_left_right_and_release(self) -> None:
        right_blob = build_dtm(3600, steering="right", steering_source="stick")
        right_pressed = record(right_blob, 30)
        self.assertFalse(right_pressed[1] & (DPAD_LEFT | DPAD_RIGHT))
        self.assertEqual(right_pressed[2:4], bytes((0, 0)))  # analog triggers released
        self.assertEqual(right_pressed[4], 255)  # full-right main stick
        self.assertEqual(right_pressed[5], NEUTRAL_AXIS)  # no unintended pitch
        self.assertEqual(right_pressed[6:], bytes((NEUTRAL_AXIS, NEUTRAL_AXIS)))
        self.assertEqual(record(right_blob, STEERING_HOLD_FRAMES)[4], NEUTRAL_AXIS)

        left_blob = build_dtm(3600, steering="left", steering_source="stick")
        left_pressed = record(left_blob, 30)
        self.assertFalse(left_pressed[1] & (DPAD_LEFT | DPAD_RIGHT))
        self.assertEqual(left_pressed[4], 0)  # full-left main stick
        self.assertEqual(left_pressed[5], NEUTRAL_AXIS)
        self.assertEqual(record(left_blob, STEERING_HOLD_FRAMES)[4], NEUTRAL_AXIS)

        neutral_blob = build_dtm(3600, steering="none", steering_source="stick")
        for frame in (0, 30, 100, 599, 600, 3000):
            with self.subTest(frame=frame):
                self.assertEqual(record(neutral_blob, frame)[4:6],
                                 bytes((NEUTRAL_AXIS, NEUTRAL_AXIS)))
                self.assertFalse(record(neutral_blob, frame)[1] & (DPAD_LEFT | DPAD_RIGHT))

    def test_rejects_unknown_steering_source(self) -> None:
        with self.assertRaises(ValueError):
            build_dtm(10, steering_source="both")  # type: ignore[arg-type]

    def test_reset_check_profile_builds_state_then_presses_y_once(self) -> None:
        blob = build_dtm(3600, steering="right", steering_source="stick",
                         scenario="reset-check")

        initial = record(blob, 0)
        self.assertEqual(initial[0], A)
        self.assertTrue(initial[1] & IS_CONNECTED)
        self.assertEqual(initial[4], 255)  # Right stick, before reset
        self.assertEqual(initial[5], NEUTRAL_AXIS)

        boosted = record(blob, 1)
        self.assertEqual(boosted[0], A | X)
        self.assertEqual(boosted[4], 255)
        before_reset = record(blob, RESET_PRESS_FRAME - 1)
        self.assertEqual(before_reset[0], A)
        self.assertEqual(before_reset[4], 255)
        self.assertFalse(before_reset[1] & DPAD_RIGHT)

        boost_release = record(blob, RESET_BOOST_END_FRAME)
        self.assertEqual(boost_release[0], A)
        self.assertEqual(boost_release[4], 255)

        reset = record(blob, RESET_PRESS_FRAME)
        self.assertEqual(reset[0], Y)  # Y alone: do not hide a reset edge
        self.assertTrue(reset[1] & IS_CONNECTED)
        self.assertFalse(reset[1] & (DPAD_LEFT | DPAD_RIGHT))
        self.assertEqual(reset[4:], bytes((NEUTRAL_AXIS,) * 4))

        for frame in (RESET_PRESS_FRAME + 1, RESET_PRESS_FRAME + 2, 599, 600, 3599):
            with self.subTest(frame=frame):
                state = record(blob, frame)
                self.assertEqual(state[0], 0)  # no input after the reset edge
                self.assertTrue(state[1] & IS_CONNECTED)
                self.assertEqual(state[2:4], bytes((0, 0)))
                self.assertEqual(state[4:], bytes((NEUTRAL_AXIS,) * 4))

    def test_full_race_profile_keeps_throttle_and_neutral_steering(self) -> None:
        frames = 6000
        blob = build_dtm(frames, steering="none", scenario="full-race")
        self.assertEqual(len(blob), HEADER_SIZE + frames * 8)
        self.assertEqual(struct.unpack_from("<Q", blob, 0x0D)[0], frames)

        for frame in (0, 1, 79, 80, 219, 220, 280, 3599, 5999):
            with self.subTest(frame=frame):
                state = record(blob, frame)
                self.assertTrue(state[0] & A)
                self.assertFalse(state[0] & (B | START))
                self.assertTrue(state[1] & IS_CONNECTED)
                self.assertFalse(state[1] & (DPAD_LEFT | DPAD_RIGHT))
                self.assertEqual(state[4:], bytes((NEUTRAL_AXIS,) * 4))
                self.assertEqual(bool(state[0] & Y), frame == 0)
                self.assertEqual(bool(state[0] & X), 1 <= frame < 80)

    def test_full_race_profile_rejects_directional_steering(self) -> None:
        with self.assertRaises(ValueError):
            build_dtm(10, steering="right", scenario="full-race")

    @unittest.skipIf(
        Image is None or ImageDraw is None or road_center_from_asphalt is None,
        "Pillow is not installed in the lightweight host-test environment",
    )
    def test_asphalt_center_estimator_is_independent_of_desert_ground_color(self) -> None:
        image = Image.new("RGB", (800, 480), (133, 98, 60))
        draw = ImageDraw.Draw(image)
        y0, y1 = int(480 * 0.65), int(480 * 0.72) - 1
        draw.rectangle((300, y0, 500, y1), fill=(37, 43, 59))
        center, rows = road_center_from_asphalt(image)
        self.assertAlmostEqual(center, 400.0)
        self.assertGreaterEqual(rows, 10)

        shifted = Image.new("RGB", (800, 480), (133, 98, 60))
        shifted_draw = ImageDraw.Draw(shifted)
        shifted_draw.rectangle((260, y0, 460, y1), fill=(45, 51, 67))
        shifted_center, shifted_rows = road_center_from_asphalt(shifted)
        self.assertAlmostEqual(shifted_center, 360.0)
        self.assertGreaterEqual(shifted_rows, 10)

    @unittest.skipIf(
        Image is None or ImageDraw is None or player_pod_bounds is None,
        "Pillow is not installed in the lightweight host-test environment",
    )
    def test_pod_bounds_ignore_sparse_color_outliers_but_reject_real_clipping(self) -> None:
        cyan = (33, 164, 220)
        image = Image.new("RGB", (800, 480), (105, 170, 225))
        draw = ImageDraw.Draw(image)
        draw.rectangle((310, 350, 370, 400), fill=cyan)
        draw.rectangle((470, 350, 540, 400), fill=cyan)
        # A couple of unrelated background pixels should not make the pod look
        # clipped, but their color is intentionally identical to the pod mask.
        image.putpixel((116, 350), cyan)
        image.putpixel((799, 350), cyan)

        center, left, right, pixel_count = player_pod_bounds(image)
        self.assertGreater(center, 400.0)
        self.assertLess(center, 450.0)
        self.assertGreater(left, 300)
        self.assertLess(left, 325)
        self.assertGreater(right, 525)
        self.assertLess(right, 550)
        self.assertGreater(pixel_count, 6000)

        clipped = Image.new("RGB", (800, 480), (105, 170, 225))
        clipped_draw = ImageDraw.Draw(clipped)
        clipped_draw.rectangle((310, 350, 370, 400), fill=cyan)
        clipped_draw.rectangle((470, 350, 540, 400), fill=cyan)
        clipped_draw.rectangle((0, 350, 40, 400), fill=cyan)
        with self.assertRaises(ValueError):
            player_pod_bounds(clipped)

    @unittest.skipIf(
        Image is None or ImageDraw is None or finish_banner_visible is None,
        "Pillow is not installed in the lightweight host-test environment",
    )
    def test_finish_detector_requires_the_centered_checkerboard(self) -> None:
        image = Image.new("RGB", (800, 480), (8, 18, 30))
        draw = ImageDraw.Draw(image)
        cx, cy, tile_w, tile_h = 400.0, 280.0, 17.5, 11.7
        left, top = cx - 2 * tile_w, cy - 1.5 * tile_h
        for row in range(3):
            for col in range(4):
                color = (238, 246, 255) if (row + col) % 2 == 0 else (12, 18, 27)
                x0 = round(left + col * tile_w)
                y0 = round(top + row * tile_h)
                x1 = round(left + (col + 1) * tile_w - 1)
                y1 = round(top + (row + 1) * tile_h - 1)
                draw.rectangle((x0, y0, x1, y1), fill=color)
        self.assertTrue(finish_banner_visible(image))

        pause = Image.new("RGB", (800, 480), (8, 18, 30))
        pause_draw = ImageDraw.Draw(pause)
        pause_draw.rectangle((387, 263, 396, 297), fill=(238, 246, 255))
        pause_draw.rectangle((404, 263, 413, 297), fill=(238, 246, 255))
        self.assertFalse(finish_banner_visible(pause))

    @unittest.skipIf(
        Image is None or ImageDraw is None or reset_state_visible is None,
        "Pillow is not installed in the lightweight host-test environment",
    )
    def test_reset_state_detector_requires_zero_speed_heat_lap_and_full_boost(self) -> None:
        image = Image.new("RGB", (800, 480), (8, 18, 30))
        draw = ImageDraw.Draw(image)
        empty = (48, 66, 80)
        # Draw the five horizontal HUD bars at the exact reset-state positions.
        for y0, y1 in ((444, 455), (428, 435), (406, 413), (414, 421), (398, 405)):
            draw.rectangle((24, y0, 213, y1), fill=empty)
        draw.rectangle((24, 428, 213, 435), fill=(255, 157, 61))
        # The reset steering tick is centered at screen x=400 and remains visible.
        draw.rectangle((398, 434, 401, 449), fill=(238, 246, 255))
        self.assertTrue(reset_state_visible(image))

        accelerated = image.copy()
        ImageDraw.Draw(accelerated).rectangle((24, 444, 80, 455), fill=(64, 220, 243))
        self.assertFalse(reset_state_visible(accelerated))

        boost_not_refilled = image.copy()
        ImageDraw.Draw(boost_not_refilled).rectangle((130, 428, 213, 435), fill=empty)
        self.assertFalse(reset_state_visible(boost_not_refilled))

        lap_progress = image.copy()
        ImageDraw.Draw(lap_progress).rectangle((24, 414, 54, 421), fill=(137, 241, 154))
        self.assertFalse(reset_state_visible(lap_progress))

        heat_not_cleared = image.copy()
        ImageDraw.Draw(heat_not_cleared).rectangle((24, 406, 44, 413), fill=(255, 75, 58))
        self.assertFalse(reset_state_visible(heat_not_cleared))

        completed_lap = image.copy()
        ImageDraw.Draw(completed_lap).rectangle((24, 398, 44, 405), fill=(137, 241, 154))
        self.assertFalse(reset_state_visible(completed_lap))

    def test_custom_game_id_must_be_exactly_six_ascii_bytes(self) -> None:
        blob = build_dtm(1, "ID-boo")
        self.assertEqual(blob[4:10], b"ID-boo")
        for invalid in ("", "A" * 7, "é" * 6):
            with self.subTest(invalid=invalid):
                with self.assertRaises((ValueError, UnicodeEncodeError)):
                    build_dtm(1, invalid)

    def test_rejects_invalid_frame_counts(self) -> None:
        for invalid in (0, -1, 12001, True, 3.5):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    build_dtm(invalid)


if __name__ == "__main__":
    unittest.main()
