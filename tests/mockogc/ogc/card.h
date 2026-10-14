#ifndef MOCK_OGC_CARD_H
#define MOCK_OGC_CARD_H
#include <stdint.h>
typedef int32_t s32;
typedef struct { s32 chan; s32 fileNo; s32 offset; s32 length; } CARDFileInfo;
void CARD_Init(const char *gamecode, const char *company);
s32 CARD_Mount(s32 chan, void *workArea, void (*detachCallback)(s32 chan, s32 result));
s32 CARD_Unmount(s32 chan);
s32 CARD_Open(s32 chan, const char *fileName, CARDFileInfo *fileInfo);
s32 CARD_Create(s32 chan, const char *fileName, uint32_t size, CARDFileInfo *fileInfo);
s32 CARD_Read(CARDFileInfo *fileInfo, void *buffer, s32 length, s32 offset);
s32 CARD_Write(CARDFileInfo *fileInfo, const void *buffer, s32 length, s32 offset);
s32 CARD_Close(CARDFileInfo *fileInfo);
#endif
