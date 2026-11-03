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

    def test_track_sampling_uses_cursor_relative_adapter_with_loop_fallback(self):
        start = self.source.index("static void track_sample_at(")
        end = self.source.index("static float track_center_x_at", start)
        block = self.source[start:end]
        self.assertIn("boonta_route_graph_sampler_sample_relative_to_cursor", block)
        self.assertIn("boonta_route_graph_sampler_sample_at", block)
        self.assertIn("if (g_route_cursor_ready", block)

    def test_cursor_is_reset_at_startup_and_on_race_reset(self):
        self.assertGreaterEqual(self.source.count("(void)reset_runtime_route_cursor();"), 2)
        self.assertIn("boonta_route_cursor_init(", self.source)

    def test_cursor_advances_by_the_same_physical_distance_as_the_race(self):
        marker = "g_distance = boonta_distance_after_pitch_scaled("
        distance_index = self.source.index(marker)
        update_index = self.source.index(
            "advance_runtime_route_cursor(g_distance - previous_distance);",
            distance_index,
        )
        lap_index = self.source.index(
            "g_lap_count = boonta_lap_count_after_frame(", distance_index
        )
        self.assertLess(distance_index, update_index)
        self.assertLess(update_index, lap_index)

    def test_cursor_failure_keeps_a_safe_closed_loop_render_fallback(self):
        start = self.source.index("static void advance_runtime_route_cursor(")
        end = self.source.index("static void track_sample_at(", start)
        block = self.source[start:end]
        self.assertIn("g_route_cursor_ready = 0;", block)
        self.assertIn("BOONTA_ROUTE_CURSOR_OK", block)


if __name__ == "__main__":
    unittest.main()
