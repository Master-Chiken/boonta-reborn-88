#ifndef BOONTA_MESH_DATA_H
#define BOONTA_MESH_DATA_H

#include <math.h>
#include <stddef.h>
#include <stdint.h>

/*
 * This contract is deliberately limited to the attributes currently submitted
 * by the GameCube GX renderer: XYZ positions and RGBA8 vertex colour.
 *
 * The existing renderer can expand at most 4096 vertices. For an indexed
 * triangle list, the expanded index count must be a multiple of three and
 * therefore cannot exceed 4095.
 */
#define BOONTA_MESH_MAX_EXPANDED_VERTICES 4096U
#define BOONTA_MESH_MAX_VERTICES BOONTA_MESH_MAX_EXPANDED_VERTICES
#define BOONTA_MESH_MAX_INDICES \
    ((BOONTA_MESH_MAX_EXPANDED_VERTICES / 3U) * 3U)

typedef struct {
    float x;
    float y;
    float z;
    uint8_t r;
    uint8_t g;
    uint8_t b;
    uint8_t a;
} BoontaMeshVertex;

/*
 * The byte lengths must describe the actual readable backing arrays, not just
 * the intended size. The validator can check declared lengths and counts, but
 * C cannot discover the allocated length behind an arbitrary non-NULL pointer.
 */
typedef struct {
    const BoontaMeshVertex *vertices;
    size_t vertex_count;
    size_t vertex_bytes;
    const uint16_t *indices;
    size_t index_count;
    size_t index_bytes;
} BoontaMeshView;

typedef enum {
    BOONTA_MESH_VALID = 0,
    BOONTA_MESH_INVALID_ARGUMENT,
    BOONTA_MESH_INVALID_COUNTS,
    BOONTA_MESH_SIZE_OVERFLOW,
    BOONTA_MESH_TRUNCATED_DATA,
    BOONTA_MESH_INVALID_INDEX,
    BOONTA_MESH_NONFINITE_POSITION,
    BOONTA_MESH_DEGENERATE_TRIANGLE
} BoontaMeshValidation;

/*
 * Checked size helper, kept independently testable. On failure, *bytes is
 * left untouched. The mesh validator applies strict count caps before calling
 * this helper, so attacker-controlled oversized mesh counts never reach an
 * allocation or array traversal.
 */
static inline int boonta_mesh_size_bytes(size_t count,
                                         size_t element_size,
                                         size_t *bytes)
{
    if (bytes == NULL || element_size == 0U ||
        count > ((size_t)-1) / element_size) {
        return 0;
    }

    *bytes = count * element_size;
    return 1;
}

/*
 * Validate a non-empty indexed triangle list before reading its contents for
 * conversion/submission. Degenerate (zero-area) triangles are rejected.
 * Validation performs no allocation or copy. Callers may submit data to GX
 * only after the complete view has passed this validator.
 */
static inline BoontaMeshValidation
boonta_mesh_validate(const BoontaMeshView *mesh)
{
    size_t vertex_bytes_required;
    size_t index_bytes_required;
    size_t i;

    if (mesh == NULL || mesh->vertices == NULL || mesh->indices == NULL) {
        return BOONTA_MESH_INVALID_ARGUMENT;
    }

    if (mesh->vertex_count < 3U ||
        mesh->vertex_count > BOONTA_MESH_MAX_VERTICES ||
        mesh->index_count < 3U ||
        mesh->index_count > BOONTA_MESH_MAX_INDICES ||
        mesh->index_count % 3U != 0U) {
        return BOONTA_MESH_INVALID_COUNTS;
    }

    if (!boonta_mesh_size_bytes(mesh->vertex_count,
                                sizeof(*mesh->vertices),
                                &vertex_bytes_required) ||
        !boonta_mesh_size_bytes(mesh->index_count,
                                sizeof(*mesh->indices),
                                &index_bytes_required)) {
        return BOONTA_MESH_SIZE_OVERFLOW;
    }

    if (mesh->vertex_bytes < vertex_bytes_required ||
        mesh->index_bytes < index_bytes_required) {
        return BOONTA_MESH_TRUNCATED_DATA;
    }

    for (i = 0U; i < mesh->vertex_count; ++i) {
        if (!isfinite(mesh->vertices[i].x) ||
            !isfinite(mesh->vertices[i].y) ||
            !isfinite(mesh->vertices[i].z)) {
            return BOONTA_MESH_NONFINITE_POSITION;
        }
    }

    for (i = 0U; i < mesh->index_count; ++i) {
        if ((size_t)mesh->indices[i] >= mesh->vertex_count) {
            return BOONTA_MESH_INVALID_INDEX;
        }
    }

    for (i = 0U; i < mesh->index_count; i += 3U) {
        const BoontaMeshVertex *a = &mesh->vertices[mesh->indices[i]];
        const BoontaMeshVertex *b = &mesh->vertices[mesh->indices[i + 1U]];
        const BoontaMeshVertex *c = &mesh->vertices[mesh->indices[i + 2U]];
        const double abx = (double)b->x - (double)a->x;
        const double aby = (double)b->y - (double)a->y;
        const double abz = (double)b->z - (double)a->z;
        const double acx = (double)c->x - (double)a->x;
        const double acy = (double)c->y - (double)a->y;
        const double acz = (double)c->z - (double)a->z;
        const double nx = aby * acz - abz * acy;
        const double ny = abz * acx - abx * acz;
        const double nz = abx * acy - aby * acx;

        if (nx == 0.0 && ny == 0.0 && nz == 0.0) {
            return BOONTA_MESH_DEGENERATE_TRIANGLE;
        }
    }

    return BOONTA_MESH_VALID;
}

#endif
