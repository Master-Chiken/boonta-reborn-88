"""Source-level checks for the single-course gameplay engineering fixture."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "gamecube-demo" / "source"


class CourseCatalogTests(unittest.TestCase):
    def test_catalog_contains_only_the_canyon_run_fixture(self):
        catalog = (SOURCE / "course_catalog.h").read_text(encoding="utf-8")
        registry = (SOURCE / "course_catalog.c").read_text(encoding="utf-8")
        self.assertIn("#define BOONTA_COURSE_COUNT 1U", catalog)
        self.assertIn("boonta_course_canyon_run", catalog)
        self.assertIn("&boonta_course_canyon_run", registry)
        self.assertNotIn("boonta_course_fork_run", catalog + registry)

    def test_only_the_temporary_vertical_slice_route_is_registered(self):
        source = (SOURCE / "course_canyon_run.c").read_text(encoding="utf-8")
        self.assertIn('"generated_route_graph.h"', source)
        self.assertIn('"canyon-run"', source)
        self.assertIn('"CANYON RUN"', source)
        self.assertIn('"course_runtime_impl.h"', source)

    def test_runtime_starts_on_the_single_course_without_a_selector(self):
        main = (SOURCE / "main.c").read_text(encoding="utf-8")
        self.assertIn("g_current_course = boonta_course_catalog[0];", main)
        self.assertNotIn("g_course_index", main)
        self.assertNotIn("boonta_course_selection_after_input", main)
        self.assertNotIn('"LEFT/RIGHT SELECT"', main)


if __name__ == "__main__":
    unittest.main()
