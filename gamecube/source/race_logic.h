#ifndef BOONTA_RACE_LOGIC_H
#define BOONTA_RACE_LOGIC_H

typedef struct RaceState {
    float speed;
    float lane_offset;
    float angle;
    float boost_energy;
    float engine_heat;
    int completed_laps;
    int paused;
    int finished;
    int boost_active;
} RaceState;

typedef struct RaceInput {
    int accelerate;
    int brake;
    int boost;
    int left;
    int right;
    int pause_pressed;
    int reset_pressed;
} RaceInput;

void race_reset(RaceState *state);
void race_update(RaceState *state, const RaceInput *input);

#endif
