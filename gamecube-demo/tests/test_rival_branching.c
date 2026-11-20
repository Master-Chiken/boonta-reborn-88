#define BOONTA_ROUTE_GRAPH_HEADER "../tests/fixtures/generated_branched_route_graph.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>

#include "../source/rival_ai.h"
#include "../source/route_graph_sampling.h"
#include "../source/course_catalog.h"

#define BOONTA_COURSE_SYMBOL boonta_test_branched_course
#define BOONTA_COURSE_ID "test-branched-course"
#define BOONTA_COURSE_DISPLAY_NAME "TEST BRANCHED COURSE"
#define BOONTA_COURSE_REGION "SYNTHETIC"
#define BOONTA_COURSE_DEFAULT_HALF_WIDTH 3.5f
#include "../source/course_runtime_impl.h"

static const BoontaRouteCursorGraph g_branch_graph = {
    boonta_runtime_route_topology_edges,
    BOONTA_RUNTIME_ROUTE_EDGE_COUNT,
    BOONTA_RUNTIME_ROUTE_NODE_COUNT,
    BOONTA_RUNTIME_ROUTE_START_NODE_INDEX,
    BOONTA_RUNTIME_ROUTE_CLOSED_LOOP
};

static void assert_vec3_close(const float a[3], const float b[3])
{
    unsigned int axis;
    for (axis = 0U; axis < 3U; ++axis) {
        assert(fabsf(a[axis] - b[axis]) < 0.00001f);
    }
}

static void assert_join_tangent_close(
    const BoontaRuntimeRouteEdge *incoming,
    const BoontaRuntimeRouteEdge *outgoing)
{
    unsigned int axis;
    for (axis = 0U; axis < 3U; ++axis) {
        const float incoming_tangent =
            incoming->p3[axis] - incoming->control2[axis];
        const float outgoing_tangent =
            outgoing->control1[axis] - outgoing->p0[axis];
        assert(fabsf(incoming_tangent - outgoing_tangent) < 0.00001f);
    }
}

static void test_synthetic_fork_geometry_is_connected(void)
{
    assert_vec3_close(boonta_runtime_route_edges[0].p3,
                      boonta_runtime_route_edges[1].p0);
    assert_vec3_close(boonta_runtime_route_edges[0].p3,
                      boonta_runtime_route_edges[2].p0);
    assert_vec3_close(boonta_runtime_route_edges[1].p3,
                      boonta_runtime_route_edges[3].p0);
    assert_vec3_close(boonta_runtime_route_edges[2].p3,
                      boonta_runtime_route_edges[4].p0);
    assert_vec3_close(boonta_runtime_route_edges[3].p3,
                      boonta_runtime_route_edges[5].p0);
    assert_vec3_close(boonta_runtime_route_edges[4].p3,
                      boonta_runtime_route_edges[5].p0);
    assert_vec3_close(boonta_runtime_route_edges[5].p3,
                      boonta_runtime_route_edges[6].p0);
    assert_vec3_close(boonta_runtime_route_edges[6].p3,
                      boonta_runtime_route_edges[0].p0);

    assert_join_tangent_close(&boonta_runtime_route_edges[1],
                              &boonta_runtime_route_edges[3]);
    assert_join_tangent_close(&boonta_runtime_route_edges[2],
                              &boonta_runtime_route_edges[4]);
    assert_join_tangent_close(&boonta_runtime_route_edges[3],
                              &boonta_runtime_route_edges[5]);
    assert_join_tangent_close(&boonta_runtime_route_edges[4],
                              &boonta_runtime_route_edges[5]);
}

static void test_rivals_choose_left_and_right_then_rejoin(void)
{
    BoontaRouteGraphSampler sampler = {0};
    BoontaRouteCursor left_rival;
    BoontaRouteCursor right_rival;
    BoontaRouteCursorState left_state;
    BoontaRouteCursorState right_state;
    const float selection_distance = 2.0f;
    const float preview_distance = 4.0f;
    const float distance_before_junction = 0.5f;
    const int left_direction =
        boonta_route_branch_direction_from_steering(-0.8f, 0.2f);
    const int right_direction =
        boonta_route_branch_direction_from_steering(0.8f, 0.2f);

    assert(BOONTA_RUNTIME_ROUTE_HAS_BRANCHES);
    assert(left_direction == -1);
    assert(right_direction == 1);
    assert(boonta_route_branch_direction_from_steering(-0.2f, 0.2f) == 0);
    assert(boonta_route_branch_direction_from_steering(0.2f, 0.2f) == 0);
    assert(boonta_route_branch_direction_from_steering(NAN, 0.2f) == 0);
    assert(boonta_route_branch_direction_from_steering(0.8f, NAN) == 0);

    assert(boonta_route_graph_sampler_prepare(&sampler));
    assert(boonta_route_cursor_init(&left_rival, &g_branch_graph,
        sampler.edge_lengths, BOONTA_RUNTIME_ROUTE_START_NODE_INDEX) ==
        BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_init(&right_rival, &g_branch_graph,
        sampler.edge_lengths, BOONTA_RUNTIME_ROUTE_START_NODE_INDEX) ==
        BOONTA_ROUTE_CURSOR_OK);

    /* Both racers reach the same fork with identical position and history. */
    assert(boonta_route_cursor_move(&left_rival,
        sampler.edge_lengths[0] - distance_before_junction,
        NULL, 0U) == BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_move(&right_rival,
        sampler.edge_lengths[0] - distance_before_junction,
        NULL, 0U) == BOONTA_ROUTE_CURSOR_OK);

    assert(boonta_route_graph_sampler_prime_lookahead(
        &sampler, &left_rival, left_direction,
        selection_distance, preview_distance) == BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_graph_sampler_prime_lookahead(
        &sampler, &right_rival, right_direction,
        selection_distance, preview_distance) == BOONTA_ROUTE_CURSOR_OK);

    assert(left_rival.path_index == 0U && right_rival.path_index == 0U);
    assert(left_rival.path_history[1] == 1U);
    assert(right_rival.path_history[1] == 2U);

    /* Traverse both distinct branch+return paths into their common exit. */
    assert(boonta_route_cursor_move(&left_rival,
        distance_before_junction + sampler.edge_lengths[1] +
            sampler.edge_lengths[3] + 0.25f, NULL, 0U) == BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_move(&right_rival,
        distance_before_junction + sampler.edge_lengths[2] +
            sampler.edge_lengths[4] + 0.25f, NULL, 0U) == BOONTA_ROUTE_CURSOR_OK);

    assert(boonta_route_cursor_get_state(&left_rival, &left_state) ==
        BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_get_state(&right_rival, &right_state) ==
        BOONTA_ROUTE_CURSOR_OK);
    assert(left_state.edge == 5U && right_state.edge == 5U);
    assert(left_rival.history_count == 4U && right_rival.history_count == 4U);
    assert(left_rival.path_history[1] == 1U &&
           left_rival.path_history[2] == 3U);
    assert(right_rival.path_history[1] == 2U &&
           right_rival.path_history[2] == 4U);
    assert(left_rival.path_history[3] == right_rival.path_history[3]);
}

static void test_course_owned_rival_cursors_use_the_selected_graph(void)
{
    const BoontaCourseDefinition *course = &boonta_test_branched_course;
    BoontaCourseRuntimeContext *context =
        (BoontaCourseRuntimeContext *)course->runtime_context;
    float route_distance[2] = {0.0f, 0.0f};
    float progress[2] = {0.0f, 0.0f};
    float next_route_distance[2] = {0.0f, 0.0f};
    float next_progress[2] = {0.0f, 0.0f};
    float left_x = 0.0f, right_x = 0.0f;
    float left_y = 0.0f, right_y = 0.0f;
    float left_z = 0.0f, right_z = 0.0f;
    float left_width = 0.0f, right_width = 0.0f;
    BoontaRouteCursorState left_state, right_state;
    const float initial_offset = 0.5f;
    const float distance_to_branch_window =
        context != NULL ? context->sampler.edge_lengths[0] - 1.5f : 0.0f;
    const float left_join_delta =
        1.0f + context->sampler.edge_lengths[1] +
        context->sampler.edge_lengths[3] + 0.25f;
    const float right_join_delta =
        1.0f + context->sampler.edge_lengths[2] +
        context->sampler.edge_lengths[4] + 0.25f;

    assert(course->has_branches);
    assert(course->reset(course->runtime_context));
    assert(course->reset_rival_route != NULL);
    assert(course->advance_rival_route != NULL);
    assert(course->sample_rival_route != NULL);

    /* The course adapter owns separate cursors, but uses one course sampler. */
    assert(course->reset_rival_route(course->runtime_context, 0U,
        initial_offset, course->lap_distance,
        &route_distance[0], &progress[0]));
    assert(course->reset_rival_route(course->runtime_context, 1U,
        initial_offset, course->lap_distance,
        &route_distance[1], &progress[1]));
    assert(fabsf(route_distance[0] - initial_offset) < 0.00001f);
    assert(fabsf(route_distance[1] - initial_offset) < 0.00001f);
    assert(isfinite(progress[0]) && isfinite(progress[1]));

    /* Move both cursors to one metre before the same fork. */
    assert(course->advance_rival_route(course->runtime_context, 0U,
        distance_to_branch_window, -0.8f, route_distance[0],
        course->lap_distance, &next_route_distance[0], &next_progress[0]));
    route_distance[0] = next_route_distance[0];
    progress[0] = next_progress[0];
    assert(course->advance_rival_route(course->runtime_context, 1U,
        distance_to_branch_window, 0.8f, route_distance[1],
        course->lap_distance, &next_route_distance[1], &next_progress[1]));
    route_distance[1] = next_route_distance[1];
    progress[1] = next_progress[1];

    assert(context->rival_cursors[0].path_history[1] == 1U);
    assert(context->rival_cursors[1].path_history[1] == 2U);

    assert(course->sample_rival_route(course->runtime_context, 0U,
        route_distance[0], route_distance[0] + 2.0f,
        course->road_half_width, &left_x, &left_y, &left_z, &left_width) ==
        BOONTA_ROUTE_CURSOR_OK);
    assert(course->sample_rival_route(course->runtime_context, 1U,
        route_distance[1], route_distance[1] + 2.0f,
        course->road_half_width, &right_x, &right_y, &right_z, &right_width) ==
        BOONTA_ROUTE_CURSOR_OK);
    assert(left_x > right_x);
    assert(isfinite(left_width) && isfinite(right_width));

    /* Course-owned cursors independently traverse their chosen paths and rejoin. */
    assert(course->advance_rival_route(course->runtime_context, 0U,
        left_join_delta, 0.0f, route_distance[0],
        course->lap_distance, &next_route_distance[0], &next_progress[0]));
    assert(course->advance_rival_route(course->runtime_context, 1U,
        right_join_delta, 0.0f, route_distance[1],
        course->lap_distance, &next_route_distance[1], &next_progress[1]));
    assert(boonta_route_cursor_get_state(&context->rival_cursors[0],
        &left_state) == BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_get_state(&context->rival_cursors[1],
        &right_state) == BOONTA_ROUTE_CURSOR_OK);
    assert(left_state.edge == 5U && right_state.edge == 5U);
    assert(context->rival_cursors[0].path_history[1] == 1U);
    assert(context->rival_cursors[1].path_history[1] == 2U);
}

int main(void)
{
    test_synthetic_fork_geometry_is_connected();
    test_rivals_choose_left_and_right_then_rejoin();
    test_course_owned_rival_cursors_use_the_selected_graph();
    puts("Synthetic rival branching tests: PASS");
    return 0;
}
