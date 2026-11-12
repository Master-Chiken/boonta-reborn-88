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

/*
 * Signed curvature in the track's X/Z plane. Positive means the route bends
 * toward +X (the right-hand side of the rendered road); negative means -X.
 */
static inline float boonta_rival_ai_signed_curvature_from_samples(
    float before_x, float before_z,
    float middle_x, float middle_z,
    float after_x, float after_z)
{
    float first_x, first_z, second_x, second_z;
    float first_length, second_length, cross, dot, angle, curvature;

    if (!isfinite(before_x) || !isfinite(before_z) ||
        !isfinite(middle_x) || !isfinite(middle_z) ||
        !isfinite(after_x) || !isfinite(after_z)) return 0.0f;

    first_x = middle_x - before_x;
    first_z = middle_z - before_z;
    second_x = after_x - middle_x;
    second_z = after_z - middle_z;
    first_length = sqrtf(first_x * first_x + first_z * first_z);
    second_length = sqrtf(second_x * second_x + second_z * second_z);
    if (!isfinite(first_length) || !isfinite(second_length) ||
        first_length <= 0.001f || second_length <= 0.001f) return 0.0f;

    cross = first_x * second_z - first_z * second_x;
    dot = first_x * second_x + first_z * second_z;
    angle = atan2f(cross, dot);
    curvature = -angle / (0.5f * (first_length + second_length));
    return boonta_rival_ai_clamp(curvature, -0.18f, 0.18f);
}

static inline float boonta_rival_ai_curvature_from_samples(
    float before_x, float before_z,
    float middle_x, float middle_z,
    float after_x, float after_z)
{
    return fabsf(boonta_rival_ai_signed_curvature_from_samples(
        before_x, before_z, middle_x, middle_z, after_x, after_z));
}

/*
 * Route samplers accept distance relative to the player's current route cursor.
 * Rival progress is absolute world distance, so subtract the player snapshot
 * before asking for the rival's look-ahead geometry.
 */
static inline float boonta_rival_route_lookahead_offset(
    float player_progress, float rival_progress, float lookahead_distance)
{
    float offset;
    if (!isfinite(player_progress) || player_progress < 0.0f ||
        !isfinite(rival_progress) || rival_progress < 0.0f ||
        !isfinite(lookahead_distance) || lookahead_distance < 0.0f) {
        return 0.0f;
    }
    offset = rival_progress - player_progress + lookahead_distance;
    return isfinite(offset) ? offset : 0.0f;
}

/*
 * Stable racing-line bias: each rival keeps its assigned lane but moves a
 * bounded amount toward the inside of the upcoming bend. Narrow roads reduce
 * both the bias and the allowed lateral envelope.
 */
static inline float boonta_rival_ai_target_line_lateral(
    unsigned int rival_index, float signed_curvature, float road_half_width)
{
    float lane_target;
    float curvature_ratio;
    float max_bias;
    float lateral_limit;

    road_half_width = boonta_rival_ai_clamp(road_half_width, 2.2f, 4.8f);
    signed_curvature = boonta_rival_ai_clamp(signed_curvature, -0.18f, 0.18f);
    lane_target = ((float)(rival_index % 3U) - 1.0f) * 1.25f;
    curvature_ratio = boonta_rival_ai_clamp(signed_curvature / 0.10f, -1.0f, 1.0f);
    max_bias = boonta_rival_ai_clamp((road_half_width - 2.0f) * 0.35f,
                                     0.15f, 0.75f);
    lateral_limit = boonta_rival_ai_clamp(
        road_half_width - 0.65f, 1.0f, BOONTA_RIVAL_AI_LATERAL_LIMIT);
    return boonta_rival_ai_clamp(
        lane_target + curvature_ratio * max_bias,
        -lateral_limit, lateral_limit);
}

static inline float boonta_rival_ai_target_lateral(
    unsigned int rival_index,
    float rival_z,
    float current_lateral,
    float player_lateral,
    const float *other_z,
    const float *other_lateral,
    unsigned int rival_count,
    float signed_curvature,
    float road_half_width)
{
    float target;
    float lateral_limit;
    unsigned int i;
    const int player_position_valid = isfinite(player_lateral);

    if (!isfinite(rival_z)) rival_z = -18.0f;
    current_lateral = boonta_rival_ai_clamp(
        current_lateral, -BOONTA_RIVAL_AI_LATERAL_LIMIT,
        BOONTA_RIVAL_AI_LATERAL_LIMIT);
    player_lateral = boonta_rival_ai_clamp(
        player_lateral, -BOONTA_RIVAL_AI_LATERAL_LIMIT,
        BOONTA_RIVAL_AI_LATERAL_LIMIT);

    road_half_width = boonta_rival_ai_clamp(road_half_width, 2.2f, 4.8f);
    lateral_limit = boonta_rival_ai_clamp(
        road_half_width - 0.65f, 1.0f, BOONTA_RIVAL_AI_LATERAL_LIMIT);

    /* Preserve the assigned lane while biasing toward the upcoming inside line. */
    target = boonta_rival_ai_target_line_lateral(
        rival_index, signed_curvature, road_half_width);

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

    return boonta_rival_ai_clamp(target, -lateral_limit, lateral_limit);
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
 * Rivals need a race pace close to the player's 1.0 top-speed envelope:
 * otherwise they can never reach the finish before a neutral full-throttle run.
 * Skill tiers keep a small deterministic spread; upcoming curvature trims pace
 * gently without making even the fastest rival mathematically uncompetitive.
 * This remains a simple pace controller, not retail physics parity.
 */
static inline float boonta_rival_ai_target_speed(
    unsigned int rival_index, float curvature_radians_per_metre)
{
    const float curvature = boonta_rival_ai_clamp(
        curvature_radians_per_metre, 0.0f, 0.18f);
    const float skill_pace = 0.985f + (float)(rival_index % BOONTA_RIVAL_COUNT) * 0.0075f;
    const float target_speed = skill_pace - curvature * 0.05f;
    return boonta_rival_ai_clamp(target_speed, 0.90f, 1.0f);
}

static inline float boonta_rival_ai_speed_after_frame(
    float current_speed, float target_speed, float frame_scale)
{
    float max_step;
    float delta;

    current_speed = boonta_rival_ai_clamp(current_speed, 0.0f, 1.0f);
    target_speed = boonta_rival_ai_clamp(target_speed, 0.90f, 1.0f);
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
