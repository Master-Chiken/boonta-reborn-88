#include "racer_physics.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#define CHECK(expr) do { if (!(expr)) { \
    fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #expr); return 1; \
} } while (0)

static void make_circle_radius(RacerTrackPoint *points, unsigned int count, float radius)
{
    unsigned int i;
    const float pi = 3.14159265358979323846f;
    for (i = 0; i < count; ++i) {
        float a = (2.0f * pi * (float)i) / (float)count;
        points[i].x = radius * cosf(a);
        points[i].y = 0.0f;
        points[i].z = radius * sinf(a);
    }
}

static void make_circle(RacerTrackPoint *points, unsigned int count)
{
    make_circle_radius(points, count, 30.0f);
}

int main(void)
{
    RacerTrackPoint track[80];
    RacerTrackPoint boost_track[80];
    RacerState state;
    RacerState boost_state;
    RacerState damaged_state;
    RacerState clean_state;
    RacerState edge_state;
    RacerState center_state;
    RacerState low_grip_state;
    RacerState high_grip_state;
    RacerState narrow_road_state;
    RacerState wide_road_state;
    RacerInput input = {0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
    RacerTrackProjection projection;
    float initial_heading;
    unsigned int i;

    make_circle(track, 80U);
    racer_init(&state, track, 80U);
    CHECK(state.lap == 1U);
    CHECK(state.speed == 0.0f);
    CHECK(state.track_distance < 0.01f);

    /* Pod height follows the cross-slope on a banked curve: on this route's
       positive turn, the +normal/outer side should sit higher than the inner. */
    {
        RacerState outer_pod, inner_pod;
        RacerInput coast = {0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
        racer_init(&outer_pod, track, 80U);
        racer_init(&inner_pod, track, 80U);
        outer_pod.x = 33.0f;
        inner_pod.x = 27.0f;
        outer_pod.z = inner_pod.z = 0.0f;
        racer_update_vehicle_surface_width(&outer_pod, track, 80U, &coast,
                                           NULL, 1.0f, 0.0f, 12.0f, 1.0f/60.0f);
        racer_update_vehicle_surface_width(&inner_pod, track, 80U, &coast,
                                           NULL, 1.0f, 0.0f, 12.0f, 1.0f/60.0f);
        CHECK(outer_pod.y > inner_pod.y + 0.10f);
    }

    input.throttle = 1.0f;
    for (i = 0; i < 100U; ++i) racer_update(&state, track, 80U, &input, 1.0f/60.0f);
    CHECK(state.speed > 10.0f);
    CHECK(state.race_time > 1.5f);

    input.throttle = 0.0f;
    input.brake = 1.0f;
    {
        float before_brake = state.speed;
        for (i = 0; i < 30U; ++i) racer_update(&state, track, 80U, &input, 1.0f/60.0f);
        CHECK(state.speed < before_brake);
    }

    input.brake = 0.0f;
    input.throttle = 1.0f;
    for (i = 0; i < 20U; ++i) racer_update(&state, track, 80U, &input, 1.0f/60.0f);
    initial_heading = state.heading;
    input.steering = 1.0f;
    for (i = 0; i < 30U; ++i) racer_update(&state, track, 80U, &input, 1.0f/60.0f);
    CHECK(fabsf(state.heading - initial_heading) > 0.05f);

    input.steering = 0.0f;
    input.boost = 1.0f;
    for (i = 0; i < 35U; ++i) racer_update(&state, track, 80U, &input, 1.0f/60.0f);
    CHECK(state.boost_heat > 10.0f);
    CHECK(state.boost_energy < 100.0f);
    CHECK(state.boost_active || state.overheated);
    for (i = 0; i < 240U; ++i) racer_update(&state, track, 80U, &input, 1.0f/60.0f);
    CHECK(state.overheated == 1);
    CHECK(state.boost_heat > 42.0f);
    input.boost = 0.0f;
    for (i = 0; i < 240U; ++i) racer_update(&state, track, 80U, &input, 1.0f/60.0f);
    CHECK(state.boost_heat < 100.0f);
    CHECK(state.overheated == 0);

    /* Boost must exceed the normal top-speed ceiling, then shed that extra
       speed progressively after release instead of cutting speed in one frame. */
    {
        RacerVehicleSpec boost_vehicle = {"BOOST TEST", 52.0f, 20.0f, 1.0f, 1.0f,
                                          25.0f, 30.0f, 20.0f, 13.0f, 1.0f,
                                          190, 52, 35};
        RacerInput boost_input = {0.0f, 1.0f, 0.0f, 1.0f, 0.0f};
        float release_speed;
        make_circle_radius(boost_track, 80U, 200.0f);
        racer_init(&boost_state, boost_track, 80U);
        boost_state.speed = boost_vehicle.top_speed;
        for (i = 0U; i < 24U; ++i) {
            racer_update_vehicle_surface_width(&boost_state, boost_track, 80U,
                &boost_input, &boost_vehicle, 1.0f, 0.0f, 20.0f, 1.0f/60.0f);
        }
        CHECK(boost_state.boost_active == 1);
        CHECK(boost_state.speed > boost_vehicle.top_speed + 1.0f);
        CHECK(boost_state.speed <= boost_vehicle.top_speed * 1.16f + 0.05f);
        release_speed = boost_state.speed;
        boost_input.boost = 0.0f;
        for (i = 0U; i < 40U; ++i) {
            racer_update_vehicle_surface_width(&boost_state, boost_track, 80U,
                &boost_input, &boost_vehicle, 1.0f, 0.0f, 20.0f, 1.0f/60.0f);
        }
        CHECK(boost_state.speed < release_speed);
        CHECK(boost_state.speed <= boost_vehicle.top_speed + 0.05f);
    }

    /* A lap counts on a physical forward crossing of the start/finish plane,
       not merely because the projected progress wraps near a self-crossing. */
    racer_init(&state, track, 80U);
    {
        float tx = track[1].x - track[0].x;
        float tz = track[1].z - track[0].z;
        float len = sqrtf(tx*tx + tz*tz);
        tx /= len; tz /= len;
        state.x = track[0].x - tx*0.15f;
        state.z = track[0].z - tz*0.15f;
        state.heading = atan2f(tx, tz);
    }
    state.speed = 15.0f;
    state.track_progress = 0.95f;
    state.track_segment = 70U;
    state.lap_time = 3.0f;
    state.checkpoint_mask = RACER_CHECKPOINT_MASK_ALL; /* simulate all three valid sectors */
    input.throttle = 0.0f;
    input.brake = 0.0f;
    input.boost = 0.0f;
    input.steering = 0.0f;
    racer_update(&state, track, 80U, &input, 1.0f/60.0f);
    CHECK(state.lap == 2U);
    CHECK(state.best_lap_time > 3.0f);
    CHECK(state.lap_time == 0.0f);
    CHECK(state.checkpoint_mask == 0U);

    /* A physically valid finish-line crossing cannot finish a lap when sector
       gates were skipped; crossing the line clears the incomplete sequence. */
    racer_init(&state, track, 80U);
    {
        float tx = track[1].x - track[0].x;
        float tz = track[1].z - track[0].z;
        float len = sqrtf(tx*tx + tz*tz);
        tx /= len; tz /= len;
        state.x = track[0].x - tx*0.15f;
        state.z = track[0].z - tz*0.15f;
        state.heading = atan2f(tx, tz);
    }
    state.speed = 15.0f;
    state.lap_time = 3.0f;
    state.checkpoint_mask = 1U; /* skipped sector gates 2 and 3 */
    racer_update(&state, track, 80U, &input, 1.0f/60.0f);
    CHECK(state.lap == 1U);
    CHECK(state.checkpoint_mask == 0U);

    /* Starting exactly on the line must not immediately register a lap, even
       if stale progress metadata claims that the pod was near the end of a lap. */
    racer_init(&state, track, 80U);
    state.x = track[0].x;
    state.z = track[0].z;
    state.heading = atan2f(track[1].x-track[0].x, track[1].z-track[0].z);
    state.speed = 15.0f;
    state.track_progress = 0.95f;
    state.track_segment = 70U;
    state.lap_time = 3.0f;
    racer_update(&state, track, 80U, &input, 1.0f/60.0f);
    CHECK(state.lap == 1U);

    /* Drift creates a chassis/velocity slip angle and stores a controlled-drift charge. */
    racer_init(&state, track, 80U);
    state.boost_energy = 10.0f;
    input.throttle = 1.0f;
    input.steering = 0.0f;
    input.boost = 0.0f;
    input.drift = 0.0f;
    for (i = 0; i < 70U; ++i) racer_update(&state, track, 80U, &input, 1.0f/60.0f);
    input.steering = 0.72f;
    input.drift = 1.0f;
    for (i = 0; i < 55U; ++i) racer_update(&state, track, 80U, &input, 1.0f/60.0f);
    CHECK(state.drifting == 1);
    CHECK(fabsf(state.drift_angle) > 0.05f);
    CHECK(state.drift_charge > 0.0f);
    CHECK(state.boost_energy > 10.0f);
    input.drift = 0.0f;
    for (i = 0; i < 90U; ++i) racer_update(&state, track, 80U, &input, 1.0f/60.0f);
    CHECK(fabsf(state.drift_angle) < 0.46f);

    /* Vehicle grip now changes the drift personality: at identical speed and
       input, a low-grip pod should hold a larger slip angle than a high-grip pod. */
    {
        RacerVehicleSpec low_grip = {"LOW GRIP", 52.0f, 20.0f, 1.0f, 0.82f,
                                     25.0f, 32.0f, 20.0f, 13.0f, 1.0f, 200, 80, 60};
        RacerVehicleSpec high_grip = {"HIGH GRIP", 52.0f, 20.0f, 1.0f, 1.25f,
                                      25.0f, 32.0f, 20.0f, 13.0f, 1.0f, 80, 180, 220};
        racer_init(&low_grip_state, track, 80U);
        racer_init(&high_grip_state, track, 80U);
        low_grip_state.speed = high_grip_state.speed = 24.0f;
        input.throttle = 0.0f;
        input.brake = 0.0f;
        input.boost = 0.0f;
        input.steering = 0.7f;
        input.drift = 1.0f;
        for (i = 0U; i < 24U; ++i) {
            racer_update_vehicle(&low_grip_state, track, 80U, &input, &low_grip, 1.0f/60.0f);
            racer_update_vehicle(&high_grip_state, track, 80U, &input, &high_grip, 1.0f/60.0f);
        }
        CHECK(fabsf(low_grip_state.drift_angle) > fabsf(high_grip_state.drift_angle) + 0.04f);
    }

    /* The road edge now penalizes speed gradually instead of switching abruptly. */
    racer_init(&edge_state, track, 80U);
    racer_init(&center_state, track, 80U);
    edge_state.speed = 20.0f;
    center_state.speed = 20.0f;
    edge_state.offroad_severity = 0.5f;
    center_state.offroad_severity = 0.0f;
    input.throttle = 0.0f;
    input.brake = 0.0f;
    input.steering = 0.0f;
    input.boost = 0.0f;
    input.drift = 0.0f;
    racer_update(&edge_state, track, 80U, &input, 1.0f/60.0f);
    racer_update(&center_state, track, 80U, &input, 1.0f/60.0f);
    CHECK(edge_state.speed < center_state.speed);

    /* Within the edge band severity is fractional before off-road status flips. */
    racer_init(&state, track, 80U);
    state.x = 36.0f;
    state.z = 0.0f;
    racer_update(&state, track, 80U, &input, 1.0f/60.0f);
    CHECK(state.offroad == 0);
    CHECK(state.offroad_severity > 0.0f && state.offroad_severity < 1.0f);

    /* Runtime road-edge checks use each circuit's rendered width: the same
       six-unit lateral offset is off-road on a narrow course but still inside
       the wider speedway, instead of applying one fixed width to every track. */
    racer_init(&narrow_road_state, track, 80U);
    racer_init(&wide_road_state, track, 80U);
    narrow_road_state.x = wide_road_state.x = 36.0f;
    narrow_road_state.z = wide_road_state.z = 0.0f;
    racer_update_vehicle_surface_width(&narrow_road_state, track, 80U, &input,
                                       NULL, 1.0f, 0.0f, 10.0f, 1.0f/60.0f);
    racer_update_vehicle_surface_width(&wide_road_state, track, 80U, &input,
                                       NULL, 1.0f, 0.0f, 13.0f, 1.0f/60.0f);
    CHECK(narrow_road_state.offroad == 1);
    CHECK(wide_road_state.offroad == 0);
    CHECK(narrow_road_state.offroad_severity > wide_road_state.offroad_severity);

    /* Severe damage lowers the effective speed ceiling compared with a clean pod. */
    racer_init(&damaged_state, track, 80U);
    racer_init(&clean_state, track, 80U);
    damaged_state.speed = 50.0f;
    clean_state.speed = 50.0f;
    damaged_state.damage = 100.0f;
    clean_state.damage = 0.0f;
    input.throttle = 0.0f;
    input.brake = 0.0f;
    input.steering = 0.0f;
    racer_update(&damaged_state, track, 80U, &input, 1.0f/60.0f);
    racer_update(&clean_state, track, 80U, &input, 1.0f/60.0f);
    CHECK(damaged_state.speed < clean_state.speed);
    CHECK(damaged_state.speed < 50.0f);

    projection = racer_project_to_track(track[12].x, track[12].z, track, 80U);
    CHECK(projection.distance_sq < 0.01f);
    CHECK(projection.total_length > 100.0f);
    CHECK(projection.progress >= 0.0f && projection.progress < 1.0f);

    state.x = 1000.0f;
    state.z = 1000.0f;
    input.throttle = 0.0f;
    input.steering = 0.0f;
    racer_update(&state, track, 80U, &input, 1.0f/60.0f);
    CHECK(state.offroad == 1);
    CHECK(state.track_distance > 10.0f);

    puts("PASS: acceleration, braking, steering, drift charging/slip recovery, boost energy/overheat/cooling, boost over-speed and smooth release, damage penalties, lap crossing, track-width-aware edge penalties, vehicle-specific drift feel and off-road detection");
    return 0;
}
