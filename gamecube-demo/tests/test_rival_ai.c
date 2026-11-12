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
    assert(nearf_ai(boonta_rival_ai_target_lateral(0U, -18.0f, 0.0f, 0.0f, z, lateral, 3U, 0.0f, 3.4f), -1.25f));
    assert(nearf_ai(boonta_rival_ai_target_lateral(1U, -34.0f, 0.0f, 0.0f, z, lateral, 3U, 0.0f, 3.4f), 0.0f));
    assert(nearf_ai(boonta_rival_ai_target_lateral(2U, -50.0f, 0.0f, 0.0f, z, lateral, 3U, 0.0f, 3.4f), 1.25f));
}

static void player_avoidance_only_when_close(void)
{
    const float z[3] = {-40.0f, -2.0f, -50.0f};
    const float lateral[3] = {0.0f, 0.0f, 0.0f};
    float target = boonta_rival_ai_target_lateral(1U, -2.0f, 0.0f, -0.2f, z, lateral, 3U, 0.0f, 3.4f);
    assert(target > 0.0f);
    target = boonta_rival_ai_target_lateral(1U, -18.0f, 0.0f, -0.2f, z, lateral, 3U, 0.0f, 3.4f);
    assert(nearf_ai(target, 0.0f));

    /* A non-finite player position must not be treated as a real center-lane car. */
    target = boonta_rival_ai_target_lateral(1U, -2.0f, 0.0f, NAN, z, lateral, 3U, 0.0f, 3.4f);
    assert(nearf_ai(target, 0.0f));
}

static void nearby_rival_avoidance(void)
{
    const float z[3] = {-10.0f, -11.0f, -40.0f};
    const float lateral[3] = {0.1f, 0.0f, 0.0f};
    const float target = boonta_rival_ai_target_lateral(0U, -10.0f, 0.1f, 0.0f, z, lateral, 3U, 0.0f, 3.4f);
    assert(target > 0.1f);
}

static void closest_rival_conflict_wins_independent_of_array_order(void)
{
    const float first_z[3] = {-18.0f, -17.0f, -15.0f};
    const float first_lateral[3] = {0.0f, 0.8f, -0.8f};
    const float reversed_z[3] = {-18.0f, -15.0f, -17.0f};
    const float reversed_lateral[3] = {0.0f, -0.8f, 0.8f};
    const float first_target = boonta_rival_ai_target_lateral(
        0U, -18.0f, 0.0f, 0.0f, first_z, first_lateral, 3U, 0.0f, 3.4f);
    const float reversed_target = boonta_rival_ai_target_lateral(
        0U, -18.0f, 0.0f, 0.0f, reversed_z, reversed_lateral,
        3U, 0.0f, 3.4f);

    /* The closer rival needs a left move in both roster arrangements. */
    assert(nearf_ai(first_target, -0.75f));
    assert(nearf_ai(reversed_target, -0.75f));
}

static void tied_rivals_split_traffic_lanes_deterministically(void)
{
    const float z[2] = {-18.0f, -17.0f};
    const float lateral[2] = {0.0f, 0.0f};
    const float first_target = boonta_rival_ai_target_lateral(
        0U, -18.0f, 0.0f, 0.0f, z, lateral, 2U, 0.0f, 3.4f);
    const float second_target = boonta_rival_ai_target_lateral(
        1U, -17.0f, 0.0f, 0.0f, z, lateral, 2U, 0.0f, 3.4f);

    assert(nearf_ai(boonta_rival_ai_traffic_avoidance_offset(0U, 1U, 0.0f),
                    -0.75f));
    assert(nearf_ai(boonta_rival_ai_traffic_avoidance_offset(1U, 0U, 0.0f),
                    0.75f));
    assert(nearf_ai(boonta_rival_ai_traffic_avoidance_offset(0U, 1U, NAN),
                    -0.75f));
    assert(nearf_ai(boonta_rival_ai_traffic_avoidance_offset(1U, 0U, 0.20f),
                    0.75f));
    assert(first_target < 0.0f);
    assert(second_target > 0.0f);
    assert(nearf_ai(first_target, -second_target));
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
        0U, NAN, NAN, INFINITY, z, lateral, 1U, 0.0f, 3.4f);
    assert(isfinite(target));
    assert(target >= -BOONTA_RIVAL_AI_LATERAL_LIMIT);
    assert(target <= BOONTA_RIVAL_AI_LATERAL_LIMIT);
}

static void signed_curvature_selects_inside_line(void)
{
    const float center_lane = boonta_rival_ai_target_line_lateral(1U, 0.0f, 3.4f);
    const float right_bend = boonta_rival_ai_target_line_lateral(1U, 0.10f, 3.4f);
    const float left_bend = boonta_rival_ai_target_line_lateral(1U, -0.10f, 3.4f);
    const float narrow_right_bend = boonta_rival_ai_target_line_lateral(1U, 0.10f, 2.2f);

    assert(nearf_ai(center_lane, 0.0f));
    assert(right_bend > center_lane);
    assert(left_bend < center_lane);
    assert(fabsf(narrow_right_bend) <= 1.55f);
    assert(right_bend <= 2.1f);
    assert(left_bend >= -2.1f);
}

static void signed_curvature_preserves_turn_direction(void)
{
    const float turns_right = boonta_rival_ai_signed_curvature_from_samples(
        0.0f, 0.0f, 0.0f, 2.0f, 1.0f, 4.0f);
    const float turns_left = boonta_rival_ai_signed_curvature_from_samples(
        0.0f, 0.0f, 0.0f, 2.0f, -1.0f, 4.0f);
    assert(turns_right > 0.0f);
    assert(turns_left < 0.0f);
    assert(nearf_ai(fabsf(turns_right), fabsf(turns_left)));
}

static void curvature_samples_are_measured_and_bounded(void)
{
    const float straight = boonta_rival_ai_curvature_from_samples(
        -2.0f, 0.0f, 0.0f, 0.0f, 2.0f, 0.0f);
    const float gentle_bend = boonta_rival_ai_curvature_from_samples(
        -2.0f, 0.0f, 0.0f, 0.0f, 1.93185165f, 0.51763809f);
    const float sharp_bend = boonta_rival_ai_curvature_from_samples(
        -2.0f, 0.0f, 0.0f, 0.0f, 0.0f, 2.0f);

    assert(nearf_ai(straight, 0.0f));
    assert(nearf_ai(gentle_bend, 0.1308997f));
    assert(nearf_ai(sharp_bend, 0.18f));
    assert(nearf_ai(boonta_rival_ai_curvature_from_samples(
        NAN, 0.0f, 0.0f, 0.0f, 2.0f, 0.0f), 0.0f));
    assert(nearf_ai(boonta_rival_ai_curvature_from_samples(
        0.0f, 0.0f, 0.0f, 0.0f, 2.0f, 0.0f), 0.0f));
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

static void rival_personalities_are_stable_and_distinct(void)
{
    assert(nearf_ai(boonta_rival_ai_personality_speed_bias(0U), -0.025f));
    assert(nearf_ai(boonta_rival_ai_personality_speed_bias(1U), 0.0f));
    assert(nearf_ai(boonta_rival_ai_personality_speed_bias(2U), 0.020f));
    assert(nearf_ai(boonta_rival_ai_personality_speed_bias(3U), 0.010f));
    assert(nearf_ai(boonta_rival_ai_personality_speed_bias(4U), -0.010f));
    assert(nearf_ai(boonta_rival_ai_personality_speed_bias(5U),
                    boonta_rival_ai_personality_speed_bias(0U)));

    assert(boonta_rival_ai_personality_curve_sensitivity(0U) >
           boonta_rival_ai_personality_curve_sensitivity(2U));
    assert(nearf_ai(boonta_rival_ai_personality_curve_sensitivity(6U),
                    boonta_rival_ai_personality_curve_sensitivity(1U)));

    /* The aggressive profile gains pace on straights and lifts less in bends. */
    assert(boonta_rival_ai_target_speed(2U, 0.0f) >
           boonta_rival_initial_speed(2U));
    assert(boonta_rival_ai_target_speed(2U, 0.10f) <
           boonta_rival_ai_target_speed(2U, 0.0f));
    assert(nearf_ai(boonta_rival_ai_target_speed(1U, 0.10f),
                    boonta_rival_initial_speed(1U) - 0.18f));
    assert(boonta_rival_ai_target_speed(0U, 0.10f) <
           boonta_rival_ai_target_speed(2U, 0.10f));
}

static void rival_personalities_choose_distinct_racing_lines(void)
{
    const float bend = 0.10f;
    const float cautious = boonta_rival_ai_target_line_lateral(0U, bend, 3.4f);
    const float balanced = boonta_rival_ai_target_line_lateral(1U, bend, 3.4f);
    const float aggressive = boonta_rival_ai_target_line_lateral(2U, bend, 3.4f);

    assert(nearf_ai(boonta_rival_ai_personality_line_commitment(0U), 0.75f));
    assert(nearf_ai(boonta_rival_ai_personality_line_commitment(1U), 1.0f));
    assert(nearf_ai(boonta_rival_ai_personality_line_commitment(2U), 1.25f));
    assert(nearf_ai(boonta_rival_ai_personality_line_commitment(5U), 0.75f));
    assert(cautious < balanced);
    assert(balanced < aggressive);
    assert(aggressive <= BOONTA_RIVAL_AI_LATERAL_LIMIT);
    assert(boonta_rival_ai_target_line_lateral(2U, -bend, 3.4f) < 1.25f);
    assert(aggressive > 1.25f);
}

static void nemesis_memory_gently_increases_rival_pace(void)
{
    const float base = boonta_rival_ai_target_speed(1U, 0.0f);
    assert(nearf_ai(boonta_rival_ai_nemesis_pace_bonus(0U), 0.0f));
    assert(nearf_ai(boonta_rival_ai_nemesis_pace_bonus(25U), 0.01f));
    assert(nearf_ai(boonta_rival_ai_nemesis_pace_bonus(100U), 0.04f));
    assert(nearf_ai(boonta_rival_ai_nemesis_pace_bonus(1000U), 0.04f));
    assert(boonta_rival_ai_target_speed_with_rivalry(1U, 0.0f, 50U) > base);
    assert(nearf_ai(boonta_rival_ai_target_speed_with_rivalry(1U, 0.0f, 1000U),
                    boonta_rival_ai_target_speed_with_rivalry(1U, 0.0f, 100U)));
    assert(nearf_ai(boonta_rival_ai_target_speed_with_rivalry(1U, NAN, 0U), base));
    assert(boonta_rival_ai_target_speed_with_rivalry(2U, 0.0f, 100U) <= 0.85f);
}

static void nemesis_memory_changes_racing_line_without_defeating_avoidance(void)
{
    const float other_z[2] = {-18.0f, -17.0f};
    const float other_lateral[2] = {0.0f, 0.0f};
    const float base = boonta_rival_ai_target_lateral(
        0U, -18.0f, 0.0f, 0.0f, 0, 0, 1U, 0.10f, 3.4f);
    const float committed = boonta_rival_ai_target_lateral_with_rivalry(
        0U, -18.0f, 0.0f, 0.0f, 0, 0, 1U, 0.10f, 3.4f, 100U);

    assert(nearf_ai(boonta_rival_ai_nemesis_line_bonus(0U), 0.0f));
    assert(nearf_ai(boonta_rival_ai_nemesis_line_bonus(100U), 0.25f));
    assert(nearf_ai(boonta_rival_ai_nemesis_line_bonus(1000U), 0.25f));
    assert(nearf_ai(boonta_rival_ai_target_lateral_with_rivalry(
        0U, -18.0f, 0.0f, 0.0f, 0, 0, 1U, 0.10f, 3.4f, 0U), base));
    assert(committed > base);
    assert(nearf_ai(boonta_rival_ai_target_lateral_with_rivalry(
        0U, -18.0f, 0.0f, 0.0f, 0, 0, 1U, -0.10f, 3.4f, 100U),
        boonta_rival_ai_target_lateral(
            0U, -18.0f, 0.0f, 0.0f, 0, 0, 1U, -0.10f, 3.4f) - 0.25f));

    /* Close player and rival traffic avoidance always take priority. */
    assert(nearf_ai(boonta_rival_ai_target_lateral_with_rivalry(
        0U, 1.5f, 0.0f, 0.0f, 0, 0, 1U, 0.10f, 3.4f, 100U),
        boonta_rival_ai_target_lateral(
            0U, 1.5f, 0.0f, 0.0f, 0, 0, 1U, 0.10f, 3.4f)));
    assert(nearf_ai(boonta_rival_ai_target_lateral_with_rivalry(
        0U, -18.0f, 0.0f, 0.0f, other_z, other_lateral, 2U,
        0.10f, 3.4f, 100U),
        boonta_rival_ai_target_lateral(
            0U, -18.0f, 0.0f, 0.0f, other_z, other_lateral, 2U,
            0.10f, 3.4f)));
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
    closest_rival_conflict_wins_independent_of_array_order();
    tied_rivals_split_traffic_lanes_deterministically();
    movement_is_bounded_and_time_scaled();
    invalid_inputs_recover_safely();
    curvature_samples_are_measured_and_bounded();
    signed_curvature_selects_inside_line();
    signed_curvature_preserves_turn_direction();
    curvature_reduces_target_speed();
    rival_personalities_are_stable_and_distinct();
    rival_personalities_choose_distinct_racing_lines();
    nemesis_memory_gently_increases_rival_pace();
    nemesis_memory_changes_racing_line_without_defeating_avoidance();
    speed_response_is_bounded_and_asymmetric();
    relative_progress_uses_player_and_rival_pace();
    puts("rival AI tests: PASS");
    return 0;
}
