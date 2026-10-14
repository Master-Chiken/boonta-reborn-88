#ifndef SWE1R_GARAGE_PROGRESSION_H
#define SWE1R_GARAGE_PROGRESSION_H

#include "career_save.h"
#include "racer_physics.h"

typedef enum {
    GARAGE_SPEED = 0,
    GARAGE_ACCELERATION = 1,
    GARAGE_HANDLING = 2,
    GARAGE_BOOST = 3,
    GARAGE_PART_COUNT = 4
} GaragePart;

unsigned int garage_upgrade_cost(unsigned int current_level);
unsigned int garage_race_prize(unsigned int finishing_place);
int garage_buy_upgrade(CareerProfile *profile, GaragePart part);
void garage_apply_upgrades(const CareerProfile *profile,
                           const RacerVehicleSpec *base,
                           RacerVehicleSpec *effective);
const char *garage_part_name(GaragePart part);

#endif
