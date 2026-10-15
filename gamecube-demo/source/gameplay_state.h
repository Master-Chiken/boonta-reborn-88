#ifndef BOONTA_REBORN_GAMEPLAY_STATE_H
#define BOONTA_REBORN_GAMEPLAY_STATE_H

#include <math.h>

#define BOONTA_RIVAL_COUNT 3U
/* Deterministic gameplay transitions shared by the native loop and host tests. */
static inline float boonta_speed_after_input(float speed, int accelerating, int braking)
{
    if (accelerating) speed += 0.012f; else speed -= 0.003f;
    if (braking) speed -= 0.022f;
    if (speed < 0.0f) return 0.0f;
    if (speed > 1.0f) return 1.0f;
    return speed;
}
static inline int boonta_boost_should_activate(int x_held, int a_held, float boost)
{
    return x_held && a_held && boost > 0.01f;
}
static inline float boonta_boost_after_frame(float boost, int active)
{
    if (active) boost -= 0.0055f; else boost += 0.0015f;
    if (boost < 0.0f) return 0.0f;
    if (boost > 1.0f) return 1.0f;
    return boost;
}
/* Boost heat rises while engaged and cools while the boost is released. */
static inline float boonta_engine_heat_after_frame(float heat, int active)
{
    if (active) heat += 0.0065f; else heat -= 0.0045f;
    if (heat < 0.0f) return 0.0f;
    if (heat > 1.0f) return 1.0f;
    return heat;
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
    return !overheated && heat < 0.98f &&
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
    float steering = stick_x / 128.0f;
    if (left_held) steering -= 0.7f;
    if (right_held) steering += 0.7f;
    if (steering < -1.0f) return -1.0f;
    if (steering > 1.0f) return 1.0f;
    return steering;
}

/* Match the native loop's inertia, damping and lateral-speed bounds. */
static inline float boonta_lateral_velocity_after_steering(float lateral_velocity,
                                                            float steering,
                                                            float speed)
{
    lateral_velocity += steering * (0.0018f + speed * 0.0030f);
    lateral_velocity *= 0.92f;
    if (lateral_velocity < -0.085f) return -0.085f;
    if (lateral_velocity > 0.085f) return 0.085f;
    return lateral_velocity;
}

/* Shared distance integration used by both the native loop and host simulation. */
static inline float boonta_distance_after_frame(float distance, float speed, int boost_active)
{
    return distance + speed * (boost_active ? 0.22f : 0.14f);
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

static inline int boonta_rival_event(float rival_z,
                                     float player_lateral,
                                     float rival_lateral)
{
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
    speed -= 0.28f;
    if (speed < 0.0f) return 0.0f;
    if (speed > 1.0f) return 1.0f;
    return speed;
}

static inline float boonta_rival_contact_nudge(float player_lateral,
                                                float rival_lateral)
{
    return player_lateral <= rival_lateral ? -0.035f : 0.035f;
}


/* Keep the demo's existing off-road and rail-edge response independently testable. */
static inline float boonta_abs_float(float value)
{
    return value < 0.0f ? -value : value;
}

static inline float boonta_speed_after_offroad(float speed, float player_lateral)
{
    const float distance_from_center = boonta_abs_float(player_lateral);
    if (distance_from_center > 3.15f) {
        const float excess = distance_from_center - 3.15f;
        speed -= 0.008f + excess * 0.012f;
    }
    if (speed < 0.0f) return 0.0f;
    if (speed > 1.0f) return 1.0f;
    return speed;
}

static inline int boonta_is_past_rail(float player_lateral)
{
    return boonta_abs_float(player_lateral) > 3.85f;
}

static inline float boonta_lateral_after_rail_contact(float player_lateral)
{
    if (player_lateral > 3.85f) return 3.85f;
    if (player_lateral < -3.85f) return -3.85f;
    return player_lateral;
}

static inline float boonta_lateral_velocity_after_rail_contact(float lateral_velocity)
{
    return lateral_velocity * -0.35f;
}

#endif
