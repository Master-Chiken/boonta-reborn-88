#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "career_save.h"

int main(void)
{
    CareerProfile p, loaded;
    unsigned char bytes[CAREER_SAVE_BYTES];
    career_profile_init(&p);
    assert(career_profile_record_race(&p, 0U, 1U, 42.125f, 0));
    assert(career_profile_record_race(&p, 24U, 3U, 51.250f, 0));
    assert(career_profile_record_race(&p, 0U, 2U, 40.500f, 1));
    assert(career_profile_record_time_trial(&p, 2U, 38.750f));
    assert(career_profile_record_time_trial(&p, 2U, 39.250f)); /* slower trial must not replace record */
    p.credits = 2450U;
    p.upgrade_levels[0] = 2U; p.upgrade_levels[1] = 1U;
    assert(p.races_completed == 5U && p.race_wins == 1U && p.championships_won == 1U);
    assert(p.best_lap_ms[2] == 38750U && (p.best_lap_mask & (1U << 2U)) != 0U);
    assert(p.best_lap_ms[0] == 40500U && p.best_lap_ms[24] == 51250U);
    assert((p.best_lap_mask & 1U) != 0U && (p.best_lap_mask & (1U << 24)) != 0U);
    assert(!career_profile_record_time_trial(&p, 25U, 30.0f));
    assert(!career_profile_record_time_trial(NULL, 0U, 30.0f));
    assert(!career_profile_record_race(&p, 25U, 1U, 30.0f, 0));
    assert(!career_profile_record_race(&p, 1U, 9U, 30.0f, 0));

    career_save_encode(&p, bytes);
    memset(&loaded, 0xA5, sizeof(loaded));
    assert(career_save_decode(&loaded, bytes));
    assert(loaded.races_completed == p.races_completed);
    assert(loaded.race_wins == p.race_wins);
    assert(loaded.championships_won == p.championships_won);
    assert(loaded.best_lap_mask == p.best_lap_mask);
    assert(loaded.best_lap_ms[0] == 40500U && loaded.best_lap_ms[24] == 51250U);
    assert(loaded.credits == 2450U && loaded.upgrade_levels[0] == 2U && loaded.upgrade_levels[1] == 1U);

    bytes[40] ^= 0x40U;
    assert(!career_save_decode(&loaded, bytes)); /* CRC catches corruption */
    career_save_encode(&p, bytes);
    bytes[7] = 3U;
    assert(!career_save_decode(&loaded, bytes)); /* unsupported version */
    career_save_encode(&p, bytes);
    memset(bytes, 0, 4U);
    assert(!career_save_decode(&loaded, bytes)); /* invalid signature */

    puts("PASS: career statistics, per-track best laps, versioning and save corruption checks");
    return 0;
}
