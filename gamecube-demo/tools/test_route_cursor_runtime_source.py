"""Source-contract checks for the runtime route-cursor integration."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "gamecube-demo" / "source" / "main.c"


class RouteCursorRuntimeSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = MAIN.read_text(encoding="utf-8")

    def test_runtime_owns_generated_topology_cursor_and_sampler(self):
        self.assertIn("static BoontaRouteGraphSampler g_route_sampler;", self.source)
        self.assertIn("static BoontaRouteCursor g_route_cursor;", self.source)
        self.assertIn("boonta_runtime_route_topology_edges", self.source)
        self.assertIn("BOONTA_RUNTIME_ROUTE_START_NODE_INDEX", self.source)
        self.assertIn("BOONTA_RUNTIME_ROUTE_CLOSED_LOOP", self.source)

    def test_single_loop_uses_direct_sampler_and_branching_keeps_cursor_adapter(self):
        start = self.source.index("static void track_sample_at(")
        end = self.source.index("static float track_center_x_at", start)
        block = self.source[start:end]
        single_loop = block.split("#if BOONTA_RUNTIME_ROUTE_IS_SINGLE_LOOP", 1)[1].split("#else", 1)[0]
        branched = block.split("#else", 1)[1].split("#endif", 1)[0]

        self.assertIn("boonta_route_graph_sampler_sample_at", single_loop)
        self.assertNotIn("sample_relative_to_cursor", single_loop)
        self.assertIn("two full cursor/history copies", single_loop)

        self.assertIn("if (g_route_cursor_ready", branched)
        self.assertIn("boonta_route_graph_sampler_sample_relative_to_cursor", branched)
        self.assertIn("boonta_route_graph_sampler_sample_cursor_at", branched)

    def test_single_loop_direct_and_cursor_relative_samplers_are_equivalent(self):
        # The C regression test compares their positions and widths across the
        # complete closed-loop seam, including negative start-line look-behind.
        test_source = (
            ROOT / "gamecube-demo" / "tests" / "test_route_graph_sampling.c"
        ).read_text(encoding="utf-8")
        self.assertIn("test_cursor_relative_sampling_matches_loop_across_seam", test_source)
        self.assertIn("sample(target_distance", test_source)

    def test_cursor_is_reset_at_startup_and_on_race_reset(self):
        self.assertGreaterEqual(self.source.count("(void)reset_runtime_route_cursor();"), 2)
        self.assertIn("boonta_route_cursor_init(", self.source)

    def test_cursor_advances_with_steering_and_uses_route_laps_for_branches(self):
        marker = "g_distance = boonta_distance_after_pitch_scaled("
        distance_index = self.source.index(marker)
        update_index = self.source.index(
            "advance_runtime_route_cursor(", distance_index
        )
        call = self.source[update_index:update_index + 220]
        self.assertIn("g_distance - previous_distance, steering)", call)
        branch_lap_index = self.source.index(
            "g_lap_count = route_state.completed_laps;", distance_index
        )
        legacy_lap_index = self.source.index(
            "g_lap_count = boonta_lap_count_after_frame(", distance_index
        )
        self.assertLess(distance_index, update_index)
        self.assertLess(update_index, branch_lap_index)
        self.assertLess(branch_lap_index, legacy_lap_index)
        self.assertIn("g_distance = previous_distance;", self.source[update_index:branch_lap_index])

    def test_branch_runtime_primes_lookahead_and_maps_steering_direction(self):
        start = self.source.index("static int advance_runtime_route_cursor(")
        end = self.source.index("static void track_sample_at(", start)
        block = self.source[start:end]
        self.assertIn("BOONTA_RUNTIME_ROUTE_HAS_BRANCHES", block)
        self.assertIn("ROUTE_BRANCH_STEERING_DEADZONE", block)
        self.assertIn("steering < -ROUTE_BRANCH_STEERING_DEADZONE ? -1", block)
        self.assertIn("steering > ROUTE_BRANCH_STEERING_DEADZONE ? 1", block)
        self.assertIn("boonta_route_graph_sampler_prime_lookahead(", block)
        self.assertIn("boonta_route_cursor_move(", block)

    def test_branched_hud_progress_uses_active_cursor_span(self):
        start = self.source.index("static float current_lap_progress(void)")
        end = self.source.index("static void append_formatted_time(", start)
        block = self.source[start:end]
        self.assertIn("BOONTA_RUNTIME_ROUTE_HAS_BRANCHES", block)
        self.assertIn("boonta_route_cursor_lap_progress", block)
        self.assertIn("fmodf(g_distance, RACE_LAP_DISTANCE)", block)
        self.assertIn("g_race_finished", block)

    def test_branch_finish_stripe_uses_selected_path_history(self):
        self.assertIn("boonta_route_cursor_distance_to_next_lap(", self.source)
        self.assertIn("ROUTE_RENDER_LOOKAHEAD_DISTANCE", self.source)
        self.assertIn("ROUTE_BRANCH_SELECTION_DISTANCE", self.source)

    def test_cursor_failure_pauses_route_distance_without_corrupting_history(self):
        start = self.source.index("static int advance_runtime_route_cursor(")
        end = self.source.index("static void track_sample_at(", start)
        block = self.source[start:end]
        self.assertIn("return boonta_route_cursor_move(", block)
        self.assertIn("BOONTA_ROUTE_CURSOR_OK", block)
        self.assertIn("g_distance = previous_distance;", self.source)


if __name__ == "__main__":
    unittest.main()
