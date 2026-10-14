#include "track_path.h"

#include <math.h>
#include <stddef.h>

static TrackVec3 vec_sub(TrackVec3 a, TrackVec3 b)
{
    TrackVec3 v = {a.x - b.x, a.y - b.y, a.z - b.z};
    return v;
}

static TrackVec3 vec_add_scaled(TrackVec3 a, TrackVec3 b, float scale)
{
    TrackVec3 v = {a.x + b.x * scale, a.y + b.y * scale,
                   a.z + b.z * scale};
    return v;
}

static float vec_dot(TrackVec3 a, TrackVec3 b)
{
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

static float vec_length(TrackVec3 v)
{
    return sqrtf(vec_dot(v, v));
}

static TrackVec3 vec_scale(TrackVec3 v, float scale)
{
    TrackVec3 result = {v.x * scale, v.y * scale, v.z * scale};
    return result;
}

static int segment_count(const TrackPath *path)
{
    if (path == NULL || path->points == NULL || path->point_count < 2) {
        return 0;
    }
    return path->closed ? path->point_count : path->point_count - 1;
}

static TrackVec3 point_at(const TrackPath *path, int index)
{
    if (index >= path->point_count) index = 0;
    return path->points[index];
}

static float segment_length(const TrackPath *path, int index)
{
    TrackVec3 delta = vec_sub(point_at(path, index + 1),
                              point_at(path, index));
    return vec_length(delta);
}

float track_path_length(const TrackPath *path)
{
    int count = segment_count(path);
    float total = 0.0f;

    for (int i = 0; i < count; ++i) {
        float length = segment_length(path, i);
        if (!isfinite(length)) return 0.0f;
        total += length;
    }
    return total;
}

static float normalize_distance(const TrackPath *path, float distance,
                               float total_length)
{
    if (path->closed) {
        distance = fmodf(distance, total_length);
        if (distance < 0.0f) distance += total_length;
        return distance;
    }
    if (distance < 0.0f) return 0.0f;
    if (distance > total_length) return total_length;
    return distance;
}

int track_path_sample_distance(const TrackPath *path, float distance,
                               TrackPathSample *out_sample)
{
    int count = segment_count(path);
    float total_length;
    float traversed = 0.0f;

    if (out_sample == NULL || count == 0 || !isfinite(distance)) return 0;
    total_length = track_path_length(path);
    if (!(total_length > 0.000001f) || !isfinite(total_length)) return 0;
    distance = normalize_distance(path, distance, total_length);

    for (int i = 0; i < count; ++i) {
        TrackVec3 start = point_at(path, i);
        TrackVec3 end = point_at(path, i + 1);
        TrackVec3 delta = vec_sub(end, start);
        float length = vec_length(delta);
        float remaining = distance - traversed;

        if (length > 0.000001f &&
            (remaining <= length || i == count - 1)) {
            float t = remaining / length;
            if (t < 0.0f) t = 0.0f;
            if (t > 1.0f) t = 1.0f;
            out_sample->position = vec_add_scaled(start, delta, t);
            out_sample->tangent = vec_scale(delta, 1.0f / length);
            out_sample->distance = distance;
            out_sample->progress = distance / total_length;
            out_sample->segment_index = i;
            return 1;
        }
        traversed += length;
    }

    /* Degenerate zero-length tail: return the final valid point if possible. */
    out_sample->position = path->points[path->point_count - 1];
    out_sample->tangent.x = 0.0f;
    out_sample->tangent.y = 0.0f;
    out_sample->tangent.z = 0.0f;
    out_sample->distance = distance;
    out_sample->progress = distance / total_length;
    out_sample->segment_index = count - 1;
    return 1;
}

int track_path_sample_progress(const TrackPath *path, float progress,
                               TrackPathSample *out_sample)
{
    float length;
    if (!isfinite(progress)) return 0;
    length = track_path_length(path);
    if (!(length > 0.000001f)) return 0;
    if (path->closed) {
        progress = fmodf(progress, 1.0f);
        if (progress < 0.0f) progress += 1.0f;
    } else {
        if (progress < 0.0f) progress = 0.0f;
        if (progress > 1.0f) progress = 1.0f;
    }
    return track_path_sample_distance(path, progress * length, out_sample);
}

int track_path_project(const TrackPath *path, TrackVec3 point,
                       TrackPathProjection *out_projection)
{
    int count = segment_count(path);
    float total_length;
    float traversed = 0.0f;
    float best_distance_squared = INFINITY;
    int best_segment = -1;
    float best_t = 0.0f;
    TrackVec3 best_point = {0.0f, 0.0f, 0.0f};

    if (out_projection == NULL || count == 0 ||
        !isfinite(point.x) || !isfinite(point.y) || !isfinite(point.z)) {
        return 0;
    }
    total_length = track_path_length(path);
    if (!(total_length > 0.000001f) || !isfinite(total_length)) return 0;

    for (int i = 0; i < count; ++i) {
        TrackVec3 start = point_at(path, i);
        TrackVec3 delta = vec_sub(point_at(path, i + 1), start);
        float length_squared = vec_dot(delta, delta);
        float t = 0.0f;
        TrackVec3 candidate;
        TrackVec3 difference;
        float distance_squared;

        if (length_squared > 0.000001f) {
            t = vec_dot(vec_sub(point, start), delta) / length_squared;
            if (t < 0.0f) t = 0.0f;
            if (t > 1.0f) t = 1.0f;
        }
        candidate = vec_add_scaled(start, delta, t);
        difference = vec_sub(point, candidate);
        distance_squared = vec_dot(difference, difference);
        if (distance_squared < best_distance_squared) {
            best_distance_squared = distance_squared;
            best_segment = i;
            best_t = t;
            best_point = candidate;
        }
        traversed += sqrtf(length_squared);
    }

    if (best_segment < 0) return 0;
    traversed = 0.0f;
    for (int i = 0; i < best_segment; ++i) {
        traversed += segment_length(path, i);
    }
    traversed += segment_length(path, best_segment) * best_t;

    out_projection->position = best_point;
    out_projection->distance_squared = best_distance_squared;
    out_projection->distance_along_path = traversed;
    out_projection->progress = traversed / total_length;
    out_projection->segment_index = best_segment;
    return 1;
}
