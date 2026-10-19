#include <assert.h>
#include <stdio.h>

#include "../source/pause_state.h"

int main(void)
{
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

    /* Test full sequence: initial (0) -> pause (1) -> continue paused (1) -> unpause (0) -> release/running (0) -> pause (1) -> reset (0). */
    {
        int state = 0;
        state = boonta_pause_state_next(state, 1, 0); /* Start pressed -> paused */
        assert(state == 1);
        state = boonta_pause_state_next(state, 0, 0); /* No buttons -> remains paused */
        assert(state == 1);
        state = boonta_pause_state_next(state, 1, 0); /* Start pressed again -> unpaused */
        assert(state == 0);
        state = boonta_pause_state_next(state, 0, 0); /* No buttons -> remains running */
        assert(state == 0);
        state = boonta_pause_state_next(state, 1, 0); /* Start pressed -> paused */
        assert(state == 1);
        state = boonta_pause_state_next(state, 0, 1); /* Y reset pressed -> unpaused */
        assert(state == 0);
    }

    puts("pause-state tests passed");
    return 0;
}
