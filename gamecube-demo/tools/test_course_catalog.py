"""Source-level checks for the selectable clean-room course catalogue."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "gamecube-demo" / "source"


class CourseCatalogTests(unittest.TestCase):
    def test_catalog_registers_canyon_run_and_fork_run(self):
        catalog = (SOURCE / "course_catalog.h").read_text(encoding="utf-8")
        registry = (SOURCE / "course_catalog.c").read_text(encoding="utf-8")
        self.assertIn("#define BOONTA_COURSE_COUNT 2U", catalog)
        self.assertIn("boonta_course_canyon_run", catalog)
        self.assertIn("boonta_course_fork_run", catalog)
        self.assertIn("&boonta_course_canyon_run", registry)
        self.assertIn("&boonta_course_fork_run", registry)

    def test_both_courses_use_the_shared_runtime_adapter(self):
        canyon = (SOURCE / "course_canyon_run.c").read_text(encoding="utf-8")
        fork = (SOURCE / "course_fork_run.c").read_text(encoding="utf-8")
        self.assertIn('"generated_route_graph.h"', canyon)
        self.assertIn('"canyon-run"', canyon)
        self.assertIn('"CANYON RUN"', canyon)
        self.assertIn('"course_runtime_impl.h"', canyon)
        self.assertIn('"generated_fork_run_route_graph.h"', fork)
        self.assertIn('"fork-run"', fork)
        self.assertIn('"FORK RUN"', fork)
        self.assertIn('"course_runtime_impl.h"', fork)

    def test_runtime_defaults_to_canyon_run_and_selects_from_ready_screen(self):
        main = (SOURCE / "main.c").read_text(encoding="utf-8")
        self.assertIn("g_course_index = 0U;", main)
        self.assertIn("g_current_course = boonta_course_catalog[g_course_index];", main)
        self.assertIn("g_current_course->sample", main)
        self.assertIn("g_current_course->distance_to_next_finish", main)
        self.assertIn("g_current_course->lap_distance", main)
        self.assertIn("boonta_course_selection_after_input(", main)
        self.assertIn("BOONTA_RACE_SESSION_READY", main)
        self.assertIn("BOONTA_BUTTON_LEFT", main)
        self.assertIn("BOONTA_BUTTON_RIGHT", main)
        self.assertIn('"LEFT/RIGHT SELECT"', main)


if __name__ == "__main__":
    unittest.main()
