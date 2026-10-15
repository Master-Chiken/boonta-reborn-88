#include "race_standings.h"

float race_standings_progress(unsigned int lap, float normalized_progress)
{
    return (float)lap - 1.0f + normalized_progress;
}

unsigned int race_standings_player_place(float player_progress,
                                        const float *opponent_progress,
                                        unsigned int opponent_count)
{
    unsigned int place = 1U;
    unsigned int i;
    if (opponent_progress == 0) return place;
    if (opponent_count > RACE_STANDINGS_MAX_RACERS - 1U)
        opponent_count = RACE_STANDINGS_MAX_RACERS - 1U;
    for (i = 0U; i < opponent_count; ++i) {
        if (opponent_progress[i] > player_progress) ++place;
    }
    return place;
}

void race_standings_rank(const float *progress, unsigned int racer_count,
                         unsigned int *places)
{
    unsigned int order[RACE_STANDINGS_MAX_RACERS];
    unsigned int i, j;
    if (progress == 0 || places == 0) return;
    if (racer_count > RACE_STANDINGS_MAX_RACERS)
        racer_count = RACE_STANDINGS_MAX_RACERS;
    for (i = 0U; i < racer_count; ++i) order[i] = i;
    /* Stable insertion sort: unlike selection-sort swaps, this preserves ties. */
    for (i = 1U; i < racer_count; ++i) {
        unsigned int racer = order[i];
        j = i;
        while (j > 0U && progress[racer] > progress[order[j-1U]]) {
            order[j] = order[j-1U];
            --j;
        }
        order[j] = racer;
    }
    for (i = 0U; i < racer_count; ++i) places[order[i]] = i + 1U;
}
