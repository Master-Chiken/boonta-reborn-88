#ifndef BOONTA_REBORN_COURSE_RUNTIME_IMPL_H
#define BOONTA_REBORN_COURSE_RUNTIME_IMPL_H
#include <math.h>
#include <string.h>
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
    if (context == NULL) return 0;
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
            steering < -BOONTA_COURSE_BRANCH_STEERING_DEADZONE ? -1 :
            steering > BOONTA_COURSE_BRANCH_STEERING_DEADZONE ? 1 : 0;
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
    &g_boonta_course_runtime_context
};
#endif
