#ifndef SWE1R_CAREER_SAVE_H
#define SWE1R_CAREER_SAVE_H

#include <stdint.h>

#define CAREER_TRACK_COUNT 25U
#define CAREER_SAVE_BYTES 8192U
#define CAREER_SAVE_VERSION 2U

typedef struct {
    uint32_t races_completed;
    uint32_t race_wins;
    uint32_t championships_won;
    uint32_t best_lap_mask;
    uint32_t best_lap_ms[CAREER_TRACK_COUNT];
    uint32_t credits;
    unsigned char upgrade_levels[4]; /* speed, acceleration, handling, boost */
} CareerProfile;

void career_profile_init(CareerProfile *profile);
int career_profile_record_race(CareerProfile *profile, unsigned int track_index,
                               unsigned int finishing_place, float best_lap_seconds,
                               int championship_won);
/* Record a completed solo time trial: race count and best lap, but no race win. */
int career_profile_record_time_trial(CareerProfile *profile, unsigned int track_index,
                                     float best_lap_seconds);
void career_save_encode(const CareerProfile *profile, unsigned char out[CAREER_SAVE_BYTES]);
int career_save_decode(CareerProfile *profile, const unsigned char in[CAREER_SAVE_BYTES]);
/* Returns 1 if a GameCube memory card was read/written, otherwise 0. */
int career_card_load(CareerProfile *profile);
int career_card_store(const CareerProfile *profile);

#endif
