/* Track pickups turn line choice into a small risk/reward decision each lap. */
#include "race_items.h"
#include "track_catalog.h"
#include <math.h>
#include <string.h>

#define RACE_ITEM_PICKUP_RADIUS 4.5f
#define RACE_ITEM_PICKUP_RADIUS_SQ (RACE_ITEM_PICKUP_RADIUS * RACE_ITEM_PICKUP_RADIUS)
#define RACE_ITEM_INVALID_DISTANCE_SQ 3.402823466e+38F

/* Four authored pickup roles are arranged differently on every circuit.
 * Track-specific offsets keep layouts deterministic while avoiding a repeated
 * four-track cycle. Values remain inside the road for the full 25-track roster. */
static const RaceItemType g_item_types[RACE_ITEM_COUNT] = {
    RACE_ITEM_BOOST, RACE_ITEM_REPAIR, RACE_ITEM_HAZARD, RACE_ITEM_BOOST
};
/* Pickup timing follows the rhythm of each procedural route family. Fast
 * layouts place boost opportunities on straights; technical layouts spread
 * rewards around the lap and keep hazards away from a single repeated point. */
static const float g_item_progress_by_style[8][RACE_ITEM_COUNT] = {
    {0.10f, 0.32f, 0.57f, 0.80f}, /* canyon */
    {0.14f, 0.36f, 0.61f, 0.84f}, /* rounded rectangle */
    {0.08f, 0.29f, 0.53f, 0.76f}, /* chicane */
    {0.12f, 0.34f, 0.59f, 0.82f}, /* switchback */
    {0.17f, 0.39f, 0.63f, 0.86f}, /* asymmetric */
    {0.06f, 0.30f, 0.58f, 0.82f}, /* long oval */
    {0.11f, 0.33f, 0.56f, 0.79f}, /* hairpin */
    {0.09f, 0.27f, 0.52f, 0.75f}  /* serpentine */
};
static const float g_item_lanes[8][RACE_ITEM_COUNT] = {
    {-2.0f,  1.8f,  0.0f, -2.4f},
    { 0.0f, -2.2f,  2.0f,  1.8f},
    { 2.0f,  0.0f, -2.0f,  2.4f},
    {-2.4f,  2.2f,  1.8f,  0.0f},
    { 1.8f, -1.8f,  0.0f,  2.2f},
    {-1.8f,  2.4f, -2.2f,  0.0f},
    { 2.4f, -2.0f,  1.8f, -1.8f},
    { 0.0f,  1.8f, -2.4f,  2.0f}
};

static float clamp_item(float v, float lo, float hi)
{
    if(v<lo) return lo;
    if(v>hi) return hi;
    return v;
}

static float progress_gap(float a, float b)
{
    float d=fabsf(a-b);
    return d>0.5f ? 1.0f-d : d;
}

void race_items_init(RaceItem *items, unsigned int count, unsigned int track_index)
{
    unsigned int i;
    float progress_shift;
    if(items==0) return;
    if(track_index>=25U) track_index=0U;
    if(count>RACE_ITEM_COUNT) count=RACE_ITEM_COUNT;
    progress_shift=(float)(track_index%5U)*0.0025f;
    for(i=0;i<count;++i){
        unsigned int style=(unsigned int)track_catalog_layout_style(track_index);
        unsigned int lane_set=(style + track_index/8U + i/3U)%8U;
        items[i].type=g_item_types[(i+(track_index%4U))%RACE_ITEM_COUNT];
        items[i].progress=g_item_progress_by_style[style][i]+progress_shift;
        if(items[i].progress>=0.98f) items[i].progress-=0.08f;
        items[i].lateral_offset=g_item_lanes[lane_set][i];
        /* Boosts on fast routes favour wider lines; technical routes mix
         * inside and outside lanes to make the player choose a racing line. */
        if(style==TRACK_LAYOUT_LONG_OVAL && items[i].type==RACE_ITEM_BOOST)
            items[i].lateral_offset*=0.55f;
        else if((style==TRACK_LAYOUT_CHICANE || style==TRACK_LAYOUT_SERPENTINE) && i==2U)
            items[i].lateral_offset*=0.82f;
        /* Small deterministic variation keeps same-family circuits distinct. */
        if(((track_index+i)%3U)==1U) items[i].lateral_offset*=0.72f;
        items[i].collected_lap=0U;
    }
}

RaceItemType race_items_update(RaceItem *items, unsigned int count,
                               RacerState *player, const RacerTrackPoint *track,
                               unsigned int track_count,
                               const RacerVehicleSpec *vehicle)
{
    unsigned int i;
    RacerTrackProjection projection;
    if(items==0 || player==0 || track==0 || track_count<3U) return RACE_ITEM_NONE;
    if(count>RACE_ITEM_COUNT) count=RACE_ITEM_COUNT;
    if(player->offroad || player->track_distance>7.0f) return RACE_ITEM_NONE;
    /* Derive item proximity from the current world position and a continuity-aware
       track projection. Progress alone can be stale for a frame or ambiguous at a
       crossing, which previously allowed pickups from a remote section of the lap. */
    projection=racer_project_to_track_near(player->x,player->z,track,track_count,
                                           player->track_segment);
    if(projection.distance_sq==RACE_ITEM_INVALID_DISTANCE_SQ) return RACE_ITEM_NONE;
    for(i=0;i<count;++i){
        RaceItem *it=&items[i];
        float item_x,item_y,item_z,item_heading;
        float dx,dy,dz,distance_sq;
        if(it->collected_lap==player->lap) continue;
        if(progress_gap(projection.progress,it->progress)>0.0125f) continue;
        if(fabsf(projection.lateral_offset-it->lateral_offset)>3.0f) continue;
        if(!race_items_get_pose(it,track,track_count,&item_x,&item_y,&item_z,&item_heading))
            continue;
        (void)item_heading;
        dx=player->x-item_x;
        dy=player->y-item_y;
        dz=player->z-item_z;
        distance_sq=dx*dx+dy*dy+dz*dz;
        if(!(distance_sq<=RACE_ITEM_PICKUP_RADIUS_SQ)) continue;
        it->collected_lap=player->lap;
        if(it->type==RACE_ITEM_BOOST){
            player->boost_energy=clamp_item(player->boost_energy+34.0f,0.0f,100.0f);
            player->boost_heat=clamp_item(player->boost_heat-15.0f,0.0f,100.0f);
            player->speed+=4.0f;
        }else if(it->type==RACE_ITEM_REPAIR){
            player->damage=clamp_item(player->damage-35.0f,0.0f,100.0f);
            player->boost_energy=clamp_item(player->boost_energy+10.0f,0.0f,100.0f);
        }else if(it->type==RACE_ITEM_HAZARD){
            racer_apply_impact(player,vehicle,14.0f,0.72f);
            player->boost_heat=clamp_item(player->boost_heat+12.0f,0.0f,100.0f);
            if(player->boost_heat>=100.0f){player->overheated=1;player->boost_active=0;}
        }
        return it->type;
    }
    return RACE_ITEM_NONE;
}

int race_items_get_pose(const RaceItem *item, const RacerTrackPoint *track,
                        unsigned int count, float *x, float *y,
                        float *z, float *heading)
{
    float total=0.0f, target, accumulated=0.0f;
    unsigned int i;
    if(item==0 || track==0 || count<2U || x==0 || y==0 || z==0 || heading==0) return 0;
    for(i=0;i<count;++i){
        const RacerTrackPoint *a=&track[i], *b=&track[(i+1U)%count];
        float dx=b->x-a->x, dz=b->z-a->z;
        total+=sqrtf(dx*dx+dz*dz);
    }
    if(total<1.0e-5f) return 0;
    target=clamp_item(item->progress,0.0f,1.0f)*total;
    for(i=0;i<count;++i){
        const RacerTrackPoint *a=&track[i], *b=&track[(i+1U)%count];
        float dx=b->x-a->x, dz=b->z-a->z, len=sqrtf(dx*dx+dz*dz);
        if(len>1.0e-5f && target<=accumulated+len){
            float t=clamp_item((target-accumulated)/len,0.0f,1.0f);
            float nx=dz/len,nz=-dx/len;
            *x=a->x+dx*t+nx*item->lateral_offset;
            *y=a->y+(b->y-a->y)*t+0.20f;
            *z=a->z+dz*t+nz*item->lateral_offset;
            *heading=atan2f(dx,dz);
            return 1;
        }
        accumulated+=len;
    }
    return 0;
}

int race_items_visible(const RaceItem *item, unsigned int player_lap)
{
    return item!=0 && item->type!=RACE_ITEM_NONE && item->collected_lap!=player_lap;
}
