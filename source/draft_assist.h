#ifndef SWE1R_DRAFT_ASSIST_H
#define SWE1R_DRAFT_ASSIST_H

#include "racer_physics.h"
#include "rival_ai.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Returns 1 when a rival is close ahead on the same line; restores boost energy. */
int draft_assist_update(RacerState *player, const RivalAIState *rivals,
                        unsigned int rival_count, float dt);

#ifdef __cplusplus
}
#endif
#endif
