#ifndef SWE1R_CHAMPIONSHIP_H
#define SWE1R_CHAMPIONSHIP_H

#define CHAMPIONSHIP_MAX_RACERS 8U
#define CHAMPIONSHIP_MAX_ROUNDS 25U

typedef struct {
    unsigned int rounds_total;
    unsigned int rounds_completed;
    unsigned int points[CHAMPIONSHIP_MAX_RACERS];
    /* Number of finishes in each place: place_counts[racer][place - 1]. */
    unsigned int place_counts[CHAMPIONSHIP_MAX_RACERS][CHAMPIONSHIP_MAX_RACERS];
    unsigned int recorded_mask;
} Championship;

void championship_init(Championship *championship, unsigned int rounds_total);
/* Record a race once; place is 1-based. Returns 1 when recorded, 0 if invalid/duplicate. */
int championship_record(Championship *championship, unsigned int round_index, unsigned int racer_index, unsigned int place);
/* Records all eight racers in finishing order; places[] contains 1-based places. */
int championship_record_race(Championship *championship, unsigned int round_index, const unsigned int places[CHAMPIONSHIP_MAX_RACERS]);
unsigned int championship_points_for_place(unsigned int place);
unsigned int championship_winner(const Championship *championship);
/* Sort racer indices by points, wins, then counts of each finishing place. */
void championship_standings(const Championship *championship, unsigned int order[CHAMPIONSHIP_MAX_RACERS]);

#endif
