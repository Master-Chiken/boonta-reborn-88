#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "garage_progression.h"

int main(void)
{
    CareerProfile p;
    RacerVehicleSpec base, tuned;
    career_profile_init(&p);
    assert(garage_race_prize(1U) == 1200U);
    assert(garage_race_prize(8U) == 100U);
    assert(garage_race_prize(0U) == 0U && garage_race_prize(9U) == 0U);
    assert(garage_upgrade_cost(0U) == 500U && garage_upgrade_cost(4U) == 2700U);
    assert(garage_upgrade_cost(5U) == 0U);
    p.credits = 499U;
    assert(!garage_buy_upgrade(&p, GARAGE_SPEED));
    assert(p.credits == 499U && p.upgrade_levels[GARAGE_SPEED] == 0U);
    p.credits = 1200U;
    assert(garage_buy_upgrade(&p, GARAGE_SPEED));
    assert(p.credits == 700U && p.upgrade_levels[GARAGE_SPEED] == 1U);
    memset(&base, 0, sizeof(base));
    base.name = "TEST"; base.top_speed = 50.0f; base.acceleration = 20.0f;
    base.steering = 1.0f; base.grip = 1.0f; base.boost_power = 25.0f;
    base.boost_heat_rate = 30.0f; base.boost_cooling_rate = 20.0f;
    garage_apply_upgrades(&p, &base, &tuned);
    assert(tuned.top_speed > base.top_speed);
    assert(tuned.acceleration == base.acceleration);
    assert(tuned.steering == base.steering && tuned.grip == base.grip);
    assert(tuned.boost_power == base.boost_power);
    assert(!garage_buy_upgrade(0, GARAGE_SPEED));
    assert(!garage_buy_upgrade(&p, (GaragePart)99));
    puts("PASS: race prizes, garage purchase rules, five-level costs and effective pod tuning");
    return 0;
}
