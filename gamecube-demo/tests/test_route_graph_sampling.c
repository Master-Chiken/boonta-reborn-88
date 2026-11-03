#include <assert.h>
#include <math.h>
#include <stdio.h>

#include "../source/gameplay_state.h"
#include "../source/generated_track.h"
#include "../source/route_graph_sampling.h"

static BoontaRouteGraphSampler g_sampler;

static void sample(float travelled, float *x, float *y, float *z, float *width)
{
    boonta_route_graph_sampler_sample_at(
        &g_sampler, travelled, BOONTA_REFERENCE_ROAD_HALF_WIDTH,
        x, y, z, width);
}

static void assert_close(float actual, float expected, float tolerance)
{
    assert(isfinite(actual));
    assert(fabsf(actual - expected) <= tolerance);
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

static void test_nonfinite_distance_returns_safe_defaults(void)
{
    float x = 9.0f, y = 9.0f, z = 9.0f, width = 0.0f;
    sample(NAN, &x, &y, &z, &width);
    assert(x == 0.0f && y == 0.0f && z == 0.0f);
    assert(width == BOONTA_REFERENCE_ROAD_HALF_WIDTH);
}

int main(void)
{
    test_route_length_matches_legacy_lap_distance();
    test_every_edge_boundary_matches_its_authored_node();
    test_every_bezier_join_has_continuous_tangent_and_width();
    test_binary_search_boundaries_and_midpoints();
    test_bezier_samples_match_legacy_track_bake();
    test_closed_loop_wrap_and_negative_distance();
    test_bezier_seam_tangent_is_continuous();
    test_dense_runtime_curve_length_matches_lap_coordinate();
    test_nonfinite_distance_returns_safe_defaults();
    puts("Native route-graph sampler C tests passed.");
    return 0;
}
