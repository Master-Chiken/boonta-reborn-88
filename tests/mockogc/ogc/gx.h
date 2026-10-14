#ifndef MOCK_GX_H
#define MOCK_GX_H
#include "../gccore.h"
#define GX_TRIANGLES 0
#define GX_TRIANGLESTRIP 1
#define GX_VTXFMT0 0
#define GX_TRUE 1
#define GX_FALSE 0
#define GX_LEQUAL 0
#define GX_ALWAYS 1
#define GX_PF_RGB565_Z16 0
#define GX_PF_RGB8_Z24 1
#define GX_ZC_LINEAR 0
#define GX_DISABLE 0
#define GX_ENABLE 1
#define GX_COLOR0A0 0
#define GX_SRC_REG 0
#define GX_SRC_VTX 1
#define GX_LIGHTNULL 0
#define GX_DF_NONE 0
#define GX_AF_NONE 0
#define GX_TEVSTAGE0 0
#define GX_PASSCLR 0
#define GX_TEXCOORD_NULL 0
#define GX_TEXMAP_NULL 0
#define GX_CULL_NONE 0
#define GX_VA_POS 0
#define GX_VA_CLR0 1
#define GX_DIRECT 0
#define GX_POS_XYZ 0
#define GX_F32 0
#define GX_CLR_RGBA 0
#define GX_RGBA8 0
#define GX_PNMTX0 0
#define GX_ORTHOGRAPHIC 0
#define GX_PERSPECTIVE 1
#define GX_GM_1_0 0
void GX_Init(void *,u32); void GX_SetCopyClear(GXColor,u32);
void GX_SetViewport(float,float,float,float,float,float); void GX_SetScissor(u32,u32,u32,u32);
void GX_SetDispCopySrc(u16,u16,u16,u16); u32 GX_SetDispCopyYScale(float);
float GX_GetYScaleFactor(u16,u16); void GX_SetDispCopyDst(u16,u16);
void GX_SetCopyFilter(int,const u8 (*)[2],int,const u8 *); void GX_SetFieldMode(int,int);
void GX_SetPixelFmt(int,int); void GX_SetZMode(int,int,int); void GX_SetColorUpdate(int); void GX_SetAlphaUpdate(int);
void GX_SetCullMode(int); void GX_SetNumChans(u8); void GX_SetChanCtrl(int,int,int,int,int,int,int);
void GX_SetNumTexGens(u8); void GX_SetNumTevStages(u8); void GX_SetTevOp(int,int); void GX_SetTevOrder(int,int,int,int);
void GX_ClearVtxDesc(void); void GX_SetVtxDesc(int,int); void GX_SetVtxAttrFmt(int,int,int,int,int);
void GX_InvVtxCache(void); void GX_SetCurrentMtx(u32); void GX_SetDispCopyGamma(int);
void GX_CopyDisp(void *,int); void GX_DrawDone(void); void GX_Begin(int,int,u16); void GX_End(void);
void GX_Position3f32(float,float,float); void GX_Color4u8(u8,u8,u8,u8);
void GX_LoadProjectionMtx(Mtx44,int); void GX_LoadPosMtxImm(Mtx,u32);
#endif
