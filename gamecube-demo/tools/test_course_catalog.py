"""Source-level checks for the selectable native course catalog."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "gamecube-demo" / "source"


class CourseCatalogTests(unittest.TestCase):
    def test_catalog_registers_three_distinct_courses(self):
        catalog = (SOURCE / "course_catalog.h").read_text(encoding="utf-8")
        registry = (SOURCE / "course_catalog.c").read_text(encoding="utf-8")
        self.assertIn("#define BOONTA_COURSE_COUNT 3U", catalog)
        for symbol in ("canyon_run", "red_dunes", "basalt_spiral"):
            self.assertIn(f"boonta_course_{symbol}", catalog)
            self.assertIn(f"&boonta_course_{symbol}", registry)

    def test_each_course_uses_its_own_generated_route_and_metadata(self):
        courses = {
            "course_canyon_run.c": ("generated_route_graph.h", "canyon-run", "CANYON RUN"),
            "course_red_dunes.c": ("generated_route_graph_red_dunes.h", "red-dune-circuit", "RED DUNE CIRCUIT"),
            "course_basalt_spiral.c": ("generated_route_graph_basalt_spiral.h", "basalt-spiral", "BASALT SPIRAL"),
        }
        for filename, (header, course_id, display_name) in courses.items():
            with self.subTest(course=filename):
                source = (SOURCE / filename).read_text(encoding="utf-8")
                self.assertIn(header, source)
                self.assertIn(f'"{course_id}"', source)
                self.assertIn(f'"{display_name}"', source)
                self.assertIn('"course_runtime_impl.h"', source)

    def test_runtime_selects_catalog_entries_and_uses_course_finish_distance(self):
        main = (SOURCE / "main.c").read_text(encoding="utf-8")
        self.assertIn("boonta_course_catalog[g_selected_course_index]", main)
        self.assertIn('"COURSE SELECT"', main)
        self.assertIn("BOONTA_BUTTON_LEFT | BOONTA_BUTTON_RIGHT", main)
        self.assertIn("g_current_course->sample", main)
        self.assertIn("g_current_course->distance_to_next_finish", main)
        self.assertIn("g_current_course->lap_distance", main)


if __name__ == "__main__":
    unittest.main()
