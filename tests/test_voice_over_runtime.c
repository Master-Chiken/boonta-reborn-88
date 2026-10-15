#include "voice_over_runtime.h"
#include <assert.h>
#include <math.h>
#include <string.h>

int main(void)
{
    VoiceOverRuntime runtime;
    const char *subtitle;
    voice_over_runtime_init(&runtime);
    voice_over_runtime_update(&runtime, 0, 1, 3, 0.0f, 0.0f, 1.0f / 60.0f);
    assert(voice_over_runtime_subtitle(&runtime) == 0);
    voice_over_runtime_update(&runtime, 1, 1, 3, 0.0f, 0.0f, 1.0f / 60.0f);
    subtitle = voice_over_runtime_subtitle(&runtime);
    assert(subtitle != 0 && strcmp(subtitle, "And they're off!") == 0);
    /* A large frame delta is clamped; it cannot instantly expire every cue. */
    voice_over_runtime_update(&runtime, 1, 1, 3, 0.0f, 0.0f, 10.0f);
    assert(voice_over_runtime_subtitle(&runtime) != 0);
    /* NaN must not poison the subtitle timer; a positive infinity is bounded. */
    {
        float before = runtime.subtitle_remaining;
        voice_over_runtime_update(&runtime, 1, 1, 3, 0.0f, 0.0f, NAN);
        assert(runtime.subtitle_remaining == before);
        assert(voice_over_runtime_subtitle(&runtime) != 0);
        voice_over_runtime_update(&runtime, 1, 1, 3, 0.0f, 0.0f, INFINITY);
        assert(runtime.subtitle_remaining >= 0.0f);
        assert(runtime.subtitle_remaining <= before);
        assert(voice_over_runtime_subtitle(&runtime) != 0);
    }
    /* Invalid meter values cannot poison threshold-crossing state. */
    voice_over_runtime_update(&runtime, 1, 1, 3, NAN, INFINITY, 0.01f);
    assert(runtime.previous_damage == 0.0f);
    assert(runtime.previous_boost == 100.0f);
    /* Trigger a damage announcement after the threshold crossing. */
    voice_over_runtime_update(&runtime, 1, 1, 3, 46.0f, 20.0f, 0.05f);
    /* Pause freezes both subtitle time and cue transitions/queue consumption. */
    assert(voice_over_pending() <= VO_QUEUE_CAPACITY);
    assert(voice_over_runtime_subtitle(&runtime) != 0);
    {
        float subtitle_before = runtime.subtitle_remaining;
        int phase_before = runtime.previous_phase;
        unsigned int lap_before = runtime.previous_lap;
        unsigned int pending_before = voice_over_pending();
        int active_cue_before = (int)runtime.active_cue;
        unsigned int i;
        voice_over_runtime_set_paused(&runtime, 1);
        for (i = 0U; i < 30U; ++i)
            voice_over_runtime_update(&runtime, 2, 3, 3, 90.0f, 100.0f, 0.25f);
        assert(runtime.paused == 1);
        assert(runtime.subtitle_remaining == subtitle_before);
        assert(runtime.previous_phase == phase_before);
        assert(runtime.previous_lap == lap_before);
        assert((int)runtime.active_cue == active_cue_before);
        assert(voice_over_pending() == pending_before);
        assert(voice_over_runtime_subtitle(&runtime) != 0);
        voice_over_runtime_set_paused(&runtime, 0);
        voice_over_runtime_update(&runtime, 1, 1, 3, 46.0f, 20.0f, 0.05f);
        assert(runtime.subtitle_remaining < subtitle_before);
    }
    /* Finish transition schedules a race-complete cue after resume. */
    voice_over_runtime_update(&runtime, 2, 3, 3, 46.0f, 20.0f, 0.05f);
    assert(voice_over_pending() <= VO_QUEUE_CAPACITY);
    /* The setter is safe for a null pointer and normalises arbitrary truthy values. */
    voice_over_runtime_set_paused(0, 1);
    voice_over_runtime_set_paused(&runtime, -42);
    assert(runtime.paused == 1);
    voice_over_runtime_set_paused(&runtime, 0);
    assert(runtime.paused == 0);
    return 0;
}
