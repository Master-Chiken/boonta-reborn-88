#ifndef BOONTA_REBORN_COURSE_RUNTIME_IMPL_H
#define BOONTA_REBORN_COURSE_RUNTIME_IMPL_H
#include <math.h>
#include <string.h>
#ifndef BOONTA_COURSE_SYMBOL
#error "Define BOONTA_COURSE_SYMBOL before including course_runtime_impl.h"
#endif
#ifndef BOONTA_COURSE_ID
#error "Define BOONTA_COURSE_ID before including course_runtime_impl.h"
#endif
#ifndef BOONTA_COURSE_DISPLAY_NAME
#error "Define BOONTA_COURSE_DISPLAY_NAME before including course_runtime_impl.h"
#endif
#ifndef BOONTA_COURSE_REGION
#error "Define BOONTA_COURSE_REGION before including course_runtime_impl.h"
#endif
#ifndef BOONTA_COURSE_DEFAULT_HALF_WIDTH
#error "Define BOONTA_COURSE_DEFAULT_HALF_WIDTH before including course_runtime_impl.h"
#endif
typedef struct { BoontaRouteGraphSampler sampler; } BoontaCourseRuntimeContext;
static BoontaCourseRuntimeContext g_boonta_course_runtime_context;
static int boonta_course_runtime_reset(void *runtime_context)
{
    BoontaCourseRuntimeContext *context=(BoontaCourseRuntimeContext *)runtime_context;
    if(context==NULL)return 0;
    if(context->sampler.lengths_ready)return 1;
    memset(&context->sampler,0,sizeof(context->sampler));
    return boonta_route_graph_sampler_prepare(&context->sampler);
}
static void boonta_course_runtime_sample(void *runtime_context,float travelled,
    float fallback_half_width,float *x,float *y,float *z,float *width)
{
    BoontaCourseRuntimeContext *context=(BoontaCourseRuntimeContext *)runtime_context;
    if (context == NULL || !context->sampler.lengths_ready) {
        if (x != NULL) *x = 0.0f;
        if (y != NULL) *y = 0.0f;
        if (z != NULL) *z = 0.0f;
        if (width != NULL) *width = fallback_half_width;
        return;
    }
    boonta_route_graph_sampler_sample_at(&context->sampler,travelled,
        fallback_half_width,x,y,z,width);
}
static int boonta_course_runtime_distance_to_next_finish(void *runtime_context,
    float player_distance,float *distance)
{
    BoontaCourseRuntimeContext *context=(BoontaCourseRuntimeContext *)runtime_context;
    float next_finish;
    if(context==NULL||distance==NULL||!context->sampler.lengths_ready||
       !isfinite(player_distance)||player_distance<0.0f||
       !isfinite(context->sampler.total_length)||context->sampler.total_length<=0.001f)return 0;
    next_finish=(floorf(player_distance/context->sampler.total_length)+1.0f)*
                context->sampler.total_length;
    *distance=next_finish-player_distance;
    return isfinite(*distance)&&*distance>=0.0f;
}
const BoontaCourseDefinition BOONTA_COURSE_SYMBOL={
    BOONTA_COURSE_ID,BOONTA_COURSE_DISPLAY_NAME,BOONTA_COURSE_REGION,
    BOONTA_RUNTIME_ROUTE_LENGTH,BOONTA_COURSE_DEFAULT_HALF_WIDTH,
    BOONTA_RUNTIME_ROUTE_NODE_COUNT,BOONTA_RUNTIME_ROUTE_EDGE_COUNT,
    boonta_course_runtime_reset,boonta_course_runtime_sample,
    boonta_course_runtime_distance_to_next_finish,&g_boonta_course_runtime_context
};
#endif
