#include "racer_physics.h"
#include <math.h>
#include <stdio.h>
#include <string.h>

#define CHECK(expr) do { if (!(expr)) { \
    fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #expr); return 1; \
} } while (0)

int main(void)
{
    /* A closed square centerline; the first segment travels along +X. */
    RacerTrackPoint route[4] = {
        {-10.0f, 0.0f, -10.0f}, {10.0f, 0.0f, -10.0f},
        {10.0f, 0.0f, 10.0f}, {-10.0f, 0.0f, 10.0f}
    };
    RacerTrackProjection p;
    RacerState state;
    RacerInput input;
    float z_before;
    unsigned int i;
    int saw_offroad = 0;

    p = racer_project_to_track(0.0f, -12.0f, route, 4U);
    CHECK(p.segment == 0U);
    CHECK(fabsf(p.lateral_offset - 2.0f) < 0.001f);
    CHECK(fabsf(racer_track_lateral_offset(0.0f, -12.0f, route, 4U) - 2.0f) < 0.001f);

    p = racer_project_to_track(0.0f, -8.0f, route, 4U);
    CHECK(p.segment == 0U);
    CHECK(fabsf(p.lateral_offset + 2.0f) < 0.001f);
    CHECK(fabsf(racer_track_lateral_offset(0.0f, -8.0f, route, 4U) + 2.0f) < 0.001f);

    memset(&state, 0, sizeof(state));
    memset(&input, 0, sizeof(input));
    state.x = 0.0f;
    state.y = 1.0f;
    state.z = -17.0f; /* 7 units outside the route centerline. */
    state.heading = 0.0f;
    state.lap = 1U;
    z_before = state.z;

    /* Low-speed edge handling should nudge the racer back from the shoulder,
       not teleport the pod to the centerline. */
    for (i = 0U; i < 5U; ++i) {
        racer_update_vehicle_surface_width(&state, route, 4U, &input, NULL,
                                           1.0f, 0.0f, 12.0f, 0.05f);
        if (state.offroad) saw_offroad = 1;
    }
    CHECK(state.z > z_before + 0.1f);
    CHECK(state.z < -10.0f + 2.0f);
    CHECK(saw_offroad == 1);
    CHECK(state.track_lateral_offset > 0.0f);
    CHECK(state.offroad_severity > 0.0f);

    puts("PASS: signed lateral offset and gradual shoulder recovery");
    return 0;
}
