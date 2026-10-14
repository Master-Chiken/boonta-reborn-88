#include "collision_mesh.h"
#include <stdio.h>
#include <string.h>

#define FIXTURE_SIZE (COLLISION_MESH_SWC1_HEADER_SIZE + 2U * COLLISION_MESH_SWC1_TRIANGLE_SIZE)
#define CHECK(expr) do { if (!(expr)) { \
    fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #expr); return 1; \
} } while (0)

static void put_u16_be(unsigned char *p, unsigned int v)
{
    p[0] = (unsigned char)((v >> 8) & 0xffU);
    p[1] = (unsigned char)(v & 0xffU);
}

static void put_u32_be(unsigned char *p, unsigned long v)
{
    p[0] = (unsigned char)((v >> 24) & 0xffUL);
    p[1] = (unsigned char)((v >> 16) & 0xffUL);
    p[2] = (unsigned char)((v >> 8) & 0xffUL);
    p[3] = (unsigned char)(v & 0xffUL);
}

static void put_i16_be(unsigned char *p, int value)
{
    put_u16_be(p, (unsigned int)value & 0xffffU);
}

static void put_vertex(unsigned char *p, int x, int y, int z)
{
    put_i16_be(p, x);
    put_i16_be(p + 2U, y);
    put_i16_be(p + 4U, z);
}

static void make_fixture(unsigned char bytes[FIXTURE_SIZE])
{
    unsigned int i;
    memset(bytes, 0, FIXTURE_SIZE);
    memcpy(bytes, "SWC1", 4U);
    put_u32_be(bytes + 4U, 2UL);
    /* x bounds [-10, 10], y [0, 4], z [-20, 20] */
    put_i16_be(bytes + 8U, -10); put_i16_be(bytes + 10U, 10);
    put_i16_be(bytes + 12U, 0);  put_i16_be(bytes + 14U, 4);
    put_i16_be(bytes + 16U, -20); put_i16_be(bytes + 18U, 20);
    for (i = 0U; i < 2U; ++i) {
        unsigned char *tri = bytes + COLLISION_MESH_SWC1_HEADER_SIZE +
                             i * COLLISION_MESH_SWC1_TRIANGLE_SIZE;
        put_vertex(tri, -10, 0, -20);
        put_vertex(tri + 6U, 10, 4, 20);
        put_vertex(tri + 12U, 0, 2, 0);
    }
}

int main(void)
{
    unsigned char fixture[FIXTURE_SIZE];
    unsigned char mutated[FIXTURE_SIZE + 1U];
    CollisionMeshView view;
    CollisionMeshTriangle tri;

    make_fixture(fixture);
    CHECK(collision_mesh_swc1_open(fixture, sizeof(fixture), &view) == COLLISION_MESH_OK);
    CHECK(view.triangle_count == 2U);
    CHECK(view.min[0] == -10 && view.max[0] == 10);
    CHECK(view.min[1] == 0 && view.max[1] == 4);
    CHECK(view.min[2] == -20 && view.max[2] == 20);
    CHECK(view.bytes == fixture);
    CHECK(collision_mesh_swc1_get_triangle(&view, 1U, &tri) == COLLISION_MESH_OK);
    CHECK(tri.vertex[0].x == -10 && tri.vertex[0].y == 0 && tri.vertex[0].z == -20);
    CHECK(tri.vertex[1].x == 10 && tri.vertex[1].y == 4 && tri.vertex[1].z == 20);
    CHECK(tri.vertex[2].x == 0 && tri.vertex[2].y == 2 && tri.vertex[2].z == 0);
    CHECK(collision_mesh_swc1_get_triangle(&view, 2U, &tri) == COLLISION_MESH_BAD_INDEX);
    CHECK(collision_mesh_swc1_open(NULL, sizeof(fixture), &view) == COLLISION_MESH_INVALID_ARGUMENT);
    CHECK(collision_mesh_swc1_open(fixture, sizeof(fixture), NULL) == COLLISION_MESH_INVALID_ARGUMENT);
    CHECK(collision_mesh_swc1_open(fixture, 0U, &view) == COLLISION_MESH_BAD_SIZE);

    memcpy(mutated, fixture, sizeof(fixture));
    mutated[0] = 'X';
    CHECK(collision_mesh_swc1_open(mutated, sizeof(fixture), &view) == COLLISION_MESH_BAD_MAGIC);
    memcpy(mutated, fixture, sizeof(fixture));
    put_u32_be(mutated + 4U, 0UL);
    CHECK(collision_mesh_swc1_open(mutated, sizeof(fixture), &view) == COLLISION_MESH_BAD_HEADER);
    memcpy(mutated, fixture, sizeof(fixture));
    put_u32_be(mutated + 4U, 3UL); /* count does not match the two records */
    CHECK(collision_mesh_swc1_open(mutated, sizeof(fixture), &view) == COLLISION_MESH_BAD_SIZE);
    memcpy(mutated, fixture, sizeof(fixture));
    mutated[20] = 1U;
    CHECK(collision_mesh_swc1_open(mutated, sizeof(fixture), &view) == COLLISION_MESH_BAD_HEADER);
    memcpy(mutated, fixture, sizeof(fixture));
    put_i16_be(mutated + 8U, 11); /* minX > maxX */
    CHECK(collision_mesh_swc1_open(mutated, sizeof(fixture), &view) == COLLISION_MESH_BAD_HEADER);
    memcpy(mutated, fixture, sizeof(fixture));
    put_vertex(mutated + COLLISION_MESH_SWC1_HEADER_SIZE, 11, 0, 0);
    CHECK(collision_mesh_swc1_open(mutated, sizeof(fixture), &view) == COLLISION_MESH_BAD_VERTEX);
    memcpy(mutated, fixture, sizeof(fixture));
    CHECK(collision_mesh_swc1_open(mutated, sizeof(fixture) - 1U, &view) == COLLISION_MESH_BAD_SIZE);
    memcpy(mutated, fixture, sizeof(fixture));
    mutated[sizeof(fixture)] = 0U;
    CHECK(collision_mesh_swc1_open(mutated, sizeof(mutated), &view) == COLLISION_MESH_BAD_SIZE);

    puts("PASS: SWC1 zero-copy open, signed big-endian vertices, bounds, index access, malformed headers, reserved bytes, truncation and trailing-data rejection");
    return 0;
}
