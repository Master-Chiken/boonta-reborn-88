#include "racer_physics.h"
#include <math.h>
#include <stdio.h>

#define CHECK(expr) do { if (!(expr)) { \
    fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #expr); return 1; \
} } while (0)

int main(void)
{
    /* A compact bow-tie route crosses at the origin. Segments 0 and 4 are
       equally close there, but represent very different race progress. */
    RacerTrackPoint route[8] = {
        {-2,0,-2}, {2,0,2}, {4,0,4}, {4,0,7},
        {-2,0,2}, {2,0,-2}, {4,0,-4}, {-4,0,-4}
    };
    RacerTrackProjection global, near_crossing, nearby_point, invalid;
    unsigned int i;

    global = racer_project_to_track(0.0f, 0.0f, route, 8U);
    near_crossing = racer_project_to_track_near(0.0f, 0.0f, route, 8U, 4U);
    CHECK(global.distance_sq < 0.001f);
    CHECK(near_crossing.distance_sq < 0.001f);
    CHECK(global.segment == 0U);
    CHECK(near_crossing.segment == 4U);
    CHECK(fabsf(global.progress - near_crossing.progress) > 0.25f);

    nearby_point = racer_project_to_track_near(0.0f, 0.1f, route, 8U, 4U);
    CHECK(nearby_point.segment == 4U);
    CHECK(nearby_point.distance_sq < 0.02f);
    CHECK(nearby_point.total_length > 0.0f);
    CHECK(nearby_point.progress >= 0.0f && nearby_point.progress < 1.0f);

    /* The continuity hint must yield to a clearly nearer segment after a
       genuine excursion, rather than locking the racer to old progress. */
    nearby_point = racer_project_to_track_near(2.0f, 2.0f, route, 8U, 4U);
    CHECK(nearby_point.segment == 0U);
    CHECK(nearby_point.distance_sq < 0.001f);

    invalid = racer_project_to_track_near(NAN, 0.0f, route, 8U, 4U);
    CHECK(invalid.distance_sq > 1.0e30f);
    route[3].y = INFINITY;
    invalid = racer_project_to_track(0.0f, 0.0f, route, 8U);
    CHECK(invalid.distance_sq > 1.0e30f);

    for (i = 0U; i < 8U; ++i) {
        route[i].x = 5.0f; route[i].y = 0.0f; route[i].z = 5.0f;
    }
    invalid = racer_project_to_track(5.0f, 5.0f, route, 8U);
    CHECK(invalid.distance_sq > 1.0e30f);

    puts("PASS: track projection keeps continuity across a crossing and rejects invalid geometry");
    return 0;
}
