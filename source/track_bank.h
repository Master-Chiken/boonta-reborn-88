#ifndef SWE1R_TRACK_BANK_H
#define SWE1R_TRACK_BANK_H

/* Shared low-cost road-banking estimate used by rendering and pod height.
 * Positive lift raises the +normal side (the side used by positive lateral
 * offsets). The curvature estimate is bounded for tiny/degenerate segments
 * and uses only data already available to the GameCube runtime. */
#include "racer_physics.h"
#include <math.h>

static inline float racer_track_bank_height(const RacerTrackPoint *track,
                                            unsigned int count,
                                            unsigned int point_index,
                                            float road_width)
{
    unsigned int prev_index, next_index;
    float in_x, in_z, out_x, out_z;
    float in_len, out_len, avg_len, cross, dot, angle;
    float half_width, bank;

    if (track == 0 || count < 3U || point_index >= count || road_width <= 0.0f)
        return 0.0f;

    prev_index = (point_index + count - 1U) % count;
    next_index = (point_index + 1U) % count;
    in_x = track[point_index].x - track[prev_index].x;
    in_z = track[point_index].z - track[prev_index].z;
    out_x = track[next_index].x - track[point_index].x;
    out_z = track[next_index].z - track[point_index].z;
    in_len = sqrtf(in_x * in_x + in_z * in_z);
    out_len = sqrtf(out_x * out_x + out_z * out_z);
    if (in_len < 1.0e-4f || out_len < 1.0e-4f) return 0.0f;

    cross = in_x * out_z - in_z * out_x;
    dot = in_x * out_x + in_z * out_z;
    angle = atan2f(cross, dot);
    avg_len = 0.5f * (in_len + out_len);
    half_width = 0.5f * road_width;

    /* Curvature * width^2 produces a stronger bank on tighter corners.
       Cap the edge rise so malformed or nearly reversing points stay safe. */
    bank = (angle / avg_len) * half_width * half_width * 0.22f;
    if (bank < -0.70f) bank = -0.70f;
    if (bank >  0.70f) bank =  0.70f;
    return bank;
}

#endif
