#include "race_feedback.h"
#include <math.h>
#include <stdio.h>
#include <string.h>

#define CHECK(expr) do { if (!(expr)) { \
    fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #expr); return 1; \
} } while (0)

#define POINTS 32U
static RacerTrackPoint ring[POINTS];

static void make_ring(void)
{
    unsigned int i;
    for (i = 0; i < POINTS; ++i) {
        float angle = (float)i * 6.2831853071795864769f / (float)POINTS;
        ring[i].x = 40.0f * sinf(angle);
        ring[i].y = 0.0f;
        ring[i].z = 28.0f * cosf(angle);
    }
}

int main(void)
{
    RaceFeedback feedback;
    RacerState player;
    RacerTrackProjection projection;
    unsigned int i;

    make_ring();
    memset(&player, 0, sizeof(player));
    player.x = ring[0].x;
    player.z = ring[0].z;
    projection = racer_project_to_track(player.x, player.z, ring, POINTS);
    player.track_segment = projection.segment;
    player.speed = 10.0f;
    player.heading = atan2f(ring[1].x-ring[0].x, ring[1].z-ring[0].z);
    race_feedback_init(&feedback);

    for (i = 0; i < 8U; ++i) race_feedback_update(&feedback, &player, ring, POINTS, 0.1f);
    CHECK(feedback.wrong_way == 0);
    CHECK(feedback.heading_alignment > 0.8f);

    player.heading += 3.14159265358979323846f;
    for (i = 0; i < 4U; ++i) race_feedback_update(&feedback, &player, ring, POINTS, 0.1f);
    CHECK(feedback.wrong_way == 0); /* short reverse input is not enough */
    for (i = 0; i < 4U; ++i) race_feedback_update(&feedback, &player, ring, POINTS, 0.1f);
    CHECK(feedback.wrong_way == 1);
    CHECK(feedback.heading_alignment < -0.8f);

    player.heading -= 3.14159265358979323846f;
    for (i = 0; i < 3U; ++i) race_feedback_update(&feedback, &player, ring, POINTS, 0.1f);
    CHECK(feedback.wrong_way == 0); /* clears after the player points forward again */

    player.heading += 3.14159265358979323846f;
    player.speed = 0.0f;
    race_feedback_init(&feedback);
    for (i = 0; i < 15U; ++i) race_feedback_update(&feedback, &player, ring, POINTS, 0.1f);
    CHECK(feedback.wrong_way == 0); /* stationary turning must not warn */

    race_feedback_update(&feedback, &player, 0, POINTS, 0.1f);
    race_feedback_update(&feedback, &player, ring, 2U, 0.1f);

    /* A self-crossing course has two coincident segments with opposite tangents.
       Global projection chooses segment 0 on the tie, which would mislabel a pod
       correctly travelling along segment 4 as moving the wrong way. */
    {
        const RacerTrackPoint crossing[8] = {
            {-10.0f,0.0f,0.0f}, {10.0f,0.0f,0.0f},
            {10.0f,0.0f,10.0f}, {-10.0f,0.0f,10.0f},
            {10.0f,0.0f,0.0f}, {-10.0f,0.0f,0.0f},
            {-10.0f,0.0f,-10.0f}, {10.0f,0.0f,-10.0f}
        };
        RacerTrackProjection global = racer_project_to_track(0.0f, 0.0f, crossing, 8U);
        RacerTrackProjection local = racer_project_to_track_near(0.0f, 0.0f, crossing, 8U, 4U);
        memset(&player, 0, sizeof(player));
        player.x = 0.0f; player.z = 0.0f; player.speed = 10.0f;
        player.track_segment = 4U;
        player.heading = -1.57079632679f; /* -X, the forward tangent of segment 4 */
        CHECK(global.segment == 0U);
        CHECK(local.segment == 4U);
        race_feedback_init(&feedback);
        for (i = 0; i < 8U; ++i)
            race_feedback_update(&feedback, &player, crossing, 8U, 0.1f);
        CHECK(feedback.wrong_way == 0);
        CHECK(feedback.heading_alignment > 0.8f);

        /* Invalid time steps must not corrupt warning persistence. */
        race_feedback_update(&feedback, &player, crossing, 8U, NAN);
        CHECK(isfinite(feedback.reverse_time));
        CHECK(isfinite(feedback.forward_time));
        CHECK(isfinite(feedback.heading_alignment));
    }
    puts("PASS: wrong-way hysteresis, crossing continuity, invalid frame deltas and bad tracks");
    return 0;
}
