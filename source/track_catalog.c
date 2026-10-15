/* 25 named SWE1R courses. With SWE1R_USE_IMPORTED_CENTERLINE enabled, all
 * course centerlines are sourced from the supplied modded PC spline block; the
 * road ribbons, collision response and materials are still generated here. */
#include "track_catalog.h"
#include "track_bank.h"
#ifdef SWE1R_USE_IMPORTED_CENTERLINE
#include "track_centerlines_pc.generated.h"
#else
#include "track_centerline.generated.h"
#endif
#include <math.h>
#include <string.h>

#define PI_TRACK 3.14159265358979323846f
#define NEW_TRACK_SAMPLES 120U

static const RacerTrackInfo g_tracks[TRACK_CATALOG_COUNT] = {
    {"BOONTA CLASSIC", "TATOOINE DESERT / FAST SWEEPERS", "TATOOINE", 12.5f,174,124,67,163,91,52,1.0f, 0.885f, 1.000f},
    {"GRABVINE GATEWAY", "JUNGLE GORGE / SPLIT PATHS", "BAROONDA", 11.0f,77,133,83,55,91,58,1.35f, 0.965f, 0.600f},
    {"BAROO COAST", "COASTAL SWEEPERS / ROLLING TERRAIN", "BAROONDA", 12.4f,78,151,132,47,99,84,1.1f, 0.915f, 0.700f},
    {"FIRE MOUNTAIN RALLY", "VOLCANIC ASCENTS / BLIND CORNERS", "BAROONDA", 11.5f,163,94,67,120,60,42,1.35f, 0.880f, 1.400f},
    {"INFERNO", "HOT ROCK / HAZARD-HEAVY LINE", "BAROONDA", 10.8f,174,91,60,128,65,44,1.5f, 0.840f, 1.600f},
    {"MON GAZZA SPEEDWAY", "INDUSTRIAL OVAL / LONG STRAIGHTS", "MON GAZZA", 13.0f,135,118,91,86,74,61,1.05f, 0.955f, 0.500f},
    {"SPICE MINE RUN", "INDUSTRIAL TUNNELS / BLIND EXITS", "MON GAZZA", 10.9f,112,91,77,74,61,53,1.45f, 1.005f, 0.400f},
    {"ZUGGA CHALLENGE", "RIDGE CRESTS / QUICK DIRECTION CHANGES", "MON GAZZA", 11.2f,114,105,91,74,67,57,1.45f, 0.950f, 0.650f},
    {"VENGEANCE", "OOVO IV FACILITY / TECHNICAL SWEEPS", "OOVO IV", 10.5f,112,108,119,75,73,83,1.5f, 0.835f, 1.600f},
    {"EXECUTIONER", "INDUSTRIAL HAZARDS / HIGH SPEED", "OOVO IV", 11.3f,129,123,136,88,81,96,1.45f, 0.785f, 1.300f},
    {"THE GAUNTLET", "ASTEROID FACILITY / TIGHT TECHNICAL LINE", "OOVO IV", 10.5f,105,99,116,69,64,80,1.5f, 0.820f, 1.700f},
    {"ANDO PRIME CENTRUM", "FROZEN PLATEAUS / BROAD HIGH-SPEED TURNS", "ANDO PRIME", 11.4f,95,129,145,61,83,111,1.3f, 0.805f, 1.500f},
    {"BEEDO'S WILD RIDE", "ICEFIELD STRAIGHTS / LATE BRAKING", "ANDO PRIME", 12.1f,131,166,188,90,123,148,1.25f, 0.755f, 1.600f},
    {"HOWLER GORGE", "MOUNTAIN GORGE / ELEVATION CHANGES", "ANDO PRIME", 11.2f,106,145,164,69,100,120,1.45f, 0.780f, 1.700f},
    {"ANDOBI MOUNTAIN RUN", "MOUNTAIN SWITCHBACKS / HIGH SPEED", "ANDO PRIME", 11.4f,95,129,145,61,83,111,1.3f, 0.805f, 1.500f},
    {"MALASTARE 100", "DUG TERRAIN / FAST BANKED BENDS", "MALASTARE", 12.0f,135,105,71,98,69,51,1.2f, 0.865f, 1.300f},
    {"DUG DERBY", "SHORT STRAIGHTS / HEAVY CORNERING", "MALASTARE", 11.1f,145,113,79,91,66,49,1.4f, 0.840f, 1.100f},
    {"SEBULBA'S LEGACY", "ROUGH ROCK / HIGH-RISK CORNERS", "MALASTARE", 10.5f,126,91,67,85,58,43,1.5f, 0.815f, 1.400f},
    {"AQUILARIS CLASSIC", "WATERFRONT SPEEDWAY / WIDE TURNS", "AQUILARIS", 12.7f,74,151,178,47,103,126,1.0f, 0.785f, 1.900f},
    {"SUNKEN CITY", "SUBMERGED RUINS / TECHNICAL LINE", "AQUILARIS", 11.0f,62,126,157,39,83,113,1.4f, 0.735f, 1.600f},
    {"BUMPY'S BREAKERS", "WAVE-LIKE CRESTS / LATE BRAKING", "AQUILARIS", 11.5f,82,169,191,45,110,135,1.3f, 0.760f, 1.700f},
    {"SCRAPPER'S RUN", "WRECKAGE CORRIDORS / TIGHT TURNS", "ORD IBANNA", 10.8f,174,155,115,121,102,75,1.35f, 0.945f, 0.700f},
    {"DETHRO'S REVENGE", "HIGH PLATEAUS / OPEN CORNERS", "ORD IBANNA", 12.0f,160,139,103,111,91,66,1.25f, 0.895f, 0.500f},
    {"ABYSS", "DEEP DESCENTS / TECHNICAL LINES", "ORD IBANNA", 10.8f,131,119,100,92,78,64,1.45f, 0.875f, 0.700f},
    {"BOONTA TRAINING COURSE", "TATOOINE TRAINING LOOP / LEARNING LINE", "TATOOINE", 9.8f,190,145,95,140,105,70,0.75f, 0.920f, 0.800f}
};

const RacerTrackInfo *track_catalog_get(unsigned int index)
{ return index < TRACK_CATALOG_COUNT ? &g_tracks[index] : &g_tracks[0]; }
unsigned int track_catalog_count(void) { return TRACK_CATALOG_COUNT; }

TrackLayoutStyle track_catalog_layout_style(unsigned int index)
{
    if (index >= TRACK_CATALOG_COUNT) index = 0U;
    return (TrackLayoutStyle)(index % 8U);
}

/* Select scenery from named metadata rather than fragile catalogue index ranges.
 * Baroo Coast is a coastal sub-environment on Baroonda; the other Baroonda
 * routes use the jungle set. This is for the prototype's procedural props. */
TrackBiome track_catalog_biome(unsigned int index)
{
    const RacerTrackInfo *info = track_catalog_get(index);
    if (strcmp(info->planet, "TATOOINE") == 0) return TRACK_BIOME_SANDSTONE;
    if (strcmp(info->planet, "ANDO PRIME") == 0) return TRACK_BIOME_ICE;
    if (strcmp(info->planet, "BAROONDA") == 0) {
        return strcmp(info->name, "BAROO COAST") == 0
            ? TRACK_BIOME_COASTAL : TRACK_BIOME_JUNGLE;
    }
    if (strcmp(info->planet, "AQUILARIS") == 0) return TRACK_BIOME_COASTAL;
    if (strcmp(info->planet, "MALASTARE") == 0) return TRACK_BIOME_VOLCANIC;
    if (strcmp(info->planet, "MON GAZZA") == 0) return TRACK_BIOME_REFINERY;
    if (strcmp(info->planet, "ORD IBANNA") == 0) return TRACK_BIOME_SKYPORT;
    if (strcmp(info->planet, "OOVO IV") == 0) return TRACK_BIOME_ASTEROID_FACILITY;
    return TRACK_BIOME_SANDSTONE;
}

static float signf_track(float x) { return x < 0.0f ? -1.0f : 1.0f; }

int track_catalog_build_points(unsigned int index, RacerTrackPoint *out,
                               unsigned int capacity, unsigned int *out_count)
{
    unsigned int i, count;
    if (out == 0 || out_count == 0) return 0;
    if (index >= TRACK_CATALOG_COUNT) index = 0U;
#ifdef SWE1R_USE_IMPORTED_CENTERLINE
    {
        const RacerImportedTrackRoute *imported = track_pc_imported_find(index);
        if (imported != 0) {
            count = imported->point_count;
            if (count > capacity) return 0;
            memcpy(out, imported->points, (size_t)count * sizeof(*out));
            *out_count = count;
            return 1;
        }
    }
#else
    if (index == 0U) {
        count = TRACK_CENTERLINE_COUNT;
        if (count > capacity) return 0;
        for (i=0; i<count; ++i) {
            out[i] = g_track_centerline[i];
            /* Existing procedural baseline is authored at 1/1.45 runtime scale. */
            out[i].x *= 1.45f;
            out[i].z *= 1.45f;
        }
        *out_count = count;
        return 1;
    }
#endif
    count = NEW_TRACK_SAMPLES;
    if (capacity < count) return 0;
    for (i=0; i<count; ++i) {
        float t=(2.0f*PI_TRACK*(float)i)/(float)count;
        float sn=sinf(t), cs=cosf(t), x=0.0f, z=0.0f, y;
        unsigned int variant=index;
        unsigned int style=(unsigned int)track_catalog_layout_style(index);
        float a=34.0f+(float)((variant*7U)%17U);
        float b=24.0f+(float)((variant*11U)%13U);
        float phase=0.23f*(float)variant;
        float h1=2.0f+(float)(variant%4U)*0.45f;
        float h2=3.0f+(float)(variant%5U)*0.31f;

        /* Five route families create recognisably different driving rhythms:
         * canyon sweeps, rounded-rectangle speedways, offset chicanes,
         * switchback loops and asymmetric technical courses. */
        if (style == TRACK_LAYOUT_CANYON) {
            float radius=1.0f + 0.10f*sinf(2.0f*t+phase)
                               + 0.055f*cosf(5.0f*t-phase);
            x=a*radius*cs;
            z=b*(0.78f+0.06f*sinf(3.0f*t+phase))*sn;
        } else if (style == TRACK_LAYOUT_ROUNDED_RECT) {
            float exponent=0.62f+(float)(variant%4U)*0.075f;
            x=a*signf_track(cs)*powf(fabsf(cs),exponent);
            z=b*signf_track(sn)*powf(fabsf(sn),exponent);
            x += 2.0f*sinf(2.0f*t+phase);
        } else if (style == TRACK_LAYOUT_CHICANE) {
            x=a*(cs+0.20f*sinf(2.0f*t+phase)+0.055f*sinf(4.0f*t-phase));
            z=b*(sn+0.16f*sinf(3.0f*t+phase));
        } else if (style == TRACK_LAYOUT_SWITCHBACK) {
            x=a*(0.82f*cs+0.22f*cosf(3.0f*t+phase));
            z=b*(sn+0.22f*sinf(2.0f*t+phase)+0.08f*sinf(4.0f*t-phase));
        } else if (style == TRACK_LAYOUT_ASYMMETRIC) {
            float radius=a+h1*sinf(2.0f*t+phase)+h2*0.72f*cosf(3.0f*t-phase)
                           + 1.7f*sinf(5.0f*t+phase*1.7f);
            x=radius*cs + 3.0f*sinf(2.0f*t+phase);
            z=radius*(0.62f+(float)(variant%5U)*0.055f)*sn
              + 5.0f*sinf(2.0f*t+phase);
        } else if (style == TRACK_LAYOUT_LONG_OVAL) {
            /* Long straights and broad ends: a speed-focused oval with a mild kink. */
            float exponent=0.38f+(float)(variant%3U)*0.045f;
            x=(a*1.22f)*signf_track(cs)*powf(fabsf(cs),exponent);
            z=(b*0.76f)*signf_track(sn)*powf(fabsf(sn),0.78f);
            z += 2.8f*sinf(2.0f*t+phase);
        } else if (style == TRACK_LAYOUT_HAIRPIN) {
            /* Two offset ends create tighter return turns without a sharp seam. */
            x=a*(0.86f*cs+0.28f*cosf(2.0f*t+phase));
            z=b*(sn+0.24f*sinf(2.0f*t+phase)-0.07f*sinf(3.0f*t-phase));
            x += 2.2f*sinf(3.0f*t+phase);
        } else {
            /* Repeated S-bends with an offset centerline for a slalom rhythm. */
            x=a*(0.88f*cs+0.24f*sinf(3.0f*t+phase)+0.07f*sinf(5.0f*t-phase));
            z=b*(0.86f*sn+0.19f*sinf(2.0f*t+phase)+0.08f*sinf(4.0f*t-phase));
        }
        /* Elevation changes remain smooth across the lap seam. */
        y=1.0f+((float)(variant%4U)+1.0f)*0.35f*sinf((2.0f+(float)(variant%3U))*t+phase)
          +0.55f*sinf((5.0f+(float)(variant%4U))*t+0.15f*variant);
        out[i].x=x*1.45f; out[i].y=y; out[i].z=z*1.45f;
    }
    *out_count=count;
    return 1;
}

static void emit_vertex(TrackVertex *out,unsigned int *used,float x,float y,float z,
                        unsigned char r,unsigned char g,unsigned char b)
{ TrackVertex *v=&out[(*used)++]; v->x=x; v->y=y; v->z=z; v->r=r; v->g=g; v->b=b; }
static void emit_triangle(TrackVertex *out,unsigned int *used,const float a[3],const float b[3],const float c[3],
                          unsigned char r,unsigned char g,unsigned char blue)
{ emit_vertex(out,used,a[0],a[1],a[2],r,g,blue); emit_vertex(out,used,b[0],b[1],b[2],r,g,blue); emit_vertex(out,used,c[0],c[1],c[2],r,g,blue); }
static void emit_quad(TrackVertex *out,unsigned int *used,const float a[3],const float b[3],const float c[3],const float d[3],
                      unsigned char r,unsigned char g,unsigned char blue)
{ emit_triangle(out,used,a,b,c,r,g,blue); emit_triangle(out,used,b,d,c,r,g,blue); }

int track_catalog_build_mesh(unsigned int index,const RacerTrackPoint *points,unsigned int count,
                             TrackVertex *out,unsigned int capacity,unsigned int *out_count)
{
    const RacerTrackInfo *info; unsigned int i,used=0U; float half,outer;
    if(index>=TRACK_CATALOG_COUNT)index=0U;
    if(!points||!out||!out_count||count<3U)return 0;
    if(count*18U>capacity)return 0;
    info=&g_tracks[index]; half=info->width*0.5f; outer=half+0.9f;
    for(i=0;i<count;++i){
        unsigned int j=(i+1U)%count,prev=(i+count-1U)%count,next=(i+1U)%count;
        float tx=points[next].x-points[prev].x,tz=points[next].z-points[prev].z;
        float tlen=sqrtf(tx*tx+tz*tz);
        float tx2=points[(j+1U)%count].x-points[(j+count-1U)%count].x;
        float tz2=points[(j+1U)%count].z-points[(j+count-1U)%count].z;
        float tlen2=sqrtf(tx2*tx2+tz2*tz2),nx,nz,nx2,nz2;
        float l0[3],r0[3],l1[3],r1[3],lo0[3],ro0[3],lo1[3],ro1[3];
        float bank0, bank1;
        unsigned char cr,cg,cb;
        if(tlen<1.0e-4f||tlen2<1.0e-4f)return 0;
        nx=tz/tlen;nz=-tx/tlen;nx2=tz2/tlen2;nz2=-tx2/tlen2;
        bank0=racer_track_bank_height(points,count,i,info->width);
        bank1=racer_track_bank_height(points,count,j,info->width);
        /* The outer edge rises in the turn direction; road shoulders follow
           the same bank, extended gently to avoid a visible height seam. */
        l0[0]=points[i].x+nx*half;l0[1]=points[i].y+0.15f+bank0;l0[2]=points[i].z+nz*half;
        r0[0]=points[i].x-nx*half;r0[1]=points[i].y+0.15f-bank0;r0[2]=points[i].z-nz*half;
        l1[0]=points[j].x+nx2*half;l1[1]=points[j].y+0.15f+bank1;l1[2]=points[j].z+nz2*half;
        r1[0]=points[j].x-nx2*half;r1[1]=points[j].y+0.15f-bank1;r1[2]=points[j].z-nz2*half;
        lo0[0]=points[i].x+nx*outer;lo0[1]=points[i].y+0.18f+bank0*1.12f;lo0[2]=points[i].z+nz*outer;
        ro0[0]=points[i].x-nx*outer;ro0[1]=points[i].y+0.18f-bank0*1.12f;ro0[2]=points[i].z-nz*outer;
        lo1[0]=points[j].x+nx2*outer;lo1[1]=points[j].y+0.18f+bank1*1.12f;lo1[2]=points[j].z+nz2*outer;
        ro1[0]=points[j].x-nx2*outer;ro1[1]=points[j].y+0.18f-bank1*1.12f;ro1[2]=points[j].z-nz2*outer;
        emit_quad(out,&used,l0,r0,l1,r1,71,74,78);
        if((i/3U)%2U==0U){cr=info->rock_r;cg=info->rock_g;cb=info->rock_b;}
        else{cr=219U;cg=215U;cb=193U;}
        emit_quad(out,&used,l0,lo0,l1,lo1,cr,cg,cb);emit_quad(out,&used,r0,ro0,r1,ro1,cr,cg,cb);
    }
    *out_count=used;return 1;
}
