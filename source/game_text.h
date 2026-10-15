#ifndef SWE1R_GAME_TEXT_H
#define SWE1R_GAME_TEXT_H

/* Step 47: the GameCube port ships with English as its sole/default UI language. */
typedef enum {
    GAME_TEXT_TITLE = 0,
    GAME_TEXT_SELECT_POD_TRACK,
    GAME_TEXT_TRACK,
    GAME_TEXT_POD,
    GAME_TEXT_PAUSED,
    GAME_TEXT_RESUME,
    GAME_TEXT_QUIT_RACE,
    GAME_TEXT_FINISH,
    GAME_TEXT_TIME_TRIAL,
    GAME_TEXT_DIRECTION_NORMAL,
    GAME_TEXT_DIRECTION_REVERSE,
    GAME_TEXT_AI_EASY,
    GAME_TEXT_AI_NORMAL,
    GAME_TEXT_AI_HARD,
    GAME_TEXT_COUNT
} GameTextId;

const char *game_text(GameTextId id);
const char *game_language_name(void);

#endif
