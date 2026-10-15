#include "race_items.h"
#include "track_catalog.h"
#include <stdio.h>
#include <math.h>
#define CHECK(e) do { if (!(e)) { fprintf(stderr,"FAIL %s:%d: %s\n",__FILE__,__LINE__,#e); return 1; } } while(0)

int main(void)
{
    RaceItem layouts[25][RACE_ITEM_COUNT];
    unsigned int t,i;
    for(t=0;t<25U;++t){
        unsigned int boosts=0U,repairs=0U,hazards=0U;
        race_items_init(layouts[t],RACE_ITEM_COUNT,t);
        CHECK(track_catalog_layout_style(t)<8);
        for(i=0;i<RACE_ITEM_COUNT;++i){
            RaceItem *it=&layouts[t][i];
            CHECK(it->progress>=0.0f && it->progress<1.0f);
            CHECK(fabsf(it->lateral_offset)<=2.5f);
            CHECK(it->collected_lap==0U);
            if(it->type==RACE_ITEM_BOOST) boosts++;
            if(it->type==RACE_ITEM_REPAIR) repairs++;
            if(it->type==RACE_ITEM_HAZARD) hazards++;
        }
        CHECK(boosts>=1U && repairs>=1U && hazards>=1U);
        for(i=0;i<t;++i){
            unsigned int j; int identical=1;
            for(j=0;j<RACE_ITEM_COUNT;++j){
                if(layouts[t][j].type!=layouts[i][j].type ||
                   fabsf(layouts[t][j].progress-layouts[i][j].progress)>0.0001f ||
                   fabsf(layouts[t][j].lateral_offset-layouts[i][j].lateral_offset)>0.0001f)
                    identical=0;
            }
            CHECK(!identical);
        }
    }
    race_items_init(layouts[0],RACE_ITEM_COUNT,0U);
    { RaceItem again[RACE_ITEM_COUNT]; race_items_init(again,RACE_ITEM_COUNT,0U);
      for(i=0;i<RACE_ITEM_COUNT;++i) CHECK(layouts[0][i].progress==again[i].progress && layouts[0][i].type==again[i].type); }
    /* Every layout family should use its own authored pickup rhythm. */
    for(t=0;t<8U;++t){
        unsigned int u;
        int differs=0;
        for(u=0;u<RACE_ITEM_COUNT;++u){
            RaceItem *a=&layouts[t][u], *b=&layouts[(t+1U)%8U][u];
            if(fabsf(a->progress-b->progress)>0.01f ||
               fabsf(a->lateral_offset-b->lateral_offset)>0.01f) differs=1;
        }
        CHECK(differs);
    }
    puts("PASS: all 25 tracks have deterministic, distinct pickup layouts tuned by route family");
    return 0;
}
