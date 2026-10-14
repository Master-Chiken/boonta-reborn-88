#ifndef SWE1R_TRACK_CATALOG_H
#define SWE1R_TRACK_CATALOG_H

#include "racer_physics.h"

#ifdef __cplusplus
extern "C" {
#endif

/* The catalog covers the 25 named SWE1R race routes. Runtime builds can use
 * supplied PC spline-derived centerlines; meshes and collision remain generated. */
#define TRACK_CATALOG_COUNT 25U
#define TRACK_POINT_CAPACITY 256U
#define TRACK_VERTEX_CAPACITY (TRACK_POINT_CAPACITY * 18U)

typedef struct {
    float x, y, z;
    unsigned char r, g, b;
} TrackVertex;

typedef enum {
    TRACK_BIOME_SANDSTONE = 0,
    TRACK_BIOME_ICE = 1,
    TRACK_BIOME_JUNGLE = 2,
    TRACK_BIOME_COASTAL = 3,
    TRACK_BIOME_VOLCANIC = 4,
    TRACK_BIOME_REFINERY = 5,
    TRACK_BIOME_SKYPORT = 6,
    TRACK_BIOME_ASTEROID_FACILITY = 7
} TrackBiome;

typedef enum {
    TRACK_LAYOUT_CANYON = 0,
    TRACK_LAYOUT_ROUNDED_RECT = 1,
    TRACK_LAYOUT_CHICANE = 2,
    TRACK_LAYOUT_SWITCHBACK = 3,
    TRACK_LAYOUT_ASYMMETRIC = 4,
    TRACK_LAYOUT_LONG_OVAL = 5,
    TRACK_LAYOUT_HAIRPIN = 6,
    TRACK_LAYOUT_SERPENTINE = 7
} TrackLayoutStyle;

typedef struct {
    const char *name;
    const char *description;
    const char *planet;
    float width;
    unsigned char ground_r, ground_g, ground_b;
    unsigned char rock_r, rock_g, rock_b;
    float difficulty;
    float surface_grip;       /* 0.65..1.15: lower means more slippery */
    float rolling_resistance; /* extra drag from sand, water, rubble, etc. */
} RacerTrackInfo;

const RacerTrackInfo *track_catalog_get(unsigned int index);
unsigned int track_catalog_count(void);
TrackLayoutStyle track_catalog_layout_style(unsigned int index);
TrackBiome track_catalog_biome(unsigned int index);
int track_catalog_build_points(unsigned int index, RacerTrackPoint *out,
                               unsigned int capacity, unsigned int *out_count);
int track_catalog_build_mesh(unsigned int index, const RacerTrackPoint *points,
                             unsigned int count, TrackVertex *out,
                             unsigned int capacity, unsigned int *out_count);

#ifdef __cplusplus
}
#endif
#endif
