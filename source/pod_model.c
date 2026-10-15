#include "pod_model.h"
#include <math.h>
#include <stddef.h>
#include <string.h>

#define POD_PI 3.14159265358979323846f
#define POD_SIDES 8U

typedef struct { float x, y, z; } PodPoint;

static int push_vertex(PodMesh *mesh, PodPoint p, unsigned char material)
{
    PodVertex *out;
    if (mesh == NULL || mesh->vertex_count >= POD_MESH_MAX_VERTICES) return -1;
    out = &mesh->vertices[mesh->vertex_count++];
    out->x = p.x; out->y = p.y; out->z = p.z; out->material = material;
    return 0;
}

static int triangle(PodMesh *mesh, PodPoint a, PodPoint b, PodPoint c,
                    unsigned char material)
{
    if (push_vertex(mesh, a, material) != 0) return -1;
    if (push_vertex(mesh, b, material) != 0) return -1;
    if (push_vertex(mesh, c, material) != 0) return -1;
    return 0;
}

static PodPoint point3(float x, float y, float z)
{
    PodPoint p; p.x=x; p.y=y; p.z=z; return p;
}

static int quad(PodMesh *mesh, PodPoint a, PodPoint b, PodPoint c, PodPoint d,
                unsigned char material)
{
    if (triangle(mesh, a, b, c, material) != 0) return -1;
    return triangle(mesh, a, c, d, material);
}

static int box(PodMesh *mesh, float cx, float cy, float cz,
               float hx, float hy, float hz, unsigned char material)
{
    PodPoint v[8];
    static const unsigned char tri[36] = {
        0,1,2, 0,2,3, 4,6,5, 4,7,6,
        0,4,5, 0,5,1, 3,2,6, 3,6,7,
        0,3,7, 0,7,4, 1,5,6, 1,6,2
    };
    unsigned int i;
    v[0]=point3(cx-hx,cy-hy,cz-hz); v[1]=point3(cx+hx,cy-hy,cz-hz);
    v[2]=point3(cx+hx,cy+hy,cz-hz); v[3]=point3(cx-hx,cy+hy,cz-hz);
    v[4]=point3(cx-hx,cy-hy,cz+hz); v[5]=point3(cx+hx,cy-hy,cz+hz);
    v[6]=point3(cx+hx,cy+hy,cz+hz); v[7]=point3(cx-hx,cy+hy,cz+hz);
    for (i=0; i<36U; i+=3U) {
        if (triangle(mesh,v[tri[i]],v[tri[i+1U]],v[tri[i+2U]],material)!=0) return -1;
    }
    return 0;
}

static PodPoint ring_point(float cx, float cy, float z, float rx, float ry,
                           unsigned int side)
{
    float angle = (2.0f * POD_PI * (float)side) / (float)POD_SIDES;
    return point3(cx + cosf(angle)*rx, cy + sinf(angle)*ry, z);
}

static unsigned char facet_material(unsigned int side)
{
    float angle = (2.0f * POD_PI * (float)side) / (float)POD_SIDES;
    float y = sinf(angle);
    if (y > 0.62f) return POD_MAT_BODY_LIGHT;
    if (y < -0.62f) return POD_MAT_DARK;
    if (side == 0U || side == 4U) return POD_MAT_ACCENT;
    return POD_MAT_BODY;
}

static int engine_shell(PodMesh *mesh, float cx)
{
    static const float rz[6] = {-2.06f, -1.72f, -0.78f, 0.18f, 1.13f, 1.90f};
    static const float rx[6] = {0.28f, 0.39f, 0.52f, 0.50f, 0.37f, 0.035f};
    static const float ry[6] = {0.28f, 0.35f, 0.43f, 0.44f, 0.33f, 0.035f};
    unsigned int ring, side;
    const float cy = 0.52f;
    for (ring=0; ring<5U; ++ring) {
        for (side=0; side<POD_SIDES; ++side) {
            unsigned int next=(side+1U)%POD_SIDES;
            PodPoint a=ring_point(cx,cy,rz[ring],rx[ring],ry[ring],side);
            PodPoint b=ring_point(cx,cy,rz[ring],rx[ring],ry[ring],next);
            PodPoint c=ring_point(cx,cy,rz[ring+1U],rx[ring+1U],ry[ring+1U],next);
            PodPoint d=ring_point(cx,cy,rz[ring+1U],rx[ring+1U],ry[ring+1U],side);
            unsigned char mat=facet_material(side);
            if (quad(mesh,a,b,c,d,mat)!=0) return -1;
        }
    }
    /* Rear nozzle face and eight segmented metal petals. */
    {
        PodPoint center=point3(cx,cy,rz[0]-0.015f);
        for (side=0; side<POD_SIDES; ++side) {
            unsigned int next=(side+1U)%POD_SIDES;
            PodPoint a=ring_point(cx,cy,rz[0],rx[0],ry[0],side);
            PodPoint b=ring_point(cx,cy,rz[0],rx[0],ry[0],next);
            if (triangle(mesh,center,a,b,POD_MAT_ENGINE)!=0) return -1;
        }
        for (side=0; side<POD_SIDES; ++side) {
            unsigned int next=(side+1U)%POD_SIDES;
            PodPoint a=ring_point(cx,cy,-2.04f,0.34f,0.33f,side);
            PodPoint b=ring_point(cx,cy,-2.04f,0.34f,0.33f,next);
            PodPoint c=ring_point(cx,cy,-1.84f,0.35f,0.34f,next);
            PodPoint d=ring_point(cx,cy,-1.84f,0.35f,0.34f,side);
            if (quad(mesh,a,b,c,d,POD_MAT_METAL)!=0) return -1;
        }
    }
    return 0;
}

static int cockpit(PodMesh *mesh)
{
    PodPoint a=point3(-0.43f,0.61f,-0.50f), b=point3(0.43f,0.61f,-0.50f);
    PodPoint c=point3(0.43f,0.61f,0.53f), d=point3(-0.43f,0.61f,0.53f);
    PodPoint e=point3(-0.27f,0.98f,-0.14f), f=point3(0.27f,0.98f,-0.14f);
    PodPoint g=point3(0.23f,0.94f,0.38f), h=point3(-0.23f,0.94f,0.38f);
    if (box(mesh,0.0f,0.53f,0.02f,0.48f,0.10f,0.60f,POD_MAT_BODY)!=0) return -1;
    if (quad(mesh,a,b,f,e,POD_MAT_METAL)!=0) return -1;
    if (quad(mesh,b,c,g,f,POD_MAT_GLASS)!=0) return -1;
    if (quad(mesh,c,d,h,g,POD_MAT_GLASS)!=0) return -1;
    if (quad(mesh,d,a,e,h,POD_MAT_GLASS)!=0) return -1;
    if (quad(mesh,e,f,g,h,POD_MAT_GLASS)!=0) return -1;
    /* Two visible tie bars between the engine nacelles. */
    if (box(mesh,0.0f,0.42f,-0.25f,1.22f,0.085f,0.13f,POD_MAT_METAL)!=0) return -1;
    if (box(mesh,0.0f,0.48f,0.68f,1.08f,0.07f,0.10f,POD_MAT_DARK)!=0) return -1;
    /* Low-poly fins on the outer shoulders. */
    if (triangle(mesh,point3(-1.70f,0.47f,-0.55f),point3(-2.03f,0.44f,0.58f),
                 point3(-1.64f,0.64f,0.38f),POD_MAT_ACCENT)!=0) return -1;
    if (triangle(mesh,point3(1.70f,0.47f,-0.55f),point3(1.64f,0.64f,0.38f),
                 point3(2.03f,0.44f,0.58f),POD_MAT_ACCENT)!=0) return -1;
    return 0;
}

int pod_model_build(PodMesh *mesh)
{
    if (mesh == NULL) return -1;
    memset(mesh,0,sizeof(*mesh));
    if (engine_shell(mesh,-1.34f)!=0) return -1;
    if (engine_shell(mesh, 1.34f)!=0) return -1;
    if (cockpit(mesh)!=0) return -1;
    return mesh->vertex_count > 0U ? 0 : -1;
}


static int add_signature_parts(PodMesh *mesh, unsigned int vehicle_index)
{
    /* Five component families create more than simple scaled copies. These are
     * original prototype details, not recreations of the commercial meshes. */
    switch (vehicle_index % 5U) {
    case 0U: /* broad forward stabilizer */
        if (box(mesh, 0.0f, 0.36f, 0.94f, 1.02f, 0.075f, 0.13f,
                POD_MAT_ACCENT) != 0) return -1;
        break;
    case 1U: /* raised dorsal spine */
        if (box(mesh, 0.0f, 0.82f, -0.02f, 0.17f, 0.13f, 0.70f,
                POD_MAT_BODY_LIGHT) != 0) return -1;
        if (triangle(mesh, point3(-0.17f,0.80f,0.52f),
                     point3(0.17f,0.80f,0.52f), point3(0.0f,1.04f,0.79f),
                     POD_MAT_ACCENT) != 0) return -1;
        break;
    case 2U: /* swept side fins */
        if (triangle(mesh,point3(-1.42f,0.42f,-0.60f),
                     point3(-2.14f,0.38f,0.10f),point3(-1.45f,0.62f,0.52f),
                     POD_MAT_ACCENT) != 0) return -1;
        if (triangle(mesh,point3(1.42f,0.42f,-0.60f),
                     point3(1.45f,0.62f,0.52f),point3(2.14f,0.38f,0.10f),
                     POD_MAT_ACCENT) != 0) return -1;
        break;
    case 3U: /* armored engine bridge */
        if (box(mesh, 0.0f, 0.40f, -0.72f, 1.38f, 0.10f, 0.18f,
                POD_MAT_METAL) != 0) return -1;
        if (box(mesh, 0.0f, 0.50f, -0.72f, 0.70f, 0.08f, 0.12f,
                POD_MAT_DARK) != 0) return -1;
        break;
    default: /* compact nose splitter and twin pylons */
        if (box(mesh, 0.0f, 0.32f, 1.04f, 0.76f, 0.055f, 0.11f,
                POD_MAT_ACCENT) != 0) return -1;
        if (box(mesh, -0.72f,0.42f,0.64f,0.07f,0.08f,0.22f,
                POD_MAT_METAL) != 0) return -1;
        if (box(mesh, 0.72f,0.42f,0.64f,0.07f,0.08f,0.22f,
                POD_MAT_METAL) != 0) return -1;
        break;
    }
    /* Small dorsal marker differentiates individual entries within a family. */
    if ((vehicle_index % 3U) == 0U) {
        if (box(mesh, 0.0f, 0.88f, -0.30f, 0.075f, 0.075f, 0.20f,
                POD_MAT_ACCENT) != 0) return -1;
    } else if ((vehicle_index % 3U) == 1U) {
        if (triangle(mesh,point3(-0.24f,0.62f,-0.08f),
                     point3(0.24f,0.62f,-0.08f),point3(0.0f,0.84f,0.26f),
                     POD_MAT_BODY_LIGHT) != 0) return -1;
    }
    return 0;
}

int pod_model_build_variant(PodMesh *mesh, unsigned int vehicle_index)
{
    unsigned int i;
    float width_scale, length_scale, height_scale, engine_spread;
    if (mesh == NULL || pod_model_build(mesh) != 0) return -1;
    vehicle_index %= 23U;
    /* Each roster slot gets a repeatable silhouette profile: engine spacing,
     * overall length, cockpit height and body width vary independently. */
    width_scale = 0.82f + (float)((vehicle_index * 7U) % 13U) * 0.033f;
    length_scale = 0.86f + (float)((vehicle_index * 5U) % 11U) * 0.031f;
    height_scale = 0.84f + (float)((vehicle_index * 3U) % 9U) * 0.040f;
    engine_spread = 0.86f + (float)((vehicle_index * 11U) % 9U) * 0.035f;
    for (i = 0U; i < mesh->vertex_count; ++i) {
        PodVertex *v = &mesh->vertices[i];
        float absx = fabsf(v->x);
        float xscale = absx > 0.90f ? engine_spread : width_scale;
        v->x *= xscale;
        v->z *= length_scale;
        v->y *= height_scale;
        if (v->material == POD_MAT_ACCENT && (vehicle_index % 3U) == 1U)
            v->material = POD_MAT_BODY_LIGHT;
        else if (v->material == POD_MAT_BODY && (vehicle_index % 4U) == 2U &&
                 absx > 1.45f)
            v->material = POD_MAT_ACCENT;
    }
    return add_signature_parts(mesh, vehicle_index);
}
