/* Strict, allocation-free reader for the SWC1 collision-triangle format. */
#include "collision_mesh.h"
#include <string.h>

static uint16_t read_u16_be(const unsigned char *p)
{
    return (uint16_t)(((uint16_t)p[0] << 8) | (uint16_t)p[1]);
}

static int16_t read_i16_be(const unsigned char *p)
{
    uint32_t value = read_u16_be(p);
    int32_t signed_value = value <= 0x7fffU ? (int32_t)value : (int32_t)value - 0x10000L;
    return (int16_t)signed_value;
}

static uint32_t read_u32_be(const unsigned char *p)
{
    return ((uint32_t)p[0] << 24) |
           ((uint32_t)p[1] << 16) |
           ((uint32_t)p[2] << 8) |
           (uint32_t)p[3];
}

static CollisionMeshVertex read_vertex(const unsigned char *p)
{
    CollisionMeshVertex v;
    v.x = read_i16_be(p);
    v.y = read_i16_be(p + 2U);
    v.z = read_i16_be(p + 4U);
    return v;
}

static int vertex_inside_bounds(const CollisionMeshVertex *v,
                                const int16_t min[3], const int16_t max[3])
{
    return v->x >= min[0] && v->x <= max[0] &&
           v->y >= min[1] && v->y <= max[1] &&
           v->z >= min[2] && v->z <= max[2];
}

CollisionMeshResult collision_mesh_swc1_open(const void *data, size_t size_bytes,
                                              CollisionMeshView *out_view)
{
    const unsigned char *bytes = (const unsigned char *)data;
    CollisionMeshView candidate;
    uint32_t i;
    size_t payload_size;
    size_t payload_triangles;
    unsigned int axis;

    if (out_view == NULL) return COLLISION_MESH_INVALID_ARGUMENT;
    memset(out_view, 0, sizeof(*out_view));
    if (data == NULL) return COLLISION_MESH_INVALID_ARGUMENT;
    if (size_bytes < COLLISION_MESH_SWC1_HEADER_SIZE) return COLLISION_MESH_BAD_SIZE;
    if (memcmp(bytes, "SWC1", 4U) != 0) return COLLISION_MESH_BAD_MAGIC;

    memset(&candidate, 0, sizeof(candidate));
    candidate.bytes = bytes;
    candidate.size_bytes = size_bytes;
    candidate.triangle_count = read_u32_be(bytes + 4U);
    if (candidate.triangle_count == 0U) return COLLISION_MESH_BAD_HEADER;

    /* Compare using division of the supplied buffer length; never multiply an
       untrusted triangle count (important on the 32-bit GameCube target). */
    payload_size = size_bytes - COLLISION_MESH_SWC1_HEADER_SIZE;
    if ((payload_size % COLLISION_MESH_SWC1_TRIANGLE_SIZE) != 0U)
        return COLLISION_MESH_BAD_SIZE;
    payload_triangles = payload_size / COLLISION_MESH_SWC1_TRIANGLE_SIZE;
    if (payload_triangles > (size_t)UINT32_MAX ||
        candidate.triangle_count != (uint32_t)payload_triangles) {
        return COLLISION_MESH_BAD_SIZE;
    }

    for (axis = 0U; axis < 3U; ++axis) {
        candidate.min[axis] = read_i16_be(bytes + 8U + axis * 4U);
        candidate.max[axis] = read_i16_be(bytes + 10U + axis * 4U);
        if (candidate.min[axis] > candidate.max[axis]) return COLLISION_MESH_BAD_HEADER;
    }
    for (i = 20U; i < COLLISION_MESH_SWC1_HEADER_SIZE; ++i) {
        if (bytes[i] != 0U) return COLLISION_MESH_BAD_HEADER;
    }

    /* Validate the entire payload once. The racing hot path can then access
       triangles by index without reparsing headers or allocating memory. */
    for (i = 0U; i < candidate.triangle_count; ++i) {
        const unsigned char *triangle = bytes + COLLISION_MESH_SWC1_HEADER_SIZE +
                                        (size_t)i * COLLISION_MESH_SWC1_TRIANGLE_SIZE;
        unsigned int vertex_index;
        for (vertex_index = 0U; vertex_index < 3U; ++vertex_index) {
            CollisionMeshVertex v = read_vertex(triangle + vertex_index * 6U);
            if (!vertex_inside_bounds(&v, candidate.min, candidate.max))
                return COLLISION_MESH_BAD_VERTEX;
        }
    }

    *out_view = candidate;
    return COLLISION_MESH_OK;
}

CollisionMeshResult collision_mesh_swc1_get_triangle(const CollisionMeshView *view,
                                                      uint32_t index,
                                                      CollisionMeshTriangle *out_triangle)
{
    const unsigned char *p;
    unsigned int i;
    if (view == NULL || out_triangle == NULL || view->bytes == NULL)
        return COLLISION_MESH_INVALID_ARGUMENT;
    memset(out_triangle, 0, sizeof(*out_triangle));
    if (index >= view->triangle_count) return COLLISION_MESH_BAD_INDEX;
    if (view->size_bytes < COLLISION_MESH_SWC1_HEADER_SIZE)
        return COLLISION_MESH_BAD_SIZE;
    {
        size_t payload_size = view->size_bytes - COLLISION_MESH_SWC1_HEADER_SIZE;
        size_t payload_triangles;
        if ((payload_size % COLLISION_MESH_SWC1_TRIANGLE_SIZE) != 0U)
            return COLLISION_MESH_BAD_SIZE;
        payload_triangles = payload_size / COLLISION_MESH_SWC1_TRIANGLE_SIZE;
        if (payload_triangles > (size_t)UINT32_MAX ||
            view->triangle_count != (uint32_t)payload_triangles)
            return COLLISION_MESH_BAD_SIZE;
    }
    p = view->bytes + COLLISION_MESH_SWC1_HEADER_SIZE +
        (size_t)index * COLLISION_MESH_SWC1_TRIANGLE_SIZE;
    for (i = 0U; i < 3U; ++i) out_triangle->vertex[i] = read_vertex(p + i * 6U);
    return COLLISION_MESH_OK;
}
