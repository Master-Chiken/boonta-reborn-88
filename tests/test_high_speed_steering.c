#include "racer_physics.h"
#include <math.h>
#include <stdio.h>
#define CHECK(e) do { if (!(e)) { fprintf(stderr,"FAIL %s:%d: %s\n",__FILE__,__LINE__,#e); return 1; } } while(0)
static void circle(RacerTrackPoint *p,unsigned int n){unsigned int i;const float pi=3.14159265358979323846f;for(i=0;i<n;++i){float a=2.0f*pi*(float)i/(float)n;p[i].x=5000.0f*cosf(a);p[i].y=0.0f;p[i].z=5000.0f*sinf(a);}}
int main(void){RacerTrackPoint track[128];RacerState medium,fast;RacerInput in={0.8f,0.0f,0.0f,0.0f,0.0f};RacerVehicleSpec pod={"TEST",60.0f,20.0f,1.0f,1.0f,24.0f,30.0f,19.0f,13.0f,1.0f,1,1,1};float dm,df;unsigned int i;circle(track,128U);racer_init(&medium,track,128U);racer_init(&fast,track,128U);medium.speed=20.0f;fast.speed=55.0f;for(i=0;i<20U;++i){racer_update_vehicle(&medium,track,128U,&in,&pod,1.0f/60.0f);racer_update_vehicle(&fast,track,128U,&in,&pod,1.0f/60.0f);}dm=fabsf(medium.heading);df=fabsf(fast.heading);CHECK(dm>df);CHECK(df>0.01f);puts("PASS: high-speed steering is calmer while low/mid-speed turning remains more agile");return 0;}
