#ifndef SWE1R_RACE_FEEDBACK_H
#define SWE1R_RACE_FEEDBACK_H

#include "racer_physics.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    float reverse_time;
    float forward_time;
    int wrong_way;
    float heading_alignment; /* -1 reverse, 0 sideways, +1 forward */
} RaceFeedback;

void race_feedback_init(RaceFeedback *feedback);
/* Set wrong_way only after sustained reverse travel; clear it after recovery. */
void race_feedback_update(RaceFeedback *feedback, const RacerState *player,
                          const RacerTrackPoint *track, unsigned int track_count,
                          float dt);

#ifdef __cplusplus
}
#endif
#endif
