/*
 * Star Wars Racer — native GameCube/Wii gameplay prototype.
 * Focus: vehicle handling, selectable circuits, race items and opponent behaviour.
 * This is still an original prototype, not a complete port of the commercial game.
 */
#include <gccore.h>
#include <ogc/pad.h>
#include <ogc/gu.h>
#include <ogc/gx.h>
#include <ogc/system.h>
#include <math.h>
#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "racer_physics.h"
#include "race_flow.h"
#include "race_gate_geometry.h"
#include "race_standings.h"
#include "rival_ai.h"
#include "draft_assist.h"
#include "race_feedback.h"
#include "pod_model.h"
#include "track_catalog.h"
#include "track_direction.h"
#include "vehicle_catalog.h"
#include "race_items.h"
#include "championship.h"
#include "career_save.h"
#include "pause_state.h"
#include "game_text.h"
#include "race_mode_select.h"
#include "garage_progression.h"
#include "voice_over_runtime.h"

#define GX_FIFO_SIZE (256 * 1024)
#define HUD_VERTEX_CAPACITY 8192U
#define SCENE_VERTEX_CAPACITY 8192U
#define OPPONENT_COUNT 7U
#define PI_F 3.14159265358979323846f

typedef RivalAIState Rival;

typedef struct {
    f32 x, y, z;
    u8 r, g, b, a;
} HudVertex;

typedef struct {
    f32 x, y, z;
    u8 r, g, b, a;
} SceneVertex;

static void *g_framebuffers[2] = { NULL, NULL };
static void *g_gx_fifo = NULL;
static u32 g_framebuffer_index = 0;
static GXRModeObj *g_video_mode = NULL;
static RacerState g_player;
static PodMesh g_pod_mesh[OPPONENT_COUNT + 1U];
static RacerTrackPoint g_active_track[TRACK_POINT_CAPACITY];
static unsigned int g_active_track_count = 0U;
static TrackVertex g_active_track_vertices[TRACK_VERTEX_CAPACITY];
static unsigned int g_active_track_vertex_count = 0U;
static unsigned int g_selected_track = 0U;
static int g_reverse_track = 0; /* Inspired by SWE1R-Mods reverse-track variants. */
static unsigned int g_selected_vehicle = 0U;
static RaceItem g_race_items[RACE_ITEM_COUNT];
static RaceItemType g_last_item = RACE_ITEM_NONE;
static float g_item_flash_timer = 0.0f;
typedef enum { GAME_MODE_SELECT = 0, GAME_MODE_RACE = 1 } GameMode;
static GameMode g_game_mode = GAME_MODE_SELECT;
static SceneVertex g_scene_vertices[SCENE_VERTEX_CAPACITY];
static u16 g_scene_vertex_count = 0;
static RaceFlow g_race_flow;
static Championship g_championship;
static CareerProfile g_career_profile;
static int g_card_save_available = 0;
static int g_championship_enabled = 0;
static int g_time_trial_enabled = 0;
static RaceSelectMode g_selected_race_mode = RACE_SELECT_SINGLE;
static int g_bonus_settings_saved = 0;
static int g_pre_bonus_reverse_track = 0;
static unsigned int g_pre_bonus_ai_difficulty = 1U;
static int g_finish_recorded = 0;
static int g_paused = 0;
static unsigned int g_championship_start_track = 0U;
static GaragePart g_garage_part = GARAGE_SPEED;
static unsigned int g_ai_difficulty = 1U; /* 0 easy, 1 normal, 2 hard */
static float g_garage_notice_timer = 0.0f;
static char g_garage_notice[48] = "WIN RACES TO BUY PARTS";
static RacerVehicleSpec g_effective_player_vehicle;
static RaceFeedback g_race_feedback;
static VoiceOverRuntime g_voice_over_runtime;
static Rival g_rivals[OPPONENT_COUNT];
static float g_track_length = 1.0f;
static float g_collision_flash_timer = 0.0f;
static int g_drafting_active = 0;
static float g_camera_x = 0.0f, g_camera_y = 0.0f, g_camera_z = 0.0f;
static int g_camera_ready = 0;
static HudVertex g_hud_vertices[HUD_VERTEX_CAPACITY];
static u32 g_hud_count = 0;

static const RacerVehicleSpec *selected_player_vehicle_spec(void)
{
    garage_apply_upgrades(&g_career_profile, vehicle_catalog_get(g_selected_vehicle),
                          &g_effective_player_vehicle);
    return &g_effective_player_vehicle;
}

/* Stable labels for every member of the eight-pod field. */
static const char *race_racer_label(unsigned int racer)
{
    static const char *labels[CHAMPIONSHIP_MAX_RACERS] = {
        "YOU", "RIVAL 1", "RIVAL 2", "RIVAL 3",
        "RIVAL 4", "RIVAL 5", "RIVAL 6", "RIVAL 7"
    };
    return racer < CHAMPIONSHIP_MAX_RACERS ? labels[racer] : "UNKNOWN";
}

/* 5x7 pixel font. Unlisted characters are intentionally blank. */
static const char g_font[128][7][6] = {
    ['0'] = {"01110","10001","10011","10101","11001","10001","01110"},
    ['1'] = {"00100","01100","00100","00100","00100","00100","01110"},
    ['2'] = {"01110","10001","00001","00010","00100","01000","11111"},
    ['3'] = {"11110","00001","00001","01110","00001","00001","11110"},
    ['4'] = {"00010","00110","01010","10010","11111","00010","00010"},
    ['5'] = {"11111","10000","10000","11110","00001","00001","11110"},
    ['6'] = {"01110","10000","10000","11110","10001","10001","01110"},
    ['7'] = {"11111","00001","00010","00100","01000","01000","01000"},
    ['8'] = {"01110","10001","10001","01110","10001","10001","01110"},
    ['9'] = {"01110","10001","10001","01111","00001","00001","01110"},
    ['A'] = {"01110","10001","10001","11111","10001","10001","10001"},
    ['B'] = {"11110","10001","10001","11110","10001","10001","11110"},
    ['C'] = {"01111","10000","10000","10000","10000","10000","01111"},
    ['D'] = {"11110","10001","10001","10001","10001","10001","11110"},
    ['E'] = {"11111","10000","10000","11110","10000","10000","11111"},
    ['F'] = {"11111","10000","10000","11110","10000","10000","10000"},
    ['G'] = {"01111","10000","10000","10111","10001","10001","01111"},
    ['H'] = {"10001","10001","10001","11111","10001","10001","10001"},
    ['I'] = {"01110","00100","00100","00100","00100","00100","01110"},
    ['J'] = {"00111","00010","00010","00010","10010","10010","01100"},
    ['K'] = {"10001","10010","10100","11000","10100","10010","10001"},
    ['L'] = {"10000","10000","10000","10000","10000","10000","11111"},
    ['M'] = {"10001","11011","10101","10101","10001","10001","10001"},
    ['N'] = {"10001","11001","10101","10011","10001","10001","10001"},
    ['O'] = {"01110","10001","10001","10001","10001","10001","01110"},
    ['P'] = {"11110","10001","10001","11110","10000","10000","10000"},
    ['Q'] = {"01110","10001","10001","10001","10101","10010","01101"},
    ['R'] = {"11110","10001","10001","11110","10100","10010","10001"},
    ['S'] = {"01111","10000","10000","01110","00001","00001","11110"},
    ['T'] = {"11111","00100","00100","00100","00100","00100","00100"},
    ['U'] = {"10001","10001","10001","10001","10001","10001","01110"},
    ['V'] = {"10001","10001","10001","10001","10001","01010","00100"},
    ['W'] = {"10001","10001","10001","10101","10101","10101","01010"},
    ['X'] = {"10001","10001","01010","00100","01010","10001","10001"},
    ['Y'] = {"10001","10001","01010","00100","00100","00100","00100"},
    ['Z'] = {"11111","00001","00010","00100","01000","10000","11111"},
    [':'] = {"00000","00100","00100","00000","00100","00100","00000"},
    ['.'] = {"00000","00000","00000","00000","00000","00110","00110"},
    ['/'] = {"00001","00010","00010","00100","01000","01000","10000"},
    ['-'] = {"00000","00000","00000","11111","00000","00000","00000"},
    ['%'] = {"11001","11010","00100","01000","10110","00110","00000"}
};

static float clampf_local(float value, float low, float high)
{
    if (value < low) return low;
    if (value > high) return high;
    return value;
}

static void initialise_video_and_gx(void)
{
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
    GX_SetCopyClear((GXColor){ 104, 170, 220, 255 }, 0x00FFFFFF);
    GX_SetViewport(0.0f, 0.0f, (f32)g_video_mode->fbWidth,
                   (f32)g_video_mode->efbHeight, 0.0f, 1.0f);
    GX_SetScissor(0, 0, g_video_mode->fbWidth, g_video_mode->efbHeight);
    GX_SetDispCopySrc(0, 0, g_video_mode->fbWidth, g_video_mode->efbHeight);
    {
        u32 copied_height = GX_SetDispCopyYScale(
            GX_GetYScaleFactor(g_video_mode->efbHeight, g_video_mode->xfbHeight));
        GX_SetDispCopyDst(g_video_mode->fbWidth, (u16)copied_height);
    }
    GX_SetCopyFilter(g_video_mode->aa, g_video_mode->sample_pattern,
                     GX_TRUE, g_video_mode->vfilter);
    GX_SetFieldMode(g_video_mode->field_rendering,
                    ((g_video_mode->viHeight == 2 * g_video_mode->xfbHeight)
                         ? GX_ENABLE : GX_DISABLE));
    if (g_video_mode->aa) GX_SetPixelFmt(GX_PF_RGB565_Z16, GX_ZC_LINEAR);
    else GX_SetPixelFmt(GX_PF_RGB8_Z24, GX_ZC_LINEAR);
    GX_SetZMode(GX_TRUE, GX_LEQUAL, GX_TRUE);
    GX_SetColorUpdate(GX_TRUE);
    GX_SetAlphaUpdate(GX_TRUE);
    GX_SetCullMode(GX_CULL_NONE);
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
    GX_InvVtxCache();
    GX_SetCurrentMtx(GX_PNMTX0);
    GX_SetDispCopyGamma(GX_GM_1_0);
    GX_CopyDisp(g_framebuffers[0], GX_TRUE);
    GX_DrawDone();
    g_framebuffer_index = 1;
}

static void emit_vertex(f32 x, f32 y, f32 z, u8 r, u8 g, u8 b, u8 a)
{
    GX_Position3f32(x, y, z);
    GX_Color4u8(r, g, b, a);
}

static void draw_ground(float center_x, float center_z)
{
    const float extent = 320.0f;
    const RacerTrackInfo *info = track_catalog_get(g_selected_track);
    GX_Begin(GX_TRIANGLESTRIP, GX_VTXFMT0, 4);
    emit_vertex(center_x-extent, -8.0f, center_z-extent, info->ground_r, info->ground_g, info->ground_b, 255);
    emit_vertex(center_x+extent, -8.0f, center_z-extent, info->ground_r, info->ground_g, info->ground_b, 255);
    emit_vertex(center_x-extent, -8.0f, center_z+extent, info->ground_r, info->ground_g, info->ground_b, 255);
    emit_vertex(center_x+extent, -8.0f, center_z+extent, info->ground_r, info->ground_g, info->ground_b, 255);
    GX_End();
}

static void draw_track(void)
{
    unsigned int i;
    if (g_active_track_vertex_count == 0U) return;
    GX_Begin(GX_TRIANGLES, GX_VTXFMT0, (u16)g_active_track_vertex_count);
    for (i = 0; i < g_active_track_vertex_count; ++i) {
        const TrackVertex *v = &g_active_track_vertices[i];
        emit_vertex(v->x, v->y, v->z, v->r, v->g, v->b, 255);
    }
    GX_End();
}

static void local_vertex_basis(float px, float py, float pz, float cs, float sn,
                               float lx, float ly, float lz, u8 r, u8 g, u8 b)
{
    float wx = px + lx*cs + lz*sn;
    float wz = pz - lx*sn + lz*cs;
    emit_vertex(wx, py+ly, wz, r, g, b, 255);
}

static void draw_local_box(float px, float py, float pz, float heading,
                           float cx, float cy, float cz,
                           float hx, float hy, float hz, u8 r, u8 g, u8 b)
{
    static const u8 order[36] = {
        0,1,2, 0,2,3, 4,6,5, 4,7,6,
        0,4,5, 0,5,1, 3,2,6, 3,6,7,
        0,3,7, 0,7,4, 1,5,6, 1,6,2
    };
    float v[8][3] = {
        {cx-hx,cy-hy,cz-hz}, {cx+hx,cy-hy,cz-hz},
        {cx+hx,cy+hy,cz-hz}, {cx-hx,cy+hy,cz-hz},
        {cx-hx,cy-hy,cz+hz}, {cx+hx,cy-hy,cz+hz},
        {cx+hx,cy+hy,cz+hz}, {cx-hx,cy+hy,cz+hz}
    };
    unsigned int i;
    {
        float cs=cosf(heading), sn=sinf(heading);
        GX_Begin(GX_TRIANGLES, GX_VTXFMT0, 36);
        for (i = 0; i < 36U; ++i) {
            const float *p = v[order[i]];
            local_vertex_basis(px,py,pz,cs,sn,p[0],p[1],p[2],r,g,b);
        }
    }
    GX_End();
}

static u8 scaled_channel(u8 value, float scale, int add)
{
    int out = (int)((float)value*scale) + add;
    if (out < 0) out = 0;
    if (out > 255) out = 255;
    return (u8)out;
}

static void pod_material_color(unsigned char material, u8 r, u8 g, u8 b,
                              u8 *out_r, u8 *out_g, u8 *out_b)
{
    switch (material) {
    case POD_MAT_BODY_LIGHT:
        *out_r=scaled_channel(r,1.18f,22); *out_g=scaled_channel(g,1.18f,22);
        *out_b=scaled_channel(b,1.18f,22); break;
    case POD_MAT_DARK:
        *out_r=scaled_channel(r,0.34f,0); *out_g=scaled_channel(g,0.34f,0);
        *out_b=scaled_channel(b,0.34f,0); break;
    case POD_MAT_METAL:
        *out_r=124; *out_g=134; *out_b=145; break;
    case POD_MAT_GLASS:
        *out_r=43; *out_g=116; *out_b=155; break;
    case POD_MAT_ACCENT:
        *out_r=scaled_channel(r,0.70f,18); *out_g=scaled_channel(g,0.70f,18);
        *out_b=scaled_channel(b,0.70f,18); break;
    case POD_MAT_ENGINE:
        *out_r=23; *out_g=27; *out_b=33; break;
    case POD_MAT_BODY:
    default:
        *out_r=r; *out_g=g; *out_b=b; break;
    }
}

static void draw_flame_cone(float x, float y, float z, float heading,
                            float engine_x, float radius, float length,
                            u8 r, u8 g, u8 b, u8 tip_r, u8 tip_g, u8 tip_b)
{
    unsigned int side;
    const unsigned int sides=8U;
    {
        float cs=cosf(heading), sn=sinf(heading);
        GX_Begin(GX_TRIANGLES, GX_VTXFMT0, (u16)(sides*3U));
        for (side=0; side<sides; ++side) {
        float a0=2.0f*PI_F*(float)side/(float)sides;
        float a1=2.0f*PI_F*(float)(side+1U)/(float)sides;
        float x0=engine_x+cosf(a0)*radius;
        float y0=0.52f+sinf(a0)*radius;
        float x1=engine_x+cosf(a1)*radius;
        float y1=0.52f+sinf(a1)*radius;
        local_vertex_basis(x,y,z,cs,sn,x0,y0,-2.02f,r,g,b);
        local_vertex_basis(x,y,z,cs,sn,x1,y1,-2.02f,r,g,b);
        local_vertex_basis(x,y,z,cs,sn,engine_x,0.52f,-2.02f-length,
                           tip_r,tip_g,tip_b);
        }
        GX_End();
    }
}

static void draw_pod(const PodMesh *mesh, float x, float track_y, float z, float heading,
                     u8 r, u8 g, u8 b, int boosting)
{
    unsigned int i;
    float cs=cosf(heading), sn=sinf(heading);
    if (mesh == NULL) return;
    GX_Begin(GX_TRIANGLES, GX_VTXFMT0, (u16)mesh->vertex_count);
    for (i=0; i<mesh->vertex_count; ++i) {
        const PodVertex *v=&mesh->vertices[i];
        u8 cr,cg,cb;
        float wx=x+v->x*cs+v->z*sn;
        float wz=z-v->x*sn+v->z*cs;
        pod_material_color(v->material,r,g,b,&cr,&cg,&cb);
        emit_vertex(wx,track_y+v->y,wz,cr,cg,cb,255);
    }
    GX_End();
    if (boosting) {
        float phase=g_player.race_time*22.0f;
        float pulse=0.88f+0.18f*sinf(phase);
        float inner=0.48f+0.08f*sinf(phase*1.43f);
        draw_flame_cone(x,track_y,z,heading,-1.34f,0.31f,1.18f*pulse,
                        30,112,255,150,218,255);
        draw_flame_cone(x,track_y,z,heading, 1.34f,0.31f,1.18f*pulse,
                        30,112,255,150,218,255);
        draw_flame_cone(x,track_y,z,heading,-1.34f,0.16f,0.72f*inner,
                        151,218,255,245,249,255);
        draw_flame_cone(x,track_y,z,heading, 1.34f,0.16f,0.72f*inner,
                        151,218,255,245,249,255);
    }
}

static void scene_push(float x,float y,float z,u8 r,u8 g,u8 b)
{
    SceneVertex *v;
    if (g_scene_vertex_count >= SCENE_VERTEX_CAPACITY) return;
    v=&g_scene_vertices[g_scene_vertex_count++];
    v->x=x; v->y=y; v->z=z; v->r=r; v->g=g; v->b=b; v->a=255;
}

static void scene_triangle(const float a[3],const float b[3],const float c[3],
                           u8 r,u8 g,u8 blue,float shade)
{
    scene_push(a[0],a[1],a[2],scaled_channel(r,shade,0),
               scaled_channel(g,shade,0),scaled_channel(blue,shade,0));
    scene_push(b[0],b[1],b[2],scaled_channel(r,shade,0),
               scaled_channel(g,shade,0),scaled_channel(blue,shade,0));
    scene_push(c[0],c[1],c[2],scaled_channel(r,shade,0),
               scaled_channel(g,shade,0),scaled_channel(blue,shade,0));
}

static void build_rock_formation(float x,float z,float sx,float sz,float height,
                                 unsigned int seed,u8 r,u8 g,u8 b)
{
    enum { SIDES=7 };
    float bx[SIDES],bz[SIDES],mx[SIDES],my[SIDES],mz[SIDES];
    float base_y=-7.88f;
    float apex_x=x+((float)(seed%7U)-3.0f)*sx*0.10f;
    float apex_z=z+((float)((seed*3U)%7U)-3.0f)*sz*0.10f;
    unsigned int i;
    for(i=0;i<SIDES;++i){
        float angle=2.0f*PI_F*(float)i/(float)SIDES;
        float jitter=0.84f+(float)((seed*11U+i*7U)%25U)*0.01f;
        float mid=0.48f+(float)((seed*5U+i*3U)%25U)*0.01f;
        bx[i]=x+cosf(angle)*sx*jitter; bz[i]=z+sinf(angle)*sz*jitter;
        mx[i]=x+cosf(angle)*sx*mid; mz[i]=z+sinf(angle)*sz*mid;
        my[i]=base_y+height*(0.53f+(float)((seed+i*2U)%11U)*0.01f);
    }
    for(i=0;i<SIDES;++i){
        unsigned int n=(i+1U)%SIDES;
        float base_a[3]={bx[i],base_y,bz[i]}, base_b[3]={bx[n],base_y,bz[n]};
        float mid_a[3]={mx[i],my[i],mz[i]}, mid_b[3]={mx[n],my[n],mz[n]};
        float apex[3]={apex_x,base_y+height,apex_z};
        float facet=0.72f+(float)((seed+i*13U)%30U)*0.01f;
        scene_triangle(base_a,base_b,mid_b,r,g,b,facet);
        scene_triangle(base_a,mid_b,mid_a,r,g,b,facet*0.94f);
        scene_triangle(mid_a,mid_b,apex,r,g,b,facet*1.12f);
    }
}

static void scene_box(float px,float py,float pz,float heading,float cx,float cy,
                      float cz,float hx,float hy,float hz,u8 r,u8 g,u8 b)
{
    static const u8 order[36]={0,1,2,0,2,3,4,6,5,4,7,6,
        0,4,5,0,5,1,3,2,6,3,6,7,0,3,7,0,7,4,1,5,6,1,6,2};
    float v[8][3]={{cx-hx,cy-hy,cz-hz},{cx+hx,cy-hy,cz-hz},
        {cx+hx,cy+hy,cz-hz},{cx-hx,cy+hy,cz-hz},
        {cx-hx,cy-hy,cz+hz},{cx+hx,cy-hy,cz+hz},
        {cx+hx,cy+hy,cz+hz},{cx-hx,cy+hy,cz+hz}};
    float cs=cosf(heading),sn=sinf(heading);
    unsigned int i;
    for(i=0;i<36U;i+=3U){
        float tri[3][3]; unsigned int j;
        for(j=0;j<3U;++j){const float *p=v[order[i+j]];
            tri[j][0]=px+p[0]*cs+p[2]*sn; tri[j][1]=py+p[1];
            tri[j][2]=pz-p[0]*sn+p[2]*cs;}
        scene_triangle(tri[0],tri[1],tri[2],r,g,b,1.0f);
    }
}

static void build_planet_landmarks(unsigned int track_index);

static void build_scene_assets(void)
{
    const RacerTrackInfo *track_info=track_catalog_get(g_selected_track);
    unsigned int count=g_active_track_count;
    unsigned int stride=count/18U;
    unsigned int i;
    if(stride<2U) stride=2U;
    g_scene_vertex_count=0;
    for(i=0;i<count;i+=stride){
        unsigned int prev=(i+count-1U)%count, next=(i+1U)%count;
        float dx=g_active_track[next].x-g_active_track[prev].x;
        float dz=g_active_track[next].z-g_active_track[prev].z;
        float len=sqrtf(dx*dx+dz*dz);
        float nx,nz; unsigned int side; unsigned int seed=i+7U;
        if(len<0.001f) continue;
        nx=dz/len; nz=-dx/len;
        for(side=0;side<2U;++side){
            float sign=side==0U ? -1.0f : 1.0f;
            float off=10.5f+(float)((seed*(side+3U))%9U)*1.15f;
            float rx=1.8f+(float)((seed+side*3U)%4U)*0.48f;
            float rz=2.0f+(float)((seed*3U+side)%4U)*0.55f;
            float h=2.4f+(float)((seed*7U+side*5U)%8U)*0.72f;
            build_rock_formation(g_active_track[i].x+nx*off*sign,
                                 g_active_track[i].z+nz*off*sign,
                                 rx,rz,h,seed+side*11U,
                                 scaled_channel(track_info->rock_r,0.86f+(float)(seed%20U)*0.01f,0),
                                 scaled_channel(track_info->rock_g,0.86f+(float)(seed%20U)*0.01f,0),
                                 scaled_channel(track_info->rock_b,0.86f+(float)(seed%20U)*0.01f,0));
        }
        /* Short safety posts, baked once so they cost no trigonometry per frame. */
        if((i%(stride*3U))==0U){
            float heading=atan2f(dx,dz);
            scene_box(g_active_track[i].x,g_active_track[i].y,
                      g_active_track[i].z,heading,-8.5f,0.35f,0.0f,
                      0.16f,0.42f,0.16f,218,203,165);
            scene_box(g_active_track[i].x,g_active_track[i].y,
                      g_active_track[i].z,heading,8.5f,0.35f,0.0f,
                      0.16f,0.42f,0.16f,218,203,165);
        }
    }
    /* Big mesas give the synthetic course a skyline. */
    for(i=0;i<10U;++i){
        unsigned int idx=(i*count)/10U;
        unsigned int prev=(idx+count-1U)%count, next=(idx+1U)%count;
        float dx=g_active_track[next].x-g_active_track[prev].x;
        float dz=g_active_track[next].z-g_active_track[prev].z;
        float len=sqrtf(dx*dx+dz*dz);
        float nx,nz,sign=(i%2U)==0U ? -1.0f : 1.0f;
        if(len<0.001f) continue;
        nx=dz/len; nz=-dx/len;
        build_rock_formation(g_active_track[idx].x+nx*(42.0f+(float)(i%4U)*5.0f)*sign,
                             g_active_track[idx].z+nz*(42.0f+(float)(i%4U)*5.0f)*sign,
                             7.0f+(float)(i%3U)*2.0f,9.0f+(float)(i%4U)*2.0f,
                             8.5f+(float)(i%5U)*1.8f,i+91U,track_info->rock_r,track_info->rock_g,track_info->rock_b);
    }
    build_planet_landmarks(g_selected_track);
}

/* Planet-specific landmark silhouettes. These are original procedural props,
 * not extracted assets; they make the eight environments read differently. */
static void build_planet_landmarks(unsigned int track_index)
{
    unsigned int count=g_active_track_count;
    unsigned int n, step=count/8U;
    TrackBiome biome;
    const RacerTrackInfo *info=track_catalog_get(track_index);
    if(step<1U) step=1U;
    biome=track_catalog_biome(track_index);

    for(n=0U;n<8U;++n){
        unsigned int idx=(n*step)%count;
        unsigned int prev=(idx+count-1U)%count,next=(idx+1U)%count;
        float dx=g_active_track[next].x-g_active_track[prev].x;
        float dz=g_active_track[next].z-g_active_track[prev].z;
        float len=sqrtf(dx*dx+dz*dz),nx,nz;
        float side=(n%2U)==0U ? -1.0f : 1.0f;
        float px,pz,heading=atan2f(dx,dz);
        u8 r=info->rock_r,g=info->rock_g,b=info->rock_b;
        if(len<0.001f) continue;
        nx=dz/len; nz=-dx/len;
        px=g_active_track[idx].x+nx*side*(17.0f+(float)(n%3U)*2.5f);
        pz=g_active_track[idx].z+nz*side*(17.0f+(float)(n%3U)*2.5f);
        switch(biome){
        case TRACK_BIOME_SANDSTONE: /* angular sandstone cairns */
            build_rock_formation(px,pz,2.5f,3.0f,4.0f+(float)(n%3U),n+201U,r,g,b);
            break;
        case TRACK_BIOME_ICE: /* frozen blue-white crystal / ice spires */
            scene_box(px, g_active_track[idx].y, pz, heading, 0.0f,1.7f,0.0f,
                      0.8f,1.8f,0.8f,125,183,210);
            scene_box(px, g_active_track[idx].y, pz, heading, 0.0f,3.8f,0.0f,
                      0.38f,1.0f,0.42f,190,225,239);
            break;
        case TRACK_BIOME_JUNGLE: /* jungle trunks and broad canopy blocks */
            scene_box(px,g_active_track[idx].y,pz,heading,0.0f,1.8f,0.0f,
                      0.45f,1.8f,0.45f,91,73,43);
            scene_box(px,g_active_track[idx].y,pz,heading,0.0f,3.6f,0.0f,
                      2.1f,0.75f,1.8f,53,113,63);
            scene_box(px,g_active_track[idx].y,pz,heading,0.0f,4.45f,0.0f,
                      1.35f,0.55f,1.25f,76,143,77);
            break;
        case TRACK_BIOME_COASTAL: /* coastal pylons / coral-like columns */
            scene_box(px,g_active_track[idx].y,pz,heading,0.0f,1.2f,0.0f,
                      1.2f,1.2f,1.1f,48,116,143);
            scene_box(px,g_active_track[idx].y,pz,heading,0.0f,2.8f,0.0f,
                      0.65f,1.0f,0.65f,84,174,190);
            break;
        case TRACK_BIOME_VOLCANIC: /* volcanic rock pillars */
            build_rock_formation(px,pz,2.1f,2.4f,5.0f+(float)(n%4U)*0.7f,
                                 n+301U,r,g,b);
            break;
        case TRACK_BIOME_REFINERY: /* refinery gantries, visually distinct from natural rocks */
            scene_box(px,g_active_track[idx].y,pz,heading,0.0f,1.8f,0.0f,
                      2.4f,1.8f,0.45f,91,91,87);
            scene_box(px,g_active_track[idx].y,pz,heading,0.0f,3.8f,0.0f,
                      2.8f,0.22f,0.6f,201,139,65);
            scene_box(px,g_active_track[idx].y,pz,heading,-1.8f,2.8f,0.0f,
                      0.22f,1.0f,0.3f,146,151,148);
            scene_box(px,g_active_track[idx].y,pz,heading,1.8f,2.8f,0.0f,
                      0.22f,1.0f,0.3f,146,151,148);
            break;
        case TRACK_BIOME_SKYPORT: /* Ord Ibanna landing towers */
            scene_box(px,g_active_track[idx].y,pz,heading,0.0f,2.1f,0.0f,
                      1.0f,2.1f,1.0f,151,137,103);
            scene_box(px,g_active_track[idx].y,pz,heading,0.0f,4.4f,0.0f,
                      1.8f,0.25f,1.8f,203,181,132);
            break;
        case TRACK_BIOME_ASTEROID_FACILITY: /* Oovo IV: dark metal containment pylons */
            scene_box(px,g_active_track[idx].y,pz,heading,0.0f,1.8f,0.0f,
                      0.9f,1.8f,0.9f,76,79,91);
            scene_box(px,g_active_track[idx].y,pz,heading,0.0f,3.8f,0.0f,
                      1.35f,0.2f,1.35f,180,94,76);
            scene_box(px,g_active_track[idx].y,pz,heading,0.0f,4.35f,0.0f,
                      0.22f,0.4f,0.22f,231,183,83);
            break;
        }
    }
}

static void configure_rival_vehicles(void)
{
    unsigned int i;
    unsigned int count = vehicle_catalog_count();
    for (i = 0U; i < OPPONENT_COUNT; ++i) {
        unsigned int model_index = (g_selected_vehicle + i + 1U) % count;
        rival_ai_set_vehicle_spec(&g_rivals[i], vehicle_catalog_get(model_index));
    }
    rival_ai_set_difficulty(g_rivals, OPPONENT_COUNT, g_ai_difficulty);
    {
        const RacerTrackInfo *surface = track_catalog_get(g_selected_track);
        rival_ai_set_track_surface(g_rivals, OPPONENT_COUNT,
                                   surface->surface_grip,
                                   surface->rolling_resistance);
        rival_ai_set_track_width(g_rivals, OPPONENT_COUNT, surface->width);
    }
}

static int load_selected_course(void)
{
    RacerTrackProjection projection;
    if (!track_catalog_build_points(g_selected_track, g_active_track,
                                    TRACK_POINT_CAPACITY, &g_active_track_count)) return 0;
    if (g_reverse_track && !track_direction_reverse(g_active_track, g_active_track_count)) return 0;
    if (!track_catalog_build_mesh(g_selected_track, g_active_track,
                                  g_active_track_count, g_active_track_vertices,
                                  TRACK_VERTEX_CAPACITY, &g_active_track_vertex_count)) return 0;
    projection = racer_project_to_track(g_active_track[0].x, g_active_track[0].z,
                                        g_active_track, g_active_track_count);
    g_track_length = projection.total_length > 1.0f ? projection.total_length : 1.0f;
    racer_init(&g_player, g_active_track, g_active_track_count);
    rival_ai_init(g_rivals, OPPONENT_COUNT, g_active_track,
                  g_active_track_count, g_track_length);
    configure_rival_vehicles();
    race_items_init(g_race_items, RACE_ITEM_COUNT, g_selected_track);
    race_feedback_init(&g_race_feedback);
    g_last_item = RACE_ITEM_NONE;
    g_item_flash_timer = 0.0f;
    g_camera_ready = 0;
    build_scene_assets();
    return 1;
}

static void draw_scene_assets(void)
{
    unsigned int i;
    if(g_scene_vertex_count==0U) return;
    GX_Begin(GX_TRIANGLES,GX_VTXFMT0,g_scene_vertex_count);
    for(i=0;i<g_scene_vertex_count;++i){
        const SceneVertex *v=&g_scene_vertices[i];
        emit_vertex(v->x,v->y,v->z,v->r,v->g,v->b,v->a);
    }
    GX_End();
}

static void draw_start_gate(void)
{
    const RacerTrackPoint *p=&g_active_track[0];
    const RacerTrackPoint *next=&g_active_track[1U%g_active_track_count];
    const RacerTrackInfo *track_info=track_catalog_get(g_selected_track);
    RaceGateGeometry gate;
    float heading=atan2f(next->x-p->x,next->z-p->z);
    u8 lamp_r=220,lamp_g=42,lamp_b=30;
    unsigned int i;
    if (!race_gate_geometry_build(track_info->width, &gate)) return;
    draw_local_box(p->x,p->y,p->z,heading,-gate.post_offset,1.55f,0.0f,
                   0.32f,1.55f,0.42f,70,74,79);
    draw_local_box(p->x,p->y,p->z,heading,gate.post_offset,1.55f,0.0f,
                   0.32f,1.55f,0.42f,70,74,79);
    draw_local_box(p->x,p->y,p->z,heading,0.0f,3.15f,0.0f,
                   gate.crossbar_half_width,0.30f,0.46f,93,48,35);
    if(g_race_flow.phase==RACE_PHASE_RUNNING){lamp_r=45;lamp_g=230;lamp_b=95;}
    else if(g_race_flow.phase==RACE_PHASE_FINISHED){lamp_r=255;lamp_g=215;lamp_b=85;}
    for(i=0;i<4U;++i){
        float cx=-1.8f+(float)i*1.2f;
        draw_local_box(p->x,p->y,p->z,heading,cx,2.72f,0.0f,
                       0.36f,0.18f,0.16f,lamp_r,lamp_g,lamp_b);
    }
    /* A striped start line lies on the road surface. */
    for(i=0;i<RACE_GATE_STRIPE_COUNT;++i){
        u8 shade=(i%2U)==0U ? 238U : 35U;
        draw_local_box(p->x,p->y+0.03f,p->z,heading,
                       gate.stripe_centers[i],0.0f,0.0f,
                       gate.stripe_half_width,0.035f,0.28f,shade,shade,shade);
    }
}

static void draw_track_items(void)
{
    unsigned int i;
    for (i=0; i<RACE_ITEM_COUNT; ++i) {
        const RaceItem *it=&g_race_items[i];
        float x,y,z,heading;
        u8 r=50,g=180,b=255;
        if (!race_items_visible(it,g_player.lap)) continue;
        if (!race_items_get_pose(it,g_active_track,g_active_track_count,
                                 &x,&y,&z,&heading)) continue;
        if (it->type==RACE_ITEM_REPAIR) { r=65; g=235; b=112; }
        else if (it->type==RACE_ITEM_HAZARD) { r=250; g=65; b=35; }
        draw_local_box(x,y,z,heading,0.0f,0.0f,0.0f,3.45f,0.12f,0.58f,r,g,b);
        if (it->type==RACE_ITEM_HAZARD) {
            draw_local_box(x,y+0.42f,z,heading,-2.35f,0.0f,0.0f,0.16f,0.38f,0.18f,255,122,48);
            draw_local_box(x,y+0.42f,z,heading, 2.35f,0.0f,0.0f,0.16f,0.38f,0.18f,255,122,48);
        } else {
            draw_local_box(x,y+0.38f,z,heading,-2.75f,0.0f,0.0f,0.13f,0.30f,0.13f,r,g,b);
            draw_local_box(x,y+0.38f,z,heading, 2.75f,0.0f,0.0f,0.13f,0.30f,0.13f,r,g,b);
        }
    }
}

static void initialise_race(void)
{
    g_paused = 0;
    g_finish_recorded = 0;
    racer_init(&g_player, g_active_track, g_active_track_count);
    race_flow_init(&g_race_flow, 3U);
    race_feedback_init(&g_race_feedback);
    voice_over_runtime_init(&g_voice_over_runtime);
    rival_ai_init(g_rivals, OPPONENT_COUNT, g_active_track,
                  g_active_track_count, g_track_length);
    configure_rival_vehicles();
    race_items_init(g_race_items, RACE_ITEM_COUNT, g_selected_track);
    g_collision_flash_timer = 0.0f;
    g_drafting_active = 0;
    g_last_item = RACE_ITEM_NONE;
    g_item_flash_timer = 0.0f;
    g_camera_ready = 0;
    g_game_mode = GAME_MODE_RACE;
}

static void update_rivals(float dt)
{
    if (g_time_trial_enabled) return;
    if (rival_ai_update(g_rivals, OPPONENT_COUNT, g_active_track,
                        g_active_track_count, g_track_length, &g_player,
                        selected_player_vehicle_spec(), dt)) {
        g_collision_flash_timer = 0.75f;
    }
}

static void hud_quad(float x, float y, float w, float h, u8 r, u8 g, u8 b)
{
    static const u8 idx[6] = {0,1,2,0,2,3};
    float v[4][3] = {{0,0,0},{0,0,0},{0,0,0},{0,0,0}};
    unsigned int i;
    v[0][0] = x;     v[0][1] = y;
    v[1][0] = x+w;   v[1][1] = y;
    v[2][0] = x+w;   v[2][1] = y+h;
    v[3][0] = x;     v[3][1] = y+h;
    for (i = 0; i < 6U && g_hud_count < HUD_VERTEX_CAPACITY; ++i) {
        const float *p = v[idx[i]];
        HudVertex *out = &g_hud_vertices[g_hud_count++];
        out->x = p[0]; out->y = p[1]; out->z = 0.0f;
        out->r = r; out->g = g; out->b = b; out->a = 255;
    }
}

static void hud_text(float x, float y, float scale, const char *text,
                     u8 r, u8 g, u8 b)
{
    unsigned int ch_index;
    if (text == NULL) return;
    for (ch_index = 0; text[ch_index] != '\0'; ++ch_index) {
        unsigned char ch = (unsigned char)text[ch_index];
        unsigned int row, col;
        if (ch < 128U) {
            for (row = 0; row < 7U; ++row) {
                for (col = 0; col < 5U; ++col) {
                    if (g_font[ch][row][col] == '1') {
                        hud_quad(x + (float)col*scale, y + (float)row*scale,
                                 scale*0.82f, scale*0.82f, r, g, b);
                    }
                }
            }
        }
        x += scale*6.0f;
    }
}

static void draw_hud(void)
{
    Mtx identity;
    Mtx44 projection;
    char line[32];
    char bestline[32];
    float screen_w = (float)g_video_mode->fbWidth;
    float screen_h = (float)g_video_mode->efbHeight;
    float speed_kmh = g_player.speed * 3.6f;
    float boost_w = 72.0f * clampf_local(g_player.boost_energy/100.0f, 0.0f, 1.0f);
    float heat_w = 72.0f * clampf_local(g_player.boost_heat/100.0f, 0.0f, 1.0f);
    float hull_w = 106.0f * clampf_local((100.0f-g_player.damage)/100.0f, 0.0f, 1.0f);
    unsigned int place = 1U;
    unsigned int i;
    float pprogress = race_standings_progress(g_player.lap, g_player.track_progress);

    if (!g_time_trial_enabled) {
        float opponent_progress[OPPONENT_COUNT];
        for (i = 0U; i < OPPONENT_COUNT; ++i)
            opponent_progress[i] = race_standings_progress(g_rivals[i].lap, g_rivals[i].progress);
        place = race_standings_player_place(pprogress, opponent_progress, OPPONENT_COUNT);
    }

    g_hud_count = 0;
    hud_quad(12.0f, 12.0f, 212.0f, 90.0f, 12, 18, 25);
    hud_text(22.0f, 20.0f, 1.7f, "SPEED", 230, 235, 240);
    (void)snprintf(line, sizeof(line), "%03d KMH", (int)(speed_kmh + 0.5f));
    hud_text(93.0f, 20.0f, 1.7f, line, 255, 226, 129);
    if (g_time_trial_enabled)
        (void)snprintf(line, sizeof(line), "LAP %02u TIME TRIAL", g_player.lap);
    else
        (void)snprintf(line, sizeof(line), "LAP %02u POS %u/8", g_player.lap, place);
    hud_text(22.0f, 38.0f, 1.6f, line, 230, 235, 240);
    {
        unsigned int minutes = (unsigned int)(g_player.race_time / 60.0f);
        float seconds = g_player.race_time - (float)minutes*60.0f;
        (void)snprintf(line, sizeof(line), "TIME %02u:%05.2f", minutes, seconds);
    }
    hud_text(22.0f, 57.0f, 1.35f, line, 190, 216, 232);
    if (g_player.best_lap_time > 0.0f) {
        unsigned int best_minutes = (unsigned int)(g_player.best_lap_time / 60.0f);
        float best_seconds = g_player.best_lap_time - (float)best_minutes*60.0f;
        (void)snprintf(bestline, sizeof(bestline), "BEST %02u:%05.2f",
                       best_minutes, best_seconds);
    } else {
        (void)snprintf(bestline, sizeof(bestline), "BEST --:--.--");
    }
    hud_text(22.0f, 76.0f, 1.12f, bestline, 255, 226, 129);
    if (g_drafting_active) {
        hud_quad(12.0f, 108.0f, 106.0f, 18.0f, 18, 60, 78);
        hud_text(20.0f, 113.0f, 1.15f, "SLIPSTREAM", 126, 230, 255);
    }

    hud_quad(screen_w-158.0f, 12.0f, 146.0f, 50.0f, 12, 18, 25);
    hud_text(screen_w-150.0f, 18.0f, 1.35f, "BOOST", 230, 235, 240);
    hud_quad(screen_w-92.0f, 20.0f, 72.0f, 8.0f, 42, 48, 54);
    hud_quad(screen_w-92.0f, 20.0f, boost_w, 8.0f,
             g_player.boost_active ? 61 : 202, g_player.boost_active ? 175 : 160,
             g_player.boost_active ? 255 : 73);
    hud_text(screen_w-150.0f, 36.0f, 1.15f, "HEAT", 230, 235, 240);
    hud_quad(screen_w-92.0f, 38.0f, 72.0f, 8.0f, 42, 48, 54);
    hud_quad(screen_w-92.0f, 38.0f, heat_w, 8.0f,
             g_player.overheated ? 240 : 221, g_player.overheated ? 48 : 117,
             g_player.overheated ? 32 : 62);
    if (g_player.offroad) {
        hud_quad(12.0f, 107.0f, 115.0f, 22.0f, 82, 21, 17);
        hud_text(20.0f, 114.0f, 1.6f, "OFF ROAD", 255, 220, 200);
    }
    if (g_player.overheated) {
        hud_quad(screen_w-158.0f, 66.0f, 146.0f, 22.0f, 82, 21, 17);
        hud_text(screen_w-150.0f, 71.0f, 1.35f, "OVERHEAT", 255, 220, 200);
    }
    if (g_race_feedback.wrong_way && g_race_flow.phase == RACE_PHASE_RUNNING) {
        hud_quad(screen_w*0.5f-74.0f, screen_h*0.12f, 148.0f, 27.0f, 104, 24, 18);
        hud_text(screen_w*0.5f-43.0f, screen_h*0.12f+7.0f, 1.55f,
                 "WRONG WAY", 255, 239, 224);
    }
    if (g_collision_flash_timer > 0.0f) {
        hud_quad(screen_w*0.5f-58.0f, 14.0f, 116.0f, 24.0f, 92, 34, 15);
        hud_text(screen_w*0.5f-25.0f, 21.0f, 1.4f, "IMPACT", 255, 238, 222);
    }

    hud_quad(12.0f, screen_h-30.0f, 150.0f, 20.0f, 12, 18, 25);
    hud_text(18.0f, screen_h-25.0f, 1.0f, "HULL", 230, 235, 240);
    hud_quad(56.0f, screen_h-22.0f, 98.0f, 7.0f, 42, 48, 54);
    hud_quad(56.0f, screen_h-22.0f, hull_w, 7.0f,
             g_player.damage>60.0f ? 230 : 68,
             g_player.damage>60.0f ? 70 : 202,
             g_player.damage>60.0f ? 45 : 120);
    if (g_player.drifting) {
        hud_quad(screen_w*0.5f-50.0f, screen_h-36.0f, 100.0f, 21.0f, 16, 47, 88);
        hud_text(screen_w*0.5f-24.0f, screen_h-31.0f, 1.2f, "DRIFT", 135, 218, 255);
    }
    if (g_item_flash_timer > 0.0f) {
        const char *item_text = g_last_item==RACE_ITEM_BOOST ? "BOOST PICKUP" :
                                (g_last_item==RACE_ITEM_REPAIR ? "POD REPAIRED" : "HAZARD HIT");
        u8 ir=g_last_item==RACE_ITEM_HAZARD?255:130;
        u8 ig=g_last_item==RACE_ITEM_REPAIR?255:225;
        u8 ib=g_last_item==RACE_ITEM_BOOST?255:190;
        hud_quad(screen_w*0.5f-83.0f, screen_h*0.18f, 166.0f, 24.0f, 16, 25, 34);
        hud_text(screen_w*0.5f-58.0f, screen_h*0.18f+6.0f, 1.2f, item_text, ir, ig, ib);
    }
    {
        const RacerVehicleSpec *vehicle=selected_player_vehicle_spec();
        const RacerTrackInfo *track_info=track_catalog_get(g_selected_track);
        hud_text(screen_w*0.5f-92.0f, screen_h-17.0f, 0.85f,
                 vehicle->name, 220, 226, 233);
        hud_text(screen_w*0.5f+4.0f, screen_h-17.0f, 0.85f,
                 track_info->name, 220, 226, 233);
    }

    /* Race-state overlay: countdown, green-light GO, and finish prompt. */
    if (g_race_flow.phase == RACE_PHASE_COUNTDOWN) {
        int count = race_flow_countdown_label(&g_race_flow);
        hud_quad(screen_w*0.5f-66.0f, screen_h*0.30f-20.0f,
                 132.0f, 76.0f, 12, 18, 25);
        if (count > 0) {
            char count_text[2] = {(char)('0' + count), '\0'};
            hud_text(screen_w*0.5f-8.0f, screen_h*0.30f, 5.0f,
                     count_text, 255, 226, 129);
        } else {
            hud_text(screen_w*0.5f-24.0f, screen_h*0.30f+4.0f, 3.2f,
                     "GO", 100, 255, 130);
        }
    } else if (g_race_flow.phase == RACE_PHASE_FINISHED) {
        hud_quad(screen_w*0.5f-145.0f, screen_h*0.30f-25.0f,
                 290.0f, (g_championship_enabled && g_championship.rounds_completed >= g_championship.rounds_total) ? 166.0f : 100.0f, 12, 18, 25);
        hud_text(screen_w*0.5f-65.0f, screen_h*0.30f-12.0f, 2.5f,
                 g_time_trial_enabled ? game_text(GAME_TEXT_TIME_TRIAL) : game_text(GAME_TEXT_FINISH), 255, 226, 129);
        {
            unsigned int result_minutes = (unsigned int)(g_player.race_time / 60.0f);
            float result_seconds = g_player.race_time - (float)result_minutes * 60.0f;
            if (g_time_trial_enabled)
                (void)snprintf(line, sizeof(line), "TOTAL %02u:%05.2f", result_minutes, result_seconds);
            else
                (void)snprintf(line, sizeof(line), "P%u/8  %02u:%05.2f",
                               place, result_minutes, result_seconds);
        }
        hud_text(screen_w*0.5f-68.0f, screen_h*0.30f+20.0f, 1.15f,
                 line, place == 1U ? 255 : 230, place == 1U ? 226 : 235,
                 place == 1U ? 129 : 240);
        if (g_time_trial_enabled) {
            unsigned int best_minutes = (unsigned int)(g_player.best_lap_time / 60.0f);
            float best_seconds = g_player.best_lap_time - (float)best_minutes * 60.0f;
            (void)snprintf(line, sizeof(line), "BEST %02u:%05.2f", best_minutes, best_seconds);
            hud_text(screen_w*0.5f-62.0f, screen_h*0.30f+39.0f, 1.05f, line, 120, 208, 255);
            hud_text(screen_w*0.5f-31.0f, screen_h*0.30f+58.0f, 1.0f,
                     "PRESS Y", 230, 235, 240);
        } else if (g_championship_enabled) {
            char pointsline[64];
            unsigned int standings[CHAMPIONSHIP_MAX_RACERS];
            championship_standings(&g_championship, standings);
            (void)snprintf(pointsline, sizeof(pointsline), "YOU %u PTS  LEADER %u",
                           g_championship.points[0],
                           g_championship.points[standings[0]]);
            hud_text(screen_w*0.5f-65.0f, screen_h*0.30f+42.0f, 0.82f, pointsline, 120, 208, 255);
            if (g_championship.rounds_completed >= g_championship.rounds_total) {
                char winnerline[32];
                unsigned int order[CHAMPIONSHIP_MAX_RACERS];
                unsigned int row;
                unsigned int winner = championship_winner(&g_championship);
                (void)snprintf(winnerline, sizeof(winnerline), "CHAMPION: %s", race_racer_label(winner));
                hud_text(screen_w*0.5f-66.0f, screen_h*0.30f+61.0f, 1.05f, winnerline, 255, 226, 129);
                championship_standings(&g_championship, order);
                for (row = 0U; row < CHAMPIONSHIP_MAX_RACERS; ++row) {
                    char standing[32];
                    unsigned int racer = order[row];
                    const char *name = race_racer_label(racer);
                    (void)snprintf(standing, sizeof(standing), "%u. %s  %u PTS", row + 1U, name, g_championship.points[racer]);
                    hud_text(screen_w*0.5f-65.0f, screen_h*0.30f+74.0f+(float)row*12.0f, 0.75f,
                             standing, row == 0U ? 255 : 210, row == 0U ? 226 : 220, row == 0U ? 129 : 230);
                }
                hud_text(screen_w*0.5f-31.0f, screen_h*0.30f+124.0f, 0.85f, "END: PRESS Y", 230, 235, 240);
            } else {
                hud_text(screen_w*0.5f-31.0f, screen_h*0.30f+58.0f, 1.0f, "NEXT: PRESS Y", 230, 235, 240);
            }
        } else {
            hud_text(screen_w*0.5f-31.0f, screen_h*0.30f+49.0f, 1.2f,
                     "PRESS Y", 230, 235, 240);
        }
    }

    if (g_paused) {
        hud_quad(screen_w*0.5f-112.0f, screen_h*0.5f-48.0f,
                 224.0f, 96.0f, 10, 18, 28);
        hud_text(screen_w*0.5f-47.0f, screen_h*0.5f-28.0f, 2.1f,
                 game_text(GAME_TEXT_PAUSED), 255, 226, 129);
        hud_text(screen_w*0.5f-75.0f, screen_h*0.5f+2.0f, 1.05f,
                 game_text(GAME_TEXT_RESUME), 220, 235, 245);
        hud_text(screen_w*0.5f-75.0f, screen_h*0.5f+20.0f, 1.05f,
                 game_text(GAME_TEXT_QUIT_RACE), 220, 235, 245);
    }

    /* English VO subtitle event bridge; WAV playback is a later platform task. */
    if (g_game_mode == GAME_MODE_RACE && !g_paused) {
        const char *subtitle = voice_over_runtime_subtitle(&g_voice_over_runtime);
        if (subtitle != NULL) {
            float box_width = screen_w - 56.0f;
            hud_quad(28.0f, screen_h - 62.0f, box_width, 28.0f, 8, 13, 22);
            hud_text(36.0f, screen_h - 52.0f, 0.95f, subtitle, 255, 239, 192);
        }
    }

    if (g_hud_count == 0U) return;
    guOrtho(projection, 0.0f, screen_h, 0.0f, screen_w, 0.0f, 1.0f);
    guMtxIdentity(identity);
    GX_LoadProjectionMtx(projection, GX_ORTHOGRAPHIC);
    GX_LoadPosMtxImm(identity, GX_PNMTX0);
    GX_SetZMode(GX_FALSE, GX_ALWAYS, GX_FALSE);
    GX_Begin(GX_TRIANGLES, GX_VTXFMT0, (u16)g_hud_count);
    for (i = 0; i < g_hud_count; ++i) {
        const HudVertex *v = &g_hud_vertices[i];
        emit_vertex(v->x, v->y, v->z, v->r, v->g, v->b, v->a);
    }
    GX_End();
    GX_SetZMode(GX_TRUE, GX_LEQUAL, GX_TRUE);
}

static void draw_selection_hud(void)
{
    Mtx identity;
    Mtx44 projection;
    const RacerTrackInfo *track=track_catalog_get(g_selected_track);
    const RacerVehicleSpec *vehicle=selected_player_vehicle_spec();
    float sw=(float)g_video_mode->fbWidth, sh=(float)g_video_mode->efbHeight;
    float left=34.0f, bar_x=178.0f, bar_w=150.0f;
    float top_value=clampf_local((vehicle->top_speed-40.0f)/17.0f,0.0f,1.0f);
    float accel_value=clampf_local((vehicle->acceleration-15.0f)/9.0f,0.0f,1.0f);
    float turn_value=clampf_local((vehicle->steering-0.75f)/0.6f,0.0f,1.0f);
    float grip_value=clampf_local((vehicle->grip-0.75f)/0.6f,0.0f,1.0f);
    g_hud_count=0U;
    hud_quad(16.0f,14.0f,sw-32.0f,sh*0.59f,9,15,23);
    hud_text(left,25.0f,2.2f,game_text(GAME_TEXT_TITLE),255,226,129);
    hud_text(left,50.0f,1.15f,game_text(GAME_TEXT_SELECT_POD_TRACK),206,221,234);
    hud_text(left,76.0f,1.45f,game_text(GAME_TEXT_TRACK),230,235,240);
    hud_text(102.0f,76.0f,1.45f,track->name,255,226,129);
    hud_text(left,96.0f,1.45f,game_text(GAME_TEXT_POD),230,235,240);
    hud_text(102.0f,96.0f,1.45f,vehicle->name,255,226,129);
    hud_text(sw*0.57f,72.0f,1.0f,track->planet,255,226,129);
    hud_text(sw*0.57f,86.0f,0.9f,track->description,206,221,234);
    hud_text(sw*0.57f,101.0f,0.95f, g_reverse_track ? game_text(GAME_TEXT_DIRECTION_REVERSE) : game_text(GAME_TEXT_DIRECTION_NORMAL),
             g_reverse_track ? 255 : 194, g_reverse_track ? 190 : 209, 129);
    hud_text(sw*0.57f,128.0f,0.95f, g_ai_difficulty == 0U ? game_text(GAME_TEXT_AI_EASY) :
             (g_ai_difficulty == 2U ? game_text(GAME_TEXT_AI_HARD) : game_text(GAME_TEXT_AI_NORMAL)),
             g_ai_difficulty == 2U ? 255 : 190, g_ai_difficulty == 0U ? 230 : 210, 160);
    {
        char surface_line[40];
        (void)snprintf(surface_line,sizeof(surface_line),"GRIP %.2f  TERRAIN DRAG %.2f",
                       track->surface_grip,track->rolling_resistance);
        hud_text(sw*0.57f,114.0f,0.9f,surface_line,190,210,225);
    }
    {
        char career_line[40];
        (void)snprintf(career_line, sizeof(career_line), "CAREER %u RACES  %u WINS",
                       g_career_profile.races_completed, g_career_profile.race_wins);
        hud_text(left,190.0f,1.0f,career_line,190,210,225);
        hud_text(left,204.0f,0.9f,g_card_save_available ? "MEMORY CARD SAVE OK" : "NO MEMORY CARD SAVE",
                 g_card_save_available ? 115 : 235, g_card_save_available ? 230 : 155,
                 g_card_save_available ? 150 : 135);
    }
    {
        char garage_line[64];
        unsigned int level = g_career_profile.upgrade_levels[(unsigned int)g_garage_part];
        unsigned int cost = garage_upgrade_cost(level);
        (void)snprintf(garage_line, sizeof(garage_line), "CREDITS %u", g_career_profile.credits);
        hud_text(sw*0.57f, 194.0f, 1.05f, garage_line, 255, 226, 129);
        (void)snprintf(garage_line, sizeof(garage_line), "%s LV %u/5", garage_part_name(g_garage_part), level);
        hud_text(sw*0.57f, 208.0f, 0.9f, garage_line, 180, 220, 255);
        if (cost > 0U) (void)snprintf(garage_line, sizeof(garage_line), "NEXT PART: %u CR", cost);
        else (void)snprintf(garage_line, sizeof(garage_line), "PART MAXED OUT");
        hud_text(sw*0.57f, 220.0f, 0.85f, garage_line, 180, 220, 255);
        if (g_garage_notice_timer > 0.0f)
            hud_text(sw*0.57f, 234.0f, 0.85f, g_garage_notice, 120, 240, 158);
    }

    hud_text(left,121.0f,1.15f,"TOP SPEED",211,222,233);
    hud_quad(bar_x,122.0f,bar_w,7.0f,41,49,60);
    hud_quad(bar_x,122.0f,bar_w*top_value,7.0f,241,192,75);
    hud_text(left,137.0f,1.15f,"ACCEL",211,222,233);
    hud_quad(bar_x,138.0f,bar_w,7.0f,41,49,60);
    hud_quad(bar_x,138.0f,bar_w*accel_value,7.0f,90,190,245);
    hud_text(left,153.0f,1.15f,"TURN",211,222,233);
    hud_quad(bar_x,154.0f,bar_w,7.0f,41,49,60);
    hud_quad(bar_x,154.0f,bar_w*turn_value,7.0f,90,230,150);
    hud_text(left,169.0f,1.15f,"GRIP",211,222,233);
    hud_quad(bar_x,170.0f,bar_w,7.0f,41,49,60);
    hud_quad(bar_x,170.0f,bar_w*grip_value,7.0f,188,125,235);
    hud_text(sw*0.57f,121.0f,1.15f,"BOOST",211,222,233);
    hud_text(sw*0.57f,138.0f,1.05f,"DRIFT TO RECHARGE",120,208,255);
    hud_text(sw*0.57f,158.0f,1.05f,"COLLECT BLUE PADS",120,208,255);
    hud_text(sw*0.57f,178.0f,1.05f,"GREEN PADS REPAIR",120,240,158);
    hud_text(left,sh*0.50f,1.15f,"LEFT RIGHT: POD",235,235,235);
    hud_text(sw*0.53f,sh*0.50f,1.15f,"UP DOWN: TRACK",235,235,235);
    hud_text(left,sh*0.535f,1.10f,"A START   B REVERSE TRACK   X BOOST",255,226,129);
    hud_text(left,sh*0.575f,0.90f,"Y: SELECT PART   Z: BUY UPGRADE",255,226,129);
    hud_text(left,sh*0.56f,0.85f,"AVOID RED HAZARDS. REPAIRS AND BOOSTS RETURN EACH LAP.",194,209,224);
    hud_text(sw*0.77f,sh*0.56f,0.95f,"START: EXIT",194,209,224);
    hud_text(sw*0.53f,sh*0.53f,1.05f,
             race_select_mode_label(g_selected_race_mode), 255,226,129);
    hud_text(sw*0.53f,sh*0.56f,0.95f,"X: CHANGE MODE",194,209,224);
    if (g_selected_race_mode == RACE_SELECT_MIRROR_CUP)
        hud_text(sw*0.53f,sh*0.59f,0.78f,"BONUS CUP: REVERSE TRACKS AND HARD AI",255,190,120);

    guOrtho(projection,0.0f,sh,0.0f,sw,0.0f,1.0f);
    guMtxIdentity(identity);
    GX_LoadProjectionMtx(projection,GX_ORTHOGRAPHIC);
    GX_LoadPosMtxImm(identity,GX_PNMTX0);
    GX_SetZMode(GX_FALSE,GX_ALWAYS,GX_FALSE);
    GX_Begin(GX_TRIANGLES,GX_VTXFMT0,(u16)g_hud_count);
    {
        unsigned int i;
        for(i=0;i<g_hud_count;++i){
            const HudVertex *v=&g_hud_vertices[i];
            emit_vertex(v->x,v->y,v->z,v->r,v->g,v->b,v->a);
        }
    }
    GX_End();
    GX_SetZMode(GX_TRUE,GX_LEQUAL,GX_TRUE);
}

static void render_frame(void)
{
    Mtx view;
    Mtx44 projection;
    guVector camera;
    guVector up = {0.0f, 1.0f, 0.0f};
    guVector target;
    float back = 18.0f + 4.0f*clampf_local(g_player.speed/52.0f, 0.0f, 1.0f);
    float desired_x = g_player.x - sinf(g_player.heading)*back;
    float desired_y = g_player.y + 9.5f + 1.1f*clampf_local(g_player.speed/52.0f, 0.0f, 1.0f);
    float desired_z = g_player.z - cosf(g_player.heading)*back;
    float smooth = 0.12f + 0.05f*clampf_local(g_player.speed/52.0f, 0.0f, 1.0f);

    if (!g_camera_ready) {
        g_camera_x = desired_x;
        g_camera_y = desired_y;
        g_camera_z = desired_z;
        g_camera_ready = 1;
    } else {
        g_camera_x += (desired_x-g_camera_x)*smooth;
        g_camera_y += (desired_y-g_camera_y)*smooth;
        g_camera_z += (desired_z-g_camera_z)*smooth;
    }
    camera.x = g_camera_x;
    camera.y = g_camera_y;
    camera.z = g_camera_z;
    target.x = g_player.x + sinf(g_player.heading)*(7.0f + g_player.speed*0.08f);
    target.y = g_player.y + 1.3f;
    target.z = g_player.z + cosf(g_player.heading)*(7.0f + g_player.speed*0.08f);

    guPerspective(projection, 54.0f,
                  (float)g_video_mode->fbWidth/(float)g_video_mode->efbHeight,
                  0.5f, 700.0f);
    guLookAt(view, &camera, &up, &target);
    GX_LoadProjectionMtx(projection, GX_PERSPECTIVE);
    GX_LoadPosMtxImm(view, GX_PNMTX0);
    GX_SetZMode(GX_TRUE, GX_LEQUAL, GX_TRUE);
    draw_ground(g_player.x, g_player.z);
    draw_scene_assets();
    draw_track();
    draw_start_gate();
    draw_track_items();
    {
        unsigned int i;
        for (i = 0; g_game_mode == GAME_MODE_RACE && !g_time_trial_enabled && i < OPPONENT_COUNT; ++i) {
            draw_pod(&g_pod_mesh[i+1U], g_rivals[i].x, g_rivals[i].y-1.0f, g_rivals[i].z,
                     g_rivals[i].heading, g_rivals[i].r, g_rivals[i].g,
                     g_rivals[i].b, g_rivals[i].boost_active);
        }
    }
    {
        const RacerVehicleSpec *vehicle=selected_player_vehicle_spec();
        draw_pod(&g_pod_mesh[0], g_player.x, g_player.y-1.0f, g_player.z, g_player.heading,
                 vehicle->r, vehicle->g, vehicle->b, g_player.boost_active);
    }
    if (g_game_mode == GAME_MODE_SELECT) draw_selection_hud();
    else draw_hud();

    GX_CopyDisp(g_framebuffers[g_framebuffer_index], GX_TRUE);
    GX_DrawDone();
    VIDEO_SetNextFramebuffer(g_framebuffers[g_framebuffer_index]);
    VIDEO_Flush();
    VIDEO_WaitVSync();
    g_framebuffer_index ^= 1U;
}

static RacerInput read_input(u16 held)
{
    RacerInput input;
    s8 stick = PAD_StickX(0);
    input.steering = (float)stick / 80.0f;
    if (abs((int)stick) < 9) input.steering = 0.0f;
    if (held & PAD_BUTTON_LEFT) input.steering -= 1.0f;
    if (held & PAD_BUTTON_RIGHT) input.steering += 1.0f;
    input.steering = clampf_local(input.steering, -1.0f, 1.0f);
    input.throttle = (held & PAD_BUTTON_A) ? 1.0f : 0.0f;
    input.brake = (held & PAD_BUTTON_B) ? 1.0f : 0.0f;
    input.boost = (held & PAD_BUTTON_X) ? 1.0f : 0.0f;
    input.drift = (held & PAD_BUTTON_Y) ? 1.0f : 0.0f;
    return input;
}

int main(int argc, char **argv)
{
    (void)argc;
    (void)argv;
    { unsigned int pod_i;
      for (pod_i = 0U; pod_i < OPPONENT_COUNT + 1U; ++pod_i)
          if (pod_model_build_variant(&g_pod_mesh[pod_i], pod_i) != 0) return 2;
    }
    initialise_video_and_gx();
    career_profile_init(&g_career_profile);
    g_card_save_available = career_card_load(&g_career_profile);
    if (!load_selected_course()) return 3;

    while (1) {
        u16 held, down;
        const float dt=1.0f/60.0f;
        if (g_garage_notice_timer > 0.0f)
            g_garage_notice_timer = g_garage_notice_timer > dt ? g_garage_notice_timer - dt : 0.0f;
        PAD_ScanPads();
        held=PAD_ButtonsHeld(0);
        down=PAD_ButtonsDown(0);
        {
            PauseAction pause_action = pause_state_update(
                g_game_mode == GAME_MODE_RACE,
                (down & PAD_BUTTON_START) != 0,
                (down & PAD_BUTTON_A) != 0,
                (down & PAD_BUTTON_B) != 0,
                &g_paused);
            if (pause_action == PAUSE_ACTION_EXIT_GAME) break;
            if (pause_action == PAUSE_ACTION_RETURN_TO_SELECT) {
                g_game_mode = GAME_MODE_SELECT;
                g_camera_ready = 0;
            }
        }
        if (g_paused) {
            /* Keep rendering the world and pause overlay, but freeze all simulation. */
        } else if (g_game_mode==GAME_MODE_SELECT) {
            int track_changed=0, vehicle_changed=0;
            if ((down & PAD_TRIGGER_L) && g_selected_race_mode != RACE_SELECT_MIRROR_CUP) {
                g_ai_difficulty = g_ai_difficulty == 0U ? 2U : g_ai_difficulty - 1U;
                configure_rival_vehicles();
            }
            if ((down & PAD_TRIGGER_R) && g_selected_race_mode != RACE_SELECT_MIRROR_CUP) {
                g_ai_difficulty = (g_ai_difficulty + 1U) % 3U;
                configure_rival_vehicles();
            }
            if ((down & PAD_BUTTON_B) && g_selected_race_mode != RACE_SELECT_MIRROR_CUP) {
                g_reverse_track = !g_reverse_track;
                track_changed = 1;
            }
            if (down & PAD_BUTTON_X) {
                RaceSelectMode previous_mode = g_selected_race_mode;
                RaceSelectMode next_mode = race_select_mode_next(previous_mode);
                if (previous_mode != RACE_SELECT_MIRROR_CUP && next_mode == RACE_SELECT_MIRROR_CUP) {
                    g_pre_bonus_reverse_track = g_reverse_track;
                    g_pre_bonus_ai_difficulty = g_ai_difficulty;
                    g_bonus_settings_saved = 1;
                    g_reverse_track = 1;
                    g_ai_difficulty = 2U;
                    track_changed = 1;
                } else if (previous_mode == RACE_SELECT_MIRROR_CUP && next_mode != RACE_SELECT_MIRROR_CUP &&
                           g_bonus_settings_saved) {
                    g_reverse_track = g_pre_bonus_reverse_track;
                    g_ai_difficulty = g_pre_bonus_ai_difficulty;
                    g_bonus_settings_saved = 0;
                    track_changed = 1;
                }
                g_selected_race_mode = next_mode;
                g_championship_enabled = g_selected_race_mode == RACE_SELECT_CHAMPIONSHIP ||
                                         g_selected_race_mode == RACE_SELECT_MIRROR_CUP;
                g_time_trial_enabled = g_selected_race_mode == RACE_SELECT_TIME_TRIAL;
                if (previous_mode == RACE_SELECT_MIRROR_CUP ||
                    g_selected_race_mode == RACE_SELECT_MIRROR_CUP)
                    configure_rival_vehicles();
                if (g_championship_enabled) {
                    championship_init(&g_championship, track_catalog_count());
                    g_championship_start_track = g_selected_track;
                }
            }
            if (down & PAD_BUTTON_Y) {
                g_garage_part = (GaragePart)(((unsigned int)g_garage_part + 1U) % GARAGE_PART_COUNT);
                (void)snprintf(g_garage_notice, sizeof(g_garage_notice), "SELECTED %s", garage_part_name(g_garage_part));
                g_garage_notice_timer = 2.5f;
            }
            if (down & PAD_TRIGGER_Z) {
                if (garage_buy_upgrade(&g_career_profile, g_garage_part)) {
                    (void)snprintf(g_garage_notice, sizeof(g_garage_notice), "%s UPGRADED", garage_part_name(g_garage_part));
                    g_card_save_available = career_card_store(&g_career_profile);
                    if (pod_model_build_variant(&g_pod_mesh[0], g_selected_vehicle) != 0) return 5;
                } else {
                    unsigned int level = g_career_profile.upgrade_levels[(unsigned int)g_garage_part];
                    unsigned int cost = garage_upgrade_cost(level);
                    (void)snprintf(g_garage_notice, sizeof(g_garage_notice), cost == 0U ? "PART ALREADY MAXED" : "NOT ENOUGH CREDITS");
                }
                g_garage_notice_timer = 2.5f;
            }
            unsigned int tracks=track_catalog_count(), vehicles=vehicle_catalog_count();
            if (down & PAD_BUTTON_LEFT) {
                g_selected_vehicle=(g_selected_vehicle+vehicles-1U)%vehicles; vehicle_changed=1;
            }
            if (down & PAD_BUTTON_RIGHT) {
                g_selected_vehicle=(g_selected_vehicle+1U)%vehicles; vehicle_changed=1;
            }
            if (down & PAD_BUTTON_UP) {
                g_selected_track=(g_selected_track+tracks-1U)%tracks; track_changed=1;
            }
            if (down & PAD_BUTTON_DOWN) {
                g_selected_track=(g_selected_track+1U)%tracks; track_changed=1;
            }
            if (track_changed) {
                if (!load_selected_course()) return 4;
            } else if (vehicle_changed) {
                unsigned int pod_i;
                if (pod_model_build_variant(&g_pod_mesh[0], g_selected_vehicle) != 0) return 5;
                for (pod_i = 0U; pod_i < OPPONENT_COUNT; ++pod_i) {
                    unsigned int rival_model = (g_selected_vehicle + pod_i + 1U) % vehicle_catalog_count();
                    if (pod_model_build_variant(&g_pod_mesh[pod_i+1U], rival_model) != 0) return 5;
                }
                racer_init(&g_player,g_active_track,g_active_track_count);
                rival_ai_init(g_rivals,OPPONENT_COUNT,g_active_track,
                              g_active_track_count,g_track_length);
                configure_rival_vehicles();
                g_camera_ready=0;
            }
            if (down & PAD_BUTTON_A) {
                if (g_championship_enabled) {
                    g_championship_start_track = g_selected_track;
                    championship_init(&g_championship, track_catalog_count());
                }
                initialise_race();
            }
        } else if (g_race_flow.phase==RACE_PHASE_FINISHED) {
            if (!g_finish_recorded) {
                unsigned int i;
                unsigned int places[CHAMPIONSHIP_MAX_RACERS] = {1U, 2U, 3U, 4U, 5U, 6U, 7U, 8U};
                float progress[CHAMPIONSHIP_MAX_RACERS];
                progress[0] = race_standings_progress(g_player.lap, g_player.track_progress);
                for (i = 0U; i < OPPONENT_COUNT; ++i)
                    progress[i + 1U] = race_standings_progress(g_rivals[i].lap, g_rivals[i].progress);
                /* The HUD and finish snapshot share the same lap-aware ranking rules. */
                race_standings_rank(progress, CHAMPIONSHIP_MAX_RACERS, places);
                int championship_won = 0;
                if (g_championship_enabled) {
                    (void)championship_record_race(&g_championship, g_championship.rounds_completed, places);
                    championship_won = (g_championship.rounds_completed >= g_championship.rounds_total &&
                                        championship_winner(&g_championship) == 0U);
                }
                if (g_time_trial_enabled) {
                    (void)career_profile_record_time_trial(&g_career_profile, g_selected_track,
                                                           g_player.best_lap_time);
                } else {
                    (void)career_profile_record_race(&g_career_profile, g_selected_track,
                                                     places[0], g_player.best_lap_time,
                                                     championship_won);
                    {
                        unsigned int prize = garage_race_prize(places[0]);
                        if (g_selected_race_mode == RACE_SELECT_MIRROR_CUP && championship_won) {
                            const unsigned int bonus_prize = 5000U;
                            if (prize <= 0xffffffffU - bonus_prize) prize += bonus_prize;
                            (void)snprintf(g_garage_notice, sizeof(g_garage_notice),
                                           "MIRROR CUP CHAMPION BONUS +%u CR", bonus_prize);
                        } else {
                            (void)snprintf(g_garage_notice, sizeof(g_garage_notice),
                                           "RACE PRIZE +%u CREDITS", prize);
                        }
                        if (g_career_profile.credits <= 0xffffffffU - prize)
                            g_career_profile.credits += prize;
                        g_garage_notice_timer = 4.0f;
                    }
                }
                g_card_save_available = career_card_store(&g_career_profile);
                g_finish_recorded = 1;
            }
            if (down & PAD_BUTTON_Y) {
                if (g_championship_enabled && g_championship.rounds_completed < g_championship.rounds_total) {
                    g_selected_track = (g_championship_start_track + g_championship.rounds_completed) % track_catalog_count();
                    if (!load_selected_course()) return 5;
                    initialise_race();
                } else if (g_championship_enabled) {
                    g_game_mode = GAME_MODE_SELECT;
                    g_championship_enabled = 0;
                    g_time_trial_enabled = 0;
                    if (g_selected_race_mode == RACE_SELECT_MIRROR_CUP && g_bonus_settings_saved) {
                        g_reverse_track = g_pre_bonus_reverse_track;
                        g_ai_difficulty = g_pre_bonus_ai_difficulty;
                        g_bonus_settings_saved = 0;
                        if (!load_selected_course()) return 5;
                    }
                    g_selected_race_mode = RACE_SELECT_SINGLE;
                } else {
                    initialise_race();
                }
            }
        } else if (g_race_flow.phase==RACE_PHASE_COUNTDOWN) {
            /* Ignore throttle and drift during lights; race timer begins at GO. */
            race_flow_update(&g_race_flow,dt,g_player.lap);
        } else if (g_race_flow.phase==RACE_PHASE_RUNNING) {
            RacerInput input=read_input(held);
            RaceItemType item_type;
            {
                const RacerTrackInfo *surface = track_catalog_get(g_selected_track);
                racer_update_vehicle_surface_width(&g_player,g_active_track,g_active_track_count,&input,
                                                   vehicle_catalog_get(g_selected_vehicle),
                                                   surface->surface_grip, surface->rolling_resistance,
                                                   surface->width, dt);
            }
            race_feedback_update(&g_race_feedback,&g_player,g_active_track,
                                 g_active_track_count,dt);
            item_type=race_items_update(g_race_items,RACE_ITEM_COUNT,&g_player,
                                        g_active_track,g_active_track_count,
                                        selected_player_vehicle_spec());
            if(item_type!=RACE_ITEM_NONE){g_last_item=item_type;g_item_flash_timer=1.1f;}
            if(g_item_flash_timer>0.0f)
                g_item_flash_timer=(g_item_flash_timer>dt)?g_item_flash_timer-dt:0.0f;
            if(g_collision_flash_timer>0.0f)
                g_collision_flash_timer=(g_collision_flash_timer>dt)?g_collision_flash_timer-dt:0.0f;
            update_rivals(dt);
            g_drafting_active = g_time_trial_enabled ? 0 :
                draft_assist_update(&g_player, g_rivals, OPPONENT_COUNT, dt);
            race_flow_update(&g_race_flow,dt,g_player.lap);
        }
        /* Pause must freeze cue transitions and subtitle expiry as well as physics.
         * The runtime is also inactive on the course-selection screen. */
        voice_over_runtime_set_paused(&g_voice_over_runtime,
                                      g_paused || g_game_mode != GAME_MODE_RACE);
        voice_over_runtime_update(&g_voice_over_runtime, (int)g_race_flow.phase,
                                  g_player.lap, g_race_flow.target_laps,
                                  g_player.damage, g_player.boost_energy, dt);
        render_frame();
    }
    return 0;
}
