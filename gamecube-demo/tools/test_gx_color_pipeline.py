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

    def test_player_mesh_uses_the_validated_texture_stage_and_track_frame(self) -> None:
        draw = SOURCE.split("static int draw_player_pod_asset(", 1)[1].split(
            "static void append_screen_quad", 1
        )[0]
        self.assertIn("boonta_mesh_validate(mesh) != BOONTA_MESH_VALID", draw)
        self.assertIn("GX_LoadTexObj(&g_pod_texture, GX_TEXMAP0);", draw)
        self.assertIn("GX_SetTevOp(GX_TEVSTAGE0, GX_MODULATE);", draw)
        self.assertIn("GX_TexCoord2f32(v->u, v->v);", draw)
        self.assertIn("track_vehicle_local_to_world(local);", draw)
        self.assertIn("GX_SetVtxDesc(GX_VA_TEX0, GX_NONE);", draw)
        self.assertIn("GX_SetTevOp(GX_TEVSTAGE0, GX_PASSCLR);", draw)

    def test_source_texture_is_aligned_copied_cached_and_rgb565(self) -> None:
        self.assertIn(
            "static u16 g_pod_texture_pixels[POD_TEXTURE_WIDTH * POD_TEXTURE_HEIGHT] ATTRIBUTE_ALIGN(32);",
            SOURCE,
        )
        self.assertIn("boonta_generated_texture_original_twin_engine_panel_pixels", SOURCE)
        self.assertIn("memcpy(g_pod_texture_pixels,", SOURCE)
        self.assertIn("DCFlushRange(g_pod_texture_pixels, sizeof(g_pod_texture_pixels));", SOURCE)
        self.assertIn("GX_TF_RGB565", SOURCE)
        self.assertIn("GX_CLAMP, GX_CLAMP, GX_FALSE", SOURCE)

    def test_player_source_mesh_replaces_side_debug_meshes(self) -> None:
        frame = SOURCE.split("static void draw_frame(void)", 1)[1].split(
            "int main(", 1
        )[0]
        self.assertIn('#include "generated_mesh_player_pod.h"', SOURCE)
        self.assertIn('#include "generated_texture_player_pod.h"', SOURCE)
        self.assertIn("add_player_exhaust();", frame)
        self.assertIn(
            "draw_player_pod_asset(&boonta_generated_mesh_original_twin_engine_racer_view)",
            frame,
        )
        self.assertNotIn("draw_synthetic_mesh(", frame)
        self.assertNotIn("boonta_generated_mesh_original_synthetic_triangle_view", frame)
        self.assertNotIn("boonta_generated_mesh_original_synthetic_diamond_view", frame)

    def test_canyon_uses_contiguous_varied_ridge_profile_and_rock_fins(self) -> None:
        profile = SOURCE.split("static float canyon_ridge_height_for_phase", 1)[1].split(
            "static void add_canyon_scenery", 1
        )[0]
        scenery = SOURCE.split("static void add_canyon_scenery(void)", 1)[1].split(
            "static void add_player_exhaust", 1
        )[0]
        self.assertIn("switch (phase % 10U)", profile)
        self.assertIn("case 2U: return 5.20f;", profile)
        self.assertIn("case 7U: return 5.55f;", profile)
        self.assertIn("canyon_ridge_height_for_phase(ridge_phase + 1U)", scenery)
        self.assertIn("if ((ridge_phase % 6U) == 2U)", scenery)
        self.assertIn("triangle_add(top_near, ridge_peak, top_far, ridge_face);", scenery)
        self.assertIn("triangle_add(ridge_peak, ridge_shoulder, top_far, C_CANYON_MID);", scenery)
        self.assertIn("g_track_world_transform_enabled = 1;", scenery)
        self.assertIn("g_track_world_transform_enabled = 0;", scenery)

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


    def test_quad_builder_keeps_finish_quads_inside_buffer_capacity(self) -> None:
        self.assertRegex(SOURCE, r"#define VERTEX_CAPACITY\s+8192U")
        quad = SOURCE.split("static void quad_add", 1)[1].split(
            "static void box_face", 1
        )[0]
        self.assertIn(
            "if ((unsigned int)g_vertex_count + 6U > VERTEX_CAPACITY) return;",
            quad,
        )

    def test_finish_banner_has_readable_label_and_required_glyphs(self) -> None:
        self.assertRegex(SOURCE, r"\['F'\]\s*=\s*\{31,16,16,30,16,16,16\}")
        self.assertRegex(SOURCE, r"\['N'\]\s*=\s*\{17,25,21,19,17,17,17\}")
        finish = SOURCE.split("/* Finish banner:", 1)[1].split(
            "} else if (g_paused)", 1
        )[0]
        self.assertIn(
            'append_text("FINISH", cx - 18.0f, cy - 30.0f, 1.0f, boost_fill);',
            finish,
        )
        self.assertIn("for (row = 0; row < 3U; ++row)", finish)
        self.assertIn("for (col = 0; col < 4U; ++col)", finish)



if __name__ == "__main__":
    unittest.main()
