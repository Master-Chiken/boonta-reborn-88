#include <assert.h>
#include <math.h>
#include <stdio.h>

#include "../source/route_cursor.h"

static const BoontaRouteCursorEdge g_split_rejoin_edges[] = {
    /* approach */
    { 0U, 1U, 0.0f, 0.2f },
    /* short branch: two edges, with a longer second span */
    { 1U, 2U, 0.2f, 0.4f },
    { 2U, 4U, 0.4f, 0.8f },
    /* alternative branch: unequal physical length, same rejoin progress */
    { 1U, 3U, 0.2f, 0.6f },
    { 3U, 4U, 0.6f, 0.8f },
    /* shared exit */
    { 4U, 5U, 0.8f, 1.0f }
};

static const float g_split_rejoin_lengths[] = {
    1.0f, 2.0f, 2.0f, 3.0f, 1.0f, 1.0f
};

static const BoontaRouteCursorGraph g_split_rejoin_graph = {
    g_split_rejoin_edges,
    sizeof(g_split_rejoin_edges) / sizeof(g_split_rejoin_edges[0]),
    6U,
    0U,
    0
};

static const BoontaRouteCursorEdge g_closed_branch_edges[] = {
    /* common approach */
    { 0U, 1U, 0.0f, 0.2f },
    /* shorter left lap */
    { 1U, 2U, 0.2f, 0.6f },
    { 2U, 0U, 0.6f, 1.0f },
    /* longer right lap */
    { 1U, 3U, 0.2f, 0.6f },
    { 3U, 0U, 0.6f, 1.0f }
};

static const float g_closed_branch_lengths[] = {
    1.0f, 1.0f, 2.0f, 2.0f, 2.0f
};

static const BoontaRouteCursorGraph g_closed_branch_graph = {
    g_closed_branch_edges,
    sizeof(g_closed_branch_edges) / sizeof(g_closed_branch_edges[0]),
    4U,
    0U,
    1
};

static void assert_close(float actual, float expected, float tolerance)
{
    assert(isfinite(actual));
    assert(fabsf(actual - expected) <= tolerance);
}

static BoontaRouteCursorState state_of(const BoontaRouteCursor *cursor)
{
    BoontaRouteCursorState state;
    assert(boonta_route_cursor_get_state(cursor, &state) == BOONTA_ROUTE_CURSOR_OK);
    return state;
}

static void test_branch_is_required_and_invalid_choice_rolls_back(void)
{
    BoontaRouteCursor cursor;
    BoontaRouteCursorState state;
    const BoontaRouteBranchChoice wrong = { 1U, 2U };

    assert(boonta_route_cursor_init(
        &cursor, &g_split_rejoin_graph, g_split_rejoin_lengths, 0U) ==
        BOONTA_ROUTE_CURSOR_OK);

    assert(boonta_route_cursor_move(&cursor, 1.1f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_BRANCH_REQUIRED);
    state = state_of(&cursor);
    assert(state.edge == 0U);
    assert(state.path_index == 0U);
    assert(state.history_count == 1U);
    assert_close(cursor.distance_on_edge, 0.0f, 0.000001f);

    assert(boonta_route_cursor_move(&cursor, 1.1f, &wrong, 1U) ==
           BOONTA_ROUTE_CURSOR_INVALID);
    state = state_of(&cursor);
    assert(state.edge == 0U);
    assert(state.history_count == 1U);
    assert_close(cursor.distance_on_edge, 0.0f, 0.000001f);
}

static void test_unequal_branch_traversal_rejoin_and_progress(void)
{
    BoontaRouteCursor cursor;
    BoontaRouteCursorState state;
    const BoontaRouteBranchChoice choose_short = { 1U, 1U };

    assert(boonta_route_cursor_init(
        &cursor, &g_split_rejoin_graph, g_split_rejoin_lengths, 0U) ==
        BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_move(&cursor, 5.1f, &choose_short, 1U) ==
           BOONTA_ROUTE_CURSOR_OK);

    state = state_of(&cursor);
    assert(state.edge == 5U);
    assert(state.path_index == 3U);
    assert(state.history_count == 4U);
    assert(cursor.path_history[0] == 0U);
    assert(cursor.path_history[1] == 1U);
    assert(cursor.path_history[2] == 2U);
    assert(cursor.path_history[3] == 5U);
    assert_close(cursor.distance_on_edge, 0.1f, 0.00001f);
    assert_close(state.progress, 0.82f, 0.00001f);
}

static void test_reverse_and_forward_replay_keep_selected_branch(void)
{
    BoontaRouteCursor cursor;
    BoontaRouteCursorState state;
    const BoontaRouteBranchChoice choose_right = { 1U, 3U };

    assert(boonta_route_cursor_init(
        &cursor, &g_split_rejoin_graph, g_split_rejoin_lengths, 0U) ==
        BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_move(&cursor, 5.1f, &choose_right, 1U) ==
           BOONTA_ROUTE_CURSOR_OK);

    assert(boonta_route_cursor_move(&cursor, -4.2f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    state = state_of(&cursor);
    assert(state.edge == 0U);
    assert_close(cursor.distance_on_edge, 0.9f, 0.00001f);

    /* Forward movement without a new choice replays the stored right branch. */
    assert(boonta_route_cursor_move(&cursor, 0.2f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    state = state_of(&cursor);
    assert(state.edge == 3U);
    assert(state.history_count == 4U);
    assert(cursor.path_history[1] == 3U);
}

static void test_new_branch_choice_replaces_cached_future(void)
{
    BoontaRouteCursor cursor;
    BoontaRouteCursorState state;
    const BoontaRouteBranchChoice choose_left = { 1U, 1U };
    const BoontaRouteBranchChoice choose_right = { 1U, 3U };

    assert(boonta_route_cursor_init(
        &cursor, &g_split_rejoin_graph, g_split_rejoin_lengths, 0U) ==
        BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_move(&cursor, 5.1f, &choose_left, 1U) ==
           BOONTA_ROUTE_CURSOR_OK);

    /* Return to the approach just before the split, then select the other path. */
    assert(boonta_route_cursor_move(&cursor, -4.2f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_move(&cursor, 0.2f, &choose_right, 1U) ==
           BOONTA_ROUTE_CURSOR_OK);

    state = state_of(&cursor);
    assert(state.edge == 3U);
    assert(state.history_count == 2U);
    assert(cursor.path_history[0] == 0U);
    assert(cursor.path_history[1] == 3U);
}

static void test_open_route_finishes_at_exact_terminal_distance(void)
{
    BoontaRouteCursor cursor;
    BoontaRouteCursorState state;
    const BoontaRouteBranchChoice choose_short = { 1U, 1U };

    assert(boonta_route_cursor_init(
        &cursor, &g_split_rejoin_graph, g_split_rejoin_lengths, 0U) ==
        BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_move(&cursor, 6.0f, &choose_short, 1U) ==
           BOONTA_ROUTE_CURSOR_OK);

    state = state_of(&cursor);
    assert(state.edge == 5U);
    assert(state.finished);
    assert_close(state.t, 1.0f, 0.000001f);
    assert_close(state.progress, 1.0f, 0.000001f);
}

static void test_closed_loop_replays_start_edge_without_finishing(void)
{
    static const BoontaRouteCursorEdge edges[] = {
        { 0U, 1U, 0.0f, 0.5f },
        { 1U, 0U, 0.5f, 1.0f }
    };
    static const float lengths[] = { 1.0f, 1.0f };
    static const BoontaRouteCursorGraph graph = {
        edges, 2U, 2U, 0U, 1
    };
    BoontaRouteCursor cursor;
    BoontaRouteCursorState state;

    assert(boonta_route_cursor_init(&cursor, &graph, lengths, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_move(&cursor, 2.1f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);

    state = state_of(&cursor);
    assert(state.edge == 0U);
    assert(state.path_index == 2U);
    assert(state.history_count == 3U);
    assert(!state.finished);
    assert(state.completed_laps == 1U);
    assert_close(cursor.distance_on_edge, 0.1f, 0.00001f);

    /* Reverse across the same start seam decrements the completed-lap count. */
    assert(boonta_route_cursor_move(&cursor, -0.2f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    state = state_of(&cursor);
    assert(state.edge == 1U);
    assert(state.completed_laps == 0U);
    assert(boonta_route_cursor_move(&cursor, 0.2f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    state = state_of(&cursor);
    assert(state.edge == 0U);
    assert(state.completed_laps == 1U);
}

static void test_closed_branch_laps_follow_selected_path_and_reverse(void)
{
    BoontaRouteCursor cursor;
    BoontaRouteCursorState state;
    const BoontaRouteBranchChoice choose_left = { 1U, 1U };
    const BoontaRouteBranchChoice choose_right = { 1U, 3U };

    assert(boonta_route_cursor_init(
        &cursor, &g_closed_branch_graph, g_closed_branch_lengths, 0U) ==
        BOONTA_ROUTE_CURSOR_OK);

    /* The first right-hand lap is 5 m: approach 1 + branch 2 + return 2. */
    assert(boonta_route_cursor_move(&cursor, 1.1f, &choose_right, 1U) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_move(&cursor, 4.0f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    state = state_of(&cursor);
    assert(state.edge == 0U);
    assert(state.completed_laps == 1U);
    assert_close(cursor.distance_on_edge, 0.1f, 0.00001f);

    /* The next left-hand lap is only 4 m; lap count does not use one fixed length. */
    assert(boonta_route_cursor_move(&cursor, 1.1f, &choose_left, 1U) ==
           BOONTA_ROUTE_CURSOR_OK);
    /* The left route is 4 m total; after the first 1.1 m, move 2.9 m. */
    assert(boonta_route_cursor_move(&cursor, 2.9f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    state = state_of(&cursor);
    assert(state.edge == 0U);
    assert(state.completed_laps == 2U);
    assert_close(cursor.distance_on_edge, 0.1f, 0.00001f);

    /* Reversing over the start seam removes exactly one completed lap. */
    assert(boonta_route_cursor_move(&cursor, -0.3f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    state = state_of(&cursor);
    assert(state.edge == 2U);
    assert(state.completed_laps == 1U);

    /* Moving forward over the same seam restores that lap. */
    assert(boonta_route_cursor_move(&cursor, 0.3f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    state = state_of(&cursor);
    assert(state.edge == 0U);
    assert(state.completed_laps == 2U);
}

static void test_distance_to_next_lap_uses_selected_variable_length_path(void)
{
    BoontaRouteCursor cursor;
    BoontaRouteCursorState state;
    const BoontaRouteBranchChoice choose_right = { 1U, 3U };
    const BoontaRouteBranchChoice choose_left = { 1U, 1U };
    float distance_to_lap = -1.0f;

    assert(boonta_route_cursor_init(
        &cursor, &g_closed_branch_graph, g_closed_branch_lengths, 0U) ==
        BOONTA_ROUTE_CURSOR_OK);

    /* Do not invent a finish position when the next branch has no history. */
    assert(boonta_route_cursor_distance_to_next_lap(
        &cursor, &distance_to_lap) == BOONTA_ROUTE_CURSOR_BRANCH_REQUIRED);
    assert_close(distance_to_lap, 0.0f, 0.000001f);

    /* Complete the longer right lap and record the next shorter left lap. */
    assert(boonta_route_cursor_move(&cursor, 1.1f, &choose_right, 1U) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_move(&cursor, 4.0f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    state = state_of(&cursor);
    assert(state.completed_laps == 1U);
    assert(state.edge == 0U);
    assert(boonta_route_cursor_move(&cursor, 1.1f, &choose_left, 1U) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_move(&cursor, 2.7f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    state = state_of(&cursor);
    assert(state.edge == 2U);
    assert(state.completed_laps == 1U);
    assert_close(cursor.distance_on_edge, 1.9f, 0.00001f);

    assert(boonta_route_cursor_distance_to_next_lap(
        &cursor, &distance_to_lap) == BOONTA_ROUTE_CURSOR_OK);
    assert_close(distance_to_lap, 0.1f, 0.00001f);

    /* Reverse and forward distances update the measured seam distance too. */
    assert(boonta_route_cursor_move(&cursor, -0.2f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_distance_to_next_lap(
        &cursor, &distance_to_lap) == BOONTA_ROUTE_CURSOR_OK);
    assert_close(distance_to_lap, 0.3f, 0.00001f);

    assert(boonta_route_cursor_move(&cursor, 0.4f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    state = state_of(&cursor);
    assert(state.completed_laps == 2U);
    assert(state.edge == 0U);
    assert(boonta_route_cursor_distance_to_next_lap(
        &cursor, &distance_to_lap) == BOONTA_ROUTE_CURSOR_BRANCH_REQUIRED);
    return;
}

static void test_open_route_never_wraps_to_start_node(void)
{
    static const BoontaRouteCursorEdge edges[] = {
        { 0U, 1U, 0.0f, 0.5f },
        { 1U, 0U, 0.5f, 1.0f }
    };
    static const float lengths[] = { 1.0f, 1.0f };
    static const BoontaRouteCursorGraph graph = {
        edges, 2U, 2U, 0U, 0
    };
    BoontaRouteCursor cursor;
    BoontaRouteCursorState state;

    assert(boonta_route_cursor_init(&cursor, &graph, lengths, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_move(&cursor, 2.1f, NULL, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);

    state = state_of(&cursor);
    assert(state.edge == 1U);
    assert(state.finished);
    assert(state.path_index == 1U);
    assert(state.history_count == 2U);
    assert_close(state.t, 1.0f, 0.000001f);
}

static void test_history_capacity_failure_is_atomic(void)
{
    static const BoontaRouteCursorEdge edges[] = {
        { 0U, 1U, 0.0f, 0.5f },
        { 1U, 0U, 0.5f, 1.0f }
    };
    static const float lengths[] = { 1.0f, 1.0f };
    static const BoontaRouteCursorGraph graph = {
        edges, 2U, 2U, 0U, 1
    };
    BoontaRouteCursor cursor;
    BoontaRouteCursorState state;

    assert(boonta_route_cursor_init(&cursor, &graph, lengths, 0U) ==
           BOONTA_ROUTE_CURSOR_OK);
    assert(boonta_route_cursor_move(
        &cursor, (float)BOONTA_ROUTE_CURSOR_MAX_HISTORY + 1.0f, NULL, 0U) ==
        BOONTA_ROUTE_CURSOR_HISTORY_FULL);

    state = state_of(&cursor);
    assert(state.edge == 0U);
    assert(state.path_index == 0U);
    assert(state.history_count == 1U);
    assert_close(cursor.distance_on_edge, 0.0f, 0.000001f);
}

int main(void)
{
    test_branch_is_required_and_invalid_choice_rolls_back();
    test_unequal_branch_traversal_rejoin_and_progress();
    test_reverse_and_forward_replay_keep_selected_branch();
    test_new_branch_choice_replaces_cached_future();
    test_open_route_finishes_at_exact_terminal_distance();
    test_closed_loop_replays_start_edge_without_finishing();
    test_closed_branch_laps_follow_selected_path_and_reverse();
    test_distance_to_next_lap_uses_selected_variable_length_path();
    test_open_route_never_wraps_to_start_node();
    test_history_capacity_failure_is_atomic();
    puts("Native route cursor tests passed.");
    return 0;
}
