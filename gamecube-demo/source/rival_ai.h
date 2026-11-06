#ifndef BOONTA_REBORN_RIVAL_AI_H
#define BOONTA_REBORN_RIVAL_AI_H

#include <math.h>

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
    if (isfinite(player_lateral) && fabsf(rival_z - 1.0f) < 5.5f &&
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

#endif
