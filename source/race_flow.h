#ifndef SWE1R_RACE_FLOW_H
#define SWE1R_RACE_FLOW_H

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    RACE_PHASE_COUNTDOWN = 0,
    RACE_PHASE_RUNNING = 1,
    RACE_PHASE_FINISHED = 2
} RacePhase;

typedef struct {
    RacePhase phase;
    float countdown_remaining;
    float race_elapsed;
    unsigned int target_laps;
} RaceFlow;

/* Starts with a 3 / 2 / 1 / GO countdown. */
void race_flow_init(RaceFlow *flow, unsigned int target_laps);
void race_flow_update(RaceFlow *flow, float dt, unsigned int player_lap);
/* Returns 3, 2, 1 while counting down; 0 during GO and once racing begins. */
int race_flow_countdown_label(const RaceFlow *flow);

#ifdef __cplusplus
}
#endif
#endif
