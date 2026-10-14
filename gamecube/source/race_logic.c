#include "race_logic.h"

#include <math.h>

#define RACE_MAX_SPEED 48.0f
#define RACE_TRACK_RADIUS 22.0f
#define RACE_LAPS 3
#define RACE_TWO_PI 6.28318530717958647692f
#define RACE_REFERENCE_DT (1.0f / 60.0f)
#define RACE_MAX_DT 0.05f

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
    state->race_seconds = 0.0f;
    state->current_lap_seconds = 0.0f;
    state->last_lap_seconds = 0.0f;
    state->best_lap_seconds = 0.0f;
    state->boost_energy = 1.0f;
    state->engine_heat = 0.0f;
    state->completed_laps = 0;
    state->paused = 0;
    state->finished = 0;
    state->boost_active = 0;
    state->collision_cooldown_seconds = 0.0f;
    state->collision_count = 0;

    /* Line up three original, lightweight rival racers just ahead of the player. */
    for (int i = 0; i < RACE_OPPONENT_COUNT; ++i) {
        state->opponent_angles[i] = 0.035f * (float)(i + 1);
        state->opponent_lanes[i] = RACE_OPPONENT_INITIAL_LANES[i];
        state->opponent_speeds[i] = 0.0f;
        state->opponent_laps[i] = 0;
    }
}

static void race_update_dt_internal(RaceState *state, const RaceInput *input,
                                    float delta_seconds, float track_length)
{
    float frame_scale;

    if (state == 0 || input == 0) return;
    if (!isfinite(delta_seconds) || delta_seconds <= 0.0f) {
        delta_seconds = RACE_REFERENCE_DT;
    }
    if (delta_seconds > RACE_MAX_DT) delta_seconds = RACE_MAX_DT;
    frame_scale = delta_seconds * 60.0f;

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

    state->race_seconds += delta_seconds;
    state->current_lap_seconds += delta_seconds;
    if (state->collision_cooldown_seconds > 0.0f) {
        state->collision_cooldown_seconds -= delta_seconds;
        if (state->collision_cooldown_seconds < 0.0f) {
            state->collision_cooldown_seconds = 0.0f;
        }
    }

    /*
     * At the start-line angle, the pod faces +Z and positive radial X projects
     * to screen-left with this camera. Keep lane controls consistent with that.
     */
    if (input->left) state->lane_offset += 0.055f * frame_scale;
    if (input->right) state->lane_offset -= 0.055f * frame_scale;
    state->lane_offset = clamp(state->lane_offset, -2.7f, 2.7f);

    if (input->accelerate) {
        state->speed += 0.20f * frame_scale;
    } else {
        state->speed -= 0.018f * frame_scale;
    }
    if (input->brake) state->speed -= 0.42f * frame_scale;
    state->speed = clamp(state->speed, 0.0f, RACE_MAX_SPEED);

    if (input->boost && state->boost_energy > 0.01f &&
        state->engine_heat < 0.98f && state->speed > 2.0f) {
        state->boost_active = 1;
        state->speed += 0.24f * frame_scale;
        state->boost_energy -= 0.0048f * frame_scale;
        state->engine_heat += 0.0065f * frame_scale;
    } else {
        state->boost_energy += 0.0022f * frame_scale;
        state->engine_heat -= 0.0045f * frame_scale;
    }

    state->speed = clamp(state->speed, 0.0f, RACE_MAX_SPEED);
    state->boost_energy = clamp(state->boost_energy, 0.0f, 1.0f);
    state->engine_heat = clamp(state->engine_heat, 0.0f, 1.0f);

    if (isfinite(track_length) && track_length > 0.001f) {
        /* Speed is world units/second, so progress follows centerline arc length. */
        state->angle += state->speed * delta_seconds * RACE_TWO_PI /
                        track_length;
    } else {
        state->angle += state->speed * delta_seconds /
                        (RACE_TRACK_RADIUS + state->lane_offset);
    }
    if (state->angle >= RACE_TWO_PI) {
        state->angle -= RACE_TWO_PI;
        ++state->completed_laps;
        state->last_lap_seconds = state->current_lap_seconds;
        if (state->best_lap_seconds <= 0.0f ||
            state->last_lap_seconds < state->best_lap_seconds) {
            state->best_lap_seconds = state->last_lap_seconds;
        }
        state->current_lap_seconds = 0.0f;
        if (state->completed_laps >= RACE_LAPS) {
            state->finished = 1;
            state->speed = 0.0f;
        }
    }

    /*
     * Rivals use deterministic target speeds and smooth, bounded lane changes.
     * The small sinusoidal sway makes their movement less static without
     * random behavior, so a race remains reproducible in tests and replays.
     */
    for (int i = 0; i < RACE_OPPONENT_COUNT; ++i) {
        float target_speed = RACE_OPPONENT_TARGET_SPEEDS[i];
        float opponent_total_angle =
            (float)state->opponent_laps[i] * RACE_TWO_PI +
            state->opponent_angles[i];
        float lane_phase =
            (opponent_total_angle - 0.035f * (float)(i + 1)) * 0.65f;
        float radius;

        state->opponent_lanes[i] = clamp(
            RACE_OPPONENT_INITIAL_LANES[i] + 0.42f * sinf(lane_phase),
            -2.4f, 2.4f);
        radius = RACE_TRACK_RADIUS + state->opponent_lanes[i];

        if (state->opponent_speeds[i] < target_speed) {
            state->opponent_speeds[i] += 0.09f * frame_scale;
            if (state->opponent_speeds[i] > target_speed) {
                state->opponent_speeds[i] = target_speed;
            }
        }

        if (isfinite(track_length) && track_length > 0.001f) {
            state->opponent_angles[i] += state->opponent_speeds[i] *
                delta_seconds * RACE_TWO_PI / track_length;
        } else {
            state->opponent_angles[i] +=
                state->opponent_speeds[i] * delta_seconds / radius;
        }
        if (state->opponent_angles[i] >= RACE_TWO_PI) {
            state->opponent_angles[i] -= RACE_TWO_PI;
            ++state->opponent_laps[i];
        }
    }

    /*
     * Simple contact model: close angular and lateral proximity triggers one
     * impact, with a short cooldown so the same pair cannot drain speed every
     * frame. This is intentionally lightweight for the GameCube prototype.
     */
    if (state->collision_cooldown_seconds <= 0.0f && state->speed > 4.0f) {
        for (int i = 0; i < RACE_OPPONENT_COUNT; ++i) {
            float angle_delta = fabsf(state->angle - state->opponent_angles[i]);
            float lane_delta = fabsf(state->lane_offset - state->opponent_lanes[i]);
            if (angle_delta > RACE_TWO_PI - angle_delta) {
                angle_delta = RACE_TWO_PI - angle_delta;
            }

            if (angle_delta < 0.12f && lane_delta < 0.85f) {
                state->speed *= 0.68f;
                state->lane_offset = clamp(
                    state->lane_offset +
                    (state->lane_offset <= state->opponent_lanes[i] ? -0.35f : 0.35f),
                    -2.7f, 2.7f);
                state->collision_cooldown_seconds = 0.85f;
                ++state->collision_count;
                break;
            }
        }
    }
}

void race_update_dt(RaceState *state, const RaceInput *input,
                    float delta_seconds)
{
    race_update_dt_internal(state, input, delta_seconds, 0.0f);
}

void race_update_track_dt(RaceState *state, const RaceInput *input,
                          float delta_seconds, float track_length)
{
    race_update_dt_internal(state, input, delta_seconds, track_length);
}

void race_update(RaceState *state, const RaceInput *input)
{
    race_update_dt(state, input, RACE_REFERENCE_DT);
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
