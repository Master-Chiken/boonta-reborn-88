#include "voice_over_runtime.h"

#define VO_PERCENT_MAX 100.0f

#define VO_SUBTITLE_SECONDS 2.8f
#define VO_PHASE_COUNTDOWN 0
#define VO_PHASE_RUNNING 1
#define VO_PHASE_FINISHED 2

static float clamp_dt(float dt)
{
    /* A NaN frame delta evades ordinary < and > comparisons and would make
       subtitle_remaining permanently NaN. Ignore it; infinities are bounded
       by the normal clamps below. */
    if (dt != dt) return 0.0f;
    if (dt < 0.0f) return 0.0f;
    if (dt > 0.25f) return 0.25f;
    return dt;
}

static float clamp_percent(float value, float fallback)
{
    /* Preserve the last known good meter if input data is NaN. Infinite and
       out-of-range values are bounded to the documented 0..100 range. */
    if (value != value) value = fallback;
    if (value < 0.0f) return 0.0f;
    if (value > VO_PERCENT_MAX) return VO_PERCENT_MAX;
    return value;
}

void voice_over_runtime_init(VoiceOverRuntime *runtime)
{
    if (!runtime) return;
    runtime->previous_phase = VO_PHASE_COUNTDOWN;
    runtime->previous_lap = 0U;
    runtime->previous_damage = 0.0f;
    runtime->previous_boost = 0.0f;
    runtime->subtitle_remaining = 0.0f;
    runtime->active_cue = VO_CUE_RACE_START;
    runtime->active_valid = 0;
    runtime->initialised = 0;
    runtime->paused = 0;
    voice_over_clear();
}

void voice_over_runtime_set_paused(VoiceOverRuntime *runtime, int paused)
{
    if (!runtime) return;
    runtime->paused = paused != 0;
}

static void enqueue_if_room(VoiceOverCue cue)
{
    (void)voice_over_enqueue(cue);
}

void voice_over_runtime_update(VoiceOverRuntime *runtime, int phase,
                               unsigned int lap, unsigned int target_laps,
                               float damage, float boost_energy, float dt)
{
    VoiceOverCue next;
    if (!runtime || runtime->paused) return;
    dt = clamp_dt(dt);
    damage = clamp_percent(damage, runtime->initialised ? runtime->previous_damage : 0.0f);
    boost_energy = clamp_percent(boost_energy,
                                 runtime->initialised ? runtime->previous_boost : 0.0f);
    if (!runtime->initialised) {
        runtime->previous_phase = phase;
        runtime->previous_lap = lap;
        runtime->previous_damage = damage;
        runtime->previous_boost = boost_energy;
        runtime->initialised = 1;
    } else {
        if (runtime->previous_phase != VO_PHASE_RUNNING && phase == VO_PHASE_RUNNING) {
            enqueue_if_room(VO_CUE_RACE_START);
            if (lap <= 1U) enqueue_if_room(VO_CUE_LAP_ONE);
        }
        if (phase == VO_PHASE_RUNNING && lap > runtime->previous_lap) {
            if (target_laps > 0U && lap >= target_laps)
                enqueue_if_room(VO_CUE_FINAL_LAP);
            else if (lap == 1U)
                enqueue_if_room(VO_CUE_LAP_ONE);
        }
        if (phase == VO_PHASE_RUNNING && damage >= 45.0f && runtime->previous_damage < 45.0f)
            enqueue_if_room(VO_CUE_PLAYER_DAMAGED);
        if (phase == VO_PHASE_RUNNING && boost_energy >= 99.0f && runtime->previous_boost < 99.0f)
            enqueue_if_room(VO_CUE_BOOST_READY);
        if (runtime->previous_phase != VO_PHASE_FINISHED && phase == VO_PHASE_FINISHED)
            enqueue_if_room(VO_CUE_RACE_FINISHED);
        runtime->previous_phase = phase;
        runtime->previous_lap = lap;
        runtime->previous_damage = damage;
        runtime->previous_boost = boost_energy;
    }

    if (runtime->subtitle_remaining > 0.0f) {
        runtime->subtitle_remaining -= dt;
        if (runtime->subtitle_remaining < 0.0f) runtime->subtitle_remaining = 0.0f;
    }
    if (runtime->subtitle_remaining <= 0.0f && voice_over_dequeue(&next)) {
        runtime->active_cue = next;
        runtime->active_valid = 1;
        runtime->subtitle_remaining = VO_SUBTITLE_SECONDS;
    }
}

const char *voice_over_runtime_subtitle(const VoiceOverRuntime *runtime)
{
    const VoiceOverEntry *entry;
    if (!runtime || !runtime->active_valid || runtime->subtitle_remaining <= 0.0f) return 0;
    entry = voice_over_entry(runtime->active_cue);
    return entry ? entry->subtitle : 0;
}
