#ifndef BOONTA_REBORN_TRACK_SAMPLING_H
#define BOONTA_REBORN_TRACK_SAMPLING_H

#include <math.h>
#include <stddef.h>

#include "generated_track.h"

/*
 * Host-testable implementation of the native renderer's closed-loop sampler.
 * Keep the chord-distance lookup and Catmull-Rom interpolation in one place so
 * tests exercise the exact C code used by GameCube/Wii rather than a Python port.
 */
typedef struct {
    float segment_lengths[BOONTA_TRACK_POINT_COUNT];
    float total_length;
    int lengths_ready;
} BoontaTrackSampler;

static inline float boonta_track_sample_clamp(float value, float low, float high)
{
    if (!isfinite(value)) return 0.0f;
    if (value < low) return low;
    if (value > high) return high;
    return value;
}

static inline float boonta_track_catmull_rom_component(
    float p0, float p1, float p2, float p3, float t)
{
    const float t2 = t * t;
    const float t3 = t2 * t;
    return 0.5f * (
        2.0f * p1 + (-p0 + p2) * t
        + (2.0f * p0 - 5.0f * p1 + 4.0f * p2 - p3) * t2
        + (-p0 + 3.0f * p1 - 3.0f * p2 + p3) * t3
    );
}

static inline void boonta_track_sampler_sample_at(
    BoontaTrackSampler *sampler, float travelled, float fallback_half_width,
    float *x_out, float *y_out, float *z_out, float *width_out)
{
    unsigned int i;

    if (x_out != NULL) *x_out = 0.0f;
    if (y_out != NULL) *y_out = 0.0f;
    if (z_out != NULL) *z_out = 0.0f;
    if (width_out != NULL) *width_out = fallback_half_width;
    if (sampler == NULL) return;

    /* Segment lengths are cached because many road vertices sample each frame. */
    if (!sampler->lengths_ready) {
        sampler->total_length = 0.0f;
        for (i = 0U; i < BOONTA_TRACK_POINT_COUNT; ++i) {
            const unsigned int next = (i + 1U) % BOONTA_TRACK_POINT_COUNT;
            const float dx = boonta_track_points_original_test_oval[next].x -
                             boonta_track_points_original_test_oval[i].x;
            const float dy = boonta_track_points_original_test_oval[next].y -
                             boonta_track_points_original_test_oval[i].y;
            const float dz = boonta_track_points_original_test_oval[next].z -
                             boonta_track_points_original_test_oval[i].z;
            sampler->segment_lengths[i] = sqrtf(dx * dx + dy * dy + dz * dz);
            sampler->total_length += sampler->segment_lengths[i];
        }
        sampler->lengths_ready = 1;
    }

    if (!isfinite(travelled) || sampler->total_length <= 0.001f) return;
    {
        float target = fmodf(travelled, sampler->total_length);
        if (target < 0.0f) target += sampler->total_length;

        for (i = 0U; i < BOONTA_TRACK_POINT_COUNT; ++i) {
            const unsigned int next = (i + 1U) % BOONTA_TRACK_POINT_COUNT;
            const float length = sampler->segment_lengths[i];
            if (target <= length || i + 1U == BOONTA_TRACK_POINT_COUNT) {
                const unsigned int previous =
                    (i + BOONTA_TRACK_POINT_COUNT - 1U) % BOONTA_TRACK_POINT_COUNT;
                const unsigned int following = (next + 1U) % BOONTA_TRACK_POINT_COUNT;
                const float t = length > 0.001f
                    ? boonta_track_sample_clamp(target / length, 0.0f, 1.0f) : 0.0f;
                const BoontaTrackPoint *p0 = &boonta_track_points_original_test_oval[previous];
                const BoontaTrackPoint *p1 = &boonta_track_points_original_test_oval[i];
                const BoontaTrackPoint *p2 = &boonta_track_points_original_test_oval[next];
                const BoontaTrackPoint *p3 = &boonta_track_points_original_test_oval[following];
                const float smooth_x = boonta_track_catmull_rom_component(
                    p0->x, p1->x, p2->x, p3->x, t);
                const float smooth_y = boonta_track_catmull_rom_component(
                    p0->y, p1->y, p2->y, p3->y, t);
                const float smooth_z = boonta_track_catmull_rom_component(
                    p0->z, p1->z, p2->z, p3->z, t);
                const float smooth_width = boonta_track_catmull_rom_component(
                    p0->half_width, p1->half_width, p2->half_width, p3->half_width, t);

                if (x_out != NULL) *x_out = smooth_x;
                if (y_out != NULL) *y_out = boonta_track_sample_clamp(smooth_y, -3.0f, 3.0f);
                if (z_out != NULL) *z_out = smooth_z;
                if (width_out != NULL) {
                    *width_out = boonta_track_sample_clamp(smooth_width, 2.2f, 4.8f);
                }
                return;
            }
            target -= length;
        }
    }
}

#endif
