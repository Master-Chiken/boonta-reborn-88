#pragma once

// Screenshot capture (issue #289). The original path (sithRender_MakeScreenShot ->
// stdDisplay_SaveScreen -> stdBmp_VBufferToBmp) converts stdDisplay_g_backBuffer, the DirectDraw
// surface the OpenGL takeover never fills, and faults in stdColor_ColorConvertOneRow. These read
// the finished frame back out of GL instead.

#ifdef __cplusplus
extern "C" {
#endif

// Replaces sithRender_MakeScreenShot: picks the next free "<prefix>NNN.bmp" and arms the capture.
void sithRender_MakeScreenShot_delta(char *prefix);

// Per frame from stdDisplay_Update_Hook, after the scene resolves and before the overlay draws.
void sithRender_CapturePendingScreenshot(void);

#ifdef __cplusplus
}
#endif
