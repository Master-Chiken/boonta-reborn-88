"""Source-contract tests for finish/restart input ordering in the native game loop."""
from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
MAIN_SOURCE = REPOSITORY_ROOT / "gamecube-demo" / "source" / "main.c"


class FinishRestartSourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = MAIN_SOURCE.read_text(encoding="utf-8")
        main_start = source.rfind("int main(")
        if main_start < 0:
            raise AssertionError("GameCube main entry point was not found")
        cls.main_loop = source[main_start:]

    def test_reset_branch_precedes_finished_race_freeze(self):
        source = self.main_loop
        reset_gate = source.find("if (boonta_race_should_reset(")
        self.assertGreaterEqual(reset_gate, 0, "input loop must evaluate finish/reset transition")
        reset_call = source.find("boonta_race_state_reset(&g_race_state);", reset_gate)
        reset_continue = source.find("continue;", reset_call)
        live_pause_gate = source.find(
            "if (!g_race_finished && (buttons_down & PAD_BUTTON_START) != 0U)",
            reset_continue,
        )
        finished_gate = source.find("if (g_paused || g_race_finished)", live_pause_gate)

        self.assertGreater(reset_call, reset_gate, "a reset decision must clear race state")
        self.assertGreater(reset_continue, reset_call, "reset must draw/continue before normal updates")
        self.assertGreater(
            live_pause_gate,
            reset_continue,
            "live-race Start pause handling must follow the finished-race restart branch",
        )
        self.assertGreater(
            finished_gate,
            live_pause_gate,
            "the finished-race freeze must not make Start-after-finish unreachable",
        )

    def test_reset_transition_receives_start_and_y_pressed_edges(self):
        source = self.main_loop
        reset_gate = source.find("if (boonta_race_should_reset(")
        self.assertGreaterEqual(reset_gate, 0, "input loop must evaluate finish/reset transition")
        reset_continue = source.find("continue;", reset_gate)
        reset_branch = source[reset_gate:reset_continue]

        self.assertIn("(buttons_down & PAD_BUTTON_START) != 0U", reset_branch)
        self.assertIn("(buttons_down & PAD_BUTTON_Y) != 0U", reset_branch)


if __name__ == "__main__":
    unittest.main()
