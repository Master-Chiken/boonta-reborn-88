/*
 * Boonta Reborn 88 — GameCube toolchain smoke test.
 * Original diagnostic code only; no commercial game code or assets.
 *
 * This confirms that devkitPPC/libogc can build a DOL and that the
 * console/framebuffer/controller APIs are available. It is not the game.
 */
#include <gccore.h>
#include <ogc/pad.h>
#include <ogc/system.h>
#include <ogc/video.h>
#include <ogc/console.h>
#include <stdio.h>

int main(int argc, char **argv)
{
    (void)argc;
    (void)argv;

    VIDEO_Init();
    PAD_Init();

    GXRModeObj *mode = VIDEO_GetPreferredMode(NULL);
    void *framebuffer = MEM_K0_TO_K1(SYS_AllocateFramebuffer(mode));
    if (framebuffer == NULL) {
        return 1;
    }

    console_init(framebuffer, 20, 20, mode->fbWidth, mode->xfbHeight,
                 mode->fbWidth * VI_DISPLAY_PIX_SZ);
    VIDEO_Configure(mode);
    VIDEO_SetNextFramebuffer(framebuffer);
    VIDEO_SetBlack(FALSE);
    VIDEO_Flush();
    VIDEO_WaitVSync();
    if (mode->viTVMode & VI_NON_INTERLACE) {
        VIDEO_WaitVSync();
    }

    printf("\n");
    printf("BOONTA REBORN 88\n");
    printf("GAMECUBE TOOLCHAIN SMOKE TEST\n\n");
    printf("Clean-room diagnostic build.\n");
    printf("No game ROM or proprietary assets included.\n\n");
    printf("Press START to exit.\n");

    for (;;) {
        PAD_ScanPads();
        if (PAD_ButtonsDown(0) & PAD_BUTTON_START) {
            SYS_ResetSystem(SYS_RETURNTOMENU, 0, 0);
        }
        VIDEO_WaitVSync();
    }

    return 0;
}
