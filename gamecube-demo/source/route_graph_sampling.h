#ifndef BOONTA_REBORN_ROUTE_GRAPH_SAMPLING_H
#define BOONTA_REBORN_ROUTE_GRAPH_SAMPLING_H

#include <math.h>
#include <stddef.h>

#include "generated_route_graph.h"

/*
 * Native sampler for the clean-room route-graph curve representation.
 * Arc-distance tables are built once, on first use, and then reused by GX
 * scene construction. The same functions are compiled by host regression tests.
 */
typedef struct {
    float distance_lut[BOONTA_RUNTIME_ROUTE_EDGE_COUNT]
                      [BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS + 1U];
    float edge_lengths[BOONTA_RUNTIME_ROUTE_EDGE_COUNT];
    float total_length;
    int lengths_ready;
} BoontaRouteGraphSampler;

static inline float boonta_route_graph_catmull_component(
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

static inline void boonta_route_graph_evaluate_edge(
    unsigned int edge_index, float t, float *x, float *y, float *z)
{
    const BoontaRuntimeRouteEdge *edge;
    const float u = 1.0f - t;
    const float b0 = u * u * u;
    const float b1 = 3.0f * u * u * t;
    const float b2 = 3.0f * u * t * t;
    const float b3 = t * t * t;

    if (edge_index >= BOONTA_RUNTIME_ROUTE_EDGE_COUNT) return;
    edge = &boonta_runtime_route_edges[edge_index];
    if (x != NULL) {
        *x = b0 * edge->p0[0] + b1 * edge->control1[0]
           + b2 * edge->control2[0] + b3 * edge->p3[0];
    }
    if (y != NULL) {
        *y = b0 * edge->p0[1] + b1 * edge->control1[1]
           + b2 * edge->control2[1] + b3 * edge->p3[1];
    }
    if (z != NULL) {
        *z = b0 * edge->p0[2] + b1 * edge->control1[2]
           + b2 * edge->control2[2] + b3 * edge->p3[2];
    }
}

static inline int boonta_route_graph_sampler_prepare(
    BoontaRouteGraphSampler *sampler)
{
    unsigned int edge_index;
    float raw_total = 0.0f;
    float scaled_prefix = 0.0f;

    if (sampler == NULL) return 0;
    if (sampler->lengths_ready) return 1;

    for (edge_index = 0U;
         edge_index < BOONTA_RUNTIME_ROUTE_EDGE_COUNT;
         ++edge_index) {
        unsigned int step;
        float previous_x = 0.0f, previous_y = 0.0f, previous_z = 0.0f;
        float cumulative = 0.0f;

        boonta_route_graph_evaluate_edge(
            edge_index, 0.0f, &previous_x, &previous_y, &previous_z);
        sampler->distance_lut[edge_index][0] = 0.0f;

        for (step = 1U;
             step <= BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS;
             ++step) {
            const float t = (float)step /
                (float)BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS;
            float x = 0.0f, y = 0.0f, z = 0.0f;
            float dx, dy, dz, interval;

            boonta_route_graph_evaluate_edge(edge_index, t, &x, &y, &z);
            dx = x - previous_x;
            dy = y - previous_y;
            dz = z - previous_z;
            interval = sqrtf(dx * dx + dy * dy + dz * dz);
            if (!isfinite(interval)) return 0;
            cumulative += interval;
            if (!isfinite(cumulative)) return 0;
            sampler->distance_lut[edge_index][step] = cumulative;
            previous_x = x;
            previous_y = y;
            previous_z = z;
        }

        if (cumulative <= 0.001f) return 0;
        raw_total += cumulative;
        if (!isfinite(raw_total)) return 0;
    }

    if (raw_total <= 0.001f || !isfinite(BOONTA_RUNTIME_ROUTE_LENGTH) ||
        BOONTA_RUNTIME_ROUTE_LENGTH <= 0.001f) {
        return 0;
    }

    /*
     * One common scale aligns the LUT period with the generated lap constant.
     * Correct only the final edge for accumulated float rounding so the last
     * endpoint and modulo seam share exactly the same distance coordinate.
     */
    for (edge_index = 0U;
         edge_index < BOONTA_RUNTIME_ROUTE_EDGE_COUNT;
         ++edge_index) {
        unsigned int step;
        const unsigned int last_edge =
            (edge_index + 1U == BOONTA_RUNTIME_ROUTE_EDGE_COUNT);
        const float raw_edge_length =
            sampler->distance_lut[edge_index][BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS];
        const float scale = last_edge
            ? (BOONTA_RUNTIME_ROUTE_LENGTH - scaled_prefix) / raw_edge_length
            : BOONTA_RUNTIME_ROUTE_LENGTH / raw_total;

        if (!isfinite(scale) || scale <= 0.0f) return 0;
        for (step = 0U;
             step <= BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS;
             ++step) {
            sampler->distance_lut[edge_index][step] *= scale;
        }
        if (last_edge) {
            sampler->distance_lut[edge_index][BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS] =
                BOONTA_RUNTIME_ROUTE_LENGTH - scaled_prefix;
        }
        sampler->edge_lengths[edge_index] =
            sampler->distance_lut[edge_index][BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS];
        scaled_prefix += sampler->edge_lengths[edge_index];
    }

    sampler->total_length = BOONTA_RUNTIME_ROUTE_LENGTH;
    sampler->lengths_ready = 1;
    return 1;
}

static inline float boonta_route_graph_width_at(
    unsigned int edge_index, float t, float fallback_half_width)
{
    const unsigned int sample_count = BOONTA_RUNTIME_ROUTE_WIDTH_SAMPLE_COUNT;
    const float coordinate =
        (float)(edge_index * BOONTA_RUNTIME_ROUTE_WIDTH_SAMPLES_PER_EDGE)
        + t * (float)BOONTA_RUNTIME_ROUTE_WIDTH_SAMPLES_PER_EDGE;
    const unsigned int base = (unsigned int)floorf(coordinate);
    const float fraction = coordinate - (float)base;
    const unsigned int i1 = base % sample_count;
    const unsigned int i0 = (i1 + sample_count - 1U) % sample_count;
    const unsigned int i2 = (i1 + 1U) % sample_count;
    const unsigned int i3 = (i1 + 2U) % sample_count;
    const float width = boonta_route_graph_catmull_component(
        boonta_runtime_route_width_samples[i0],
        boonta_runtime_route_width_samples[i1],
        boonta_runtime_route_width_samples[i2],
        boonta_runtime_route_width_samples[i3],
        fraction);

    if (!isfinite(width)) return fallback_half_width;
    if (width < 2.2f) return 2.2f;
    if (width > 4.8f) return 4.8f;
    return width;
}

static inline void boonta_route_graph_sampler_sample_at(
    BoontaRouteGraphSampler *sampler, float travelled,
    float fallback_half_width,
    float *x_out, float *y_out, float *z_out, float *width_out)
{
    unsigned int edge_index;
    float target;

    if (x_out != NULL) *x_out = 0.0f;
    if (y_out != NULL) *y_out = 0.0f;
    if (z_out != NULL) *z_out = 0.0f;
    if (width_out != NULL) *width_out = fallback_half_width;
    if (sampler == NULL || !isfinite(travelled) ||
        !boonta_route_graph_sampler_prepare(sampler)) {
        return;
    }

    target = fmodf(travelled, sampler->total_length);
    if (target < 0.0f) target += sampler->total_length;

    for (edge_index = 0U;
         edge_index < BOONTA_RUNTIME_ROUTE_EDGE_COUNT;
         ++edge_index) {
        const float edge_length = sampler->edge_lengths[edge_index];
        if (target <= edge_length ||
            edge_index + 1U == BOONTA_RUNTIME_ROUTE_EDGE_COUNT) {
            unsigned int lower = 0U;
            const float edge_target = target;
            float t;
            float span;

            while (lower + 1U < BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS &&
                   sampler->distance_lut[edge_index][lower + 1U] < edge_target) {
                ++lower;
            }
            span = sampler->distance_lut[edge_index][lower + 1U]
                 - sampler->distance_lut[edge_index][lower];
            if (span > 0.000001f) {
                const float fraction = (edge_target
                    - sampler->distance_lut[edge_index][lower]) / span;
                t = ((float)lower + fraction) /
                    (float)BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS;
                if (t < 0.0f) t = 0.0f;
                if (t > 1.0f) t = 1.0f;
            } else {
                t = (float)lower /
                    (float)BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS;
            }

            boonta_route_graph_evaluate_edge(
                edge_index, t, x_out, y_out, z_out);
            if (width_out != NULL) {
                *width_out = boonta_route_graph_width_at(
                    edge_index, t, fallback_half_width);
            }
            if (y_out != NULL) {
                if (*y_out < -3.0f) *y_out = -3.0f;
                if (*y_out > 3.0f) *y_out = 3.0f;
            }
            return;
        }
        target -= edge_length;
    }
}

#endif /* BOONTA_REBORN_ROUTE_GRAPH_SAMPLING_H */
