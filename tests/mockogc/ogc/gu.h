#ifndef MOCK_GU_H
#define MOCK_GU_H
#include "../gccore.h"
typedef struct { f32 x,y,z; } guVector;
void guOrtho(Mtx44,float,float,float,float,float,float);
void guPerspective(Mtx44,float,float,float,float);
void guMtxIdentity(Mtx);
void guLookAt(Mtx,const guVector *,const guVector *,const guVector *);
#endif
