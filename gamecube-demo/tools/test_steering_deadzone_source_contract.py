"""Source-contract tests for the analog steering deadzone call path."""
from pathlib import Path
import re
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = REPOSITORY_ROOT / "gamecube-demo" / "source"
MAIN_SOURCE = SOURCE_DIR / "main.c"
INPUT_BACKEND_SOURCE = SOURCE_DIR / "input_backend.c"


class SteeringDeadzoneSourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = MAIN_SOURCE.read_text(encoding="utf-8")
        main_start = source.rfind("int main(")
        if main_start < 0:
            raise AssertionError("GameCube main entry point was not found")
        cls.main_loop = source[main_start:]
        cls.input_backend = INPUT_BACKEND_SOURCE.read_text(encoding="utf-8")

    def test_analog_stick_and_dpad_flow_through_steering_input(self):
        source = self.main_loop
        self.assertIn("boonta_input_poll(&input);", source)
        self.assertIn("stick_x = (s8)input.stick_x;", source)
        self.assertIn("stick_y = (s8)input.stick_y;", source)
        pattern = re.compile(
            r"steering\\s*=\\s*boonta_steering_after_pitch\\s*\\(\\s*"
            r"boonta_steering_input\\s*\\((.*?)\\)\\s*,\\s*pitch_down\\s*\\)",
            re.DOTALL,
        )
        match = pattern.search(source)
        self.assertIsNotNone(
            match,
            "the primary steering path must pass boonta_steering_input through pitch handling",
        )
        arguments = match.group(1)
        self.assertIn("(float)stick_x", arguments)
        self.assertIn("(buttons_held & BOONTA_BUTTON_LEFT) != 0U", arguments)
        self.assertIn("(buttons_held & BOONTA_BUTTON_RIGHT) != 0U", arguments)

    def test_gamecube_pad_backend_remains_available(self):
        source = self.input_backend
        self.assertIn("#ifdef BOONTA_WII", source)
        self.assertIn("#include <wiiuse/wpad.h>", source)
        self.assertIn("#include <ogc/pad.h>", source)
        self.assertIn("PAD_ScanPads();", source)
        self.assertIn("PAD_StickX(0)", source)
        self.assertIn("PAD_StickY(0)", source)

    def test_wii_backend_requires_classic_expansion(self):
        source = self.input_backend
        self.assertIn("WPAD_Probe(WPAD_CHAN_0, &expansion_type)", source)
        self.assertIn("expansion_type != WPAD_EXP_CLASSIC", source)
        self.assertIn("data->exp.type != WPAD_EXP_CLASSIC", source)
        self.assertIn("return;", source)

    def test_deadzone_mapping_stays_in_gameplay_state_helper(self):
        header = (
            SOURCE_DIR / "gameplay_state.h"
        ).read_text(encoding="utf-8")
        self.assertIn("if (stick_x > 16.0f)", header)
        self.assertIn("else if (stick_x < -16.0f)", header)
        self.assertIn("(stick_x - 16.0f) / 111.0f", header)
        self.assertIn("(stick_x + 16.0f) / 112.0f", header)


if __name__ == "__main__":
    unittest.main()
