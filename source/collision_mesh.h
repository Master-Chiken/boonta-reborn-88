#ifndef SWE1R_COLLISION_MESH_H
#define SWE1R_COLLISION_MESH_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define COLLISION_MESH_SWC1_HEADER_SIZE 32U
#define COLLISION_MESH_SWC1_TRIANGLE_SIZE 18U

typedef enum {
    COLLISION_MESH_OK = 0,
    COLLISION_MESH_INVALID_ARGUMENT = -1,
    COLLISION_MESH_BAD_MAGIC = -2,
    COLLISION_MESH_BAD_HEADER = -3,
    COLLISION_MESH_BAD_SIZE = -4,
    COLLISION_MESH_BAD_VERTEX = -5,
    COLLISION_MESH_BAD_INDEX = -6
} CollisionMeshResult;

typedef struct {
    int16_t x;
    int16_t y;
    int16_t z;
} CollisionMeshVertex;

typedef struct {
    CollisionMeshVertex vertex[3];
} CollisionMeshTriangle;

/*
 * Zero-copy view over a validated SWC1 byte buffer.
 * The caller retains ownership of the bytes and must keep them alive while
 * the view is being used. No allocation is performed by this module.
 */
typedef struct {
    const unsigned char *bytes;
    size_t size_bytes;
    uint32_t triangle_count;
    int16_t min[3]; /* X, Y, Z */
    int16_t max[3]; /* X, Y, Z */
} CollisionMeshView;

/* Strictly validates the SWC1 header, exact payload size, reserved bytes,
 * declared bounds, and every vertex before publishing a usable view. */
CollisionMeshResult collision_mesh_swc1_open(const void *bytes, size_t size_bytes,
                                              CollisionMeshView *out_view);

/* Decodes a triangle to host-endian signed coordinates. The view must have
 * been produced by collision_mesh_swc1_open(). */
CollisionMeshResult collision_mesh_swc1_get_triangle(const CollisionMeshView *view,
                                                      uint32_t index,
                                                      CollisionMeshTriangle *out_triangle);

#ifdef __cplusplus
}
#endif
#endif
