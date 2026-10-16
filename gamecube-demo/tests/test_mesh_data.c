#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "../source/mesh_data.h"
#include "mesh_fixture.h"

static BoontaMeshVertex max_vertices[BOONTA_MESH_MAX_VERTICES];
static uint16_t max_indices[BOONTA_MESH_MAX_INDICES];

static void test_valid_fixture(void)
{
    BoontaMeshView mesh = boonta_test_triangle();

    assert(boonta_mesh_validate(&mesh) == BOONTA_MESH_VALID);
}

static void test_invalid_arguments_and_counts(void)
{
    BoontaMeshView mesh = boonta_test_triangle();

    assert(boonta_mesh_validate(NULL) == BOONTA_MESH_INVALID_ARGUMENT);

    mesh.vertices = NULL;
    assert(boonta_mesh_validate(&mesh) == BOONTA_MESH_INVALID_ARGUMENT);
    mesh = boonta_test_triangle();
    mesh.indices = NULL;
    assert(boonta_mesh_validate(&mesh) == BOONTA_MESH_INVALID_ARGUMENT);

    mesh = boonta_test_triangle();
    mesh.vertex_count = 0U;
    assert(boonta_mesh_validate(&mesh) == BOONTA_MESH_INVALID_COUNTS);

    mesh = boonta_test_triangle();
    mesh.vertex_count = BOONTA_MESH_MAX_VERTICES + 1U;
    mesh.vertex_bytes = (size_t)-1;
    assert(boonta_mesh_validate(&mesh) == BOONTA_MESH_INVALID_COUNTS);

    mesh = boonta_test_triangle();
    mesh.index_count = 0U;
    assert(boonta_mesh_validate(&mesh) == BOONTA_MESH_INVALID_COUNTS);

    mesh = boonta_test_triangle();
    mesh.index_count = 4U;
    mesh.index_bytes = 4U * sizeof(uint16_t);
    assert(boonta_mesh_validate(&mesh) == BOONTA_MESH_INVALID_COUNTS);

    mesh = boonta_test_triangle();
    mesh.index_count = BOONTA_MESH_MAX_INDICES + 1U;
    mesh.index_bytes = (size_t)-1;
    assert(boonta_mesh_validate(&mesh) == BOONTA_MESH_INVALID_COUNTS);
}

static void test_truncated_views_and_size_overflow(void)
{
    BoontaMeshView mesh = boonta_test_triangle();
    size_t bytes = 123U;

    mesh.vertex_bytes--;
    assert(boonta_mesh_validate(&mesh) == BOONTA_MESH_TRUNCATED_DATA);

    mesh = boonta_test_triangle();
    mesh.index_bytes--;
    assert(boonta_mesh_validate(&mesh) == BOONTA_MESH_TRUNCATED_DATA);

    assert(boonta_mesh_size_bytes(3U, sizeof(BoontaMeshVertex), &bytes));
    assert(bytes == 3U * sizeof(BoontaMeshVertex));

    bytes = 123U;
    assert(!boonta_mesh_size_bytes((size_t)-1, 2U, &bytes));
    assert(bytes == 123U);

    assert(!boonta_mesh_size_bytes(1U, 0U, &bytes));
    assert(!boonta_mesh_size_bytes(1U, sizeof(uint16_t), NULL));
}

static void test_nonfinite_positions(void)
{
    BoontaMeshView mesh = boonta_test_triangle();
    BoontaMeshVertex vertices[3];

    memcpy(vertices, boonta_test_triangle_vertices, sizeof(vertices));
    vertices[1].x = NAN;
    mesh.vertices = vertices;
    assert(boonta_mesh_validate(&mesh) == BOONTA_MESH_NONFINITE_POSITION);

    memcpy(vertices, boonta_test_triangle_vertices, sizeof(vertices));
    vertices[1].y = INFINITY;
    mesh.vertices = vertices;
    assert(boonta_mesh_validate(&mesh) == BOONTA_MESH_NONFINITE_POSITION);

    memcpy(vertices, boonta_test_triangle_vertices, sizeof(vertices));
    vertices[2].z = -INFINITY;
    mesh.vertices = vertices;
    assert(boonta_mesh_validate(&mesh) == BOONTA_MESH_NONFINITE_POSITION);
}

static void test_invalid_indices_and_degenerate_triangles(void)
{
    BoontaMeshView mesh = boonta_test_triangle();
    uint16_t indices[3] = { 0U, 1U, 3U };
    BoontaMeshVertex vertices[3];

    mesh.indices = indices;
    assert(boonta_mesh_validate(&mesh) == BOONTA_MESH_INVALID_INDEX);

    memcpy(vertices, boonta_test_triangle_vertices, sizeof(vertices));
    vertices[2] = vertices[1];
    mesh = boonta_test_triangle();
    mesh.vertices = vertices;
    assert(boonta_mesh_validate(&mesh) == BOONTA_MESH_DEGENERATE_TRIANGLE);
}

static void test_maximum_accepted_counts(void)
{
    size_t i;
    BoontaMeshView mesh;

    for (i = 0U; i < BOONTA_MESH_MAX_VERTICES; ++i) {
        const size_t corner = i % 3U;
        max_vertices[i].x = (float)((i / 3U) * 2U) +
                            (corner == 1U ? 1.0f : 0.0f);
        max_vertices[i].y = corner == 2U ? 1.0f : 0.0f;
        max_vertices[i].z = 0.0f;
        max_vertices[i].r = 255U;
        max_vertices[i].g = 255U;
        max_vertices[i].b = 255U;
        max_vertices[i].a = 255U;
    }

    /* 4095 is the largest index count divisible by three under the 4096 cap. */
    for (i = 0U; i < BOONTA_MESH_MAX_INDICES; i += 3U) {
        max_indices[i] = (uint16_t)i;
        max_indices[i + 1U] = (uint16_t)(i + 1U);
        max_indices[i + 2U] = (uint16_t)(i + 2U);
    }

    mesh.vertices = max_vertices;
    mesh.vertex_count = BOONTA_MESH_MAX_VERTICES;
    mesh.vertex_bytes = sizeof(max_vertices);
    mesh.indices = max_indices;
    mesh.index_count = BOONTA_MESH_MAX_INDICES;
    mesh.index_bytes = sizeof(max_indices);

    assert(boonta_mesh_validate(&mesh) == BOONTA_MESH_VALID);
}

int main(void)
{
    test_valid_fixture();
    test_invalid_arguments_and_counts();
    test_truncated_views_and_size_overflow();
    test_nonfinite_positions();
    test_invalid_indices_and_degenerate_triangles();
    test_maximum_accepted_counts();
    puts("mesh-data tests passed");
    return 0;
}
