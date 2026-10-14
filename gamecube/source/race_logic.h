#ifndef BOONTA_RACE_LOGIC_H
#define BOONTA_RACE_LOGIC_H

#define RACE_OPPONENT_COUNT 3

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
    float opponent_angles[RACE_OPPONENT_COUNT];
    float opponent_lanes[RACE_OPPONENT_COUNT];
    float opponent_speeds[RACE_OPPONENT_COUNT];
    int opponent_laps[RACE_OPPONENT_COUNT];
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
/* delta_seconds is measured wall time and is clamped to protect lap logic from stalls. */
void race_update_dt(RaceState *state, const RaceInput *input, float delta_seconds);
int race_position(const RaceState *state);

#endif
