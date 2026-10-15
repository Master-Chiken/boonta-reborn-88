#include "rival_ai.h"
#include "vehicle_catalog.h"
#include <math.h>
#include <stdio.h>
#include <string.h>

#define CHECK(expr) do { if (!(expr)) { \
    fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #expr); return 1; \
} } while (0)

static void make_circle(RacerTrackPoint *points, unsigned int count)
{
    unsigned int i;
    const float pi = 3.14159265358979323846f;
    for (i = 0; i < count; ++i) {
        float a = (2.0f*pi*(float)i)/(float)count;
        points[i].x = 40.0f*cosf(a);
        points[i].y = 1.2f*sinf(a*2.0f);
        points[i].z = 40.0f*sinf(a);
    }
}

int main(void)
{
    RacerTrackPoint track[96];
    RacerState player;
    RivalAIState rivals[7];
    RacerTrackProjection p;
    float length, initial_progress, initial_speed, initial_lane;
    const RacerVehicleSpec *vehicle=vehicle_catalog_get(0U);
    unsigned int i;
    int collided;

    make_circle(track, 96U);
    p = racer_project_to_track(track[0].x, track[0].z, track, 96U);
    length = p.total_length;
    CHECK(length > 200.0f);
    racer_init(&player, track, 96U);
    rival_ai_init(rivals, 7U, track, 96U, length);
    CHECK(rivals[6].r != rivals[0].r);
    CHECK(rivals[6].progress < rivals[5].progress);
    CHECK(rivals[0].lap == 0U && rivals[1].lap == 0U && rivals[2].lap == 0U);
    CHECK(rivals[0].progress > 0.94f && rivals[0].progress < 1.0f);
    CHECK(rivals[0].r != rivals[1].r);
    CHECK(rivals[0].lane_offset != rivals[1].lane_offset);
    CHECK(rivals[1].lane_offset != rivals[2].lane_offset);
    CHECK(rivals[2].aggression > rivals[0].aggression);
    CHECK(rivals[2].lane_change_interval < rivals[0].lane_change_interval);
    CHECK(rivals[6].aggression < rivals[5].aggression);

    /* AI lane spacing and banking now follow the selected course width rather
       than using a fixed 12-unit assumption on every circuit. */
    {
        RivalAIState narrow[1], wide[1];
        float narrow_limit = rival_ai_lane_limit_for_width(9.8f);
        float standard_limit = rival_ai_lane_limit_for_width(12.0f);
        float wide_limit = rival_ai_lane_limit_for_width(13.0f);
        CHECK(narrow_limit < standard_limit);
        CHECK(standard_limit < wide_limit);
        CHECK(fabsf(standard_limit - 2.7f) < 0.001f);
        rival_ai_init(narrow, 1U, track, 96U, length);
        rival_ai_init(wide, 1U, track, 96U, length);
        rival_ai_set_track_width(narrow, 1U, 9.8f);
        rival_ai_set_track_width(wide, 1U, 13.0f);
        CHECK(fabsf(narrow[0].road_width - 9.8f) < 0.001f);
        CHECK(fabsf(wide[0].road_width - 13.0f) < 0.001f);
        CHECK(fabsf(narrow[0].lane_offset) <= narrow_limit);
        CHECK(fabsf(wide[0].lane_offset) <= wide_limit);
        narrow[0].progress = wide[0].progress = 0.25f;
        narrow[0].lane_offset = wide[0].lane_offset = 2.0f;
        rival_ai_set_pose(&narrow[0], track, 96U, length);
        rival_ai_set_pose(&wide[0], track, 96U, length);
        CHECK(fabsf(narrow[0].y - wide[0].y) > 0.0001f);
        /* Bad metadata is clamped to a safe width range. */
        rival_ai_set_track_width(narrow, 1U, 100.0f);
        CHECK(narrow[0].road_width == 20.0f);
        CHECK(fabsf(narrow[0].lane_offset) <= rival_ai_lane_limit_for_width(20.0f));
        rival_ai_set_track_width(narrow, 1U, NAN);
        CHECK(narrow[0].road_width == 12.0f);
        CHECK(fabsf(rival_ai_lane_limit_for_width(NAN) - standard_limit) < 0.001f);
    }

    /* Corner anticipation: a tight bend several segments ahead should already
       be visible to the AI's pace/boost planner on the straight approach. */
    {
        RacerTrackPoint approach[8] = {
            { 0.0f, 0.0f,  0.0f}, { 0.0f, 0.0f, 10.0f},
            { 0.0f, 0.0f, 20.0f}, { 0.0f, 0.0f, 30.0f},
            {-10.0f, 0.0f, 30.0f}, {-20.0f, 0.0f, 30.0f},
            {-20.0f, 0.0f, 20.0f}, {-20.0f, 0.0f, 10.0f}
        };
        RivalAIState approach_rival;
        float approach_length = 0.0f;
        unsigned int k;
        memset(&approach_rival, 0, sizeof(approach_rival));
        for (k = 0U; k < 8U; ++k) {
            float dx = approach[(k+1U)%8U].x - approach[k].x;
            float dz = approach[(k+1U)%8U].z - approach[k].z;
            approach_length += sqrtf(dx*dx + dz*dz);
        }
        approach_rival.progress = 4.0f / approach_length; /* segment 0, well before the bend */
        rival_ai_set_pose(&approach_rival, approach, 8U, approach_length);
        CHECK(approach_rival.corner_factor > 0.40f);
        CHECK(approach_rival.corner_factor < 1.0f);
    }

    /* A fast rival should shed more speed than a slow rival before the same
       sharp bend. This protects the new speed-sensitive corner planner from
       regressing to a fixed curve penalty or straight-line acceleration only. */
    {
        RacerTrackPoint approach[8] = {
            { 0.0f, 0.0f,  0.0f}, { 0.0f, 0.0f, 10.0f},
            { 0.0f, 0.0f, 20.0f}, { 0.0f, 0.0f, 30.0f},
            {-10.0f, 0.0f, 30.0f}, {-20.0f, 0.0f, 30.0f},
            {-20.0f, 0.0f, 20.0f}, {-20.0f, 0.0f, 10.0f}
        };
        RivalAIState fast[1], slow[1];
        RacerState far_player;
        float route_length = 0.0f;
        float fast_before, slow_before;
        unsigned int k;
        for (k = 0U; k < 8U; ++k) {
            float dx = approach[(k+1U)%8U].x - approach[k].x;
            float dz = approach[(k+1U)%8U].z - approach[k].z;
            route_length += sqrtf(dx*dx + dz*dz);
        }
        rival_ai_init(fast, 1U, approach, 8U, route_length);
        rival_ai_init(slow, 1U, approach, 8U, route_length);
        fast[0].progress = slow[0].progress = 4.0f / route_length;
        fast[0].lap = slow[0].lap = 1U;
        fast[0].speed = 35.0f;
        slow[0].speed = 20.0f;
        fast[0].boost_energy = slow[0].boost_energy = 0.0f;
        fast[0].boost_cooldown = slow[0].boost_cooldown = 100.0f;
        fast[0].lane_timer = slow[0].lane_timer = 100.0f;
        rival_ai_set_pose(&fast[0], approach, 8U, route_length);
        rival_ai_set_pose(&slow[0], approach, 8U, route_length);
        CHECK(fast[0].corner_factor > 0.40f);
        CHECK(slow[0].corner_factor > 0.40f);
        racer_init(&far_player, approach, 8U);
        far_player.x = far_player.z = 1000.0f;
        far_player.lap = 1U;
        far_player.track_progress = fast[0].progress;
        fast_before = fast[0].speed;
        slow_before = slow[0].speed;
        (void)rival_ai_update(fast, 1U, approach, 8U, route_length,
                              &far_player, vehicle, 0.05f);
        (void)rival_ai_update(slow, 1U, approach, 8U, route_length,
                              &far_player, vehicle, 0.05f);
        CHECK(fast[0].speed < fast_before);
        CHECK(slow[0].speed < slow_before);
        CHECK((fast_before-fast[0].speed) > (slow_before-slow[0].speed));
    }

    /* Lane placement and heading should stay continuous when a rival crosses
       a sharp polyline vertex. This prevents lateral jumps when the track's
       centerline changes direction between adjacent samples. */
    {
        RacerTrackPoint bend[8] = {
            { 0.0f, 0.0f,  0.0f}, { 0.0f, 0.0f, 10.0f},
            { 0.0f, 0.0f, 20.0f}, { 0.0f, 0.0f, 30.0f},
            {-10.0f, 0.0f, 30.0f}, {-20.0f, 0.0f, 30.0f},
            {-20.0f, 0.0f, 20.0f}, {-20.0f, 0.0f, 10.0f}
        };
        RivalAIState before, after;
        float route_length = 0.0f, dx, dz, heading_delta;
        unsigned int k;
        for (k = 0U; k < 8U; ++k) {
            float sx = bend[(k+1U)%8U].x-bend[k].x;
            float sz = bend[(k+1U)%8U].z-bend[k].z;
            route_length += sqrtf(sx*sx+sz*sz);
        }
        memset(&before, 0, sizeof(before));
        memset(&after, 0, sizeof(after));
        before.progress = 29.99f/route_length;
        after.progress = 30.01f/route_length;
        before.lane_offset = after.lane_offset = 2.25f;
        rival_ai_set_pose(&before, bend, 8U, route_length);
        rival_ai_set_pose(&after, bend, 8U, route_length);
        dx = before.x-after.x;
        dz = before.z-after.z;
        heading_delta = fabsf(before.heading-after.heading);
        if (heading_delta > 3.14159265358979323846f)
            heading_delta = 6.28318530717958647692f-heading_delta;
        CHECK(sqrtf(dx*dx+dz*dz) < 0.10f);
        CHECK(heading_delta < 0.05f);
    }

    initial_progress = (float)rivals[0].lap - 1.0f + rivals[0].progress;
    initial_speed = rivals[0].speed;
    initial_lane = rivals[0].lane_offset;
    for (i = 0; i < 90U; ++i)
        (void)rival_ai_update(rivals, 3U, track, 96U, length, &player, vehicle, 1.0f/60.0f);
    CHECK(((float)rivals[0].lap - 1.0f + rivals[0].progress) > initial_progress);
    CHECK(rivals[0].speed > 0.0f);
    CHECK(fabsf(rivals[0].lane_offset-initial_lane) > 0.1f ||
          fabsf(rivals[0].target_lane_offset-initial_lane) > 0.1f);
    CHECK(rivals[0].x == rivals[0].x); /* pose remains finite */
    CHECK(rivals[0].y == rivals[0].y);
    CHECK(rivals[0].z == rivals[0].z);
    CHECK(rivals[0].speed <= initial_speed + 10.0f);
    CHECK(rivals[2].boost_energy < 100.0f || rivals[2].boost_active);

    /* Rival boost must raise the actual speed ceiling, then return smoothly to
       normal pace once it ends. The old normal-only clamp made boost add force
       but never allowed speed to exceed max_speed. */
    {
        RivalAIState boosted[1];
        RacerState distant_player;
        float normal_max;
        unsigned int frame;
        rival_ai_init(boosted, 1U, track, 96U, length);
        racer_init(&distant_player, track, 96U);
        distant_player.x = distant_player.z = 1000.0f;
        distant_player.track_progress = 0.60f;
        boosted[0].progress = 0.30f;
        boosted[0].speed = boosted[0].max_speed - 0.5f;
        boosted[0].boost_timer = 5.0f;
        boosted[0].boost_active = 1;
        boosted[0].boost_energy = 100.0f;
        boosted[0].boost_heat = 10.0f;
        boosted[0].boost_cooldown = 100.0f;
        boosted[0].lane_timer = 100.0f;
        rival_ai_set_pose(&boosted[0], track, 96U, length);
        normal_max = boosted[0].max_speed;
        for (frame = 0U; frame < 30U; ++frame)
            (void)rival_ai_update(boosted, 1U, track, 96U, length,
                                  &distant_player, vehicle, 1.0f/60.0f);
        CHECK(boosted[0].speed > normal_max + 0.1f);
        CHECK(boosted[0].speed <= normal_max*1.12f + 0.02f);
        boosted[0].boost_active = 0;
        boosted[0].boost_timer = 0.0f;
        boosted[0].boost_cooldown = 100.0f;
        for (frame = 0U; frame < 90U; ++frame)
            (void)rival_ai_update(boosted, 1U, track, 96U, length,
                                  &distant_player, vehicle, 1.0f/60.0f);
        CHECK(boosted[0].speed <= normal_max + 0.02f);
    }

    /* Course conditions affect rival pace: slippery/rough tracks are slower than grippy ones. */
    {
        RivalAIState rough[1], smooth[1];
        RacerState player_rough, player_smooth;
        unsigned int frame;
        rival_ai_init(rough, 1U, track, 96U, length);
        rival_ai_init(smooth, 1U, track, 96U, length);
        rival_ai_set_track_surface(rough, 1U, 0.75f, 1.6f);
        rival_ai_set_track_surface(smooth, 1U, 1.0f, 0.4f);
        CHECK(rough[0].surface_grip < smooth[0].surface_grip);
        CHECK(rough[0].rolling_resistance > smooth[0].rolling_resistance);
        racer_init(&player_rough, track, 96U);
        racer_init(&player_smooth, track, 96U);
        player_rough.x = player_smooth.x = 1000.0f;
        player_rough.z = player_smooth.z = 1000.0f;
        for (frame = 0U; frame < 120U; ++frame) {
            (void)rival_ai_update(rough, 1U, track, 96U, length,
                                  &player_rough, vehicle, 1.0f/60.0f);
            (void)rival_ai_update(smooth, 1U, track, 96U, length,
                                  &player_smooth, vehicle, 1.0f/60.0f);
        }
        CHECK(rough[0].speed < smooth[0].speed);
        /* Out-of-range surface values are safely clamped. */
        rival_ai_set_track_surface(rough, 1U, 9.0f, -4.0f);
        CHECK(rough[0].surface_grip == 1.20f);
        CHECK(rough[0].rolling_resistance == 0.0f);
    }

    /* A rival drafting behind another pod recovers more boost energy than a lone pod. */
    {
        RivalAIState drafting[2], lone[1];
        RacerState drafting_player, lone_player;
        unsigned int frame;
        rival_ai_init(drafting, 2U, track, 96U, length);
        rival_ai_init(lone, 1U, track, 96U, length);
        drafting[0].progress = 0.20f;
        drafting[1].progress = 0.20f + 10.0f/length;
        drafting[0].lane_offset = drafting[1].lane_offset = 0.0f;
        drafting[0].target_lane_offset = drafting[1].target_lane_offset = 0.0f;
        drafting[0].lane_timer = drafting[1].lane_timer = 100.0f;
        drafting[0].boost_energy = lone[0].boost_energy = 50.0f;
        lone[0].progress = drafting[0].progress;
        lone[0].lane_offset = lone[0].target_lane_offset = 0.0f;
        lone[0].lane_timer = 100.0f;
        racer_init(&drafting_player, track, 96U);
        racer_init(&lone_player, track, 96U);
        drafting_player.x = lone_player.x = 1000.0f;
        drafting_player.z = lone_player.z = 1000.0f;
        for (frame = 0U; frame < 45U; ++frame) {
            (void)rival_ai_update(drafting, 2U, track, 96U, length,
                                  &drafting_player, vehicle, 1.0f/60.0f);
            (void)rival_ai_update(lone, 1U, track, 96U, length,
                                  &lone_player, vehicle, 1.0f/60.0f);
        }
        CHECK(drafting[0].boost_energy > lone[0].boost_energy);
    }

    /* Progress-close rivals on a different world-space line must not grant
       a fake draft; this matters on switchbacks and hairpin exits. */
    {
        RivalAIState misaligned[2], baseline[1];
        RacerState misaligned_player, baseline_player;
        rival_ai_init(misaligned, 2U, track, 96U, length);
        rival_ai_init(baseline, 1U, track, 96U, length);
        misaligned[0].progress = baseline[0].progress = 0.20f;
        misaligned[1].progress = 0.20f + 10.0f/length;
        misaligned[0].lane_offset = misaligned[1].lane_offset = 0.0f;
        misaligned[0].target_lane_offset = misaligned[1].target_lane_offset = 0.0f;
        misaligned[0].lane_timer = misaligned[1].lane_timer = 100.0f;
        misaligned[0].boost_energy = baseline[0].boost_energy = 50.0f;
        misaligned[0].boost_cooldown = baseline[0].boost_cooldown = 10.0f;
        /* Force the nominally-ahead pod far to the side for the draft check. */
        misaligned[1].x += 12.0f;
        racer_init(&misaligned_player, track, 96U);
        racer_init(&baseline_player, track, 96U);
        misaligned_player.x = baseline_player.x = 1000.0f;
        misaligned_player.z = baseline_player.z = 1000.0f;
        (void)rival_ai_update(misaligned, 2U, track, 96U, length,
                              &misaligned_player, vehicle, 1.0f/60.0f);
        (void)rival_ai_update(baseline, 1U, track, 96U, length,
                              &baseline_player, vehicle, 1.0f/60.0f);
        CHECK(fabsf(misaligned[0].boost_energy - baseline[0].boost_energy) < 0.001f);
    }

    /* A rival one lap behind must not provide a slipstream just because its
       normalized progress happens to be 10 m ahead on the circular coordinate. */
    {
        RivalAIState lapped[2], baseline[1];
        RacerState lapped_player, baseline_player;
        unsigned int frame;
        rival_ai_init(lapped, 2U, track, 96U, length);
        rival_ai_init(baseline, 1U, track, 96U, length);
        lapped[0].progress = 0.30f;
        lapped[0].lap = 2U;
        lapped[1].progress = 0.30f + 10.0f/length;
        lapped[1].lap = 1U;
        lapped[0].lane_offset = lapped[1].lane_offset = 0.0f;
        lapped[0].target_lane_offset = lapped[1].target_lane_offset = 0.0f;
        lapped[0].lane_timer = lapped[1].lane_timer = 100.0f;
        lapped[0].boost_active = lapped[1].boost_active = 0;
        lapped[0].boost_cooldown = lapped[1].boost_cooldown = 100.0f;
        baseline[0].progress = lapped[0].progress;
        baseline[0].lap = lapped[0].lap;
        baseline[0].lane_offset = baseline[0].target_lane_offset = 0.0f;
        baseline[0].lane_timer = 100.0f;
        baseline[0].boost_active = 0;
        baseline[0].boost_cooldown = 100.0f;
        racer_init(&lapped_player, track, 96U);
        racer_init(&baseline_player, track, 96U);
        lapped_player.x = baseline_player.x = 1000.0f;
        lapped_player.z = baseline_player.z = 1000.0f;
        for (frame = 0U; frame < 45U; ++frame) {
            (void)rival_ai_update(lapped, 2U, track, 96U, length,
                                  &lapped_player, vehicle, 1.0f/60.0f);
            (void)rival_ai_update(baseline, 1U, track, 96U, length,
                                  &baseline_player, vehicle, 1.0f/60.0f);
        }
        CHECK(lapped[0].boost_energy <= baseline[0].boost_energy + 0.001f);
    }

    /* Rival-to-rival contact penalizes both pods and opens a deterministic lane. */
    {
        RivalAIState pack[2];
        RacerState remote_player;
        float before_a, before_b;
        float before_lane_gap;
        racer_init(&remote_player, track, 96U);
        remote_player.x = 1000.0f;
        remote_player.z = 1000.0f;
        rival_ai_init(pack, 2U, track, 96U, length);
        pack[0].progress = 0.22f;
        pack[1].progress = 0.22f;
        pack[0].lane_offset = pack[1].lane_offset = 0.0f;
        pack[0].target_lane_offset = pack[1].target_lane_offset = 0.0f;
        pack[0].lane_timer = pack[1].lane_timer = 100.0f;
        pack[0].collision_cooldown = pack[1].collision_cooldown = 0.0f;
        pack[0].boost_timer = pack[1].boost_timer = 0.8f;
        pack[0].boost_active = pack[1].boost_active = 1;
        pack[0].boost_heat = pack[1].boost_heat = 10.0f;
        rival_ai_set_pose(&pack[0], track, 96U, length);
        rival_ai_set_pose(&pack[1], track, 96U, length);
        before_a = pack[0].speed;
        before_b = pack[1].speed;
        before_lane_gap = fabsf(pack[0].lane_offset-pack[1].lane_offset);
        (void)rival_ai_update(pack, 2U, track, 96U, length, &remote_player, vehicle, 1.0f/120.0f);
        CHECK(pack[0].collision_cooldown > 0.0f);
        CHECK(pack[1].collision_cooldown > 0.0f);
        CHECK(pack[0].boost_active == 0 && pack[1].boost_active == 0);
        CHECK(pack[0].boost_heat >= 10.0f && pack[1].boost_heat >= 10.0f);
        CHECK(fabsf(pack[0].target_lane_offset-pack[1].target_lane_offset) > 0.5f);
        CHECK(fabsf(pack[0].lane_offset-pack[1].lane_offset) > before_lane_gap + 0.5f);
        CHECK(pack[0].speed <= before_a + 1.0f && pack[1].speed <= before_b + 1.0f);
        /* During the impact cooldown, ordinary pack avoidance must not erase
           the escape lane chosen by the collision response on the next frame. */
        {
            float recovery_target_a = pack[0].target_lane_offset;
            float recovery_target_b = pack[1].target_lane_offset;
            (void)rival_ai_update(pack, 2U, track, 96U, length,
                                  &remote_player, vehicle, 1.0f/120.0f);
            CHECK(pack[0].collision_cooldown > 0.0f && pack[1].collision_cooldown > 0.0f);
            CHECK(pack[0].impact_recovery_timer > 0.0f && pack[1].impact_recovery_timer > 0.0f);
            CHECK(pack[0].target_lane_offset == recovery_target_a);
            CHECK(pack[1].target_lane_offset == recovery_target_b);
        }
    }

    /* Dense-pack avoidance evaluates the whole pack and avoids assigning every
       pod the same escape lane when three rivals begin overlapped. */
    {
        RivalAIState pack[3];
        RacerState remote_player;
        unsigned int frame;
        int distinct = 0;
        racer_init(&remote_player, track, 96U);
        remote_player.x = 1000.0f;
        remote_player.z = 1000.0f;
        rival_ai_init(pack, 3U, track, 96U, length);
        for (i = 0U; i < 3U; ++i) {
            pack[i].progress = 0.34f;
            pack[i].lane_offset = 0.0f;
            pack[i].target_lane_offset = 0.0f;
            pack[i].lane_timer = 100.0f;
            pack[i].collision_cooldown = 1.0f; /* isolate lane choice from impact response */
            rival_ai_set_pose(&pack[i], track, 96U, length);
        }
        for (frame = 0U; frame < 3U; ++frame)
            (void)rival_ai_update(pack, 3U, track, 96U, length,
                                  &remote_player, vehicle, 1.0f/60.0f);
        for (i = 0U; i < 3U; ++i) {
            CHECK(pack[i].target_lane_offset == pack[i].target_lane_offset);
            CHECK(fabsf(pack[i].target_lane_offset) <= 2.7f);
        }
        if (fabsf(pack[0].target_lane_offset-pack[1].target_lane_offset) > 0.1f) distinct++;
        if (fabsf(pack[0].target_lane_offset-pack[2].target_lane_offset) > 0.1f) distinct++;
        if (fabsf(pack[1].target_lane_offset-pack[2].target_lane_offset) > 0.1f) distinct++;
        CHECK(distinct >= 2);
    }

    /* Contact with a rival nudges the pod away, reduces speed and heats the boost. */
    racer_init(&player, track, 96U);
    player.speed = 30.0f;
    player.boost_heat = 12.0f;
    rivals[0].progress = player.track_progress;
    rivals[0].lane_offset = 0.0f;
    rivals[0].target_lane_offset = 0.0f;
    rivals[0].lane_timer = 100.0f;
    rivals[0].speed = 0.0f;
    rivals[0].collision_cooldown = 0.0f;
    rival_ai_set_pose(&rivals[0], track, 96U, length);
    player.x = rivals[0].x;
    player.y = rivals[0].y;
    player.z = rivals[0].z;
    player.track_progress = rivals[0].progress;
    collided = rival_ai_update(rivals, 1U, track, 96U, length, &player, vehicle, 1.0f/60.0f);
    CHECK(collided == 1);
    CHECK(player.speed < 30.0f);
    CHECK(player.boost_heat >= 18.9f); /* contact heat now varies with overlap depth */
    CHECK(player.damage > 0.0f);
    CHECK(rivals[0].collision_cooldown > 0.0f);

    /* Re-overlap on purpose: the cooldown should suppress an immediate second hit. */
    player.x = rivals[0].x;
    player.z = rivals[0].z;
    player.speed = 20.0f;
    {
        float damage_after_first_hit = player.damage;
        float heat_after_first_hit = player.boost_heat;
        collided = rival_ai_update(rivals, 1U, track, 96U, length, &player, vehicle, 1.0f/60.0f);
        CHECK(collided == 0);
        CHECK(player.damage == damage_after_first_hit);
        CHECK(player.boost_heat <= heat_after_first_hit);
    }
    CHECK(player.collision_cooldown > 0.0f);
    CHECK(rivals[0].collision_cooldown > 0.0f);

    /* Two rivals occupying the same racing line should trigger a passing lane. */
    racer_init(&player, track, 96U);
    player.track_progress = 0.12f;
    player.x = track[12].x;
    player.z = track[12].z;
    rivals[0].progress = 0.48f;
    rivals[1].progress = 0.48f;
    rivals[0].lane_offset = rivals[1].lane_offset = 0.0f;
    rivals[0].target_lane_offset = rivals[1].target_lane_offset = 0.0f;
    rivals[0].lane_timer = rivals[1].lane_timer = 100.0f;
    rivals[0].collision_cooldown = rivals[1].collision_cooldown = 1.0f;
    rival_ai_set_pose(&rivals[0], track, 96U, length);
    rival_ai_set_pose(&rivals[1], track, 96U, length);
    (void)rival_ai_update(rivals, 2U, track, 96U, length, &player, vehicle, 1.0f/60.0f);
    CHECK(fabsf(rivals[0].target_lane_offset) > 1.0f ||
          fabsf(rivals[1].target_lane_offset) > 1.0f);

    /* A rival commits to an overtaking lane when the player is just ahead,
       even before the pods are close enough for contact avoidance. */
    {
        RivalAIState passer[1];
        RacerState target;
        unsigned int seg;
        const float target_progress = 0.30f;
        racer_init(&target, track, 96U);
        rival_ai_init(passer, 1U, track, 96U, length);
        passer[0].progress = target_progress - 20.0f/length;
        passer[0].lap = 1U;
        passer[0].lane_offset = 0.0f;
        passer[0].target_lane_offset = 0.0f;
        passer[0].lane_timer = 100.0f;
        rival_ai_set_pose(&passer[0], track, 96U, length);
        seg = (unsigned int)(target_progress * 96.0f) % 96U;
        target.x = track[seg].x;
        target.y = track[seg].y;
        target.z = track[seg].z;
        target.track_progress = target_progress;
        target.lap = 1U;
        (void)rival_ai_update(passer, 1U, track, 96U, length, &target, vehicle, 1.0f/60.0f);
        CHECK(fabsf(passer[0].target_lane_offset) > 1.0f);
    }

    /* Each rival's selected pod must affect its actual AI tuning, not just its mesh. */
    {
        RivalAIState fast_pod, agile_pod;
        memset(&fast_pod, 0, sizeof(fast_pod));
        memset(&agile_pod, 0, sizeof(agile_pod));
        rival_ai_set_vehicle_spec(&fast_pod, vehicle_catalog_get(22U));
        rival_ai_set_vehicle_spec(&agile_pod, vehicle_catalog_get(15U));
        CHECK(fast_pod.max_speed > agile_pod.max_speed);
        CHECK(agile_pod.grip > fast_pod.grip);
        CHECK(fast_pod.acceleration > 0.0f && agile_pod.acceleration > 0.0f);
        CHECK(fast_pod.boost_power > 0.0f && agile_pod.boost_power > 0.0f);
    }

    puts("PASS: rival progression, width-aware lanes/banking, lane changes, boost, contact response and rival-to-rival passing avoidance");
    return 0;
}
