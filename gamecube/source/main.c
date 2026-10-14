/*
 * Boonta Reborn 88 — clean-room GameCube driving prototype.
 *
 * Original procedural geometry only: no commercial game code or assets.
 * This early vertical slice demonstrates a controllable pod on a loop track.
 * It is not the full Step 102 racing prototype or a remaster.
 */
#include <gccore.h>
#include <ogc/pad.h>
#include <ogc/system.h>
#include <ogc/video.h>
#include <ogc/gu.h>
#include <ogc/gx.h>
#include <math.h>
#include <malloc.h>
#include <stdio.h>
#include "race_logic.h"
#include <string.h>

#define FIFO_SIZE (256 * 1024)
#define TRACK_SEGMENTS 96
#define TRACK_RADIUS 22.0f
#define TRACK_HALF_WIDTH 4.5f
#define MAX_SPEED 48.0f
#define RACE_LAPS 3
#define PI_F 3.14159265358979323846f
#define TWO_PI_F (2.0f * PI_F)

static void *framebuffer;
static GXRModeObj *video_mode;
static void *gx_fifo;
static RaceState race;

static const u8 font5x7[128][7] = {
    ['0'] = {14,17,19,21,25,17,14},
    ['1'] = {4,12,4,4,4,4,14},
    ['2'] = {14,17,1,2,4,8,31},
    ['3'] = {30,1,1,14,1,1,30},
    ['4'] = {2,6,10,18,31,2,2},
    ['5'] = {31,16,16,30,1,1,30},
    ['6'] = {14,16,16,30,17,17,14},
    ['7'] = {31,1,2,4,8,8,8},
    ['8'] = {14,17,17,14,17,17,14},
    ['9'] = {14,17,17,15,1,1,14},
    ['A'] = {14,17,17,31,17,17,17},
    ['B'] = {30,17,17,30,17,17,30},
    ['C'] = {14,17,16,16,16,17,14},
    ['D'] = {30,17,17,17,17,17,30},
    ['E'] = {31,16,16,30,16,16,31},
    ['F'] = {31,16,16,30,16,16,16},
    ['G'] = {14,17,16,23,17,17,15},
    ['H'] = {17,17,17,31,17,17,17},
    ['I'] = {14,4,4,4,4,4,14},
    ['J'] = {7,2,2,2,2,18,12},
    ['K'] = {17,18,20,24,20,18,17},
    ['L'] = {16,16,16,16,16,16,31},
    ['M'] = {17,27,21,21,17,17,17},
    ['N'] = {17,25,25,21,19,19,17},
    ['O'] = {14,17,17,17,17,17,14},
    ['P'] = {30,17,17,30,16,16,16},
    ['Q'] = {14,17,17,17,21,18,13},
    ['R'] = {30,17,17,30,20,18,17},
    ['S'] = {15,16,16,14,1,1,30},
    ['T'] = {31,4,4,4,4,4,4},
    ['U'] = {17,17,17,17,17,17,14},
    ['V'] = {17,17,17,17,17,10,4},
    ['W'] = {17,17,17,21,21,21,10},
    ['X'] = {17,17,10,4,10,17,17},
    ['Y'] = {17,17,10,4,4,4,4},
    ['Z'] = {31,1,2,4,8,16,31},
    ['/'] = {1,2,2,4,8,8,16},
    [':'] = {0,4,4,0,4,4,0},
    ['-'] = {0,0,0,31,0,0,0},
    [' '] = {0,0,0,0,0,0,0}
};

static void vertex3(float x, float y, float z, u8 r, u8 g, u8 b)
{
    GX_Position3f32(x, y, z);
    GX_Color4u8(r, g, b, 255);
}

static void vertex2(float x, float y, u8 r, u8 g, u8 b)
{
    GX_Position3f32(x, y, 0.0f);
    GX_Color4u8(r, g, b, 255);
}

static void draw_rect(float x1, float y1, float x2, float y2,
                      u8 r, u8 g, u8 b)
{
    GX_Begin(GX_QUADS, GX_VTXFMT0, 4);
    vertex2(x1, y1, r, g, b);
    vertex2(x2, y1, r, g, b);
    vertex2(x2, y2, r, g, b);
    vertex2(x1, y2, r, g, b);
    GX_End();
}

static void draw_text(const char *text, float x, float y, float scale,
                      u8 r, u8 g, u8 b)
{
    unsigned int pixels = 0;
    float start_x = x;

    for (const unsigned char *ch = (const unsigned char *)text; *ch; ++ch) {
        unsigned char c = *ch < 128 ? *ch : ' ';
        for (int row = 0; row < 7; ++row) {
            for (int col = 0; col < 5; ++col) {
                if (font5x7[c][row] & (1u << (4 - col))) {
                    ++pixels;
                }
            }
        }
    }

    if (pixels == 0) {
        return;
    }

    GX_Begin(GX_QUADS, GX_VTXFMT0, (u16)(pixels * 4));
    for (const unsigned char *ch = (const unsigned char *)text; *ch; ++ch) {
        unsigned char c = *ch < 128 ? *ch : ' ';
        for (int row = 0; row < 7; ++row) {
            for (int col = 0; col < 5; ++col) {
                if (font5x7[c][row] & (1u << (4 - col))) {
                    float px = x + col * scale;
                    float py = y + row * scale;
                    vertex2(px, py, r, g, b);
                    vertex2(px + scale, py, r, g, b);
                    vertex2(px + scale, py + scale, r, g, b);
                    vertex2(px, py + scale, r, g, b);
                }
            }
        }
        x += 6.0f * scale;
    }
    GX_End();
    (void)start_x;
}

static void draw_ground(void)
{
    GX_Begin(GX_QUADS, GX_VTXFMT0, 4);
    vertex3(-160.0f, -0.35f, -160.0f, 14, 25, 38);
    vertex3( 160.0f, -0.35f, -160.0f, 14, 25, 38);
    vertex3( 160.0f, -0.35f,  160.0f, 14, 25, 38);
    vertex3(-160.0f, -0.35f,  160.0f, 14, 25, 38);
    GX_End();
}

static void draw_ring(float inner_radius, float outer_radius, float y, int style)
{
    GX_Begin(GX_QUADS, GX_VTXFMT0, TRACK_SEGMENTS * 4);
    for (int i = 0; i < TRACK_SEGMENTS; ++i) {
        float a0 = TWO_PI_F * (float)i / (float)TRACK_SEGMENTS;
        float a1 = TWO_PI_F * (float)(i + 1) / (float)TRACK_SEGMENTS;
        float c0 = cosf(a0), s0 = sinf(a0);
        float c1 = cosf(a1), s1 = sinf(a1);
        u8 r, g, b;

        if (style == 0) {
            if ((i / 6) % 2 == 0) {
                r = 52; g = 65; b = 78;
            } else {
                r = 43; g = 55; b = 68;
            }
        } else if (style == 1) {
            if ((i / 4) % 2 == 0) {
                r = 238; g = 197; b = 75;
            } else {
                r = 216; g = 227; b = 235;
            }
        } else {
            if ((i / 4) % 2 == 0) {
                r = 48; g = 210; b = 255;
            } else {
                r = 28; g = 94; b = 133;
            }
        }

        vertex3(outer_radius * c0, y, outer_radius * s0, r, g, b);
        vertex3(outer_radius * c1, y, outer_radius * s1, r, g, b);
        vertex3(inner_radius * c1, y, inner_radius * s1, r, g, b);
        vertex3(inner_radius * c0, y, inner_radius * s0, r, g, b);
    }
    GX_End();
}

static void draw_center_dashes(void)
{
    const int dash_count = TRACK_SEGMENTS / 2;
    GX_Begin(GX_QUADS, GX_VTXFMT0, dash_count * 4);
    for (int i = 0; i < TRACK_SEGMENTS; i += 2) {
        float a0 = TWO_PI_F * (float)i / (float)TRACK_SEGMENTS;
        float a1 = TWO_PI_F * (float)(i + 1) / (float)TRACK_SEGMENTS;
        float ri = TRACK_RADIUS - 0.09f;
        float ro = TRACK_RADIUS + 0.09f;
        vertex3(ro * cosf(a0), 0.08f, ro * sinf(a0), 50, 221, 255);
        vertex3(ro * cosf(a1), 0.08f, ro * sinf(a1), 50, 221, 255);
        vertex3(ri * cosf(a1), 0.08f, ri * sinf(a1), 50, 221, 255);
        vertex3(ri * cosf(a0), 0.08f, ri * sinf(a0), 50, 221, 255);
    }
    GX_End();
}

static void draw_finish_line(void)
{
    const int tiles = 8;
    GX_Begin(GX_QUADS, GX_VTXFMT0, tiles * 4);
    for (int i = 0; i < tiles; ++i) {
        float x0 = TRACK_RADIUS - TRACK_HALF_WIDTH +
                   (2.0f * TRACK_HALF_WIDTH * (float)i / (float)tiles);
        float x1 = TRACK_RADIUS - TRACK_HALF_WIDTH +
                   (2.0f * TRACK_HALF_WIDTH * (float)(i + 1) / (float)tiles);
        u8 c = (i % 2 == 0) ? 235 : 18;
        vertex3(x0, 0.10f, -0.38f, c, c, c);
        vertex3(x1, 0.10f, -0.38f, c, c, c);
        vertex3(x1, 0.10f,  0.38f, c, c, c);
        vertex3(x0, 0.10f,  0.38f, c, c, c);
    }
    GX_End();
}

static void draw_pylons(void)
{
    const int count = 16;
    GX_Begin(GX_QUADS, GX_VTXFMT0, count * 4);
    for (int i = 0; i < count; ++i) {
        float a = TWO_PI_F * (float)i / (float)count;
        float cx = 28.0f * cosf(a);
        float cz = 28.0f * sinf(a);
        float tx = -sinf(a) * 0.42f;
        float tz =  cosf(a) * 0.42f;
        u8 r = (i % 2 == 0) ? 55 : 255;
        u8 g = (i % 2 == 0) ? 205 : 112;
        u8 b = (i % 2 == 0) ? 255 : 62;
        vertex3(cx - tx, 0.0f, cz - tz, r, g, b);
        vertex3(cx + tx, 0.0f, cz + tz, r, g, b);
        vertex3(cx + tx, 3.0f, cz + tz, r, g, b);
        vertex3(cx - tx, 3.0f, cz - tz, r, g, b);
    }
    GX_End();
}

static void draw_pod(float px, float pz, float tx, float tz, float rx, float rz,
                     int boost_active, u8 body_r, u8 body_g, u8 body_b)
{
    float nx = px + tx * 2.1f;
    float nz = pz + tz * 2.1f;
    float bx = px - tx * 1.25f;
    float bz = pz - tz * 1.25f;
    float lx = bx + rx * 0.95f;
    float lz = bz + rz * 0.95f;
    float rxp = bx - rx * 0.95f;
    float rzp = bz - rz * 0.95f;

    /* Main wedge-shaped pod body. */
    GX_Begin(GX_TRIANGLES, GX_VTXFMT0, 3);
    vertex3(nx, 1.0f, nz, body_r, body_g, body_b);
    vertex3(lx, 0.68f, lz,
            (u8)(body_r / 3), (u8)(body_g / 2), (u8)(body_b / 2));
    vertex3(rxp, 0.68f, rzp,
            (u8)(body_r / 3), (u8)(body_g / 2), (u8)(body_b / 2));
    GX_End();

    /* Two original engine nacelles. */
    GX_Begin(GX_TRIANGLES, GX_VTXFMT0, 6);
    vertex3(px + rx * 0.48f, 0.88f, pz + rz * 0.48f,
            body_r, body_g, body_b);
    vertex3(px + rx * 1.05f - tx * 0.55f, 0.64f,
            pz + rz * 1.05f - tz * 0.55f, 29, 143, 211);
    vertex3(px + rx * 0.2f - tx * 0.7f, 0.72f,
            pz + rz * 0.2f - tz * 0.7f, 29, 143, 211);
    vertex3(px - rx * 0.48f, 0.88f, pz - rz * 0.48f,
            body_r, body_g, body_b);
    vertex3(px - rx * 1.05f - tx * 0.55f, 0.64f,
            pz - rz * 1.05f - tz * 0.55f, 29, 143, 211);
    vertex3(px - rx * 0.2f - tx * 0.7f, 0.72f,
            pz - rz * 0.2f - tz * 0.7f, 29, 143, 211);
    GX_End();

    if (boost_active) {
        GX_Begin(GX_TRIANGLES, GX_VTXFMT0, 6);
        vertex3(bx, 0.72f, bz, 255, 216, 86);
        vertex3(bx - tx * 1.1f + rx * 0.24f, 0.55f,
                bz - tz * 1.1f + rz * 0.24f, 255, 92, 42);
        vertex3(bx - tx * 1.1f - rx * 0.24f, 0.55f,
                bz - tz * 1.1f - rz * 0.24f, 255, 92, 42);
        vertex3(bx, 0.72f, bz, 255, 216, 86);
        vertex3(bx - tx * 1.7f + rx * 0.18f, 0.48f,
                bz - tz * 1.7f + rz * 0.18f, 255, 143, 50);
        vertex3(bx - tx * 1.7f - rx * 0.18f, 0.48f,
                bz - tz * 1.7f - rz * 0.18f, 255, 143, 50);
        GX_End();
    }
}

static void draw_hud(void)
{
    Mtx identity;
    Mtx ortho;
    char number[8];
    float screen_w = (float)video_mode->fbWidth;
    float screen_h = (float)video_mode->efbHeight;
    float speed_fraction = race.speed / MAX_SPEED;

    guOrtho(ortho, 0.0f, screen_h, 0.0f, screen_w, 0.0f, 1.0f);
    GX_LoadProjectionMtx(ortho, GX_ORTHOGRAPHIC);
    guMtxIdentity(identity);
    GX_LoadPosMtxImm(identity, GX_PNMTX0);
    GX_SetCurrentMtx(GX_PNMTX0);
    GX_SetZMode(GX_FALSE, GX_ALWAYS, GX_FALSE);

    draw_rect(12.0f, 12.0f, 234.0f, 101.0f, 7, 17, 29);
    draw_text("SPEED", 22.0f, 22.0f, 1.5f, 196, 237, 255);
    snprintf(number, sizeof(number), "%02d", (int)(race.speed * 2.0f));
    draw_text(number, 105.0f, 20.0f, 2.0f, 255, 255, 255);
    draw_rect(22.0f, 42.0f, 220.0f, 50.0f, 27, 47, 61);
    draw_rect(22.0f, 42.0f, 22.0f + 198.0f * speed_fraction, 50.0f,
              46, 199, 255);

    draw_text("BOOST", 22.0f, 61.0f, 1.0f, 196, 237, 255);
    draw_rect(79.0f, 61.0f, 220.0f, 69.0f, 27, 47, 61);
    draw_rect(79.0f, 61.0f, 79.0f + 141.0f * race.boost_energy, 69.0f,
              race.engine_heat > 0.7f ? 255 : 68,
              race.engine_heat > 0.7f ? 90 : 211,
              race.engine_heat > 0.7f ? 45 : 255);

    draw_rect(screen_w - 112.0f, 12.0f, screen_w - 12.0f, 84.0f,
              7, 17, 29);
    if (race.finished) {
        draw_text("FINISH", screen_w - 100.0f, 28.0f, 1.5f,
                  255, 219, 110);
    } else {
        draw_text("LAP", screen_w - 101.0f, 21.0f, 1.5f,
                  196, 237, 255);
        snprintf(number, sizeof(number), "%d", race.completed_laps + 1);
        draw_text(number, screen_w - 57.0f, 20.0f, 2.0f,
                  255, 255, 255);
        draw_text("/3", screen_w - 43.0f, 30.0f, 1.0f,
                  196, 237, 255);
    }
    draw_text("POS", screen_w - 101.0f, 53.0f, 1.0f,
              196, 237, 255);
    snprintf(number, sizeof(number), "%d/4", race_position(&race));
    draw_text(number, screen_w - 64.0f, 52.0f, 1.0f,
              255, 255, 255);

    draw_rect(12.0f, screen_h - 25.0f, screen_w - 12.0f,
              screen_h - 8.0f, 7, 17, 29);
    draw_text("A ACCEL  B BRAKE  X BOOST  L/R LANE  Y RESET  START PAUSE",
              20.0f, screen_h - 20.0f, 1.0f, 196, 237, 255);

    if (race.paused && !race.finished) {
        draw_rect(screen_w * 0.5f - 65.0f, screen_h * 0.5f - 20.0f,
                  screen_w * 0.5f + 65.0f, screen_h * 0.5f + 20.0f,
                  7, 17, 29);
        draw_text("PAUSED", screen_w * 0.5f - 40.0f,
                  screen_h * 0.5f - 5.0f, 2.0f, 255, 255, 255);
    }
    if (race.finished) {
        draw_rect(screen_w * 0.5f - 88.0f, screen_h * 0.5f - 10.0f,
                  screen_w * 0.5f + 88.0f, screen_h * 0.5f + 13.0f,
                  7, 17, 29);
        draw_text("Y RESTART", screen_w * 0.5f - 58.0f,
                  screen_h * 0.5f - 1.0f, 2.0f, 255, 219, 110);
    }
    GX_SetZMode(GX_TRUE, GX_LEQUAL, GX_TRUE);
}

static void reset_race(void)
{
    race_reset(&race);
}

static void update_race(u32 held, u32 down)
{
    RaceInput input;
    input.accelerate = (held & PAD_BUTTON_A) != 0;
    input.brake = (held & PAD_BUTTON_B) != 0;
    input.boost = (held & PAD_BUTTON_X) != 0;
    input.left = (held & PAD_BUTTON_LEFT) != 0;
    input.right = (held & PAD_BUTTON_RIGHT) != 0;
    input.pause_pressed = (down & PAD_BUTTON_START) != 0;
    input.reset_pressed = (down & PAD_BUTTON_Y) != 0;
    race_update(&race, &input);
}

static void init_video_and_gx(void)
{
    GXColor clear_colour = {6, 10, 22, 255};
    u16 copy_height;

    VIDEO_Init();
    PAD_Init();
    video_mode = VIDEO_GetPreferredMode(NULL);
    framebuffer = MEM_K0_TO_K1(SYS_AllocateFramebuffer(video_mode));
    gx_fifo = memalign(32, FIFO_SIZE);
    if (framebuffer == NULL || gx_fifo == NULL) {
        SYS_ResetSystem(SYS_RETURNTOMENU, 0, 0);
    }
    memset(gx_fifo, 0, FIFO_SIZE);

    VIDEO_Configure(video_mode);
    VIDEO_SetNextFramebuffer(framebuffer);
    VIDEO_SetBlack(TRUE);
    VIDEO_Flush();
    VIDEO_WaitVSync();

    GX_Init(gx_fifo, FIFO_SIZE);
    GX_SetCopyClear(clear_colour, 0x00ffffff);
    GX_SetViewport(0.0f, 0.0f, (float)video_mode->fbWidth,
                   (float)video_mode->efbHeight, 0.0f, 1.0f);
    GX_SetScissor(0, 0, video_mode->fbWidth, video_mode->efbHeight);
    GX_SetDispCopySrc(0, 0, video_mode->fbWidth, video_mode->efbHeight);
    copy_height = GX_SetDispCopyYScale(
        GX_GetYScaleFactor(video_mode->efbHeight, video_mode->xfbHeight));
    GX_SetDispCopyDst(video_mode->fbWidth, copy_height);
    GX_SetCopyFilter(video_mode->aa, video_mode->sample_pattern,
                     GX_TRUE, video_mode->vfilter);
    GX_SetFieldMode(video_mode->field_rendering,
        ((video_mode->viHeight == 2 * video_mode->xfbHeight) ?
            GX_ENABLE : GX_DISABLE));
    if (video_mode->aa) {
        GX_SetPixelFmt(GX_PF_RGB565_Z16, GX_ZC_LINEAR);
    } else {
        GX_SetPixelFmt(GX_PF_RGB8_Z24, GX_ZC_LINEAR);
    }
    GX_SetCullMode(GX_CULL_NONE);
    GX_SetZMode(GX_TRUE, GX_LEQUAL, GX_TRUE);
    GX_SetColorUpdate(GX_TRUE);
    GX_SetAlphaUpdate(GX_TRUE);
    GX_SetNumChans(1);
    GX_SetNumTexGens(0);
    GX_SetNumTevStages(1);
    GX_SetTevOp(GX_TEVSTAGE0, GX_PASSCLR);
    GX_SetTevOrder(GX_TEVSTAGE0, GX_TEXCOORDNULL,
                   GX_TEXMAP_NULL, GX_COLOR0A0);
    GX_SetChanCtrl(GX_COLOR0A0, GX_DISABLE, GX_SRC_REG, GX_SRC_VTX,
                   GX_LIGHTNULL, GX_DF_NONE, GX_AF_NONE);
    GX_ClearVtxDesc();
    GX_SetVtxDesc(GX_VA_POS, GX_DIRECT);
    GX_SetVtxDesc(GX_VA_CLR0, GX_DIRECT);
    GX_SetVtxAttrFmt(GX_VTXFMT0, GX_VA_POS, GX_POS_XYZ, GX_F32, 0);
    GX_SetVtxAttrFmt(GX_VTXFMT0, GX_VA_CLR0, GX_CLR_RGBA, GX_RGBA8, 0);
    GX_SetDispCopyGamma(GX_GM_1_0);
    GX_InvVtxCache();
}

static void render_frame(void)
{
    Mtx view;
    Mtx projection;
    guVector camera;
    guVector up = {0.0f, 1.0f, 0.0f};
    guVector target;
    float radius = TRACK_RADIUS + race.lane_offset;
    float px = radius * cosf(race.angle);
    float pz = radius * sinf(race.angle);
    float tx = -sinf(race.angle);
    float tz =  cosf(race.angle);

    camera.x = px - tx * 8.0f;
    camera.y = 7.5f;
    camera.z = pz - tz * 8.0f;
    target.x = px + tx * 4.0f;
    target.y = 0.8f;
    target.z = pz + tz * 4.0f;

    guPerspective(projection, 52.0f,
        (float)video_mode->fbWidth / (float)video_mode->efbHeight,
        0.1f, 220.0f);
    guLookAt(view, &camera, &up, &target);
    GX_LoadProjectionMtx(projection, GX_PERSPECTIVE);
    GX_LoadPosMtxImm(view, GX_PNMTX0);
    GX_SetCurrentMtx(GX_PNMTX0);
    GX_SetZMode(GX_TRUE, GX_LEQUAL, GX_TRUE);

    draw_ground();
    draw_pylons();
    draw_ring(TRACK_RADIUS - TRACK_HALF_WIDTH,
              TRACK_RADIUS + TRACK_HALF_WIDTH, 0.0f, 0);
    draw_ring(TRACK_RADIUS + 3.85f, TRACK_RADIUS + 4.25f, 0.09f, 1);
    draw_ring(TRACK_RADIUS - 4.25f, TRACK_RADIUS - 3.85f, 0.09f, 1);
    draw_center_dashes();
    draw_finish_line();

    /* Original procedural rival pods; no commercial models or textures. */
    for (int i = 0; i < RACE_OPPONENT_COUNT; ++i) {
        float rival_angle = race.opponent_angles[i];
        float rival_radius = TRACK_RADIUS + race.opponent_lanes[i];
        float rival_x = rival_radius * cosf(rival_angle);
        float rival_z = rival_radius * sinf(rival_angle);
        u8 rival_r = 255, rival_g = 105, rival_b = 78;

        if (i == 1) {
            rival_r = 255; rival_g = 205; rival_b = 70;
        } else if (i == 2) {
            rival_r = 190; rival_g = 120; rival_b = 255;
        }

        draw_pod(rival_x, rival_z, -sinf(rival_angle), cosf(rival_angle),
                 cosf(rival_angle), sinf(rival_angle), 0,
                 rival_r, rival_g, rival_b);
    }
    draw_pod(px, pz, tx, tz, cosf(race.angle), sinf(race.angle),
             race.boost_active && race.speed > 2.0f, 58, 211, 255);
    draw_hud();

    GX_DrawDone();
    GX_CopyDisp(framebuffer, GX_TRUE);
    VIDEO_SetNextFramebuffer(framebuffer);
    VIDEO_Flush();
    VIDEO_WaitVSync();
    VIDEO_SetBlack(FALSE);
}

int main(int argc, char **argv)
{
    (void)argc;
    (void)argv;

    init_video_and_gx();
    reset_race();

    while (SYS_MainLoop()) {
        PAD_ScanPads();
        update_race(PAD_ButtonsHeld(0), PAD_ButtonsDown(0));
        render_frame();
    }

    return 0;
}
