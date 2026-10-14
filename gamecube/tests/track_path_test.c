#include "track_path.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>

static int near(float a, float b, float epsilon)
{
    return fabsf(a - b) <= epsilon;
}

static void test_open_path_length_and_end_clamping(void)
{
    const TrackVec3 points[] = {
        {0.0f, 0.0f, 0.0f},
        {3.0f, 0.0f, 0.0f},
        {3.0f, 0.0f, 4.0f}
    };
    const TrackPath path = {points, 3, 0};
    TrackPathSample sample;

    assert(near(track_path_length(&path), 7.0f, 0.0001f));
    assert(track_path_sample_distance(&path, 1.5f, &sample));
    assert(near(sample.position.x, 1.5f, 0.0001f));
    assert(near(sample.position.z, 0.0f, 0.0001f));
    assert(near(sample.tangent.x, 1.0f, 0.0001f));
    assert(track_path_sample_progress(&path, 1.0f, &sample));
    assert(near(sample.position.x, 3.0f, 0.0001f));
    assert(near(sample.position.z, 4.0f, 0.0001f));
    assert(track_path_sample_distance(&path, 100.0f, &sample));
    assert(near(sample.distance, 7.0f, 0.0001f));
}

static void test_closed_path_wrap_and_negative_progress(void)
{
    const TrackVec3 points[] = {
        {0.0f, 0.0f, 0.0f},
        {2.0f, 0.0f, 0.0f},
        {2.0f, 0.0f, 2.0f},
        {0.0f, 0.0f, 2.0f}
    };
    const TrackPath path = {points, 4, 1};
    TrackPathSample a, b;

    assert(near(track_path_length(&path), 8.0f, 0.0001f));
    assert(track_path_sample_distance(&path, 0.5f, &a));
    assert(track_path_sample_distance(&path, 8.5f, &b));
    assert(near(a.position.x, b.position.x, 0.0001f));
    assert(near(a.position.z, b.position.z, 0.0001f));
    assert(track_path_sample_progress(&path, -0.125f, &b));
    assert(near(b.position.x, 0.0f, 0.0001f));
    assert(near(b.position.z, 1.0f, 0.0001f));
    assert(near(b.progress, 0.875f, 0.0001f));
}

static void test_projection_onto_nearest_segment(void)
{
    const TrackVec3 points[] = {
        {0.0f, 0.0f, 0.0f},
        {4.0f, 0.0f, 0.0f},
        {4.0f, 0.0f, 3.0f}
    };
    const TrackPath path = {points, 3, 0};
    const TrackVec3 query = {2.0f, 1.0f, 0.5f};
    TrackPathProjection projection;

    assert(track_path_project(&path, query, &projection));
    assert(projection.segment_index == 0);
    assert(near(projection.position.x, 2.0f, 0.0001f));
    assert(near(projection.position.y, 0.0f, 0.0001f));
    assert(near(projection.position.z, 0.0f, 0.0001f));
    assert(near(projection.distance_squared, 1.25f, 0.0001f));
    assert(near(projection.distance_along_path, 2.0f, 0.0001f));
    assert(near(projection.progress, 2.0f / 7.0f, 0.0001f));
}

static void test_invalid_and_degenerate_paths(void)
{
    const TrackVec3 one_point[] = {{1.0f, 2.0f, 3.0f}};
    const TrackVec3 duplicate_points[] = {
        {1.0f, 2.0f, 3.0f}, {1.0f, 2.0f, 3.0f}
    };
    const TrackPath too_short = {one_point, 1, 0};
    const TrackPath degenerate = {duplicate_points, 2, 0};
    TrackPathSample sample;
    TrackPathProjection projection;
    const TrackVec3 query = {1.0f, 2.0f, 3.0f};

    assert(track_path_length(&too_short) == 0.0f);
    assert(!track_path_sample_progress(&too_short, 0.5f, &sample));
    assert(track_path_length(&degenerate) == 0.0f);
    assert(!track_path_project(&degenerate, query, &projection));
    assert(!track_path_sample_distance(&degenerate, 0.0f, &sample));
    assert(!track_path_sample_progress(&degenerate, NAN, &sample));
}


static void test_progress_is_distance_based_not_point_index_based(void)
{
    const TrackVec3 points[] = {
        {0.0f, 0.0f, 0.0f},
        {1.0f, 0.0f, 0.0f},
        {5.0f, 0.0f, 0.0f}
    };
    const TrackPath path = {points, 3, 0};
    TrackPathSample sample;

    assert(near(track_path_length(&path), 5.0f, 0.0001f));
    assert(track_path_sample_progress(&path, 0.4f, &sample));
    assert(near(sample.position.x, 2.0f, 0.0001f));
    assert(near(sample.distance, 2.0f, 0.0001f));
    assert(sample.segment_index == 1);
}

static void test_projection_on_closed_seam(void)
{
    const TrackVec3 points[] = {
        {0.0f, 0.0f, 0.0f},
        {4.0f, 0.0f, 0.0f},
        {4.0f, 0.0f, 3.0f},
        {0.0f, 0.0f, 3.0f}
    };
    const TrackPath path = {points, 4, 1};
    const TrackVec3 query = {-0.5f, 0.0f, 1.5f};
    TrackPathProjection projection;

    assert(track_path_project(&path, query, &projection));
    assert(projection.segment_index == 3);
    assert(near(projection.position.x, 0.0f, 0.0001f));
    assert(near(projection.position.z, 1.5f, 0.0001f));
    assert(near(projection.distance_along_path, 12.5f, 0.0001f));
    assert(near(projection.progress, 12.5f / 14.0f, 0.0001f));
}

int main(void)
{
    test_open_path_length_and_end_clamping();
    test_closed_path_wrap_and_negative_progress();
    test_projection_onto_nearest_segment();
    test_invalid_and_degenerate_paths();
    test_progress_is_distance_based_not_point_index_based();
    test_projection_on_closed_seam();
    puts("track_path_test: 6 suites passed");
    return 0;
}
