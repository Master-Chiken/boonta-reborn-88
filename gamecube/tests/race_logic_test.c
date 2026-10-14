#include "race_logic.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>

static RaceInput neutral_input(void)
{
    RaceInput input = {0, 0, 0, 0, 0, 0, 0};
    return input;
}

static void test_reset(void)
{
    RaceState state;
    RaceInput input = neutral_input();
    state.speed = 17.0f;
    state.lane_offset = -2.0f;
    state.angle = 3.0f;
    state.boost_energy = 0.2f;
    state.engine_heat = 0.8f;
    state.completed_laps = 2;
    state.paused = 1;
    state.finished = 1;
    state.boost_active = 1;

    race_reset(&state);
    assert(state.speed == 0.0f);
    assert(state.lane_offset == 0.0f);
    assert(state.angle == 0.0f);
    assert(state.boost_energy == 1.0f);
    assert(state.engine_heat == 0.0f);
    assert(state.completed_laps == 0);
    assert(state.paused == 0);
    assert(state.finished == 0);
    assert(state.boost_active == 0);

    input.reset_pressed = 1;
    state.speed = 9.0f;
    race_update(&state, &input);
    assert(state.speed == 0.0f);
}

static void test_acceleration_braking_and_speed_limit(void)
{
    RaceState state;
    RaceInput input = neutral_input();
    race_reset(&state);

    input.accelerate = 1;
    for (int i = 0; i < 20; ++i) race_update(&state, &input);
    assert(state.speed > 0.0f);
    assert(state.speed <= 48.0f);

    input.accelerate = 0;
    input.brake = 1;
    float before = state.speed;
    race_update(&state, &input);
    assert(state.speed < before);

    state.speed = 47.99f;
    input.brake = 0;
    input.accelerate = 1;
    for (int i = 0; i < 20; ++i) race_update(&state, &input);
    assert(state.speed <= 48.0f);
}

static void test_lane_clamping_and_steering_direction(void)
{
    RaceState state;
    RaceInput input = neutral_input();
    race_reset(&state);

    /* At the start-line angle, left moves outward and right moves inward. */
    input.left = 1;
    for (int i = 0; i < 100; ++i) race_update(&state, &input);
    assert(fabsf(state.lane_offset - 2.7f) < 0.001f);

    input.left = 0;
    input.right = 1;
    for (int i = 0; i < 200; ++i) race_update(&state, &input);
    assert(fabsf(state.lane_offset + 2.7f) < 0.001f);
}

static void test_boost_heat_and_recharge(void)
{
    RaceState state;
    RaceInput input = neutral_input();
    race_reset(&state);
    state.speed = 10.0f;
    input.boost = 1;

    race_update(&state, &input);
    assert(state.boost_active == 1);
    assert(state.speed > 10.0f);
    assert(state.boost_energy < 1.0f);
    assert(state.engine_heat > 0.0f);

    input.boost = 0;
    float fuel_before = state.boost_energy;
    float heat_before = state.engine_heat;
    race_update(&state, &input);
    assert(state.boost_active == 0);
    assert(state.boost_energy > fuel_before);
    assert(state.engine_heat < heat_before);

    state.speed = 10.0f;
    state.engine_heat = 0.99f;
    input.boost = 1;
    race_update(&state, &input);
    assert(state.boost_active == 0);
}

static void test_pause_freezes_motion_and_reset_unpauses(void)
{
    RaceState state;
    RaceInput input = neutral_input();
    race_reset(&state);
    state.speed = 12.0f;
    state.angle = 1.0f;

    input.pause_pressed = 1;
    race_update(&state, &input);
    assert(state.paused == 1);
    float speed = state.speed;
    float angle = state.angle;

    input.pause_pressed = 0;
    input.accelerate = 1;
    race_update(&state, &input);
    assert(state.speed == speed);
    assert(state.angle == angle);

    input.reset_pressed = 1;
    race_update(&state, &input);
    assert(state.paused == 0);
    assert(state.speed == 0.0f);
}

static void test_opponents_progress_and_position(void)
{
    RaceState state;
    RaceInput input = neutral_input();
    float initial_angles[RACE_OPPONENT_COUNT];

    race_reset(&state);
    assert(race_position(&state) == 4);
    for (int i = 0; i < RACE_OPPONENT_COUNT; ++i) {
        initial_angles[i] = state.opponent_angles[i];
    }

    for (int frame = 0; frame < 100; ++frame) {
        race_update(&state, &input);
    }

    for (int i = 0; i < RACE_OPPONENT_COUNT; ++i) {
        assert(state.opponent_angles[i] != initial_angles[i]);
        assert(state.opponent_speeds[i] > 0.0f);
        assert(state.opponent_speeds[i] <= 32.0f);
    }

    /* Moving the player beyond the rivals on the course updates race position. */
    state.angle = 1.0f;
    assert(race_position(&state) == 1);
    assert(race_position(NULL) == 0);
}

static void test_three_lap_finish(void)
{
    RaceState state;
    RaceInput input = neutral_input();
    race_reset(&state);
    state.speed = 20.0f;

    for (int lap = 0; lap < 3; ++lap) {
        state.angle = 6.282f;
        race_update(&state, &input);
        assert(state.completed_laps == lap + 1);
        if (lap < 2) {
            assert(state.finished == 0);
        }
    }
    assert(state.finished == 1);
    assert(state.speed == 0.0f);

    float angle = state.angle;
    input.accelerate = 1;
    race_update(&state, &input);
    assert(state.speed == 0.0f);
    assert(state.angle == angle);
}

int main(void)
{
    test_reset();
    test_acceleration_braking_and_speed_limit();
    test_lane_clamping_and_steering_direction();
    test_boost_heat_and_recharge();
    test_pause_freezes_motion_and_reset_unpauses();
    test_opponents_progress_and_position();
    test_three_lap_finish();
    puts("race_logic_test: 7 suites passed");
    return 0;
}
