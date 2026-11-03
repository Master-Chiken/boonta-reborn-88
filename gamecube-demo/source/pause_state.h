#ifndef BOONTA_REBORN_PAUSE_STATE_H
#define BOONTA_REBORN_PAUSE_STATE_H

/*
 * Reset Y from any race state, and let Start restart only after the finish.
 * This check must run before the finished/paused simulation freeze.
 */
static inline int boonta_race_should_reset(int race_finished, int start_pressed,
                                            int reset_pressed)
{
    if (reset_pressed) return 1;
    if (race_finished && start_pressed) return 1;
    return 0;
}

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
