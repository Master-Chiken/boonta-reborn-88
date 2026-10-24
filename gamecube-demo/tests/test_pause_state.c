#include <assert.h>
#include <stdio.h>

#include "../source/pause_state.h"

int main(void)
{
    /* Race reset rules: Y always resets; Start restarts a finished race. */
    assert(boonta_race_should_reset(0, 0, 0) == 0);
    assert(boonta_race_should_reset(0, 1, 0) == 0);
    assert(boonta_race_should_reset(0, 0, 1) == 1);
    assert(boonta_race_should_reset(0, 1, 1) == 1);

    assert(boonta_race_should_reset(1, 0, 0) == 0);
    assert(boonta_race_should_reset(1, 1, 0) == 1);
    assert(boonta_race_should_reset(1, 0, 1) == 1);
    assert(boonta_race_should_reset(1, 1, 1) == 1);

    /* No button press preserves the current state. */
    assert(boonta_pause_state_next(0, 0, 0) == 0);
    assert(boonta_pause_state_next(1, 0, 0) == 1);

    /* Start toggles both running -> paused and paused -> running. */
    assert(boonta_pause_state_next(0, 1, 0) == 1);
    assert(boonta_pause_state_next(1, 1, 0) == 0);

    /* Y resets/unpauses from either state. */
    assert(boonta_pause_state_next(0, 0, 1) == 0);
    assert(boonta_pause_state_next(1, 0, 1) == 0);

    /* If Start and Y are pressed together, reset/unpause takes precedence. */
    assert(boonta_pause_state_next(1, 1, 1) == 0);
    assert(boonta_pause_state_next(0, 1, 1) == 0);

    puts("pause-state tests passed");
    return 0;
}
