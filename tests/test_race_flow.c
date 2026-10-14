#include "race_flow.h"
#include <stdio.h>
#include <math.h>

#define CHECK(expr) do { if (!(expr)) { \
    fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #expr); return 1; \
} } while (0)

int main(void)
{
    RaceFlow flow;
    unsigned int i;
    race_flow_init(&flow, 3U);
    CHECK(flow.phase == RACE_PHASE_COUNTDOWN);
    CHECK(flow.target_laps == 3U);
    CHECK(race_flow_countdown_label(&flow) == 3);

    for (i = 0; i < 61U; ++i) race_flow_update(&flow, 1.0f/60.0f, 1U);
    CHECK(race_flow_countdown_label(&flow) == 2);
    for (i = 0; i < 60U; ++i) race_flow_update(&flow, 1.0f/60.0f, 1U);
    CHECK(race_flow_countdown_label(&flow) == 1);
    for (i = 0; i < 60U; ++i) race_flow_update(&flow, 1.0f/60.0f, 1U);
    CHECK(race_flow_countdown_label(&flow) == 0); /* GO */
    for (i = 0; i < 100U && flow.phase == RACE_PHASE_COUNTDOWN; ++i)
        race_flow_update(&flow, 1.0f/60.0f, 1U);
    CHECK(flow.phase == RACE_PHASE_RUNNING);
    CHECK(flow.race_elapsed == 0.0f); /* countdown time is not race time */

    race_flow_update(&flow, 0.05f, 1U);
    CHECK(flow.race_elapsed > 0.04f);
    race_flow_update(&flow, 0.05f, 3U);
    CHECK(flow.phase == RACE_PHASE_RUNNING); /* final lap has not been crossed */
    race_flow_update(&flow, 0.05f, 4U);
    CHECK(flow.phase == RACE_PHASE_FINISHED);
    {
        float finished_time = flow.race_elapsed;
        race_flow_update(&flow, 0.05f, 5U);
        CHECK(flow.race_elapsed == finished_time); /* finish is absorbing */
    }

    race_flow_init(&flow, 0U);
    CHECK(flow.target_laps == 3U);
    {
        float remaining = flow.countdown_remaining;
        race_flow_update(&flow, NAN, 1U);
        CHECK(flow.countdown_remaining == remaining); /* NaN must not poison countdown */
    }
    race_flow_update(&flow, INFINITY, 1U); /* positive infinity is capped */
    CHECK(flow.countdown_remaining > 3.49f && flow.countdown_remaining < 3.51f);
    race_flow_update(&flow, 10.0f, 1U); /* large delta is capped for stability */
    CHECK(flow.countdown_remaining >= 0.0f);
    while (flow.phase == RACE_PHASE_COUNTDOWN)
        race_flow_update(&flow, 0.10f, 1U);
    {
        float elapsed = flow.race_elapsed;
        race_flow_update(&flow, NAN, 1U);
        CHECK(flow.race_elapsed == elapsed); /* NaN must not poison race time */
        race_flow_update(&flow, 0.05f, 1U);
        CHECK(flow.race_elapsed > elapsed);
    }
    puts("PASS: countdown, GO phase, lap target, finite delta handling and finish lock");
    return 0;
}
