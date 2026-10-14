#include "pause_state.h"

PauseAction pause_state_update(int in_race, int start_pressed,
                               int confirm_pressed, int back_pressed,
                               int *paused)
{
    if (paused == 0) return PAUSE_ACTION_NONE;
    if (!in_race) {
        *paused = 0;
        return start_pressed ? PAUSE_ACTION_EXIT_GAME : PAUSE_ACTION_NONE;
    }
    if (start_pressed) {
        *paused = !*paused;
        return PAUSE_ACTION_NONE;
    }
    if (*paused && confirm_pressed) {
        *paused = 0;
        return PAUSE_ACTION_NONE;
    }
    if (*paused && back_pressed) {
        *paused = 0;
        return PAUSE_ACTION_RETURN_TO_SELECT;
    }
    return PAUSE_ACTION_NONE;
}
