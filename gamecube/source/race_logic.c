#include "race_logic.h"

#define RACE_MAX_SPEED 48.0f
#define RACE_TRACK_RADIUS 22.0f
#define RACE_LAPS 3
#define RACE_TWO_PI 6.28318530717958647692f

static float clamp(float value, float low, float high)
{
    if (value < low) return low;
    if (value > high) return high;
    return value;
}

void race_reset(RaceState *state)
{
    if (state == 0) return;

    state->speed = 0.0f;
    state->lane_offset = 0.0f;
    state->angle = 0.0f;
    state->boost_energy = 1.0f;
    state->engine_heat = 0.0f;
    state->completed_laps = 0;
    state->paused = 0;
    state->finished = 0;
    state->boost_active = 0;
}

void race_update(RaceState *state, const RaceInput *input)
{
    if (state == 0 || input == 0) return;

    state->boost_active = 0;

    if (input->reset_pressed) {
        race_reset(state);
        return;
    }

    if (input->pause_pressed && !state->finished) {
        state->paused = !state->paused;
    }
    if (state->paused || state->finished) {
        return;
    }

    if (input->left) state->lane_offset += 0.055f;
    if (input->right) state->lane_offset -= 0.055f;
    state->lane_offset = clamp(state->lane_offset, -2.7f, 2.7f);

    if (input->accelerate) {
        state->speed += 0.20f;
    } else {
        state->speed -= 0.018f;
    }
    if (input->brake) state->speed -= 0.42f;
    state->speed = clamp(state->speed, 0.0f, RACE_MAX_SPEED);

    if (input->boost && state->boost_energy > 0.01f &&
        state->engine_heat < 0.98f && state->speed > 2.0f) {
        state->boost_active = 1;
        state->speed += 0.24f;
        state->boost_energy -= 0.0048f;
        state->engine_heat += 0.0065f;
    } else {
        state->boost_energy += 0.0022f;
        state->engine_heat -= 0.0045f;
    }

    state->speed = clamp(state->speed, 0.0f, RACE_MAX_SPEED);
    state->boost_energy = clamp(state->boost_energy, 0.0f, 1.0f);
    state->engine_heat = clamp(state->engine_heat, 0.0f, 1.0f);

    state->angle += state->speed * 0.016f /
                    (RACE_TRACK_RADIUS + state->lane_offset);
    if (state->angle >= RACE_TWO_PI) {
        state->angle -= RACE_TWO_PI;
        ++state->completed_laps;
        if (state->completed_laps >= RACE_LAPS) {
            state->finished = 1;
            state->speed = 0.0f;
        }
    }
}
