"""Original selectable course-route and header regressions."""
from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TOOLS=ROOT/"tools"/"route_graph_format"
sys.path.insert(0,str(TOOLS))
from export_runtime_route_header import generate_runtime_route_header  # noqa: E402
from validate_route_graph import validate_route_graph,sample_route_edge_lengths  # noqa: E402
COURSES=(("red-dune-circuit",3.55,"generated_route_graph_red_dunes.h"),
         ("basalt-spiral",3.25,"generated_route_graph_basalt_spiral.h"))
class CourseTests(unittest.TestCase):
 def test_route_sources_and_headers(self):
  lengths=[]
  for rid,width,hname in COURSES:
   data=ROOT/"gamecube-demo"/"data"
   graph=validate_route_graph(json.loads((data/f"{rid}-route-graph.json").read_text()))
   widths=json.loads((data/f"{rid}-surface-widths.json").read_text())
   self.assertTrue(graph["closed_loop"])
   self.assertEqual(len(graph["nodes"]),8)
   self.assertEqual(len(graph["edges"]),8)
   self.assertTrue(all(e["curve"]["type"]=="cubic_bezier" for e in graph["edges"]))
   lengths.append(sum(sample_route_edge_lengths(graph,samples=128).values()))
   expected=generate_runtime_route_header(graph,widths,default_half_width=width,distance_subdivisions=128)
   actual=(ROOT/"gamecube-demo"/"source"/hname).read_text()
   self.assertEqual(actual,expected)
  self.assertGreater(abs(lengths[0]-lengths[1]),10.0)
 def test_runtime_has_selectable_course_menu(self):
  s=(ROOT/"gamecube-demo"/"source"/"main.c").read_text()
  self.assertIn("boonta_course_catalog[g_selected_course_index]",s)
  self.assertIn('"COURSE SELECT"',s)
  self.assertIn("BOONTA_BUTTON_LEFT | BOONTA_BUTTON_RIGHT",s)
  self.assertIn("g_current_course->lap_distance",s)
  self.assertNotIn('#include "generated_route_graph.h"',s)
if __name__=="__main__":unittest.main()
