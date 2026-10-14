#include "race_gate_geometry.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>

static void assert_close(float a, float b, float eps)
{
    assert(fabsf(a - b) <= eps);
}

static void check_width(float width)
{
    RaceGateGeometry gate;
    unsigned int i;
    assert(race_gate_geometry_build(width, &gate));
    assert_close(gate.road_width, width, 0.0001f);
    assert(gate.post_offset > gate.road_width * 0.5f);
    assert(gate.crossbar_half_width > gate.post_offset);
    assert(gate.stripe_half_width > 0.0f);
    for (i = 0U; i < RACE_GATE_STRIPE_COUNT; ++i) {
        float abs_center = fabsf(gate.stripe_centers[i]);
        assert(abs_center + gate.stripe_half_width <= gate.road_width * 0.5f + 0.001f);
        if (i > 0U) {
            assert(gate.stripe_centers[i] > gate.stripe_centers[i - 1U]);
            assert_close(gate.stripe_centers[i] + gate.stripe_centers[RACE_GATE_STRIPE_COUNT - 1U - i],
                         0.0f, 0.0001f);
        }
    }
}

int main(void)
{
    RaceGateGeometry gate;
    check_width(9.8f);   /* Boonta Training */
    check_width(12.5f);  /* Boonta Classic */
    check_width(13.0f);  /* wider speedway */
    assert(race_gate_geometry_build(2.0f, &gate));
    assert_close(gate.road_width, 8.0f, 0.0001f);
    assert(race_gate_geometry_build(25.0f, &gate));
    assert_close(gate.road_width, 20.0f, 0.0001f);
    assert(race_gate_geometry_build(NAN, &gate));
    assert_close(gate.road_width, 12.0f, 0.0001f);
    assert(race_gate_geometry_build(INFINITY, &gate));
    assert_close(gate.road_width, 12.0f, 0.0001f);
    assert(!race_gate_geometry_build(12.0f, 0));
    puts("PASS: race gate geometry follows road width with safe bounded inputs.");
    return 0;
}
