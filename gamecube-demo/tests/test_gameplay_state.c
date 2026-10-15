#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "../source/gameplay_state.h"

static int nearf(float a, float b) { return fabsf(a-b) < 0.00001f; }


static void frame_scale_tests(void) {
 assert(nearf(boonta_frame_scale_from_delta(1.0f / 60.0f), 1.0f));
 assert(nearf(boonta_frame_scale_from_delta(1.0f / 50.0f), 1.2f));
 assert(nearf(boonta_frame_scale_from_delta(1.0f), 3.0f));
 assert(nearf(boonta_frame_scale_from_delta(0.0f), 1.0f));
 assert(nearf(boonta_frame_scale_from_delta(-0.01f), 1.0f));
 assert(nearf(boonta_frame_scale_from_delta(NAN), 1.0f));
 assert(nearf(boonta_frame_scale_from_delta(INFINITY), 3.0f));
}

static void cadence_consistency_tests(void) {
 float speed60 = 0.5f, speed50 = 0.5f;
 float boost60 = 0.8f, boost50 = 0.8f;
 float heat60 = 0.2f, heat50 = 0.2f;
 float lateral60 = 0.05f, lateral50 = 0.05f;
 float distance60 = 0.0f, distance50 = 0.0f;
 unsigned int i;

 /* One simulated second: 60 nominal frames versus 50 PAL-rate frames. */
 for (i = 0U; i < 60U; ++i) {
  const int accelerating = i < 24U;
  const int braking = i >= 48U;
  speed60 = boonta_speed_after_input_scaled(speed60, accelerating, braking, 1.0f);
  boost60 = boonta_boost_after_frame_scaled(boost60, 1, 1.0f);
  heat60 = boonta_engine_heat_after_frame_scaled(heat60, 1, 1.0f);
  lateral60 = boonta_lateral_velocity_after_steering_scaled(lateral60, 0.0f, 0.0f, 1.0f);
  distance60 = boonta_distance_after_frame_scaled(distance60, 0.5f, 0, 1.0f);
 }
 for (i = 0U; i < 50U; ++i) {
  const int accelerating = i < 20U;
  const int braking = i >= 40U;
  speed50 = boonta_speed_after_input_scaled(speed50, accelerating, braking, 1.2f);
  boost50 = boonta_boost_after_frame_scaled(boost50, 1, 1.2f);
  heat50 = boonta_engine_heat_after_frame_scaled(heat50, 1, 1.2f);
  lateral50 = boonta_lateral_velocity_after_steering_scaled(lateral50, 0.0f, 0.0f, 1.2f);
  distance50 = boonta_distance_after_frame_scaled(distance50, 0.5f, 0, 1.2f);
 }

 assert(nearf(speed60, speed50));
 assert(nearf(boost60, boost50));
 assert(nearf(heat60, heat50));
 assert(nearf(lateral60, lateral50));
 assert(nearf(distance60, distance50));
}

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

static void boost_overheat_tests(void) {
 /* Heat rises under boost, cools when released, and remains clamped. */
 assert(nearf(boonta_engine_heat_after_frame(0.50f, 1), 0.5065f));
 assert(nearf(boonta_engine_heat_after_frame(0.50f, 0), 0.4955f));
 assert(nearf(boonta_engine_heat_after_frame(0.999f, 1), 1.0f));
 assert(nearf(boonta_engine_heat_after_frame(0.003f, 0), 0.0f));

 /* Boost cannot start above the heat limit or while overheat is latched. */
 assert(boonta_boost_should_activate_with_heat(1, 1, 0.50f, 0.50f, 0));
 assert(!boonta_boost_should_activate_with_heat(1, 1, 0.50f, 0.98f, 0));
 assert(!boonta_boost_should_activate_with_heat(1, 1, 0.50f, 0.30f, 1));
 assert(!boonta_boost_should_activate_with_heat(1, 1, 0.01f, 0.30f, 0));

 /* Enter lockout at 98%, retain it while hot, and re-enable only at 60%. */
 assert(!boonta_boost_overheated_after_frame(0, 0.979f));
 assert(boonta_boost_overheated_after_frame(0, 0.98f));
 assert(boonta_boost_overheated_after_frame(1, 0.85f));
 assert(boonta_boost_overheated_after_frame(1, 0.6001f));
 assert(!boonta_boost_overheated_after_frame(1, 0.60f));

 /* A full cooldown cycle must not pulse boost on/off around the 98% boundary. */
 {
  float heat = 0.97f;
  int overheated = 0;
  int frames = 0;
  while (!overheated && frames < 10) {
   int active = boonta_boost_should_activate_with_heat(1, 1, 1.0f, heat, overheated);
   assert(active);
   heat = boonta_engine_heat_after_frame(heat, active);
   overheated = boonta_boost_overheated_after_frame(overheated, heat);
   ++frames;
  }
  assert(overheated && heat >= 0.98f);
  frames = 0;
  while (overheated && frames < 100) {
   assert(!boonta_boost_should_activate_with_heat(1, 1, 1.0f, heat, overheated));
   heat = boonta_engine_heat_after_frame(heat, 0);
   overheated = boonta_boost_overheated_after_frame(overheated, heat);
   ++frames;
  }
  assert(!overheated && heat <= 0.60f);
  assert(boonta_boost_should_activate_with_heat(1, 1, 1.0f, heat, overheated));
 }
}

static void steering_input_tests(void) {
 /* The analog stick maps its signed byte range to a normalized steering value. */
 assert(nearf(boonta_steering_input(0.0f, 0, 0), 0.0f));
 assert(nearf(boonta_steering_input(64.0f, 0, 0), 0.5f));
 assert(nearf(boonta_steering_input(-64.0f, 0, 0), -0.5f));
 assert(nearf(boonta_steering_input(127.0f, 0, 0), 127.0f / 128.0f));
 assert(nearf(boonta_steering_input(-128.0f, 0, 0), -1.0f));

 /* D-pad steering adds to analog input, with bounded saturation. */
 assert(nearf(boonta_steering_input(0.0f, 1, 0), -0.7f));
 assert(nearf(boonta_steering_input(0.0f, 0, 1), 0.7f));
 assert(nearf(boonta_steering_input(64.0f, 1, 0), -0.2f));
 assert(nearf(boonta_steering_input(-64.0f, 0, 1), 0.2f));
 assert(nearf(boonta_steering_input(127.0f, 0, 1), 1.0f));
 assert(nearf(boonta_steering_input(-128.0f, 1, 0), -1.0f));

 /* Simultaneous opposite D-pad directions cancel; valid stick input remains. */
 assert(nearf(boonta_steering_input(0.0f, 1, 1), 0.0f));
 assert(nearf(boonta_steering_input(32.0f, 1, 1), 0.25f));
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

static void distance_progression_tests(void) {
 assert(nearf(boonta_distance_after_frame(0.0f, 0.5f, 0), 0.07f));
 assert(nearf(boonta_distance_after_frame(0.0f, 0.5f, 1), 0.11f));
 assert(nearf(boonta_distance_after_frame(10.0f, 1.0f, 0), 10.14f));
 assert(nearf(boonta_distance_after_frame(10.0f, 1.0f, 1), 10.22f));
}

/* Deterministic straight-line frame simulation: exercises the same speed,
 * boost, distance and lap helpers called by the native GameCube loop.
 * This is a host regression test, not proof of live controller or hardware input. */
static void simulated_three_lap_run_tests(void) {
 float distance = 0.0f;
 float speed = 0.0f;
 float boost = 1.0f;
 float heat = 0.0f;
 unsigned int laps = 0U;
 unsigned int frames = 0U;
 int overheated = 0;
 int finished = 0;

 while (!finished && frames < 5000U) {
  const int boost_active = boonta_boost_should_activate_with_heat(1, 1, boost, heat, overheated);
  const float previous_distance = distance;
  boost = boonta_boost_after_frame(boost, boost_active);
  heat = boonta_engine_heat_after_frame(heat, boost_active);
  overheated = boonta_boost_overheated_after_frame(overheated, heat);
  speed = boonta_speed_after_input(speed, 1, 0);
  distance = boonta_distance_after_frame(distance, speed, boost_active);
  laps = boonta_lap_count_after_frame(laps, previous_distance, distance, 120.0f);
  finished = boonta_race_is_finished(laps, 3U);
  if (finished) speed = 0.0f;
  ++frames;
 }

 assert(frames > 0U && frames < 5000U);
 assert(finished == 1);
 assert(laps == 3U);
 assert(distance >= 360.0f);
 assert(nearf(speed, 0.0f));
}

int main(void) {
 frame_scale_tests();
 cadence_consistency_tests();
 speed_tests();
 boost_tests();
 boost_overheat_tests();
 steering_input_tests();
 steering_inertia_tests();
 lap_tests();
 three_lap_finish_tests();
 distance_progression_tests();
 simulated_three_lap_run_tests();
 rival_event_tests();
 offroad_and_rail_tests();
 puts("gameplay-state tests passed");
 return 0;
}
