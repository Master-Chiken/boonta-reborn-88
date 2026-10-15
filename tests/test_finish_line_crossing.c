#include "racer_physics.h"
#include <math.h>
#include <stdio.h>

#define CHECK(expr) do { if (!(expr)) { \
    fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #expr); return 1; \
} } while (0)

int main(void)
{
    /* First segment runs along +X. The finish plane is perpendicular to it
       through route point zero, and the legal road spans twelve world units. */
    const RacerTrackPoint route[4] = {
        {-10.0f, 0.0f, -10.0f}, {10.0f, 0.0f, -10.0f},
        {10.0f, 0.0f, 10.0f}, {-10.0f, 0.0f, 10.0f}
    };
    CHECK(racer_crossed_finish_line(-10.25f, -10.0f, -9.75f, -10.0f,
                                    route, 4U, 12.0f) == 1);
    CHECK(racer_crossed_finish_line(-9.75f, -10.0f, -10.25f, -10.0f,
                                    route, 4U, 12.0f) == 0);
    CHECK(racer_crossed_finish_line(-10.25f, -18.0f, -9.75f, -18.0f,
                                    route, 4U, 12.0f) == 0);
    /* Being exactly on the start plane and moving forward must not count. */
    CHECK(racer_crossed_finish_line(-10.0f, -10.0f, -9.5f, -10.0f,
                                    route, 4U, 12.0f) == 0);
    CHECK(racer_crossed_finish_line(-10.25f, -10.0f, -9.75f, -10.0f,
                                    route, 4U, 0.0f) == 0);
    CHECK(racer_crossed_finish_line(NAN, -10.0f, -9.75f, -10.0f,
                                    route, 4U, 12.0f) == 0);
    /* A teleport spanning the finish plane cannot register a lap. */
    CHECK(racer_crossed_finish_line(-100.0f, -10.0f, 100.0f, -10.0f,
                                    route, 4U, 12.0f) == 0);
    /* A high-speed but plausible physical step remains valid. */
    CHECK(racer_crossed_finish_line(-12.0f, -10.0f, -8.0f, -10.0f,
                                    route, 4U, 12.0f) == 1);

    /* Intermediate gates follow route arc length and only accept a forward,
       on-road physical crossing. */
    {
        RacerCheckpointGate gate;
        CHECK(racer_checkpoint_gate_at_progress(route, 4U, 0.25f, &gate) == 1);
        CHECK(gate.valid == 1);
        CHECK(fabsf(gate.x - 10.0f) < 0.001f);
        CHECK(fabsf(gate.z + 10.0f) < 0.001f);
        CHECK(racer_crossed_checkpoint_gate(9.75f, -10.0f, 10.25f, -10.0f,
                                            &gate, 12.0f) == 1);
        CHECK(racer_crossed_checkpoint_gate(10.25f, -10.0f, 9.75f, -10.0f,
                                            &gate, 12.0f) == 0);
        CHECK(racer_crossed_checkpoint_gate(9.75f, -18.0f, 10.25f, -18.0f,
                                            &gate, 12.0f) == 0);
        /* A large positional discontinuity must not skip a physical gate. */
        CHECK(racer_crossed_checkpoint_gate(-100.0f, -10.0f, 100.0f, -10.0f,
                                            &gate, 12.0f) == 0);
        CHECK(racer_checkpoint_gate_at_progress(route, 4U, NAN, &gate) == 0);
        CHECK(gate.valid == 0);
    }
    puts("PASS: finish line and intermediate checkpoint gates require forward, on-road, plausible crossings");
    return 0;
}
