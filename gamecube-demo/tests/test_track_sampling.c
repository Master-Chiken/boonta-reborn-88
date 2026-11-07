#include "../source/track_sampling.h"
#include "../source/gameplay_state.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>

static BoontaTrackSampler g_sampler;

static void sample(float travelled, float *x, float *y, float *z, float *width)
{
    boonta_track_sampler_sample_at(&g_sampler, travelled, 3.5f, x, y, z, width);
}

static void assert_close(float actual, float expected, float tolerance)
{
    assert(isfinite(actual));
    assert(fabsf(actual - expected) <= tolerance);
}

static void test_sampler_length_matches_generated_lap_length(void)
{
    float x, y, z, width;
    sample(0.0f, &x, &y, &z, &width);
    assert(g_sampler.lengths_ready);
    assert(g_sampler.total_length > 0.0f);
    assert(g_sampler.total_length == BOONTA_TRACK_LENGTH);
}

static void test_all_internal_chord_boundaries_land_on_the_next_track_point(void)
{
    unsigned int i;
    float travelled = 0.0f;
    float x, y, z, width;

    sample(0.0f, &x, &y, &z, &width);
    for (i = 0U; i < BOONTA_TRACK_POINT_COUNT; ++i) {
        const unsigned int next = (i + 1U) % BOONTA_TRACK_POINT_COUNT;
        travelled += g_sampler.segment_lengths[i];
        sample(travelled, &x, &y, &z, &width);
        assert_close(x, boonta_track_points_original_test_oval[next].x, 0.0001f);
        assert_close(y, boonta_track_points_original_test_oval[next].y, 0.0001f);
        assert_close(z, boonta_track_points_original_test_oval[next].z, 0.0001f);
        assert_close(width, boonta_track_points_original_test_oval[next].half_width, 0.0001f);
    }
}

static void test_positive_negative_and_multiple_lap_sampling_wraps(void)
{
    const float base = g_sampler.total_length * 0.371f;
    const float period = g_sampler.total_length;
    float reference[4];
    float x, y, z, width;
    int laps;

    sample(base, &reference[0], &reference[1], &reference[2], &reference[3]);
    for (laps = -3; laps <= 3; ++laps) {
        sample(base + (float)laps * period, &x, &y, &z, &width);
        assert_close(x, reference[0], 0.001f);
        assert_close(y, reference[1], 0.001f);
        assert_close(z, reference[2], 0.001f);
        assert_close(width, reference[3], 0.001f);
    }

    sample(-0.25f, &x, &y, &z, &width);
    {
        float wrapped_x, wrapped_y, wrapped_z, wrapped_width;
        sample(period - 0.25f, &wrapped_x, &wrapped_y, &wrapped_z, &wrapped_width);
        assert_close(x, wrapped_x, 0.001f);
        assert_close(y, wrapped_y, 0.001f);
        assert_close(z, wrapped_z, 0.001f);
        assert_close(width, wrapped_width, 0.001f);
    }
}

static void test_closed_loop_seam_position_and_tangent_are_continuous(void)
{
    const float step = 0.02f;
    const float length = g_sampler.total_length;
    float before_x, before_y, before_z, width;
    float seam_x, seam_y, seam_z;
    float after_x, after_y, after_z;
    float in_x, in_y, in_z, out_x, out_y, out_z;
    float in_length, out_length, direction_dot;

    sample(length - step, &before_x, &before_y, &before_z, &width);
    sample(0.0f, &seam_x, &seam_y, &seam_z, &width);
    sample(step, &after_x, &after_y, &after_z, &width);

    in_x = seam_x - before_x;
    in_y = seam_y - before_y;
    in_z = seam_z - before_z;
    out_x = after_x - seam_x;
    out_y = after_y - seam_y;
    out_z = after_z - seam_z;
    in_length = sqrtf(in_x * in_x + in_y * in_y + in_z * in_z);
    out_length = sqrtf(out_x * out_x + out_y * out_y + out_z * out_z);
    assert(in_length > 0.0001f && out_length > 0.0001f);
    direction_dot = (in_x * out_x + in_y * out_y + in_z * out_z) /
                    (in_length * out_length);
    assert(direction_dot > 0.99f);
}


static void test_compiled_lap_length_drives_three_lap_finish_and_sampler_wrap(void)
{
    const float lap_length = BOONTA_TRACK_LENGTH;
    float start_x, start_y, start_z, start_width;
    float x, y, z, width;
    unsigned int lap_count = 0U;
    unsigned int lap;

    assert(isfinite(lap_length) && lap_length > 1.0f);
    sample(0.0f, &start_x, &start_y, &start_z, &start_width);

    /*
     * The actual renderer sampler wraps its Catmull-Rom position while the
     * gameplay counter stays unwrapped and counts this compiled header length.
     * These values must remain aligned over the complete three-lap race.
     */
    for (lap = 1U; lap <= 3U; ++lap) {
        const float boundary = (float)lap * lap_length;
        const float previous_distance = boundary - 0.01f;
        const float current_distance = boundary + 0.01f;

        sample(boundary, &x, &y, &z, &width);
        assert_close(x, start_x, 0.001f);
        assert_close(y, start_y, 0.001f);
        assert_close(z, start_z, 0.001f);
        assert_close(width, start_width, 0.001f);

        lap_count = boonta_lap_count_after_frame(
            lap_count, previous_distance, current_distance, lap_length);
        assert(lap_count == lap);
        assert(boonta_race_is_finished(lap_count, 3U) == (lap == 3U));
    }

    /* A single large update must count every crossed boundary on this track. */
    assert(boonta_lap_count_after_frame(
        0U, lap_length * 0.25f, lap_length * 3.25f, lap_length) == 3U);
}


static void test_runtime_catmull_rom_length_matches_compiled_lap_distance(void)
{
    const unsigned int subdivisions_per_segment = 128U;
    float travelled = 0.0f;
    float runtime_curve_length = 0.0f;
    float previous_x, previous_y, previous_z, width;
    unsigned int segment;

    sample(0.0f, &previous_x, &previous_y, &previous_z, &width);
    for (segment = 0U; segment < BOONTA_TRACK_POINT_COUNT; ++segment) {
        const float segment_length = g_sampler.segment_lengths[segment];
        unsigned int step;
        for (step = 1U; step <= subdivisions_per_segment; ++step) {
            const float distance = travelled + segment_length *
                ((float)step / (float)subdivisions_per_segment);
            float x, y, z;
            sample(distance, &x, &y, &z, &width);
            {
                const float dx = x - previous_x;
                const float dy = y - previous_y;
                const float dz = z - previous_z;
                runtime_curve_length += sqrtf(dx * dx + dy * dy + dz * dz);
            }
            previous_x = x;
            previous_y = y;
            previous_z = z;
        }
        travelled += segment_length;
    }

    {
        const float relative_error =
            fabsf(runtime_curve_length - BOONTA_TRACK_LENGTH) / BOONTA_TRACK_LENGTH;
        printf("Runtime Catmull-Rom sampler length: %.6f m; "
               "compiled lap distance: %.6f m; difference: %.5f%%\n",
               runtime_curve_length, BOONTA_TRACK_LENGTH, relative_error * 100.0f);
        assert(relative_error < 0.0002f);
    }
}

static void test_nonfinite_distance_returns_safe_defaults(void)
{
    float x = 9.0f, y = 9.0f, z = 9.0f, width = 0.0f;
    sample(NAN, &x, &y, &z, &width);
    assert(x == 0.0f && y == 0.0f && z == 0.0f);
    assert(width == 3.5f);
}

int main(void)
{
    test_sampler_length_matches_generated_lap_length();
    test_all_internal_chord_boundaries_land_on_the_next_track_point();
    test_positive_negative_and_multiple_lap_sampling_wraps();
    test_closed_loop_seam_position_and_tangent_are_continuous();
    test_compiled_lap_length_drives_three_lap_finish_and_sampler_wrap();
    test_runtime_catmull_rom_length_matches_compiled_lap_distance();
    test_nonfinite_distance_returns_safe_defaults();
    puts("Production track-sampling C tests passed.");
    return 0;
}
