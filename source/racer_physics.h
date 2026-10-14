#ifndef SWE1R_RACER_PHYSICS_H
#define SWE1R_RACER_PHYSICS_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    float x;
    float y;
    float z;
} RacerTrackPoint;

#define RACER_CHECKPOINT_COUNT 3U
#define RACER_CHECKPOINT_MASK_ALL ((1U << RACER_CHECKPOINT_COUNT) - 1U)

typedef struct {
    float x, z;
    float tangent_x, tangent_z;
    int valid;
} RacerCheckpointGate;

/* Data-driven pod handling: all values are tuning multipliers or world units. */
typedef struct {
    const char *name;
    float top_speed;
    float acceleration;
    float steering;
    float grip;
    float boost_power;
    float boost_heat_rate;
    float boost_cooling_rate;
    float drift_charge_rate;
    float damage_resistance;
    unsigned char r, g, b;
} RacerVehicleSpec;

typedef struct {
    float x;
    float y;
    float z;
    float heading;          /* radians; local +Z is forward */
    float speed;            /* world units per second */
    float boost_heat;       /* 0..100; overheat disables boost until cooled */
    float boost_energy;     /* 0..100; depleted by boosting, recovered by drifting */
    float drift_charge;     /* 0..100; long, controlled drifts award boost energy */
    float drift_angle;      /* chassis/velocity angle, radians */
    float damage;            /* 0..100; affects acceleration above 60 */
    float collision_cooldown; /* seconds before another impact can add damage */
    float race_time;
    float lap_time;
    float best_lap_time;
    float track_progress;   /* 0..1 along the centerline */
    float track_distance;   /* nearest centerline distance in world units */
    float track_lateral_offset; /* signed distance from the route centerline */
    float offroad_severity; /* 0..1; gradual edge penalty before full off-road */
    unsigned int track_segment;
    unsigned int checkpoint_mask; /* three physical sector gates required per valid lap */
    RacerCheckpointGate checkpoint_gates[RACER_CHECKPOINT_COUNT];
    unsigned int lap;       /* starts at lap 1 */
    int offroad;
    int overheated;
    int boost_active;
    int drifting;
} RacerState;

typedef struct {
    float steering;         /* -1..1; negative = left */
    float throttle;         /* 0..1 */
    float brake;            /* 0..1 */
    float boost;            /* 0..1 */
    float drift;            /* 0..1; handbrake drift */
} RacerInput;

typedef struct {
    unsigned int segment;
    float segment_t;
    float x;
    float y;
    float z;
    float distance_sq;
    float lateral_offset; /* signed across-track distance in the segment normal */
    float progress;
    float total_length;
} RacerTrackProjection;

void racer_init(RacerState *state, const RacerTrackPoint *track, unsigned int count);
RacerTrackProjection racer_project_to_track(float x, float z,
                                             const RacerTrackPoint *track,
                                             unsigned int count);
/* Continuity-aware projection for a racer that was previously on hint_segment.
   At near-equal geometric distances it prefers nearby segments, avoiding
   progress jumps between overlapping/crossing parts of a circuit. */
RacerTrackProjection racer_project_to_track_near(float x, float z,
                                                  const RacerTrackPoint *track,
                                                  unsigned int count,
                                                  unsigned int hint_segment);
void racer_update(RacerState *state, const RacerTrackPoint *track,
                  unsigned int count, const RacerInput *input, float dt);
void racer_update_vehicle(RacerState *state, const RacerTrackPoint *track,
                          unsigned int count, const RacerInput *input,
                          const RacerVehicleSpec *vehicle, float dt);
void racer_update_vehicle_surface(RacerState *state, const RacerTrackPoint *track,
                                  unsigned int count, const RacerInput *input,
                                  const RacerVehicleSpec *vehicle,
                                  float surface_grip, float rolling_resistance,
                                  float dt);
/* Runtime variant that matches off-road handling to the rendered track width.
   road_width is the full ribbon width in world units. */
void racer_update_vehicle_surface_width(RacerState *state, const RacerTrackPoint *track,
                                        unsigned int count, const RacerInput *input,
                                        const RacerVehicleSpec *vehicle,
                                        float surface_grip, float rolling_resistance,
                                        float road_width, float dt);
void racer_apply_impact(RacerState *state, const RacerVehicleSpec *vehicle,
                        float damage_amount, float speed_multiplier);
float racer_track_lateral_offset(float x, float z,
                                 const RacerTrackPoint *track,
                                 unsigned int count);
/* Returns true only when a movement segment crosses the start/finish plane in
   the course's forward direction and within the road-width lateral bounds. */
/* Build a forward-facing checkpoint gate at normalized route progress [0,1]. */
int racer_checkpoint_gate_at_progress(const RacerTrackPoint *track, unsigned int count,
                                       float progress, RacerCheckpointGate *out_gate);
/* Physical, forward-only crossing test with lateral limits matching the road. */
int racer_crossed_checkpoint_gate(float previous_x, float previous_z,
                                  float current_x, float current_z,
                                  const RacerCheckpointGate *gate, float road_width);
int racer_crossed_finish_line(float previous_x, float previous_z,
                              float current_x, float current_z,
                              const RacerTrackPoint *track, unsigned int count,
                              float road_width);

#ifdef __cplusplus
}
#endif
#endif
