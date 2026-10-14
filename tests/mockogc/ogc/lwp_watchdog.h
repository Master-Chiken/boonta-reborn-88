#ifndef MOCK_LWP_WATCHDOG_H
#define MOCK_LWP_WATCHDOG_H
#include <gccore.h>
typedef unsigned long long u64;
u64 gettime(void);
u32 diff_usec(u64 start, u64 end);
#endif
