#ifndef BOONTA_TEST_MESH_FIXTURE_H
#define BOONTA_TEST_MESH_FIXTURE_H

#include "../source/mesh_data.h"

/* Original test-only triangle; no game-derived geometry or assets. */
static const BoontaMeshVertex boonta_test_triangle_vertices[3] = {
    { 0.0f, 0.0f, 0.0f, 255U, 40U, 40U, 255U },
    { 1.0f, 0.0f, 0.0f, 40U, 255U, 40U, 255U },
    { 0.0f, 1.0f, 0.0f, 40U, 40U, 255U, 255U }
};
static const uint16_t boonta_test_triangle_indices[3] = { 0U, 1U, 2U };

static inline BoontaMeshView boonta_test_triangle(void)
{
    const BoontaMeshView mesh = {
        boonta_test_triangle_vertices,
        3U,
        sizeof(boonta_test_triangle_vertices),
        boonta_test_triangle_indices,
        3U,
        sizeof(boonta_test_triangle_indices)
    };
    return mesh;
}

#endif
