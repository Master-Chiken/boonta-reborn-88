#include "race_logic.h"

#define RACE_MAX_SPEED 48.0f
#define RACE_TRACK_RADIUS 22.0f
#define RACE_LAPS 3
#define RACE_TWO_PI 6.28318530717958647692f

static const float RACE_OPPONENT_TARGET_SPEEDS[RACE_OPPONENT_COUNT] = {
    28.0f, 32.0f, 30.0f
};
static const float RACE_OPPONENT_INITIAL_LANES[RACE_OPPONENT_COUNT] = {
    -1.8f, 0.0f, 1.8f
};

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

    /* Line up three original, lightweight rival racers just ahead of the player. */
    for (int i = 0; i < RACE_OPPONENT_COUNT; ++i) {
        state->opponent_angles[i] = 0.035f * (float)(i + 1);
        state->opponent_lanes[i] = RACE_OPPONENT_INITIAL_LANES[i];
        state->opponent_speeds[i] = 0.0f;
        state->opponent_laps[i] = 0;
    }
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

    /*
     * At angle zero the pod travels toward +Z; its left side points toward
     * the inside of the ring (-X). Keep left/right consistent with that basis.
     */
    if (input->left) state->lane_offset -= 0.055f;
    if (input->right) state->lane_offset += 0.055f;
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

    /* Rivals use deterministic target speeds so tests and races are repeatable. */
    for (int i = 0; i < RACE_OPPONENT_COUNT; ++i) {
        float target_speed = RACE_OPPONENT_TARGET_SPEEDS[i];
        float radius = RACE_TRACK_RADIUS + state->opponent_lanes[i];

        if (state->opponent_speeds[i] < target_speed) {
            state->opponent_speeds[i] += 0.09f;
            if (state->opponent_speeds[i] > target_speed) {
                state->opponent_speeds[i] = target_speed;
            }
        }

        state->opponent_angles[i] +=
            state->opponent_speeds[i] * 0.016f / radius;
        if (state->opponent_angles[i] >= RACE_TWO_PI) {
            state->opponent_angles[i] -= RACE_TWO_PI;
            ++state->opponent_laps[i];
        }
    }
}

int race_position(const RaceState *state)
{
    float player_progress;
    int position = 1;

    if (state == 0) return 0;

    player_progress = (float)state->completed_laps * RACE_TWO_PI +
                      state->angle;
    for (int i = 0; i < RACE_OPPONENT_COUNT; ++i) {
        float opponent_progress =
            (float)state->opponent_laps[i] * RACE_TWO_PI +
            state->opponent_angles[i];
        if (opponent_progress > player_progress) {
            ++position;
        }
    }

    return position;
}
