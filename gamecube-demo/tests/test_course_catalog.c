#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "../source/course_catalog.h"

static void test_course(const BoontaCourseDefinition *c,float *sx,float *sy,float *sz)
{
    unsigned int laps=99U;
    float progress=-1.0f,remaining=0.0f,x=0.0f,y=0.0f,z=0.0f,w=0.0f;
    assert(c!=NULL&&c->id!=NULL&&c->display_name!=NULL&&c->region!=NULL);
    assert(isfinite(c->lap_distance)&&c->lap_distance>150.0f);
    assert(c->node_count==8U&&c->edge_count==8U);
    assert(c->reset&&c->advance&&c->sample&&c->get_lap_state&&c->distance_to_next_finish);
    assert(c->runtime_context!=NULL);
    assert(c->reset(c->runtime_context));
    assert(c->get_lap_state(c->runtime_context,&laps,&progress));
    assert(laps==0U&&isfinite(progress)&&progress>=0.0f&&progress<=1.0f);
    assert(c->distance_to_next_finish(c->runtime_context,0.0f,&remaining));
    assert(fabsf(remaining-c->lap_distance)<0.001f);
    c->sample(c->runtime_context,0.0f,c->lap_distance*0.25f,c->road_half_width,
              &x,&y,&z,&w);
    assert(isfinite(x)&&isfinite(y)&&isfinite(z)&&isfinite(w));
    assert(w>=2.2f&&w<=4.8f);
    *sx=x;*sy=y;*sz=z;
    assert(c->advance(c->runtime_context,0.25f,0.0f));
    assert(c->distance_to_next_finish(c->runtime_context,0.25f,&remaining));
    assert(fabsf(remaining-(c->lap_distance-0.25f))<0.001f);
}
int main(void)
{
    unsigned int i,j;
    float x[BOONTA_COURSE_COUNT],y[BOONTA_COURSE_COUNT],z[BOONTA_COURSE_COUNT];
    for(i=0U;i<BOONTA_COURSE_COUNT;i++){
        test_course(boonta_course_catalog[i],&x[i],&y[i],&z[i]);
        for(j=0U;j<i;j++){
            assert(fabsf(x[i]-x[j])+fabsf(y[i]-y[j])+fabsf(z[i]-z[j])>1.0f);
            assert(strcmp(boonta_course_catalog[i]->id,boonta_course_catalog[j]->id)!=0);
        }
    }
    assert(!boonta_course_catalog[0]->has_branches);
    assert(!boonta_course_catalog[1]->has_branches);
    assert(!boonta_course_catalog[2]->has_branches);
    puts("course catalog tests passed");
    return 0;
}
