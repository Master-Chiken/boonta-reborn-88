#define BOONTA_ROUTE_GRAPH_HEADER "../tests/fixtures/generated_branched_route_graph.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>

#include "../source/rival_ai.h"
#include "../source/route_graph_sampling.h"

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
        boonta_rival_route_branch_direction_from_steering(-0.8f, 0.2f);
    const int right_direction =
        boonta_rival_route_branch_direction_from_steering(0.8f, 0.2f);

    assert(BOONTA_RUNTIME_ROUTE_HAS_BRANCHES);
    assert(left_direction == -1);
    assert(right_direction == 1);
    assert(boonta_rival_route_branch_direction_from_steering(-0.2f, 0.2f) == 0);
    assert(boonta_rival_route_branch_direction_from_steering(0.2f, 0.2f) == 0);
    assert(boonta_rival_route_branch_direction_from_steering(NAN, 0.2f) == 0);
    assert(boonta_rival_route_branch_direction_from_steering(0.8f, NAN) == 0);

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

int main(void)
{
    test_synthetic_fork_geometry_is_connected();
    test_rivals_choose_left_and_right_then_rejoin();
    puts("Synthetic rival branching tests: PASS");
    return 0;
}
