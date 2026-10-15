#ifndef BOONTA_REBORN_GAMEPLAY_STATE_H
#define BOONTA_REBORN_GAMEPLAY_STATE_H

#include <math.h>

#define BOONTA_RIVAL_COUNT 3U
/* Deterministic gameplay transitions shared by the native loop and host tests. */

/* Clamp finite simulation state; recover NaN/infinity without propagating it. */
static inline float boonta_clamp_finite_float(float value, float low, float high)
{
    if (!isfinite(value)) return 0.0f;
    if (value < low) return low;
    if (value > high) return high;
    return value;
}

/* Preserve 60 Hz tuning, compensate PAL/NTSC cadence and cap long stalls. */
static inline float boonta_frame_scale_from_delta(float delta_seconds)
{
    if (!(delta_seconds > 0.0f)) delta_seconds = 1.0f / 60.0f;
    if (delta_seconds > 0.05f) delta_seconds = 0.05f;
    return delta_seconds * 60.0f;
}

/* Invalid frame scales must never propagate NaN/infinity into simulation state. */
static inline float boonta_sanitize_frame_scale(float frame_scale)
{
    if (!isfinite(frame_scale) || frame_scale < 0.0f) return 0.0f;
    return frame_scale;
}

static inline float boonta_speed_after_input_scaled(float speed, int accelerating,
                                                      int braking, float frame_scale)
{
    /* Recover deterministically from corrupted simulation state or timing. */
    if (!isfinite(speed)) speed = 0.0f;
    frame_scale = boonta_sanitize_frame_scale(frame_scale);
    if (accelerating) speed += 0.012f * frame_scale;
    else speed -= 0.003f * frame_scale;
    if (braking) speed -= 0.022f * frame_scale;
    if (speed < 0.0f) return 0.0f;
    if (speed > 1.0f) return 1.0f;
    return speed;
}

static inline float boonta_speed_after_input(float speed, int accelerating, int braking)
{
    return boonta_speed_after_input_scaled(speed, accelerating, braking, 1.0f);
}

/*
 * Racer-style pitch: a forward/up stick push means nose-down. Pitching down
 * rewards risk with more forward travel but reduces steering authority; pitching
 * up trades speed for tighter control. Ignore small stick noise around center.
 */
static inline float boonta_pitch_input(float stick_y)
{
    if (!isfinite(stick_y)) return 0.0f;
    if (stick_y >= -16.0f && stick_y <= 16.0f) return 0.0f;
    if (stick_y > 0.0f) return boonta_clamp_finite_float((stick_y - 16.0f) / 111.0f, 0.0f, 1.0f);
    return boonta_clamp_finite_float((stick_y + 16.0f) / 112.0f, -1.0f, 0.0f);
}

/* While pitching up (negative), steering grows up to +35%; nose-down loses 40%. */
static inline float boonta_steering_after_pitch(float steering, float pitch_down)
{
    float steering_scale;
    if (!isfinite(steering)) steering = 0.0f;
    if (!isfinite(pitch_down)) pitch_down = 0.0f;
    pitch_down = boonta_clamp_finite_float(pitch_down, -1.0f, 1.0f);
    steering = boonta_clamp_finite_float(steering, -1.0f, 1.0f);
    steering_scale = 1.0f - (pitch_down >= 0.0f ? 0.40f : 0.35f) * pitch_down;
    return boonta_clamp_finite_float(steering * steering_scale, -1.0f, 1.0f);
}
static inline int boonta_boost_should_activate(int x_held, int a_held, float boost)
{
    return isfinite(boost) && x_held && a_held && boost > 0.01f;
}
static inline float boonta_boost_after_frame_scaled(float boost, int active, float frame_scale)
{
    /* Recover corrupted resource state before arithmetic. */
    if (!isfinite(boost)) boost = 0.0f;
    frame_scale = boonta_sanitize_frame_scale(frame_scale);
    if (active) boost -= 0.0055f * frame_scale;
    else boost += 0.0015f * frame_scale;
    if (boost < 0.0f) return 0.0f;
    if (boost > 1.0f) return 1.0f;
    return boost;
}

static inline float boonta_boost_after_frame(float boost, int active)
{
    return boonta_boost_after_frame_scaled(boost, active, 1.0f);
}
/* Boost heat rises while engaged and cools while the boost is released. */
static inline float boonta_engine_heat_after_frame_scaled(float heat, int active,
                                                           float frame_scale)
{
    /* Heat follows the same finite-state contract as boost and speed. */
    if (!isfinite(heat)) heat = 0.0f;
    frame_scale = boonta_sanitize_frame_scale(frame_scale);
    if (active) heat += 0.0065f * frame_scale;
    else heat -= 0.0045f * frame_scale;
    if (heat < 0.0f) return 0.0f;
    if (heat > 1.0f) return 1.0f;
    return heat;
}

static inline float boonta_engine_heat_after_frame(float heat, int active)
{
    return boonta_engine_heat_after_frame_scaled(heat, active, 1.0f);
}

/* Latch an overheat until the engine cools to 60%; this avoids rapid toggling. */
static inline int boonta_boost_overheated_after_frame(int overheated, float heat)
{
    if (overheated) return heat > 0.60f;
    return heat >= 0.98f;
}

static inline int boonta_boost_should_activate_with_heat(int x_held, int a_held,
                                                           float boost, float heat,
                                                           int overheated)
{
    return isfinite(heat) && !overheated && heat < 0.98f &&
           boonta_boost_should_activate(x_held, a_held, boost);
}
/* Wall-clock elapsed time updates only while race simulation is active.
 * Clamp one stalled frame to one second to avoid absurd timer jumps. */
static inline float boonta_elapsed_after_frame(float elapsed, float delta_seconds,
                                               int active)
{
    if (!isfinite(elapsed) || elapsed < 0.0f) elapsed = 0.0f;
    if (!active || !isfinite(delta_seconds) || delta_seconds <= 0.0f) return elapsed;
    if (delta_seconds > 1.0f) delta_seconds = 1.0f;
    return elapsed + delta_seconds;
}

/* Keep the best positive lap; invalid or incomplete laps never replace it. */
static inline float boonta_best_lap_after_finish(float best_seconds,
                                                 float completed_lap_seconds)
{
    if (!isfinite(completed_lap_seconds) || completed_lap_seconds <= 0.0f) {
        return isfinite(best_seconds) && best_seconds > 0.0f ? best_seconds : 0.0f;
    }
    if (!isfinite(best_seconds) || best_seconds <= 0.0f ||
        completed_lap_seconds < best_seconds) {
        return completed_lap_seconds;
    }
    return best_seconds;
}

/* Normalize the GameCube analog stick and D-pad into bounded steering input. */
static inline float boonta_steering_input(float stick_x,
                                          int left_held,
                                          int right_held)
{
    /* Corrupt controller data must not poison lateral physics with NaN. */
    if (!isfinite(stick_x)) stick_x = 0.0f;
    float steering = stick_x / 128.0f;
    if (left_held) steering -= 0.7f;
    if (right_held) steering += 0.7f;
    if (steering < -1.0f) return -1.0f;
    if (steering > 1.0f) return 1.0f;
    return steering;
}

/* Match steering inertia and damping to elapsed time, with legacy 60 Hz wrappers. */
static inline float boonta_lateral_velocity_after_steering_scaled(float lateral_velocity,
                                                                    float steering,
                                                                    float speed,
                                                                    float frame_scale)
{
    if (!isfinite(lateral_velocity)) lateral_velocity = 0.0f;
    if (!isfinite(steering)) steering = 0.0f;
    speed = boonta_clamp_finite_float(speed, 0.0f, 1.0f);
    frame_scale = boonta_sanitize_frame_scale(frame_scale);
    lateral_velocity += steering * (0.0018f + speed * 0.0030f) * frame_scale;
    lateral_velocity *= powf(0.92f, frame_scale);
    if (!isfinite(lateral_velocity)) return 0.0f;
    if (lateral_velocity < -0.085f) return -0.085f;
    if (lateral_velocity > 0.085f) return 0.085f;
    return lateral_velocity;
}

static inline float boonta_lateral_velocity_after_steering(float lateral_velocity,
                                                            float steering,
                                                            float speed)
{
    return boonta_lateral_velocity_after_steering_scaled(
        lateral_velocity, steering, speed, 1.0f);
}

/*
 * Holding slide increases turn impulse while reducing lateral grip. That makes
 * a corner easier to initiate but lets sideways drift persist after release.
 */
static inline float boonta_lateral_velocity_after_steering_slide_scaled(
    float lateral_velocity, float steering, float speed, int slide_active,
    float frame_scale)
{
    if (!slide_active) {
        return boonta_lateral_velocity_after_steering_scaled(
            lateral_velocity, steering, speed, frame_scale);
    }
    if (!isfinite(lateral_velocity)) lateral_velocity = 0.0f;
    if (!isfinite(steering)) steering = 0.0f;
    speed = boonta_clamp_finite_float(speed, 0.0f, 1.0f);
    frame_scale = boonta_sanitize_frame_scale(frame_scale);
    lateral_velocity += steering * (0.0018f + speed * 0.0030f) *
                        1.35f * frame_scale;
    lateral_velocity *= powf(0.965f, frame_scale);
    if (!isfinite(lateral_velocity)) return 0.0f;
    return boonta_clamp_finite_float(lateral_velocity, -0.085f, 0.085f);
}

static inline float boonta_lateral_velocity_after_steering_slide(
    float lateral_velocity, float steering, float speed, int slide_active)
{
    return boonta_lateral_velocity_after_steering_slide_scaled(
        lateral_velocity, steering, speed, slide_active, 1.0f);
}

static inline float boonta_lateral_position_after_frame(float lateral_position,
                                                         float lateral_velocity,
                                                         float frame_scale)
{
    if (!isfinite(lateral_position)) lateral_position = 0.0f;
    if (!isfinite(lateral_velocity)) lateral_velocity = 0.0f;
    frame_scale = boonta_sanitize_frame_scale(frame_scale);
    {
        const float next_position = lateral_position + lateral_velocity * frame_scale;
        return isfinite(next_position) ? next_position : lateral_position;
    }
}

/* Shared distance integration used by both the native loop and host simulation. */
static inline float boonta_distance_after_frame_scaled(float distance, float speed,
                                                        int boost_active, float frame_scale)
{
    if (!isfinite(distance) || distance < 0.0f) distance = 0.0f;
    speed = boonta_clamp_finite_float(speed, 0.0f, 1.0f);
    frame_scale = boonta_sanitize_frame_scale(frame_scale);
    {
        const float next_distance = distance + speed * (boost_active ? 0.22f : 0.14f) * frame_scale;
        return isfinite(next_distance) && next_distance >= 0.0f ? next_distance : 0.0f;
    }
}

static inline float boonta_distance_after_frame(float distance, float speed, int boost_active)
{
    return boonta_distance_after_frame_scaled(distance, speed, boost_active, 1.0f);
}

/* Apply the pitch trade-off to forward progress without corrupting the HUD's 0..1 speed state. */
static inline float boonta_distance_after_pitch_scaled(float distance, float speed,
                                                        int boost_active, float pitch_down,
                                                        float frame_scale)
{
    float motion_scale;
    float next_distance;
    if (!isfinite(distance) || distance < 0.0f) distance = 0.0f;
    speed = boonta_clamp_finite_float(speed, 0.0f, 1.0f);
    pitch_down = boonta_clamp_finite_float(pitch_down, -1.0f, 1.0f);
    frame_scale = boonta_sanitize_frame_scale(frame_scale);
    motion_scale = 1.0f + pitch_down * 0.12f;
    next_distance = distance + speed * (boost_active ? 0.22f : 0.14f) *
                    motion_scale * frame_scale;
    return isfinite(next_distance) && next_distance >= distance ? next_distance : distance;
}

static inline int boonta_lap_was_crossed(float previous_distance, float current_distance, float lap_distance)
{
    /* Reject NaN/infinity before float-to-unsigned conversion (undefined behavior
     * for non-finite or out-of-range values). A corrupt frame must not invent laps. */
    if (!isfinite(previous_distance) || !isfinite(current_distance) ||
        !isfinite(lap_distance) || lap_distance <= 0.0f ||
        previous_distance < 0.0f || current_distance < previous_distance) {
        return 0;
    }
    {
        const float previous_lap_index = floorf(previous_distance / lap_distance);
        const float current_lap_index = floorf(current_distance / lap_distance);

        /* Division can overflow to +infinity even when every input is finite.
         * If distance advanced and the current index overflowed, a crossing
         * occurred; comparing +infinity with +infinity alone would miss it. */
        return current_lap_index > previous_lap_index ||
               (isinf(current_lap_index) && current_distance > previous_distance);
    }
}

static inline unsigned int boonta_lap_count_after_frame(unsigned int lap_count,
                                                         float previous_distance,
                                                         float current_distance,
                                                         float lap_distance)
{
    if (boonta_lap_was_crossed(previous_distance, current_distance, lap_distance) &&
        lap_count < 0xffffffffU) {
        return lap_count + 1U;
    }
    return lap_count;
}

static inline int boonta_race_is_finished(unsigned int lap_count, unsigned int lap_limit)
{
    return lap_limit > 0U && lap_count >= lap_limit;
}


enum {
    BOONTA_RIVAL_EVENT_NONE = 0,
    BOONTA_RIVAL_EVENT_COLLISION = 1,
    BOONTA_RIVAL_EVENT_OVERTAKE = 2
};

/* Three procedural rivals keep a readable stagger in the scrolling-course demo. */
static inline float boonta_rival_initial_z(unsigned int rival_index)
{
    return -18.0f - (float)rival_index * 16.0f;
}

static inline float boonta_rival_respawn_z(unsigned int rival_index, int collision)
{
    const float respawn_base = collision ? -20.0f : -22.0f;
    return respawn_base - (float)rival_index * 12.0f;
}

static inline float boonta_rival_z_after_frame(float rival_z, float speed, float frame_scale)
{
    if (!isfinite(rival_z)) rival_z = -18.0f;
    speed = boonta_clamp_finite_float(speed, 0.0f, 1.0f);
    frame_scale = boonta_sanitize_frame_scale(frame_scale);
    {
        const float next_z = rival_z + (0.035f + speed * 0.045f) * frame_scale;
        return isfinite(next_z) ? next_z : -18.0f;
    }
}

static inline int boonta_rival_event(float rival_z,
                                     float player_lateral,
                                     float rival_lateral)
{
    if (!isfinite(rival_z) || !isfinite(player_lateral) || !isfinite(rival_lateral)) {
        return BOONTA_RIVAL_EVENT_NONE;
    }
    if (rival_z > -1.0f && rival_z < 1.8f) {
        float lateral_gap = player_lateral - rival_lateral;
        if (lateral_gap < 0.0f) lateral_gap = -lateral_gap;
        return lateral_gap < 0.92f
            ? BOONTA_RIVAL_EVENT_COLLISION
            : BOONTA_RIVAL_EVENT_OVERTAKE;
    }
    if (rival_z >= 1.8f) return BOONTA_RIVAL_EVENT_OVERTAKE;
    return BOONTA_RIVAL_EVENT_NONE;
}

static inline float boonta_speed_after_rival_contact(float speed)
{
    speed = boonta_clamp_finite_float(speed, 0.0f, 1.0f);
    speed -= 0.28f;
    if (speed < 0.0f) return 0.0f;
    if (speed > 1.0f) return 1.0f;
    return speed;
}

static inline float boonta_rival_contact_nudge(float player_lateral,
                                                float rival_lateral)
{
    if (!isfinite(player_lateral) || !isfinite(rival_lateral)) return 0.0f;
    return player_lateral <= rival_lateral ? -0.035f : 0.035f;
}

/* Shared by runtime and host tests: reject invalid state and bound collision drift. */
static inline float boonta_lateral_velocity_after_rival_contact(float lateral_velocity,
                                                                 float player_lateral,
                                                                 float rival_lateral)
{
    if (!isfinite(lateral_velocity)) lateral_velocity = 0.0f;
    if (!isfinite(player_lateral) || !isfinite(rival_lateral)) {
        return boonta_clamp_finite_float(lateral_velocity, -0.085f, 0.085f);
    }
    return boonta_clamp_finite_float(
        lateral_velocity + boonta_rival_contact_nudge(player_lateral, rival_lateral),
        -0.085f, 0.085f);
}


/* Keep the demo's existing off-road and rail-edge response independently testable. */
static inline float boonta_abs_float(float value)
{
    if (!isfinite(value)) return 0.0f;
    return value < 0.0f ? -value : value;
}

static inline float boonta_speed_after_offroad_scaled(float speed, float player_lateral,
                                                       float frame_scale)
{
    speed = boonta_clamp_finite_float(speed, 0.0f, 1.0f);
    if (!isfinite(player_lateral)) player_lateral = 0.0f;
    frame_scale = boonta_sanitize_frame_scale(frame_scale);
    const float distance_from_center = boonta_abs_float(player_lateral);
    if (distance_from_center > 3.15f) {
        const float excess = distance_from_center - 3.15f;
        speed -= (0.008f + excess * 0.012f) * frame_scale;
    }
    if (speed < 0.0f) return 0.0f;
    if (speed > 1.0f) return 1.0f;
    return speed;
}

static inline float boonta_speed_after_offroad(float speed, float player_lateral)
{
    return boonta_speed_after_offroad_scaled(speed, player_lateral, 1.0f);
}

static inline int boonta_is_past_rail(float player_lateral)
{
    return isfinite(player_lateral) && boonta_abs_float(player_lateral) > 3.85f;
}

static inline float boonta_lateral_after_rail_contact(float player_lateral)
{
    if (!isfinite(player_lateral)) return 0.0f;
    if (player_lateral > 3.85f) return 3.85f;
    if (player_lateral < -3.85f) return -3.85f;
    return player_lateral;
}

static inline float boonta_lateral_velocity_after_rail_contact(float lateral_velocity)
{
    if (!isfinite(lateral_velocity)) return 0.0f;
    return boonta_clamp_finite_float(lateral_velocity * -0.35f, -0.085f, 0.085f);
}

#endif
