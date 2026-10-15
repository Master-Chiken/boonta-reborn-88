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
 /* Extreme inputs must remain inside the normalized speed range. */
 assert(nearf(boonta_speed_after_input(1.0f,1,0),1.0f));
 assert(nearf(boonta_speed_after_input(0.0f,0,1),0.0f));
 assert(nearf(boonta_speed_after_input(-0.5f,0,0),0.0f));
 assert(nearf(boonta_speed_after_input(1.5f,0,0),1.0f));
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

static void steering_inertia_tests(void) {
 /* Neutral input leaves zero lateral velocity at zero. */
 assert(nearf(boonta_lateral_velocity_after_steering(0.0f, 0.0f, 0.0f), 0.0f));

 /* Steering acceleration grows with speed and is symmetric left/right. */
 assert(nearf(boonta_lateral_velocity_after_steering(0.0f, 1.0f, 0.0f), 0.001656f));
 assert(nearf(boonta_lateral_velocity_after_steering(0.0f, -1.0f, 0.0f), -0.001656f));
 assert(nearf(boonta_lateral_velocity_after_steering(0.0f, 1.0f, 1.0f), 0.004416f));
 assert(nearf(boonta_lateral_velocity_after_steering(0.0f, -1.0f, 1.0f), -0.004416f));

 /* Releasing the stick damps existing drift instead of stopping it instantly. */
 assert(nearf(boonta_lateral_velocity_after_steering(0.05f, 0.0f, 0.0f), 0.046f));
 assert(nearf(boonta_lateral_velocity_after_steering(-0.05f, 0.0f, 0.0f), -0.046f));

 /* The post-damping velocity is clamped even for an abnormal starting state. */
 assert(nearf(boonta_lateral_velocity_after_steering(0.2f, 1.0f, 1.0f), 0.085f));
 assert(nearf(boonta_lateral_velocity_after_steering(-0.2f, -1.0f, 1.0f), -0.085f));
}

static void lap_tests(void) {
 assert(boonta_lap_was_crossed(0.0f,119.99f,120.0f)==0);
 assert(boonta_lap_was_crossed(119.99f,120.01f,120.0f)==1);
 assert(boonta_lap_was_crossed(120.0f,120.1f,120.0f)==0);
 assert(boonta_lap_was_crossed(239.99f,240.01f,120.0f)==1);
 assert(boonta_lap_was_crossed(10.0f,9.0f,120.0f)==0);
 assert(boonta_lap_was_crossed(10.0f,20.0f,0.0f)==0);
 assert(boonta_lap_was_crossed(10.0f,20.0f,-120.0f)==0);
 assert(boonta_lap_was_crossed(-1.0f,120.0f,120.0f)==0);
 /* Exact boundary crossings count once; a stationary frame never counts. */
 assert(boonta_lap_was_crossed(119.0f,120.0f,120.0f)==1);
 assert(boonta_lap_was_crossed(120.0f,120.0f,120.0f)==0);
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

 /* Lap count saturates instead of wrapping at UINT_MAX. */
 assert(boonta_lap_count_after_frame(0xffffffffU, 119.0f, 121.0f, 120.0f) == 0xffffffffU);
}


static void rival_event_tests(void) {
 /* The rival only triggers a contact/overtake decision once it reaches the player. */
 assert(boonta_rival_event(-18.0f, 0.0f, 0.0f) == BOONTA_RIVAL_EVENT_NONE);
 assert(boonta_rival_event(-1.0f, 0.0f, 0.0f) == BOONTA_RIVAL_EVENT_NONE);
 assert(boonta_rival_event(-0.99f, 0.0f, 0.0f) == BOONTA_RIVAL_EVENT_COLLISION);
 assert(boonta_rival_event(1.79f, 0.0f, 2.0f) == BOONTA_RIVAL_EVENT_OVERTAKE);
 assert(boonta_rival_event(1.8f, 0.0f, 0.0f) == BOONTA_RIVAL_EVENT_OVERTAKE);
 assert(boonta_rival_event(2.1f, 0.0f, 0.0f) == BOONTA_RIVAL_EVENT_OVERTAKE);

 /* The 0.92 lane-gap boundary is not a collision; it counts as an overtake. */
 assert(boonta_rival_event(0.0f, 0.92f, 0.0f) == BOONTA_RIVAL_EVENT_OVERTAKE);
 assert(boonta_rival_event(0.0f, 0.919f, 0.0f) == BOONTA_RIVAL_EVENT_COLLISION);

 /* Contact penalty is bounded and the lateral response pushes away from the rival. */
 assert(nearf(boonta_speed_after_rival_contact(1.0f), 0.72f));
 assert(nearf(boonta_speed_after_rival_contact(0.1f), 0.0f));
 assert(nearf(boonta_speed_after_rival_contact(0.0f), 0.0f));
 assert(nearf(boonta_rival_contact_nudge(-0.5f, 0.0f), -0.035f));
 assert(nearf(boonta_rival_contact_nudge(0.5f, 0.0f), 0.035f));
 assert(nearf(boonta_rival_contact_nudge(0.0f, 0.0f), -0.035f));
}


static void offroad_and_rail_tests(void) {
 /* No speed loss on the road, including the exact 3.15 boundary. */
 assert(nearf(boonta_speed_after_offroad(0.5f, 0.0f), 0.5f));
 assert(nearf(boonta_speed_after_offroad(0.5f, 3.15f), 0.5f));
 assert(nearf(boonta_speed_after_offroad(0.5f, -3.15f), 0.5f));

 /* The existing off-road drag starts just outside the road edge and is symmetric. */
 assert(nearf(boonta_speed_after_offroad(0.5f, 3.16f), 0.49188f));
 assert(nearf(boonta_speed_after_offroad(0.5f, -3.16f), 0.49188f));
 assert(nearf(boonta_speed_after_offroad(0.01f, 3.85f), 0.0f));
 assert(nearf(boonta_speed_after_offroad(1.0f, 100.0f), 0.0f));

 /* A rail contact triggers strictly beyond +/-3.85 and clamps the lateral position. */
 assert(!boonta_is_past_rail(3.85f));
 assert(!boonta_is_past_rail(-3.85f));
 assert(boonta_is_past_rail(3.851f));
 assert(boonta_is_past_rail(-3.851f));
 assert(nearf(boonta_lateral_after_rail_contact(4.5f), 3.85f));
 assert(nearf(boonta_lateral_after_rail_contact(-4.5f), -3.85f));
 assert(nearf(boonta_lateral_after_rail_contact(3.0f), 3.0f));

 /* The contact reverses and attenuates lateral velocity (bounce-back). */
 assert(nearf(boonta_lateral_velocity_after_rail_contact(0.08f), -0.028f));
 assert(nearf(boonta_lateral_velocity_after_rail_contact(-0.08f), 0.028f));
}

int main(void) {
 speed_tests();
 boost_tests();
 steering_inertia_tests();
 lap_tests();
 three_lap_finish_tests();
 rival_event_tests();
 offroad_and_rail_tests();
 puts("gameplay-state tests passed");
 return 0;
}
