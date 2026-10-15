#ifndef SWE1R_PAUSE_STATE_H
#define SWE1R_PAUSE_STATE_H

/* Input-driven pause state, deliberately independent of libogc for host tests. */
typedef enum {
    PAUSE_ACTION_NONE = 0,
    PAUSE_ACTION_EXIT_GAME,
    PAUSE_ACTION_RETURN_TO_SELECT
} PauseAction;

/*
 * Selection screen: START exits to the loader.
 * During a race: START toggles pause; A resumes; B abandons the current race
 * and returns to selection. Button arguments are one-frame press events.
 */
PauseAction pause_state_update(int in_race, int start_pressed,
                               int confirm_pressed, int back_pressed,
                               int *paused);

#endif
