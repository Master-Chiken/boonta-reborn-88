"""Source-contract tests for per-course route samplers and branch-capable cursors."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
MAIN=ROOT/"gamecube-demo"/"source"/"main.c"
COURSE_IMPL=ROOT/"gamecube-demo"/"source"/"course_runtime_impl.h"
CATALOG=ROOT/"gamecube-demo"/"source"/"course_catalog.h"

class RouteCursorRuntimeSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main=MAIN.read_text(encoding="utf-8")
        cls.impl=COURSE_IMPL.read_text(encoding="utf-8")
        cls.catalog=CATALOG.read_text(encoding="utf-8")

    def test_cursor_and_sampler_are_owned_by_each_course_context(self):
        self.assertIn("BoontaRouteGraphSampler sampler;",self.impl)
        self.assertIn("BoontaRouteCursor cursor;",self.impl)
        self.assertIn("boonta_runtime_route_topology_edges",self.impl)
        self.assertIn("boonta_route_cursor_init(",self.impl)
        self.assertIn("int has_branches;",self.catalog)
        self.assertIn("void *runtime_context;",self.catalog)

    def test_single_loop_uses_direct_sampler_and_branches_use_cursor_relative_sampling(self):
        start=self.impl.index("static void boonta_course_runtime_sample(")
        end=self.impl.index("static int boonta_course_runtime_get_lap_state(",start)
        block=self.impl[start:end]
        single=block.split("#if BOONTA_RUNTIME_ROUTE_IS_SINGLE_LOOP",1)[1].split("#else",1)[0]
        branched=block.split("#else",1)[1].split("#endif",1)[0]
        self.assertIn("boonta_route_graph_sampler_sample_at",single)
        self.assertNotIn("sample_relative_to_cursor",single)
        self.assertIn("boonta_route_graph_sampler_sample_relative_to_cursor",branched)
        self.assertIn("boonta_route_graph_sampler_sample_cursor_at",branched)

    def test_main_delegates_route_lifecycle_to_selected_course(self):
        self.assertIn("g_current_course = boonta_course_catalog[g_selected_course_index]",self.main)
        self.assertIn("g_current_course->reset(",self.main)
        self.assertIn("g_current_course->advance(",self.main)
        self.assertIn("g_current_course->sample(",self.main)
        self.assertIn("advance_runtime_route_cursor(",self.main)
        self.assertIn("g_distance = previous_distance;",self.main)

    def test_branch_advance_primes_lookahead_using_steering(self):
        start=self.impl.index("static int boonta_course_runtime_advance(")
        end=self.impl.index("static void boonta_course_runtime_sample(",start)
        block=self.impl[start:end]
        self.assertIn("BOONTA_RUNTIME_ROUTE_HAS_BRANCHES",block)
        self.assertIn("BOONTA_COURSE_BRANCH_STEERING_DEADZONE",block)
        self.assertIn("steering < -BOONTA_COURSE_BRANCH_STEERING_DEADZONE ? -1",block)
        self.assertIn("steering > BOONTA_COURSE_BRANCH_STEERING_DEADZONE ? 1",block)
        self.assertIn("boonta_route_graph_sampler_prime_lookahead(",block)
        self.assertIn("boonta_route_cursor_move(",block)

    def test_hud_and_finish_marker_keep_branch_cursor_semantics(self):
        start=self.main.index("static float current_lap_progress(void)")
        end=self.main.index("static void append_formatted_time(",start)
        block=self.main[start:end]
        self.assertIn("g_current_course->has_branches",block)
        self.assertIn("g_current_course->get_lap_state(",block)
        self.assertIn("fmodf(g_distance",block)
        self.assertIn("g_race_finished",block)
        self.assertIn("boonta_route_cursor_distance_to_next_lap(",self.impl)
        self.assertIn("BOONTA_COURSE_RENDER_LOOKAHEAD_DISTANCE",self.impl)

    def test_three_catalog_entries_are_explicit(self):
        self.assertIn("boonta_course_red_dunes",self.catalog)
        self.assertIn("boonta_course_basalt_spiral",self.catalog)
        self.assertEqual(self.catalog.count("extern const BoontaCourseDefinition boonta_course_"),3)

if __name__=="__main__":
    unittest.main()
