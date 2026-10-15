#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "../source/gameplay_state.h"

static int nearf(float a, float b) { return fabsf(a-b) < 0.00001f; }

static void speed_tests(void) {
 assert(nearf(boonta_speed_after_input(0.0f,1,0),0.012f));
 assert(nearf(boonta_speed_after_input(0.5f,0,0),0.497f));
 assert(nearf(boonta_speed_after_input(0.5f,1,1),0.490f));
 assert(nearf(boonta_speed_after_input(0.0f,0,1),0.0f));
 assert(nearf(boonta_speed_after_input(0.999f,1,0),1.0f));
}

static void boost_tests(void) {
 assert(boonta_boost_should_activate(1,1,0.50f)==1);
 assert(boonta_boost_should_activate(0,1,0.50f)==0);
 assert(boonta_boost_should_activate(1,0,0.50f)==0);
 assert(boonta_boost_should_activate(1,1,0.01f)==0);
 assert(nearf(boonta_boost_after_frame(0.50f,1),0.4945f));
 assert(nearf(boonta_boost_after_frame(0.50f,0),0.5015f));
 assert(nearf(boonta_boost_after_frame(0.003f,1),0.0f));
 assert(nearf(boonta_boost_after_frame(0.999f,0),1.0f));
}

static void lap_tests(void) {
 assert(boonta_lap_was_crossed(0.0f,119.99f,120.0f)==0);
 assert(boonta_lap_was_crossed(119.99f,120.01f,120.0f)==1);
 assert(boonta_lap_was_crossed(120.0f,120.1f,120.0f)==0);
 assert(boonta_lap_was_crossed(239.99f,240.01f,120.0f)==1);
 assert(boonta_lap_was_crossed(10.0f,9.0f,120.0f)==0);
 assert(boonta_lap_was_crossed(10.0f,20.0f,0.0f)==0);
}

static void three_lap_finish_tests(void) {
 unsigned int laps = 0U;
 laps = boonta_lap_count_after_frame(laps, 0.0f, 119.99f, 120.0f);
 assert(laps == 0U);
 assert(!boonta_race_is_finished(laps, 3U));

 laps = boonta_lap_count_after_frame(laps, 119.99f, 120.01f, 120.0f);
 assert(laps == 1U);
 assert(!boonta_race_is_finished(laps, 3U));

 laps = boonta_lap_count_after_frame(laps, 239.99f, 240.01f, 120.0f);
 assert(laps == 2U);
 assert(!boonta_race_is_finished(laps, 3U));

 laps = boonta_lap_count_after_frame(laps, 359.99f, 360.01f, 120.0f);
 assert(laps == 3U);
 assert(boonta_race_is_finished(laps, 3U));
 assert(boonta_race_is_finished(4U, 3U));
 assert(!boonta_race_is_finished(3U, 0U));

 /* No new lap should be counted after movement stops at the finish. */
 laps = boonta_lap_count_after_frame(laps, 360.01f, 360.01f, 120.0f);
 assert(laps == 3U);
}

int main(void) {
 speed_tests();
 boost_tests();
 lap_tests();
 three_lap_finish_tests();
 puts("gameplay-state tests passed");
 return 0;
}
