/* Lightweight slipstream mechanic: reward staying behind a rival, not contact. */
#include "draft_assist.h"
#include <math.h>

#define DRAFT_MIN_FORWARD 3.0f
#define DRAFT_MAX_FORWARD 25.0f
#define DRAFT_MAX_LATERAL 3.6f
#define DRAFT_RECHARGE_PER_SECOND 10.5f

static float draft_clamp(float v, float lo, float hi)
{
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

int draft_assist_update(RacerState *player, const RivalAIState *rivals,
                        unsigned int rival_count, float dt)
{
    unsigned int i;
    float sin_heading, cos_heading;
    if (player == 0 || rivals == 0 || rival_count == 0U) return 0;
    dt = draft_clamp(dt, 0.0f, 0.05f);
    if (dt <= 0.0f) return 0;
    if (rival_count > 7U) rival_count = 7U;
    sin_heading = sinf(player->heading);
    cos_heading = cosf(player->heading);
    for (i = 0U; i < rival_count; ++i) {
        float dx = rivals[i].x - player->x;
        float dz = rivals[i].z - player->z;
        float forward = dx*sin_heading + dz*cos_heading;
        float lateral = dx*cos_heading - dz*sin_heading;
        float distance_sq = dx*dx + dz*dz;
        if (forward >= DRAFT_MIN_FORWARD && forward <= DRAFT_MAX_FORWARD &&
            fabsf(lateral) <= DRAFT_MAX_LATERAL &&
            distance_sq <= DRAFT_MAX_FORWARD*DRAFT_MAX_FORWARD) {
            player->boost_energy = draft_clamp(
                player->boost_energy + DRAFT_RECHARGE_PER_SECOND*dt, 0.0f, 100.0f);
            return 1;
        }
    }
    return 0;
}
