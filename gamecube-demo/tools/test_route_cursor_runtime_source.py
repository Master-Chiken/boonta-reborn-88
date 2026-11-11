"""Runtime source contracts for the course-owned route sampler."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "gamecube-demo" / "source"
MAIN = SOURCE / "main.c"


class CourseRuntimeSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = MAIN.read_text(encoding="utf-8")
        cls.runtime = (SOURCE / "course_runtime_impl.h").read_text(encoding="utf-8")

    def test_runtime_samples_through_selected_course_interface(self):
        start = self.main.index("static void track_sample_at(")
        end = self.main.index("static void select_course(", start)
        sampler = self.main[start:end]
        self.assertIn("g_current_course->sample", sampler)
        self.assertIn("g_course_ready", sampler)
        self.assertIn("BOONTA_REFERENCE_ROAD_HALF_WIDTH", sampler)

    def test_course_runtime_owns_and_prepares_independent_sampler(self):
        self.assertIn("BoontaRouteGraphSampler sampler;", self.runtime)
        self.assertIn("boonta_route_graph_sampler_prepare", self.runtime)
        self.assertIn("boonta_route_graph_sampler_sample_at", self.runtime)
        self.assertIn("context->sampler.lengths_ready", self.runtime)

    def test_finish_distance_is_derived_from_actual_course_length(self):
        start = self.runtime.index("static int boonta_course_runtime_distance_to_next_finish(")
        end = self.runtime.index("const BoontaCourseDefinition", start)
        finish = self.runtime[start:end]
        self.assertIn("context->sampler.total_length", finish)
        self.assertIn("floorf(player_distance", finish)
        self.assertIn("!isfinite(player_distance)", finish)
        self.assertIn("player_distance < 0.0f", finish)
        self.assertIn("BOONTA_RUNTIME_ROUTE_HAS_BRANCHES", finish)
        self.assertIn("boonta_route_cursor_distance_to_next_lap", finish)

    def test_course_selection_and_reset_reinitialize_runtime_context(self):
        start = self.main.index("static void select_course(")
        end = self.main.index("/*", start)
        selection = self.main[start:end]
        self.assertIn("boonta_course_catalog[g_selected_course_index]", selection)
        self.assertIn("boonta_race_state_reset", selection)
        self.assertIn("reset_runtime_route_cursor", selection)
        self.assertGreaterEqual(self.main.count("reset_runtime_route_cursor();"), 2)

    def test_branch_cursor_is_wired_through_the_selected_course_adapter(self):
        self.assertIn("static int advance_runtime_route_cursor(", self.main)
        self.assertIn("g_current_course->advance", self.main)
        self.assertIn("g_current_course->has_branches", self.main)
        self.assertIn("boonta_route_cursor_move(", self.runtime)
        self.assertIn("boonta_route_graph_sampler_prime_lookahead(", self.runtime)
        self.assertIn("g_current_course->distance_to_next_finish", self.main)


if __name__ == "__main__":
    unittest.main()
