/*
 * Boonta Reborn 88 — clean-room GameCube rendering/input prototype.
 *
 * Original procedural geometry only. This small milestone validates a native
 * GX render path, controller-driven steering, throttle/brake, and a scrolling
 * test road. It does not include commercial game code, models, sounds, or data.
 */
#include <gccore.h>
#include <ogc/pad.h>
#include <ogc/gu.h>
#include <ogc/gx.h>
#include <ogc/system.h>
#include <ogc/lwp_watchdog.h>

#include "pause_state.h"
#include "gameplay_state.h"

#include <math.h>
#include <malloc.h>
#include <stdio.h>
#include <string.h>

#define GX_FIFO_SIZE       (256 * 1024)
#define VERTEX_CAPACITY    4096U
#define ROAD_SEGMENTS      32U
#define ROAD_HALF_WIDTH    3.6f
#define RACE_LAP_DISTANCE   120.0f
#define RACE_LAP_LIMIT       3U
#define LAP_INDICATOR_COUNT  RACE_LAP_LIMIT
#define ROAD_Y             (-1.05f)
#define PI_F               3.14159265358979323846f

typedef struct {
    f32 x, y, z;
} Point3;

typedef struct {
    f32 x, y, z;
    u8 r, g, b, a;
} SceneVertex;

static GXRModeObj *g_video_mode;
static void *g_framebuffers[2] = { NULL, NULL };
static void *g_gx_fifo;
static u32 g_framebuffer_index;
static SceneVertex g_vertices[VERTEX_CAPACITY];
static u16 g_vertex_count;
static float g_distance;
static unsigned int g_lap_count;
static float g_race_seconds;
static float g_lap_seconds;
static float g_last_lap_seconds;
static float g_best_lap_seconds;
static float g_speed;
static float g_player_lateral;
static float g_lateral_velocity;
static float g_boost = 1.0f;
static float g_engine_heat;
static int g_boost_overheated;
static int g_boost_active;
static float g_rival_z[BOONTA_RIVAL_COUNT];
static float g_rival_lateral[BOONTA_RIVAL_COUNT];
static unsigned int g_overtake_count;
static int g_paused;
static int g_race_finished;

static const GXColor C_GROUND = { 23, 48, 40, 255 };
static const GXColor C_ROAD_A = { 37, 43, 59, 255 };
static const GXColor C_ROAD_B = { 45, 51, 67, 255 };
static const GXColor C_EDGE_L = { 255, 94, 63, 255 };
static const GXColor C_EDGE_R = { 50, 225, 246, 255 };
static const GXColor C_RAIL_A = { 36, 98, 120, 255 };
static const GXColor C_RAIL_B = { 50, 134, 150, 255 };
static const GXColor C_MARKER = { 239, 230, 175, 255 };
static const GXColor C_POD_TOP = { 33, 164, 220, 255 };
static const GXColor C_POD_SIDE = { 17, 75, 139, 255 };
static const GXColor C_POD_ACCENT = { 70, 231, 248, 255 };
static const GXColor C_THRUST = { 255, 132, 45, 255 };
static const GXColor C_THRUST_HOT = { 255, 215, 99, 255 };

/* Compact original 5x7 glyphs for race-clock HUD text. */
static const u8 g_font5x7[128][7] = {
    ['0'] = {14,17,19,21,25,17,14}, ['1'] = {4,12,4,4,4,4,14},
    ['2'] = {14,17,1,2,4,8,31}, ['3'] = {30,1,1,14,1,1,30},
    ['4'] = {2,6,10,18,31,2,2}, ['5'] = {31,16,16,30,1,1,30},
    ['6'] = {14,16,16,30,17,17,14}, ['7'] = {31,1,2,4,8,8,8},
    ['8'] = {14,17,17,14,17,17,14}, ['9'] = {14,17,17,15,1,1,14},
    ['A'] = {14,17,17,31,17,17,17}, ['B'] = {30,17,17,30,17,17,30},
    ['E'] = {31,16,16,30,16,16,31}, ['I'] = {14,4,4,4,4,4,14},
    ['L'] = {16,16,16,16,16,16,31}, ['M'] = {17,27,21,21,17,17,17},
    ['P'] = {30,17,17,30,16,16,16}, ['S'] = {15,16,16,14,1,1,30},
    ['T'] = {31,4,4,4,4,4,4}, [':'] = {0,4,4,0,4,4,0},
    ['.'] = {0,0,0,0,0,4,4}, ['-'] = {0,0,0,31,0,0,0},
    [' '] = {0,0,0,0,0,0,0}
};


static float clampf_local(float value, float low, float high)
{
    return boonta_clamp_finite_float(value, low, high);
}

static float road_center_at(float z, float distance)
{
    const float phase = z + distance * 1.15f;
    return 2.15f * sinf(phase * 0.035f) + 0.85f * sinf(phase * 0.078f);
}

static void vertex_add(Point3 point, GXColor color)
{
    SceneVertex *v;
    if (g_vertex_count >= VERTEX_CAPACITY) return;
    v = &g_vertices[g_vertex_count++];
    v->x = point.x;
    v->y = point.y;
    v->z = point.z;
    v->r = color.r;
    v->g = color.g;
    v->b = color.b;
    v->a = color.a;
}

static void triangle_add(Point3 a, Point3 b, Point3 c, GXColor color)
{
    if ((unsigned int)g_vertex_count + 3U > VERTEX_CAPACITY) return;
    vertex_add(a, color);
    vertex_add(b, color);
    vertex_add(c, color);
}

static void quad_add(Point3 a, Point3 b, Point3 c, Point3 d, GXColor color)
{
    triangle_add(a, b, c, color);
    triangle_add(a, c, d, color);
}

static void box_face(Point3 p0, Point3 p1, Point3 p2, Point3 p3, GXColor color)
{
    quad_add(p0, p1, p2, p3, color);
}

static void box_add(float cx, float cy, float cz,
                    float hx, float hy, float hz,
                    GXColor top, GXColor side, GXColor rear)
{
    Point3 p[8];
    p[0] = (Point3){ cx - hx, cy - hy, cz - hz };
    p[1] = (Point3){ cx + hx, cy - hy, cz - hz };
    p[2] = (Point3){ cx + hx, cy + hy, cz - hz };
    p[3] = (Point3){ cx - hx, cy + hy, cz - hz };
    p[4] = (Point3){ cx - hx, cy - hy, cz + hz };
    p[5] = (Point3){ cx + hx, cy - hy, cz + hz };
    p[6] = (Point3){ cx + hx, cy + hy, cz + hz };
    p[7] = (Point3){ cx - hx, cy + hy, cz + hz };

    /* Front, rear, left, right, top and underside. */
    box_face(p[0], p[1], p[2], p[3], side);
    box_face(p[5], p[4], p[7], p[6], rear);
    box_face(p[4], p[0], p[3], p[7], side);
    box_face(p[1], p[5], p[6], p[2], side);
    box_face(p[3], p[2], p[6], p[7], top);
    box_face(p[4], p[5], p[1], p[0], rear);
}

static void add_road(void)
{
    unsigned int i;
    const Point3 ground_a = { -100.0f, ROAD_Y - 0.24f, 7.0f };
    const Point3 ground_b = {  100.0f, ROAD_Y - 0.24f, 7.0f };
    const Point3 ground_c = {  100.0f, ROAD_Y - 0.24f, -110.0f };
    const Point3 ground_d = { -100.0f, ROAD_Y - 0.24f, -110.0f };
    quad_add(ground_a, ground_b, ground_c, ground_d, C_GROUND);

    for (i = 0; i < ROAD_SEGMENTS; ++i) {
        const float z0 = 4.0f - (float)i * 2.8f;
        const float z1 = z0 - 2.8f;
        const float c0 = road_center_at(z0, g_distance);
        const float c1 = road_center_at(z1, g_distance);
        const float w = ROAD_HALF_WIDTH;
        const GXColor road = ((i & 1U) == 0U) ? C_ROAD_A : C_ROAD_B;
        const GXColor rail = ((i & 1U) == 0U) ? C_RAIL_A : C_RAIL_B;

        quad_add((Point3){ c0 - w, ROAD_Y, z0 },
                 (Point3){ c0 + w, ROAD_Y, z0 },
                 (Point3){ c1 + w, ROAD_Y, z1 },
                 (Point3){ c1 - w, ROAD_Y, z1 }, road);

        /* Two bright edge strips make the procedural course readable. */
        quad_add((Point3){ c0 - w, ROAD_Y + 0.018f, z0 },
                 (Point3){ c0 - w + 0.12f, ROAD_Y + 0.018f, z0 },
                 (Point3){ c1 - w + 0.12f, ROAD_Y + 0.018f, z1 },
                 (Point3){ c1 - w, ROAD_Y + 0.018f, z1 }, C_EDGE_L);
        quad_add((Point3){ c0 + w - 0.12f, ROAD_Y + 0.018f, z0 },
                 (Point3){ c0 + w, ROAD_Y + 0.018f, z0 },
                 (Point3){ c1 + w, ROAD_Y + 0.018f, z1 },
                 (Point3){ c1 + w - 0.12f, ROAD_Y + 0.018f, z1 }, C_EDGE_R);

        /* Low outer rails are simple original geometry, not game assets. */
        quad_add((Point3){ c0 - w - 0.28f, ROAD_Y + 0.02f, z0 },
                 (Point3){ c0 - w - 0.28f, ROAD_Y + 0.52f, z0 },
                 (Point3){ c1 - w - 0.28f, ROAD_Y + 0.52f, z1 },
                 (Point3){ c1 - w - 0.28f, ROAD_Y + 0.02f, z1 }, rail);
        quad_add((Point3){ c0 + w + 0.28f, ROAD_Y + 0.02f, z0 },
                 (Point3){ c0 + w + 0.28f, ROAD_Y + 0.52f, z0 },
                 (Point3){ c1 + w + 0.28f, ROAD_Y + 0.52f, z1 },
                 (Point3){ c1 + w + 0.28f, ROAD_Y + 0.02f, z1 }, rail);

        if ((i % 2U) == 0U) {
            const float mark_z0 = z0 - 0.35f;
            const float mark_z1 = z0 - 1.35f;
            const float mc0 = road_center_at(mark_z0, g_distance);
            const float mc1 = road_center_at(mark_z1, g_distance);
            quad_add((Point3){ mc0 - 0.055f, ROAD_Y + 0.035f, mark_z0 },
                     (Point3){ mc0 + 0.055f, ROAD_Y + 0.035f, mark_z0 },
                     (Point3){ mc1 + 0.055f, ROAD_Y + 0.035f, mark_z1 },
                     (Point3){ mc1 - 0.055f, ROAD_Y + 0.035f, mark_z1 }, C_MARKER);
        }
    }

    /* A repeating start/finish stripe gives the endless prototype a lap cue. */
    {
        const float offset = fmodf(g_distance, RACE_LAP_DISTANCE);
        const float finish_z = 4.0f - offset;
        if (finish_z > -108.0f && finish_z < 4.0f) {
            const float c0 = road_center_at(finish_z, g_distance);
            const float c1 = road_center_at(finish_z - 0.55f, g_distance);
            const float half = ROAD_HALF_WIDTH;
            const GXColor stripe = { 240, 244, 250, 255 };
            quad_add((Point3){ c0 - half, ROAD_Y + 0.04f, finish_z },
                     (Point3){ c0 + half, ROAD_Y + 0.04f, finish_z },
                     (Point3){ c1 + half, ROAD_Y + 0.04f, finish_z - 0.55f },
                     (Point3){ c1 - half, ROAD_Y + 0.04f, finish_z - 0.55f }, stripe);
        }
    }
}

static void add_player_pod(void)
{
    const float center = road_center_at(1.0f, g_distance) + g_player_lateral;

    /* Paired engine pods, rear thrusters and a central tapered-looking nose. */
    box_add(center - 0.62f, -0.62f, 1.08f,
            0.27f, 0.25f, 0.83f, C_POD_TOP, C_POD_SIDE, C_THRUST);
    box_add(center + 0.62f, -0.62f, 1.08f,
            0.27f, 0.25f, 0.83f, C_POD_TOP, C_POD_SIDE, C_THRUST);
    box_add(center, -0.49f, 0.63f, 0.54f, 0.09f, 0.18f,
            C_POD_ACCENT, C_POD_SIDE, C_POD_SIDE);

    triangle_add((Point3){ center - 0.42f, -0.52f, 0.52f },
                 (Point3){ center + 0.42f, -0.52f, 0.52f },
                 (Point3){ center, -0.28f, -0.55f }, C_POD_TOP);
    triangle_add((Point3){ center - 0.42f, -0.52f, 0.52f },
                 (Point3){ center, -0.28f, -0.55f },
                 (Point3){ center - 0.08f, -0.45f, -0.40f }, C_POD_ACCENT);
    triangle_add((Point3){ center + 0.42f, -0.52f, 0.52f },
                 (Point3){ center + 0.08f, -0.45f, -0.40f },
                 (Point3){ center, -0.28f, -0.55f }, C_POD_SIDE);

    if (g_speed > 0.12f) {
        const GXColor thrust = (g_boost_active || g_speed > 0.70f) ? C_THRUST_HOT : C_THRUST;
        box_add(center - 0.62f, -0.62f, 2.10f,
                0.13f, 0.12f, 0.36f, thrust, C_THRUST, C_THRUST);
        box_add(center + 0.62f, -0.62f, 2.10f,
                0.13f, 0.12f, 0.36f, thrust, C_THRUST, C_THRUST);
    }
}

static void add_rival_pod(float z, float lateral, unsigned int rival_index)
{
    /* Original procedural rivals have distinct colors to make the pack readable. */
    const float center = road_center_at(z, g_distance) + lateral;
    GXColor rival_top = { 220, 82, 62, 255 };
    GXColor rival_side = { 120, 39, 70, 255 };
    GXColor rival_glow = { 255, 184, 92, 255 };

    if (rival_index == 1U) {
        rival_top = (GXColor){ 170, 110, 242, 255 };
        rival_side = (GXColor){ 83, 53, 145, 255 };
        rival_glow = (GXColor){ 220, 188, 255, 255 };
    } else if (rival_index == 2U) {
        rival_top = (GXColor){ 248, 188, 54, 255 };
        rival_side = (GXColor){ 146, 82, 24, 255 };
        rival_glow = (GXColor){ 255, 232, 130, 255 };
    }

    box_add(center - 0.34f, -0.78f, z + 0.35f,
            0.15f, 0.13f, 0.42f, rival_top, rival_side, rival_glow);
    box_add(center + 0.34f, -0.78f, z + 0.35f,
            0.15f, 0.13f, 0.42f, rival_top, rival_side, rival_glow);
    box_add(center, -0.70f, z + 0.20f,
            0.30f, 0.10f, 0.28f, rival_top, rival_side, rival_side);

    triangle_add((Point3){ center - 0.42f, -0.77f, z + 0.08f },
                 (Point3){ center + 0.42f, -0.77f, z + 0.08f },
                 (Point3){ center, -0.60f, z - 0.92f }, rival_top);
    triangle_add((Point3){ center - 0.42f, -0.77f, z + 0.08f },
                 (Point3){ center, -0.60f, z - 0.92f },
                 (Point3){ center - 0.08f, -0.72f, z - 0.72f }, rival_side);
    triangle_add((Point3){ center + 0.42f, -0.77f, z + 0.08f },
                 (Point3){ center + 0.08f, -0.72f, z - 0.72f },
                 (Point3){ center, -0.60f, z - 0.92f }, rival_side);

    box_add(center - 0.34f, -0.78f, z + 0.80f,
            0.075f, 0.07f, 0.20f, rival_glow, rival_glow, rival_glow);
    box_add(center + 0.34f, -0.78f, z + 0.80f,
            0.075f, 0.07f, 0.20f, rival_glow, rival_glow, rival_glow);
}

static void draw_vertex_buffer(void)
{
    u16 i;
    GX_Begin(GX_TRIANGLES, GX_VTXFMT0, g_vertex_count);
    for (i = 0; i < g_vertex_count; ++i) {
        const SceneVertex *v = &g_vertices[i];
        GX_Position3f32(v->x, v->y, v->z);
        GX_Color4u8(v->r, v->g, v->b, v->a);
    }
    GX_End();
}

static void append_screen_quad(float x0, float y0, float x1, float y1,
                               float z, GXColor color)
{
    quad_add((Point3){ x0, y0, z }, (Point3){ x1, y0, z },
             (Point3){ x1, y1, z }, (Point3){ x0, y1, z }, color);
}

static void append_text(const char *text, float x, float y, float scale,
                         GXColor color)
{
    const unsigned char *ch;
    for (ch = (const unsigned char *)text; *ch != '\0'; ++ch) {
        const unsigned char c = (*ch < 128U) ? *ch : (unsigned char)' ';
        unsigned int row;
        unsigned int col;
        for (row = 0; row < 7U; ++row) {
            for (col = 0; col < 5U; ++col) {
                if ((g_font5x7[c][row] & (1U << (4U - col))) != 0U) {
                    const float px = x + (float)col * scale;
                    const float py = y + (float)row * scale;
                    append_screen_quad(px, py, px + scale, py + scale, 0.15f, color);
                }
            }
        }
        x += 6.0f * scale;
    }
}

static void append_formatted_time(char *buffer, size_t size, float seconds)
{
    unsigned int tenths;
    if (!isfinite(seconds) || seconds < 0.0f) seconds = 0.0f;
    if (seconds > 5999.9f) seconds = 5999.9f;
    tenths = (unsigned int)(seconds * 10.0f);
    (void)snprintf(buffer, size, "%02u:%02u.%u",
                   tenths / 600U, (tenths / 10U) % 60U, tenths % 10U);
}

static void draw_hud(void)
{
    Mtx identity;
    Mtx44 ortho;
    char time_text[20];
    char lap_text[40];
    char best_text[20];
    unsigned int lap_display;
    const float w = (float)g_video_mode->fbWidth;
    const float h = (float)g_video_mode->efbHeight;
    const GXColor dark = { 8, 18, 30, 235 };
    const GXColor empty = { 48, 66, 80, 255 };
    const GXColor fill = { 64, 220, 243, 255 };
    const GXColor boost_fill = { 255, 157, 61, 255 };
    const GXColor heat_cool = { 255, 195, 83, 255 };
    const GXColor heat_hot = { 255, 75, 58, 255 };
    const GXColor progress_fill = { 137, 241, 154, 255 };
    const GXColor lap_done = { 137, 241, 154, 255 };
    const GXColor rival_mark = { 255, 128, 88, 255 };
    const GXColor white = { 238, 246, 255, 255 };
    const float bar_left = 24.0f;
    const float bar_bottom = h - 24.0f;
    const float lap_progress = g_race_finished ? 1.0f : fmodf(g_distance, RACE_LAP_DISTANCE) / RACE_LAP_DISTANCE;
    const float bar_width = (w < 500.0f) ? 130.0f : 190.0f;

    append_formatted_time(time_text, sizeof(time_text), g_race_seconds);
    append_formatted_time(best_text, sizeof(best_text), g_best_lap_seconds);
    lap_display = g_race_finished ? g_lap_count : g_lap_count + 1U;
    {
        char lap_time[20];
        append_formatted_time(lap_time, sizeof(lap_time), g_lap_seconds);
        (void)snprintf(lap_text, sizeof(lap_text), "LAP %u %s", lap_display, lap_time);
    }

    GX_SetZMode(GX_FALSE, GX_ALWAYS, GX_FALSE);
    guMtxIdentity(identity);
    guOrtho(ortho, 0.0f, h, 0.0f, w, 0.0f, 1.0f);
    GX_LoadPosMtxImm(identity, GX_PNMTX0);
    GX_LoadProjectionMtx(ortho, GX_ORTHOGRAPHIC);

    g_vertex_count = 0;
    append_screen_quad(bar_left - 8.0f, bar_bottom - 62.0f,
                       bar_left + bar_width + 8.0f, bar_bottom + 4.0f,
                       0.5f, dark);
    append_screen_quad(bar_left, bar_bottom - 12.0f,
                       bar_left + bar_width, bar_bottom,
                       0.4f, empty);
    append_screen_quad(bar_left, bar_bottom - 12.0f,
                       bar_left + bar_width * g_speed, bar_bottom,
                       0.3f, fill);
    append_screen_quad(bar_left, bar_bottom - 28.0f,
                       bar_left + bar_width, bar_bottom - 20.0f,
                       0.4f, empty);
    append_screen_quad(bar_left, bar_bottom - 28.0f,
                       bar_left + bar_width * g_boost, bar_bottom - 20.0f,
                       0.3f, boost_fill);
    append_screen_quad(bar_left, bar_bottom - 50.0f,
                       bar_left + bar_width, bar_bottom - 42.0f,
                       0.4f, empty);
    append_screen_quad(bar_left, bar_bottom - 50.0f,
                       bar_left + bar_width * g_engine_heat, bar_bottom - 42.0f,
                       0.3f, (g_engine_heat >= 0.70f || g_boost_overheated) ? heat_hot : heat_cool);
    append_screen_quad(bar_left, bar_bottom - 42.0f,
                       bar_left + bar_width, bar_bottom - 34.0f,
                       0.4f, empty);
    append_screen_quad(bar_left, bar_bottom - 42.0f,
                       bar_left + bar_width * lap_progress, bar_bottom - 34.0f,
                       0.3f, progress_fill);
    /* One marker per configured race lap; the prototype finishes at RACE_LAP_LIMIT. */
    {
        unsigned int i;
        const float marker_gap = 4.0f;
        const float marker_width = (bar_width - marker_gap * (LAP_INDICATOR_COUNT - 1U)) / (float)LAP_INDICATOR_COUNT;
        for (i = 0; i < LAP_INDICATOR_COUNT; ++i) {
            const float left = bar_left + (marker_width + marker_gap) * (float)i;
            const GXColor marker = (i < g_lap_count) ? lap_done : empty;
            append_screen_quad(left, bar_bottom - 58.0f,
                               left + marker_width, bar_bottom - 50.0f,
                               0.3f, marker);
        }
    }

    /* Race, current-lap and best-lap clocks remain visible above the course. */
    {
        const float cx = w * 0.5f;
        append_screen_quad(cx - 100.0f, 10.0f, cx + 100.0f, 60.0f, 0.55f, dark);
        append_text("TIME", cx - 90.0f, 15.0f, 1.0f, white);
        append_text(time_text, cx - 55.0f, 15.0f, 1.0f, white);
        append_text(lap_text, cx - 90.0f, 28.0f, 1.0f, white);
        if (g_best_lap_seconds > 0.0f) {
            append_text("BEST", cx - 90.0f, 41.0f, 1.0f, heat_cool);
            append_text(best_text, cx - 55.0f, 41.0f, 1.0f, heat_cool);
        } else {
            append_text("BEST --:--.-", cx - 55.0f, 41.0f, 1.0f, heat_cool);
        }
    }

    /* Each completed overtake lights a compact marker in the upper-right. */
    {
        unsigned int i;
        const unsigned int visible_overtakes = (g_overtake_count > 8U) ? 8U : g_overtake_count;
        const float marker_width = 9.0f;
        const float marker_gap = 4.0f;
        const float right = w - 20.0f;
        for (i = 0; i < 8U; ++i) {
            const float left = right - (marker_width + marker_gap) * (float)(i + 1U);
            const GXColor marker = (i < visible_overtakes) ? rival_mark : empty;
            append_screen_quad(left, 22.0f, left + marker_width, 30.0f, 0.3f, marker);
        }
    }

    /* Symbolic finish banner: a checkered flag made from original GX quads. */
    if (g_race_finished) {
        const float cx = w * 0.5f;
        const float cy = h * 0.5f;
        const float tile = 14.0f;
        const float left = cx - 28.0f;
        const float top = cy - 21.0f;
        const GXColor finish_panel = { 8, 18, 30, 245 };
        const GXColor black = { 12, 18, 27, 255 };
        unsigned int row;
        unsigned int col;
        append_screen_quad(cx - 52.0f, cy - 34.0f, cx + 52.0f, cy + 34.0f,
                           0.6f, finish_panel);
        for (row = 0; row < 3U; ++row) {
            for (col = 0; col < 4U; ++col) {
                const GXColor square = (((row + col) & 1U) == 0U) ? white : black;
                append_screen_quad(left + (float)col * tile,
                                   top + (float)row * tile,
                                   left + (float)(col + 1U) * tile,
                                   top + (float)(row + 1U) * tile,
                                   0.2f, square);
            }
        }
    } else if (g_paused) {
        /* Pause icon: a framed pair of bars, with no font or external assets. */
        const float cx = w * 0.5f;
        const float cy = h * 0.5f;
        const GXColor pause_panel = { 8, 18, 30, 235 };
        append_screen_quad(cx - 32.0f, cy - 30.0f, cx + 32.0f, cy + 30.0f, 0.6f, pause_panel);
        append_screen_quad(cx - 13.0f, cy - 18.0f, cx - 4.0f, cy + 18.0f, 0.2f, white);
        append_screen_quad(cx + 4.0f, cy - 18.0f, cx + 13.0f, cy + 18.0f, 0.2f, white);
    }

    /* A centered steering tick gives immediate visual feedback without text. */
    {
        const float cx = w * 0.5f + g_player_lateral * 18.0f;
        append_screen_quad(cx - 2.0f, h - 46.0f, cx + 2.0f, h - 30.0f,
                           0.2f, white);
        append_screen_quad(w * 0.5f - 48.0f, h - 43.0f,
                           w * 0.5f + 48.0f, h - 40.0f,
                           0.25f, empty);
    }

    GX_SetZMode(GX_FALSE, GX_ALWAYS, GX_FALSE);
    draw_vertex_buffer();
}

static void initialise_video_and_gx(void)
{
    f32 yscale;
    u32 scaled_height;

    VIDEO_Init();
    PAD_Init();
    g_video_mode = VIDEO_GetPreferredMode(NULL);
    g_framebuffers[0] = MEM_K0_TO_K1(SYS_AllocateFramebuffer(g_video_mode));
    g_framebuffers[1] = MEM_K0_TO_K1(SYS_AllocateFramebuffer(g_video_mode));
    g_gx_fifo = memalign(32, GX_FIFO_SIZE);

    if (g_framebuffers[0] == NULL || g_framebuffers[1] == NULL || g_gx_fifo == NULL) {
        while (1) VIDEO_WaitVSync();
    }
    memset(g_gx_fifo, 0, GX_FIFO_SIZE);

    VIDEO_Configure(g_video_mode);
    VIDEO_SetNextFramebuffer(g_framebuffers[0]);
    VIDEO_SetBlack(FALSE);
    VIDEO_Flush();
    VIDEO_WaitVSync();
    if (g_video_mode->viTVMode & VI_NON_INTERLACE) VIDEO_WaitVSync();

    GX_Init(g_gx_fifo, GX_FIFO_SIZE);
    GX_SetCopyClear((GXColor){ 10, 21, 42, 255 }, 0x00FFFFFF);
    GX_SetViewport(0.0f, 0.0f, (f32)g_video_mode->fbWidth,
                   (f32)g_video_mode->efbHeight, 0.0f, 1.0f);
    GX_SetScissor(0, 0, g_video_mode->fbWidth, g_video_mode->efbHeight);

    yscale = GX_GetYScaleFactor(g_video_mode->efbHeight, g_video_mode->xfbHeight);
    scaled_height = GX_SetDispCopyYScale(yscale);
    GX_SetDispCopySrc(0, 0, g_video_mode->fbWidth, g_video_mode->efbHeight);
    GX_SetDispCopyDst(g_video_mode->fbWidth, scaled_height);
    GX_SetCopyFilter(g_video_mode->aa, g_video_mode->sample_pattern,
                     GX_TRUE, g_video_mode->vfilter);
    GX_SetFieldMode(g_video_mode->field_rendering,
        ((g_video_mode->viHeight == 2 * g_video_mode->xfbHeight) ?
         GX_ENABLE : GX_DISABLE));
    GX_SetPixelFmt(g_video_mode->aa ? GX_PF_RGB565_Z16 : GX_PF_RGB8_Z24,
                   GX_ZC_LINEAR);
    GX_SetCullMode(GX_CULL_NONE);
    GX_SetZMode(GX_TRUE, GX_LEQUAL, GX_TRUE);
    GX_SetColorUpdate(GX_TRUE);
    GX_SetAlphaUpdate(GX_TRUE);
    GX_SetBlendMode(GX_BM_NONE, GX_BL_ONE, GX_BL_ZERO, GX_LO_CLEAR);

    GX_SetNumChans(1);
    GX_SetChanCtrl(GX_COLOR0A0, GX_DISABLE, GX_SRC_REG, GX_SRC_VTX,
                   GX_LIGHTNULL, GX_DF_NONE, GX_AF_NONE);
    GX_SetNumTexGens(0);
    GX_SetNumTevStages(1);
    GX_SetTevOp(GX_TEVSTAGE0, GX_PASSCLR);
    GX_SetTevOrder(GX_TEVSTAGE0, GX_TEXCOORDNULL, GX_TEXMAP_NULL, GX_COLOR0A0);
    GX_ClearVtxDesc();
    GX_SetVtxDesc(GX_VA_POS, GX_DIRECT);
    GX_SetVtxDesc(GX_VA_CLR0, GX_DIRECT);
    GX_SetVtxAttrFmt(GX_VTXFMT0, GX_VA_POS, GX_POS_XYZ, GX_F32, 0);
    GX_SetVtxAttrFmt(GX_VTXFMT0, GX_VA_CLR0, GX_CLR_RGBA, GX_RGBA8, 0);
    GX_SetDispCopyGamma(GX_GM_1_0);
    GX_CopyDisp(g_framebuffers[0], GX_TRUE);
}

static void draw_frame(void)
{
    const float center_near = road_center_at(5.5f, g_distance);
    const float center_ahead = road_center_at(-14.0f, g_distance);
    guVector camera = { center_near, 1.65f, 7.0f };
    guVector up = { 0.0f, 1.0f, 0.0f };
    guVector target = { center_ahead, -0.85f, -15.0f };
    Mtx view;
    Mtx44 projection;

    g_vertex_count = 0;
    add_road();
    {
        unsigned int rival_index;
        for (rival_index = 0U; rival_index < BOONTA_RIVAL_COUNT; ++rival_index) {
            add_rival_pod(g_rival_z[rival_index], g_rival_lateral[rival_index], rival_index);
        }
    }
    add_player_pod();

    GX_SetCopyClear((GXColor){ 10, 21, 42, 255 }, 0x00FFFFFF);
    GX_SetZMode(GX_TRUE, GX_LEQUAL, GX_TRUE);
    guLookAt(view, &camera, &up, &target);
    guPerspective(projection, 55.0f,
                  (f32)g_video_mode->fbWidth / (f32)g_video_mode->efbHeight,
                  0.1f, 180.0f);
    GX_LoadProjectionMtx(projection, GX_PERSPECTIVE);
    GX_LoadPosMtxImm(view, GX_PNMTX0);
    GX_SetCurrentMtx(GX_PNMTX0);
    draw_vertex_buffer();
    draw_hud();

    GX_DrawDone();
    GX_CopyDisp(g_framebuffers[g_framebuffer_index], GX_TRUE);
    VIDEO_SetNextFramebuffer(g_framebuffers[g_framebuffer_index]);
    VIDEO_Flush();
    VIDEO_WaitVSync();
    g_framebuffer_index ^= 1U;
}

int main(int argc, char **argv)
{
    u64 previous_tick;
    unsigned int rival_index;
    (void)argc;
    (void)argv;
    initialise_video_and_gx();
    for (rival_index = 0U; rival_index < BOONTA_RIVAL_COUNT; ++rival_index) {
        g_rival_z[rival_index] = boonta_rival_initial_z(rival_index);
        g_rival_lateral[rival_index] = 0.0f;
    }
    previous_tick = gettime();

    for (;;) {
        u32 buttons_down;
        u32 buttons_held;
        s8 stick_x;
        float steering;
        u64 frame_tick;
        float frame_delta_seconds;
        float frame_scale;

        PAD_ScanPads();
        frame_tick = gettime();
        frame_delta_seconds = (float)diff_usec(previous_tick, frame_tick) * 0.000001f;
        frame_scale = boonta_frame_scale_from_delta(frame_delta_seconds);
        previous_tick = frame_tick;
        buttons_down = PAD_ButtonsDown(0);
        buttons_held = PAD_ButtonsHeld(0);
        stick_x = PAD_StickX(0);
        if (!g_race_finished && (buttons_down & PAD_BUTTON_START) != 0U) {
            g_paused = boonta_pause_state_next(g_paused, 1, 0);
        }
        if ((buttons_down & PAD_BUTTON_Y) != 0U) {
            g_distance = 0.0f;
            g_lap_count = 0U;
            g_race_seconds = 0.0f;
            g_lap_seconds = 0.0f;
            g_last_lap_seconds = 0.0f;
            g_best_lap_seconds = 0.0f;
            g_player_lateral = 0.0f;
            g_lateral_velocity = 0.0f;
            g_speed = 0.0f;
            g_boost = 1.0f;
            g_engine_heat = 0.0f;
            g_boost_overheated = 0;
            g_boost_active = 0;
            for (rival_index = 0U; rival_index < BOONTA_RIVAL_COUNT; ++rival_index) {
                g_rival_z[rival_index] = boonta_rival_initial_z(rival_index);
                g_rival_lateral[rival_index] = 0.0f;
            }
            g_overtake_count = 0U;
            g_race_finished = 0;
            g_paused = boonta_pause_state_next(g_paused, 0, 1);
        }

        if (g_paused || g_race_finished) {
            g_boost_active = 0;
            draw_frame();
            continue;
        }

        g_race_seconds = boonta_elapsed_after_frame(g_race_seconds, frame_delta_seconds, 1);
        g_lap_seconds = boonta_elapsed_after_frame(g_lap_seconds, frame_delta_seconds, 1);

        g_boost_active = boonta_boost_should_activate_with_heat(
            (buttons_held & PAD_BUTTON_X) != 0U,
            (buttons_held & PAD_BUTTON_A) != 0U,
            g_boost, g_engine_heat, g_boost_overheated);
        g_boost = boonta_boost_after_frame_scaled(g_boost, g_boost_active, frame_scale);
        g_engine_heat = boonta_engine_heat_after_frame_scaled(g_engine_heat, g_boost_active, frame_scale);
        g_boost_overheated = boonta_boost_overheated_after_frame(
            g_boost_overheated, g_engine_heat);

        steering = boonta_steering_input(
            (float)stick_x,
            (buttons_held & PAD_BUTTON_LEFT) != 0U,
            (buttons_held & PAD_BUTTON_RIGHT) != 0U);

        g_speed = boonta_speed_after_input_scaled(
            g_speed,
            (buttons_held & PAD_BUTTON_A) != 0U,
            (buttons_held & PAD_BUTTON_B) != 0U,
            frame_scale);

        /* Steering has inertia: quick direction changes need a moment to settle. */
        g_lateral_velocity = boonta_lateral_velocity_after_steering_scaled(
            g_lateral_velocity, steering, g_speed, frame_scale);
        g_player_lateral = boonta_lateral_position_after_frame(
            g_player_lateral, g_lateral_velocity, frame_scale);

        /* Leave the road and the craft loses speed; hitting the rail pushes it back. */
        g_speed = boonta_speed_after_offroad_scaled(g_speed, g_player_lateral, frame_scale);
        if (boonta_is_past_rail(g_player_lateral)) {
            g_player_lateral = boonta_lateral_after_rail_contact(g_player_lateral);
            g_lateral_velocity = boonta_lateral_velocity_after_rail_contact(g_lateral_velocity);
        }
        {
            const float previous_distance = g_distance;
            const unsigned int previous_laps = g_lap_count;
            g_distance = boonta_distance_after_frame_scaled(g_distance, g_speed, g_boost_active, frame_scale);
            g_lap_count = boonta_lap_count_after_frame(
                g_lap_count, previous_distance, g_distance, RACE_LAP_DISTANCE);
            if (g_lap_count > previous_laps) {
                g_last_lap_seconds = g_lap_seconds;
                g_best_lap_seconds = boonta_best_lap_after_finish(
                    g_best_lap_seconds, g_last_lap_seconds);
                g_lap_seconds = 0.0f;
            }
            if (boonta_race_is_finished(g_lap_count, RACE_LAP_LIMIT)) {
                g_race_finished = 1;
                g_speed = 0.0f;
                g_boost_active = 0;
                /* Keep the finished HUD on the completed final-lap time. */
                g_lap_seconds = g_last_lap_seconds;
            }
        }

        /* Staggered scripted opponents approach in camera space and change lanes. */
        if (!g_race_finished) {
            for (rival_index = 0U; rival_index < BOONTA_RIVAL_COUNT; ++rival_index) {
                int rival_event;
                g_rival_lateral[rival_index] = 1.10f * sinf(
                    g_distance * 0.022f + 1.2f + (float)rival_index * 1.55f);
                g_rival_z[rival_index] = boonta_rival_z_after_frame(
                    g_rival_z[rival_index], g_speed, frame_scale);
                rival_event = boonta_rival_event(
                    g_rival_z[rival_index], g_player_lateral,
                    g_rival_lateral[rival_index]);
                if (rival_event == BOONTA_RIVAL_EVENT_COLLISION) {
                    /* Any single contact costs speed and nudges the player from that rival. */
                    g_speed = boonta_speed_after_rival_contact(g_speed);
                    g_lateral_velocity = boonta_lateral_velocity_after_rival_contact(
                        g_lateral_velocity, g_player_lateral, g_rival_lateral[rival_index]);
                    g_rival_z[rival_index] = boonta_rival_respawn_z(rival_index, 1);
                } else if (rival_event == BOONTA_RIVAL_EVENT_OVERTAKE) {
                    ++g_overtake_count;
                    g_rival_z[rival_index] = boonta_rival_respawn_z(rival_index, 0);
                }
            }
        }

        draw_frame();
    }
    return 0;
}