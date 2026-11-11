#ifndef BOONTA_REBORN_COURSE_CATALOG_H
#define BOONTA_REBORN_COURSE_CATALOG_H
#define BOONTA_COURSE_COUNT 3U
typedef struct BoontaCourseDefinition {
    const char *id;
    const char *display_name;
    const char *region;
    float lap_distance;
    float road_half_width;
    unsigned int node_count;
    unsigned int edge_count;
    int (*reset)(void *runtime_context);
    void (*sample)(void *runtime_context, float travelled, float fallback_half_width,
                   float *x, float *y, float *z, float *width);
    int (*distance_to_next_finish)(void *runtime_context, float player_distance,
                                   float *distance);
    void *runtime_context;
} BoontaCourseDefinition;
extern const BoontaCourseDefinition boonta_course_canyon_run;
extern const BoontaCourseDefinition boonta_course_red_dunes;
extern const BoontaCourseDefinition boonta_course_basalt_spiral;
extern const BoontaCourseDefinition *const boonta_course_catalog[BOONTA_COURSE_COUNT];
#endif
