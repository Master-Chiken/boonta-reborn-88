#include "pod_model.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#define REQUIRE(cond, message) do { if (!(cond)) { fprintf(stderr,"FAIL: %s\n",message); return 1; } } while (0)

int main(void)
{
    PodMesh *mesh=(PodMesh *)malloc(sizeof(PodMesh));
    PodMesh *variant=(PodMesh *)malloc(sizeof(PodMesh));
    unsigned int i, materials[7]={0,0,0,0,0,0,0};
    float minx=1e9f,maxx=-1e9f,miny=1e9f,maxy=-1e9f,minz=1e9f,maxz=-1e9f;
    REQUIRE(mesh!=NULL && variant!=NULL,"mesh allocation");
    REQUIRE(pod_model_build(mesh)==0,"model build");
    REQUIRE(mesh->vertex_count>=600U,"model has enough detailed triangles");
    REQUIRE(mesh->vertex_count%3U==0U,"mesh is a triangle list");
    REQUIRE(mesh->vertex_count<POD_MESH_MAX_VERTICES,"mesh stays within fixed buffer");
    for (i=0;i<mesh->vertex_count;++i) {
        const PodVertex *v=&mesh->vertices[i];
        REQUIRE(isfinite(v->x)&&isfinite(v->y)&&isfinite(v->z),"all vertices finite");
        REQUIRE(v->material<=POD_MAT_ENGINE,"valid material tag");
        materials[v->material]++;
        if (v->x<minx) minx=v->x;
        if (v->x>maxx) maxx=v->x;
        if (v->y<miny) miny=v->y;
        if (v->y>maxy) maxy=v->y;
        if (v->z<minz) minz=v->z;
        if (v->z>maxz) maxz=v->z;
    }
    REQUIRE(minx < -1.80f && maxx > 1.80f,"twin engine width");
    REQUIRE(fabsf(minx+maxx)<0.08f,"model is symmetrical across X");
    REQUIRE(miny < 0.25f && maxy > 0.90f,"pod has vertical shape");
    REQUIRE(minz < -2.0f && maxz > 1.8f,"engine length and pointed nose");
    REQUIRE(materials[POD_MAT_BODY]>0U,"body livery material exists");
    REQUIRE(materials[POD_MAT_METAL]>0U,"metal material exists");
    REQUIRE(materials[POD_MAT_GLASS]>0U,"canopy material exists");
    REQUIRE(materials[POD_MAT_ENGINE]>0U,"engine nozzle material exists");
    printf("PASS: pod mesh vertices=%u bounds x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]\n",
           mesh->vertex_count,minx,maxx,miny,maxy,minz,maxz);
    REQUIRE(pod_model_build_variant(variant, 0U)==0,"variant zero builds");
    REQUIRE(variant->vertex_count>mesh->vertex_count,"variant adds signature components");
    {
        unsigned int roster, j, min_vertices=0xffffffffU, max_vertices=0U;
        unsigned int archetypes_seen=0U;
        for (roster=0U; roster<23U; ++roster) {
            unsigned int count;
            REQUIRE(pod_model_build_variant(variant, roster)==0,"all roster models build");
            REQUIRE(variant->vertex_count%3U==0U,"variant triangle list valid");
            REQUIRE(variant->vertex_count>mesh->vertex_count,"variant has added components");
            if (variant->vertex_count<min_vertices) min_vertices=variant->vertex_count;
            if (variant->vertex_count>max_vertices) max_vertices=variant->vertex_count;
            for (j=0U; j<variant->vertex_count; ++j) {
                REQUIRE(isfinite(variant->vertices[j].x) &&
                        isfinite(variant->vertices[j].y) &&
                        isfinite(variant->vertices[j].z),"variant coordinates finite");
            }
            count=variant->vertex_count-mesh->vertex_count;
            REQUIRE(count>=3U,"signature contains extra geometry");
            archetypes_seen |= 1U << (roster%5U);
        }
        REQUIRE(archetypes_seen==31U,"all five signature component families are present");
        REQUIRE(max_vertices>min_vertices,"individual variants have different component counts");
        REQUIRE(pod_model_build_variant(variant, 1U)==0,"second variant builds");
        REQUIRE(fabsf(variant->vertices[0].x-mesh->vertices[0].x)>0.001f ||
                fabsf(variant->vertices[0].z-mesh->vertices[0].z)>0.001f,
                "variant changes the actual silhouette geometry");
    }
    printf("PASS: 23 pod variants include five signature component families\n");
    free(variant);
    free(mesh);
    return 0;
}
