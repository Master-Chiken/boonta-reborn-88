#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "../source/course_catalog.h"
#include "../source/gameplay_state.h"

static void test_single_vertical_slice_course(void)
{
    const BoontaCourseDefinition *course = boonta_course_catalog[0];
    unsigned int completed_laps = 99U;
    float progress = -1.0f;
    float remaining = 0.0f;
    float x = 0.0f, y = 0.0f, z = 0.0f, width = 0.0f;

    assert(BOONTA_COURSE_COUNT == 2U);
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

static void test_course_owns_independent_rival_route_cursors(void)
{
    const BoontaCourseDefinition *course = boonta_course_catalog[0];
    unsigned int rival;

    assert(course->reset_rival_route != NULL);
    assert(course->advance_rival_route != NULL);
    assert(course->sample_rival_route != NULL);
    assert(course->reset(course->runtime_context));

    for (rival = 0U; rival < BOONTA_RIVAL_COUNT; ++rival) {
        const float grid_offset = boonta_rival_initial_progress(rival);
        float route_distance = -1.0f;
        float progress = -1.0f;
        float next_route_distance = -1.0f;
        float next_progress = -1.0f;
        float x = 0.0f, y = 0.0f, z = 0.0f, width = 0.0f;

        assert(course->reset_rival_route(course->runtime_context, rival,
            grid_offset, course->lap_distance, &route_distance, &progress));
        assert(fabsf(route_distance - grid_offset) < 0.001f);
        assert(fabsf(progress - grid_offset) < 0.02f);

        assert(course->sample_rival_route(course->runtime_context, rival,
            route_distance, route_distance + 4.0f, course->road_half_width,
            &x, &y, &z, &width) == BOONTA_ROUTE_CURSOR_OK);
        assert(isfinite(x) && isfinite(y) && isfinite(z));
        assert(isfinite(width) && width >= 2.2f && width <= 4.8f);

        assert(course->advance_rival_route(course->runtime_context, rival,
            0.25f, 0.0f, route_distance, course->lap_distance,
            &next_route_distance, &next_progress));
        assert(fabsf(next_route_distance - (route_distance + 0.25f)) < 0.001f);
        assert(next_progress > progress);

        /* Invalid movement must fail atomically and clear output coordinates. */
        next_route_distance = -1.0f;
        next_progress = -1.0f;
        assert(!course->advance_rival_route(course->runtime_context, rival,
            NAN, 0.0f, next_route_distance, course->lap_distance,
            &next_route_distance, &next_progress));
        assert(next_route_distance == 0.0f && next_progress == 0.0f);
    }
}

static void test_fork_run_course_exposes_real_left_and_right_routes(void)
{
    const BoontaCourseDefinition *course = boonta_course_catalog[1];
    unsigned int completed_laps = 99U;
    float lap_progress = -1.0f;
    float x_left = 0.0f, y_left = 0.0f, z_left = 0.0f, width_left = 0.0f;
    float x_right = 0.0f, y_right = 0.0f, z_right = 0.0f, width_right = 0.0f;
    float remaining = 0.0f;

    assert(course != NULL);
    assert(strcmp(course->id, "fork-run") == 0);
    assert(strcmp(course->display_name, "FORK RUN") == 0);
    assert(strcmp(course->region, "BRANCHING CANYON") == 0);
    assert(course->has_branches);
    assert(course->node_count == 6U && course->edge_count == 7U);
    assert(isfinite(course->lap_distance) && course->lap_distance > 90.0f);
    assert(course->reset && course->advance && course->sample);
    assert(course->reset_rival_route && course->advance_rival_route &&
           course->sample_rival_route);

    /* Negative steering chooses the positive-X (left) branch. */
    assert(course->reset(course->runtime_context));
    assert(course->get_lap_state(course->runtime_context,
        &completed_laps, &lap_progress));
    assert(course->advance(course->runtime_context, 1.0f, -0.8f));
    course->sample(course->runtime_context, 1.0f, 13.0f,
        course->road_half_width, &x_left, &y_left, &z_left, &width_left);
    assert(x_left > 0.5f);
    assert(isfinite(y_left) && isfinite(z_left));
    assert(isfinite(width_left) && width_left >= 2.2f && width_left <= 4.8f);

    /* Positive steering chooses the negative-X (right) branch. */
    assert(course->reset(course->runtime_context));
    assert(course->advance(course->runtime_context, 1.0f, 0.8f));
    course->sample(course->runtime_context, 1.0f, 13.0f,
        course->road_half_width, &x_right, &y_right, &z_right, &width_right);
    assert(x_right < -0.5f);
    assert(isfinite(y_right) && isfinite(z_right));
    assert(isfinite(width_right) && width_right >= 2.2f && width_right <= 4.8f);

    assert(course->distance_to_next_finish(
        course->runtime_context, 1.0f, &remaining));
    assert(isfinite(remaining) && remaining > 0.0f);
}

int main(void)
{
    test_single_vertical_slice_course();
    test_course_owns_independent_rival_route_cursors();
    test_fork_run_course_exposes_real_left_and_right_routes();
    puts("single-course and rival-route adapter tests passed");
    return 0;
}
