#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "../source/rival_ai.h"

static int nearf_ai(float a, float b)
{
    return fabsf(a - b) < 0.0001f;
}

static void lane_preference_is_deterministic(void)
{
    const float z[3] = {-18.0f, -34.0f, -50.0f};
    const float lateral[3] = {0.0f, 0.0f, 0.0f};
    assert(nearf_ai(boonta_rival_ai_target_lateral(0U, -18.0f, 0.0f, 0.0f, z, lateral, 3U), -1.25f));
    assert(nearf_ai(boonta_rival_ai_target_lateral(1U, -34.0f, 0.0f, 0.0f, z, lateral, 3U), 0.0f));
    assert(nearf_ai(boonta_rival_ai_target_lateral(2U, -50.0f, 0.0f, 0.0f, z, lateral, 3U), 1.25f));
}

static void player_avoidance_only_when_close(void)
{
    const float z[3] = {-18.0f, -2.0f, -40.0f};
    const float lateral[3] = {0.0f, 0.0f, 0.0f};
    float target = boonta_rival_ai_target_lateral(1U, -2.0f, 0.0f, -0.2f, z, lateral, 3U);
    assert(target > 0.0f);
    target = boonta_rival_ai_target_lateral(1U, -18.0f, 0.0f, -0.2f, z, lateral, 3U);
    assert(nearf_ai(target, 0.0f));

    /* A non-finite player position must not be treated as a real center-lane car. */
    target = boonta_rival_ai_target_lateral(1U, -2.0f, 0.0f, NAN, z, lateral, 3U);
    assert(nearf_ai(target, 0.0f));
}

static void nearby_rival_avoidance(void)
{
    const float z[3] = {-10.0f, -11.0f, -40.0f};
    const float lateral[3] = {0.1f, 0.0f, 0.0f};
    const float target = boonta_rival_ai_target_lateral(0U, -10.0f, 0.1f, 0.0f, z, lateral, 3U);
    assert(target > 0.1f);
}

static void movement_is_bounded_and_time_scaled(void)
{
    assert(nearf_ai(boonta_rival_ai_after_frame(0.0f, 1.0f, 1.0f), 0.035f));
    assert(nearf_ai(boonta_rival_ai_after_frame(0.0f, 1.0f, 2.0f), 0.070f));
    assert(nearf_ai(boonta_rival_ai_after_frame(0.0f, 1.0f, NAN), 0.0f));
    assert(nearf_ai(boonta_rival_ai_after_frame(2.0f, 4.0f, 1.0f), 2.035f));
    assert(nearf_ai(boonta_rival_ai_after_frame(-4.0f, -1.0f, 1.0f), -2.065f));
}

static void invalid_inputs_recover_safely(void)
{
    const float z[1] = {NAN};
    const float lateral[1] = {INFINITY};
    const float target = boonta_rival_ai_target_lateral(
        0U, NAN, NAN, INFINITY, z, lateral, 1U);
    assert(isfinite(target));
    assert(target >= -BOONTA_RIVAL_AI_LATERAL_LIMIT);
    assert(target <= BOONTA_RIVAL_AI_LATERAL_LIMIT);
}

static void curvature_reduces_target_speed(void)
{
    const float straight = boonta_rival_ai_target_speed(1U, 0.0f);
    const float bend = boonta_rival_ai_target_speed(1U, 0.10f);
    assert(nearf_ai(straight, boonta_rival_initial_speed(1U)));
    assert(bend < straight);
    assert(nearf_ai(boonta_rival_ai_target_speed(1U, NAN), straight));
    assert(nearf_ai(boonta_rival_ai_target_speed(1U, -0.10f), straight));
}

static void speed_response_is_bounded_and_asymmetric(void)
{
    assert(nearf_ai(boonta_rival_ai_speed_after_frame(0.50f, 0.70f, 1.0f), 0.504f));
    assert(nearf_ai(boonta_rival_ai_speed_after_frame(0.70f, 0.50f, 1.0f), 0.690f));
    assert(nearf_ai(boonta_rival_ai_speed_after_frame(0.50f, 0.70f, 2.0f), 0.508f));
    assert(nearf_ai(boonta_rival_ai_speed_after_frame(NAN, 0.70f, 1.0f), 0.004f));
    assert(nearf_ai(boonta_rival_ai_speed_after_frame(0.70f, 0.50f, NAN), 0.70f));
}

static void relative_progress_uses_player_and_rival_pace(void)
{
    assert(nearf_ai(boonta_rival_relative_z_after_frame(
        -18.0f, 1.0f, 0, 0.0f, 0.5f, 1.0f), -17.93f));
    assert(nearf_ai(boonta_rival_relative_z_after_frame(
        -18.0f, 0.5f, 0, 0.0f, 1.0f, 1.0f), -18.07f));
    assert(nearf_ai(boonta_rival_relative_z_after_frame(
        -18.0f, 0.5f, 1, 0.0f, 0.5f, 1.0f), -17.96f));
    assert(nearf_ai(boonta_rival_relative_z_after_frame(
        -18.0f, 0.5f, 0, 1.0f, 0.5f, 1.0f), -17.9916f));
    assert(nearf_ai(boonta_rival_relative_z_after_frame(
        NAN, NAN, 0, NAN, INFINITY, 1.0f), -18.0f));
}

int main(void)
{
    lane_preference_is_deterministic();
    player_avoidance_only_when_close();
    nearby_rival_avoidance();
    movement_is_bounded_and_time_scaled();
    invalid_inputs_recover_safely();
    curvature_reduces_target_speed();
    speed_response_is_bounded_and_asymmetric();
    relative_progress_uses_player_and_rival_pace();
    puts("rival AI tests: PASS");
    return 0;
}
