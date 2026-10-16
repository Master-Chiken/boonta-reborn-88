#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "../source/gameplay_state.h"

static int nearf(float a, float b) { return fabsf(a-b) < 0.00001f; }


static void finite_clamp_tests(void) {
 assert(nearf(boonta_clamp_finite_float(0.04f, -0.085f, 0.085f), 0.04f));
 assert(nearf(boonta_clamp_finite_float(0.12f, -0.085f, 0.085f), 0.085f));
 assert(nearf(boonta_clamp_finite_float(-0.12f, -0.085f, 0.085f), -0.085f));
 assert(nearf(boonta_clamp_finite_float(NAN, -0.085f, 0.085f), 0.0f));
 assert(nearf(boonta_clamp_finite_float(INFINITY, -0.085f, 0.085f), 0.0f));
 assert(nearf(boonta_clamp_finite_float(-INFINITY, -0.085f, 0.085f), 0.0f));
}

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
 float offroad60 = 0.8f, offroad50 = 0.8f;
 float move_velocity60 = 0.01f, move_velocity50 = 0.01f;
 float lateral_position60 = 0.0f, lateral_position50 = 0.0f;
 float rival_z60 = -18.0f, rival_z50 = -18.0f;
 unsigned int i;

 /* One second: accelerate for 0.4 s, coast for 0.4 s, brake for 0.2 s. */
 for (i = 0U; i < 60U; ++i) {
  const int accelerating = i < 24U;
  const int braking = i >= 48U;
  speed60 = boonta_speed_after_input_scaled(speed60, accelerating, braking, 1.0f);
  boost60 = boonta_boost_after_frame_scaled(boost60, 1, 1.0f);
  heat60 = boonta_engine_heat_after_frame_scaled(heat60, 1, 1.0f);
  lateral60 = boonta_lateral_velocity_after_steering_scaled(lateral60, 0.0f, 0.0f, 1.0f);
  distance60 = boonta_distance_after_frame_scaled(distance60, 0.5f, 0, 1.0f);
  offroad60 = boonta_speed_after_offroad_scaled(offroad60, 3.5f, 1.0f);
  move_velocity60 = boonta_lateral_velocity_after_steering_scaled(move_velocity60, 0.2f, 0.5f, 1.0f);
  lateral_position60 = boonta_lateral_position_after_frame(lateral_position60, move_velocity60, 1.0f);
  rival_z60 = boonta_rival_z_after_frame(rival_z60, 0.5f, 1.0f);
 }
 for (i = 0U; i < 50U; ++i) {
  const int accelerating = i < 20U;
  const int braking = i >= 40U;
  speed50 = boonta_speed_after_input_scaled(speed50, accelerating, braking, 1.2f);
  boost50 = boonta_boost_after_frame_scaled(boost50, 1, 1.2f);
  heat50 = boonta_engine_heat_after_frame_scaled(heat50, 1, 1.2f);
  lateral50 = boonta_lateral_velocity_after_steering_scaled(lateral50, 0.0f, 0.0f, 1.2f);
  distance50 = boonta_distance_after_frame_scaled(distance50, 0.5f, 0, 1.2f);
  offroad50 = boonta_speed_after_offroad_scaled(offroad50, 3.5f, 1.2f);
  move_velocity50 = boonta_lateral_velocity_after_steering_scaled(move_velocity50, 0.2f, 0.5f, 1.2f);
  lateral_position50 = boonta_lateral_position_after_frame(lateral_position50, move_velocity50, 1.2f);
  rival_z50 = boonta_rival_z_after_frame(rival_z50, 0.5f, 1.2f);
 }

 assert(nearf(speed60, speed50));
 assert(nearf(boost60, boost50));
 assert(nearf(heat60, heat50));
 assert(nearf(lateral60, lateral50));
 assert(nearf(distance60, distance50));
 assert(nearf(offroad60, offroad50));
 assert(fabsf(rival_z60 - rival_z50) < 0.0001f); /* bounded float accumulation drift */
 assert(fabsf(lateral_position60 - lateral_position50) < 0.005f);
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
 /* The unscaled public wrapper must also recover from non-finite state. */
 assert(nearf(boonta_speed_after_input(NAN, 1, 0), 0.012f));
 assert(nearf(boonta_speed_after_input(INFINITY, 0, 0), 0.0f));
 assert(nearf(boonta_speed_after_input(-INFINITY, 1, 0), 0.012f));
 /* The scaled speed helper must recover from invalid state without NaN propagation. */
 assert(nearf(boonta_speed_after_input_scaled(NAN, 1, 0, 1.0f), 0.012f));
 assert(nearf(boonta_speed_after_input_scaled(INFINITY, 0, 0, 1.0f), 0.0f));
 assert(nearf(boonta_speed_after_input_scaled(-INFINITY, 1, 0, 1.0f), 0.012f));
 /* Invalid frame scales must not poison the speed state with NaN/inf. */
 assert(nearf(boonta_speed_after_input_scaled(0.5f, 1, 0, NAN), 0.5f));
 assert(nearf(boonta_speed_after_input_scaled(0.5f, 1, 0, INFINITY), 0.5f));
 assert(nearf(boonta_speed_after_input_scaled(0.5f, 1, 0, -INFINITY), 0.5f));
 assert(nearf(boonta_speed_after_input_scaled(0.5f, 1, 0, -1.0f), 0.5f));
 /* The native loop uses the scaled helper directly; invalid state must not leak. */
 assert(nearf(boonta_speed_after_input_scaled(NAN,1,0,1.0f),0.012f));
 assert(nearf(boonta_speed_after_input_scaled(INFINITY,0,0,1.0f),0.0f));
 assert(nearf(boonta_speed_after_input_scaled(-INFINITY,1,0,1.2f),0.0144f));
}

static void boost_tests(void) {
 assert(boonta_boost_should_activate(1,1,0.50f)==1);
 assert(boonta_boost_should_activate(0,1,0.50f)==0);
 assert(boonta_boost_should_activate(1,0,0.50f)==0);
 assert(boonta_boost_should_activate(1,1,0.01f)==0);
 assert(nearf(boonta_boost_after_frame(0.50f,1),0.4945f));
 assert(nearf(boonta_boost_after_frame(0.50f,0),0.5015f));
 assert(nearf(boonta_boost_after_frame(0.003f,1),0.0f));
 /* Invalid boost resource recovers; invalid time scale contributes no change. */
 assert(nearf(boonta_boost_after_frame_scaled(NAN, 0, 1.0f), 0.0015f));
 assert(nearf(boonta_boost_after_frame_scaled(INFINITY, 1, 1.0f), 0.0f));
 assert(nearf(boonta_boost_after_frame_scaled(0.5f, 1, NAN), 0.5f));
 assert(nearf(boonta_boost_after_frame_scaled(0.5f, 0, -1.0f), 0.5f));
 assert(nearf(boonta_boost_after_frame(0.999f,0),1.0f));
}

static void boost_overheat_tests(void) {
 /* Heat rises under boost, cools when released, and remains clamped. */
 assert(nearf(boonta_engine_heat_after_frame(0.50f, 1), 0.5065f));
 assert(nearf(boonta_engine_heat_after_frame(0.50f, 0), 0.4955f));
 assert(nearf(boonta_engine_heat_after_frame(0.999f, 1), 1.0f));
 assert(nearf(boonta_engine_heat_after_frame(0.003f, 0), 0.0f));
 /* Invalid heat resource recovers; invalid time scale contributes no change. */
 assert(nearf(boonta_engine_heat_after_frame_scaled(NAN, 1, 1.0f), 0.0065f));
 assert(nearf(boonta_engine_heat_after_frame_scaled(INFINITY, 0, 1.0f), 0.0f));
 assert(nearf(boonta_engine_heat_after_frame_scaled(0.5f, 1, NAN), 0.5f));
 assert(nearf(boonta_engine_heat_after_frame_scaled(0.5f, 0, -1.0f), 0.5f));

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
 /* Non-finite analog input is treated as a neutral stick, not NaN steering. */
 assert(nearf(boonta_steering_input(NAN, 0, 0), 0.0f));
 assert(nearf(boonta_steering_input(INFINITY, 0, 0), 0.0f));
 assert(nearf(boonta_steering_input(-INFINITY, 0, 0), 0.0f));
 assert(nearf(boonta_steering_input(NAN, 1, 0), -0.7f));

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


static void pitch_tradeoff_tests(void) {
 /* Centered/noisy input is neutral; stick-up maps to nose-down. */
 assert(nearf(boonta_pitch_input(0.0f), 0.0f));
 assert(nearf(boonta_pitch_input(12.0f), 0.0f));
 assert(nearf(boonta_pitch_input(-16.0f), 0.0f));
 assert(nearf(boonta_pitch_input(72.0f), 56.0f / 111.0f));
 assert(nearf(boonta_pitch_input(-72.0f), -0.5f));
 assert(nearf(boonta_pitch_input(127.0f), 1.0f));
 assert(nearf(boonta_pitch_input(-128.0f), -1.0f));
 assert(nearf(boonta_pitch_input(NAN), 0.0f));
 assert(nearf(boonta_pitch_input(INFINITY), 0.0f));

 /* Nose-down trades steering authority for faster progress; nose-up does the opposite. */
 assert(nearf(boonta_steering_after_pitch(0.5f, 0.0f), 0.5f));
 assert(nearf(boonta_steering_after_pitch(0.5f, 1.0f), 0.3f));
 assert(nearf(boonta_steering_after_pitch(0.5f, -1.0f), 0.675f));
 assert(nearf(boonta_steering_after_pitch(1.0f, -1.0f), 1.0f));
 assert(nearf(boonta_steering_after_pitch(NAN, 0.8f), 0.0f));
 assert(nearf(boonta_steering_after_pitch(0.5f, NAN), 0.5f));

 /* Compare actual forward progress at the same throttle/speed and frame scale. */
 {
  const float neutral = boonta_distance_after_pitch_scaled(0.0f, 0.5f, 0, 0.0f, 1.0f);
  const float nose_down = boonta_distance_after_pitch_scaled(0.0f, 0.5f, 0, 1.0f, 1.0f);
  const float nose_up = boonta_distance_after_pitch_scaled(0.0f, 0.5f, 0, -1.0f, 1.0f);
  assert(nearf(neutral, 0.07f));
  assert(nearf(nose_down, 0.0784f));
  assert(nearf(nose_up, 0.0616f));
  assert(nose_down > neutral && neutral > nose_up);

  /* Pitch is elapsed-time scaled, and boost's greater base motion is preserved. */
  assert(nearf(
      boonta_distance_after_pitch_scaled(0.0f, 0.5f, 1, 1.0f, 1.0f),
      0.1232f));
  assert(nearf(
      boonta_distance_after_pitch_scaled(0.0f, 0.5f, 0, 1.0f, 1.2f),
      0.09408f));
  assert(nearf(
      boonta_distance_after_pitch_scaled(0.0f, 0.5f, 0, NAN, 1.0f),
      0.07f));
  assert(nearf(
      boonta_distance_after_pitch_scaled(10.0f, 0.5f, 0, 1.0f, NAN),
      10.0f));
 }
}



static void track_scroll_tests(void) {
 const float road_length = 2.8f;
 const float wall_length = 10.0f;

 assert(nearf(boonta_track_scroll_offset(0.0f, road_length), 0.0f));
 assert(nearf(boonta_track_scroll_offset(2.7f, road_length), 2.7f));
 assert(nearf(boonta_track_scroll_offset(2.8f, road_length), 0.0f));
 assert(boonta_track_section_index(2.799f, road_length) == 0U);
 assert(boonta_track_section_index(2.8f, road_length) == 1U);
 assert(boonta_track_section_index(9.999f, wall_length) == 0U);
 assert(boonta_track_section_index(10.0f, wall_length) == 1U);

 /* The world-space phase of adjacent segments is continuous at scroll wrap. */
 {
  const float before_distance = 2.799f;
  const float before_scroll = boonta_track_scroll_offset(before_distance, road_length);
  const float before_z = 4.0f + before_scroll - road_length;
  const float before_phase = boonta_track_phase(before_distance, before_z);
  const float after_distance = road_length;
  const float after_z = 4.0f + boonta_track_scroll_offset(after_distance, road_length);
  const float after_phase = boonta_track_phase(after_distance, after_z);
  assert(nearf(before_phase, after_phase));

  const float before_wall_distance = 9.999f;
  const float before_wall_z = -10.0f +
      boonta_track_scroll_offset(before_wall_distance, wall_length) - wall_length;
  const float before_wall_phase = boonta_track_phase(before_wall_distance, before_wall_z);
  const float after_wall_phase = boonta_track_phase(
      wall_length, -10.0f + boonta_track_scroll_offset(wall_length, wall_length));
  assert(nearf(before_wall_phase, after_wall_phase));
 }

 /* Bad distance, segment length or coordinates must not propagate non-finite data. */
 assert(nearf(boonta_track_scroll_offset(-1.0f, road_length), 0.0f));
 assert(nearf(boonta_track_scroll_offset(NAN, road_length), 0.0f));
 assert(nearf(boonta_track_scroll_offset(1.0f, 0.0f), 0.0f));
 assert(boonta_track_section_index(INFINITY, road_length) == 0U);
 assert(boonta_track_section_index(1.0f, NAN) == 0U);
 assert(nearf(boonta_track_phase(NAN, 2.0f), 0.0f));
 assert(nearf(boonta_track_phase(2.0f, INFINITY), 0.0f));
}

static void slide_drift_tests(void) {
 const float regular_turn = boonta_lateral_velocity_after_steering_scaled(
     0.0f, 1.0f, 1.0f, 1.0f);
 const float slide_turn = boonta_lateral_velocity_after_steering_slide_scaled(
     0.0f, 1.0f, 1.0f, 1, 1.0f);
 const float regular_coast = boonta_lateral_velocity_after_steering_scaled(
     0.05f, 0.0f, 0.0f, 1.0f);
 const float slide_coast = boonta_lateral_velocity_after_steering_slide_scaled(
     0.05f, 0.0f, 0.0f, 1, 1.0f);

 /* Disabled slide preserves established handling; active slide turns harder. */
 assert(nearf(
     boonta_lateral_velocity_after_steering_slide_scaled(
         0.02f, -0.3f, 0.7f, 0, 1.0f),
     boonta_lateral_velocity_after_steering_scaled(
         0.02f, -0.3f, 0.7f, 1.0f)));
 assert(slide_turn > regular_turn);
 assert(slide_coast > regular_coast);
 assert(nearf(slide_coast, 0.04825f));

 /* Drift is still bounded and invalid state/timing remains finite. */
 assert(nearf(
     boonta_lateral_velocity_after_steering_slide_scaled(
         0.2f, 1.0f, 1.0f, 1, 1.0f),
     0.085f));
 assert(nearf(
     boonta_lateral_velocity_after_steering_slide_scaled(
         NAN, NAN, NAN, 1, 1.0f),
     0.0f));
 assert(nearf(
     boonta_lateral_velocity_after_steering_slide_scaled(
         0.05f, 1.0f, 0.5f, 1, NAN),
     0.05f));
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

static void lap_clock_tests(void) {
 assert(nearf(boonta_elapsed_after_frame(12.0f, 0.5f, 1), 12.5f));
 assert(nearf(boonta_elapsed_after_frame(12.0f, 0.5f, 0), 12.0f));
 assert(nearf(boonta_elapsed_after_frame(12.0f, 0.0f, 1), 12.0f));
 assert(nearf(boonta_elapsed_after_frame(12.0f, -0.1f, 1), 12.0f));
 assert(nearf(boonta_elapsed_after_frame(12.0f, NAN, 1), 12.0f));
 assert(nearf(boonta_elapsed_after_frame(NAN, 0.1f, 1), 0.1f));
 assert(nearf(boonta_elapsed_after_frame(12.0f, 2.0f, 1), 13.0f));

 assert(nearf(boonta_best_lap_after_finish(0.0f, 21.5f), 21.5f));
 assert(nearf(boonta_best_lap_after_finish(21.5f, 22.0f), 21.5f));
 assert(nearf(boonta_best_lap_after_finish(21.5f, 18.25f), 18.25f));
 assert(nearf(boonta_best_lap_after_finish(21.5f, 0.0f), 21.5f));
 assert(nearf(boonta_best_lap_after_finish(21.5f, NAN), 21.5f));
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
 /* Reject non-finite values before any float-to-integer conversion. */
 assert(boonta_lap_was_crossed(NAN,120.0f,120.0f)==0);
 assert(boonta_lap_was_crossed(0.0f,NAN,120.0f)==0);
 assert(boonta_lap_was_crossed(0.0f,120.0f,INFINITY)==0);
 assert(boonta_lap_was_crossed(INFINITY,INFINITY,120.0f)==0);
 /* A finite but enormous distance must not overflow an unsigned lap index. */
 assert(boonta_lap_was_crossed(0.0f,3.0e38f,120.0f)==1);
 /* Finite inputs can still overflow the floating-point division itself. */
 assert(boonta_lap_was_crossed(1.0e30f,2.0e30f,1.0e-10f)==1);
 assert(boonta_lap_was_crossed(2.0e30f,2.0e30f,1.0e-10f)==0);
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


static void multiple_rival_spacing_tests(void) {
 assert(BOONTA_RIVAL_COUNT == 3U);
 assert(nearf(boonta_rival_initial_z(0U), -18.0f));
 assert(nearf(boonta_rival_initial_z(1U), -34.0f));
 assert(nearf(boonta_rival_initial_z(2U), -50.0f));

 /* Collision respawns and overtakes preserve staggered spacing. */
 assert(nearf(boonta_rival_respawn_z(0U, 1), -20.0f));
 assert(nearf(boonta_rival_respawn_z(1U, 1), -32.0f));
 assert(nearf(boonta_rival_respawn_z(2U, 1), -44.0f));
 assert(nearf(boonta_rival_respawn_z(0U, 0), -22.0f));
 assert(nearf(boonta_rival_respawn_z(1U, 0), -34.0f));
 assert(nearf(boonta_rival_respawn_z(2U, 0), -46.0f));

 assert(boonta_rival_event(boonta_rival_initial_z(0U), 0.0f, 0.0f) == BOONTA_RIVAL_EVENT_NONE);
 assert(boonta_rival_event(boonta_rival_initial_z(1U), 0.0f, 0.0f) == BOONTA_RIVAL_EVENT_NONE);
 assert(boonta_rival_event(boonta_rival_initial_z(2U), 0.0f, 0.0f) == BOONTA_RIVAL_EVENT_NONE);
}

static void rival_contact_velocity_tests(void) {
 /* A collision impulse stays inside the same +/-0.085 steering-velocity bound. */
 assert(nearf(boonta_lateral_velocity_after_rival_contact(0.05f, 0.0f, 0.0f),
              0.015f));
 assert(nearf(boonta_lateral_velocity_after_rival_contact(0.08f, 0.5f, 0.0f),
              0.085f));
 assert(nearf(boonta_lateral_velocity_after_rival_contact(-0.08f, -0.5f, 0.0f),
              -0.085f));

 /* Invalid velocity is reset before the collision impulse is applied. */
 assert(nearf(boonta_lateral_velocity_after_rival_contact(NAN, 0.0f, 1.0f),
              -0.035f));
 assert(nearf(boonta_lateral_velocity_after_rival_contact(INFINITY, 0.0f, 1.0f),
              -0.035f));
 assert(nearf(boonta_lateral_velocity_after_rival_contact(-INFINITY, 0.0f, -1.0f),
              0.035f));

 /* Invalid lateral positions suppress direction guessing but preserve safe velocity. */
 assert(nearf(boonta_lateral_velocity_after_rival_contact(0.04f, NAN, 0.0f), 0.04f));
 assert(nearf(boonta_lateral_velocity_after_rival_contact(0.04f, 0.0f, INFINITY), 0.04f));
 assert(nearf(boonta_lateral_velocity_after_rival_contact(0.12f, 0.0f, NAN), 0.085f));
}

static void multiframe_rival_contact_tests(void) {
 float speed = 0.90f;
 float player_lateral = 0.0f;
 float lateral_velocity = 0.0f;
 const float rival_laterals[] = { 0.50f, -0.50f, 0.20f, -0.20f };
 unsigned int i;

 /*
  * Several contacts across a race should reduce speed without producing
  * non-finite state or allowing lateral momentum to escape its physics bound.
  * The neutral-steering frame between contacts models the retained drift.
  */
 for (i = 0U; i < sizeof(rival_laterals) / sizeof(rival_laterals[0]); ++i) {
  const float speed_before = speed;

  speed = boonta_speed_after_rival_contact(speed);
  lateral_velocity = boonta_lateral_velocity_after_rival_contact(
      lateral_velocity, player_lateral, rival_laterals[i]);
  player_lateral = boonta_lateral_position_after_frame(
      player_lateral, lateral_velocity, 1.0f);
  lateral_velocity = boonta_lateral_velocity_after_steering_scaled(
      lateral_velocity, 0.0f, speed, 1.0f);

  assert(isfinite(speed) && speed >= 0.0f && speed <= 1.0f);
  assert(isfinite(player_lateral));
  assert(isfinite(lateral_velocity));
  assert(fabsf(lateral_velocity) <= 0.085f);
  assert(speed < speed_before);
 }

 /* Four successive contacts must clamp the racer at rest, never below zero. */
 assert(nearf(speed, 0.0f));
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
 float race_seconds = 0.0f;
 float lap_seconds = 0.0f;
 float best_lap_seconds = 0.0f;
 float last_lap_seconds = 0.0f;
 unsigned int laps = 0U;
 unsigned int frames = 0U;
 int overheated = 0;
 int finished = 0;

 while (!finished && frames < 5000U) {
  const int boost_active = boonta_boost_should_activate_with_heat(1, 1, boost, heat, overheated);
  const float previous_distance = distance;
  const unsigned int previous_laps = laps;
  race_seconds = boonta_elapsed_after_frame(race_seconds, 1.0f / 60.0f, 1);
  lap_seconds = boonta_elapsed_after_frame(lap_seconds, 1.0f / 60.0f, 1);
  boost = boonta_boost_after_frame(boost, boost_active);
  heat = boonta_engine_heat_after_frame(heat, boost_active);
  overheated = boonta_boost_overheated_after_frame(overheated, heat);
  speed = boonta_speed_after_input(speed, 1, 0);
  distance = boonta_distance_after_frame(distance, speed, boost_active);
  laps = boonta_lap_count_after_frame(laps, previous_distance, distance, 120.0f);
  if (laps > previous_laps) {
   last_lap_seconds = lap_seconds;
   best_lap_seconds = boonta_best_lap_after_finish(best_lap_seconds, last_lap_seconds);
   lap_seconds = 0.0f;
  }
  finished = boonta_race_is_finished(laps, 3U);
  if (finished) {
   speed = 0.0f;
   lap_seconds = last_lap_seconds;
  }
  ++frames;
 }

 assert(frames > 0U && frames < 5000U);
 assert(finished == 1);
 assert(laps == 3U);
 assert(distance >= 360.0f);
 assert(race_seconds > 0.0f);
 assert(best_lap_seconds > 0.0f);
 assert(last_lap_seconds > 0.0f);
 assert(nearf(lap_seconds, last_lap_seconds));
 assert(nearf(speed, 0.0f));
}

static void non_finite_physics_state_tests(void) {
 /* Steering inputs and residual state must recover without propagating NaN. */
 assert(nearf(boonta_lateral_velocity_after_steering_scaled(NAN, 1.0f, 0.5f, 1.0f),
              boonta_lateral_velocity_after_steering_scaled(0.0f, 1.0f, 0.5f, 1.0f)));
 assert(nearf(boonta_lateral_velocity_after_steering_scaled(0.0f, NAN, 0.5f, 1.0f),
              boonta_lateral_velocity_after_steering_scaled(0.0f, 0.0f, 0.5f, 1.0f)));
 assert(nearf(boonta_lateral_velocity_after_steering_scaled(0.0f, 1.0f, INFINITY, 1.0f),
              boonta_lateral_velocity_after_steering_scaled(0.0f, 1.0f, 0.0f, 1.0f)));
 assert(nearf(boonta_lateral_position_after_frame(NAN, 0.04f, 1.0f), 0.04f));
 assert(nearf(boonta_lateral_position_after_frame(1.0f, NAN, 1.0f), 1.0f));
 assert(nearf(boonta_lateral_position_after_frame(INFINITY, 0.04f, 1.0f), 0.04f));

 /* Distance and rival movement recover from corrupt inputs deterministically. */
 assert(nearf(boonta_distance_after_frame_scaled(NAN, 0.5f, 0, 1.0f), 0.07f));
 assert(nearf(boonta_distance_after_frame_scaled(10.0f, NAN, 0, 1.0f), 10.0f));
 assert(nearf(boonta_distance_after_frame_scaled(INFINITY, 0.5f, 0, 1.0f), 0.07f));
 assert(nearf(boonta_rival_z_after_frame(NAN, 0.5f, 1.0f),
              boonta_rival_z_after_frame(-18.0f, 0.5f, 1.0f)));
 assert(nearf(boonta_rival_z_after_frame(-18.0f, NAN, 1.0f),
              boonta_rival_z_after_frame(-18.0f, 0.0f, 1.0f)));
 assert(boonta_rival_event(NAN, 0.0f, 0.0f) == BOONTA_RIVAL_EVENT_NONE);
 assert(boonta_rival_event(0.0f, NAN, 0.0f) == BOONTA_RIVAL_EVENT_NONE);
 assert(boonta_rival_event(0.0f, 0.0f, INFINITY) == BOONTA_RIVAL_EVENT_NONE);
 assert(nearf(boonta_speed_after_rival_contact(NAN), 0.0f));
 assert(nearf(boonta_speed_after_rival_contact(INFINITY), 0.0f));
 assert(nearf(boonta_rival_contact_nudge(NAN, 0.0f), 0.0f));

 /* Off-road and rail helpers must not feed invalid values back into the loop. */
 assert(nearf(boonta_speed_after_offroad_scaled(NAN, 0.0f, 1.0f), 0.0f));
 assert(nearf(boonta_speed_after_offroad_scaled(0.5f, NAN, 1.0f), 0.5f));
 assert(nearf(boonta_abs_float(NAN), 0.0f));
 assert(!boonta_is_past_rail(NAN));
 assert(nearf(boonta_lateral_after_rail_contact(NAN), 0.0f));
 assert(nearf(boonta_lateral_after_rail_contact(INFINITY), 0.0f));
 assert(nearf(boonta_lateral_velocity_after_rail_contact(NAN), 0.0f));
 assert(nearf(boonta_lateral_velocity_after_rail_contact(INFINITY), 0.0f));

 /* A corrupted boost/heat value must not briefly enable boost for one frame. */
 assert(!boonta_boost_should_activate(1, 1, INFINITY));
 assert(!boonta_boost_should_activate_with_heat(1, 1, 0.5f, NAN, 0));
}

static void race_state_reset_tests(void) {
 BoontaRaceState state;
 unsigned int i;

 state.distance = 42.0f;
 state.lap_count = 2U;
 state.race_seconds = 88.0f;
 state.lap_seconds = 22.0f;
 state.last_lap_seconds = 21.0f;
 state.best_lap_seconds = 19.0f;
 state.speed = 0.9f;
 state.pitch_down = 0.8f;
 state.player_lateral = 2.2f;
 state.lateral_velocity = -0.04f;
 state.boost = 0.1f;
 state.engine_heat = 0.99f;
 state.boost_overheated = 1;
 state.boost_active = 1;
 state.slide_active = 1;
 state.overtake_count = 7U;
 state.paused = 1;
 state.race_finished = 1;
 for (i = 0U; i < BOONTA_RIVAL_COUNT; ++i) {
  state.rival_z[i] = 8.0f + (float)i;
  state.rival_lateral[i] = -1.0f - (float)i;
 }

 boonta_race_state_reset(&state);

 assert(nearf(state.distance, 0.0f));
 assert(state.lap_count == 0U);
 assert(nearf(state.race_seconds, 0.0f));
 assert(nearf(state.lap_seconds, 0.0f));
 assert(nearf(state.last_lap_seconds, 0.0f));
 assert(nearf(state.best_lap_seconds, 0.0f));
 assert(nearf(state.speed, 0.0f));
 assert(nearf(state.pitch_down, 0.0f));
 assert(nearf(state.player_lateral, 0.0f));
 assert(nearf(state.lateral_velocity, 0.0f));
 assert(nearf(state.boost, 1.0f));
 assert(nearf(state.engine_heat, 0.0f));
 assert(state.boost_overheated == 0);
 assert(state.boost_active == 0);
 assert(state.slide_active == 0);
 assert(state.overtake_count == 0U);
 assert(state.paused == 0);
 assert(state.race_finished == 0);
 for (i = 0U; i < BOONTA_RIVAL_COUNT; ++i) {
  assert(nearf(state.rival_z[i], boonta_rival_initial_z(i)));
  assert(nearf(state.rival_lateral[i], 0.0f));
 }

 /* Defensive no-op for a missing state pointer. */
 boonta_race_state_reset(0);
}

static void invalid_scaled_frame_tests(void) {
 const float invalid_scales[] = { NAN, INFINITY, -INFINITY, -1.0f };
 unsigned int i;

 for (i = 0U; i < sizeof(invalid_scales) / sizeof(invalid_scales[0]); ++i) {
  const float scale = invalid_scales[i];
  assert(nearf(boonta_sanitize_frame_scale(scale), 0.0f));
  assert(nearf(boonta_speed_after_input_scaled(0.5f, 1, 0, scale), 0.5f));
  assert(nearf(boonta_boost_after_frame_scaled(0.5f, 1, scale), 0.5f));
  assert(nearf(boonta_engine_heat_after_frame_scaled(0.5f, 1, scale), 0.5f));
  assert(nearf(boonta_lateral_velocity_after_steering_scaled(0.04f, 1.0f, 0.5f, scale), 0.04f));
  assert(nearf(boonta_lateral_position_after_frame(1.0f, 0.04f, scale), 1.0f));
  assert(nearf(boonta_distance_after_frame_scaled(10.0f, 0.5f, 0, scale), 10.0f));
  assert(nearf(boonta_rival_z_after_frame(-18.0f, 0.5f, scale), -18.0f));
  assert(nearf(boonta_speed_after_offroad_scaled(0.5f, 4.0f, scale), 0.5f));
 }
}

int main(void) {
 finite_clamp_tests();
 frame_scale_tests();
 non_finite_physics_state_tests();
 invalid_scaled_frame_tests();
 cadence_consistency_tests();
 speed_tests();
 boost_tests();
 boost_overheat_tests();
 lap_clock_tests();
 steering_input_tests();
 pitch_tradeoff_tests();
 slide_drift_tests();
 steering_inertia_tests();
 lap_tests();
 three_lap_finish_tests();
 distance_progression_tests();
 track_scroll_tests();
 simulated_three_lap_run_tests();
 multiple_rival_spacing_tests();
 rival_contact_velocity_tests();
 multiframe_rival_contact_tests();
 rival_event_tests();
 offroad_and_rail_tests();
 puts("gameplay-state tests passed");
 return 0;
}
