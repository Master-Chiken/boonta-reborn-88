#include "track_catalog.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#define CHECK(e) do { if (!(e)) { fprintf(stderr,"FAIL %s:%d: %s\n",__FILE__,__LINE__,#e); return 1; } } while(0)

int main(void)
{
    RacerTrackPoint points[TRACK_POINT_CAPACITY];
    TrackVertex mesh[TRACK_VERTEX_CAPACITY];
    float lengths[TRACK_CATALOG_COUNT]={0};
    unsigned int style_seen[8]={0U,0U,0U,0U,0U,0U,0U,0U};
    unsigned int t;
    for(t=0;t<TRACK_CATALOG_COUNT;++t){
        unsigned int count=0U, vertices=0U, i;
        CHECK(track_catalog_build_points(t,points,TRACK_POINT_CAPACITY,&count));
        CHECK(track_catalog_layout_style(t) >= TRACK_LAYOUT_CANYON &&
              track_catalog_layout_style(t) <= TRACK_LAYOUT_SERPENTINE);
        style_seen[(unsigned int)track_catalog_layout_style(t)]++;
        CHECK(count>=80U && count<=TRACK_POINT_CAPACITY);
        for(i=0;i<count;++i){
            float dx=points[(i+1U)%count].x-points[i].x;
            float dz=points[(i+1U)%count].z-points[i].z;
            CHECK(isfinite(points[i].x) && isfinite(points[i].y) && isfinite(points[i].z));
            CHECK(dx*dx+dz*dz>0.01f);
            lengths[t]+=sqrtf(dx*dx+dz*dz);
        }
        CHECK(track_catalog_build_mesh(t,points,count,mesh,TRACK_VERTEX_CAPACITY,&vertices));
        CHECK(vertices==count*18U);
        CHECK(mesh[0].r>0U && mesh[0].g>0U && mesh[0].b>0U);
        CHECK(track_catalog_get(t)->name!=0);
        CHECK(track_catalog_get(t)->surface_grip>=0.68f && track_catalog_get(t)->surface_grip<=1.08f);
        CHECK(track_catalog_get(t)->rolling_resistance>=0.3f && track_catalog_get(t)->rolling_resistance<=1.9f);
    }
    CHECK(track_catalog_count()==25U);
    for(t=0;t<8U;++t) CHECK(style_seen[t]>=3U);
    /* Ensure the expanded catalogue is not just 25 labels on one route. */
    for(t=0;t<TRACK_CATALOG_COUNT;++t){
        unsigned int u;
        CHECK(track_catalog_get(t)->planet!=0);
        for(u=t+1U;u<TRACK_CATALOG_COUNT;++u)
            CHECK(track_catalog_get(t)!=track_catalog_get(u));
    }
    CHECK(fabsf(lengths[0]-lengths[1])>5.0f);
    CHECK(fabsf(lengths[1]-lengths[2])>10.0f);
    CHECK(fabsf(lengths[2]-lengths[3])>20.0f);
    CHECK(track_catalog_get(18U)->surface_grip < track_catalog_get(6U)->surface_grip);
    CHECK(track_catalog_get(11U)->rolling_resistance > track_catalog_get(17U)->rolling_resistance);

    /* The rendered road now banks into a turn. A counter-clockwise circular
       route raises its +normal edge; reversing the route must reverse the bank
       sign. This guards both geometry and the shared curvature calculation. */
    {
        RacerTrackPoint curve[16], reversed[16];
        TrackVertex curve_mesh[TRACK_VERTEX_CAPACITY];
        unsigned int curve_vertices = 0U, k;
        const float pi = 3.14159265358979323846f;
        for (k=0U; k<16U; ++k) {
            float angle = 2.0f*pi*(float)k/16.0f;
            curve[k].x = 30.0f*cosf(angle);
            curve[k].y = 3.0f;
            curve[k].z = 30.0f*sinf(angle);
        }
        for (k=0U; k<16U; ++k) {
            reversed[k].x = curve[16U-k-1U].x;
            reversed[k].y = curve[16U-k-1U].y;
            reversed[k].z = curve[16U-k-1U].z;
        }
        CHECK(track_catalog_build_mesh(0U,curve,16U,curve_mesh,
                                       TRACK_VERTEX_CAPACITY,&curve_vertices));
        CHECK(curve_vertices==16U*18U);
        CHECK(curve_mesh[0].y > curve_mesh[1].y + 0.10f);
        CHECK(track_catalog_build_mesh(0U,reversed,16U,curve_mesh,
                                       TRACK_VERTEX_CAPACITY,&curve_vertices));
        CHECK(curve_mesh[0].y + 0.10f < curve_mesh[1].y);
    }
    CHECK(!track_catalog_build_points(1U,points,3U,&t));
    puts("PASS: 25 tracks across eight route families, environment grip/drag and runtime meshes");
    return 0;
}
