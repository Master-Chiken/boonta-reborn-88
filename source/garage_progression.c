#include "garage_progression.h"
#include <string.h>

static const unsigned int g_upgrade_costs[5] = {500U, 900U, 1400U, 2000U, 2700U};
static const unsigned int g_race_prizes[8] = {1200U, 900U, 700U, 500U, 350U, 250U, 150U, 100U};
static const char *g_part_names[GARAGE_PART_COUNT] = {"TOP SPEED", "ACCELERATION", "HANDLING", "BOOST"};

unsigned int garage_upgrade_cost(unsigned int level)
{
    return level < 5U ? g_upgrade_costs[level] : 0U;
}

unsigned int garage_race_prize(unsigned int place)
{
    return place >= 1U && place <= 8U ? g_race_prizes[place - 1U] : 0U;
}

int garage_buy_upgrade(CareerProfile *p, GaragePart part)
{
    unsigned int level, cost;
    if (p == 0 || part < GARAGE_SPEED || part >= GARAGE_PART_COUNT) return 0;
    level = p->upgrade_levels[(unsigned int)part];
    cost = garage_upgrade_cost(level);
    if (cost == 0U || p->credits < cost) return 0;
    p->credits -= cost;
    p->upgrade_levels[(unsigned int)part] = (unsigned char)(level + 1U);
    return 1;
}

void garage_apply_upgrades(const CareerProfile *p, const RacerVehicleSpec *base,
                           RacerVehicleSpec *out)
{
    unsigned int speed, accel, handling, boost;
    if (base == 0 || out == 0) return;
    *out = *base;
    if (p == 0) return;
    speed = p->upgrade_levels[GARAGE_SPEED] > 5U ? 5U : p->upgrade_levels[GARAGE_SPEED];
    accel = p->upgrade_levels[GARAGE_ACCELERATION] > 5U ? 5U : p->upgrade_levels[GARAGE_ACCELERATION];
    handling = p->upgrade_levels[GARAGE_HANDLING] > 5U ? 5U : p->upgrade_levels[GARAGE_HANDLING];
    boost = p->upgrade_levels[GARAGE_BOOST] > 5U ? 5U : p->upgrade_levels[GARAGE_BOOST];
    out->top_speed += (float)speed * 1.15f;
    out->acceleration += (float)accel * 0.72f;
    out->steering *= 1.0f + (float)handling * 0.035f;
    out->grip *= 1.0f + (float)handling * 0.04f;
    out->boost_power += (float)boost * 1.1f;
    out->boost_heat_rate *= 1.0f - (float)boost * 0.035f;
    out->boost_cooling_rate += (float)boost * 0.55f;
}

const char *garage_part_name(GaragePart part)
{
    return part >= GARAGE_SPEED && part < GARAGE_PART_COUNT ? g_part_names[(unsigned int)part] : "UNKNOWN";
}
