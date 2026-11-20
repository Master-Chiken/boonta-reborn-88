#ifndef BOONTA_REBORN_COURSE_CATALOG_H
#define BOONTA_REBORN_COURSE_CATALOG_H
#define BOONTA_COURSE_COUNT 1U
typedef struct BoontaCourseDefinition {
    const char *id;
    const char *display_name;
    const char *region;
    float lap_distance;
    float road_half_width;
    unsigned int node_count;
    unsigned int edge_count;
    int has_branches;
    int (*reset)(void *runtime_context);
    int (*advance)(void *runtime_context, float distance_delta, float steering);
    void (*sample)(void *runtime_context, float player_distance, float travelled,
                   float fallback_half_width,
                   float *x, float *y, float *z, float *width);
    int (*reset_rival_route)(void *runtime_context, unsigned int rival_index,
                             float initial_route_distance, float lap_distance,
                             float *route_distance_out, float *progress_out);
    int (*advance_rival_route)(void *runtime_context, unsigned int rival_index,
                               float distance_delta, float steering,
                               float current_route_distance, float lap_distance,
                               float *next_route_distance_out, float *next_progress_out);
    int (*sample_rival_route)(void *runtime_context, unsigned int rival_index,
                              float current_route_distance, float target_route_distance,
                              float fallback_half_width,
                              float *x, float *y, float *z, float *width);
    int (*get_lap_state)(void *runtime_context,
                         unsigned int *completed_laps, float *lap_progress);
    int (*distance_to_next_finish)(void *runtime_context, float player_distance,
                                   float *distance);
    void *runtime_context;
} BoontaCourseDefinition;
extern const BoontaCourseDefinition boonta_course_canyon_run;
extern const BoontaCourseDefinition *const boonta_course_catalog[BOONTA_COURSE_COUNT];
#endif
