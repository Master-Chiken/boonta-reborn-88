#include "vehicle_catalog.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#define CHECK(e) do { if (!(e)) { fprintf(stderr,"FAIL %s:%d: %s\n",__FILE__,__LINE__,#e); return 1; } } while(0)

static void make_large_circle(RacerTrackPoint *p,unsigned int n)
{
    unsigned int i; const float pi=3.14159265358979323846f;
    for(i=0;i<n;++i){float a=2.0f*pi*(float)i/(float)n;p[i].x=2000.0f*cosf(a);p[i].y=0.0f;p[i].z=2000.0f*sinf(a);}
}
int main(void)
{
    unsigned int i;
    float min_speed=1000.0f,max_speed=0.0f,min_steer=1000.0f,max_steer=0.0f;
    RacerTrackPoint track[128]; RacerState sebulba,ratts,dud,icy,smooth;
    RacerInput input={0.0f,1.0f,0.0f,0.0f,0.0f};
    const RacerVehicleSpec *fast=vehicle_catalog_get(1U);
    const RacerVehicleSpec *agile=vehicle_catalog_get(2U);
    const RacerVehicleSpec *fragile=vehicle_catalog_get(5U);
    CHECK(vehicle_catalog_count()==RACER_VEHICLE_COUNT);
    for(i=0;i<vehicle_catalog_count();++i){
        const RacerVehicleSpec *v=vehicle_catalog_get(i);
        CHECK(v!=0 && v->name!=0 && v->top_speed>40.0f && v->top_speed<60.0f);
        CHECK(v->acceleration>15.0f && v->steering>0.5f && v->grip>0.5f);
        if(v->top_speed<min_speed) min_speed=v->top_speed;
        if(v->top_speed>max_speed) max_speed=v->top_speed;
        if(v->steering<min_steer) min_steer=v->steering;
        if(v->steering>max_steer) max_steer=v->steering;
    }
    CHECK(max_speed-min_speed>=10.0f);
    CHECK(max_steer-min_steer>=0.3f);
    CHECK(vehicle_catalog_get(999U)==vehicle_catalog_get(0U));

    /* Presets affect live acceleration/top speed, not just the selection-screen bars. */
    make_large_circle(track,128U);
    racer_init(&sebulba,track,128U); racer_init(&ratts,track,128U);
    sebulba.speed=44.0f; ratts.speed=44.0f;
    for(i=0;i<60U;++i){
        racer_update_vehicle(&sebulba,track,128U,&input,fast,1.0f/60.0f);
        racer_update_vehicle(&ratts,track,128U,&input,agile,1.0f/60.0f);
    }
    CHECK(sebulba.speed>ratts.speed+5.0f);

    /* Steering and impact resistance are also used by the simulation. */
    racer_init(&sebulba,track,128U); racer_init(&ratts,track,128U);
    sebulba.speed=ratts.speed=35.0f; input.throttle=0.0f; input.steering=1.0f;
    for(i=0;i<40U;++i){
        racer_update_vehicle(&sebulba,track,128U,&input,fast,1.0f/60.0f);
        racer_update_vehicle(&ratts,track,128U,&input,agile,1.0f/60.0f);
    }
    CHECK(fabsf(ratts.heading)>fabsf(sebulba.heading));
    racer_init(&ratts,track,128U); racer_init(&dud,track,128U);
    racer_apply_impact(&ratts,agile,20.0f,1.0f);
    racer_apply_impact(&dud,fragile,20.0f,1.0f);
    CHECK(dud.damage>ratts.damage);

    /* Track surfaces affect live driving: ice has less steering authority and more drag. */
    racer_init(&icy,track,128U); racer_init(&smooth,track,128U);
    icy.speed=smooth.speed=30.0f; input.throttle=1.0f; input.steering=0.8f;
    for(i=0;i<45U;++i){
        racer_update_vehicle_surface(&icy,track,128U,&input,agile,0.72f,1.6f,1.0f/60.0f);
        racer_update_vehicle_surface(&smooth,track,128U,&input,agile,1.02f,0.35f,1.0f/60.0f);
    }
    CHECK(fabsf(smooth.heading)>fabsf(icy.heading));
    racer_init(&icy,track,128U); racer_init(&smooth,track,128U);
    icy.speed=smooth.speed=30.0f; input.throttle=1.0f; input.steering=0.0f;
    for(i=0;i<30U;++i){
        racer_update_vehicle_surface(&icy,track,128U,&input,agile,0.72f,1.6f,1.0f/60.0f);
        racer_update_vehicle_surface(&smooth,track,128U,&input,agile,1.02f,0.35f,1.0f/60.0f);
    }
    CHECK(smooth.speed>icy.speed+0.25f);
    puts("PASS: 23 pilot presets and track surface grip/drag affect live handling");
    return 0;
}
