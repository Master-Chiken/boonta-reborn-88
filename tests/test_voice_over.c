#include <assert.h>
#include <string.h>
#include "voice_over.h"
int main(void) {
    VoiceOverCue out = VO_CUE_COUNT;
    const VoiceOverEntry *e = voice_over_entry(VO_CUE_FINAL_LAP);
    assert(e && strcmp(e->asset_path, "assets/voice_en/final_lap.wav") == 0);
    assert(strstr(e->subtitle, "Final lap") != 0);
    assert(voice_over_entry((VoiceOverCue)99) == 0);
    voice_over_clear();
    assert(voice_over_pending() == 0);
    assert(!voice_over_dequeue(&out));
    for (int i=0; i<VO_QUEUE_CAPACITY; ++i) assert(voice_over_enqueue((VoiceOverCue)(i % VO_CUE_COUNT)));
    assert(!voice_over_enqueue(VO_CUE_RACE_START));
    assert(voice_over_pending() == VO_QUEUE_CAPACITY);
    for (int i=0; i<VO_QUEUE_CAPACITY; ++i) assert(voice_over_dequeue(&out));
    assert(!voice_over_dequeue(&out));
    assert(voice_over_enqueue(VO_CUE_RACE_FINISHED));
    assert(voice_over_dequeue(&out) && out == VO_CUE_RACE_FINISHED);
    assert(!voice_over_dequeue(0));
    return 0;
}
