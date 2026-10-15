#include "race_gate_geometry.h"

int race_gate_geometry_build(float road_width, RaceGateGeometry *out)
{
    unsigned int i;
    float half_width, spacing;
    if (out == 0) return 0;

    /* Reject NaN and infinities without relying on non-C99 isfinite macros. */
    if (!(road_width == road_width) || road_width > 1000.0f || road_width < -1000.0f ||
        road_width < 1.0f) {
        road_width = 12.0f;
    }
    if (road_width < 8.0f) road_width = 8.0f;
    if (road_width > 20.0f) road_width = 20.0f;

    half_width = road_width * 0.5f;
    spacing = road_width / (float)RACE_GATE_STRIPE_COUNT;
    out->road_width = road_width;
    out->post_offset = half_width + 0.35f;
    out->crossbar_half_width = half_width + 0.65f;
    out->stripe_half_width = spacing * 0.48f;
    for (i = 0U; i < RACE_GATE_STRIPE_COUNT; ++i) {
        out->stripe_centers[i] = -half_width + ((float)i + 0.5f) * spacing;
    }
    return 1;
}
