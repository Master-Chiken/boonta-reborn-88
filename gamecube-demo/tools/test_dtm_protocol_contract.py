"""Guard the raw Dolphin DTM input invariants used by the visual capture CI.

These checks live separately from test_dolphin_dtm.py so an older candidate
branch cannot weaken its own assertions and silently revert the protocol fix.
"""
from __future__ import annotations

import unittest

from make_dolphin_dtm import (
    CONTROLLER_STATE_SIZE,
    HEADER_SIZE,
    NEUTRAL_AXIS,
    STEERING_HOLD_FRAMES,
    build_dtm,
)


class DtmProtocolContractTests(unittest.TestCase):
    def test_raw_dtm_analog_axes_use_unsigned_center(self) -> None:
        self.assertEqual(
            NEUTRAL_AXIS,
            128,
            "Dolphin DTM stores raw analog axes as unsigned bytes centered at 128.",
        )

    def test_generated_records_keep_all_analog_axes_neutral(self) -> None:
        expected = bytes((128, 128, 128, 128))
        for steering in ("none", "left", "right"):
            blob = build_dtm(24, steering=steering)
            for frame in (0, 5, 23):
                offset = HEADER_SIZE + frame * CONTROLLER_STATE_SIZE
                with self.subTest(steering=steering, frame=frame):
                    self.assertEqual(blob[offset + 4:offset + 8], expected)

    def test_capture_steering_hold_stays_inside_validated_window(self) -> None:
        self.assertGreater(STEERING_HOLD_FRAMES, 0)
        self.assertLessEqual(
            STEERING_HOLD_FRAMES,
            600,
            "The Software Renderer capture is validated with a 600-frame input hold; "
            "longer holds can push the pod off-frame and need fresh visual evidence.",
        )


if __name__ == "__main__":
    unittest.main()
