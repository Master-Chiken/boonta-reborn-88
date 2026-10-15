#ifndef BOONTA_REBORN_GAMEPLAY_STATE_H
#define BOONTA_REBORN_GAMEPLAY_STATE_H
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

static inline int boonta_lap_was_crossed(float previous_distance, float current_distance, float lap_distance)
{
    if (lap_distance <= 0.0f || previous_distance < 0.0f || current_distance < previous_distance) return 0;
    return (unsigned int)(current_distance / lap_distance) > (unsigned int)(previous_distance / lap_distance);
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
