#ifndef SWE1R_RIVAL_AI_H
#define SWE1R_RIVAL_AI_H

#include "racer_physics.h"

#ifdef __cplusplus
extern "C" {
#endif

#define RIVAL_AI_LANE_COUNT 3U

typedef struct {
    float x, y, z, heading;
    float progress;
    float speed;
    float lane_offset;
    float target_lane_offset;
    float lane_timer;
    float collision_cooldown;
    float impact_recovery_timer; /* keeps the post-impact escape lane briefly */
    float corner_factor;
    float cruise_speed;
    float max_speed;
    float acceleration;
    float grip;
    float boost_power;
    float difficulty_scale; /* 0.88 easy, 1.00 normal, 1.12 hard */
    float aggression; /* deterministic rival personality, roughly 0.75..1.25 */
    float lane_change_interval; /* personality-specific lane-change cadence */
    float surface_grip; /* current course grip, 0.60..1.20 */
    float rolling_resistance; /* current course drag, 0..3 */
    float road_width; /* full course ribbon width; synchronizes AI lanes with track */
    float boost_energy, boost_heat, boost_timer, boost_cooldown;
    int boost_active;
    unsigned int lap;
    unsigned int lane_choice;
    unsigned char r, g, b;
} RivalAIState;

void rival_ai_init(RivalAIState *rivals, unsigned int count,
                   const RacerTrackPoint *track, unsigned int track_count,
                   float track_length);
void rival_ai_set_pose(RivalAIState *rival, const RacerTrackPoint *track,
                       unsigned int track_count, float track_length);
/* Apply the selected pod tuning to a rival so AI handling matches its model. */
void rival_ai_set_vehicle_spec(RivalAIState *rival, const RacerVehicleSpec *vehicle);
/* Set AI race difficulty for all rivals without changing their vehicle identity. */
void rival_ai_set_difficulty(RivalAIState *rivals, unsigned int count, unsigned int level);
/* Apply course surface properties to all rivals so AI and player share the same conditions. */
void rival_ai_set_track_surface(RivalAIState *rivals, unsigned int count,
                                float surface_grip, float rolling_resistance);
/* Set the rendered/physical course width and constrain AI lanes to its usable area. */
void rival_ai_set_track_width(RivalAIState *rivals, unsigned int count, float road_width);
float rival_ai_lane_limit_for_width(float road_width);
/* Returns non-zero if a pod-to-pod impact affected the player this frame. */
int rival_ai_update(RivalAIState *rivals, unsigned int count,
                    const RacerTrackPoint *track, unsigned int track_count,
                    float track_length, RacerState *player,
                    const RacerVehicleSpec *player_vehicle, float dt);

#ifdef __cplusplus
}
#endif
#endif
