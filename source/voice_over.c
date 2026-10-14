#include "voice_over.h"

static const VoiceOverEntry g_voice_over[VO_CUE_COUNT] = {
    { VO_CUE_RACE_START,       "assets/voice_en/race_start.wav",       "And they're off!" },
    { VO_CUE_LAP_ONE,          "assets/voice_en/lap_one.wav",          "Lap one." },
    { VO_CUE_FINAL_LAP,        "assets/voice_en/final_lap.wav",        "Final lap! Give it everything you've got!" },
    { VO_CUE_PLAYER_DAMAGED,   "assets/voice_en/player_damaged.wav",   "Pod damage detected. Watch your handling." },
    { VO_CUE_BOOST_READY,      "assets/voice_en/boost_ready.wav",      "Boost system ready." },
    { VO_CUE_PLAYER_OVERTAKEN, "assets/voice_en/player_overtaken.wav", "You've been passed! Get back in the race!" },
    { VO_CUE_PLAYER_OVERTAKES, "assets/voice_en/player_overtakes.wav", "Nice pass! Keep pushing!" },
    { VO_CUE_RACE_FINISHED,    "assets/voice_en/race_finished.wav",    "Race complete! Check the results." }
};

static VoiceOverCue g_queue[VO_QUEUE_CAPACITY];
static unsigned int g_head;
static unsigned int g_count;

const VoiceOverEntry *voice_over_entry(VoiceOverCue cue)
{
    if ((unsigned int)cue >= (unsigned int)VO_CUE_COUNT) return 0;
    return &g_voice_over[(unsigned int)cue];
}

int voice_over_enqueue(VoiceOverCue cue)
{
    unsigned int tail;
    if (!voice_over_entry(cue) || g_count >= VO_QUEUE_CAPACITY) return 0;
    tail = (g_head + g_count) % VO_QUEUE_CAPACITY;
    g_queue[tail] = cue;
    ++g_count;
    return 1;
}

int voice_over_dequeue(VoiceOverCue *cue_out)
{
    if (!cue_out || g_count == 0) return 0;
    *cue_out = g_queue[g_head];
    g_head = (g_head + 1U) % VO_QUEUE_CAPACITY;
    --g_count;
    return 1;
}

void voice_over_clear(void)
{
    g_head = 0;
    g_count = 0;
}

unsigned int voice_over_pending(void) { return g_count; }
