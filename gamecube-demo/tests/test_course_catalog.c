#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "../source/course_catalog.h"

static void test_single_vertical_slice_course(void)
{
    const BoontaCourseDefinition *course = boonta_course_catalog[0];
    unsigned int completed_laps = 99U;
    float progress = -1.0f;
    float remaining = 0.0f;
    float x = 0.0f, y = 0.0f, z = 0.0f, width = 0.0f;

    assert(BOONTA_COURSE_COUNT == 1U);
    assert(course != NULL);
    assert(strcmp(course->id, "canyon-run") == 0);
    assert(strcmp(course->display_name, "CANYON RUN") == 0);
    assert(strcmp(course->region, "DESERT CANYON") == 0);
    assert(isfinite(course->lap_distance) && course->lap_distance > 150.0f);
    assert(course->node_count == 8U && course->edge_count == 8U);
    assert(!course->has_branches);
    assert(course->reset && course->advance && course->sample);
    assert(course->get_lap_state && course->distance_to_next_finish);
    assert(course->runtime_context != NULL);

    assert(course->reset(course->runtime_context));
    assert(course->get_lap_state(course->runtime_context, &completed_laps, &progress));
    assert(completed_laps == 0U);
    assert(isfinite(progress) && progress >= 0.0f && progress <= 1.0f);

    assert(course->distance_to_next_finish(course->runtime_context, 0.0f, &remaining));
    assert(fabsf(remaining - course->lap_distance) < 0.001f);

    course->sample(course->runtime_context, 0.0f, course->lap_distance * 0.25f,
                   course->road_half_width, &x, &y, &z, &width);
    assert(isfinite(x) && isfinite(y) && isfinite(z) && isfinite(width));
    assert(width >= 2.2f && width <= 4.8f);

    assert(course->advance(course->runtime_context, 0.25f, 0.0f));
    assert(course->distance_to_next_finish(course->runtime_context, 0.25f, &remaining));
    assert(fabsf(remaining - (course->lap_distance - 0.25f)) < 0.001f);
}

int main(void)
{
    test_single_vertical_slice_course();
    puts("single-course vertical-slice tests passed");
    return 0;
}
