#include <assert.h>
#include <string.h>
#include "game_text.h"

int main(void)
{
    assert(strcmp(game_language_name(), "English") == 0);
    assert(strcmp(game_text(GAME_TEXT_TITLE), "STAR WARS RACER") == 0);
    assert(strcmp(game_text(GAME_TEXT_SELECT_POD_TRACK), "CHOOSE YOUR POD AND TRACK") == 0);
    assert(strcmp(game_text(GAME_TEXT_PAUSED), "PAUSED") == 0);
    assert(strcmp(game_text(GAME_TEXT_RESUME), "A: RESUME") == 0);
    assert(strcmp(game_text(GAME_TEXT_QUIT_RACE), "B: QUIT RACE") == 0);
    assert(strcmp(game_text((GameTextId)999), "") == 0);
    return 0;
}
