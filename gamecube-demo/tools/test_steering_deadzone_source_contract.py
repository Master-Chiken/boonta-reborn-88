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


if __name__ == "__main__":
    unittest.main()
