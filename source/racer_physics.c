/* Portable arcade pod handling used by the native GameCube prototype and host tests. */
#include "racer_physics.h"
#include "track_bank.h"
#include <math.h>
#include <stddef.h>
#include <string.h>

#define RACER_BASE_TOP_SPEED 52.0f
#define RACER_ROAD_HALF_WIDTH 6.0f
#define RACER_PI 3.14159265358979323846f

static const RacerVehicleSpec g_default_vehicle = {
    "BALANCED", RACER_BASE_TOP_SPEED, 19.0f, 1.0f, 1.0f,
    24.0f, 30.0f, 19.0f, 13.0f, 1.0f, 190, 52, 35
};

static float clampf(float value, float low, float high)
{
    if (value < low) return low;
    if (value > high) return high;
    return value;
}

static float length2(float x, float z)
{
    return sqrtf(x*x + z*z);
}


#define RACER_TRACK_COORD_LIMIT 1000000.0f
#define RACER_TRACK_COUNT_LIMIT 4096U

static int track_value_is_valid(float value)
{
    return value == value && value >= -RACER_TRACK_COORD_LIMIT &&
           value <= RACER_TRACK_COORD_LIMIT;
}

/* Reject teleports and severe frame discontinuities as lap/checkpoint
   crossings. Normal movement remains well below this bound because physics
   clamps dt to 0.05 s, with extra room for high-speed boosted crossings. */
static int gate_sweep_is_plausible(float previous_x, float previous_z,
                                   float current_x, float current_z,
                                   float road_width)
{
    float dx = current_x - previous_x;
    float dz = current_z - previous_z;
    float maximum_sweep = road_width * 1.5f + 4.0f;
    float distance_sq = dx * dx + dz * dz;
    return track_value_is_valid(dx) && track_value_is_valid(dz) &&
           track_value_is_valid(distance_sq) &&
           distance_sq <= maximum_sweep * maximum_sweep;
}

static RacerTrackProjection invalid_track_projection(void)
{
    RacerTrackProjection result;
    memset(&result, 0, sizeof(result));
    result.distance_sq = 3.402823466e+38F;
    return result;
}

static unsigned int segment_ring_distance(unsigned int a, unsigned int b,
                                          unsigned int count)
{
    unsigned int direct = a > b ? a - b : b - a;
    unsigned int wrapped = count - direct;
    return direct < wrapped ? direct : wrapped;
}

RacerTrackProjection racer_project_to_track(float x, float z,
                                             const RacerTrackPoint *track,
                                             unsigned int count)
{
    RacerTrackProjection result = invalid_track_projection();
    float best_sq = 3.402823466e+38F;
    float accumulated = 0.0f;
    float best_along = 0.0f;
    float total_length = 0.0f;
    unsigned int i;

    if (track == NULL || count < 3U || count > RACER_TRACK_COUNT_LIMIT ||
        !track_value_is_valid(x) || !track_value_is_valid(z)) return result;

    /* Validate the complete route before doing geometry: one NaN would make
       closest-segment selection dependent on comparison order. */
    for (i = 0U; i < count; ++i) {
        if (!track_value_is_valid(track[i].x) ||
            !track_value_is_valid(track[i].y) ||
            !track_value_is_valid(track[i].z)) return result;
    }

    for (i = 0U; i < count; ++i) {
        const RacerTrackPoint *a = &track[i];
        const RacerTrackPoint *b = &track[(i + 1U) % count];
        float dx = b->x - a->x;
        float dz = b->z - a->z;
        total_length += length2(dx, dz);
    }
    if (!(total_length > 1.0e-5f) || !track_value_is_valid(total_length))
        return result;

    for (i = 0U; i < count; ++i) {
        const RacerTrackPoint *a = &track[i];
        const RacerTrackPoint *b = &track[(i + 1U) % count];
        float dx = b->x - a->x;
        float dz = b->z - a->z;
        float seg_len_sq = dx*dx + dz*dz;
        float t = 0.0f;
        float px, pz, py, ex, ez, dist_sq, seg_len, lateral = 0.0f;
        if (seg_len_sq > 1.0e-8f) {
            t = clampf(((x - a->x)*dx + (z - a->z)*dz) / seg_len_sq,
                       0.0f, 1.0f);
        }
        px = a->x + t*dx;
        pz = a->z + t*dz;
        py = a->y + t*(b->y - a->y);
        ex = x - px;
        ez = z - pz;
        dist_sq = ex*ex + ez*ez;
        seg_len = sqrtf(seg_len_sq);
        if (seg_len > 1.0e-5f)
            lateral = ex * (dz / seg_len) + ez * (-dx / seg_len);
        if (dist_sq < best_sq) {
            best_sq = dist_sq;
            result.segment = i;
            result.segment_t = t;
            result.x = px;
            result.y = py;
            result.z = pz;
            result.lateral_offset = lateral;
            best_along = accumulated + t*seg_len;
        }
        accumulated += seg_len;
    }

    result.distance_sq = best_sq;
    result.total_length = total_length;
    result.progress = best_along / total_length;
    if (result.progress < 0.0f) result.progress = 0.0f;
    if (result.progress >= 1.0f) result.progress = 0.0f;
    return result;
}

RacerTrackProjection racer_project_to_track_near(float x, float z,
                                                  const RacerTrackPoint *track,
                                                  unsigned int count,
                                                  unsigned int hint_segment)
{
    RacerTrackProjection global = racer_project_to_track(x, z, track, count);
    RacerTrackProjection local = invalid_track_projection();
    float accumulated = 0.0f;
    float best_sq = 3.402823466e+38F;
    float best_along = 0.0f;
    unsigned int i, radius;

    if (track == NULL || count < 3U || count > RACER_TRACK_COUNT_LIMIT ||
        global.distance_sq == 3.402823466e+38F) return global;

    hint_segment %= count;
    radius = count / 16U;
    if (radius < 2U) radius = 2U;
    if (radius > 12U) radius = 12U;

    for (i = 0U; i < count; ++i) {
        const RacerTrackPoint *a = &track[i];
        const RacerTrackPoint *b = &track[(i + 1U) % count];
        float dx = b->x - a->x;
        float dz = b->z - a->z;
        float seg_len_sq = dx*dx + dz*dz;
        float seg_len = sqrtf(seg_len_sq);
        if (segment_ring_distance(i, hint_segment, count) <= radius) {
            float t = 0.0f, px, pz, py, ex, ez, dist_sq, lateral = 0.0f;
            if (seg_len_sq > 1.0e-8f) {
                t = clampf(((x - a->x)*dx + (z - a->z)*dz) / seg_len_sq,
                           0.0f, 1.0f);
            }
            px = a->x + t*dx;
            pz = a->z + t*dz;
            py = a->y + t*(b->y - a->y);
            ex = x - px;
            ez = z - pz;
            dist_sq = ex*ex + ez*ez;
            if (seg_len > 1.0e-5f)
                lateral = ex * (dz / seg_len) + ez * (-dx / seg_len);
            if (dist_sq < best_sq) {
                best_sq = dist_sq;
                local.segment = i;
                local.segment_t = t;
                local.x = px;
                local.y = py;
                local.z = pz;
                local.lateral_offset = lateral;
                best_along = accumulated + t*seg_len;
            }
        }
        accumulated += seg_len;
    }

    if (best_sq == 3.402823466e+38F) return global;
    /* Two world units of slack preserves continuity through self-crossings,
       without trapping a pod on a distant segment after an off-road excursion. */
    if (best_sq <= global.distance_sq + 4.0f) {
        local.distance_sq = best_sq;
        local.total_length = global.total_length;
        local.progress = best_along / global.total_length;
        if (local.progress < 0.0f) local.progress = 0.0f;
        if (local.progress >= 1.0f) local.progress = 0.0f;
        return local;
    }
    return global;
}

float racer_track_lateral_offset(float x, float z,
                                 const RacerTrackPoint *track,
                                 unsigned int count)
{
    RacerTrackProjection p;
    if (track == NULL || count < 3U) return 0.0f;
    p = racer_project_to_track(x, z, track, count);
    if (p.distance_sq == 3.402823466e+38F) return 0.0f;
    return p.lateral_offset;
}


int racer_checkpoint_gate_at_progress(const RacerTrackPoint *track, unsigned int count,
                                       float progress, RacerCheckpointGate *out_gate)
{
    float total_length = 0.0f, target, accumulated = 0.0f;
    unsigned int i;
    if (out_gate == NULL) return 0;
    memset(out_gate, 0, sizeof(*out_gate));
    if (track == NULL || count < 3U || count > RACER_TRACK_COUNT_LIMIT ||
        !track_value_is_valid(progress) || progress < 0.0f || progress > 1.0f)
        return 0;
    for (i = 0U; i < count; ++i) {
        const RacerTrackPoint *a = &track[i];
        const RacerTrackPoint *b = &track[(i + 1U) % count];
        float dx, dz, length;
        if (!track_value_is_valid(a->x) || !track_value_is_valid(a->y) ||
            !track_value_is_valid(a->z)) return 0;
        dx = b->x - a->x;
        dz = b->z - a->z;
        length = length2(dx, dz);
        total_length += length;
        if (!track_value_is_valid(total_length)) return 0;
    }
    if (!(total_length > 1.0e-5f)) return 0;
    target = progress * total_length;
    for (i = 0U; i < count; ++i) {
        const RacerTrackPoint *a = &track[i];
        const RacerTrackPoint *b = &track[(i + 1U) % count];
        float dx = b->x - a->x;
        float dz = b->z - a->z;
        float length = length2(dx, dz);
        if (length > 1.0e-5f && (target <= accumulated + length || i == count - 1U)) {
            float t = clampf((target - accumulated) / length, 0.0f, 1.0f);
            out_gate->x = a->x + dx * t;
            out_gate->z = a->z + dz * t;
            out_gate->tangent_x = dx / length;
            out_gate->tangent_z = dz / length;
            out_gate->valid = 1;
            return 1;
        }
        accumulated += length;
    }
    return 0;
}

int racer_crossed_checkpoint_gate(float previous_x, float previous_z,
                                  float current_x, float current_z,
                                  const RacerCheckpointGate *gate, float road_width)
{
    float previous_along, current_along, cross_fraction;
    float cross_x, cross_z, lateral;
    if (gate == NULL || !gate->valid ||
        !track_value_is_valid(previous_x) || !track_value_is_valid(previous_z) ||
        !track_value_is_valid(current_x) || !track_value_is_valid(current_z) ||
        !track_value_is_valid(gate->x) || !track_value_is_valid(gate->z) ||
        !track_value_is_valid(gate->tangent_x) || !track_value_is_valid(gate->tangent_z) ||
        !track_value_is_valid(road_width) || road_width < 1.0f ||
        !gate_sweep_is_plausible(previous_x, previous_z, current_x, current_z,
                                 road_width)) return 0;
    previous_along = (previous_x - gate->x) * gate->tangent_x +
                     (previous_z - gate->z) * gate->tangent_z;
    current_along = (current_x - gate->x) * gate->tangent_x +
                    (current_z - gate->z) * gate->tangent_z;
    if (!(previous_along < -0.05f && current_along >= 0.0f) ||
        current_along - previous_along < 1.0e-5f) return 0;
    cross_fraction = -previous_along / (current_along - previous_along);
    cross_fraction = clampf(cross_fraction, 0.0f, 1.0f);
    cross_x = previous_x + (current_x - previous_x) * cross_fraction;
    cross_z = previous_z + (current_z - previous_z) * cross_fraction;
    lateral = (cross_x - gate->x) * gate->tangent_z -
              (cross_z - gate->z) * gate->tangent_x;
    return fabsf(lateral) <= road_width * 0.5f + 1.0f;
}

int racer_crossed_finish_line(float previous_x, float previous_z,
                              float current_x, float current_z,
                              const RacerTrackPoint *track, unsigned int count,
                              float road_width)
{
    float tx, tz, tangent_len, previous_along, current_along;
    float cross_fraction, cross_x, cross_z, lateral, allowed_lateral;
    if (track == NULL || count < 3U || count > RACER_TRACK_COUNT_LIMIT ||
        !track_value_is_valid(previous_x) || !track_value_is_valid(previous_z) ||
        !track_value_is_valid(current_x) || !track_value_is_valid(current_z) ||
        !track_value_is_valid(track[0].x) || !track_value_is_valid(track[0].z) ||
        !track_value_is_valid(track[1].x) || !track_value_is_valid(track[1].z))
        return 0;
    if (!track_value_is_valid(road_width) || road_width < 1.0f ||
        !gate_sweep_is_plausible(previous_x, previous_z, current_x, current_z,
                                 road_width)) return 0;

    tx = track[1].x - track[0].x;
    tz = track[1].z - track[0].z;
    tangent_len = length2(tx, tz);
    if (tangent_len < 1.0e-5f) return 0;
    tx /= tangent_len;
    tz /= tangent_len;

    /* Signed distance along the first route tangent: negative is before the
       finish plane, positive is beyond it. Requiring a meaningful negative
       starting distance prevents the race start itself from counting a lap. */
    previous_along = (previous_x - track[0].x) * tx +
                     (previous_z - track[0].z) * tz;
    current_along = (current_x - track[0].x) * tx +
                    (current_z - track[0].z) * tz;
    if (!(previous_along < -0.05f && current_along >= 0.0f) ||
        current_along - previous_along < 1.0e-5f) return 0;

    cross_fraction = -previous_along / (current_along - previous_along);
    cross_fraction = clampf(cross_fraction, 0.0f, 1.0f);
    cross_x = previous_x + (current_x - previous_x) * cross_fraction;
    cross_z = previous_z + (current_z - previous_z) * cross_fraction;
    /* The start line spans the local road width, not the infinite plane. */
    lateral = (cross_x - track[0].x) * tz - (cross_z - track[0].z) * tx;
    allowed_lateral = road_width * 0.5f + 1.0f;
    return fabsf(lateral) <= allowed_lateral;
}

void racer_init(RacerState *state, const RacerTrackPoint *track, unsigned int count)
{
    RacerTrackProjection projection;
    const RacerTrackPoint *a;
    const RacerTrackPoint *b;
    if (state == NULL) return;
    memset(state, 0, sizeof(*state));
    state->lap = 1U;
    state->boost_energy = 100.0f;
    if (track == NULL || count < 3U) return;
    state->x = track[0].x;
    state->y = track[0].y + 1.0f;
    state->z = track[0].z;
    a = &track[0];
    b = &track[1];
    state->heading = atan2f(b->x - a->x, b->z - a->z);
    projection = racer_project_to_track(state->x, state->z, track, count);
    state->track_segment = projection.segment;
    state->track_progress = projection.progress;
    state->track_distance = sqrtf(projection.distance_sq);
    state->track_lateral_offset = projection.lateral_offset;
    {
        unsigned int checkpoint;
        for (checkpoint = 0U; checkpoint < RACER_CHECKPOINT_COUNT; ++checkpoint) {
            float progress = (float)(checkpoint + 1U) /
                             (float)(RACER_CHECKPOINT_COUNT + 1U);
            (void)racer_checkpoint_gate_at_progress(track, count, progress,
                                                     &state->checkpoint_gates[checkpoint]);
        }
    }
}

static float move_toward_physics(float current, float target, float max_delta)
{
    if (current < target) return current + ((target-current < max_delta) ? target-current : max_delta);
    if (current > target) return current - ((current-target < max_delta) ? current-target : max_delta);
    return target;
}

void racer_update_vehicle_surface_width(RacerState *state, const RacerTrackPoint *track,
                                        unsigned int count, const RacerInput *input,
                                        const RacerVehicleSpec *vehicle,
                                        float surface_grip, float rolling_resistance,
                                        float road_width, float dt)
{
    RacerTrackProjection projection;
    float previous_x, previous_z, steering, throttle, brake, boost, drift;
    float acceleration, drag, steering_rate, travel_heading, speed_ratio;
    float damage_top_speed, damage_handling, high_speed_steering;
    float normal_speed_limit, speed_limit, speed_before_update;
    float road_half_width, offroad_limit, edge_start, offroad_metric;
    unsigned int previous_segment;
    int boosting;
    float damage_factor;

    if (state == NULL || track == NULL || count < 3U || input == NULL) return;
    if (vehicle == NULL) vehicle = &g_default_vehicle;
    dt = clampf(dt, 0.0f, 0.05f);
    surface_grip = clampf(surface_grip, 0.60f, 1.20f);
    rolling_resistance = clampf(rolling_resistance, 0.0f, 3.0f);
    /* Protect physics from invalid track metadata while supporting the current
       narrow technical tracks and wider speedways. */
    road_width = clampf(road_width, 8.0f, 20.0f);
    road_half_width = road_width * 0.5f;
    edge_start = fmaxf(0.5f, road_half_width - 0.5f);
    offroad_limit = road_half_width + 8.0f;
    if (dt <= 0.0f) return;

    steering = clampf(input->steering, -1.0f, 1.0f);
    throttle = clampf(input->throttle, 0.0f, 1.0f);
    brake = clampf(input->brake, 0.0f, 1.0f);
    boost = clampf(input->boost, 0.0f, 1.0f);
    drift = clampf(input->drift, 0.0f, 1.0f);
    previous_x = state->x;
    previous_z = state->z;
    previous_segment = state->track_segment;
    state->race_time += dt;
    state->lap_time += dt;

    if (vehicle->top_speed < 10.0f || vehicle->acceleration < 0.0f ||
        vehicle->steering < 0.1f || vehicle->grip < 0.1f) vehicle = &g_default_vehicle;
    boosting = (boost > 0.01f && state->boost_energy > 0.01f &&
                state->boost_heat < 100.0f && !state->overheated);
    state->boost_active = boosting;
    if (boosting) {
        state->boost_energy -= 24.0f * dt * boost;
        state->boost_heat += vehicle->boost_heat_rate * dt * boost;
        if (state->boost_energy < 0.0f) state->boost_energy = 0.0f;
        if (state->boost_heat >= 100.0f) {
            state->boost_heat = 100.0f;
            state->overheated = 1;
            state->boost_active = 0;
        }
    } else {
        state->boost_heat -= vehicle->boost_cooling_rate * dt;
        if (state->boost_heat < 0.0f) state->boost_heat = 0.0f;
        if (state->overheated && state->boost_heat <= 42.0f) state->overheated = 0;
        state->boost_energy += 2.4f * dt;
    }

    /* Damage now has three readable consequences: weaker acceleration, a lower
       speed ceiling, and less responsive steering. The effects build gradually
       so a small scrape does not make the pod feel broken. */
    damage_factor = state->damage > 60.0f ? 1.0f - (state->damage - 60.0f)*0.0075f : 1.0f;
    damage_factor = clampf(damage_factor, 0.70f, 1.0f);
    damage_top_speed = 1.0f - 0.18f * (state->damage / 100.0f);
    damage_handling = 1.0f - 0.22f * (state->damage / 100.0f);
    speed_ratio = clampf(state->speed / vehicle->top_speed, 0.0f, 1.0f);
    acceleration = vehicle->acceleration * throttle * damage_factor;
    if (state->boost_active) acceleration += vehicle->boost_power * boost;
    acceleration *= 1.0f - 0.25f * speed_ratio;
    drag = 1.15f + 0.047f*state->speed + rolling_resistance;
    /* The road edge is a gradient, not a binary switch: grip and speed
       begin to suffer before the pod is fully classified as off-road. */
    drag += 6.5f * clampf(state->offroad_severity, 0.0f, 1.0f);
    if (state->damage > 80.0f) drag += 1.7f;
    speed_before_update = state->speed;
    state->speed += (acceleration - drag) * dt;
    state->speed -= 34.0f * brake * dt;

    /* A live boost can push a pod beyond its normal top speed. When boost is
       released or overheats, let that extra velocity bleed away over time
       instead of snapping instantly back to the normal speed ceiling. */
    normal_speed_limit = vehicle->top_speed * damage_top_speed;
    speed_limit = normal_speed_limit;
    if (state->boost_active) {
        speed_limit *= 1.16f;
    } else if (state->speed > normal_speed_limit) {
        speed_limit = fmaxf(normal_speed_limit, speed_before_update - 18.0f * dt);
    }
    state->speed = clampf(state->speed, 0.0f, speed_limit);

    /* Y is a handbrake drift: yaw continues to turn while the velocity direction lags. */
    state->drifting = drift > 0.5f && state->speed > 10.0f && fabsf(steering) > 0.08f;
    /* At high speed, a small stick movement should not snap the pod sideways.
       The speed curve keeps low/mid-speed agility while making fast corners
       require anticipation. Vehicle steering and grip still differentiate pods. */
    high_speed_steering = 1.0f - 0.75f * speed_ratio * speed_ratio;
    high_speed_steering = clampf(high_speed_steering, 0.25f, 1.0f);
    steering_rate = (0.20f + 0.031f*state->speed) * vehicle->steering *
                    surface_grip * damage_handling * high_speed_steering;
    steering_rate *= 1.0f - 0.28f * clampf(state->offroad_severity, 0.0f, 1.0f);
    if (state->drifting) steering_rate *= 1.24f;
    state->heading += steering * steering_rate * dt;
    while (state->heading > RACER_PI) state->heading -= 2.0f*RACER_PI;
    while (state->heading < -RACER_PI) state->heading += 2.0f*RACER_PI;

    if (state->drifting) {
        /* Give each pod a recognizable drift personality: high-grip vehicles
           hold a tighter slip angle, while low-grip/high-speed specialists
           rotate farther and need more correction. Keep the multiplier bounded
           so catalogue tuning cannot create an uncontrollable snap-spin. */
        float grip_slip = clampf(1.0f / vehicle->grip, 0.78f, 1.25f);
        float target_slip = steering * 0.46f *
                            clampf(state->speed/28.0f, 0.35f, 1.0f) * grip_slip;
        state->drift_angle = move_toward_physics(state->drift_angle, target_slip,
                                                 (2.2f + vehicle->grip*0.55f)*dt);
        {
            float edge_factor = 1.0f - clampf(state->offroad_severity, 0.0f, 1.0f);
            float charge = vehicle->drift_charge_rate * fabsf(steering) *
                           clampf(state->speed/vehicle->top_speed, 0.0f, 1.0f) *
                           edge_factor * dt;
            state->boost_energy += charge * 0.78f;
            state->drift_charge += charge * 3.2f;
            if (state->drift_charge >= 100.0f) {
                state->drift_charge = 60.0f;
                state->boost_energy += 12.0f;
            }
        }
    } else {
        state->drift_angle = move_toward_physics(state->drift_angle, 0.0f,
                                                  (2.3f*vehicle->grip*surface_grip)*dt);
        state->drift_charge -= 24.0f*dt;
        if (state->drift_charge < 0.0f) state->drift_charge = 0.0f;
    }
    state->boost_energy = clampf(state->boost_energy, 0.0f, 100.0f);
    state->damage = clampf(state->damage, 0.0f, 100.0f);

    travel_heading = state->heading - state->drift_angle;
    state->x += sinf(travel_heading) * state->speed * dt;
    state->z += cosf(travel_heading) * state->speed * dt;

    projection = racer_project_to_track_near(state->x, state->z, track, count,
                                             previous_segment);
    state->track_segment = projection.segment;
    state->track_progress = projection.progress;
    state->track_distance = sqrtf(projection.distance_sq);
    state->track_lateral_offset = projection.lateral_offset;
    /* Use the signed cross-track offset as well as Euclidean distance. This
       avoids treating a longitudinal endpoint miss as if it were lateral
       drift, while preserving the old recovery metric for sparse routes. */
    offroad_metric = fmaxf(state->track_distance, fabsf(state->track_lateral_offset));
    state->offroad_severity = clampf((offroad_metric - edge_start) /
                                      (offroad_limit - edge_start), 0.0f, 1.0f);
    state->offroad = (offroad_metric > road_half_width + 0.8f) ? 1 : 0;
    {
        const RacerTrackPoint *seg_a = &track[projection.segment % count];
        const RacerTrackPoint *seg_b = &track[(projection.segment + 1U) % count];
        float seg_dx = seg_b->x - seg_a->x;
        float seg_dz = seg_b->z - seg_a->z;
        float seg_len = length2(seg_dx, seg_dz);
        float lateral = 0.0f;
        float bank0 = racer_track_bank_height(track, count, projection.segment, road_width);
        if (seg_len > 1.0e-5f) {
            lateral = (state->x - projection.x) * (seg_dz / seg_len) +
                      (state->z - projection.z) * (-seg_dx / seg_len);
        }
        float bank1 = racer_track_bank_height(track, count,
                                              (projection.segment + 1U) % count,
                                              road_width);
        float bank = bank0 + (bank1 - bank0) * projection.segment_t;
        float across = clampf(lateral / road_half_width, -1.0f, 1.0f);
        /* Match the road mesh's cross-slope so pods do not float above or cut
           into the surface when running near the inside/outside edge. */
        state->y = projection.y + 1.0f + bank * across;
    }

    /* A soft edge response keeps the player on recoverable shoulders without
       snapping them back to the centerline. The correction is signed, so the
       nearest tangent determines which side is outside. */
    {
        float lateral = projection.lateral_offset;
        float abs_lateral = fabsf(lateral);
        float shoulder_limit = road_half_width + 0.15f;
        if (abs_lateral > shoulder_limit && abs_lateral <= offroad_limit) {
            const RacerTrackPoint *a = &track[projection.segment % count];
            const RacerTrackPoint *b = &track[(projection.segment + 1U) % count];
            float dx = b->x - a->x;
            float dz = b->z - a->z;
            float len = length2(dx, dz);
            if (len > 1.0e-5f) {
                float normal_x = dz / len;
                float normal_z = -dx / len;
                float target = lateral < 0.0f ? -shoulder_limit : shoulder_limit;
                float correction = (target - lateral) * clampf(4.0f * dt, 0.0f, 0.20f);
                state->x += normal_x * correction;
                state->z += normal_z * correction;
                state->speed = fmaxf(0.0f, state->speed - 2.5f * dt);
            }
        }
    }
    if (state->track_distance > offroad_limit) {
        float pull = clampf((state->track_distance - offroad_limit) * 0.8f * dt, 0.0f, 0.18f);
        state->x += (projection.x - state->x) * pull;
        state->z += (projection.z - state->z) * pull;
        state->speed = fmaxf(0.0f, state->speed - 4.0f*dt);
    }

    /* Check three physical sector gates in route order. A finish-line crossing
       without all sectors invalidates the partial lap and clears the mask, so
       accumulated checkpoints cannot be carried across a shortcut. */
    {
        unsigned int checkpoint;
        for (checkpoint = 0U; checkpoint < RACER_CHECKPOINT_COUNT; ++checkpoint) {
            unsigned int required_before = (1U << checkpoint) - 1U;
            /* Gates must be reached in route order. Merely crossing a nearby
               later gate on a self-intersecting circuit cannot validate it. */
            if ((state->checkpoint_mask & required_before) == required_before &&
                racer_crossed_checkpoint_gate(previous_x, previous_z,
                    state->x, state->z, &state->checkpoint_gates[checkpoint],
                    road_width))
                state->checkpoint_mask |= (1U << checkpoint);
        }
    }
    /* A lap requires the physical finish line and every physical sector gate.
       Progress wrapping alone is insufficient on self-crossing routes. */
    if (racer_crossed_finish_line(previous_x, previous_z, state->x, state->z,
                                  track, count, road_width)) {
        if (state->speed > 4.0f && state->lap_time > 2.0f &&
            (state->checkpoint_mask & RACER_CHECKPOINT_MASK_ALL) ==
                RACER_CHECKPOINT_MASK_ALL) {
            if (state->best_lap_time <= 0.0f || state->lap_time < state->best_lap_time)
                state->best_lap_time = state->lap_time;
            state->lap += 1U;
            state->lap_time = 0.0f;
        }
        state->checkpoint_mask = 0U;
    }
}


void racer_update_vehicle_surface(RacerState *state, const RacerTrackPoint *track,
                                  unsigned int count, const RacerInput *input,
                                  const RacerVehicleSpec *vehicle,
                                  float surface_grip, float rolling_resistance,
                                  float dt)
{
    /* Backwards-compatible default for host utilities and older callers. */
    racer_update_vehicle_surface_width(state, track, count, input, vehicle,
                                       surface_grip, rolling_resistance,
                                       RACER_ROAD_HALF_WIDTH * 2.0f, dt);
}

void racer_update_vehicle(RacerState *state, const RacerTrackPoint *track,
                          unsigned int count, const RacerInput *input,
                          const RacerVehicleSpec *vehicle, float dt)
{
    racer_update_vehicle_surface(state, track, count, input, vehicle, 1.0f, 0.0f, dt);
}

void racer_apply_impact(RacerState *state, const RacerVehicleSpec *vehicle,
                        float damage_amount, float speed_multiplier)
{
    float resistance;
    if (state == NULL) return;
    if (vehicle == NULL) vehicle = &g_default_vehicle;
    resistance = clampf(vehicle->damage_resistance, 0.25f, 2.0f);
    if (damage_amount < 0.0f) damage_amount = 0.0f;
    if (speed_multiplier < 0.0f) speed_multiplier = 0.0f;
    if (speed_multiplier > 1.0f) speed_multiplier = 1.0f;
    state->damage = clampf(state->damage + damage_amount / resistance, 0.0f, 100.0f);
    state->speed *= speed_multiplier;
    state->boost_energy = clampf(state->boost_energy - damage_amount*0.65f, 0.0f, 100.0f);
}

void racer_update(RacerState *state, const RacerTrackPoint *track,
                  unsigned int count, const RacerInput *input, float dt)
{
    racer_update_vehicle(state, track, count, input, &g_default_vehicle, dt);
}
