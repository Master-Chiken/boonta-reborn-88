#include "draft_assist.h"
#include <math.h>
#include <stdio.h>
#include <string.h>

#define CHECK(expr) do { if (!(expr)) { \
    fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #expr); return 1; \
} } while (0)

int main(void)
{
    RacerState player;
    RivalAIState rivals[7];
    float energy;
    memset(&player, 0, sizeof(player));
    memset(rivals, 0, sizeof(rivals));
    player.heading = 0.0f; /* local +Z is forward */
    player.boost_energy = 30.0f;
    rivals[0].x = 0.5f;
    rivals[0].z = 12.0f;
    CHECK(draft_assist_update(&player, rivals, 1U, 1.0f/60.0f) == 1);
    CHECK(player.boost_energy > 30.0f);
    energy = player.boost_energy;
    CHECK(draft_assist_update(&player, rivals, 1U, 1.0f/60.0f) == 1);
    CHECK(player.boost_energy > energy);

    /* Too far sideways or behind must not grant free boost energy. */
    player.boost_energy = 30.0f;
    rivals[0].x = 8.0f;
    rivals[0].z = 12.0f;
    CHECK(draft_assist_update(&player, rivals, 1U, 1.0f/60.0f) == 0);
    CHECK(player.boost_energy == 30.0f);
    rivals[0].x = 0.0f;
    rivals[0].z = -5.0f;
    CHECK(draft_assist_update(&player, rivals, 1U, 1.0f/60.0f) == 0);
    CHECK(player.boost_energy == 30.0f);

    /* Energy is capped; dt and invalid inputs are safe. */
    player.boost_energy = 99.9f;
    rivals[0].x = 0.0f;
    rivals[0].z = 12.0f;
    CHECK(draft_assist_update(&player, rivals, 1U, 0.05f) == 1);
    CHECK(player.boost_energy == 100.0f);
    CHECK(draft_assist_update(0, rivals, 1U, 0.016f) == 0);
    CHECK(draft_assist_update(&player, 0, 1U, 0.016f) == 0);
    puts("PASS: slipstream detection, boost recharge, alignment and bounds");
    return 0;
}
