#include <assert.h>
#include <math.h>
#include <stdio.h>

#include "../source/gameplay_state.h"
#include "../source/generated_track.h"
#include "../source/route_graph_sampling.h"

static BoontaRouteGraphSampler g_sampler;
static const BoontaRouteCursorGraph g_generated_route_cursor_graph = {
    boonta_runtime_route_topology_edges,
    BOONTA_RUNTIME_ROUTE_EDGE_COUNT,
    BOONTA_RUNTIME_ROUTE_NODE_COUNT,
    BOONTA_RUNTIME_ROUTE_START_NODE_INDEX,
    BOONTA_RUNTIME_ROUTE_CLOSED_LOOP
};

static void sample(float travelled, float *x, float *y, float *z, float *width)
{
    boonta_route_graph_sampler_sample_at(
        &g_sampler, travelled, BOONTA_REFERENCE_ROAD_HALF_WIDTH,
        x, y, z, width);
}

static void assert_close(float actual, float expected, float tolerance)
{
    if (!isfinite(actual) || fabsf(actual - expected) > tolerance) {
        fprintf(stderr,
                "assert_close failed: actual=%.9g expected=%.9g tolerance=%.9g\\n",
                (double)actual, (double)expected, (double)tolerance);
        assert(isfinite(actual));
        assert(fabsf(actual - expected) <= tolerance);
    }
}

static void test_route_length_matches_legacy_lap_distance(void)
{
    assert(boonta_route_graph_sampler_prepare(&g_sampler));
    assert(g_sampler.total_length == BOONTA_RUNTIME_ROUTE_LENGTH);
    assert(g_sampler.lengths_ready);
    assert(fabsf(BOONTA_RUNTIME_ROUTE_LENGTH - BOONTA_TRACK_LENGTH) /
           BOONTA_TRACK_LENGTH < 0.0002f);
}

static void test_every_edge_boundary_matches_its_authored_node(void)
{
    unsigned int edge;
    float travelled = 0.0f;

    assert(boonta_route_graph_sampler_prepare(&g_sampler));
    for (edge = 0U; edge < BOONTA_RUNTIME_ROUTE_EDGE_COUNT; ++edge) {
        const BoontaRuntimeRouteEdge *route_edge =
            &boonta_runtime_route_edges[edge];
        float x, y, z, width;
        travelled += g_sampler.edge_lengths[edge];
        sample(travelled, &x, &y, &z, &width);
        assert_close(x, route_edge->p3[0], 0.0002f);
        assert_close(y, route_edge->p3[1], 0.0002f);
        assert_close(z, route_edge->p3[2], 0.0002f);
        assert(isfinite(width));
        assert(width >= 3.2f && width <= 3.8f);
    }
}

static void test_every_bezier_join_has_continuous_tangent_and_width(void)
{
    unsigned int edge;

    for (edge = 0U; edge < BOONTA_RUNTIME_ROUTE_EDGE_COUNT; ++edge) {
        const unsigned int next =
            (edge + 1U) % BOONTA_RUNTIME_ROUTE_EDGE_COUNT;
        const BoontaRuntimeRouteEdge *incoming =
            &boonta_runtime_route_edges[edge];
        const BoontaRuntimeRouteEdge *outgoing =
            &boonta_runtime_route_edges[next];
        unsigned int axis;

        /*
         * A cubic Bezier's endpoint derivatives are 3*(P3-C2) and
         * 3*(C1-P0). Matching these vectors preserves C1 continuity at
         * every node, including the closed-loop seam.
         */
        for (axis = 0U; axis < 3U; ++axis) {
            const float incoming_tangent =
                3.0f * (incoming->p3[axis] - incoming->control2[axis]);
            const float outgoing_tangent =
                3.0f * (outgoing->control1[axis] - outgoing->p0[axis]);
            assert_close(incoming_tangent, outgoing_tangent, 0.00001f);
        }

        /* Width is a separate periodic surface signal and must meet at joins. */
        assert_close(
            boonta_route_graph_width_at(
                edge, 1.0f, BOONTA_REFERENCE_ROAD_HALF_WIDTH),
            boonta_route_graph_width_at(
                next, 0.0f, BOONTA_REFERENCE_ROAD_HALF_WIDTH),
            0.000001f);
    }
}

static void test_binary_search_boundaries_and_midpoints(void)
{
    unsigned int edge;

    assert(boonta_route_graph_sampler_prepare(&g_sampler));
    assert_close(g_sampler.edge_start_distances[0], 0.0f, 0.000001f);

    for (edge = 0U; edge < BOONTA_RUNTIME_ROUTE_EDGE_COUNT; ++edge) {
        const float edge_start = g_sampler.edge_start_distances[edge];
        unsigned int step;

        if (edge > 0U) {
            assert(edge_start > g_sampler.edge_start_distances[edge - 1U]);
            assert_close(
                edge_start,
                g_sampler.edge_start_distances[edge - 1U] +
                    g_sampler.edge_lengths[edge - 1U],
                0.00002f);
        }

        for (step = 0U;
             step <= BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS;
             ++step) {
            const float t = (float)step /
                (float)BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS;
            const float travelled = edge_start +
                g_sampler.distance_lut[edge][step];
            float expected_x, expected_y, expected_z;
            float actual_x, actual_y, actual_z;

            boonta_route_graph_evaluate_edge(
                edge, t, &expected_x, &expected_y, &expected_z);
            sample(travelled, &actual_x, &actual_y, &actual_z, NULL);
            assert_close(actual_x, expected_x, 0.00015f);
            assert_close(actual_y, expected_y, 0.00015f);
            assert_close(actual_z, expected_z, 0.00015f);

            if (step < BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS) {
                const float midpoint_distance = edge_start +
                    0.5f * (g_sampler.distance_lut[edge][step] +
                            g_sampler.distance_lut[edge][step + 1U]);
                const float midpoint_t = ((float)step + 0.5f) /
                    (float)BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS;

                boonta_route_graph_evaluate_edge(
                    edge, midpoint_t, &expected_x, &expected_y, &expected_z);
                sample(midpoint_distance, &actual_x, &actual_y, &actual_z, NULL);
                assert_close(actual_x, expected_x, 0.00015f);
                assert_close(actual_y, expected_y, 0.00015f);
                assert_close(actual_z, expected_z, 0.00015f);
            }
        }
    }

    assert_close(
        g_sampler.edge_start_distances[BOONTA_RUNTIME_ROUTE_EDGE_COUNT - 1U] +
            g_sampler.edge_lengths[BOONTA_RUNTIME_ROUTE_EDGE_COUNT - 1U],
        g_sampler.total_length,
        0.00002f);
}

static void test_bezier_samples_match_legacy_track_bake(void)
{
    unsigned int edge;
    for (edge = 0U; edge < BOONTA_RUNTIME_ROUTE_EDGE_COUNT; ++edge) {
        unsigned int sample_index;
        for (sample_index = 0U;
             sample_index < BOONTA_RUNTIME_ROUTE_WIDTH_SAMPLES_PER_EDGE;
             ++sample_index) {
            const unsigned int point_index =
                edge * BOONTA_RUNTIME_ROUTE_WIDTH_SAMPLES_PER_EDGE + sample_index;
            const float t = (float)sample_index /
                (float)BOONTA_RUNTIME_ROUTE_WIDTH_SAMPLES_PER_EDGE;
            const BoontaTrackPoint *legacy =
                &boonta_track_points_original_test_oval[point_index];
            float x, y, z;
            boonta_route_graph_evaluate_edge(edge, t, &x, &y, &z);
            assert_close(x, legacy->x, 0.0001f);
            assert_close(y, legacy->y, 0.0001f);
            assert_close(z, legacy->z, 0.0001f);
            assert_close(
                boonta_runtime_route_width_samples[point_index],
                legacy->half_width, 0.0001f);
        }
    }
}

static void test_closed_loop_wrap_and_negative_distance(void)
{
    float x0, y0, z0, w0;
    float x1, y1, z1, w1;
    float xn, yn, zn, wn;

    sample(0.0f, &x0, &y0, &z0, &w0);
    sample(BOONTA_RUNTIME_ROUTE_LENGTH, &x1, &y1, &z1, &w1);
    sample(-BOONTA_RUNTIME_ROUTE_LENGTH, &xn, &yn, &zn, &wn);
    assert_close(x1, x0, 0.00001f);
    assert_close(y1, y0, 0.00001f);
    assert_close(z1, z0, 0.00001f);
    assert_close(xn, x0, 0.00001f);
    assert_close(yn, y0, 0.00001f);
    assert_close(zn, z0, 0.00001f);
    assert_close(w1, w0, 0.00001f);
    assert_close(wn, w0, 0.00001f);
}

static void test_bezier_seam_tangent_is_continuous(void)
{
    float x0, y0, z0, w;
    float xf, yf, zf;
    float xb, yb, zb;

    sample(0.0f, &x0, &y0, &z0, &w);
    sample(0.01f, &xf, &yf, &zf, NULL);
    sample(BOONTA_RUNTIME_ROUTE_LENGTH - 0.01f, &xb, &yb, &zb, NULL);

    assert_close(xf - x0, x0 - xb, 0.0005f);
    assert_close(yf - y0, y0 - yb, 0.0005f);
    assert_close(zf - z0, z0 - zb, 0.0005f);
}

static void test_dense_runtime_curve_length_matches_lap_coordinate(void)
{
    const unsigned int subdivisions = 16384U;
    unsigned int index;
    float previous_x, previous_y, previous_z, width;
    float measured_length = 0.0f;

    sample(0.0f, &previous_x, &previous_y, &previous_z, &width);
    for (index = 1U; index <= subdivisions; ++index) {
        const float travelled = BOONTA_RUNTIME_ROUTE_LENGTH *
            (float)index / (float)subdivisions;
        float x, y, z;
        float dx, dy, dz;

        sample(travelled, &x, &y, &z, &width);
        dx = x - previous_x;
        dy = y - previous_y;
        dz = z - previous_z;
        measured_length += sqrtf(dx * dx + dy * dy + dz * dz);
        previous_x = x;
        previous_y = y;
        previous_z = z;
    }

    {
        const float relative_error =
            fabsf(measured_length - BOONTA_RUNTIME_ROUTE_LENGTH) /
            BOONTA_RUNTIME_ROUTE_LENGTH;
        printf("Native route-graph Bezier length: %.6f m; "
               "lap coordinate: %.6f m; difference: %.5f%%\n",
               measured_length, BOONTA_RUNTIME_ROUTE_LENGTH,
               relative_error * 100.0f);
        assert(relative_error < 0.0002f);
    }
}

static void test_curve_evaluator_rejects_invalid_queries(void)
{
    float x = 9.0f, y = 9.0f, z = 9.0f;

    boonta_route_graph_evaluate_edge(
        BOONTA_RUNTIME_ROUTE_EDGE_COUNT, 0.5f, &x, &y, &z);
    assert(x == 0.0f && y == 0.0f && z == 0.0f);

    x = 9.0f; y = 9.0f; z = 9.0f;
    boonta_route_graph_evaluate_edge(0U, NAN, &x, &y, &z);
    assert(x == 0.0f && y == 0.0f && z == 0.0f);

    x = 9.0f; y = 9.0f; z = 9.0f;
    boonta_route_graph_evaluate_edge(0U, INFINITY, &x, &y, &z);
    assert(x == 0.0f && y == 0.0f && z == 0.0f);
}

static void test_curve_evaluator_clamps_finite_t(void)
{
    float start_x, start_y, start_z;
    float end_x, end_y, end_z;
    float actual_x, actual_y, actual_z;

    boonta_route_graph_evaluate_edge(0U, 0.0f, &start_x, &start_y, &start_z);
    boonta_route_graph_evaluate_edge(0U, 1.0f, &end_x, &end_y, &end_z);

    boonta_route_graph_evaluate_edge(0U, -1.0f, &actual_x, &actual_y, &actual_z);
    assert_close(actual_x, start_x, 0.000001f);
    assert_close(actual_y, start_y, 0.000001f);
    assert_close(actual_z, start_z, 0.000001f);

    boonta_route_graph_evaluate_edge(0U, 2.0f, &actual_x, &actual_y, &actual_z);
    assert_close(actual_x, end_x, 0.000001f);
    assert_close(actual_y, end_y, 0.000001f);
    assert_close(actual_z, end_z, 0.000001f);
}

static void test_width_sampler_rejects_invalid_queries_and_clamps_t(void)
{
    const float fallback = 99.0f;
    const float width_start = boonta_route_graph_width_at(0U, 0.0f, fallback);
    const float width_end = boonta_route_graph_width_at(0U, 1.0f, fallback);

    assert_close(boonta_route_graph_width_at(
        BOONTA_RUNTIME_ROUTE_EDGE_COUNT, 0.5f, fallback), fallback, 0.0f);
    assert_close(boonta_route_graph_width_at(0U, NAN, fallback), fallback, 0.0f);
    assert_close(boonta_route_graph_width_at(0U, INFINITY, fallback), fallback, 0.0f);
    assert_close(boonta_route_graph_width_at(0U, -1.0f, fallback), width_start, 0.000001f);
    assert_close(boonta_route_graph_width_at(0U, 2.0f, fallback), width_end, 0.000001f);
}

static void test_edge_local_sampling_matches_loop_positions(void)
{
    unsigned int edge;

    assert(boonta_route_graph_sampler_prepare(&g_sampler));
    for (edge = 0U; edge < BOONTA_RUNTIME_ROUTE_EDGE_COUNT; ++edge) {
        const float edge_length = g_sampler.edge_lengths[edge];
        const float local_distances[3] = {
            0.0f, edge_length * 0.5f, edge_length
        };
        unsigned int sample_index;

        for (sample_index = 0U; sample_index < 3U; ++sample_index) {
            const float local_distance = local_distances[sample_index];
            const float global_distance =
                g_sampler.edge_start_distances[edge] + local_distance;
            float local_x, local_y, local_z, local_width;
            float loop_x, loop_y, loop_z, loop_width;

            boonta_route_graph_sampler_sample_edge_at(
                &g_sampler, edge, local_distance,
                BOONTA_REFERENCE_ROAD_HALF_WIDTH,
                &local_x, &local_y, &local_z, &local_width);
            sample(global_distance, &loop_x, &loop_y, &loop_z, &loop_width);

            assert_close(local_x, loop_x, 0.0002f);
            assert_close(local_y, loop_y, 0.0002f);
            assert_close(local_z, loop_z, 0.0002f);
            assert_close(local_width, loop_width, 0.0002f);
        }
    }
}

static void test_edge_local_sampling_clamps_and_rejects_invalid_queries(void)
{
    float start_x, start_y, start_z, start_width;
    float end_x, end_y, end_z, end_width;
    float actual_x, actual_y, actual_z, actual_width;
    const float fallback = 99.0f;
    const unsigned int edge = 0U;

    assert(boonta_route_graph_sampler_prepare(&g_sampler));
    boonta_route_graph_evaluate_edge(edge, 0.0f, &start_x, &start_y, &start_z);
    boonta_route_graph_evaluate_edge(edge, 1.0f, &end_x, &end_y, &end_z);
    start_width = boonta_route_graph_width_at(edge, 0.0f, fallback);
    end_width = boonta_route_graph_width_at(edge, 1.0f, fallback);

    boonta_route_graph_sampler_sample_edge_at(
        &g_sampler, edge, -1.0f, fallback,
        &actual_x, &actual_y, &actual_z, &actual_width);
    assert_close(actual_x, start_x, 0.000001f);
    assert_close(actual_y, start_y, 0.000001f);
    assert_close(actual_z, start_z, 0.000001f);
    assert_close(actual_width, start_width, 0.000001f);

    boonta_route_graph_sampler_sample_edge_at(
        &g_sampler, edge, g_sampler.edge_lengths[edge] + 1.0f, fallback,
        &actual_x, &actual_y, &actual_z, &actual_width);
    assert_close(actual_x, end_x, 0.000001f);
    assert_close(actual_y, end_y, 0.000001f);
    assert_close(actual_z, end_z, 0.000001f);
    assert_close(actual_width, end_width, 0.000001f);

    actual_x = 9.0f; actual_y = 9.0f; actual_z = 9.0f; actual_width = 0.0f;
    boonta_route_graph_sampler_sample_edge_at(
        &g_sampler, BOONTA_RUNTIME_ROUTE_EDGE_COUNT, 0.5f, fallback,
        &actual_x, &actual_y, &actual_z, &actual_width);
    assert(actual_x == 0.0f && actual_y == 0.0f && actual_z == 0.0f);
    assert(actual_width == fallback);

    actual_x = 9.0f; actual_y = 9.0f; actual_z = 9.0f; actual_width = 0.0f;
    boonta_route_graph_sampler_sample_edge_at(
        &g_sampler, edge, NAN, fallback,
        &actual_x, &actual_y, &actual_z, &actual_width);
    assert(actual_x == 0.0f && actual_y == 0.0f && actual_z == 0.0f);
    assert(actual_width == fallback);
}

static void test_generated_topology_cursor_uses_edge_sampler(void)
{
    BoontaRouteCursor cursor;
    BoontaRouteCursorState state;
    float cursor_x, cursor_y, cursor_z, cursor_width;
    float loop_x, loop_y, loop_z, loop_width;
    const float offset = 0.05f;

    assert(boonta_route_graph_sampler_prepare(&g_sampler));
    assert(g_generated_route_cursor_graph.edge_count ==
           BOONTA_RUNTIME_ROUTE_EDGE_COUNT);
    assert(g_generated_route_cursor_graph.node_count ==
           BOONTA_RUNTIME_ROUTE_NODE_COUNT);
    assert(g_generated_route_cursor_graph.closed_loop == 1);
    assert(boonta_route_cursor_init(
        &cursor, &g_generated_route_cursor_graph,
        g_sampler.edge_lengths, BOONTA_RUNTIME_ROUTE_EDGE_COUNT - 1U) ==
        BOONTA_ROUTE_CURSOR_INVALID);
    assert(boonta_route_cursor_init(
        &cursor, &g_generated_route_cursor_graph,
        g_sampler.edge_lengths, BOONTA_RUNTIME_ROUTE_START_NODE_INDEX) ==
        BOONTA_ROUTE_CURSOR_OK);

    /* Walk one complete generated lap and a small distance into the next. */
    assert(boonta_route_cursor_move(
        &cursor, g_sampler.total_length + offset, NULL, 0U) ==
        BOONTA_ROUTE_CURSOR_OK);
    state = (BoontaRouteCursorState){0};
    assert(boonta_route_cursor_get_state(&cursor, &state) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(state.edge == BOONTA_RUNTIME_ROUTE_START_NODE_INDEX);
    assert(state.path_index == BOONTA_RUNTIME_ROUTE_EDGE_COUNT);
    assert(state.history_count == BOONTA_RUNTIME_ROUTE_EDGE_COUNT + 1U);
    assert(!state.finished);
    boonta_route_graph_sampler_sample_edge_at(
        &g_sampler, state.edge, cursor.distance_on_edge,
        BOONTA_REFERENCE_ROAD_HALF_WIDTH,
        &cursor_x, &cursor_y, &cursor_z, &cursor_width);
    sample(g_sampler.total_length + offset,
           &loop_x, &loop_y, &loop_z, &loop_width);
    assert_close(cursor_x, loop_x, 0.0002f);
    assert_close(cursor_y, loop_y, 0.0002f);
    assert_close(cursor_z, loop_z, 0.0002f);
    assert_close(cursor_width, loop_width, 0.0002f);

    /* Reverse across the seam, then replay the cached start edge. */
    assert(boonta_route_cursor_move(&cursor, -0.1f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    state = (BoontaRouteCursorState){0};
    assert(boonta_route_cursor_get_state(&cursor, &state) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(state.edge == BOONTA_RUNTIME_ROUTE_EDGE_COUNT - 1U);
    assert(state.path_index == BOONTA_RUNTIME_ROUTE_EDGE_COUNT - 1U);

    assert(boonta_route_cursor_move(&cursor, 0.1f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    state = (BoontaRouteCursorState){0};
    assert(boonta_route_cursor_get_state(&cursor, &state) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(state.edge == BOONTA_RUNTIME_ROUTE_START_NODE_INDEX);
    assert_close(cursor.distance_on_edge, offset, 0.00002f);
}

static void test_nonfinite_distance_returns_safe_defaults(void)
{
    float x = 9.0f, y = 9.0f, z = 9.0f, width = 0.0f;
    sample(NAN, &x, &y, &z, &width);
    assert(x == 0.0f && y == 0.0f && z == 0.0f);
    assert(width == BOONTA_REFERENCE_ROAD_HALF_WIDTH);
}

int main(void)
{
    fprintf(stderr, "[route-test] test_route_length_matches_legacy_lap_distance\n");
    test_route_length_matches_legacy_lap_distance();
    fprintf(stderr, "[route-test] test_every_edge_boundary_matches_its_authored_node\n");
    test_every_edge_boundary_matches_its_authored_node();
    fprintf(stderr, "[route-test] test_every_bezier_join_has_continuous_tangent_and_width\n");
    test_every_bezier_join_has_continuous_tangent_and_width();
    fprintf(stderr, "[route-test] test_binary_search_boundaries_and_midpoints\n");
    test_binary_search_boundaries_and_midpoints();
    fprintf(stderr, "[route-test] test_bezier_samples_match_legacy_track_bake\n");
    test_bezier_samples_match_legacy_track_bake();
    fprintf(stderr, "[route-test] test_closed_loop_wrap_and_negative_distance\n");
    test_closed_loop_wrap_and_negative_distance();
    fprintf(stderr, "[route-test] test_bezier_seam_tangent_is_continuous\n");
    test_bezier_seam_tangent_is_continuous();
    fprintf(stderr, "[route-test] test_dense_runtime_curve_length_matches_lap_coordinate\n");
    test_dense_runtime_curve_length_matches_lap_coordinate();
    fprintf(stderr, "[route-test] test_curve_evaluator_rejects_invalid_queries\n");
    test_curve_evaluator_rejects_invalid_queries();
    fprintf(stderr, "[route-test] test_curve_evaluator_clamps_finite_t\n");
    test_curve_evaluator_clamps_finite_t();
    fprintf(stderr, "[route-test] test_width_sampler_rejects_invalid_queries_and_clamps_t\n");
    test_width_sampler_rejects_invalid_queries_and_clamps_t();
    fprintf(stderr, "[route-test] test_edge_local_sampling_matches_loop_positions\n");
    test_edge_local_sampling_matches_loop_positions();
    fprintf(stderr, "[route-test] test_edge_local_sampling_clamps_and_rejects_invalid_queries\n");
    test_edge_local_sampling_clamps_and_rejects_invalid_queries();
    fprintf(stderr, "[route-test] test_generated_topology_cursor_uses_edge_sampler\n");
    test_generated_topology_cursor_uses_edge_sampler();
    fprintf(stderr, "[route-test] test_nonfinite_distance_returns_safe_defaults\n");
    test_nonfinite_distance_returns_safe_defaults();
    puts("Native route-graph sampler C tests passed.");
    return 0;
}
