#include "track_direction.h"

int track_direction_reverse(RacerTrackPoint *points, unsigned int count)
{
    unsigned int left, right;
    if (points == 0 || count < 3U) return 0;
    left = 1U;
    right = count - 1U;
    while (left < right) {
        RacerTrackPoint tmp = points[left];
        points[left] = points[right];
        points[right] = tmp;
        ++left;
        --right;
    }
    return 1;
}
