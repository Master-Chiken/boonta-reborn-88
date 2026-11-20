/* Synthetic, geometrically connected fork/rejoin course for host tests. */
#ifndef BOONTA_TEST_GENERATED_BRANCHED_ROUTE_GRAPH_H
#define BOONTA_TEST_GENERATED_BRANCHED_ROUTE_GRAPH_H

#include "../../source/route_cursor.h"

#define BOONTA_RUNTIME_ROUTE_NODE_COUNT 6U
#define BOONTA_RUNTIME_ROUTE_EDGE_COUNT 7U
#define BOONTA_RUNTIME_ROUTE_START_NODE_INDEX 0U
#define BOONTA_RUNTIME_ROUTE_CLOSED_LOOP 1
#define BOONTA_RUNTIME_ROUTE_HAS_BRANCHES 1
#define BOONTA_RUNTIME_ROUTE_IS_SINGLE_LOOP 0
#define BOONTA_RUNTIME_ROUTE_DISTANCE_SUBDIVISIONS 64U
#define BOONTA_RUNTIME_ROUTE_WIDTH_SAMPLES_PER_EDGE 4U
#define BOONTA_RUNTIME_ROUTE_WIDTH_SAMPLE_COUNT \
    (BOONTA_RUNTIME_ROUTE_EDGE_COUNT * BOONTA_RUNTIME_ROUTE_WIDTH_SAMPLES_PER_EDGE)
#define BOONTA_RUNTIME_ROUTE_LENGTH 70.0f

typedef struct {
    float p0[3];
    float control1[3];
    float control2[3];
    float p3[3];
} BoontaRuntimeRouteEdge;

static const BoontaRouteCursorEdge boonta_runtime_route_topology_edges[
    BOONTA_RUNTIME_ROUTE_EDGE_COUNT] = {
    { 0U, 1U, 0.000f, 0.250f }, /* shared approach */
    { 1U, 2U, 0.250f, 0.500f }, /* left branch */
    { 1U, 3U, 0.250f, 0.500f }, /* right branch */
    { 2U, 4U, 0.500f, 0.750f }, /* left return */
    { 3U, 4U, 0.500f, 0.750f }, /* right return */
    { 4U, 5U, 0.750f, 0.850f }, /* shared exit */
    { 5U, 0U, 0.850f, 1.000f }  /* return to start */
};

/*
 * The two branch curves leave the same junction and both returns meet at the
 * same merge. Cubic endpoints and endpoint tangents are intentionally matched
 * at every non-fork join.
 */
static const BoontaRuntimeRouteEdge boonta_runtime_route_edges[
    BOONTA_RUNTIME_ROUTE_EDGE_COUNT] = {
    /* approach: (0,0,0) -> (0,0,10) */
    { { 0.0f, 0.0f, 0.0f }, { 0.0f, 0.0f, 3.0f },
      { 0.0f, 0.0f, 7.0f }, { 0.0f, 0.0f, 10.0f } },
    /* left: (0,0,10) -> (4,0,18) */
    { { 0.0f, 0.0f, 10.0f }, { 1.0f, 0.0f, 13.0f },
      { 3.0f, 0.0f, 16.0f }, { 4.0f, 0.0f, 18.0f } },
    /* right: (0,0,10) -> (-4,0,18) */
    { { 0.0f, 0.0f, 10.0f }, { -1.0f, 0.0f, 13.0f },
      { -3.0f, 0.0f, 16.0f }, { -4.0f, 0.0f, 18.0f } },
    /* left return: (4,0,18) -> (0,0,26) */
    { { 4.0f, 0.0f, 18.0f }, { 5.0f, 0.0f, 20.0f },
      { 0.0f, 0.0f, 23.0f }, { 0.0f, 0.0f, 26.0f } },
    /* right return: (-4,0,18) -> (0,0,26) */
    { { -4.0f, 0.0f, 18.0f }, { -5.0f, 0.0f, 20.0f },
      { 0.0f, 0.0f, 23.0f }, { 0.0f, 0.0f, 26.0f } },
    /* shared exit: (0,0,26) -> (0,0,36) */
    { { 0.0f, 0.0f, 26.0f }, { 0.0f, 0.0f, 29.0f },
      { 0.0f, 0.0f, 33.0f }, { 0.0f, 0.0f, 36.0f } },
    /* broad return to start; endpoint tangent agrees with the approach */
    { { 0.0f, 0.0f, 36.0f }, { 0.0f, 0.0f, 39.0f },
      { 0.0f, 0.0f, -3.0f }, { 0.0f, 0.0f, 0.0f } }
};

static const float boonta_runtime_route_width_samples[
    BOONTA_RUNTIME_ROUTE_WIDTH_SAMPLE_COUNT] = {
    3.5f, 3.5f, 3.5f, 3.5f, 3.5f, 3.5f, 3.5f, 3.5f,
    3.5f, 3.5f, 3.5f, 3.5f, 3.5f, 3.5f, 3.5f, 3.5f,
    3.5f, 3.5f, 3.5f, 3.5f, 3.5f, 3.5f, 3.5f, 3.5f,
    3.5f, 3.5f, 3.5f, 3.5f
};

static const float boonta_runtime_route_width_end_samples[
    BOONTA_RUNTIME_ROUTE_EDGE_COUNT] = {
    3.5f, 3.5f, 3.5f, 3.5f, 3.5f, 3.5f, 3.5f
};

#endif
