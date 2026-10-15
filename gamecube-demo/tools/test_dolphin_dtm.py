from __future__ import annotations

import struct
import unittest

from make_dolphin_dtm import (
    A,
    B,
    DPAD_LEFT,
    DPAD_RIGHT,
    HEADER_SIZE,
    IS_CONNECTED,
    START,
    X,
    Y,
    build_dtm,
)


def record(blob: bytes, frame: int) -> bytes:
    start = HEADER_SIZE + frame * 8
    return blob[start:start + 8]


class DolphinDtmTests(unittest.TestCase):
    def test_header_and_fixed_record_layout(self) -> None:
        frames = 3000
        blob = build_dtm(frames)
        self.assertEqual(blob[:4], b"DTM\x1a")
        self.assertEqual(len(blob), HEADER_SIZE + frames * 8)
        self.assertEqual(blob[0x0B], 1)  # controller port 1 connected
        self.assertEqual(blob[0x0C], 0)  # starts from boot, not savestate
        self.assertEqual(struct.unpack_from("<Q", blob, 0x0D)[0], frames)
        self.assertEqual(struct.unpack_from("<Q", blob, 0x15)[0], frames)
        self.assertEqual(blob[0x89], 0)  # do not import movie settings

    def test_known_start_boost_brake_and_pause_resume_presses(self) -> None:
        blob = build_dtm(3600)
        first = record(blob, 0)
        self.assertTrue(first[0] & A)
        self.assertTrue(first[0] & Y)
        self.assertTrue(first[1] & IS_CONNECTED)
        self.assertTrue(first[1] & DPAD_RIGHT)

        boost = record(blob, 20)
        self.assertTrue(boost[0] & A)
        self.assertTrue(boost[0] & X)
        brake = record(blob, 120)
        self.assertTrue(brake[0] & B)

        pause = record(blob, 220)
        resume = record(blob, 280)
        self.assertTrue(pause[0] & START)
        self.assertTrue(resume[0] & START)
        self.assertFalse(record(blob, 221)[0] & START)
        self.assertFalse(record(blob, 281)[0] & START)

    def test_steering_direction_changes_are_deterministic(self) -> None:
        blob = build_dtm(3600)
        self.assertTrue(record(blob, 1500)[1] & DPAD_RIGHT)
        self.assertFalse(record(blob, 1500)[1] & DPAD_LEFT)
        self.assertTrue(record(blob, 2200)[1] & DPAD_LEFT)
        self.assertFalse(record(blob, 2200)[1] & DPAD_RIGHT)
        self.assertFalse(record(blob, 3000)[1] & DPAD_LEFT)
        self.assertFalse(record(blob, 3000)[1] & DPAD_RIGHT)

    def test_rejects_invalid_frame_counts(self) -> None:
        for invalid in (0, -1, 12001, True, 3.5):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    build_dtm(invalid)


if __name__ == "__main__":
    unittest.main()
