#ifndef SWE1R_VOICE_OVER_H
#define SWE1R_VOICE_OVER_H

/* English voice-over cue catalog and small FIFO for race events.
 * Audio files are generated original placeholder narration, not ripped game audio.
 * The cue queue is platform-independent; actual GameCube playback is a separate integration step.
 */
typedef enum {
    VO_CUE_RACE_START = 0,
    VO_CUE_LAP_ONE,
    VO_CUE_FINAL_LAP,
    VO_CUE_PLAYER_DAMAGED,
    VO_CUE_BOOST_READY,
    VO_CUE_PLAYER_OVERTAKEN,
    VO_CUE_PLAYER_OVERTAKES,
    VO_CUE_RACE_FINISHED,
    VO_CUE_COUNT
} VoiceOverCue;

typedef struct {
    VoiceOverCue cue;
    const char *asset_path;
    const char *subtitle;
} VoiceOverEntry;

#define VO_QUEUE_CAPACITY 8

const VoiceOverEntry *voice_over_entry(VoiceOverCue cue);
int voice_over_enqueue(VoiceOverCue cue);
int voice_over_dequeue(VoiceOverCue *cue_out);
void voice_over_clear(void);
unsigned int voice_over_pending(void);

#endif
