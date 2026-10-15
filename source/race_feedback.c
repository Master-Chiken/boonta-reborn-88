/* Portable driving guidance: sustained direction checks against track tangent. */
#include "race_feedback.h"
#include <math.h>

static float clamp_feedback(float value, float low, float high)
{
    if (value < low) return low;
    if (value > high) return high;
    return value;
}

void race_feedback_init(RaceFeedback *feedback)
{
    if (feedback == 0) return;
    feedback->reverse_time = 0.0f;
    feedback->forward_time = 0.0f;
    feedback->wrong_way = 0;
    feedback->heading_alignment = 1.0f;
}

void race_feedback_update(RaceFeedback *feedback, const RacerState *player,
                          const RacerTrackPoint *track, unsigned int track_count,
                          float dt)
{
    RacerTrackProjection projection;
    const RacerTrackPoint *a, *b;
    float dx, dz, length, heading_x, heading_z, alignment;

    if (feedback == 0 || player == 0 || track == 0 || track_count < 3U) return;
    /* A NaN frame delta would poison both persistence timers. Ignore it instead
       of letting the wrong-way warning become permanently stuck. */
    if (!(dt >= 0.0f)) return;
    dt = clamp_feedback(dt, 0.0f, 0.10f);
    if (dt <= 0.0f) return;

    /* At a self-crossing, a global nearest-segment search may select a different
       branch from the one the pod was following last frame. Use the physics
       segment hint so the warning uses the same local tangent as race progress. */
    projection = racer_project_to_track_near(player->x, player->z, track,
                                              track_count, player->track_segment);
    if (!(projection.distance_sq < 3.402823466e+38F)) return;
    a = &track[projection.segment % track_count];
    b = &track[(projection.segment + 1U) % track_count];
    dx = b->x - a->x;
    dz = b->z - a->z;
    length = sqrtf(dx*dx + dz*dz);
    if (!(length >= 1.0e-5f)) return;

    heading_x = sinf(player->heading);
    heading_z = cosf(player->heading);
    alignment = (heading_x * dx + heading_z * dz) / length;
    if (!(alignment == alignment)) return;
    feedback->heading_alignment = clamp_feedback(alignment, -1.0f, 1.0f);

    /* Ignore low-speed manoeuvres and require sustained reverse alignment to avoid
       false warnings while the course curves or the player spins briefly. */
    if (player->speed >= 3.0f && feedback->heading_alignment < -0.35f) {
        feedback->reverse_time += dt;
        feedback->forward_time = 0.0f;
        if (feedback->reverse_time >= 0.55f) feedback->wrong_way = 1;
    } else {
        feedback->reverse_time = 0.0f;
        if (player->speed < 2.0f || feedback->heading_alignment > 0.20f) {
            feedback->forward_time += dt;
            if (feedback->forward_time >= 0.25f) feedback->wrong_way = 0;
        } else {
            feedback->forward_time = 0.0f;
        }
    }
}
