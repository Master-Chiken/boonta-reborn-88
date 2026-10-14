#ifndef BOONTA_TRACK_PATH_H
#define BOONTA_TRACK_PATH_H

/*
 * Clean-room sampled track path primitives.
 * Points are caller-owned, ordered centerline samples in world units.
 * Closed paths wrap progress; open paths clamp progress to [0, 1].
 */
typedef struct TrackVec3 {
    float x;
    float y;
    float z;
} TrackVec3;

typedef struct TrackPath {
    const TrackVec3 *points;
    int point_count;
    int closed;
} TrackPath;

typedef struct TrackPathSample {
    TrackVec3 position;
    TrackVec3 tangent;
    float distance;
    float progress;
    int segment_index;
} TrackPathSample;

typedef struct TrackPathProjection {
    TrackVec3 position;
    float distance_squared;
    float distance_along_path;
    float progress;
    int segment_index;
} TrackPathProjection;

/* Returns total polyline length, or 0 for invalid/degenerate paths. */
float track_path_length(const TrackPath *path);

/* Evaluate by distance along the centerline; closed paths wrap, open paths clamp. */
int track_path_sample_distance(const TrackPath *path, float distance,
                               TrackPathSample *out_sample);

/* Evaluate normalized progress; closed paths wrap, open paths clamp. */
int track_path_sample_progress(const TrackPath *path, float progress,
                               TrackPathSample *out_sample);

/* Project a world-space point to the nearest centerline segment. */
int track_path_project(const TrackPath *path, TrackVec3 point,
                       TrackPathProjection *out_projection);

#endif
