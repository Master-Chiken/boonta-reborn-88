#include "race_mode_select.h"

RaceSelectMode race_select_mode_next(RaceSelectMode mode)
{
    if (mode < RACE_SELECT_SINGLE || mode >= RACE_SELECT_MODE_COUNT)
        return RACE_SELECT_SINGLE;
    return (RaceSelectMode)(((unsigned int)mode + 1U) % (unsigned int)RACE_SELECT_MODE_COUNT);
}

const char *race_select_mode_label(RaceSelectMode mode)
{
    switch (mode) {
        case RACE_SELECT_CHAMPIONSHIP: return "MODE: CHAMPIONSHIP";
        case RACE_SELECT_TIME_TRIAL: return "MODE: TIME TRIAL";
        case RACE_SELECT_MIRROR_CUP: return "MODE: BONUS MIRROR CUP";
        case RACE_SELECT_SINGLE:
        default: return "MODE: SINGLE RACE";
    }
}
