"""Source contract for width-aware player lateral bounds."""
from pathlib import Path
import unittest

GAMECUBE_DEMO = Path(__file__).resolve().parents[1]
MAIN_SOURCE = GAMECUBE_DEMO / "source" / "main.c"
GAMEPLAY_HEADER = GAMECUBE_DEMO / "source" / "gameplay_state.h"


class PlayerLateralGuardTests(unittest.TestCase):
    def test_runtime_uses_guard_before_width_aware_rail_resolution(self):
        source = MAIN_SOURCE.read_text(encoding="utf-8")
        guard_at = source.find("boonta_clamp_player_lateral(")
        collision_at = source.find("boonta_is_past_rail(")
        self.assertGreaterEqual(guard_at, 0, "runtime must use the shared lateral guard")
        self.assertGreater(collision_at, guard_at, "rail collision must run after lateral guard")
        self.assertNotIn("-4.0f, 4.0f", source, "fixed +/-4 clamp makes wide rails unreachable")

    def test_guard_covers_widest_rail_plus_one_maximum_frame_step(self):
        header = GAMEPLAY_HEADER.read_text(encoding="utf-8")
        self.assertIn("BOONTA_MAX_ROAD_HALF_WIDTH + BOONTA_RAIL_OUTER_OFFSET", header)
        self.assertIn("BOONTA_MAX_LATERAL_VELOCITY * BOONTA_MAX_FRAME_SCALE", header)
        self.assertIn("BOONTA_MAX_FRAME_SCALE 3.0f", header)
        self.assertIn("BOONTA_MAX_LATERAL_VELOCITY 0.085f", header)


    def test_rendered_rails_and_collision_share_the_same_offset(self):
        source = MAIN_SOURCE.read_text(encoding="utf-8")
        header = GAMEPLAY_HEADER.read_text(encoding="utf-8")

        self.assertIn("#define BOONTA_RAIL_OUTER_OFFSET 0.28f", header)
        self.assertIn("effective_half_width + BOONTA_RAIL_OUTER_OFFSET", header)
        self.assertIn("-w0 - BOONTA_RAIL_OUTER_OFFSET", source)
        self.assertIn("-w1 - BOONTA_RAIL_OUTER_OFFSET", source)
        self.assertIn("w0 + BOONTA_RAIL_OUTER_OFFSET", source)
        self.assertIn("w1 + BOONTA_RAIL_OUTER_OFFSET", source)

    def test_collision_samples_width_at_the_rendered_player_anchor(self):
        source = MAIN_SOURCE.read_text(encoding="utf-8")
        self.assertIn("#define PLAYER_ANCHOR_LOCAL_Z 1.0f", source)
        self.assertIn("g_vehicle_anchor_local_z = PLAYER_ANCHOR_LOCAL_Z;", source)
        self.assertIn(
            "track_half_width_at(\n                g_distance + (4.0f - PLAYER_ANCHOR_LOCAL_Z))",
            source,
        )


if __name__ == "__main__":
    unittest.main()
