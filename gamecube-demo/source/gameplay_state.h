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
static inline int boonta_lap_was_crossed(float previous_distance, float current_distance, float lap_distance)
{
    if (lap_distance <= 0.0f || previous_distance < 0.0f || current_distance < previous_distance) return 0;
    return (unsigned int)(current_distance / lap_distance) > (unsigned int)(previous_distance / lap_distance);
}
#endif
