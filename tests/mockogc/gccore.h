#ifndef MOCK_GCCORE_H
#define MOCK_GCCORE_H
#include <stddef.h>
typedef unsigned char u8; typedef signed char s8;
typedef unsigned short u16; typedef unsigned int u32; typedef float f32;
typedef float Mtx[3][4]; typedef float Mtx44[4][4];
typedef struct { u8 r,g,b,a; } GXColor;
typedef struct { u16 fbWidth,efbHeight,xfbHeight,viTVMode,viHeight; u8 aa,field_rendering; u8 sample_pattern[12][2]; u8 vfilter[7]; } GXRModeObj;
#define MEM_K0_TO_K1(p) (p)
#define VI_NON_INTERLACE 1
#define FALSE 0
#define TRUE 1
void VIDEO_Init(void); GXRModeObj *VIDEO_GetPreferredMode(void *);
void VIDEO_Configure(GXRModeObj *); void VIDEO_SetNextFramebuffer(void *);
void VIDEO_SetBlack(int); void VIDEO_Flush(void); void VIDEO_WaitVSync(void);
#endif
