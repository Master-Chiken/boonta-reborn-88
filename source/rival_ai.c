/* Portable rival driving, lane choice, and contact response for host tests and libogc. */
#include "rival_ai.h"
#include "track_bank.h"
#include <math.h>
#include <string.h>

#define RIVAL_PI 3.14159265358979323846f
#define RIVAL_COLLISION_RADIUS 4.4f
#define RIVAL_DEFAULT_ROAD_WIDTH 12.0f

static float clampf_ai(float v, float lo, float hi)
{
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

float rival_ai_lane_limit_for_width(float road_width)
{
    /* Keep two reliable racing lanes on narrow technical routes while allowing
       modestly wider overtakes on wide speedways. The limit is never so wide
       that a default pod begins on the shoulder. */
    if (!(road_width == road_width)) road_width = RIVAL_DEFAULT_ROAD_WIDTH; /* NaN guard */
    road_width = clampf_ai(road_width, 8.0f, 20.0f);
    return clampf_ai(road_width * 0.225f, 2.0f, 3.8f);
}

static float move_toward(float current, float target, float max_delta)
{
    if (current < target) return current + ((target-current < max_delta) ? target-current : max_delta);
    if (current > target) return current - ((current-target < max_delta) ? current-target : max_delta);
    return target;
}

static float wrap01_ai(float p)
{
    while (p < 0.0f) p += 1.0f;
    while (p >= 1.0f) p -= 1.0f;
    return p;
}

static float track_total_length(const RacerTrackPoint *track, unsigned int count)
{
    float total = 0.0f;
    unsigned int i;
    if (track == 0 || count < 2U) return 0.0f;
    for (i = 0; i < count; ++i) {
        const RacerTrackPoint *a = &track[i];
        const RacerTrackPoint *b = &track[(i+1U)%count];
        float dx = b->x-a->x;
        float dz = b->z-a->z;
        total += sqrtf(dx*dx + dz*dz);
    }
    return total;
}

static float track_lateral_offset(const RacerState *player,
                                  const RacerTrackPoint *track,
                                  unsigned int count)
{
    RacerTrackProjection p;
    const RacerTrackPoint *a, *b;
    float dx, dz, len;
    if (player == 0 || track == 0 || count < 2U) return 0.0f;
    p = racer_project_to_track(player->x, player->z, track, count);
    a = &track[p.segment % count];
    b = &track[(p.segment+1U)%count];
    dx = b->x-a->x;
    dz = b->z-a->z;
    len = sqrtf(dx*dx + dz*dz);
    if (len < 1.0e-5f) return 0.0f;
    /* Match the local +X direction used by the pod renderer. */
    return (player->x-p.x)*(dz/len) + (player->z-p.z)*(-dx/len);
}

void rival_ai_set_pose(RivalAIState *rival, const RacerTrackPoint *track,
                       unsigned int track_count, float track_length)
{
    float distance, accumulated = 0.0f;
    unsigned int i;
    if (rival == 0 || track == 0 || track_count < 2U) return;
    if (track_length <= 1.0e-5f) track_length = track_total_length(track, track_count);
    if (track_length <= 1.0e-5f) return;
    rival->progress = wrap01_ai(rival->progress);
    distance = rival->progress * track_length;
    for (i = 0; i < track_count; ++i) {
        const RacerTrackPoint *a = &track[i];
        const RacerTrackPoint *b = &track[(i+1U)%track_count];
        float dx = b->x-a->x;
        float dz = b->z-a->z;
        float len = sqrtf(dx*dx + dz*dz);
        if (len > 1.0e-5f && distance <= accumulated + len) {
            float t = clampf_ai((distance-accumulated)/len, 0.0f, 1.0f);
            float smooth_t = t*t*(3.0f - 2.0f*t);
            float tangent_x = dx/len;
            float tangent_z = dz/len;
            float nx, nz;
            /* Blend the current segment tangent into the next one. At the end
               of a segment, the lane normal and heading now converge to the
               outgoing tangent; the next segment begins with that same tangent.
               This removes visible lateral snaps at polyline/spline vertices. */
            {
                const RacerTrackPoint *c = &track[(i+2U)%track_count];
                float next_dx = c->x-b->x;
                float next_dz = c->z-b->z;
                float next_len = sqrtf(next_dx*next_dx + next_dz*next_dz);
                if (next_len > 1.0e-5f) {
                    float blend_x = tangent_x + (next_dx/next_len-tangent_x)*smooth_t;
                    float blend_z = tangent_z + (next_dz/next_len-tangent_z)*smooth_t;
                    float blend_len = sqrtf(blend_x*blend_x + blend_z*blend_z);
                    /* A near-reversal has no stable averaged tangent; preserve
                       the current segment direction rather than amplify noise. */
                    if (blend_len > 1.0e-4f) {
                        tangent_x = blend_x/blend_len;
                        tangent_z = blend_z/blend_len;
                    }
                }
            }
            nx = tangent_z;
            nz = -tangent_x;
            rival->x = a->x + dx*t + nx*rival->lane_offset;
            {
                float road_width = rival->road_width > 0.0f ? rival->road_width : RIVAL_DEFAULT_ROAD_WIDTH;
                float bank0 = racer_track_bank_height(track, track_count, i, road_width);
                float bank1 = racer_track_bank_height(track, track_count,
                                                      (i + 1U) % track_count, road_width);
                float bank = bank0 + (bank1 - bank0) * t;
                float across = clampf_ai(rival->lane_offset / (0.5f * road_width), -1.0f, 1.0f);
                rival->y = a->y + (b->y-a->y)*t + 1.0f + bank * across;
            }
            rival->z = a->z + dz*t + nz*rival->lane_offset;
            rival->heading = atan2f(tangent_x, tangent_z);
            {
                /* Read several vertices ahead instead of reacting only to the
                   next tiny spline segment. The weighted maximum helps rivals
                   lift before tight turns, while distant corners fade smoothly
                   and cannot dominate the current section indefinitely. */
                unsigned int look;
                float ahead_distance = 0.0f;
                float predicted_corner = 0.0f;
                for (look = 0U; look < 5U && ahead_distance < 60.0f; ++look) {
                    unsigned int vertex = (i + 1U + look) % track_count;
                    const RacerTrackPoint *prev = &track[(vertex + track_count - 1U) % track_count];
                    const RacerTrackPoint *corner = &track[vertex];
                    const RacerTrackPoint *next = &track[(vertex + 1U) % track_count];
                    float ix = corner->x - prev->x;
                    float iz = corner->z - prev->z;
                    float ox = next->x - corner->x;
                    float oz = next->z - corner->z;
                    float in_len = sqrtf(ix*ix + iz*iz);
                    float out_len = sqrtf(ox*ox + oz*oz);
                    if (in_len > 1.0e-5f && out_len > 1.0e-5f) {
                        float turn = fabsf(ix*oz - iz*ox) / (in_len * out_len);
                        float distance_weight = clampf_ai(1.0f - ahead_distance / 60.0f,
                                                          0.20f, 1.0f);
                        float weighted_turn = turn * distance_weight;
                        if (weighted_turn > predicted_corner)
                            predicted_corner = weighted_turn;
                    }
                    /* The next corner is reached after this outgoing segment. */
                    ahead_distance += out_len;
                }
                rival->corner_factor = clampf_ai(predicted_corner, 0.0f, 1.0f);
            }
            return;
        }
        accumulated += len;
    }
    rival->x = track[0].x;
    rival->y = track[0].y + 1.0f +
               racer_track_bank_height(track, track_count, 0U,
                   rival->road_width > 0.0f ? rival->road_width : RIVAL_DEFAULT_ROAD_WIDTH) *
               clampf_ai(rival->lane_offset / (0.5f * (rival->road_width > 0.0f ? rival->road_width : RIVAL_DEFAULT_ROAD_WIDTH)), -1.0f, 1.0f);
    rival->z = track[0].z;
    rival->heading = atan2f(track[1].x-track[0].x, track[1].z-track[0].z);
    rival->corner_factor = 0.0f;
}

void rival_ai_init(RivalAIState *rivals, unsigned int count,
                   const RacerTrackPoint *track, unsigned int track_count,
                   float track_length)
{
    static const unsigned char colors[7][3] = {
        {55,164,233}, {205,77,52}, {104,212,118}, {225,184,63},
        {176,102,218}, {64,205,190}, {225,132,62}
    };
    static const float starting_lanes[RIVAL_AI_LANE_COUNT] = {-2.25f, 2.25f, 0.0f};
    static const float personalities[7] = {0.82f, 1.18f, 1.28f, 0.92f, 1.08f, 1.22f, 0.76f};
    static const float lane_cadence[7] = {3.1f, 2.2f, 1.8f, 2.8f, 2.4f, 1.95f, 3.3f};
    unsigned int i;
    if (rivals == 0) return;
    if (count > 7U) count = 7U;
    if (track_length <= 1.0e-5f) track_length = track_total_length(track, track_count);
    for (i = 0; i < count; ++i) {
        memset(&rivals[i], 0, sizeof(rivals[i]));
        rivals[i].progress = 0.982f - 0.014f*(float)i;
        rivals[i].lap = 0U; /* Pre-grid positions are just before the start line. */
        rivals[i].cruise_speed = 25.5f + (float)(i%4U)*1.25f;
        rivals[i].max_speed = 33.0f + (float)(i%5U)*0.8f;
        rivals[i].acceleration = 7.0f;
        rivals[i].grip = 1.0f;
        rivals[i].boost_power = 7.0f;
        rivals[i].difficulty_scale = 1.0f;
        rivals[i].aggression = personalities[i];
        rivals[i].lane_change_interval = lane_cadence[i];
        rivals[i].surface_grip = 1.0f;
        rivals[i].rolling_resistance = 0.0f;
        rivals[i].road_width = RIVAL_DEFAULT_ROAD_WIDTH;
        rivals[i].speed = rivals[i].cruise_speed;
        rivals[i].boost_energy = 100.0f;
        rivals[i].lane_offset = starting_lanes[i % RIVAL_AI_LANE_COUNT];
        rivals[i].target_lane_offset = starting_lanes[i % RIVAL_AI_LANE_COUNT];
        rivals[i].lane_timer = 1.0f + (float)i*0.65f;
        rivals[i].lane_choice = i;
        rivals[i].r = colors[i][0];
        rivals[i].g = colors[i][1];
        rivals[i].b = colors[i][2];
        rival_ai_set_pose(&rivals[i], track, track_count, track_length);
    }
}

void rival_ai_set_difficulty(RivalAIState *rivals, unsigned int count, unsigned int level)
{
    unsigned int i;
    static const float scales[3] = {0.88f, 1.0f, 1.12f};
    if (rivals == 0) return;
    if (level > 2U) level = 1U;
    if (count > 7U) count = 7U;
    for (i = 0U; i < count; ++i) rivals[i].difficulty_scale = scales[level];
}

void rival_ai_set_track_surface(RivalAIState *rivals, unsigned int count,
                                float surface_grip, float rolling_resistance)
{
    unsigned int i;
    if (rivals == 0) return;
    surface_grip = clampf_ai(surface_grip, 0.60f, 1.20f);
    rolling_resistance = clampf_ai(rolling_resistance, 0.0f, 3.0f);
    if (count > 7U) count = 7U;
    for (i = 0U; i < count; ++i) {
        rivals[i].surface_grip = surface_grip;
        rivals[i].rolling_resistance = rolling_resistance;
    }
}

void rival_ai_set_track_width(RivalAIState *rivals, unsigned int count, float road_width)
{
    unsigned int i;
    if (rivals == 0) return;
    if (!(road_width == road_width)) road_width = RIVAL_DEFAULT_ROAD_WIDTH; /* NaN guard */
    road_width = clampf_ai(road_width, 8.0f, 20.0f);
    if (count > 7U) count = 7U;
    for (i = 0U; i < count; ++i) {
        float limit = rival_ai_lane_limit_for_width(road_width);
        rivals[i].road_width = road_width;
        rivals[i].lane_offset = clampf_ai(rivals[i].lane_offset, -limit, limit);
        rivals[i].target_lane_offset = clampf_ai(rivals[i].target_lane_offset, -limit, limit);
    }
}

void rival_ai_set_vehicle_spec(RivalAIState *r, const RacerVehicleSpec *vehicle)
{
    if (r == 0 || vehicle == 0) return;
    /* Scale catalogue values into the AI's world-units-per-second tuning. */
    r->cruise_speed = clampf_ai(vehicle->top_speed * 0.55f, 23.0f, 32.0f);
    r->max_speed = clampf_ai(vehicle->top_speed * 0.64f, 27.0f, 37.0f);
    r->acceleration = clampf_ai(vehicle->acceleration * 0.31f, 5.0f, 7.8f);
    r->grip = clampf_ai(vehicle->grip, 0.65f, 1.35f);
    r->boost_power = clampf_ai(vehicle->boost_power * 0.27f, 5.0f, 8.5f);
    r->r = vehicle->r;
    r->g = vehicle->g;
    r->b = vehicle->b;
    if (r->speed > r->max_speed) r->speed = r->max_speed;
}

int rival_ai_update(RivalAIState *rivals, unsigned int count,
                    const RacerTrackPoint *track, unsigned int track_count,
                    float track_length, RacerState *player,
                    const RacerVehicleSpec *player_vehicle, float dt)
{
    float player_lateral, player_total_progress;
    unsigned int i;
    int collision = 0;
    if (rivals == 0 || track == 0 || player == 0 || track_count < 3U) return 0;
    dt = clampf_ai(dt, 0.0f, 0.05f);
    if (dt <= 0.0f) return 0;
    if (track_length <= 1.0e-5f) track_length = track_total_length(track, track_count);
    if (track_length <= 1.0e-5f) return 0;
    if (count > 7U) count = 7U;

    /* One player-wide impact cooldown prevents a pack from stacking damage
       across consecutive frames when several pods overlap at once. */
    player->collision_cooldown = (player->collision_cooldown > dt) ?
        player->collision_cooldown - dt : 0.0f;
    player_lateral = track_lateral_offset(player, track, track_count);
    player_total_progress = (float)player->lap - 1.0f + player->track_progress;
    for (i = 0; i < count; ++i) {
        RivalAIState *r = &rivals[i];
        float lane_limit = rival_ai_lane_limit_for_width(r->road_width > 0.0f ? r->road_width : RIVAL_DEFAULT_ROAD_WIDTH);
        float lane_targets[RIVAL_AI_LANE_COUNT] = {-lane_limit, 0.0f, lane_limit};
        float rival_total = (float)r->lap - 1.0f + r->progress;
        float gap = player_total_progress-rival_total;
        float base_speed = r->cruise_speed;
        float desired_speed;
        float dx, dz, dist_sq;
        float draft_strength = 0.0f;
        unsigned int draft_j;

        /* Drafting: a rival following another pod closely and in the same
           lane gains a small pace benefit and recovers extra boost energy.
           Keep the effect bounded and deterministic to avoid rubber-banding. */
        for (draft_j = 0U; draft_j < count; ++draft_j) {
            float ahead_gap, ahead_distance, lane_delta;
            float ahead_dx, ahead_dz, forward, lateral;
            if (draft_j == i) continue;
            /* Use lap-aware race progress: wrapping normalized progress here
               incorrectly let a rival one or more laps behind provide a draft. */
            ahead_gap = ((float)rivals[draft_j].lap + rivals[draft_j].progress) -
                        ((float)r->lap + r->progress);
            ahead_distance = ahead_gap * track_length;
            lane_delta = fabsf(rivals[draft_j].lane_offset - r->lane_offset);
            /* Progress distance alone is not enough on tight hairpins or
               switchbacks: the next racer along the spline may be beside or
               behind us in world space. Require a real forward, in-line pod. */
            ahead_dx = rivals[draft_j].x - r->x;
            ahead_dz = rivals[draft_j].z - r->z;
            forward = ahead_dx*sinf(r->heading) + ahead_dz*cosf(r->heading);
            lateral = ahead_dx*cosf(r->heading) - ahead_dz*sinf(r->heading);
            if (ahead_distance >= 4.0f && ahead_distance <= 20.0f &&
                lane_delta <= 1.8f && forward >= 3.0f && forward <= 22.0f &&
                fabsf(lateral) <= 3.6f) {
                float strength = 1.0f - (ahead_distance - 4.0f) / 16.0f;
                if (strength > draft_strength) draft_strength = strength;
            }
        }

        /* Catch-up is bounded: rivals respond to the race, but cannot teleport. */
        /* Track conditions now affect rival pace as well as player handling.
           Low-grip surfaces require earlier lift through corners; rough terrain
           also adds drag, but the penalty is bounded so the field keeps moving. */
        {
            float grip = r->surface_grip > 0.0f ? r->surface_grip : 1.0f;
            float speed_fraction = clampf_ai(r->speed /
                (r->max_speed > 0.1f ? r->max_speed : 1.0f), 0.0f, 1.12f);
            /* At higher speed, the same bend needs a larger lift. A fixed
               corner penalty made a fast rival carry nearly the same target
               speed as a slow one into a hairpin. */
            float corner_penalty = r->corner_factor *
                ((5.6f + 5.0f * speed_fraction) /
                 (0.72f + r->grip * 0.35f)) * (1.10f / grip);
            float surface_drag = r->rolling_resistance * 0.62f;
            float catchup = clampf_ai(gap * 16.0f, -3.0f, 9.5f);
            /* Keep rubber-banding from completely cancelling corner planning. */
            catchup *= 1.0f - 0.55f * clampf_ai(r->corner_factor, 0.0f, 1.0f);
            desired_speed = base_speed *
                (r->difficulty_scale > 0.0f ? r->difficulty_scale : 1.0f)
                - corner_penalty - surface_drag + catchup;
        }
        desired_speed = clampf_ai(desired_speed + 1.15f*draft_strength, 12.0f, r->max_speed);
        /* Rivals fire short boost bursts on straights, then must cool and recharge. */
        if (r->boost_timer > 0.0f) {
            r->boost_timer = (r->boost_timer > dt) ? r->boost_timer-dt : 0.0f;
            r->boost_active = r->boost_timer > 0.0f;
            if (!r->boost_active) r->boost_cooldown = 1.45f;
        } else if (r->boost_cooldown > 0.0f) {
            r->boost_cooldown = (r->boost_cooldown > dt) ? r->boost_cooldown-dt : 0.0f;
        }
        if (!r->boost_active && r->boost_cooldown <= 0.0f &&
            r->corner_factor < 0.085f && r->boost_energy > (r->aggression > 1.15f ? 18.0f : 24.0f) &&
            r->boost_heat < (r->aggression > 1.15f ? 82.0f : 74.0f) &&
            (gap > 0.025f || r->aggression > 1.12f || i == 2U || i == 5U)) {
            r->boost_timer = 0.72f + 0.10f*(float)i;
            r->boost_active = 1;
        }
        if (r->boost_active) {
            r->boost_energy -= 28.0f*dt;
            r->boost_heat += 31.0f*dt;
            if (r->boost_energy <= 0.0f || r->boost_heat >= 100.0f) {
                r->boost_energy = clampf_ai(r->boost_energy,0.0f,100.0f);
                r->boost_heat = clampf_ai(r->boost_heat,0.0f,100.0f);
                r->boost_timer = 0.0f;
                r->boost_active = 0;
                r->boost_cooldown = 1.8f;
            }
        } else {
            r->boost_energy = clampf_ai(r->boost_energy+(3.5f + 5.0f*draft_strength)*dt,0.0f,100.0f);
            r->boost_heat = clampf_ai(r->boost_heat-21.0f*dt,0.0f,100.0f);
        }
        /* Give rival boost a real over-speed window, matching the player's
           handling model. Previously the final clamp used max_speed in both
           cases, so boost could help acceleration but could never raise the
           rival's actual speed ceiling. When boost ends, the target cap returns
           to normal and move_toward bleeds the excess speed away smoothly. */
        {
            float speed_ceiling = r->max_speed * (r->boost_active ? 1.12f : 1.0f);
            desired_speed = clampf_ai(desired_speed +
                                     (r->boost_active ? r->boost_power : 0.0f),
                                     12.0f, speed_ceiling);
        }
        {
            float step;
            if (desired_speed < r->speed) {
                /* Braking response becomes stronger as the bend approaches,
                   and slightly stronger again when there is a large speed
                   gap. Acceleration on straights retains the vehicle tuning. */
                float speed_gap = clampf_ai((r->speed - desired_speed) /
                    (r->max_speed > 0.1f ? r->max_speed : 1.0f), 0.0f, 1.0f);
                float deceleration = 6.8f + 8.0f *
                    clampf_ai(r->corner_factor, 0.0f, 1.0f) + 2.0f * speed_gap;
                step = deceleration * dt;
            } else {
                step = r->acceleration *
                    (r->difficulty_scale > 0.0f ? r->difficulty_scale : 1.0f) * dt;
            }
            r->speed = move_toward(r->speed, desired_speed, step);
        }

        r->lane_timer -= dt;
        if (r->lane_timer <= 0.0f) {
            r->lane_choice = (r->lane_choice+1U+(unsigned int)i) % RIVAL_AI_LANE_COUNT;
            r->target_lane_offset = lane_targets[r->lane_choice];
            r->lane_timer = r->lane_change_interval > 0.0f ? r->lane_change_interval : (2.1f + 0.45f*(float)i);
        }
        rival_ai_set_pose(r, track, track_count, track_length);
        dx = player->x-r->x;
        dz = player->z-r->z;
        dist_sq = dx*dx+dz*dz;

        /* Avoid rival-to-rival pile-ups: pick the lane with the most room when
           another pod is close on the track. Keep the choice deterministic so
           two rivals do not oscillate randomly between lanes. */
        {
            unsigned int j;
            float best_lane = r->target_lane_offset;
            float best_score = -1.0e9f;
            int crowded = 0;
            /* Score each lane against every nearby rival, rather than letting
               the last neighbour in the loop overwrite the earlier decision.
               This matters in a dense pack: choose the lane with the best
               worst-case clearance, with a small preference for less weaving. */
            for (j = 0U; j < count; ++j) {
                float odx, odz, other_dist_sq, progress_gap;
                if (j == i) continue;
                odx = r->x-rivals[j].x;
                odz = r->z-rivals[j].z;
                other_dist_sq = odx*odx+odz*odz;
                progress_gap = r->progress-rivals[j].progress;
                if (progress_gap > 0.5f) progress_gap -= 1.0f;
                if (progress_gap < -0.5f) progress_gap += 1.0f;
                if (other_dist_sq < 11.0f*11.0f && fabsf(progress_gap) < 0.035f)
                    crowded = 1;
            }
            /* Preserve the escape lane during impact recovery. Without this lock,
               normal pack avoidance can overwrite the collision response on the
               very next frame and pull the pods back into each other. */
            if (crowded && r->impact_recovery_timer <= dt) {
                unsigned int lane_idx;
                float current_score = -1.0e9f;
                /* Score the current target too. A tiny change in neighbour
                   positions must not make the AI bounce left/right every frame.
                   Only commit to another lane when its clearance advantage is
                   meaningful; this gives passing decisions a little inertia. */
                for (lane_idx = 0U; lane_idx < RIVAL_AI_LANE_COUNT; ++lane_idx) {
                    float candidate = lane_targets[lane_idx];
                    float min_clearance = 1000.0f;
                    float score;
                    for (j = 0U; j < count; ++j) {
                        float odx, odz, other_dist_sq, progress_gap, clearance;
                        if (j == i) continue;
                        odx = r->x-rivals[j].x;
                        odz = r->z-rivals[j].z;
                        other_dist_sq = odx*odx+odz*odz;
                        progress_gap = r->progress-rivals[j].progress;
                        if (progress_gap > 0.5f) progress_gap -= 1.0f;
                        if (progress_gap < -0.5f) progress_gap += 1.0f;
                        if (other_dist_sq >= 11.0f*11.0f || fabsf(progress_gap) >= 0.035f)
                            continue;
                        clearance = fabsf(candidate-rivals[j].target_lane_offset);
                        if (clearance < min_clearance) min_clearance = clearance;
                    }
                    score = min_clearance - 0.18f*fabsf(candidate-r->lane_offset);
                    if (fabsf(candidate-r->target_lane_offset) < 0.01f)
                        current_score = score;
                    if (score > best_score) {
                        best_score = score;
                        best_lane = candidate;
                    }
                }
                if (best_score > current_score + 0.35f)
                    r->target_lane_offset = best_lane;
            }
        }

        /* If the player is alongside, choose the other lane rather than pinning them. */
        if (r->impact_recovery_timer <= dt && dist_sq < 15.0f*15.0f &&
            fabsf(r->lane_offset-player_lateral) < 2.3f) {
            r->target_lane_offset = (player_lateral >= r->lane_offset) ? -lane_limit : lane_limit;
        }

        /* Tactical overtake: if the player is just ahead on the same stretch,
           commit to the lane with the most lateral separation before reaching
           them. The distance gate avoids reacting to racers on the far side of
           a loop whose normalized progress happens to be close. */
        {
            float local_gap = player_total_progress -
                ((float)r->lap - 1.0f + r->progress);
            if (local_gap < -0.5f) local_gap += 1.0f;
            if (local_gap > 0.5f) local_gap -= 1.0f;
            if (r->impact_recovery_timer <= dt && local_gap > 0.0f &&
                local_gap * track_length < (27.0f + r->aggression*5.0f) &&
                fabsf(r->lane_offset-player_lateral) < 2.5f) {
                unsigned int lane_idx;
                float best_lane = lane_targets[0];
                float best_score = -1.0e9f;
                /* Pick a passing lane using both the player and the nearby pack.
                   The old player-only choice could send every rival into the same
                   empty-looking lane, creating a second collision immediately. */
                for (lane_idx = 0U; lane_idx < RIVAL_AI_LANE_COUNT; ++lane_idx) {
                    float candidate = lane_targets[lane_idx];
                    float score = fabsf(candidate-player_lateral) * 1.25f;
                    float nearest_clearance = lane_limit * 2.0f;
                    unsigned int j;
                    for (j = 0U; j < count; ++j) {
                        float other_gap, world_dx, world_dz, world_dist_sq;
                        float clearance;
                        if (j == i) continue;
                        other_gap = ((float)rivals[j].lap + rivals[j].progress) -
                                    ((float)r->lap + r->progress);
                        other_gap *= track_length;
                        world_dx = rivals[j].x-r->x;
                        world_dz = rivals[j].z-r->z;
                        world_dist_sq = world_dx*world_dx+world_dz*world_dz;
                        /* Only nearby racers on the same local stretch count; this
                           avoids treating the far side of a hairpin as an obstacle. */
                        if (fabsf(other_gap) > 32.0f || world_dist_sq > 42.0f*42.0f)
                            continue;
                        clearance = fabsf(candidate-rivals[j].target_lane_offset);
                        if (clearance < nearest_clearance) nearest_clearance = clearance;
                    }
                    score += nearest_clearance * 0.85f;
                    /* Prefer a modest steering commitment over needless lane snaps. */
                    score -= fabsf(candidate-r->lane_offset) * 0.12f;
                    if (fabsf(candidate-r->target_lane_offset) < 0.01f) score += 0.15f;
                    if (score > best_score) {
                        best_score = score;
                        best_lane = candidate;
                    }
                }
                r->target_lane_offset = best_lane;
            }
        }
        r->lane_offset = move_toward(r->lane_offset, r->target_lane_offset, 2.4f*dt);
        r->collision_cooldown = (r->collision_cooldown > dt) ? r->collision_cooldown-dt : 0.0f;
        r->impact_recovery_timer = (r->impact_recovery_timer > dt) ?
            r->impact_recovery_timer-dt : 0.0f;

        r->progress += r->speed*dt/track_length;
        if (r->progress >= 1.0f) {
            r->progress -= 1.0f;
            r->lap += 1U;
        }
        rival_ai_set_pose(r, track, track_count, track_length);
    }

    /* Rival-to-rival impacts: lane avoidance is anticipatory, but crowded starts
       and late overtakes can still make contact. Resolve each pair once, with a
       bounded speed/boost penalty and deterministic lateral separation. */
    for (i = 0U; i < count; ++i) {
        unsigned int j;
        for (j = i + 1U; j < count; ++j) {
            RivalAIState *a = &rivals[i];
            RivalAIState *b = &rivals[j];
            float dx = b->x - a->x;
            float dz = b->z - a->z;
            float dist_sq = dx*dx + dz*dz;
            float progress_gap = a->progress - b->progress;
            if (progress_gap > 0.5f) progress_gap -= 1.0f;
            if (progress_gap < -0.5f) progress_gap += 1.0f;
            if (dist_sq < 6.0f*6.0f && fabsf(progress_gap) < 0.025f &&
                a->collision_cooldown <= 0.0f && b->collision_cooldown <= 0.0f) {
                float side;
                float impact;
                /* Stronger lateral impulse for deeper overlap, gentler for a
                   near miss; keep the response bounded and frame-independent. */
                float severity = clampf_ai((36.0f - dist_sq) / 36.0f, 0.0f, 1.0f);
                float separation = 0.28f + severity * 0.24f;
                /* A deeper overlap costs more speed; near misses still get a
                   modest penalty, preventing a fixed, arcade-like slowdown. */
                impact = 0.82f - severity * 0.10f;
                /* Prefer separating pods according to their existing lateral
                   order. Index parity is only a deterministic tie-breaker when
                   they are effectively side-by-side; this avoids swapping their
                   escape directions during a collision in a tight pack. */
                if (a->lane_offset < b->lane_offset - 0.25f) side = 1.0f;
                else if (a->lane_offset > b->lane_offset + 0.25f) side = -1.0f;
                else side = ((i + j) & 1U) ? 1.0f : -1.0f;
                {
                    float limit_a = rival_ai_lane_limit_for_width(a->road_width > 0.0f ? a->road_width : RIVAL_DEFAULT_ROAD_WIDTH);
                    float limit_b = rival_ai_lane_limit_for_width(b->road_width > 0.0f ? b->road_width : RIVAL_DEFAULT_ROAD_WIDTH);
                    a->target_lane_offset = clampf_ai(a->lane_offset - side*1.25f, -limit_a, limit_a);
                    b->target_lane_offset = clampf_ai(b->lane_offset + side*1.25f, -limit_b, limit_b);
                /* Apply a small immediate lateral impulse as well as choosing
                   future targets. Without this, overlapping rivals can remain
                   visually interpenetrating until gradual lane steering catches up. */
                    a->lane_offset = clampf_ai(a->lane_offset - side*separation, -limit_a, limit_a);
                    b->lane_offset = clampf_ai(b->lane_offset + side*separation, -limit_b, limit_b);
                }
                rival_ai_set_pose(a, track, track_count, track_length);
                rival_ai_set_pose(b, track, track_count, track_length);
                a->speed *= impact;
                b->speed *= impact;
                /* Impact heat follows collision severity: a glancing contact is
                   less punishing than a deep overlap. */
                a->boost_heat = clampf_ai(a->boost_heat + 5.0f + severity * 8.0f,
                                          0.0f, 100.0f);
                b->boost_heat = clampf_ai(b->boost_heat + 5.0f + severity * 8.0f,
                                          0.0f, 100.0f);
                a->boost_timer = b->boost_timer = 0.0f;
                a->boost_active = b->boost_active = 0;
                a->boost_cooldown = b->boost_cooldown = 0.45f;
                a->collision_cooldown = b->collision_cooldown = 0.55f;
                /* Deep impacts need a little longer to settle than glancing contacts. */
                {
                    float recovery = 0.35f + severity * 0.30f;
                    a->impact_recovery_timer = recovery;
                    b->impact_recovery_timer = recovery;
                }
                break;
            }
        }
    }

    /* Low-speed tolerant contact resolution; only one impact is processed per frame. */
    for (i = 0; i < count; ++i) {
        RivalAIState *r = &rivals[i];
        float dx = player->x-r->x;
        float dz = player->z-r->z;
        float dist_sq = dx*dx+dz*dz;
        if (dist_sq < RIVAL_COLLISION_RADIUS*RIVAL_COLLISION_RADIUS) {
            float dist = sqrtf(dist_sq);
            float nx, nz, push;
            /* Reuse contact depth as a bounded impact-severity signal. A scrape
               near the edge of the collision radius should heat the boost less
               than a head-on overlap; the response remains deterministic. */
            float impact_severity = clampf_ai(
                (RIVAL_COLLISION_RADIUS - dist) / RIVAL_COLLISION_RADIUS,
                0.0f, 1.0f);
            if (dist < 1.0e-4f) {
                nx = cosf(player->heading);
                nz = -sinf(player->heading);
                dist = 0.0f;
            } else {
                nx = dx/dist;
                nz = dz/dist;
            }
            /* Separate overlapping pods every frame, but apply damage/heat only
               once per contact burst, even if a second rival is also touching. */
            push = RIVAL_COLLISION_RADIUS-dist+0.25f;
            player->x += nx*push;
            player->z += nz*push;
            r->collision_cooldown = 0.85f;
            if (player->collision_cooldown <= 0.0f) {
                racer_apply_impact(player, player_vehicle, 10.0f, 0.78f);
                /* Deep impacts add up to 21 heat; glancing contacts start at 7. */
                player->boost_heat = clampf_ai(
                    player->boost_heat + 7.0f + impact_severity * 14.0f,
                    0.0f, 100.0f);
                if (player->boost_heat >= 100.0f) player->overheated = 1;
                player->collision_cooldown = 0.65f;
                player->heading += (nx*cosf(player->heading)+nz*sinf(player->heading) >= 0.0f) ? 0.045f : -0.045f;
                collision = 1;
            }
            player->track_distance = sqrtf(racer_project_to_track(player->x, player->z, track, track_count).distance_sq);
            player->offroad = player->track_distance > 6.8f ? 1 : 0;
            player->offroad_severity = clampf_ai((player->track_distance - 5.5f) / 8.5f, 0.0f, 1.0f);
            break;
        }
    }
    return collision;
}
