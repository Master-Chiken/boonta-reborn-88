#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "../source/course_catalog.h"
static void test_course(const BoontaCourseDefinition *c,float *sx,float *sy,float *sz)
{
 float remaining=0.0f,x=0.0f,y=0.0f,z=0.0f,w=0.0f;
 assert(c!=NULL&&c->id!=NULL&&c->display_name!=NULL&&c->region!=NULL);
 assert(isfinite(c->lap_distance)&&c->lap_distance>150.0f);
 assert(c->node_count==8U&&c->edge_count==8U);
 assert(c->reset!=NULL&&c->sample!=NULL&&c->distance_to_next_finish!=NULL);
 assert(c->reset(c->runtime_context));
 assert(c->distance_to_next_finish(c->runtime_context,0.0f,&remaining));
 assert(fabsf(remaining-c->lap_distance)<0.001f);
 c->sample(c->runtime_context,c->lap_distance*0.25f,c->road_half_width,&x,&y,&z,&w);
 assert(isfinite(x)&&isfinite(y)&&isfinite(z)&&isfinite(w));
 assert(w>=2.2f&&w<=4.8f);
 *sx=x;*sy=y;*sz=z;
 assert(c->distance_to_next_finish(c->runtime_context,0.25f,&remaining));
 assert(fabsf(remaining-(c->lap_distance-0.25f))<0.001f);
}
int main(void)
{
 unsigned int i,j;float x[3],y[3],z[3];
 for(i=0;i<BOONTA_COURSE_COUNT;i++){
  test_course(boonta_course_catalog[i],&x[i],&y[i],&z[i]);
  for(j=0;j<i;j++){
   assert(fabsf(x[i]-x[j])+fabsf(y[i]-y[j])+fabsf(z[i]-z[j])>1.0f);
   assert(strcmp(boonta_course_catalog[i]->id,boonta_course_catalog[j]->id)!=0);
  }
 }
 assert(boonta_course_catalog[0]==&boonta_course_canyon_run);
 assert(boonta_course_catalog[1]==&boonta_course_red_dunes);
 assert(boonta_course_catalog[2]==&boonta_course_basalt_spiral);
 puts("course catalog tests passed");return 0;
}
