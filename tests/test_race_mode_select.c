#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "race_mode_select.h"

int main(void)
{
    RaceSelectMode mode = RACE_SELECT_SINGLE;
    assert(strcmp(race_select_mode_label(mode), "MODE: SINGLE RACE") == 0);
    mode = race_select_mode_next(mode);
    assert(mode == RACE_SELECT_CHAMPIONSHIP);
    assert(strcmp(race_select_mode_label(mode), "MODE: CHAMPIONSHIP") == 0);
    mode = race_select_mode_next(mode);
    assert(mode == RACE_SELECT_TIME_TRIAL);
    assert(strcmp(race_select_mode_label(mode), "MODE: TIME TRIAL") == 0);
    mode = race_select_mode_next(mode);
    assert(mode == RACE_SELECT_MIRROR_CUP);
    assert(strcmp(race_select_mode_label(mode), "MODE: BONUS MIRROR CUP") == 0);
    mode = race_select_mode_next(mode);
    assert(mode == RACE_SELECT_SINGLE);
    assert(race_select_mode_next((RaceSelectMode)99) == RACE_SELECT_SINGLE);
    puts("PASS: single race, championship, time trial and bonus Mirror Cup selection cycle");
    return 0;
}
