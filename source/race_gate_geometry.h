#ifndef SWE1R_RACE_GATE_GEOMETRY_H
#define SWE1R_RACE_GATE_GEOMETRY_H

#ifdef __cplusplus
extern "C" {
#endif

#define RACE_GATE_STRIPE_COUNT 8U

typedef struct {
    float road_width;
    float post_offset;
    float crossbar_half_width;
    float stripe_half_width;
    float stripe_centers[RACE_GATE_STRIPE_COUNT];
} RaceGateGeometry;

/* Build start/finish visuals from the selected course's road width.
   Invalid widths fall back to the prototype's 12-unit default. */
int race_gate_geometry_build(float road_width, RaceGateGeometry *out);

#ifdef __cplusplus
}
#endif
#endif
