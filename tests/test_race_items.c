#include "race_items.h"
#include "vehicle_catalog.h"
#include <math.h>
#include <stdio.h>
#define CHECK(e) do { if (!(e)) { fprintf(stderr,"FAIL %s:%d: %s\n",__FILE__,__LINE__,#e); return 1; } } while(0)

static void circle(RacerTrackPoint *p,unsigned int n)
{
    unsigned int i;
    const float pi=3.14159265358979323846f;
    for(i=0;i<n;++i){float a=2.0f*pi*(float)i/(float)n;p[i].x=300.0f*cosf(a);p[i].y=0.0f;p[i].z=300.0f*sinf(a);}
}
static int place_at(const RaceItem *it,const RacerTrackPoint *track,unsigned int n,RacerState *p)
{
    float heading;
    CHECK(race_items_get_pose(it,track,n,&p->x,&p->y,&p->z,&heading));
    p->heading=heading;
    { RacerTrackProjection pr=racer_project_to_track(p->x,p->z,track,n);p->track_progress=pr.progress;p->track_distance=sqrtf(pr.distance_sq);p->track_segment=pr.segment; }
    p->offroad=0;
    return 1;
}
int main(void)
{
    RacerTrackPoint track[120]; RacerState p; RaceItem items[RACE_ITEM_COUNT]; unsigned int i,boost_index=RACE_ITEM_COUNT;
    const RacerVehicleSpec *vehicle=vehicle_catalog_get(0U);
    circle(track,120U); racer_init(&p,track,120U); race_items_init(items,RACE_ITEM_COUNT,0U);
    for(i=0;i<RACE_ITEM_COUNT;++i) if(items[i].type==RACE_ITEM_BOOST){boost_index=i;break;}
    CHECK(boost_index<RACE_ITEM_COUNT);
    p.boost_energy=30.0f;
    /* A stale/ambiguous progress value must not collect a pickup from a distant
       point on the same long course merely because normalized progress is close. */
    {
        RaceItem nearby=items[boost_index];
        float heading;
        nearby.progress += 0.010f;
        CHECK(race_items_get_pose(&nearby,track,120U,&p.x,&p.y,&p.z,&heading));
        p.heading=heading;
        {
            RacerTrackProjection pr=racer_project_to_track(p.x,p.z,track,120U);
            p.track_progress=pr.progress; p.track_distance=sqrtf(pr.distance_sq);
            p.track_segment=pr.segment; p.track_lateral_offset=pr.lateral_offset;
        }
        p.offroad=0;
    }
    CHECK(race_items_visible(&items[boost_index],p.lap));
    CHECK(race_items_update(items,RACE_ITEM_COUNT,&p,track,120U,vehicle)==RACE_ITEM_NONE);
    CHECK(place_at(&items[boost_index],track,120U,&p));
    CHECK(race_items_update(items,RACE_ITEM_COUNT,&p,track,120U,vehicle)==RACE_ITEM_BOOST);
    CHECK(p.boost_energy>60.0f);
    CHECK(!race_items_visible(&items[boost_index],p.lap));
    CHECK(race_items_update(items,RACE_ITEM_COUNT,&p,track,120U,vehicle)==RACE_ITEM_NONE);
    p.lap++;
    CHECK(race_items_visible(&items[boost_index],p.lap));
    /* A repair pickup reduces accumulated hull damage. */
    for(i=0;i<RACE_ITEM_COUNT;++i) if(items[i].type==RACE_ITEM_REPAIR){CHECK(place_at(&items[i],track,120U,&p));p.damage=65.0f;CHECK(race_items_update(items,RACE_ITEM_COUNT,&p,track,120U,vehicle)==RACE_ITEM_REPAIR);CHECK(p.damage<40.0f);break;}
    CHECK(i<RACE_ITEM_COUNT);
    /* A hazard increases damage and slows the pod. */
    for(i=0;i<RACE_ITEM_COUNT;++i) if(items[i].type==RACE_ITEM_HAZARD){CHECK(place_at(&items[i],track,120U,&p));p.damage=0.0f;p.speed=30.0f;CHECK(race_items_update(items,RACE_ITEM_COUNT,&p,track,120U,vehicle)==RACE_ITEM_HAZARD);CHECK(p.damage>0.0f && p.speed<25.0f);break;}
    CHECK(i<RACE_ITEM_COUNT);
    puts("PASS: boost pickups, repair pickups, hazards and once-per-lap collection");
    return 0;
}
