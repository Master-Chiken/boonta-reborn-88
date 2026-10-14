#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "rival_ai.h"

int main(void)
{
    RivalAIState rivals[3];
    memset(rivals, 0, sizeof(rivals));
    rivals[0].difficulty_scale = rivals[1].difficulty_scale = rivals[2].difficulty_scale = 1.0f;
    rival_ai_set_difficulty(rivals, 3U, 0U);
    assert(rivals[0].difficulty_scale > 0.87f && rivals[0].difficulty_scale < 0.89f);
    assert(rivals[1].difficulty_scale == rivals[0].difficulty_scale);
    rival_ai_set_difficulty(rivals, 3U, 2U);
    assert(rivals[2].difficulty_scale > 1.11f && rivals[2].difficulty_scale < 1.13f);
    rival_ai_set_difficulty(rivals, 3U, 99U);
    assert(rivals[0].difficulty_scale == 1.0f);
    rival_ai_set_difficulty(NULL, 3U, 2U);
    puts("PASS: AI difficulty scales, invalid-level fallback, and null safety");
    return 0;
}
