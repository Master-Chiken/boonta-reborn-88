#ifndef SWE1R_RACE_STANDINGS_H
#define SWE1R_RACE_STANDINGS_H

#ifdef __cplusplus
extern "C" {
#endif

#define RACE_STANDINGS_MAX_RACERS 8U

/* Convert a lap counter and normalized track progress into comparable race progress.
   lap==0 is supported for racers staged just before the start/finish line. */
float race_standings_progress(unsigned int lap, float normalized_progress);

/* Count racers strictly ahead of the player. Ties deliberately keep the player's place. */
unsigned int race_standings_player_place(float player_progress,
                                        const float *opponent_progress,
                                        unsigned int opponent_count);

/* Stable finish order: places[racer_index] is a unique 1-based finishing place.
   Equal progress retains the original input order. */
void race_standings_rank(const float *progress, unsigned int racer_count,
                         unsigned int *places);

#ifdef __cplusplus
}
#endif
#endif
