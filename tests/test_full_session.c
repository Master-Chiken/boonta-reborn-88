#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "track_catalog.h"
#include "vehicle_catalog.h"
#include "racer_physics.h"
#include "rival_ai.h"
#include "race_items.h"
#include "race_flow.h"
#include "championship.h"

static float track_length_of(const RacerTrackPoint *track, unsigned int count)
{
    unsigned int i;
    float length = 0.0f;
    for (i = 0; i < count; ++i) {
        unsigned int next = (i + 1U) % count;
        float dx = track[next].x - track[i].x;
        float dz = track[next].z - track[i].z;
        length += sqrtf(dx * dx + dz * dz);
    }
    return length;
}

static int finite_state(const RacerState *s)
{
    return isfinite(s->x) && isfinite(s->y) && isfinite(s->z) &&
           isfinite(s->heading) && isfinite(s->speed) &&
           isfinite(s->track_progress) && isfinite(s->track_distance) &&
           isfinite(s->boost_energy) && isfinite(s->damage);
}

int main(void)
{
    unsigned int track_id, vehicle_id, round;
    Championship championship;
    championship_init(&championship, TRACK_CATALOG_COUNT);

    /* Integration smoke test: every track builds geometry and runs all gameplay modules. */
    for (track_id = 0U; track_id < track_catalog_count(); ++track_id) {
        RacerTrackPoint points[TRACK_POINT_CAPACITY];
        TrackVertex mesh[TRACK_VERTEX_CAPACITY];
        unsigned int point_count = 0U, mesh_count = 0U, frame;
        RacerState player;
        RivalAIState rivals[3];
        RaceItem items[RACE_ITEM_COUNT];
        RaceFlow flow;
        const RacerTrackInfo *surface = track_catalog_get(track_id);
        float length;
        RacerInput input = {0.12f, 1.0f, 0.0f, 0.25f, 0.0f};

        assert(surface != NULL && surface->name != NULL && surface->planet != NULL);
        assert(track_catalog_build_points(track_id, points, TRACK_POINT_CAPACITY, &point_count));
        assert(point_count >= 32U && point_count <= TRACK_POINT_CAPACITY);
        assert(track_catalog_build_mesh(track_id, points, point_count, mesh,
                                        TRACK_VERTEX_CAPACITY, &mesh_count));
        assert(mesh_count > 0U && mesh_count <= TRACK_VERTEX_CAPACITY);
        length = track_length_of(points, point_count);
        assert(isfinite(length) && length > 100.0f);

        vehicle_id = track_id % vehicle_catalog_count();
        racer_init(&player, points, point_count);
        for (frame = 0U; frame < 180U; ++frame) {
            const RacerVehicleSpec *spec = vehicle_catalog_get(vehicle_id);
            racer_update_vehicle_surface(&player, points, point_count, &input,
                                         spec, surface->surface_grip,
                                         surface->rolling_resistance, 1.0f / 60.0f);
            assert(finite_state(&player));
        }
        rival_ai_init(rivals, 3U, points, point_count, length);
        for (frame = 0U; frame < 3U; ++frame)
            rival_ai_set_vehicle_spec(&rivals[frame],
                vehicle_catalog_get((vehicle_id + frame + 1U) % vehicle_catalog_count()));
        race_items_init(items, RACE_ITEM_COUNT, track_id);
        for (frame = 0U; frame < 120U; ++frame) {
            (void)rival_ai_update(rivals, 3U, points, point_count, length,
                                  &player, vehicle_catalog_get(vehicle_id), 1.0f / 60.0f);
            (void)race_items_update(items, RACE_ITEM_COUNT, &player, points,
                                    point_count, vehicle_catalog_get(vehicle_id));
            assert(finite_state(&player));
        }
        race_flow_init(&flow, 3U);
        for (frame = 0U; frame < 240U; ++frame) race_flow_update(&flow, 1.0f / 60.0f, 1U);
        assert(flow.phase == RACE_PHASE_RUNNING);
    }

    /* A full 25-round season must accept every valid finish exactly once. */
    for (round = 0U; round < TRACK_CATALOG_COUNT; ++round) {
        unsigned int places[CHAMPIONSHIP_MAX_RACERS];
        unsigned int i;
        for (i = 0U; i < CHAMPIONSHIP_MAX_RACERS; ++i)
            places[i] = ((i + round) % CHAMPIONSHIP_MAX_RACERS) + 1U;
        assert(championship_record_race(&championship, round, places));
        assert(!championship_record_race(&championship, round, places));
    }
    assert(championship.rounds_completed == TRACK_CATALOG_COUNT);
    assert(championship.rounds_total == TRACK_CATALOG_COUNT);
    {
        unsigned int order[CHAMPIONSHIP_MAX_RACERS];
        championship_standings(&championship, order);
        for (vehicle_id = 0U; vehicle_id < CHAMPIONSHIP_MAX_RACERS; ++vehicle_id)
            assert(order[vehicle_id] < CHAMPIONSHIP_MAX_RACERS);
    }
    printf("PASS: full-session integration across %u tracks, %u pods and a %u-round championship.\n",
           track_catalog_count(), vehicle_catalog_count(), championship.rounds_completed);
    return 0;
}
