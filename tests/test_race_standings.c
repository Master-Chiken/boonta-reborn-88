#include "race_standings.h"
#include <stdio.h>

#define CHECK(expr) do { if (!(expr)) { \
    fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #expr); return 1; \
} } while (0)

int main(void)
{
    float opponents[7] = {-0.01f, 0.20f, 0.80f, 1.05f, 0.30f, 0.90f, 0.60f};
    float progress[8] = {0.50f, 0.10f, 0.90f, 0.90f, -0.10f, 1.10f, 0.30f, 0.70f};
    unsigned int places[8] = {0U};
    CHECK(race_standings_progress(0U, 0.98f) < 0.0f);
    CHECK(race_standings_progress(2U, 0.25f) == 1.25f);
    CHECK(race_standings_player_place(0.50f, opponents, 7U) == 5U);
    CHECK(race_standings_player_place(0.50f, 0, 7U) == 1U);
    race_standings_rank(progress, 8U, places);
    CHECK(places[5] == 1U);
    CHECK(places[2] == 2U);
    CHECK(places[3] == 3U); /* Equal progress preserves the earlier racer. */
    CHECK(places[0] == 5U);
    CHECK(places[4] == 8U);
    puts("PASS: lap-aware progress, HUD place and stable 8-racer finish ranking");
    return 0;
}
