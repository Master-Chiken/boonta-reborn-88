#ifndef BOONTA_REBORN_PAUSE_STATE_H
#define BOONTA_REBORN_PAUSE_STATE_H

/*
 * Pure pause-state transition used by the GameCube input loop.
 * reset_pressed takes precedence so Y always resets/unpauses the run.
 */
static inline int boonta_pause_state_next(int paused, int start_pressed, int reset_pressed)
{
    if (reset_pressed) {
        return 0;
    }
    if (start_pressed) {
        return paused == 0;
    }
    return paused != 0;
}

#endif
