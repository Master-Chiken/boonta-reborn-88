#include "race_flow.h"

static float clamp_delta(float dt)
{
    /* Reject NaN as well as negative deltas before they reach race timers.
       The comparison form is C99/libogc-friendly and also clamps +infinity. */
    if (!(dt >= 0.0f)) return 0.0f;
    if (dt > 0.10f) return 0.10f;
    return dt;
}

void race_flow_init(RaceFlow *flow, unsigned int target_laps)
{
    if (flow == 0) return;
    flow->phase = RACE_PHASE_COUNTDOWN;
    flow->countdown_remaining = 3.60f;
    flow->race_elapsed = 0.0f;
    flow->target_laps = target_laps > 0U ? target_laps : 3U;
}

void race_flow_update(RaceFlow *flow, float dt, unsigned int player_lap)
{
    if (flow == 0) return;
    dt = clamp_delta(dt);
    if (flow->phase == RACE_PHASE_COUNTDOWN) {
        flow->countdown_remaining -= dt;
        if (flow->countdown_remaining <= 0.0f) {
            flow->countdown_remaining = 0.0f;
            flow->phase = RACE_PHASE_RUNNING;
        }
    } else if (flow->phase == RACE_PHASE_RUNNING) {
        flow->race_elapsed += dt;
        if (player_lap > flow->target_laps) flow->phase = RACE_PHASE_FINISHED;
    }
}

int race_flow_countdown_label(const RaceFlow *flow)
{
    if (flow == 0 || flow->phase != RACE_PHASE_COUNTDOWN) return 0;
    if (flow->countdown_remaining > 2.60f) return 3;
    if (flow->countdown_remaining > 1.60f) return 2;
    if (flow->countdown_remaining > 0.60f) return 1;
    return 0; /* GO */
}
