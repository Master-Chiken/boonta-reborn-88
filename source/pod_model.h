#ifndef SWE1R_POD_MODEL_H
#define SWE1R_POD_MODEL_H

#ifdef __cplusplus
extern "C" {
#endif

#define POD_MESH_MAX_VERTICES 2048U

typedef enum {
    POD_MAT_BODY = 0,
    POD_MAT_BODY_LIGHT = 1,
    POD_MAT_DARK = 2,
    POD_MAT_METAL = 3,
    POD_MAT_GLASS = 4,
    POD_MAT_ACCENT = 5,
    POD_MAT_ENGINE = 6
} PodMaterial;

typedef struct {
    float x;
    float y;
    float z;
    unsigned char material;
} PodVertex;

typedef struct {
    PodVertex vertices[POD_MESH_MAX_VERTICES];
    unsigned int vertex_count;
} PodMesh;

/* Build a symmetrical, low-poly twin-engine pod mesh in local coordinates.
 * Local +Z points forwards. Returns 0 on success, -1 on capacity failure. */
int pod_model_build(PodMesh *mesh);
/* Build a procedural silhouette variant for a roster entry (0..22).
 * These are distinct prototype shapes, not faithful original game assets. */
int pod_model_build_variant(PodMesh *mesh, unsigned int vehicle_index);

#ifdef __cplusplus
}
#endif
#endif
