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

static void test_lane_clamping(void)
{
    RaceState state;
    RaceInput input = neutral_input();
    race_reset(&state);

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
    test_lane_clamping();
    test_boost_heat_and_recharge();
    test_pause_freezes_motion_and_reset_unpauses();
    test_three_lap_finish();
    puts("race_logic_test: 6 suites passed");
    return 0;
}
