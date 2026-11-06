#ifndef BOONTA_REBORN_RIVAL_AI_H
#define BOONTA_REBORN_RIVAL_AI_H

#include <math.h>
#include "gameplay_state.h"

/*
 * First deterministic opponent controller for the existing camera-space race
 * prototype. It selects a stable lane, avoids nearby traffic, and moves toward
 * that lane at a bounded rate. This is not yet a full route-aware racing AI.
 */
#define BOONTA_RIVAL_AI_LATERAL_LIMIT 2.1f
#define BOONTA_RIVAL_AI_PLAYER_GAP 1.25f
#define BOONTA_RIVAL_AI_TRAFFIC_GAP 1.15f

static inline float boonta_rival_ai_clamp(float value, float low, float high)
{
    if (!isfinite(value)) return 0.0f;
    if (value < low) return low;
    if (value > high) return high;
    return value;
}

static inline float boonta_rival_ai_target_lateral(
    unsigned int rival_index,
    float rival_z,
    float current_lateral,
    float player_lateral,
    const float *other_z,
    const float *other_lateral,
    unsigned int rival_count)
{
    float target;
    unsigned int i;
    const int player_position_valid = isfinite(player_lateral);

    if (!isfinite(rival_z)) rival_z = -18.0f;
    current_lateral = boonta_rival_ai_clamp(
        current_lateral, -BOONTA_RIVAL_AI_LATERAL_LIMIT,
        BOONTA_RIVAL_AI_LATERAL_LIMIT);
    player_lateral = boonta_rival_ai_clamp(
        player_lateral, -BOONTA_RIVAL_AI_LATERAL_LIMIT,
        BOONTA_RIVAL_AI_LATERAL_LIMIT);

    /* Stable three-lane preference prevents all opponents choosing one line. */
    target = ((float)(rival_index % 3U) - 1.0f) * 1.25f;

    /* Avoid the player only when the two racers are close longitudinally. */
    if (player_position_valid && fabsf(rival_z - 1.0f) < 5.5f &&
        fabsf(current_lateral - player_lateral) < BOONTA_RIVAL_AI_PLAYER_GAP) {
        target = player_lateral <= current_lateral ? 1.45f : -1.45f;
    }

    /* Keep a small lateral gap from nearby rivals; ignore distant traffic. */
    if (other_z != 0 && other_lateral != 0) {
        for (i = 0U; i < rival_count; ++i) {
            float longitudinal_gap;
            float lateral_gap;
            if (i == rival_index || !isfinite(other_z[i]) ||
                !isfinite(other_lateral[i])) continue;
            longitudinal_gap = fabsf(rival_z - other_z[i]);
            lateral_gap = current_lateral - other_lateral[i];
            if (longitudinal_gap < 3.5f &&
                fabsf(lateral_gap) < BOONTA_RIVAL_AI_TRAFFIC_GAP) {
                target = current_lateral + (lateral_gap < 0.0f ? -0.75f : 0.75f);
            }
        }
    }

    return boonta_rival_ai_clamp(
        target, -BOONTA_RIVAL_AI_LATERAL_LIMIT,
        BOONTA_RIVAL_AI_LATERAL_LIMIT);
}

static inline float boonta_rival_ai_after_frame(
    float current_lateral, float target_lateral, float frame_scale)
{
    float max_step;
    float delta;

    current_lateral = boonta_rival_ai_clamp(
        current_lateral, -BOONTA_RIVAL_AI_LATERAL_LIMIT,
        BOONTA_RIVAL_AI_LATERAL_LIMIT);
    target_lateral = boonta_rival_ai_clamp(
        target_lateral, -BOONTA_RIVAL_AI_LATERAL_LIMIT,
        BOONTA_RIVAL_AI_LATERAL_LIMIT);
    if (!isfinite(frame_scale) || frame_scale < 0.0f) frame_scale = 0.0f;
    if (frame_scale > 3.0f) frame_scale = 3.0f;

    max_step = 0.035f * frame_scale;
    delta = target_lateral - current_lateral;
    if (delta > max_step) delta = max_step;
    if (delta < -max_step) delta = -max_step;
    return boonta_rival_ai_clamp(
        current_lateral + delta, -BOONTA_RIVAL_AI_LATERAL_LIMIT,
        BOONTA_RIVAL_AI_LATERAL_LIMIT);
}

/*
 * Curvature is estimated from the clean-room track sampler in radians per metre.
 * This first pace model intentionally adjusts speed only; it does not modify
 * the player's physics or claim retail GameCube/Wii physics parity.
 */
static inline float boonta_rival_ai_target_speed(
    unsigned int rival_index, float curvature_radians_per_metre)
{
    const float curvature = boonta_rival_ai_clamp(
        curvature_radians_per_metre, 0.0f, 0.18f);
    const float target_speed = boonta_rival_initial_speed(rival_index) -
                               curvature * 1.8f;
    return boonta_rival_ai_clamp(target_speed, 0.35f, 0.85f);
}

static inline float boonta_rival_ai_speed_after_frame(
    float current_speed, float target_speed, float frame_scale)
{
    float max_step;
    float delta;

    current_speed = boonta_rival_ai_clamp(current_speed, 0.0f, 1.0f);
    target_speed = boonta_rival_ai_clamp(target_speed, 0.35f, 0.85f);
    frame_scale = boonta_sanitize_frame_scale(frame_scale);
    delta = target_speed - current_speed;
    max_step = (delta >= 0.0f ? 0.004f : 0.010f) * frame_scale;
    if (delta > max_step) delta = max_step;
    if (delta < -max_step) delta = -max_step;
    return boonta_rival_ai_clamp(current_speed + delta, 0.0f, 1.0f);
}

static inline float boonta_rival_relative_z_after_frame(
    float rival_z, float player_speed, int player_boost_active,
    float player_pitch_down, float rival_speed, float frame_scale)
{
    float player_motion_scale;
    float player_step;
    float rival_step;
    float next_z;

    if (!isfinite(rival_z)) rival_z = -18.0f;
    player_speed = boonta_rival_ai_clamp(player_speed, 0.0f, 1.0f);
    rival_speed = boonta_rival_ai_clamp(rival_speed, 0.0f, 1.0f);
    player_pitch_down = boonta_rival_ai_clamp(player_pitch_down, -1.0f, 1.0f);
    frame_scale = boonta_sanitize_frame_scale(frame_scale);
    player_motion_scale = 1.0f + player_pitch_down * 0.12f;
    player_step = player_speed * (player_boost_active ? 0.22f : 0.14f) *
                  player_motion_scale;
    rival_step = rival_speed * 0.14f;
    next_z = rival_z + (player_step - rival_step) * frame_scale;
    return isfinite(next_z) ? next_z : -18.0f;
}

#endif
