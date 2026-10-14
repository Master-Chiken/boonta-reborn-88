#ifndef SWE1R_RACE_ITEMS_H
#define SWE1R_RACE_ITEMS_H

#include "racer_physics.h"

#ifdef __cplusplus
extern "C" {
#endif

#define RACE_ITEM_COUNT 4U

typedef enum {
    RACE_ITEM_NONE = 0,
    RACE_ITEM_BOOST = 1,
    RACE_ITEM_REPAIR = 2,
    RACE_ITEM_HAZARD = 3
} RaceItemType;

typedef struct {
    RaceItemType type;
    float progress;
    float lateral_offset;
    unsigned int collected_lap;
} RaceItem;

void race_items_init(RaceItem *items, unsigned int count, unsigned int track_index);
RaceItemType race_items_update(RaceItem *items, unsigned int count,
                               RacerState *player, const RacerTrackPoint *track,
                               unsigned int track_count,
                               const RacerVehicleSpec *vehicle);
int race_items_get_pose(const RaceItem *item, const RacerTrackPoint *track,
                        unsigned int track_count, float *x, float *y,
                        float *z, float *heading);
int race_items_visible(const RaceItem *item, unsigned int player_lap);

#ifdef __cplusplus
}
#endif
#endif
