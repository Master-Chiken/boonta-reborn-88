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
#include "generated_track.h"
#include "generated_mesh.h"
#include "generated_mesh_diamond.h"

#if !BOONTA_TRACK_CLOSED_LOOP
#error "The scrolling GameCube race runtime currently requires a closed-loop track."
#endif
#if BOONTA_TRACK_POINT_COUNT < 4U
#error "Closed-loop Catmull-Rom runtime tracks require at least four points."
#endif

#include <math.h>
#include <malloc.h>
#include <stdio.h>
#include <string.h>

#define GX_FIFO_SIZE       (256 * 1024)
/* HUD text plus layered finish-banner quads can exceed the old 4096-vertex cap.
 * Keep enough headroom so append operations don't silently drop the checkerboard. */
#define VERTEX_CAPACITY    8192U
#define ROAD_SEGMENTS      32U
#define ROAD_HALF_WIDTH    3.6f
#define RACE_LAP_DISTANCE   BOONTA_TRACK_LENGTH
#define RACE_LAP_LIMIT       3U
#define LAP_INDICATOR_COUNT  RACE_LAP_LIMIT
#define ROAD_Y             (-1.05f)
#define PI_F               3.14159265358979323846f

typedef struct {
    f32 x, y, z;
} Point3;

typedef struct {
    float x, y, z;
    float right_x, right_z;
    float half_width;
} TrackFrame;

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
static float g_vertex_y_offset;
/* 0 = ordinary world geometry, 1 = spline surface, 2 = rigid craft frame. */
static int g_track_world_transform_enabled;
static float g_vehicle_anchor_progress;
static float g_vehicle_anchor_local_z;
static float g_vehicle_anchor_center_x;
static BoontaRaceState g_race_state;

/* 8x8 RGB565 checkerboard stored in GX's 4x4 tiled texture layout. */
#define MESH_TEXTURE_SIZE 8U
static GXTexObj g_mesh_texture;
static u16 g_mesh_texture_pixels[MESH_TEXTURE_SIZE * MESH_TEXTURE_SIZE] ATTRIBUTE_ALIGN(32);

static u16 pack_rgb565(u8 r, u8 g, u8 b)
{
    return (u16)(((u16)(r >> 3) << 11) |
                 ((u16)(g >> 2) << 5) |
                 (u16)(b >> 3));
}

static void initialise_mesh_texture(void)
{
    u32 x;
    u32 y;

    for (y = 0U; y < MESH_TEXTURE_SIZE; ++y) {
        for (x = 0U; x < MESH_TEXTURE_SIZE; ++x) {
            const u32 tile = ((y / 4U) * (MESH_TEXTURE_SIZE / 4U) +
                              (x / 4U)) * 16U;
            const u32 within_tile = (y % 4U) * 4U + (x % 4U);
            const int alternate = (((x / 2U) + (y / 2U)) & 1U) != 0U;
            g_mesh_texture_pixels[tile + within_tile] = alternate
                ? pack_rgb565(35U, 210U, 240U)
                : pack_rgb565(255U, 105U, 45U);
        }
    }

    DCFlushRange(g_mesh_texture_pixels, sizeof(g_mesh_texture_pixels));
    GX_InitTexObj(&g_mesh_texture, g_mesh_texture_pixels,
                  MESH_TEXTURE_SIZE, MESH_TEXTURE_SIZE, GX_TF_RGB565,
                  GX_REPEAT, GX_REPEAT, GX_FALSE);
}

/*
 * Keep the established runtime expressions readable while placing all state
 * cleared by reset into one host-testable object.
 */
#define g_distance          (g_race_state.distance)
#define g_lap_count         (g_race_state.lap_count)
#define g_race_seconds      (g_race_state.race_seconds)
#define g_lap_seconds       (g_race_state.lap_seconds)
#define g_last_lap_seconds  (g_race_state.last_lap_seconds)
#define g_best_lap_seconds  (g_race_state.best_lap_seconds)
#define g_speed             (g_race_state.speed)
#define g_pitch_down        (g_race_state.pitch_down)
#define g_player_lateral    (g_race_state.player_lateral)
#define g_lateral_velocity  (g_race_state.lateral_velocity)
#define g_boost             (g_race_state.boost)
#define g_engine_heat       (g_race_state.engine_heat)
#define g_boost_overheated  (g_race_state.boost_overheated)
#define g_boost_active      (g_race_state.boost_active)
#define g_slide_active      (g_race_state.slide_active)
#define g_rival_z           (g_race_state.rival_z)
#define g_rival_lateral     (g_race_state.rival_lateral)
#define g_overtake_count    (g_race_state.overtake_count)
#define g_paused            (g_race_state.paused)
#define g_race_finished     (g_race_state.race_finished)

static const GXColor C_SKY = { 105, 170, 225, 255 };
static const GXColor C_GROUND = { 133, 98, 60, 255 };
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
static const GXColor C_EXHAUST_CORE = { 255, 244, 190, 255 };
static const GXColor C_TETHER = { 20, 43, 66, 255 };
static const GXColor C_TETHER_HIGHLIGHT = { 67, 205, 231, 255 };
static const GXColor C_CANYON_DARK = { 79, 48, 42, 255 };
static const GXColor C_CANYON_MID = { 130, 75, 48, 255 };
static const GXColor C_CANYON_LIGHT = { 170, 108, 62, 255 };

/* Compact original 5x7 glyphs for race-clock HUD text. */
static const u8 g_font5x7[128][7] = {
    ['0'] = {14,17,19,21,25,17,14}, ['1'] = {4,12,4,4,4,4,14},
    ['2'] = {14,17,1,2,4,8,31}, ['3'] = {30,1,1,14,1,1,30},
    ['4'] = {2,6,10,18,31,2,2}, ['5'] = {31,16,16,30,1,1,30},
    ['6'] = {14,16,16,30,17,17,14}, ['7'] = {31,1,2,4,8,8,8},
    ['8'] = {14,17,17,14,17,17,14}, ['9'] = {14,17,17,15,1,1,14},
    ['A'] = {14,17,17,31,17,17,17}, ['B'] = {30,17,17,30,17,17,30},
    ['C'] = {14,17,16,16,16,17,14}, ['D'] = {30,17,17,17,17,17,30},
    ['H'] = {17,17,17,31,17,17,17},
    ['E'] = {31,16,16,30,16,16,31}, ['F'] = {31,16,16,30,16,16,16},
    ['I'] = {14,4,4,4,4,4,14}, ['N'] = {17,25,21,19,17,17,17},
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

/*
 * Sample the authored closed-loop spline by travelled arc length. Runtime track
 * points remain in world coordinates; existing scene meshes are built in a local
 * forward plane and mapped into the actual course frame vertex by vertex.
 */
static float catmull_rom_component(float p0, float p1, float p2, float p3, float t)
{
    const float t2 = t * t;
    const float t3 = t2 * t;
    return 0.5f * (
        2.0f * p1 + (-p0 + p2) * t
        + (2.0f * p0 - 5.0f * p1 + 4.0f * p2 - p3) * t2
        + (-p0 + 3.0f * p1 - 3.0f * p2 + p3) * t3
    );
}

static void track_sample_at(float travelled, float *x_out, float *y_out,
                            float *z_out, float *width_out)
{
    /* Segment lengths are cached because many road vertices sample each frame. */
    static float segment_lengths[BOONTA_TRACK_POINT_COUNT];
    static float total_length;
    static int lengths_ready;
    unsigned int i;
    float target;

    if (x_out != NULL) *x_out = 0.0f;
    if (y_out != NULL) *y_out = 0.0f;
    if (z_out != NULL) *z_out = 0.0f;
    if (width_out != NULL) *width_out = ROAD_HALF_WIDTH;

    if (!lengths_ready) {
        for (i = 0U; i < BOONTA_TRACK_POINT_COUNT; ++i) {
            const unsigned int next = (i + 1U) % BOONTA_TRACK_POINT_COUNT;
            const float dx = boonta_track_points_original_test_oval[next].x -
                             boonta_track_points_original_test_oval[i].x;
            const float dy = boonta_track_points_original_test_oval[next].y -
                             boonta_track_points_original_test_oval[i].y;
            const float dz = boonta_track_points_original_test_oval[next].z -
                             boonta_track_points_original_test_oval[i].z;
            segment_lengths[i] = sqrtf(dx * dx + dy * dy + dz * dz);
            total_length += segment_lengths[i];
        }
        lengths_ready = 1;
    }

    if (!isfinite(travelled) || total_length <= 0.001f) return;
    target = fmodf(travelled, total_length);
    if (target < 0.0f) target += total_length;

    for (i = 0U; i < BOONTA_TRACK_POINT_COUNT; ++i) {
        const unsigned int next = (i + 1U) % BOONTA_TRACK_POINT_COUNT;
        const float length = segment_lengths[i];
        if (target <= length || i + 1U == BOONTA_TRACK_POINT_COUNT) {
            const unsigned int previous =
                (i + BOONTA_TRACK_POINT_COUNT - 1U) % BOONTA_TRACK_POINT_COUNT;
            const unsigned int following = (next + 1U) % BOONTA_TRACK_POINT_COUNT;
            const float t = length > 0.001f
                ? clampf_local(target / length, 0.0f, 1.0f) : 0.0f;
            const BoontaTrackPoint *p0 = &boonta_track_points_original_test_oval[previous];
            const BoontaTrackPoint *p1 = &boonta_track_points_original_test_oval[i];
            const BoontaTrackPoint *p2 = &boonta_track_points_original_test_oval[next];
            const BoontaTrackPoint *p3 = &boonta_track_points_original_test_oval[following];
            const float smooth_x = catmull_rom_component(p0->x, p1->x, p2->x, p3->x, t);
            const float smooth_y = catmull_rom_component(p0->y, p1->y, p2->y, p3->y, t);
            const float smooth_z = catmull_rom_component(p0->z, p1->z, p2->z, p3->z, t);
            const float smooth_width = catmull_rom_component(
                p0->half_width, p1->half_width, p2->half_width, p3->half_width, t);

            if (x_out != NULL) *x_out = smooth_x;
            if (y_out != NULL) *y_out = clampf_local(smooth_y, -3.0f, 3.0f);
            if (z_out != NULL) *z_out = smooth_z;
            if (width_out != NULL) *width_out = clampf_local(smooth_width, 2.2f, 4.8f);
            return;
        }
        target -= length;
    }
}

static float track_center_x_at(float travelled)
{
    float x = 0.0f;
    track_sample_at(travelled, &x, NULL, NULL, NULL);
    return x * (ROAD_HALF_WIDTH * 0.78f / 22.0f);
}

static float track_half_width_at(float travelled)
{
    float width = ROAD_HALF_WIDTH;
    track_sample_at(travelled, NULL, NULL, NULL, &width);
    return width;
}

static float track_elevation_at(float travelled)
{
    float elevation = 0.0f;
    track_sample_at(travelled, NULL, &elevation, NULL, NULL);
    return elevation;
}

static float road_center_at(float z, float distance)
{
    return track_center_x_at(distance + (4.0f - z));
}

static float road_half_width_at(float z, float distance)
{
    return track_half_width_at(distance + (4.0f - z));
}

static float road_height_at(float z, float distance)
{
    return ROAD_Y + track_elevation_at(distance + (4.0f - z)) * 0.45f;
}

/* Map a distance/lateral/elevation triple into the authored world-space track. */
static void track_world_point_at(float travelled, float lateral, float height,
                                 Point3 *out)
{
    float center_x = 0.0f, center_y = 0.0f, center_z = 0.0f;
    float before_x = 0.0f, before_y = 0.0f, before_z = 0.0f;
    float after_x = 0.0f, after_y = 0.0f, after_z = 0.0f;
    float tangent_x, tangent_z, tangent_length, right_x, right_z;

    track_sample_at(travelled, &center_x, &center_y, &center_z, NULL);
    track_sample_at(travelled - 0.25f, &before_x, &before_y, &before_z, NULL);
    track_sample_at(travelled + 0.25f, &after_x, &after_y, &after_z, NULL);
    tangent_x = after_x - before_x;
    tangent_z = after_z - before_z;
    tangent_length = sqrtf(tangent_x * tangent_x + tangent_z * tangent_z);
    if (tangent_length > 0.001f) {
        /* With travel along +Z, camera-right points toward -X. */
        right_x = -tangent_z / tangent_length;
        right_z = tangent_x / tangent_length;
    } else {
        right_x = -1.0f;
        right_z = 0.0f;
    }

    out->x = center_x + right_x * lateral;
    out->y = center_y + height;
    out->z = center_z + right_z * lateral;
}

/* A stable local frame for one authored point, reused for all road vertices in its row. */
static TrackFrame track_frame_at(float travelled)
{
    TrackFrame frame;
    float before_x = 0.0f, before_y = 0.0f, before_z = 0.0f;
    float after_x = 0.0f, after_y = 0.0f, after_z = 0.0f;
    float dx, dz, horizontal_length;

    track_sample_at(travelled, &frame.x, &frame.y, &frame.z, &frame.half_width);
    track_sample_at(travelled - 0.25f, &before_x, &before_y, &before_z, NULL);
    track_sample_at(travelled + 0.25f, &after_x, &after_y, &after_z, NULL);
    dx = after_x - before_x;
    dz = after_z - before_z;
    horizontal_length = sqrtf(dx * dx + dz * dz);
    if (horizontal_length > 0.001f) {
        /* Match the camera's right-handed basis along the authored course. */
        frame.right_x = -dz / horizontal_length;
        frame.right_z = dx / horizontal_length;
    } else {
        frame.right_x = -1.0f;
        frame.right_z = 0.0f;
    }
    return frame;
}

static Point3 track_frame_point(TrackFrame frame, float lateral, float height)
{
    Point3 point;
    point.x = frame.x + frame.right_x * lateral;
    point.y = frame.y + height;
    point.z = frame.z + frame.right_z * lateral;
    return point;
}

/* Road vertices follow the spline at each depth. */
static Point3 track_local_to_world(Point3 local_point)
{
    const float travelled = g_distance + (4.0f - local_point.z);
    float center_y = 0.0f;
    const float lateral = local_point.x - track_center_x_at(travelled);
    float height;
    Point3 world_point;

    track_sample_at(travelled, NULL, &center_y, NULL, NULL);
    height = local_point.y - (ROAD_Y + center_y * 0.45f);
    track_world_point_at(travelled, lateral, height, &world_point);
    return world_point;
}

/* A racer has one anchor and a fixed tangent: its mesh must not bend around corners. */
static Point3 track_vehicle_local_to_world(Point3 local_point)
{
    float center_x = 0.0f, center_y = 0.0f, center_z = 0.0f;
    float before_x = 0.0f, before_y = 0.0f, before_z = 0.0f;
    float after_x = 0.0f, after_y = 0.0f, after_z = 0.0f;
    float dx, dy, dz, tangent_length, horizontal_length;
    float forward, lateral, right_x, right_z, height;
    Point3 world_point;

    track_sample_at(g_vehicle_anchor_progress, &center_x, &center_y, &center_z, NULL);
    track_sample_at(g_vehicle_anchor_progress - 0.25f,
                    &before_x, &before_y, &before_z, NULL);
    track_sample_at(g_vehicle_anchor_progress + 0.25f,
                    &after_x, &after_y, &after_z, NULL);
    dx = after_x - before_x;
    dy = after_y - before_y;
    dz = after_z - before_z;
    tangent_length = sqrtf(dx * dx + dy * dy + dz * dz);
    horizontal_length = sqrtf(dx * dx + dz * dz);
    if (tangent_length > 0.001f) {
        forward = g_vehicle_anchor_local_z - local_point.z;
        world_point.x = center_x + (dx / tangent_length) * forward;
        world_point.y = center_y + (dy / tangent_length) * forward;
        world_point.z = center_z + (dz / tangent_length) * forward;
    } else {
        forward = 0.0f;
        world_point.x = center_x;
        world_point.y = center_y;
        world_point.z = center_z;
    }

    if (horizontal_length > 0.001f) {
        /* Keep craft lateral offsets consistent with road and camera frames. */
        right_x = -dz / horizontal_length;
        right_z = dx / horizontal_length;
    } else {
        right_x = -1.0f;
        right_z = 0.0f;
    }
    lateral = local_point.x - g_vehicle_anchor_center_x;
    height = local_point.y - (ROAD_Y + center_y * 0.45f);
    world_point.x += right_x * lateral;
    world_point.y += height;
    world_point.z += right_z * lateral;
    return world_point;
}

static void vertex_add(Point3 point, GXColor color)
{
    SceneVertex *v;
    if (g_vertex_count >= VERTEX_CAPACITY) return;
    point.y += g_vertex_y_offset;
    if (g_track_world_transform_enabled == 1) {
        point = track_local_to_world(point);
    } else if (g_track_world_transform_enabled == 2) {
        point = track_vehicle_local_to_world(point);
    }
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
    /* Reserve the entire quad before submitting either triangle. */
    if ((unsigned int)g_vertex_count + 6U > VERTEX_CAPACITY) return;
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
    const float segment_length = 2.8f;
    const unsigned int passed_sections = boonta_track_section_index(g_distance, segment_length);
    /* The floor follows the same spline as the road, with a short reach behind the
     * player and a little more reach than the visible canyon panels. This keeps the
     * cliff bases grounded on bends instead of leaving a giant flat plane under them. */
    const unsigned int ground_segments = ROAD_SEGMENTS + 12U;
    const float ground_start = -2.0f * segment_length;
    const float ground_margin = 4.2f;
    const float ground_drop = 0.24f;

    g_track_world_transform_enabled = 0;
    g_vertex_y_offset = 0.0f;
    for (i = 0U; i < ground_segments; ++i) {
        const float distance0 = g_distance + ground_start + (float)i * segment_length;
        const float distance1 = distance0 + segment_length;
        const TrackFrame f0 = track_frame_at(distance0);
        const TrackFrame f1 = track_frame_at(distance1);
        const float half0 = clampf_local(f0.half_width, 2.2f, 4.8f) + ground_margin;
        const float half1 = clampf_local(f1.half_width, 2.2f, 4.8f) + ground_margin;

        quad_add(track_frame_point(f0, -half0, -ground_drop),
                 track_frame_point(f0,  half0, -ground_drop),
                 track_frame_point(f1,  half1, -ground_drop),
                 track_frame_point(f1, -half1, -ground_drop), C_GROUND);
    }

    for (i = 0; i < ROAD_SEGMENTS; ++i) {
        const unsigned int section_phase = i + passed_sections;
        const float distance0 = g_distance + (float)i * segment_length;
        const float distance1 = distance0 + segment_length;
        const TrackFrame f0 = track_frame_at(distance0);
        const TrackFrame f1 = track_frame_at(distance1);
        const float w0 = clampf_local(f0.half_width, 2.2f, 4.8f);
        const float w1 = clampf_local(f1.half_width, 2.2f, 4.8f);
        const GXColor road = ((section_phase & 1U) == 0U) ? C_ROAD_A : C_ROAD_B;
        const GXColor rail = ((section_phase & 1U) == 0U) ? C_RAIL_A : C_RAIL_B;

        quad_add(track_frame_point(f0, -w0, 0.0f),
                 track_frame_point(f0,  w0, 0.0f),
                 track_frame_point(f1,  w1, 0.0f),
                 track_frame_point(f1, -w1, 0.0f), road);

        /* Edge paint, safety rails, and lane dashes use the same world-space frame. */
        quad_add(track_frame_point(f0, -w0, 0.018f),
                 track_frame_point(f0, -w0 + 0.12f, 0.018f),
                 track_frame_point(f1, -w1 + 0.12f, 0.018f),
                 track_frame_point(f1, -w1, 0.018f), C_EDGE_L);
        quad_add(track_frame_point(f0, w0 - 0.12f, 0.018f),
                 track_frame_point(f0, w0, 0.018f),
                 track_frame_point(f1, w1, 0.018f),
                 track_frame_point(f1, w1 - 0.12f, 0.018f), C_EDGE_R);

        quad_add(track_frame_point(f0, -w0 - 0.28f, 0.02f),
                 track_frame_point(f0, -w0 - 0.28f, 0.52f),
                 track_frame_point(f1, -w1 - 0.28f, 0.52f),
                 track_frame_point(f1, -w1 - 0.28f, 0.02f), rail);
        quad_add(track_frame_point(f0, w0 + 0.28f, 0.02f),
                 track_frame_point(f0, w0 + 0.28f, 0.52f),
                 track_frame_point(f1, w1 + 0.28f, 0.52f),
                 track_frame_point(f1, w1 + 0.28f, 0.02f), rail);

        if ((section_phase % 2U) == 0U) {
            const TrackFrame mark0 = track_frame_at(distance0 + 0.35f);
            const TrackFrame mark1 = track_frame_at(distance0 + 1.35f);
            quad_add(track_frame_point(mark0, -0.055f, 0.035f),
                     track_frame_point(mark0,  0.055f, 0.035f),
                     track_frame_point(mark1,  0.055f, 0.035f),
                     track_frame_point(mark1, -0.055f, 0.035f), C_MARKER);
        }
    }

    /* The finish stripe is placed at the next actual lap crossing along the spline. */
    {
        const float next_finish =
            (floorf(g_distance / RACE_LAP_DISTANCE) + 1.0f) * RACE_LAP_DISTANCE;
        const float remaining = next_finish - g_distance;
        if (remaining >= 0.0f && remaining < (float)ROAD_SEGMENTS * segment_length) {
            const TrackFrame finish0 = track_frame_at(next_finish);
            const TrackFrame finish1 = track_frame_at(next_finish + 0.55f);
            const float w0 = clampf_local(finish0.half_width, 2.2f, 4.8f);
            const float w1 = clampf_local(finish1.half_width, 2.2f, 4.8f);
            const GXColor stripe = { 240, 244, 250, 255 };
            quad_add(track_frame_point(finish0, -w0, 0.04f),
                     track_frame_point(finish0,  w0, 0.04f),
                     track_frame_point(finish1,  w1, 0.04f),
                     track_frame_point(finish1, -w1, 0.04f), stripe);
        }
    }
}

/*
 * Original low-poly canyon walls give the test road a readable world silhouette.
 * The panels are deliberately simple, stable geometry rather than extracted game art.
 * Their bases sit just above the desert floor and remain outside the track rails.
 */
static void add_canyon_scenery(void)
{
    const float wall_margin = 4.2f;
    g_track_world_transform_enabled = 1;
    const float wall_length = 6.0f;
    const unsigned int passed_wall_sections = boonta_track_section_index(g_distance, wall_length);
    unsigned int i;

    for (i = 0U; i < 18U; ++i) {
        const unsigned int wall_phase = i + passed_wall_sections;
        /* More, shorter panels keep the canyon continuous around tight spline bends. */
        const float z_near = -2.0f - (float)i * wall_length;
        const float z_far = z_near - wall_length;
        const float center_near = road_center_at(z_near, g_distance);
        const float center_far = road_center_at(z_far, g_distance);
        const float base_offset_near = road_half_width_at(z_near, g_distance) + wall_margin;
        const float base_offset_far = road_half_width_at(z_far, g_distance) + wall_margin;
        /* Keep wall footings aligned with the matching spline-following floor ribbon. */
        const float base_y_near = road_height_at(z_near, g_distance) - 0.24f;
        const float base_y_far = road_height_at(z_far, g_distance) - 0.24f;
        const float near_height = 3.8f + (float)(wall_phase % 4U) * 0.15f;
        const float far_height = 3.8f + (float)((wall_phase + 1U) % 4U) * 0.15f;
        const float near_top_offset = base_offset_near + 0.15f + (float)(wall_phase % 2U) * 0.08f;
        const float far_top_offset = base_offset_far + 0.15f + (float)((wall_phase + 1U) % 2U) * 0.08f;
        unsigned int side_index;

        for (side_index = 0U; side_index < 2U; ++side_index) {
            const float side = side_index == 0U ? -1.0f : 1.0f;
            const Point3 base_near = {
                center_near + side * base_offset_near, base_y_near, z_near
            };
            const Point3 top_near = {
                center_near + side * near_top_offset, base_y_near + near_height, z_near
            };
            const Point3 base_far = {
                center_far + side * base_offset_far, base_y_far, z_far
            };
            const Point3 top_far = {
                center_far + side * far_top_offset, base_y_far + far_height, z_far
            };
            GXColor face;
            const unsigned int tone_phase = wall_phase + side_index;

            if ((tone_phase % 4U) == 0U) {
                face = C_CANYON_LIGHT;
            } else if ((tone_phase & 1U) == 0U) {
                face = C_CANYON_MID;
            } else {
                face = C_CANYON_DARK;
            }

            /* Same tone on both triangles avoids an oversized diagonal facet. */
            triangle_add(base_near, top_near, top_far, face);
            triangle_add(base_near, top_far, base_far, face);
        }
    }
    g_track_world_transform_enabled = 0;
}
static void add_player_pod(void)
{
    const float center = road_center_at(1.0f, g_distance) + g_player_lateral;
    const float engine_offset = 0.82f;
    const float flame_length = 0.22f + 0.55f * g_speed + (g_boost_active ? 0.55f : 0.0f);

    /*
     * Twin engines need to read as two separate masses connected to a cockpit,
     * rather than one blue block. Draw the narrow clean-room tether strips first
     * so their anchors disappear naturally beneath the engine nacelles.
     */
    quad_add((Point3){ center - 0.51f, -0.41f, 0.25f },
             (Point3){ center - 0.48f, -0.61f, 0.25f },
             (Point3){ center - 0.16f, -0.51f, -0.38f },
             (Point3){ center - 0.21f, -0.40f, -0.38f }, C_TETHER);
    quad_add((Point3){ center + 0.48f, -0.61f, 0.25f },
             (Point3){ center + 0.51f, -0.41f, 0.25f },
             (Point3){ center + 0.21f, -0.40f, -0.38f },
             (Point3){ center + 0.16f, -0.51f, -0.38f }, C_TETHER);
    quad_add((Point3){ center - 0.49f, -0.43f, 0.23f },
             (Point3){ center - 0.48f, -0.48f, 0.23f },
             (Point3){ center - 0.20f, -0.43f, -0.36f },
             (Point3){ center - 0.21f, -0.40f, -0.36f }, C_TETHER_HIGHLIGHT);
    quad_add((Point3){ center + 0.48f, -0.48f, 0.23f },
             (Point3){ center + 0.49f, -0.43f, 0.23f },
             (Point3){ center + 0.21f, -0.40f, -0.36f },
             (Point3){ center + 0.20f, -0.43f, -0.36f }, C_TETHER_HIGHLIGHT);

    /* Longer, wider-spaced nacelles give the racer a stronger twin-engine silhouette. */
    box_add(center - engine_offset, -0.62f, 1.08f,
            0.31f, 0.25f, 0.85f, C_POD_TOP, C_POD_SIDE, C_THRUST);
    box_add(center + engine_offset, -0.62f, 1.08f,
            0.31f, 0.25f, 0.85f, C_POD_TOP, C_POD_SIDE, C_THRUST);

    /* Central body and raised canopy keep the cockpit visually separate from the engines. */
    box_add(center, -0.49f, 0.23f, 0.35f, 0.09f, 0.20f,
            C_POD_ACCENT, C_POD_SIDE, C_POD_SIDE);
    box_add(center, -0.34f, -0.12f, 0.22f, 0.11f, 0.24f,
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

    /*
     * Exhaust length follows speed, with an additional boost plume. This is
     * intentionally simple original geometry, but its state is now readable
     * in the scene instead of only in the HUD meters.
     */
    if (g_speed > 0.12f) {
        const GXColor thrust = (g_boost_active || g_speed > 0.70f)
            ? C_THRUST_HOT : C_THRUST;
        const float exhaust_end = 1.93f + flame_length;
        box_add(center - engine_offset, -0.62f, 1.93f + flame_length * 0.5f,
                0.15f, 0.14f, flame_length * 0.5f,
                thrust, C_THRUST, C_THRUST);
        box_add(center + engine_offset, -0.62f, 1.93f + flame_length * 0.5f,
                0.15f, 0.14f, flame_length * 0.5f,
                thrust, C_THRUST, C_THRUST);

        /* Small hot cores sit just behind the plume so boost has a brighter tip. */
        quad_add((Point3){ center - engine_offset - 0.065f, -0.68f, exhaust_end + 0.02f },
                 (Point3){ center - engine_offset + 0.065f, -0.68f, exhaust_end + 0.02f },
                 (Point3){ center - engine_offset + 0.065f, -0.56f, exhaust_end + 0.02f },
                 (Point3){ center - engine_offset - 0.065f, -0.56f, exhaust_end + 0.02f },
                 g_boost_active ? C_EXHAUST_CORE : C_THRUST_HOT);
        quad_add((Point3){ center + engine_offset - 0.065f, -0.68f, exhaust_end + 0.02f },
                 (Point3){ center + engine_offset + 0.065f, -0.68f, exhaust_end + 0.02f },
                 (Point3){ center + engine_offset + 0.065f, -0.56f, exhaust_end + 0.02f },
                 (Point3){ center + engine_offset - 0.065f, -0.56f, exhaust_end + 0.02f },
                 g_boost_active ? C_EXHAUST_CORE : C_THRUST_HOT);
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

/*
 * Submit one original indexed mesh through the validated GX path. Each mesh is
 * drawn separately so the existing procedural scene keeps its vertex budget;
 * local offsets make the test fixtures distinguishable in the same camera view.
 */
static int draw_synthetic_mesh(const BoontaMeshView *mesh,
                               float local_offset_x, float local_offset_y)
{
    size_t i;

    if (mesh == NULL || boonta_mesh_validate(mesh) != BOONTA_MESH_VALID) {
        return 0;
    }

    /* Enable a real GX texture stage only for this source-driven mesh. */
    GX_LoadTexObj(&g_mesh_texture, GX_TEXMAP0);
    GX_SetNumTexGens(1);
    GX_SetNumTevStages(1);
    GX_SetTevOrder(GX_TEVSTAGE0, GX_TEXCOORD0, GX_TEXMAP0, GX_COLOR0A0);
    GX_SetTevOp(GX_TEVSTAGE0, GX_MODULATE);
    GX_SetTexCoordGen(GX_TEXCOORD0, GX_TG_MTX2x4, GX_TG_TEX0, GX_IDENTITY);
    GX_SetVtxDesc(GX_VA_TEX0, GX_DIRECT);
    GX_SetVtxAttrFmt(GX_VTXFMT0, GX_VA_TEX0, GX_TEX_ST, GX_F32, 0);

    GX_Begin(GX_TRIANGLES, GX_VTXFMT0, (u16)mesh->index_count);
    for (i = 0U; i < mesh->index_count; ++i) {
        const BoontaMeshVertex *v = &mesh->vertices[mesh->indices[i]];
        const Point3 local = {
            v->x + local_offset_x, v->y + local_offset_y, v->z
        };
        const Point3 world = track_local_to_world(local);
        GX_Position3f32(world.x, world.y, world.z);
        GX_Color4u8(v->r, v->g, v->b, v->a);
        GX_TexCoord2f32(v->u, v->v);
    }
    GX_End();

    /* Return to the vertex-colour-only state used by the procedural scene/HUD. */
    GX_SetVtxDesc(GX_VA_TEX0, GX_NONE);
    GX_SetNumTexGens(0);
    GX_SetTevOp(GX_TEVSTAGE0, GX_PASSCLR);
    GX_SetTevOrder(GX_TEVSTAGE0, GX_TEXCOORDNULL, GX_TEXMAP_NULL, GX_COLOR0A0);
    return 1;
}

static void append_screen_quad(float x0, float y0, float x1, float y1,
                               float z, GXColor color)
{
    /* guOrtho looks down -Z: positive screen-space depths are outside its clip volume. */
    const float clip_z = -z;
    quad_add((Point3){ x0, y0, clip_z }, (Point3){ x1, y0, clip_z },
             (Point3){ x1, y1, clip_z }, (Point3){ x0, y1, clip_z }, color);
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
    GX_SetCurrentMtx(GX_PNMTX0);
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

    /* Small pitch gauge: nose-down is right, nose-up is left, neutral is centered. */
    {
        const float pitch_center = w - 78.0f;
        const float pitch_left = pitch_center - 42.0f;
        const float pitch_right = pitch_center + 42.0f;
        const float pitch_marker = pitch_center + 35.0f * g_pitch_down;
        append_screen_quad(pitch_left, 37.0f, pitch_right, 43.0f, 0.5f, dark);
        append_screen_quad(pitch_center - 1.0f, 36.0f, pitch_center + 1.0f, 44.0f, 0.4f, white);
        append_screen_quad(pitch_marker - 2.0f, 35.0f, pitch_marker + 2.0f, 45.0f,
                           0.3f, g_pitch_down > 0.65f ? boost_fill : fill);
        append_text("PITCH", pitch_left, 46.0f, 1.0f, white);
        append_text("SLIDE", pitch_left, 56.0f, 1.0f,
                    g_slide_active ? boost_fill : empty);
    }

    /* Finish banner: a readable FINISH label and checkered flag made from original GX quads. */
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
        append_text("FINISH", cx - 18.0f, cy - 30.0f, 1.0f, boost_fill);
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
    initialise_mesh_texture();
    GX_SetCopyClear(C_SKY, 0x00FFFFFF);
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
    Point3 camera_point;
    Point3 target_point;
    /* Position and aim are sampled from the same world-space spline as the mesh. */
    /* Follow the local course tangent with enough downward pitch to keep the
     * near road and the player's pod in frame, including the first start-line view. */
    track_world_point_at(g_distance - 2.5f, g_player_lateral,
                         3.20f - 0.20f * g_pitch_down, &camera_point);
    track_world_point_at(g_distance + 8.0f, g_player_lateral,
                         -0.05f - 0.45f * g_pitch_down, &target_point);
    guVector camera = { camera_point.x, camera_point.y, camera_point.z };
    guVector up = { 0.0f, 1.0f, 0.0f };
    guVector target = { target_point.x, target_point.y, target_point.z };
    Mtx view;
    Mtx44 projection;

    GX_SetCopyClear(C_SKY, 0x00FFFFFF);
    /* Render straight into the cleared EFB; a 2D backdrop previously left
     * orthographic state immediately before the depth-tested world pass. */
    g_vertex_count = 0;
    g_vertex_y_offset = 0.0f;
    g_track_world_transform_enabled = 0;
    add_road();
    add_canyon_scenery();
    {
        unsigned int rival_index;
        for (rival_index = 0U; rival_index < BOONTA_RIVAL_COUNT; ++rival_index) {
            g_track_world_transform_enabled = 2;
            g_vehicle_anchor_local_z = g_rival_z[rival_index];
            g_vehicle_anchor_progress = g_distance + (4.0f - g_vehicle_anchor_local_z);
            g_vehicle_anchor_center_x = road_center_at(g_vehicle_anchor_local_z, g_distance);
            g_vertex_y_offset = road_height_at(g_vehicle_anchor_local_z, g_distance) - ROAD_Y;
            add_rival_pod(g_rival_z[rival_index], g_rival_lateral[rival_index], rival_index);
        }
        g_track_world_transform_enabled = 0;
        g_vertex_y_offset = 0.0f;
    }
    g_track_world_transform_enabled = 2;
    g_vehicle_anchor_local_z = 1.0f;
    g_vehicle_anchor_progress = g_distance + (4.0f - g_vehicle_anchor_local_z);
    g_vehicle_anchor_center_x = road_center_at(g_vehicle_anchor_local_z, g_distance);
    g_vertex_y_offset = road_height_at(g_vehicle_anchor_local_z, g_distance) - ROAD_Y;
    add_player_pod();
    g_track_world_transform_enabled = 0;
    g_vertex_y_offset = 0.0f;

    GX_SetCopyClear(C_SKY, 0x00FFFFFF);
    /* Keep real depth testing for the ground, spline road, canyon panels and pods. */
    GX_SetZMode(GX_TRUE, GX_LEQUAL, GX_TRUE);
    guLookAt(view, &camera, &up, &target);
    guPerspective(projection, 55.0f,
                  (f32)g_video_mode->fbWidth / (f32)g_video_mode->efbHeight,
                  0.1f, 180.0f);
    GX_LoadProjectionMtx(projection, GX_PERSPECTIVE);
    GX_LoadPosMtxImm(view, GX_PNMTX0);
    GX_SetCurrentMtx(GX_PNMTX0);
    draw_vertex_buffer();
    (void)draw_synthetic_mesh(
        &boonta_generated_mesh_original_synthetic_triangle_view, 2.05f, -0.45f);
    (void)draw_synthetic_mesh(
        &boonta_generated_mesh_original_synthetic_diamond_view, -2.05f, -0.45f);
    draw_hud();

    /*
     * draw_hud disables Z updates for overlay quads. Restore them before the
     * copy: GX_CopyDisp(..., GX_TRUE) clears EFB depth only while Z updates
     * are enabled. Without this, stale depth from the previous frame hides
     * the moving world-space track as the camera follows a closed loop.
     */
    GX_SetZMode(GX_TRUE, GX_LEQUAL, GX_TRUE);
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
    boonta_race_state_reset(&g_race_state);
    previous_tick = gettime();

    for (;;) {
        u32 buttons_down;
        u32 buttons_held;
        s8 stick_x;
        s8 stick_y;
        float pitch_down;
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
        stick_y = PAD_StickY(0);
        if (!g_race_finished && (buttons_down & PAD_BUTTON_START) != 0U) {
            g_paused = boonta_pause_state_next(g_paused, 1, 0);
        }
        if ((buttons_down & PAD_BUTTON_Y) != 0U) {
            boonta_race_state_reset(&g_race_state);
            /* Render the clean start state before any input advances the race. */
            draw_frame();
            continue;
        }

        if (g_paused || g_race_finished) {
            g_boost_active = 0;
            g_slide_active = 0;
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

        /* Up/forward on the analog stick pitches down; down pitches up. */
        pitch_down = boonta_pitch_input((float)stick_y);
        g_pitch_down = pitch_down;
        g_slide_active = (buttons_held & PAD_TRIGGER_L) != 0U;
        steering = boonta_steering_after_pitch(
            boonta_steering_input(
                (float)stick_x,
                (buttons_held & PAD_BUTTON_LEFT) != 0U,
                (buttons_held & PAD_BUTTON_RIGHT) != 0U),
            pitch_down);

        g_speed = boonta_speed_after_input_scaled(
            g_speed,
            (buttons_held & PAD_BUTTON_A) != 0U,
            (buttons_held & PAD_BUTTON_B) != 0U,
            frame_scale);

        /* Steering has inertia: quick direction changes need a moment to settle. */
        g_lateral_velocity = boonta_lateral_velocity_after_steering_slide_scaled(
            g_lateral_velocity, steering, g_speed, g_slide_active, frame_scale);
        g_player_lateral = clampf_local(
            boonta_lateral_position_after_frame(
                g_player_lateral, g_lateral_velocity, frame_scale),
            -4.0f, 4.0f);

        /*
         * Off-road and rail limits are expressed relative to the local authored
         * half-width, so narrow sections are not secretly as wide as broad ones.
         */
        {
            const float local_half_width = track_half_width_at(g_distance);
            const float lateral_scale = ROAD_HALF_WIDTH /
                (local_half_width > 0.1f ? local_half_width : ROAD_HALF_WIDTH);
            const float normalized_lateral = g_player_lateral * lateral_scale;
            g_speed = boonta_speed_after_offroad_scaled(
                g_speed, normalized_lateral, frame_scale);
            if (boonta_is_past_rail(normalized_lateral)) {
                const float resolved_lateral =
                    boonta_lateral_after_rail_contact(normalized_lateral);
                g_player_lateral = resolved_lateral / lateral_scale;
                g_lateral_velocity = boonta_lateral_velocity_after_rail_contact(
                    g_lateral_velocity);
            }
        }
        {
            const float previous_distance = g_distance;
            const unsigned int previous_laps = g_lap_count;
            g_distance = boonta_distance_after_pitch_scaled(g_distance, g_speed, g_boost_active, pitch_down, frame_scale);
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