from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "source" / "main.c").read_text(encoding="utf-8")


class GXColorPipelineTests(unittest.TestCase):
    def test_disabled_lighting_passes_vertex_material_color(self) -> None:
        # With lighting disabled, matsrc selects the color passed to the rasterizer.
        # The procedural world supplies per-vertex colors through GX_Color4u8().
        self.assertRegex(
            SOURCE,
            re.compile(
                r"GX_SetChanCtrl\(\s*GX_COLOR0A0\s*,\s*GX_DISABLE\s*,"
                r"\s*GX_SRC_REG\s*,\s*GX_SRC_VTX\s*,",
                re.MULTILINE,
            ),
        )

    def test_vertex_color_attribute_is_enabled(self) -> None:
        self.assertIn("GX_SetVtxDesc(GX_VA_CLR0, GX_DIRECT);", SOURCE)
        self.assertIn(
            "GX_SetVtxAttrFmt(GX_VTXFMT0, GX_VA_CLR0, GX_CLR_RGBA, GX_RGBA8, 0);",
            SOURCE,
        )

    def test_tev_stage_passes_raster_color(self) -> None:
        self.assertIn("GX_SetTevOp(GX_TEVSTAGE0, GX_PASSCLR);", SOURCE)
        self.assertIn(
            "GX_SetTevOrder(GX_TEVSTAGE0, GX_TEXCOORDNULL, GX_TEXMAP_NULL, GX_COLOR0A0);",
            SOURCE,
        )

    def test_hud_binds_position_matrix_for_orthographic_vertices(self) -> None:
        hud = SOURCE.split("static void draw_hud(void)", 1)[1].split(
            "static void initialise_video_and_gx", 1
        )[0]
        position_load = hud.index("GX_LoadPosMtxImm(identity, GX_PNMTX0);")
        matrix_bind = hud.index("GX_SetCurrentMtx(GX_PNMTX0);")
        projection_load = hud.index("GX_LoadProjectionMtx(ortho, GX_ORTHOGRAPHIC);")
        hud_draw = hud.index("draw_vertex_buffer();")
        self.assertLess(position_load, matrix_bind)
        self.assertLess(matrix_bind, projection_load)
        self.assertLess(projection_load, hud_draw)

    def test_hud_screen_quads_use_negative_orthographic_depth(self) -> None:
        helper = SOURCE.split("static void append_screen_quad", 1)[1].split(
            "static void append_text", 1
        )[0]
        self.assertIn("const float clip_z = -z;", helper)
        self.assertEqual(helper.count("clip_z }"), 4)



if __name__ == "__main__":
    unittest.main()
