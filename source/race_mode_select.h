#ifndef SWE1R_RACE_MODE_SELECT_H
#define SWE1R_RACE_MODE_SELECT_H

typedef enum {
    RACE_SELECT_SINGLE = 0,
    RACE_SELECT_CHAMPIONSHIP = 1,
    RACE_SELECT_TIME_TRIAL = 2,
    RACE_SELECT_MIRROR_CUP = 3, /* Bonus championship: reverse tracks + hard AI. */
    RACE_SELECT_MODE_COUNT = 4
} RaceSelectMode;

/* Cycles the core modes and the bonus Mirror Cup. */
RaceSelectMode race_select_mode_next(RaceSelectMode mode);
const char *race_select_mode_label(RaceSelectMode mode);

#endif
