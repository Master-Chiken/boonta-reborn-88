#include "championship.h"

static const unsigned int g_points[CHAMPIONSHIP_MAX_RACERS] = {15U, 12U, 10U, 8U, 6U, 4U, 2U, 1U};

void championship_init(Championship *c, unsigned int rounds_total)
{
    unsigned int i;
    if (!c) return;
    c->rounds_total = rounds_total > CHAMPIONSHIP_MAX_ROUNDS ? CHAMPIONSHIP_MAX_ROUNDS : rounds_total;
    if (c->rounds_total == 0U) c->rounds_total = 1U;
    c->rounds_completed = 0U;
    c->recorded_mask = 0U;
    for (i = 0U; i < CHAMPIONSHIP_MAX_RACERS; ++i) {
        unsigned int j;
        c->points[i] = 0U;
        for (j = 0U; j < CHAMPIONSHIP_MAX_RACERS; ++j) c->place_counts[i][j] = 0U;
    }
}

unsigned int championship_points_for_place(unsigned int place)
{
    return (place >= 1U && place <= CHAMPIONSHIP_MAX_RACERS) ? g_points[place - 1U] : 0U;
}

static void update_rounds_completed(Championship *c)
{
    c->rounds_completed = 0U;
    while (c->rounds_completed < c->rounds_total &&
           (c->recorded_mask & (1U << c->rounds_completed))) c->rounds_completed++;
}

int championship_record_race(Championship *c, unsigned int round_index, const unsigned int places[CHAMPIONSHIP_MAX_RACERS])
{
    unsigned int i, j, seen = 0U, bit;
    if (!c || !places || round_index >= c->rounds_total) return 0;
    bit = 1U << round_index;
    if (c->recorded_mask & bit) return 0;
    /* Reject incomplete or duplicated finishing orders before mutating scores. */
    for (i = 0U; i < CHAMPIONSHIP_MAX_RACERS; ++i) {
        if (places[i] < 1U || places[i] > CHAMPIONSHIP_MAX_RACERS) return 0;
        for (j = 0U; j < i; ++j) if (places[j] == places[i]) return 0;
        seen |= 1U << (places[i] - 1U);
    }
    if (seen != 0xffU) return 0;
    for (i = 0U; i < CHAMPIONSHIP_MAX_RACERS; ++i) {
        unsigned int racer = i;
        unsigned int place = places[racer];
        c->points[racer] += championship_points_for_place(place);
        c->place_counts[racer][place - 1U]++;
    }
    c->recorded_mask |= bit;
    update_rounds_completed(c);
    return 1;
}

int championship_record(Championship *c, unsigned int round_index, unsigned int racer_index, unsigned int place)
{
    unsigned int bit;
    if (!c || round_index >= c->rounds_total || racer_index >= CHAMPIONSHIP_MAX_RACERS || place < 1U || place > CHAMPIONSHIP_MAX_RACERS) return 0;
    bit = 1U << round_index;
    if (c->recorded_mask & bit) return 0;
    c->recorded_mask |= bit;
    c->points[racer_index] += championship_points_for_place(place);
    c->place_counts[racer_index][place - 1U]++;
    update_rounds_completed(c);
    return 1;
}

static int racer_precedes(const Championship *c, unsigned int a, unsigned int b)
{
    int place;
    if (c->points[a] != c->points[b]) return c->points[a] > c->points[b];
    /* Official-style tie-break: most wins, then most second places, etc. */
    for (place = 0; place < (int)CHAMPIONSHIP_MAX_RACERS; ++place) {
        if (c->place_counts[a][place] != c->place_counts[b][place])
            return c->place_counts[a][place] > c->place_counts[b][place];
    }
    return a < b; /* deterministic order for a complete tie */
}

void championship_standings(const Championship *c, unsigned int order[CHAMPIONSHIP_MAX_RACERS])
{
    unsigned int i, j;
    if (!order) return;
    for (i = 0U; i < CHAMPIONSHIP_MAX_RACERS; ++i) order[i] = i;
    if (!c) return;
    for (i = 0U; i < CHAMPIONSHIP_MAX_RACERS; ++i) {
        for (j = i + 1U; j < CHAMPIONSHIP_MAX_RACERS; ++j) {
            if (racer_precedes(c, order[j], order[i])) {
                unsigned int swap = order[i]; order[i] = order[j]; order[j] = swap;
            }
        }
    }
}

unsigned int championship_winner(const Championship *c)
{
    unsigned int order[CHAMPIONSHIP_MAX_RACERS];
    championship_standings(c, order);
    return order[0];
}
