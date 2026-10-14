#include "game_text.h"

/* English is intentional: this build's menus, HUD and prompts are in English. */
static const char *const g_english_text[GAME_TEXT_COUNT] = {
    "STAR WARS RACER",
    "CHOOSE YOUR POD AND TRACK",
    "TRACK",
    "POD",
    "PAUSED",
    "A: RESUME",
    "B: QUIT RACE",
    "FINISH",
    "TIME TRIAL",
    "DIRECTION: NORMAL",
    "DIRECTION: REVERSE",
    "AI DIFFICULTY: EASY",
    "AI DIFFICULTY: NORMAL",
    "AI DIFFICULTY: HARD"
};

const char *game_text(GameTextId id)
{
    if ((unsigned int)id >= (unsigned int)GAME_TEXT_COUNT)
        return "";
    return g_english_text[(unsigned int)id];
}

const char *game_language_name(void)
{
    return "English";
}
