from __future__ import annotations

import struct
import unittest

from make_dolphin_dtm import (
    A,
    B,
    NEUTRAL_AXIS,
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
    from check_dolphin_frame import finish_banner_visible
except ImportError:
    Image = None
    ImageDraw = None
    finish_banner_visible = None


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
        self.assertTrue(record(right_blob, 300)[1] & DPAD_RIGHT)
        self.assertTrue(record(right_blob, STEERING_HOLD_FRAMES - 1)[1] & DPAD_RIGHT)
        self.assertFalse(record(right_blob, STEERING_HOLD_FRAMES)[1] & DPAD_RIGHT)
        self.assertFalse(record(right_blob, 2020)[1] & DPAD_LEFT)
        self.assertFalse(record(right_blob, 2020)[1] & DPAD_RIGHT)

        left_blob = build_dtm(3600, steering="left")
        self.assertTrue(record(left_blob, 30)[1] & DPAD_LEFT)
        self.assertFalse(record(left_blob, 30)[1] & DPAD_RIGHT)
        self.assertTrue(record(left_blob, 300)[1] & DPAD_LEFT)
        self.assertFalse(record(left_blob, STEERING_HOLD_FRAMES)[1] & DPAD_LEFT)

        neutral_blob = build_dtm(3600, steering="none")
        for frame in (0, 30, 100, 2020, 3000):
            with self.subTest(frame=frame):
                self.assertFalse(record(neutral_blob, frame)[1] & DPAD_LEFT)
                self.assertFalse(record(neutral_blob, frame)[1] & DPAD_RIGHT)

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
