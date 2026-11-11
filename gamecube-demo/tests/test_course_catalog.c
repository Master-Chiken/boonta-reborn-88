#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "../source/course_catalog.h"

static void test_course(const BoontaCourseDefinition *course,
                        float *sample_x, float *sample_y, float *sample_z)
{
    float remaining = 0.0f;
    float x = 0.0f, y = 0.0f, z = 0.0f, width = 0.0f;
    float start_x = 0.0f, start_y = 0.0f, start_z = 0.0f;
    float seam_x = 0.0f, seam_y = 0.0f, seam_z = 0.0f;

    assert(course != NULL && course->id != NULL &&
           course->display_name != NULL && course->region != NULL);
    assert(isfinite(course->lap_distance) && course->lap_distance > 150.0f);
    assert(course->node_count == 8U && course->edge_count == 8U);
    assert(course->reset != NULL && course->sample != NULL &&
           course->distance_to_next_finish != NULL);
    assert(course->reset(course->runtime_context));

    assert(course->distance_to_next_finish(course->runtime_context, 0.0f, &remaining));
    assert(fabsf(remaining - course->lap_distance) < 0.001f);
    assert(course->distance_to_next_finish(course->runtime_context, 0.25f, &remaining));
    assert(fabsf(remaining - (course->lap_distance - 0.25f)) < 0.001f);

    /* The route must close continuously at the lap boundary. */
    course->sample(course->runtime_context, 0.0f, course->road_half_width,
                   &start_x, &start_y, &start_z, NULL);
    course->sample(course->runtime_context, course->lap_distance,
                   course->road_half_width, &seam_x, &seam_y, &seam_z, NULL);
    assert(fabsf(start_x - seam_x) < 0.05f);
    assert(fabsf(start_y - seam_y) < 0.05f);
    assert(fabsf(start_z - seam_z) < 0.05f);

    /* Immediately before the line, the remaining distance must approach zero. */
    assert(course->distance_to_next_finish(
        course->runtime_context, course->lap_distance - 0.001f, &remaining));
    assert(fabsf(remaining - 0.001f) < 0.001f);

    /* At the line, report the next lap's finish rather than a zero-length lap. */
    assert(course->distance_to_next_finish(
        course->runtime_context, course->lap_distance, &remaining));
    assert(fabsf(remaining - course->lap_distance) < 0.001f);

    assert(!course->distance_to_next_finish(course->runtime_context, -1.0f, &remaining));
    assert(!course->distance_to_next_finish(course->runtime_context, NAN, &remaining));
    assert(!course->distance_to_next_finish(course->runtime_context, 0.0f, NULL));

    course->sample(course->runtime_context, course->lap_distance * 0.25f,
                   course->road_half_width, &x, &y, &z, &width);
    assert(isfinite(x) && isfinite(y) && isfinite(z) && isfinite(width));
    assert(width >= 2.2f && width <= 4.8f);
    *sample_x = x;
    *sample_y = y;
    *sample_z = z;
}

int main(void)
{
    unsigned int i, j;
    float x[BOONTA_COURSE_COUNT];
    float y[BOONTA_COURSE_COUNT];
    float z[BOONTA_COURSE_COUNT];

    for (i = 0U; i < BOONTA_COURSE_COUNT; ++i) {
        test_course(boonta_course_catalog[i], &x[i], &y[i], &z[i]);
        for (j = 0U; j < i; ++j) {
            assert(fabsf(x[i] - x[j]) + fabsf(y[i] - y[j]) +
                   fabsf(z[i] - z[j]) > 1.0f);
            assert(strcmp(boonta_course_catalog[i]->id,
                          boonta_course_catalog[j]->id) != 0);
        }
    }

    assert(boonta_course_catalog[0] == &boonta_course_canyon_run);
    assert(boonta_course_catalog[1] == &boonta_course_red_dunes);
    assert(boonta_course_catalog[2] == &boonta_course_basalt_spiral);
    puts("course catalog tests passed");
    return 0;
}
