#include <assert.h>
#include "../source/championship.h"
int main(void) {
 Championship c; unsigned int places[CHAMPIONSHIP_MAX_RACERS] = {2U, 1U, 4U, 3U, 5U, 6U, 8U, 7U};
 unsigned int order[CHAMPIONSHIP_MAX_RACERS];
 championship_init(&c, 4U);
 assert(championship_points_for_place(1U)==15U); assert(championship_points_for_place(4U)==8U);
 assert(championship_record(&c,0U,0U,1U)==1); assert(c.points[0]==15U);
 assert(championship_record(&c,0U,0U,1U)==0); assert(c.points[0]==15U);
 assert(championship_record(&c,1U,0U,3U)==1); assert(c.points[0]==25U);
 assert(championship_record(&c,9U,0U,2U)==0); assert(championship_record(&c,2U,0U,9U)==0);
 assert(c.rounds_completed==2U); assert(championship_winner(&c)==0U);
 championship_init(&c, 2U);
 assert(championship_record_race(&c,0U,places)==1);
 assert(c.points[0]==12U && c.points[1]==15U && c.points[2]==8U && c.points[3]==10U);
 assert(championship_winner(&c)==1U);
 championship_standings(&c, order); assert(order[0]==1U && order[1]==0U);
 assert(c.place_counts[1][0]==1U && c.place_counts[0][1]==1U);
 assert(championship_record_race(&c,0U,places)==0); /* duplicate round */
 { unsigned int invalid[CHAMPIONSHIP_MAX_RACERS] = {1U, 1U, 3U, 4U, 5U, 6U, 7U, 8U};
   assert(championship_record_race(&c,1U,invalid)==0); /* duplicate place */
   assert(c.rounds_completed==1U); /* rejected input is atomic */
 }
 assert(championship_record_race(&c,1U,places)==1);
 assert(c.rounds_completed==2U);
 /* The complete game championship can include all 25 catalogued tracks. */
 championship_init(&c, 25U);
 assert(c.rounds_total==25U);
 { unsigned int full_places[CHAMPIONSHIP_MAX_RACERS] = {1U, 2U, 3U, 4U, 5U, 6U, 7U, 8U};
   unsigned int round;
   for (round=0U; round<25U; ++round) assert(championship_record_race(&c,round,full_places)==1);
   assert(c.rounds_completed==25U && championship_winner(&c)==0U);
   assert(championship_record_race(&c,24U,full_places)==0);
 }
 /* Points tie is broken by number of wins, then the next finishing places. */
 championship_init(&c, 3U);
 c.points[0]=10U; c.points[1]=10U;
 c.place_counts[0][0]=1U; c.place_counts[1][2]=2U;
 championship_standings(&c, order); assert(order[0]==0U && championship_winner(&c)==0U);
 return 0;
}
