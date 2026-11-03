#ifndef BOONTA_REBORN_ROUTE_CURSOR_H
#define BOONTA_REBORN_ROUTE_CURSOR_H

#include <math.h>
#include <stddef.h>

#define BOONTA_ROUTE_CURSOR_MAX_HISTORY 128U
#define BOONTA_ROUTE_CURSOR_NO_EDGE 0xffffffffU
#define BOONTA_ROUTE_CURSOR_EPSILON 0.000001f
#define BOONTA_ROUTE_CURSOR_TRANSITION_LIMIT 10000U

typedef enum {
    BOONTA_ROUTE_CURSOR_OK = 0,
    BOONTA_ROUTE_CURSOR_INVALID = -1,
    BOONTA_ROUTE_CURSOR_BRANCH_REQUIRED = -2,
    BOONTA_ROUTE_CURSOR_HISTORY_FULL = -3,
    BOONTA_ROUTE_CURSOR_TRANSITION_LIMIT_REACHED = -4
} BoontaRouteCursorResult;

typedef struct {
    unsigned int from_node;
    unsigned int to_node;
    float progress_start;
    float progress_end;
} BoontaRouteCursorEdge;

typedef struct {
    const BoontaRouteCursorEdge *edges;
    unsigned int edge_count;
    unsigned int node_count;
    unsigned int start_node;
    int closed_loop;
} BoontaRouteCursorGraph;

typedef struct {
    unsigned int node;
    unsigned int edge;
} BoontaRouteBranchChoice;

typedef struct {
    unsigned int edge;
    float t;
    float progress;
    unsigned int completed_laps;
    int finished;
    int at_start;
    unsigned int path_index;
    unsigned int history_count;
} BoontaRouteCursorState;

/*
 * The cursor owns only traversal state. Geometry and arc lengths remain in
 * BoontaRouteGraphSampler; the same edge index selects both geometry and
 * topology. History is bounded so malformed/very long paths fail safely.
 */
typedef struct {
    const BoontaRouteCursorGraph *graph;
    const float *edge_lengths;
    unsigned int path_history[BOONTA_ROUTE_CURSOR_MAX_HISTORY];
    unsigned int history_count;
    unsigned int path_index;
    float distance_on_edge;
    unsigned int completed_laps;
    int finished;
    int started;
} BoontaRouteCursor;

static inline int boonta_route_cursor_graph_is_valid(
    const BoontaRouteCursorGraph *graph, const float *edge_lengths)
{
    unsigned int edge;

    if (graph == NULL || graph->edges == NULL || edge_lengths == NULL ||
        graph->edge_count == 0U || graph->node_count == 0U ||
        graph->start_node >= graph->node_count ||
        (graph->closed_loop != 0 && graph->closed_loop != 1)) {
        return 0;
    }

    for (edge = 0U; edge < graph->edge_count; ++edge) {
        const BoontaRouteCursorEdge *item = &graph->edges[edge];
        const float length = edge_lengths[edge];
        if (item->from_node >= graph->node_count ||
            item->to_node >= graph->node_count ||
            item->from_node == item->to_node ||
            !isfinite(item->progress_start) ||
            !isfinite(item->progress_end) ||
            item->progress_start < 0.0f ||
            item->progress_end > 1.0f ||
            item->progress_end - item->progress_start <= 0.000001f ||
            !isfinite(length) || length <= 0.001f) {
            return 0;
        }
    }
    return 1;
}

static inline int boonta_route_cursor_init(
    BoontaRouteCursor *cursor, const BoontaRouteCursorGraph *graph,
    const float *edge_lengths, unsigned int start_edge)
{
    if (cursor == NULL ||
        !boonta_route_cursor_graph_is_valid(graph, edge_lengths) ||
        start_edge >= graph->edge_count ||
        graph->edges[start_edge].from_node != graph->start_node) {
        return BOONTA_ROUTE_CURSOR_INVALID;
    }

    cursor->graph = graph;
    cursor->edge_lengths = edge_lengths;
    cursor->history_count = 1U;
    cursor->path_index = 0U;
    cursor->path_history[0] = start_edge;
    cursor->distance_on_edge = 0.0f;
    cursor->completed_laps = 0U;
    cursor->finished = 0;
    cursor->started = 1;
    return BOONTA_ROUTE_CURSOR_OK;
}

static inline unsigned int boonta_route_cursor_outgoing_count(
    const BoontaRouteCursorGraph *graph, unsigned int node,
    unsigned int *only_edge)
{
    unsigned int edge;
    unsigned int count = 0U;

    if (only_edge != NULL) *only_edge = BOONTA_ROUTE_CURSOR_NO_EDGE;
    for (edge = 0U; edge < graph->edge_count; ++edge) {
        if (graph->edges[edge].from_node == node) {
            ++count;
            if (only_edge != NULL) *only_edge = edge;
        }
    }
    return count;
}

static inline int boonta_route_cursor_find_choice(
    const BoontaRouteBranchChoice *choices, unsigned int choice_count,
    unsigned int node, unsigned int *edge_out)
{
    unsigned int index;
    int found = 0;

    if (edge_out != NULL) *edge_out = BOONTA_ROUTE_CURSOR_NO_EDGE;
    for (index = 0U; index < choice_count; ++index) {
        if (choices[index].node == node) {
            if (found) return -1;
            found = 1;
            if (edge_out != NULL) *edge_out = choices[index].edge;
        }
    }
    return found;
}

/* Resolve one forward transition, preserving an existing branch on replay. */
static inline int boonta_route_cursor_choose_next(
    BoontaRouteCursor *cursor, unsigned int node,
    const BoontaRouteBranchChoice *choices, unsigned int choice_count,
    unsigned int *next_edge, int *has_next)
{
    const BoontaRouteCursorGraph *graph = cursor->graph;
    const unsigned int cached_edge =
        cursor->path_index + 1U < cursor->history_count
            ? cursor->path_history[cursor->path_index + 1U]
            : BOONTA_ROUTE_CURSOR_NO_EDGE;
    unsigned int only_edge = BOONTA_ROUTE_CURSOR_NO_EDGE;
    unsigned int requested_edge = BOONTA_ROUTE_CURSOR_NO_EDGE;
    const unsigned int actual_count =
        (!graph->closed_loop && node == graph->start_node)
            ? 0U : boonta_route_cursor_outgoing_count(graph, node, &only_edge);
    const int choice_found = boonta_route_cursor_find_choice(
        choices, choice_count, node, &requested_edge);
    unsigned int selected = BOONTA_ROUTE_CURSOR_NO_EDGE;
    int append_history = 0;
    unsigned int edge;

    if (choice_found < 0) return BOONTA_ROUTE_CURSOR_INVALID;
    *next_edge = BOONTA_ROUTE_CURSOR_NO_EDGE;
    *has_next = 0;

    if (actual_count == 0U) {
        return choice_found == 1
            ? BOONTA_ROUTE_CURSOR_INVALID : BOONTA_ROUTE_CURSOR_OK;
    }

    if (choice_found == 1) {
        int is_outgoing = 0;
        for (edge = 0U; edge < graph->edge_count; ++edge) {
            if (edge == requested_edge &&
                graph->edges[edge].from_node == node) {
                is_outgoing = 1;
                break;
            }
        }
        if (!is_outgoing) return BOONTA_ROUTE_CURSOR_INVALID;
        selected = requested_edge;
        if (cached_edge != requested_edge) {
            cursor->history_count = cursor->path_index + 1U;
            append_history = 1;
        }
    } else if (cached_edge != BOONTA_ROUTE_CURSOR_NO_EDGE) {
        if (cached_edge >= graph->edge_count ||
            graph->edges[cached_edge].from_node != node) {
            return BOONTA_ROUTE_CURSOR_INVALID;
        }
        selected = cached_edge;
    } else if (actual_count == 1U) {
        selected = only_edge;
        append_history = 1;
    } else {
        return BOONTA_ROUTE_CURSOR_BRANCH_REQUIRED;
    }

    if (append_history) {
        if (cursor->history_count >= BOONTA_ROUTE_CURSOR_MAX_HISTORY) {
            return BOONTA_ROUTE_CURSOR_HISTORY_FULL;
        }
        cursor->path_history[cursor->history_count++] = selected;
    }

    *next_edge = selected;
    *has_next = 1;
    return BOONTA_ROUTE_CURSOR_OK;
}

/*
 * Move by physical arc distance in metres. Explicit branch choices are keyed
 * by node index; a stored choice is replayed after reverse movement unless a
 * new valid choice is supplied at that node.
 */
static inline int boonta_route_cursor_move(
    BoontaRouteCursor *cursor, float delta_distance,
    const BoontaRouteBranchChoice *choices, unsigned int choice_count)
{
    BoontaRouteCursor backup;
    unsigned int transitions = 0U;
    float next_distance;

    if (cursor == NULL || cursor->graph == NULL ||
        cursor->edge_lengths == NULL || !isfinite(delta_distance) ||
        (choice_count > 0U && choices == NULL) ||
        cursor->history_count == 0U ||
        cursor->history_count > BOONTA_ROUTE_CURSOR_MAX_HISTORY ||
        cursor->path_index >= cursor->history_count ||
        cursor->path_history[cursor->path_index] >= cursor->graph->edge_count) {
        return BOONTA_ROUTE_CURSOR_INVALID;
    }

    backup = *cursor;
    next_distance = cursor->distance_on_edge + delta_distance;
    if (!isfinite(next_distance)) return BOONTA_ROUTE_CURSOR_INVALID;
    cursor->distance_on_edge = next_distance;
    if (delta_distance < 0.0f) cursor->finished = 0;

    while (cursor->distance_on_edge >
           cursor->edge_lengths[cursor->path_history[cursor->path_index]] +
               BOONTA_ROUTE_CURSOR_EPSILON) {
        const unsigned int current_edge = cursor->path_history[cursor->path_index];
        const unsigned int node = cursor->graph->edges[current_edge].to_node;
        unsigned int next_edge = BOONTA_ROUTE_CURSOR_NO_EDGE;
        int has_next = 0;
        const int result = boonta_route_cursor_choose_next(
            cursor, node, choices, choice_count, &next_edge, &has_next);

        ++transitions;
        if (transitions > BOONTA_ROUTE_CURSOR_TRANSITION_LIMIT) {
            *cursor = backup;
            return BOONTA_ROUTE_CURSOR_TRANSITION_LIMIT_REACHED;
        }
        if (result != BOONTA_ROUTE_CURSOR_OK) {
            *cursor = backup;
            return result;
        }
        if (!has_next) {
            cursor->distance_on_edge = cursor->edge_lengths[current_edge];
            cursor->finished = 1;
            break;
        }

        cursor->distance_on_edge -= cursor->edge_lengths[current_edge];
        if (cursor->graph->closed_loop &&
            node == cursor->graph->start_node &&
            cursor->completed_laps < 0xffffffffU) {
            ++cursor->completed_laps;
        }
        ++cursor->path_index;
        cursor->finished = 0;
    }

    while (cursor->distance_on_edge < -BOONTA_ROUTE_CURSOR_EPSILON) {
        unsigned int previous_edge;

        ++transitions;
        if (transitions > BOONTA_ROUTE_CURSOR_TRANSITION_LIMIT) {
            *cursor = backup;
            return BOONTA_ROUTE_CURSOR_TRANSITION_LIMIT_REACHED;
        }
        if (cursor->path_index == 0U) {
            cursor->distance_on_edge = 0.0f;
            cursor->started = 1;
            break;
        }

        previous_edge = cursor->path_history[cursor->path_index - 1U];
        if (previous_edge >= cursor->graph->edge_count ||
            cursor->graph->edges[previous_edge].to_node !=
                cursor->graph->edges[
                    cursor->path_history[cursor->path_index]].from_node) {
            *cursor = backup;
            return BOONTA_ROUTE_CURSOR_INVALID;
        }

        if (cursor->graph->closed_loop &&
            cursor->graph->edges[
                cursor->path_history[cursor->path_index]].from_node ==
                cursor->graph->start_node &&
            cursor->completed_laps > 0U) {
            --cursor->completed_laps;
        }
        --cursor->path_index;
        cursor->distance_on_edge += cursor->edge_lengths[previous_edge];
        cursor->finished = 0;
    }

    {
        const unsigned int current_edge = cursor->path_history[cursor->path_index];
        const float edge_length = cursor->edge_lengths[current_edge];
        unsigned int only_edge = BOONTA_ROUTE_CURSOR_NO_EDGE;
        const unsigned int outgoing = boonta_route_cursor_outgoing_count(
            cursor->graph, cursor->graph->edges[current_edge].to_node, &only_edge);

        if (cursor->distance_on_edge < 0.0f &&
            cursor->distance_on_edge >= -BOONTA_ROUTE_CURSOR_EPSILON) {
            cursor->distance_on_edge = 0.0f;
        }
        if (cursor->distance_on_edge > edge_length &&
            cursor->distance_on_edge <= edge_length + BOONTA_ROUTE_CURSOR_EPSILON) {
            cursor->distance_on_edge = edge_length;
        }
        if (delta_distance >= 0.0f &&
            fabsf(cursor->distance_on_edge - edge_length) <=
                BOONTA_ROUTE_CURSOR_EPSILON &&
            outgoing == 0U) {
            cursor->distance_on_edge = edge_length;
            cursor->finished = 1;
        }
        cursor->started = cursor->path_index == 0U &&
            cursor->distance_on_edge <= BOONTA_ROUTE_CURSOR_EPSILON;
    }

    return BOONTA_ROUTE_CURSOR_OK;
}

static inline int boonta_route_cursor_get_state(
    const BoontaRouteCursor *cursor, BoontaRouteCursorState *state)
{
    unsigned int edge;
    float t;

    if (cursor == NULL || state == NULL || cursor->graph == NULL ||
        cursor->edge_lengths == NULL || cursor->history_count == 0U ||
        cursor->path_index >= cursor->history_count) {
        return BOONTA_ROUTE_CURSOR_INVALID;
    }

    edge = cursor->path_history[cursor->path_index];
    if (edge >= cursor->graph->edge_count ||
        !isfinite(cursor->edge_lengths[edge]) ||
        cursor->edge_lengths[edge] <= 0.001f ||
        !isfinite(cursor->distance_on_edge)) {
        return BOONTA_ROUTE_CURSOR_INVALID;
    }

    t = cursor->distance_on_edge / cursor->edge_lengths[edge];
    if (t < 0.0f) t = 0.0f;
    if (t > 1.0f) t = 1.0f;

    state->edge = edge;
    state->t = t;
    state->progress =
        cursor->graph->edges[edge].progress_start +
        (cursor->graph->edges[edge].progress_end -
         cursor->graph->edges[edge].progress_start) * t;
    state->completed_laps = cursor->completed_laps;
    state->finished = cursor->finished;
    state->at_start = cursor->started;
    state->path_index = cursor->path_index;
    state->history_count = cursor->history_count;
    return BOONTA_ROUTE_CURSOR_OK;
}


/*
 * Return physical distance from the cursor to the next closed-loop start
 * seam along the already selected path history. A branch with no cached
 * continuation is reported as BRANCH_REQUIRED rather than guessing an edge.
 */
static inline int boonta_route_cursor_distance_to_next_lap(
    const BoontaRouteCursor *cursor, float *distance_out)
{
    unsigned int path_index;
    unsigned int previous_edge;
    float distance;

    if (distance_out != NULL) *distance_out = 0.0f;
    if (cursor == NULL || distance_out == NULL || cursor->graph == NULL ||
        cursor->edge_lengths == NULL || !cursor->graph->closed_loop ||
        cursor->history_count == 0U ||
        cursor->history_count > BOONTA_ROUTE_CURSOR_MAX_HISTORY ||
        cursor->path_index >= cursor->history_count) {
        return BOONTA_ROUTE_CURSOR_INVALID;
    }

    previous_edge = cursor->path_history[cursor->path_index];
    if (previous_edge >= cursor->graph->edge_count ||
        !isfinite(cursor->distance_on_edge) ||
        !isfinite(cursor->edge_lengths[previous_edge]) ||
        cursor->edge_lengths[previous_edge] <= 0.001f ||
        cursor->distance_on_edge < 0.0f ||
        cursor->distance_on_edge >
            cursor->edge_lengths[previous_edge] +
                BOONTA_ROUTE_CURSOR_EPSILON) {
        return BOONTA_ROUTE_CURSOR_INVALID;
    }

    distance = cursor->edge_lengths[previous_edge] -
        cursor->distance_on_edge;
    if (cursor->graph->edges[previous_edge].to_node ==
            cursor->graph->start_node) {
        *distance_out = distance;
        return BOONTA_ROUTE_CURSOR_OK;
    }

    for (path_index = cursor->path_index + 1U;
         path_index < cursor->history_count; ++path_index) {
        const unsigned int edge = cursor->path_history[path_index];
        const BoontaRouteCursorEdge *item;

        if (edge >= cursor->graph->edge_count) {
            return BOONTA_ROUTE_CURSOR_INVALID;
        }
        item = &cursor->graph->edges[edge];
        if (item->from_node !=
                cursor->graph->edges[previous_edge].to_node ||
            !isfinite(cursor->edge_lengths[edge]) ||
            cursor->edge_lengths[edge] <= 0.001f) {
            return BOONTA_ROUTE_CURSOR_INVALID;
        }

        distance += cursor->edge_lengths[edge];
        if (!isfinite(distance)) return BOONTA_ROUTE_CURSOR_INVALID;
        if (item->to_node == cursor->graph->start_node) {
            *distance_out = distance;
            return BOONTA_ROUTE_CURSOR_OK;
        }
        previous_edge = edge;
    }

    return BOONTA_ROUTE_CURSOR_BRANCH_REQUIRED;
}

#endif /* BOONTA_REBORN_ROUTE_CURSOR_H */
