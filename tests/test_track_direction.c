#include "track_direction.h"
#include <stdio.h>

#define CHECK(x) do { if (!(x)) { fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #x); return 1; } } while (0)

int main(void)
{
    RacerTrackPoint p[5] = {{0,0,0},{1,1,0},{2,2,0},{3,3,0},{4,4,0}};
    RacerTrackPoint before[2] = {{7,0,8},{9,0,10}};
    CHECK(track_direction_reverse(p, 5U) == 1);
    CHECK(p[0].x == 0.0f);
    CHECK(p[1].x == 4.0f);
    CHECK(p[2].x == 3.0f);
    CHECK(p[3].x == 2.0f);
    CHECK(p[4].x == 1.0f);
    CHECK(track_direction_reverse(p, 5U) == 1);
    CHECK(p[0].x == 0.0f && p[1].x == 1.0f && p[4].x == 4.0f);
    CHECK(track_direction_reverse(before, 2U) == 0);
    CHECK(before[0].x == 7.0f && before[1].x == 9.0f);
    CHECK(track_direction_reverse(0, 5U) == 0);
    puts("PASS: reverse track preserves start marker and is reversible");
    return 0;
}
