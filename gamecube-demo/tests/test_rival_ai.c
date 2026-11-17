#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "../source/rival_ai.h"
#include "../source/gameplay_state.h"
#include "../source/route_graph_sampling.h"

static int nearf_ai(float a, float b)
{
    return fabsf(a - b) < 0.0001f;
}

static void lane_preference_is_deterministic(void)
{
    const float z[3] = {-18.0f, -34.0f, -50.0f};
    const float lateral[3] = {0.0f, 0.0f, 0.0f};
    assert(nearf_ai(boonta_rival_ai_target_lateral(0U, -18.0f, 0.0f, 0.0f, z, lateral, 3U, 0.0f, 3.4f), -1.25f));
    assert(nearf_ai(boonta_rival_ai_target_lateral(1U, -34.0f, 0.0f, 0.0f, z, lateral, 3U, 0.0f, 3.4f), 0.0f));
    assert(nearf_ai(boonta_rival_ai_target_lateral(2U, -50.0f, 0.0f, 0.0f, z, lateral, 3U, 0.0f, 3.4f), 1.25f));
}

static void player_avoidance_only_when_close(void)
{
    const float z[3] = {-40.0f, -2.0f, -50.0f};
    const float lateral[3] = {0.0f, 0.0f, 0.0f};
    float target = boonta_rival_ai_target_lateral(1U, -2.0f, 0.0f, -0.2f, z, lateral, 3U, 0.0f, 3.4f);
    assert(target > 0.0f);
    target = boonta_rival_ai_target_lateral(1U, -18.0f, 0.0f, -0.2f, z, lateral, 3U, 0.0f, 3.4f);
    assert(nearf_ai(target, 0.0f));

    /* A non-finite player position must not be treated as a real center-lane car. */
    target = boonta_rival_ai_target_lateral(1U, -2.0f, 0.0f, NAN, z, lateral, 3U, 0.0f, 3.4f);
    assert(nearf_ai(target, 0.0f));
}

static void nearby_rival_avoidance(void)
{
    const float z[3] = {-10.0f, -11.0f, -40.0f};
    const float lateral[3] = {0.1f, 0.0f, 0.0f};
    const float target = boonta_rival_ai_target_lateral(0U, -10.0f, 0.1f, 0.0f, z, lateral, 3U, 0.0f, 3.4f);
    assert(target > 0.1f);
}

static void movement_is_bounded_and_time_scaled(void)
{
    assert(nearf_ai(boonta_rival_ai_after_frame(0.0f, 1.0f, 1.0f), 0.035f));
    assert(nearf_ai(boonta_rival_ai_after_frame(0.0f, 1.0f, 2.0f), 0.070f));
    assert(nearf_ai(boonta_rival_ai_after_frame(0.0f, 1.0f, NAN), 0.0f));
    assert(nearf_ai(boonta_rival_ai_after_frame(2.0f, 4.0f, 1.0f), 2.035f));
    assert(nearf_ai(boonta_rival_ai_after_frame(-4.0f, -1.0f, 1.0f), -2.065f));
}

static void invalid_inputs_recover_safely(void)
{
    const float z[1] = {NAN};
    const float lateral[1] = {INFINITY};
    const float target = boonta_rival_ai_target_lateral(
        0U, NAN, NAN, INFINITY, z, lateral, 1U, 0.0f, 3.4f);
    assert(isfinite(target));
    assert(target >= -BOONTA_RIVAL_AI_LATERAL_LIMIT);
    assert(target <= BOONTA_RIVAL_AI_LATERAL_LIMIT);
}

static void signed_curvature_selects_inside_line(void)
{
    const float center_lane = boonta_rival_ai_target_line_lateral(1U, 0.0f, 3.4f);
    const float right_bend = boonta_rival_ai_target_line_lateral(1U, 0.10f, 3.4f);
    const float left_bend = boonta_rival_ai_target_line_lateral(1U, -0.10f, 3.4f);
    const float narrow_right_bend = boonta_rival_ai_target_line_lateral(1U, 0.10f, 2.2f);

    assert(nearf_ai(center_lane, 0.0f));
    assert(right_bend > center_lane);
    assert(left_bend < center_lane);
    assert(fabsf(narrow_right_bend) <= 1.55f);
    assert(right_bend <= 2.1f);
    assert(left_bend >= -2.1f);
}

static void signed_curvature_preserves_turn_direction(void)
{
    const float turns_right = boonta_rival_ai_signed_curvature_from_samples(
        0.0f, 0.0f, 0.0f, 2.0f, 1.0f, 4.0f);
    const float turns_left = boonta_rival_ai_signed_curvature_from_samples(
        0.0f, 0.0f, 0.0f, 2.0f, -1.0f, 4.0f);
    assert(turns_right > 0.0f);
    assert(turns_left < 0.0f);
    assert(nearf_ai(fabsf(turns_right), fabsf(turns_left)));
}

static void curvature_samples_are_measured_and_bounded(void)
{
    const float straight = boonta_rival_ai_curvature_from_samples(
        -2.0f, 0.0f, 0.0f, 0.0f, 2.0f, 0.0f);
    const float gentle_bend = boonta_rival_ai_curvature_from_samples(
        -2.0f, 0.0f, 0.0f, 0.0f, 1.93185165f, 0.51763809f);
    const float sharp_bend = boonta_rival_ai_curvature_from_samples(
        -2.0f, 0.0f, 0.0f, 0.0f, 0.0f, 2.0f);

    assert(nearf_ai(straight, 0.0f));
    assert(nearf_ai(gentle_bend, 0.1308997f));
    assert(nearf_ai(sharp_bend, 0.18f));
    assert(nearf_ai(boonta_rival_ai_curvature_from_samples(
        NAN, 0.0f, 0.0f, 0.0f, 2.0f, 0.0f), 0.0f));
    assert(nearf_ai(boonta_rival_ai_curvature_from_samples(
        0.0f, 0.0f, 0.0f, 0.0f, 2.0f, 0.0f), 0.0f));
}

static void rival_route_lookahead_uses_the_sampler_coordinate_system(void)
{
    /* The current single-loop sampler consumes absolute course distance. */
    assert(nearf_ai(boonta_rival_route_lookahead_sample(
        0.0f, 22.0f, 4.0f, 0), 26.0f));
    assert(nearf_ai(boonta_rival_route_lookahead_sample(
        100.0f, 82.0f, 4.0f, 0), 86.0f));
    assert(nearf_ai(boonta_rival_route_lookahead_sample(
        100.0f, 103.0f, 4.0f, 0), 107.0f));

    /* A branched sampler consumes a distance relative to the player's cursor. */
    assert(nearf_ai(boonta_rival_route_lookahead_sample(
        100.0f, 82.0f, 4.0f, 1), -14.0f));
    assert(nearf_ai(boonta_rival_route_lookahead_sample(
        100.0f, 103.0f, 4.0f, 1), 7.0f));

    assert(nearf_ai(boonta_rival_route_lookahead_sample(
        NAN, 22.0f, 4.0f, 0), 0.0f));
    assert(nearf_ai(boonta_rival_route_lookahead_sample(
        0.0f, INFINITY, 4.0f, 1), 0.0f));
    assert(nearf_ai(boonta_rival_route_lookahead_sample(
        0.0f, 22.0f, NAN, 0), 0.0f));
    assert(nearf_ai(boonta_rival_route_lookahead_sample(
        0.0f, 22.0f, 4.0f, 2), 0.0f));
}

static void closest_rival_conflict_wins_independent_of_array_order(void)
{
    const float first_z[3] = {-18.0f, -17.0f, -15.0f};
    const float first_lateral[3] = {0.0f, 0.8f, -0.8f};
    const float reversed_z[3] = {-18.0f, -15.0f, -17.0f};
    const float reversed_lateral[3] = {0.0f, -0.8f, 0.8f};
    const float first_target = boonta_rival_ai_target_lateral(
        0U, -18.0f, 0.0f, 0.0f, first_z, first_lateral, 3U, 0.0f, 3.4f);
    const float reversed_target = boonta_rival_ai_target_lateral(
        0U, -18.0f, 0.0f, 0.0f, reversed_z, reversed_lateral,
        3U, 0.0f, 3.4f);

    assert(nearf_ai(first_target, -0.75f));
    assert(nearf_ai(reversed_target, -0.75f));
}

static void curvature_reduces_target_speed(void)
{
    const float slow_rival = boonta_rival_ai_target_speed(0U, 0.0f);
    const float middle_rival = boonta_rival_ai_target_speed(1U, 0.0f);
    const float fast_rival = boonta_rival_ai_target_speed(2U, 0.0f);
    const float bend = boonta_rival_ai_target_speed(1U, 0.10f);

    assert(nearf_ai(slow_rival, 0.985f));
    assert(nearf_ai(middle_rival, 0.9925f));
    assert(nearf_ai(fast_rival, 1.0f));
    assert(slow_rival < middle_rival && middle_rival < fast_rival);
    assert(bend < middle_rival && bend >= 0.90f);
    assert(nearf_ai(boonta_rival_ai_target_speed(1U, NAN), middle_rival));
    assert(nearf_ai(boonta_rival_ai_target_speed(1U, -0.10f), middle_rival));
}

static void speed_response_is_bounded_and_asymmetric(void)
{
    assert(nearf_ai(boonta_rival_ai_speed_after_frame(0.90f, 1.0f, 1.0f), 0.904f));
    assert(nearf_ai(boonta_rival_ai_speed_after_frame(1.0f, 0.90f, 1.0f), 0.990f));
    assert(nearf_ai(boonta_rival_ai_speed_after_frame(0.90f, 1.0f, 2.0f), 0.908f));
    assert(nearf_ai(boonta_rival_ai_speed_after_frame(NAN, 1.0f, 1.0f), 0.004f));
    assert(nearf_ai(boonta_rival_ai_speed_after_frame(0.95f, 0.90f, NAN), 0.95f));
}

static void relative_progress_uses_player_and_rival_pace(void)
{
    assert(nearf_ai(boonta_rival_relative_z_after_frame(
        -18.0f, 1.0f, 0, 0.0f, 0.5f, 1.0f), -17.93f));
    assert(nearf_ai(boonta_rival_relative_z_after_frame(
        -18.0f, 0.5f, 0, 0.0f, 1.0f, 1.0f), -18.07f));
    assert(nearf_ai(boonta_rival_relative_z_after_frame(
        -18.0f, 0.5f, 1, 0.0f, 0.5f, 1.0f), -17.96f));
    assert(nearf_ai(boonta_rival_relative_z_after_frame(
        -18.0f, 0.5f, 0, 1.0f, 0.5f, 1.0f), -17.9916f));
    assert(nearf_ai(boonta_rival_relative_z_after_frame(
        NAN, NAN, 0, NAN, INFINITY, 1.0f), -18.0f));
}

static void roster_personalities_shape_lines_and_corner_pace(void)
{
    const float cautious = boonta_rival_ai_target_line_lateral(0U, 0.10f, 3.4f);
    const float balanced = boonta_rival_ai_target_line_lateral(1U, 0.10f, 3.4f);
    const float assertive = boonta_rival_ai_target_line_lateral(2U, 0.10f, 3.4f);
    const float cautious_bias = cautious + 1.25f;
    const float balanced_bias = balanced;
    const float assertive_bias = assertive - 1.25f;

    assert(cautious_bias > 0.0f);
    assert(cautious_bias < balanced_bias);
    assert(balanced_bias < assertive_bias);
    assert(nearf_ai(boonta_rival_ai_personality_curve_sensitivity(0U), 0.060f));
    assert(nearf_ai(boonta_rival_ai_personality_curve_sensitivity(1U), 0.050f));
    assert(nearf_ai(boonta_rival_ai_personality_curve_sensitivity(2U), 0.035f));
    assert(boonta_rival_ai_target_speed(0U, 0.10f) <
           boonta_rival_ai_target_speed(1U, 0.10f));
    assert(boonta_rival_ai_target_speed(1U, 0.10f) <
           boonta_rival_ai_target_speed(2U, 0.10f));
}

static void nemesis_memory_changes_a_rivals_line_and_pace_fairly(void)
{
    const float other_z[3] = {-18.0f, -34.0f, -50.0f};
    const float other_lateral[3] = {-1.25f, 0.0f, 1.25f};
    const float base_line = boonta_rival_ai_target_lateral(
        0U, -18.0f, -1.25f, 0.0f, other_z, other_lateral, 3U, 0.10f, 3.4f);
    const float nemesis_line = boonta_rival_ai_target_lateral_with_rivalry(
        0U, -18.0f, -1.25f, 0.0f, other_z, other_lateral, 3U,
        0.10f, 3.4f, BOONTA_RIVAL_RIVALRY_MAX);
    const float base_pace = boonta_rival_ai_target_speed(0U, 0.0f);
    const float nemesis_pace = boonta_rival_ai_target_speed_with_rivalry(
        0U, 0.0f, BOONTA_RIVAL_RIVALRY_MAX);

    assert(nemesis_line > base_line);
    assert(nemesis_line <= BOONTA_RIVAL_AI_LATERAL_LIMIT);
    assert(nemesis_pace > base_pace);
    assert(nemesis_pace <= 1.0f);
    assert(nearf_ai(boonta_rival_ai_target_speed_with_rivalry(
        2U, 0.0f, BOONTA_RIVAL_RIVALRY_MAX), 1.0f));
}

static void nemesis_bonus_yields_to_player_and_close_traffic(void)
{
    const float player_close_z[3] = {1.0f, -20.0f, -35.0f};
    const float player_close_lateral[3] = {-0.25f, 0.8f, -0.8f};
    const float base_player_avoidance = boonta_rival_ai_target_lateral(
        0U, 1.0f, -0.25f, 0.0f, player_close_z,
        player_close_lateral, 3U, 0.10f, 3.4f);
    const float nemesis_player_avoidance = boonta_rival_ai_target_lateral_with_rivalry(
        0U, 1.0f, -0.25f, 0.0f, player_close_z,
        player_close_lateral, 3U, 0.10f, 3.4f, BOONTA_RIVAL_RIVALRY_MAX);
    const float traffic_z[3] = {-18.0f, -17.0f, -50.0f};
    const float traffic_lateral[3] = {-1.25f, -0.75f, 1.25f};
    const float base_traffic = boonta_rival_ai_target_lateral(
        0U, -18.0f, -1.25f, 0.0f, traffic_z,
        traffic_lateral, 3U, 0.10f, 3.4f);
    const float nemesis_traffic = boonta_rival_ai_target_lateral_with_rivalry(
        0U, -18.0f, -1.25f, 0.0f, traffic_z,
        traffic_lateral, 3U, 0.10f, 3.4f, BOONTA_RIVAL_RIVALRY_MAX);

    assert(nearf_ai(nemesis_player_avoidance, base_player_avoidance));
    assert(nearf_ai(nemesis_traffic, base_traffic));
}

/* Shared geometry is immutable; each opponent must own its traversal history. */
static void rival_route_cursors_are_independent_and_order_invariant(void)
{
    BoontaRouteGraphSampler sampler = {0};
    BoontaRouteCursor forward[BOONTA_RIVAL_COUNT];
    BoontaRouteCursor reverse[BOONTA_RIVAL_COUNT];
    const BoontaRouteCursorGraph graph = {
        boonta_runtime_route_topology_edges,
        BOONTA_RUNTIME_ROUTE_EDGE_COUNT,
        BOONTA_RUNTIME_ROUTE_NODE_COUNT,
        BOONTA_RUNTIME_ROUTE_START_NODE_INDEX,
        BOONTA_RUNTIME_ROUTE_CLOSED_LOOP
    };
    unsigned int start_edge = BOONTA_ROUTE_CURSOR_NO_EDGE;
    unsigned int edge, rival, frame;

    assert(boonta_route_graph_sampler_prepare(&sampler));
    for (edge = 0U; edge < BOONTA_RUNTIME_ROUTE_EDGE_COUNT; ++edge) {
        if (boonta_runtime_route_topology_edges[edge].from_node ==
            BOONTA_RUNTIME_ROUTE_START_NODE_INDEX) {
            start_edge = edge;
            break;
        }
    }
    assert(start_edge != BOONTA_ROUTE_CURSOR_NO_EDGE);

    for (rival = 0U; rival < BOONTA_RIVAL_COUNT; ++rival) {
        assert(boonta_route_cursor_init(&forward[rival], &graph,
            sampler.edge_lengths, start_edge) == BOONTA_ROUTE_CURSOR_OK);
        assert(boonta_route_cursor_move(&forward[rival],
            boonta_rival_initial_progress(rival), NULL, 0U) ==
            BOONTA_ROUTE_CURSOR_OK);
        reverse[rival] = forward[rival];
    }

    /* Different per-rival deltas must not leak between cursor histories. */
    for (frame = 0U; frame < 2400U; ++frame) {
        for (rival = 0U; rival < BOONTA_RIVAL_COUNT; ++rival) {
            const float delta = (0.08f + (float)rival * 0.025f);
            assert(boonta_route_cursor_move(&forward[rival], delta,
                NULL, 0U) == BOONTA_ROUTE_CURSOR_OK);
        }
        for (rival = BOONTA_RIVAL_COUNT; rival > 0U; --rival) {
            const unsigned int index = rival - 1U;
            const float delta = (0.08f + (float)index * 0.025f);
            assert(boonta_route_cursor_move(&reverse[index], delta,
                NULL, 0U) == BOONTA_ROUTE_CURSOR_OK);
        }
    }

    for (rival = 0U; rival < BOONTA_RIVAL_COUNT; ++rival) {
        float forward_lap = 0.0f, reverse_lap = 0.0f;
        BoontaRouteCursorState a, b;
        assert(boonta_route_cursor_get_state(&forward[rival], &a) ==
            BOONTA_ROUTE_CURSOR_OK);
        assert(boonta_route_cursor_get_state(&reverse[rival], &b) ==
            BOONTA_ROUTE_CURSOR_OK);
        assert(a.edge == b.edge);
        assert(a.completed_laps >= 1U);
        assert(a.completed_laps == b.completed_laps);
        assert(nearf_ai(forward[rival].distance_on_edge,
            reverse[rival].distance_on_edge));
        assert(boonta_route_cursor_lap_progress(&forward[rival],
            &forward_lap) == BOONTA_ROUTE_CURSOR_OK);
        assert(boonta_route_cursor_lap_progress(&reverse[rival],
            &reverse_lap) == BOONTA_ROUTE_CURSOR_OK);
        assert(nearf_ai(forward_lap, reverse_lap));
        assert(forward[rival].edge_lengths == sampler.edge_lengths);
        assert(reverse[rival].edge_lengths == sampler.edge_lengths);
    }

    /* Advancing one cursor to the finish must not mark another rival finished. */
    assert(boonta_route_cursor_move(&forward[0],
        sampler.total_length * 3.0f, NULL, 0U) == BOONTA_ROUTE_CURSOR_OK);
    {
        BoontaRouteCursorState finished, still_racing;
        assert(boonta_route_cursor_get_state(&forward[0], &finished) ==
            BOONTA_ROUTE_CURSOR_OK);
        assert(boonta_route_cursor_get_state(&forward[1], &still_racing) ==
            BOONTA_ROUTE_CURSOR_OK);
        assert(finished.completed_laps >= 3U);
        assert(still_racing.completed_laps < 3U);
        assert(!still_racing.finished);
    }
}

/* Exercise the same cursor-to-race-distance conversion used by main.c. */
static void rival_route_progress_finishes_independently_and_resets(void)
{
    BoontaRouteGraphSampler sampler = {0};
    BoontaRouteCursor cursors[BOONTA_RIVAL_COUNT];
    const BoontaRouteCursorGraph graph = {
        boonta_runtime_route_topology_edges,
        BOONTA_RUNTIME_ROUTE_EDGE_COUNT,
        BOONTA_RUNTIME_ROUTE_NODE_COUNT,
        BOONTA_RUNTIME_ROUTE_START_NODE_INDEX,
        BOONTA_RUNTIME_ROUTE_CLOSED_LOOP
    };
    BoontaRaceState race;
    unsigned int start_edge = BOONTA_ROUTE_CURSOR_NO_EDGE;
    unsigned int edge, rival, frame;
    const unsigned int all_finished = (1U << BOONTA_RIVAL_COUNT) - 1U;

    assert(boonta_route_graph_sampler_prepare(&sampler));
    for (edge = 0U; edge < BOONTA_RUNTIME_ROUTE_EDGE_COUNT; ++edge) {
        if (boonta_runtime_route_topology_edges[edge].from_node ==
            BOONTA_RUNTIME_ROUTE_START_NODE_INDEX) {
            start_edge = edge;
            break;
        }
    }
    assert(start_edge != BOONTA_ROUTE_CURSOR_NO_EDGE);

    boonta_race_state_reset(&race);
    boonta_race_session_start_press(&race);
    for (rival = 0U; rival < BOONTA_RIVAL_COUNT; ++rival) {
        float lap_progress = 0.0f;
        BoontaRouteCursor before_invalid;
        assert(boonta_route_cursor_init(&cursors[rival], &graph,
            sampler.edge_lengths, start_edge) == BOONTA_ROUTE_CURSOR_OK);
        assert(boonta_route_cursor_move(&cursors[rival],
            boonta_rival_initial_progress(rival), NULL, 0U) ==
            BOONTA_ROUTE_CURSOR_OK);
        assert(boonta_route_cursor_lap_progress(&cursors[rival],
            &lap_progress) == BOONTA_ROUTE_CURSOR_OK);
        assert(boonta_rival_progress_from_cursor_state(
            cursors[rival].completed_laps, lap_progress,
            sampler.total_length, &race.rival_progress[rival]));
        assert(nearf_ai(race.rival_progress[rival],
            boonta_rival_initial_progress(rival)));

        before_invalid = cursors[rival];
        assert(boonta_route_cursor_move(&cursors[rival], NAN, NULL, 0U) ==
            BOONTA_ROUTE_CURSOR_INVALID);
        assert(cursors[rival].path_index == before_invalid.path_index);
        assert(cursors[rival].completed_laps == before_invalid.completed_laps);
        assert(nearf_ai(cursors[rival].distance_on_edge,
            before_invalid.distance_on_edge));
    }

    /* Advance each independent cursor in small steps through real lap seams. */
    for (frame = 0U; frame < 2000U && race.rival_finished_mask != all_finished;
         ++frame) {
        for (rival = 0U; rival < BOONTA_RIVAL_COUNT; ++rival) {
            const unsigned int finish_bit = 1U << rival;
            float lap_progress = 0.0f;
            float next_progress = 0.0f;
            const float finish_distance = boonta_rival_finish_distance(
                rival, sampler.total_length, BOONTA_RACE_LAP_CAPACITY);
            if ((race.rival_finished_mask & finish_bit) != 0U) continue;
            assert(boonta_route_cursor_move(&cursors[rival], 0.5f,
                NULL, 0U) == BOONTA_ROUTE_CURSOR_OK);
            assert(boonta_route_cursor_lap_progress(&cursors[rival],
                &lap_progress) == BOONTA_ROUTE_CURSOR_OK);
            assert(boonta_rival_progress_from_cursor_state(
                cursors[rival].completed_laps, lap_progress,
                sampler.total_length, &next_progress));
            race.rival_progress[rival] = next_progress;
            (void)boonta_rival_record_finish(&race, rival, finish_distance,
                ((float)frame + 1.0f) / 60.0f);
        }
    }

    assert(race.rival_finished_mask == all_finished);
    for (rival = 0U; rival < BOONTA_RIVAL_COUNT; ++rival) {
        const float recorded = race.rival_finish_seconds[rival];
        assert(recorded > 0.0f);
        assert(!boonta_rival_record_finish(&race, rival,
            boonta_rival_finish_distance(
                rival, sampler.total_length, BOONTA_RACE_LAP_CAPACITY),
            recorded + 1.0f));
        assert(nearf_ai(race.rival_finish_seconds[rival], recorded));
    }

    /* Y-reset semantics: clear finish data and restore every staggered cursor. */
    boonta_race_state_reset(&race);
    assert(race.rival_finished_mask == 0U);
    for (rival = 0U; rival < BOONTA_RIVAL_COUNT; ++rival) {
        float lap_progress = 0.0f;
        float reset_progress = 0.0f;
        BoontaRouteCursorState cursor_state;
        assert(boonta_route_cursor_init(&cursors[rival], &graph,
            sampler.edge_lengths, start_edge) == BOONTA_ROUTE_CURSOR_OK);
        assert(boonta_route_cursor_move(&cursors[rival],
            boonta_rival_initial_progress(rival), NULL, 0U) ==
            BOONTA_ROUTE_CURSOR_OK);
        assert(boonta_route_cursor_get_state(&cursors[rival],
            &cursor_state) == BOONTA_ROUTE_CURSOR_OK);
        assert(cursor_state.completed_laps == 0U);
        assert(boonta_route_cursor_lap_progress(&cursors[rival],
            &lap_progress) == BOONTA_ROUTE_CURSOR_OK);
        assert(boonta_rival_progress_from_cursor_state(
            cursors[rival].completed_laps, lap_progress,
            sampler.total_length, &reset_progress));
        assert(nearf_ai(reset_progress, boonta_rival_initial_progress(rival)));
        assert(nearf_ai(race.rival_progress[rival], reset_progress));
        assert(race.rival_finish_seconds[rival] == 0.0f);
    }
}

int main(void)
{
    lane_preference_is_deterministic();
    player_avoidance_only_when_close();
    nearby_rival_avoidance();
    movement_is_bounded_and_time_scaled();
    invalid_inputs_recover_safely();
    roster_personalities_shape_lines_and_corner_pace();
    nemesis_memory_changes_a_rivals_line_and_pace_fairly();
    nemesis_bonus_yields_to_player_and_close_traffic();
    curvature_samples_are_measured_and_bounded();
    signed_curvature_selects_inside_line();
    signed_curvature_preserves_turn_direction();
    curvature_reduces_target_speed();
    rival_route_lookahead_uses_the_sampler_coordinate_system();
    closest_rival_conflict_wins_independent_of_array_order();
    speed_response_is_bounded_and_asymmetric();
    relative_progress_uses_player_and_rival_pace();
    rival_route_cursors_are_independent_and_order_invariant();
    rival_route_progress_finishes_independently_and_resets();
    puts("rival AI tests: PASS");
    return 0;
}
