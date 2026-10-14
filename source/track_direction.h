#ifndef SWE1R_TRACK_DIRECTION_H
#define SWE1R_TRACK_DIRECTION_H

#include "racer_physics.h"

/* Reverse a closed course while keeping point 0 as the start/finish marker.
 * Returns 1 on success; invalid/too-short paths are left unchanged. */
int track_direction_reverse(RacerTrackPoint *points, unsigned int count);

#endif
