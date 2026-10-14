#include <assert.h>
#include <stdio.h>
#include "pause_state.h"

int main(void)
{
    int paused = 0;
    assert(pause_state_update(0, 0, 0, 0, &paused) == PAUSE_ACTION_NONE);
    assert(pause_state_update(0, 1, 0, 0, &paused) == PAUSE_ACTION_EXIT_GAME);
    assert(paused == 0);

    assert(pause_state_update(1, 1, 0, 0, &paused) == PAUSE_ACTION_NONE);
    assert(paused == 1);
    assert(pause_state_update(1, 0, 0, 0, &paused) == PAUSE_ACTION_NONE);
    assert(paused == 1); /* no input: pause persists */
    assert(pause_state_update(1, 0, 1, 0, &paused) == PAUSE_ACTION_NONE);
    assert(paused == 0); /* A resumes */

    assert(pause_state_update(1, 1, 0, 0, &paused) == PAUSE_ACTION_NONE);
    assert(paused == 1);
    assert(pause_state_update(1, 0, 0, 1, &paused) == PAUSE_ACTION_RETURN_TO_SELECT);
    assert(paused == 0); /* B abandons race and returns to selection */

    paused = 1;
    assert(pause_state_update(0, 0, 0, 0, &paused) == PAUSE_ACTION_NONE);
    assert(paused == 0); /* no stale pause on selection */
    assert(pause_state_update(1, 0, 0, 1, &paused) == PAUSE_ACTION_NONE);
    assert(paused == 0); /* B does not abandon an unpaused race */
    puts("PASS: pause/resume, abandon and selection exit transitions");
    return 0;
}
