#ifndef BOONTA_REBORN_ROUTE_GRAPH_SAMPLING_H
#define BOONTA_REBORN_ROUTE_GRAPH_SAMPLING_H

#include <math.h>
#include <stddef.h>

#ifndef BOONTA_ROUTE_GRAPH_HEADER
#define BOONTA_ROUTE_GRAPH_HEADER "generated_route_graph.h"
#endif
#include BOONTA_ROUTE_GRAPH_HEADER

/*
 * Native sampler for the clean-room route-graph curve representation.
 * Arc-distance tables are built once, on first use, and then reused by GX
 * scene construction. The same functions are compiled by host regression tests.
 */
typedef struct {
    float distance_lut[BOONTA_RUNTIME_ROUTE_EDGE_COUNT]
                      [BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS + 1U];
    float edge_lengths[BOONTA_RUNTIME_ROUTE_EDGE_COUNT];
    float edge_start_distances[BOONTA_RUNTIME_ROUTE_EDGE_COUNT];
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
    float u;
    float b0, b1, b2, b3;

    if (x != NULL) *x = 0.0f;
    if (y != NULL) *y = 0.0f;
    if (z != NULL) *z = 0.0f;
    if (edge_index >= BOONTA_RUNTIME_ROUTE_EDGE_COUNT || !isfinite(t)) return;
    /* A route edge is parameterized only on its closed interval [0, 1]. */
    if (t < 0.0f) t = 0.0f;
    if (t > 1.0f) t = 1.0f;
    /* Coefficients must be calculated after clamping the parameter. */
    u = 1.0f - t;
    b0 = u * u * u;
    b1 = 3.0f * u * u * t;
    b2 = 3.0f * u * t * t;
    b3 = t * t * t;
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
        sampler->edge_start_distances[edge_index] = scaled_prefix;
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
    float coordinate;
    unsigned int base;
    float fraction;
    if (edge_index >= BOONTA_RUNTIME_ROUTE_EDGE_COUNT || !isfinite(t)) {
        return fallback_half_width;
    }
    /* Width lookup is defined on one edge; never let conversion of an
     * arbitrary/NaN parameter become an out-of-bounds sample index. */
    if (t < 0.0f) t = 0.0f;
    if (t > 1.0f) t = 1.0f;
    coordinate =
        (float)(edge_index * BOONTA_RUNTIME_ROUTE_WIDTH_SAMPLES_PER_EDGE)
        + t * (float)BOONTA_RUNTIME_ROUTE_WIDTH_SAMPLES_PER_EDGE;
    base = (unsigned int)floorf(coordinate);
    fraction = coordinate - (float)base;
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

/*
 * Sample one selected edge by its local arc distance. Unlike sample_at(), this
 * API does not wrap at the whole-loop seam: callers that own a route cursor can
 * select the next edge explicitly and clamp progress at that edge's endpoints.
 */
static inline void boonta_route_graph_sampler_sample_edge_at(
    BoontaRouteGraphSampler *sampler, unsigned int edge_index,
    float distance_on_edge, float fallback_half_width,
    float *x_out, float *y_out, float *z_out, float *width_out)
{
    unsigned int lower = 0U;
    unsigned int upper = BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS;
    float edge_length;
    float target;
    float span;
    float t;

    if (x_out != NULL) *x_out = 0.0f;
    if (y_out != NULL) *y_out = 0.0f;
    if (z_out != NULL) *z_out = 0.0f;
    if (width_out != NULL) *width_out = fallback_half_width;
    if (sampler == NULL || edge_index >= BOONTA_RUNTIME_ROUTE_EDGE_COUNT ||
        !isfinite(distance_on_edge) ||
        !boonta_route_graph_sampler_prepare(sampler)) {
        return;
    }

    edge_length = sampler->edge_lengths[edge_index];
    if (!isfinite(edge_length) || edge_length <= 0.001f) return;

    /* Edge-local traversal stops at the endpoints; only the loop API wraps. */
    target = distance_on_edge;
    if (target < 0.0f) target = 0.0f;
    if (target > edge_length) target = edge_length;

    /*
     * Locate the LUT interval with bounded binary search. The same arc-distance
     * table is shared with the closed-loop sampler and the future route cursor.
     */
    while (lower + 1U < upper) {
        const unsigned int middle = lower + (upper - lower) / 2U;
        if (sampler->distance_lut[edge_index][middle] <= target) {
            lower = middle;
        } else {
            upper = middle;
        }
    }

    span = sampler->distance_lut[edge_index][lower + 1U]
         - sampler->distance_lut[edge_index][lower];
    if (span > 0.000001f) {
        const float fraction = (target
            - sampler->distance_lut[edge_index][lower]) / span;
        t = ((float)lower + fraction) /
            (float)BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS;
        if (t < 0.0f) t = 0.0f;
        if (t > 1.0f) t = 1.0f;
    } else {
        t = (float)lower /
            (float)BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS;
    }

    boonta_route_graph_evaluate_edge(edge_index, t, x_out, y_out, z_out);
    if (width_out != NULL) {
        *width_out = boonta_route_graph_width_at(
            edge_index, t, fallback_half_width);
    }
    if (y_out != NULL) {
        if (*y_out < -3.0f) *y_out = -3.0f;
        if (*y_out > 3.0f) *y_out = 3.0f;
    }
}

/*
 * Select an outgoing edge from its horizontal turn relative to the incoming
 * tangent. direction < 0 means steer left, > 0 means steer right, and 0
 * chooses the straightest continuation. Project axes are x lateral, y up,
 * z forward; positive cross here represents a left turn.
 */
/*
 * Return a normalized horizontal endpoint tangent for a cubic Bezier edge.
 * A collapsed first handle has a valid second-/third-order direction, so do
 * not reject a curve merely because its endpoint derivative is zero.
 */
static inline int boonta_route_graph_edge_horizontal_tangent(
    unsigned int edge_index, int at_end, float *x_out, float *z_out)
{
    const BoontaRuntimeRouteEdge *edge;
    float tangent_x;
    float tangent_z;
    float length;

    if (x_out != NULL) *x_out = 0.0f;
    if (z_out != NULL) *z_out = 0.0f;
    if (edge_index >= BOONTA_RUNTIME_ROUTE_EDGE_COUNT ||
        (at_end != 0 && at_end != 1) || x_out == NULL || z_out == NULL) {
        return BOONTA_ROUTE_CURSOR_INVALID;
    }

    edge = &boonta_runtime_route_edges[edge_index];
    if (at_end) {
        /* B'(1), then its first useful higher-order direction, then chord. */
        tangent_x = edge->p3[0] - edge->control2[0];
        tangent_z = edge->p3[2] - edge->control2[2];
        length = sqrtf(tangent_x * tangent_x + tangent_z * tangent_z);
        if (!isfinite(length) || length <= 0.000001f) {
            tangent_x = edge->p3[0] - edge->control1[0];
            tangent_z = edge->p3[2] - edge->control1[2];
            length = sqrtf(tangent_x * tangent_x + tangent_z * tangent_z);
        }
        if (!isfinite(length) || length <= 0.000001f) {
            tangent_x = edge->p3[0] - edge->p0[0];
            tangent_z = edge->p3[2] - edge->p0[2];
            length = sqrtf(tangent_x * tangent_x + tangent_z * tangent_z);
        }
    } else {
        /* B'(0), then its first useful higher-order direction, then chord. */
        tangent_x = edge->control1[0] - edge->p0[0];
        tangent_z = edge->control1[2] - edge->p0[2];
        length = sqrtf(tangent_x * tangent_x + tangent_z * tangent_z);
        if (!isfinite(length) || length <= 0.000001f) {
            tangent_x = edge->control2[0] - edge->p0[0];
            tangent_z = edge->control2[2] - edge->p0[2];
            length = sqrtf(tangent_x * tangent_x + tangent_z * tangent_z);
        }
        if (!isfinite(length) || length <= 0.000001f) {
            tangent_x = edge->p3[0] - edge->p0[0];
            tangent_z = edge->p3[2] - edge->p0[2];
            length = sqrtf(tangent_x * tangent_x + tangent_z * tangent_z);
        }
    }

    if (!isfinite(length) || length <= 0.000001f) {
        return BOONTA_ROUTE_CURSOR_INVALID;
    }
    *x_out = tangent_x / length;
    *z_out = tangent_z / length;
    return BOONTA_ROUTE_CURSOR_OK;
}

/*
 * Select an outgoing edge from its horizontal turn relative to the incoming
 * tangent. direction < 0 means steer left, > 0 means steer right, and 0
 * chooses the straightest continuation. Project axes are x lateral, y up,
 * z forward; positive cross here represents a left turn.
 */
static inline int boonta_route_graph_choose_outgoing_edge(
    const BoontaRouteCursor *cursor, unsigned int node, int direction,
    unsigned int *selected_edge)
{
    unsigned int current_edge;
    unsigned int edge;
    float incoming_x, incoming_z;
    float best_score = 0.0f;
    int found = 0;

    if (selected_edge != NULL) *selected_edge = BOONTA_ROUTE_CURSOR_NO_EDGE;
    if (cursor == NULL || cursor->graph == NULL ||
        cursor->history_count == 0U ||
        cursor->path_index >= cursor->history_count ||
        node >= cursor->graph->node_count ||
        direction < -1 || direction > 1 ||
        selected_edge == NULL) {
        return BOONTA_ROUTE_CURSOR_INVALID;
    }

    current_edge = cursor->path_history[cursor->path_index];
    if (current_edge >= cursor->graph->edge_count ||
        cursor->graph->edges[current_edge].to_node != node ||
        boonta_route_graph_edge_horizontal_tangent(
            current_edge, 1, &incoming_x, &incoming_z) !=
            BOONTA_ROUTE_CURSOR_OK) {
        return BOONTA_ROUTE_CURSOR_INVALID;
    }

    for (edge = 0U; edge < cursor->graph->edge_count; ++edge) {
        float outgoing_x, outgoing_z;
        float dot, cross, angle, score;
        int better;

        if (cursor->graph->edges[edge].from_node != node) continue;
        if (boonta_route_graph_edge_horizontal_tangent(
                edge, 0, &outgoing_x, &outgoing_z) !=
            BOONTA_ROUTE_CURSOR_OK) {
            continue;
        }

        dot = incoming_x * outgoing_x + incoming_z * outgoing_z;
        cross = incoming_z * outgoing_x - incoming_x * outgoing_z;
        angle = atan2f(cross, dot);
        if (!isfinite(angle)) continue;

        if (direction < 0) {
            score = angle;
            better = !found || score > best_score + 0.000001f;
        } else if (direction > 0) {
            score = angle;
            better = !found || score < best_score - 0.000001f;
        } else {
            score = fabsf(angle);
            better = !found || score < best_score - 0.000001f;
        }

        /* Stable edge-index tie break makes identical branches deterministic. */
        if (better || (!better && found &&
            fabsf(score - best_score) <= 0.000001f && edge < *selected_edge)) {
            best_score = score;
            *selected_edge = edge;
            found = 1;
        }
    }

    return found ? BOONTA_ROUTE_CURSOR_OK : BOONTA_ROUTE_CURSOR_INVALID;
}


/*
 * Cache the next junction choice before the vehicle reaches the node. The
 * cursor is moved just beyond the current edge endpoint and then reversed;
 * its physical position is restored while the chosen future edge remains in
 * path_history. Renderer look-ahead can then follow the same selected branch.
 *
 * selection_distance is measured in the sampler's arc-distance units. A new
 * steering choice can replace an already-cached future edge while still on
 * the incoming edge.
 */
static inline int boonta_route_graph_sampler_prime_branch_choice(
    const BoontaRouteGraphSampler *sampler, BoontaRouteCursor *cursor,
    int direction, float selection_distance)
{
    BoontaRouteCursor backup;
    BoontaRouteCursorState state;
    BoontaRouteBranchChoice choice;
    unsigned int node;
    unsigned int selected_edge = BOONTA_ROUTE_CURSOR_NO_EDGE;
    unsigned int outgoing_count;
    float edge_length;
    float remaining_distance;
    float transition_distance;
    int result;

    if (sampler == NULL || cursor == NULL ||
        cursor->graph == NULL ||
        cursor->edge_lengths != sampler->edge_lengths ||
        cursor->graph->edge_count != BOONTA_RUNTIME_ROUTE_EDGE_COUNT ||
        !isfinite(selection_distance) || selection_distance < 0.0f ||
        direction < -1 || direction > 1) {
        return BOONTA_ROUTE_CURSOR_INVALID;
    }

    result = boonta_route_cursor_get_state(cursor, &state);
    if (result != BOONTA_ROUTE_CURSOR_OK) return result;

    edge_length = cursor->edge_lengths[state.edge];
    if (!isfinite(edge_length) || edge_length <= 0.001f ||
        !isfinite(cursor->distance_on_edge) ||
        cursor->distance_on_edge < 0.0f ||
        cursor->distance_on_edge > edge_length) {
        return BOONTA_ROUTE_CURSOR_INVALID;
    }

    node = cursor->graph->edges[state.edge].to_node;
    outgoing_count = boonta_route_cursor_outgoing_count(
        cursor->graph, node, NULL);
    if (outgoing_count <= 1U) return BOONTA_ROUTE_CURSOR_OK;

    remaining_distance = edge_length - cursor->distance_on_edge;
    if (remaining_distance > selection_distance) {
        return BOONTA_ROUTE_CURSOR_OK;
    }

    result = boonta_route_graph_choose_outgoing_edge(
        cursor, node, direction, &selected_edge);
    if (result != BOONTA_ROUTE_CURSOR_OK) return result;

    backup = *cursor;
    choice.node = node;
    choice.edge = selected_edge;
    transition_distance = remaining_distance +
        4.0f * BOONTA_ROUTE_CURSOR_EPSILON;
    if (!isfinite(transition_distance)) return BOONTA_ROUTE_CURSOR_INVALID;

    result = boonta_route_cursor_move(
        cursor, transition_distance, &choice, 1U);
    if (result != BOONTA_ROUTE_CURSOR_OK) {
        *cursor = backup;
        return result;
    }

    result = boonta_route_cursor_move(
        cursor, -transition_distance, NULL, 0U);
    if (result != BOONTA_ROUTE_CURSOR_OK ||
        cursor->path_index != backup.path_index ||
        cursor->path_history[cursor->path_index] !=
            backup.path_history[backup.path_index] ||
        fabsf(cursor->distance_on_edge - backup.distance_on_edge) >
            0.0001f) {
        *cursor = backup;
        return result == BOONTA_ROUTE_CURSOR_OK
            ? BOONTA_ROUTE_CURSOR_INVALID : result;
    }

    return BOONTA_ROUTE_CURSOR_OK;
}

static inline void boonta_route_graph_sampler_sample_at(
    BoontaRouteGraphSampler *sampler, float travelled,
    float fallback_half_width,
    float *x_out, float *y_out, float *z_out, float *width_out)
{
    unsigned int edge_index;
    float target;
    float edge_target;
    unsigned int edge_low = 0U;
    unsigned int edge_high = BOONTA_RUNTIME_ROUTE_EDGE_COUNT;

    if (x_out != NULL) *x_out = 0.0f;
    if (y_out != NULL) *y_out = 0.0f;
    if (z_out != NULL) *z_out = 0.0f;
    if (width_out != NULL) *width_out = fallback_half_width;
    if (sampler == NULL || !isfinite(travelled) ||
        !boonta_route_graph_sampler_prepare(sampler)) {
        return;
    }
#if !BOONTA_RUNTIME_ROUTE_IS_SINGLE_LOOP
    /* A catalogue of branched edges has no single global wrap coordinate. */
    return;
#endif

    target = fmodf(travelled, sampler->total_length);
    if (target < 0.0f) target += sampler->total_length;

    /*
     * Find the last edge whose start is at or before target. At an exact
     * edge boundary this selects the following edge; connected endpoints
     * and the shared width samples make that representation continuous.
     */
    while (edge_low + 1U < edge_high) {
        const unsigned int middle = edge_low + (edge_high - edge_low) / 2U;
        if (target < sampler->edge_start_distances[middle]) {
            edge_high = middle;
        } else {
            edge_low = middle;
        }
    }
    edge_index = edge_low;
    edge_target = target - sampler->edge_start_distances[edge_index];

    boonta_route_graph_sampler_sample_edge_at(
        sampler, edge_index, edge_target, fallback_half_width,
        x_out, y_out, z_out, width_out);
}

/*
 * Adapter for the topology cursor: sample its selected edge using the exact
 * arc-length table the cursor was initialized with. Keeping geometry lookup
 * here avoids duplicating edge-index/distance handling in gameplay code.
 */
static inline void boonta_route_graph_sampler_sample_cursor_at(
    BoontaRouteGraphSampler *sampler, const BoontaRouteCursor *cursor,
    float fallback_half_width,
    float *x_out, float *y_out, float *z_out, float *width_out)
{
    BoontaRouteCursorState state;

    if (x_out != NULL) *x_out = 0.0f;
    if (y_out != NULL) *y_out = 0.0f;
    if (z_out != NULL) *z_out = 0.0f;
    if (width_out != NULL) *width_out = fallback_half_width;
    if (sampler == NULL || cursor == NULL || cursor->graph == NULL ||
        cursor->edge_lengths != sampler->edge_lengths ||
        cursor->graph->edge_count != BOONTA_RUNTIME_ROUTE_EDGE_COUNT ||
        boonta_route_cursor_get_state(cursor, &state) != BOONTA_ROUTE_CURSOR_OK) {
        return;
    }

    boonta_route_graph_sampler_sample_edge_at(
        sampler, state.edge, cursor->distance_on_edge, fallback_half_width,
        x_out, y_out, z_out, width_out);
}

/*
 * Sample an arbitrary nearby route coordinate relative to the cursor's current
 * distance. A copy is advanced, so rendering look-ahead/look-behind never
 * mutates simulation history. At the initial closed-loop start, a small
 * negative look-behind is interpreted across the loop seam.
 */
static inline int boonta_route_graph_sampler_sample_relative_to_cursor(
    BoontaRouteGraphSampler *sampler, const BoontaRouteCursor *cursor,
    float current_route_distance, float target_route_distance,
    float fallback_half_width,
    float *x_out, float *y_out, float *z_out, float *width_out)
{
    BoontaRouteCursor sample_cursor;
    float delta_distance;
    int result;

    if (x_out != NULL) *x_out = 0.0f;
    if (y_out != NULL) *y_out = 0.0f;
    if (z_out != NULL) *z_out = 0.0f;
    if (width_out != NULL) *width_out = fallback_half_width;
    if (sampler == NULL || cursor == NULL ||
        !isfinite(current_route_distance) || !isfinite(target_route_distance)) {
        return BOONTA_ROUTE_CURSOR_INVALID;
    }

    sample_cursor = *cursor;
    delta_distance = target_route_distance - current_route_distance;
    if (BOONTA_RUNTIME_ROUTE_IS_SINGLE_LOOP &&
        sample_cursor.graph != NULL && sample_cursor.graph->closed_loop &&
        sample_cursor.path_index == 0U &&
        sample_cursor.distance_on_edge <= BOONTA_ROUTE_CURSOR_EPSILON &&
        delta_distance < 0.0f) {
        delta_distance += sampler->total_length;
    }

    result = boonta_route_cursor_move(&sample_cursor, delta_distance, NULL, 0U);
    if (result != BOONTA_ROUTE_CURSOR_OK) return result;

    boonta_route_graph_sampler_sample_cursor_at(
        sampler, &sample_cursor, fallback_half_width,
        x_out, y_out, z_out, width_out);
    return BOONTA_ROUTE_CURSOR_OK;
}

#endif /* BOONTA_REBORN_ROUTE_GRAPH_SAMPLING_H */
