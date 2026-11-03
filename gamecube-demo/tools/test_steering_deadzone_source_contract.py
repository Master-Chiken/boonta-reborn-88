"""Source-contract tests for the analog steering deadzone call path."""
from pathlib import Path
import re
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MAIN_SOURCE = REPOSITORY_ROOT / "gamecube-demo" / "source" / "main.c"


class SteeringDeadzoneSourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = MAIN_SOURCE.read_text(encoding="utf-8")
        main_start = source.rfind("int main(")
        if main_start < 0:
            raise AssertionError("GameCube main entry point was not found")
        cls.main_loop = source[main_start:]

    def test_analog_stick_and_dpad_flow_through_steering_input(self):
        source = self.main_loop
        self.assertIn("stick_x = PAD_StickX(0);", source)
        pattern = re.compile(
            r"steering\s*=\s*boonta_steering_after_pitch\s*\(\s*"
            r"boonta_steering_input\s*\((.*?)\)\s*,\s*pitch_down\s*\)",
            re.DOTALL,
        )
        match = pattern.search(source)
        self.assertIsNotNone(
            match,
            "the primary steering path must pass boonta_steering_input through pitch handling",
        )
        arguments = match.group(1)
        self.assertIn("(float)stick_x", arguments)
        self.assertIn("(buttons_held & PAD_BUTTON_LEFT) != 0U", arguments)
        self.assertIn("(buttons_held & PAD_BUTTON_RIGHT) != 0U", arguments)

    def test_deadzone_mapping_stays_in_gameplay_state_helper(self):
        header = (
            REPOSITORY_ROOT / "gamecube-demo" / "source" / "gameplay_state.h"
        ).read_text(encoding="utf-8")
        self.assertIn("if (stick_x > 16.0f)", header)
        self.assertIn("else if (stick_x < -16.0f)", header)
        self.assertIn("(stick_x - 16.0f) / 111.0f", header)
        self.assertIn("(stick_x + 16.0f) / 112.0f", header)


    def test_pitch_uses_analog_stick_and_dpad_up_down(self):
        self.assertIn("pitch_down = boonta_pitch_input(", self.main_loop)
        self.assertIn("(float)stick_y", self.main_loop)
        self.assertIn("(buttons_held & PAD_BUTTON_UP) != 0U", self.main_loop)
        self.assertIn("(buttons_held & PAD_BUTTON_DOWN) != 0U", self.main_loop)

    def test_slide_supports_both_digital_and_analog_triggers(self):
        self.assertIn("boonta_slide_input(", self.main_loop)
        self.assertIn("(buttons_held & PAD_TRIGGER_L) != 0U", self.main_loop)
        self.assertIn("(buttons_held & PAD_TRIGGER_R) != 0U", self.main_loop)
        self.assertIn("(unsigned char)PAD_TriggerL(0)", self.main_loop)
        self.assertIn("(unsigned char)PAD_TriggerR(0)", self.main_loop)

    def test_overtake_counter_uses_saturating_increment(self):
        self.assertIn("boonta_overtake_count_after_event(g_overtake_count)", self.main_loop)


if __name__ == "__main__":
    unittest.main()
