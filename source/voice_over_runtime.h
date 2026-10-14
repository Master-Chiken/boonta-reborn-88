#ifndef SWE1R_VOICE_OVER_RUNTIME_H
#define SWE1R_VOICE_OVER_RUNTIME_H

#include "voice_over.h"

/* Lightweight event bridge. It drives English subtitles and cue scheduling;
 * platform audio playback is intentionally kept separate. */
typedef struct {
    int previous_phase;
    unsigned int previous_lap;
    float previous_damage;
    float previous_boost;
    float subtitle_remaining;
    VoiceOverCue active_cue;
    int active_valid;
    int initialised;
    int paused; /* Freeze event transitions and subtitle time while gameplay is paused. */
} VoiceOverRuntime;

void voice_over_runtime_init(VoiceOverRuntime *runtime);
void voice_over_runtime_set_paused(VoiceOverRuntime *runtime, int paused);
void voice_over_runtime_update(VoiceOverRuntime *runtime, int phase,
                               unsigned int lap, unsigned int target_laps,
                               float damage, float boost_energy, float dt);
const char *voice_over_runtime_subtitle(const VoiceOverRuntime *runtime);

#endif
