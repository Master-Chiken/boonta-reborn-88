#include <assert.h>
#include <math.h>
#include <stdio.h>

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
    test_closed_loop_wrap_and_negative_distance();
    test_bezier_seam_tangent_is_continuous();
    test_dense_runtime_curve_length_matches_lap_coordinate();
    test_nonfinite_distance_returns_safe_defaults();
    puts("Native route-graph sampler C tests passed.");
    return 0;
}
