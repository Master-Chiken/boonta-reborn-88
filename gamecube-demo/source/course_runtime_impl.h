#ifndef BOONTA_REBORN_COURSE_RUNTIME_IMPL_H
#define BOONTA_REBORN_COURSE_RUNTIME_IMPL_H
#include <math.h>
#include <string.h>
#include "gameplay_state.h"
#ifndef BOONTA_COURSE_SYMBOL
#error "Define BOONTA_COURSE_SYMBOL before including course_runtime_impl.h"
#endif
#ifndef BOONTA_COURSE_ID
#error "Define BOONTA_COURSE_ID before including course_runtime_impl.h"
#endif
#ifndef BOONTA_COURSE_DISPLAY_NAME
#error "Define BOONTA_COURSE_DISPLAY_NAME before including course_runtime_impl.h"
#endif
#ifndef BOONTA_COURSE_REGION
#error "Define BOONTA_COURSE_REGION before including course_runtime_impl.h"
#endif
#ifndef BOONTA_COURSE_DEFAULT_HALF_WIDTH
#error "Define BOONTA_COURSE_DEFAULT_HALF_WIDTH before including course_runtime_impl.h"
#endif
#define BOONTA_COURSE_BRANCH_STEERING_DEADZONE 0.20f
#define BOONTA_COURSE_BRANCH_SELECTION_DISTANCE 16.8f
#define BOONTA_COURSE_RENDER_LOOKAHEAD_DISTANCE 117.6f

typedef struct {
    BoontaRouteGraphSampler sampler;
    BoontaRouteCursor cursor;
    int cursor_ready;
    BoontaRouteCursor rival_cursors[BOONTA_RIVAL_COUNT];
    int rival_cursor_ready[BOONTA_RIVAL_COUNT];
} BoontaCourseRuntimeContext;
static BoontaCourseRuntimeContext g_boonta_course_runtime_context;
static const BoontaRouteCursorGraph g_boonta_course_cursor_graph = {
    boonta_runtime_route_topology_edges,
    BOONTA_RUNTIME_ROUTE_EDGE_COUNT,
    BOONTA_RUNTIME_ROUTE_NODE_COUNT,
    BOONTA_RUNTIME_ROUTE_START_NODE_INDEX,
    BOONTA_RUNTIME_ROUTE_CLOSED_LOOP
};

static int boonta_course_runtime_reset(void *runtime_context)
{
    BoontaCourseRuntimeContext *context = (BoontaCourseRuntimeContext *)runtime_context;
    unsigned int start_edge = BOONTA_ROUTE_CURSOR_NO_EDGE;
    unsigned int edge;
    unsigned int rival_index;
    if (context == NULL) return 0;
    for (rival_index = 0U; rival_index < BOONTA_RIVAL_COUNT; ++rival_index) {
        context->rival_cursor_ready[rival_index] = 0;
    }
    if (!context->sampler.lengths_ready) {
        memset(&context->sampler, 0, sizeof(context->sampler));
        if (!boonta_route_graph_sampler_prepare(&context->sampler)) {
            context->cursor_ready = 0;
            return 0;
        }
    }
    for (edge = 0U; edge < BOONTA_RUNTIME_ROUTE_EDGE_COUNT; ++edge) {
        if (boonta_runtime_route_topology_edges[edge].from_node ==
            BOONTA_RUNTIME_ROUTE_START_NODE_INDEX) {
            start_edge = edge;
            break;
        }
    }
    if (start_edge == BOONTA_ROUTE_CURSOR_NO_EDGE) {
        context->cursor_ready = 0;
        return 0;
    }
    context->cursor_ready = boonta_route_cursor_init(
        &context->cursor, &g_boonta_course_cursor_graph,
        context->sampler.edge_lengths, start_edge) == BOONTA_ROUTE_CURSOR_OK;
    if (context->cursor_ready && BOONTA_RUNTIME_ROUTE_HAS_BRANCHES) {
        if (boonta_route_graph_sampler_prime_lookahead(
                &context->sampler, &context->cursor, 0,
                BOONTA_COURSE_BRANCH_SELECTION_DISTANCE,
                BOONTA_COURSE_RENDER_LOOKAHEAD_DISTANCE) != BOONTA_ROUTE_CURSOR_OK) {
            context->cursor_ready = 0;
        }
    }
    return context->cursor_ready;
}

static int boonta_course_runtime_advance(void *runtime_context,
                                         float distance_delta, float steering)
{
    BoontaCourseRuntimeContext *context = (BoontaCourseRuntimeContext *)runtime_context;
    if (context == NULL || !context->cursor_ready) return 0;
    if (BOONTA_RUNTIME_ROUTE_HAS_BRANCHES) {
        const int branch_direction =
            boonta_route_branch_direction_from_steering(
                steering, BOONTA_COURSE_BRANCH_STEERING_DEADZONE);
        if (boonta_route_graph_sampler_prime_lookahead(
                &context->sampler, &context->cursor, branch_direction,
                BOONTA_COURSE_BRANCH_SELECTION_DISTANCE,
                BOONTA_COURSE_RENDER_LOOKAHEAD_DISTANCE) != BOONTA_ROUTE_CURSOR_OK) {
            return 0;
        }
    }
    return boonta_route_cursor_move(
        &context->cursor, distance_delta, NULL, 0U) == BOONTA_ROUTE_CURSOR_OK;
}

static void boonta_course_runtime_sample(void *runtime_context,
    float player_distance, float travelled, float fallback_half_width,
    float *x, float *y, float *z, float *width)
{
    BoontaCourseRuntimeContext *context = (BoontaCourseRuntimeContext *)runtime_context;
    if (context == NULL || !context->sampler.lengths_ready) {
        if (x != NULL) *x = 0.0f;
        if (y != NULL) *y = 0.0f;
        if (z != NULL) *z = 0.0f;
        if (width != NULL) *width = fallback_half_width;
        return;
    }
#if BOONTA_RUNTIME_ROUTE_IS_SINGLE_LOOP
    (void)player_distance;
    boonta_route_graph_sampler_sample_at(
        &context->sampler, travelled, fallback_half_width, x, y, z, width);
#else
    if (context->cursor_ready &&
        boonta_route_graph_sampler_sample_relative_to_cursor(
            &context->sampler, &context->cursor, player_distance, travelled,
            fallback_half_width, x, y, z, width) == BOONTA_ROUTE_CURSOR_OK) {
        return;
    }
    boonta_route_graph_sampler_sample_cursor_at(
        &context->sampler, &context->cursor, fallback_half_width, x, y, z, width);
#endif
}

static unsigned int boonta_course_runtime_find_start_edge(void)
{
    unsigned int edge;
    for (edge = 0U; edge < BOONTA_RUNTIME_ROUTE_EDGE_COUNT; ++edge) {
        if (boonta_runtime_route_topology_edges[edge].from_node ==
            BOONTA_RUNTIME_ROUTE_START_NODE_INDEX) {
            return edge;
        }
    }
    return BOONTA_ROUTE_CURSOR_NO_EDGE;
}

/*
 * Each course runtime owns rival cursors that point at that course's sampler.
 * main.c retains race-facing coordinates, while the course owns all route
 * topology and geometry. Prime a default path before applying the grid offset
 * so a rival placed beyond an early split still has valid branch history.
 */
static int boonta_course_runtime_reset_rival_route(
    void *runtime_context, unsigned int rival_index,
    float initial_route_distance, float lap_distance,
    float *route_distance_out, float *progress_out)
{
    BoontaCourseRuntimeContext *context = (BoontaCourseRuntimeContext *)runtime_context;
    BoontaRouteCursor candidate;
    const unsigned int start_edge = boonta_course_runtime_find_start_edge();
    float lap_progress = 0.0f;
    float initial_progress = 0.0f;

    if (route_distance_out != NULL) *route_distance_out = 0.0f;
    if (progress_out != NULL) *progress_out = 0.0f;
    if (context == NULL || rival_index >= BOONTA_RIVAL_COUNT ||
        !context->sampler.lengths_ready || start_edge == BOONTA_ROUTE_CURSOR_NO_EDGE ||
        route_distance_out == NULL || progress_out == NULL ||
        !isfinite(initial_route_distance) || initial_route_distance < 0.0f ||
        !isfinite(lap_distance) || lap_distance <= 0.0f) {
        return 0;
    }

    context->rival_cursor_ready[rival_index] = 0;
    if (boonta_route_cursor_init(&candidate, &g_boonta_course_cursor_graph,
            context->sampler.edge_lengths, start_edge) != BOONTA_ROUTE_CURSOR_OK) {
        return 0;
    }
    if (BOONTA_RUNTIME_ROUTE_HAS_BRANCHES &&
        boonta_route_graph_sampler_prime_lookahead(
            &context->sampler, &candidate, 0,
            BOONTA_COURSE_BRANCH_SELECTION_DISTANCE,
            BOONTA_COURSE_RENDER_LOOKAHEAD_DISTANCE) != BOONTA_ROUTE_CURSOR_OK) {
        return 0;
    }
    if (initial_route_distance > 0.0f &&
        boonta_route_cursor_move(&candidate, initial_route_distance,
            NULL, 0U) != BOONTA_ROUTE_CURSOR_OK) {
        return 0;
    }
    if (BOONTA_RUNTIME_ROUTE_HAS_BRANCHES &&
        boonta_route_graph_sampler_prime_lookahead(
            &context->sampler, &candidate, 0,
            BOONTA_COURSE_BRANCH_SELECTION_DISTANCE,
            BOONTA_COURSE_RENDER_LOOKAHEAD_DISTANCE) != BOONTA_ROUTE_CURSOR_OK) {
        return 0;
    }
    if (boonta_route_cursor_lap_progress(&candidate, &lap_progress) !=
            BOONTA_ROUTE_CURSOR_OK ||
        !boonta_rival_progress_from_cursor_state(
            candidate.completed_laps, lap_progress, lap_distance,
            &initial_progress)) {
        return 0;
    }

    context->rival_cursors[rival_index] = candidate;
    context->rival_cursor_ready[rival_index] = 1;
    *route_distance_out = initial_route_distance;
    *progress_out = initial_progress;
    return 1;
}

static int boonta_course_runtime_advance_rival_route(
    void *runtime_context, unsigned int rival_index,
    float distance_delta, float steering, float current_route_distance,
    float lap_distance, float *next_route_distance_out, float *next_progress_out)
{
    BoontaCourseRuntimeContext *context = (BoontaCourseRuntimeContext *)runtime_context;
    BoontaRouteCursor candidate;
    int branch_direction = 0;

    if (next_route_distance_out != NULL) *next_route_distance_out = 0.0f;
    if (next_progress_out != NULL) *next_progress_out = 0.0f;
    if (context == NULL || rival_index >= BOONTA_RIVAL_COUNT ||
        !context->rival_cursor_ready[rival_index] ||
        !isfinite(distance_delta) || distance_delta < 0.0f ||
        !isfinite(current_route_distance) || current_route_distance < 0.0f ||
        !isfinite(lap_distance) || lap_distance <= 0.0f ||
        next_route_distance_out == NULL || next_progress_out == NULL) {
        return 0;
    }

    candidate = context->rival_cursors[rival_index];
    if (BOONTA_RUNTIME_ROUTE_HAS_BRANCHES) {
        branch_direction = boonta_route_branch_direction_from_steering(
            steering, BOONTA_COURSE_BRANCH_STEERING_DEADZONE);
        if (boonta_route_graph_sampler_prime_lookahead(
                &context->sampler, &candidate, branch_direction,
                BOONTA_COURSE_BRANCH_SELECTION_DISTANCE,
                BOONTA_COURSE_RENDER_LOOKAHEAD_DISTANCE) != BOONTA_ROUTE_CURSOR_OK) {
            return 0;
        }
    }
    if (!boonta_rival_advance_cursor_transaction(
            &candidate, distance_delta, current_route_distance, lap_distance,
            next_route_distance_out, next_progress_out)) {
        return 0;
    }

    context->rival_cursors[rival_index] = candidate;
    return 1;
}

static int boonta_course_runtime_sample_rival_route(
    void *runtime_context, unsigned int rival_index,
    float current_route_distance, float target_route_distance,
    float fallback_half_width,
    float *x, float *y, float *z, float *width)
{
    BoontaCourseRuntimeContext *context = (BoontaCourseRuntimeContext *)runtime_context;
    if (x != NULL) *x = 0.0f;
    if (y != NULL) *y = 0.0f;
    if (z != NULL) *z = 0.0f;
    if (width != NULL) *width = fallback_half_width;
    if (context == NULL || rival_index >= BOONTA_RIVAL_COUNT ||
        !context->rival_cursor_ready[rival_index] ||
        !isfinite(current_route_distance) || !isfinite(target_route_distance)) {
        return BOONTA_ROUTE_CURSOR_INVALID;
    }
    return boonta_route_graph_sampler_sample_relative_to_cursor(
        &context->sampler, &context->rival_cursors[rival_index],
        current_route_distance, target_route_distance, fallback_half_width,
        x, y, z, width);
}

static int boonta_course_runtime_get_lap_state(void *runtime_context,
    unsigned int *completed_laps, float *lap_progress)
{
    BoontaCourseRuntimeContext *context = (BoontaCourseRuntimeContext *)runtime_context;
    BoontaRouteCursorState state;
    if (context == NULL || !context->cursor_ready ||
        boonta_route_cursor_get_state(&context->cursor, &state) != BOONTA_ROUTE_CURSOR_OK) {
        return 0;
    }
    if (completed_laps != NULL) *completed_laps = state.completed_laps;
    if (lap_progress != NULL &&
        boonta_route_cursor_lap_progress(&context->cursor, lap_progress) != BOONTA_ROUTE_CURSOR_OK) {
        return 0;
    }
    return 1;
}

static int boonta_course_runtime_distance_to_next_finish(
    void *runtime_context, float player_distance, float *distance)
{
    BoontaCourseRuntimeContext *context = (BoontaCourseRuntimeContext *)runtime_context;
    float next_finish;
    if (context == NULL || distance == NULL || !context->sampler.lengths_ready) return 0;
    if (BOONTA_RUNTIME_ROUTE_HAS_BRANCHES) {
        return context->cursor_ready &&
            boonta_route_cursor_distance_to_next_lap(
                &context->cursor, distance) == BOONTA_ROUTE_CURSOR_OK;
    }
    if (!isfinite(player_distance) || player_distance < 0.0f ||
        !isfinite(context->sampler.total_length) || context->sampler.total_length <= 0.001f) {
        return 0;
    }
    next_finish = (floorf(player_distance / context->sampler.total_length) + 1.0f) *
                  context->sampler.total_length;
    *distance = next_finish - player_distance;
    return isfinite(*distance) && *distance >= 0.0f;
}

const BoontaCourseDefinition BOONTA_COURSE_SYMBOL = {
    BOONTA_COURSE_ID, BOONTA_COURSE_DISPLAY_NAME, BOONTA_COURSE_REGION,
    BOONTA_RUNTIME_ROUTE_LENGTH, BOONTA_COURSE_DEFAULT_HALF_WIDTH,
    BOONTA_RUNTIME_ROUTE_NODE_COUNT, BOONTA_RUNTIME_ROUTE_EDGE_COUNT,
    BOONTA_RUNTIME_ROUTE_HAS_BRANCHES,
    boonta_course_runtime_reset, boonta_course_runtime_advance,
    boonta_course_runtime_sample, boonta_course_runtime_get_lap_state,
    boonta_course_runtime_distance_to_next_finish,
    boonta_course_runtime_reset_rival_route,
    boonta_course_runtime_advance_rival_route,
    boonta_course_runtime_sample_rival_route,
    &g_boonta_course_runtime_context
};
#endif
