#include "sithRender_delta.h"

#include <cstdio>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>

#include <glad/glad.h>
#include <GLFW/glfw3.h>

extern "C" {
#include "globals.h"
}

extern "C" FILE *hook_log;

// Armed by the F12 handler, consumed at end of frame. Empty means nothing pending.
static std::string g_pending_screenshot;

// Time of the last accepted request, in glfwGetTime() seconds; negative means "none yet".
// swrMain_ProcessDebugKeys has no rising-edge check on F12, so one press can ask for a capture
// more than once. Neither a frame count nor the physical key state separates a repeat from a
// second press: the repeat lands a variable number of frames out, and the handler runs after the
// key-down edge so the key always reads as held. Spacing does -- measured repeats sit 47-70 ms
// behind their press, deliberate presses no closer than 1.8 s.
static double g_last_request_time = -1.0;

static constexpr double SCREENSHOT_DEBOUNCE_SECONDS = 0.25;

// BMP layout (BITMAPFILEHEADER + BITMAPINFOHEADER, both fixed by the format).
static constexpr int BMP_FILE_HEADER_SIZE = 14;
static constexpr int BMP_INFO_HEADER_SIZE = 40;
static constexpr int BMP_PIXEL_OFFSET = BMP_FILE_HEADER_SIZE + BMP_INFO_HEADER_SIZE;
static constexpr int BMP_BITS_PER_PIXEL = 24;
static constexpr int BMP_BYTES_PER_PIXEL = 3;
static constexpr int BMP_ROW_ALIGN = 4;// each row is padded up to a 4-byte boundary

// Field offsets within the two headers, in the order the format lays them out.
static constexpr int BMP_OFF_FILE_SIZE = 2;
static constexpr int BMP_OFF_PIXEL_OFFSET = 10;
static constexpr int BMP_OFF_INFO_SIZE = BMP_FILE_HEADER_SIZE + 0;
static constexpr int BMP_OFF_WIDTH = BMP_FILE_HEADER_SIZE + 4;
static constexpr int BMP_OFF_HEIGHT = BMP_FILE_HEADER_SIZE + 8;
static constexpr int BMP_OFF_PLANES = BMP_FILE_HEADER_SIZE + 12;
static constexpr int BMP_OFF_BIT_COUNT = BMP_FILE_HEADER_SIZE + 14;
static constexpr int BMP_OFF_IMAGE_SIZE = BMP_FILE_HEADER_SIZE + 20;

// glReadPixels hands back rows bottom-up in GL_BGR, which is the on-disk layout, so rows go
// straight out with only stride padding applied.
static bool write_bmp_24(const char *filename, int width, int height,
                         const std::vector<uint8_t> &bgr) {
    const int row_bytes = width * BMP_BYTES_PER_PIXEL;
    const int padded_row = (row_bytes + BMP_ROW_ALIGN - 1) & ~(BMP_ROW_ALIGN - 1);
    const uint32_t pixel_bytes = (uint32_t) padded_row * (uint32_t) height;

    FILE *f = fopen(filename, "wb");
    if (!f)
        return false;

    uint8_t header[BMP_PIXEL_OFFSET] = {0};
    header[0] = 'B';
    header[1] = 'M';
    const uint32_t file_size = (uint32_t) BMP_PIXEL_OFFSET + pixel_bytes;
    const uint32_t pixel_offset = BMP_PIXEL_OFFSET;
    const uint32_t info_size = BMP_INFO_HEADER_SIZE;
    const int32_t w32 = width;
    const int32_t h32 = height;
    const uint16_t planes = 1;
    const uint16_t bpp = BMP_BITS_PER_PIXEL;
    std::memcpy(&header[BMP_OFF_FILE_SIZE], &file_size, sizeof(file_size));
    std::memcpy(&header[BMP_OFF_PIXEL_OFFSET], &pixel_offset, sizeof(pixel_offset));
    std::memcpy(&header[BMP_OFF_INFO_SIZE], &info_size, sizeof(info_size));
    std::memcpy(&header[BMP_OFF_WIDTH], &w32, sizeof(w32));
    std::memcpy(&header[BMP_OFF_HEIGHT], &h32, sizeof(h32));
    std::memcpy(&header[BMP_OFF_PLANES], &planes, sizeof(planes));
    std::memcpy(&header[BMP_OFF_BIT_COUNT], &bpp, sizeof(bpp));
    std::memcpy(&header[BMP_OFF_IMAGE_SIZE], &pixel_bytes, sizeof(pixel_bytes));

    bool ok = fwrite(header, 1, sizeof(header), f) == sizeof(header);

    static const uint8_t padding[BMP_ROW_ALIGN - 1] = {0};
    const int pad = padded_row - row_bytes;
    for (int y = 0; ok && y < height; y++) {
        ok = fwrite(&bgr[(size_t) y * row_bytes], 1, row_bytes, f) == (size_t) row_bytes;
        if (ok && pad)
            ok = fwrite(padding, 1, pad, f) == (size_t) pad;
    }

    fclose(f);
    return ok;
}

void sithRender_MakeScreenShot_delta(char *prefix) {
    // Swallow the repeat before picking a name, so it does not burn a file index and leave a gap in
    // the numbering.
    const double now = glfwGetTime();
    if (g_last_request_time >= 0.0 && (now - g_last_request_time) < SCREENSHOT_DEBOUNCE_SECONDS) {
        g_last_request_time = now;
        return;
    }
    g_last_request_time = now;

    // Same numbering the original uses: walk the index until a name is free, and leave
    // stdDisplay_ScreenshotIndex past it so the next shot starts from there.
    char filename[80];
    FILE *probe = NULL;
    do {
        const int index = stdDisplay_ScreenshotIndex;
        stdDisplay_ScreenshotIndex = index + 1;
        snprintf(filename, sizeof(filename), "%s%03d.bmp", prefix ? prefix : "snap_", index);
        probe = fopen(filename, "rb");
        if (probe == NULL)
            break;
        fclose(probe);
    } while (true);

    // Arm only; the frame is not finished at input time. A second request in the same frame keeps
    // the first name rather than dropping a numbered file that never gets written.
    if (g_pending_screenshot.empty())
        g_pending_screenshot = filename;
}

void sithRender_CapturePendingScreenshot(void) {
    if (g_pending_screenshot.empty())
        return;

    const std::string filename = g_pending_screenshot;
    g_pending_screenshot.clear();

    int width = 0;
    int height = 0;
    GLFWwindow *window = glfwGetCurrentContext();
    if (window)
        glfwGetFramebufferSize(window, &width, &height);
    if (width <= 0 || height <= 0)
        return;

    std::vector<uint8_t> pixels((size_t) width * height * BMP_BYTES_PER_PIXEL);

    // swrViewport_Render_Hook has already blitted the scene into framebuffer 0. Tight row stride so
    // the buffer matches the width.
    GLint prev_read_fb = 0;
    GLint prev_pack_align = 4;
    glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING, &prev_read_fb);
    glGetIntegerv(GL_PACK_ALIGNMENT, &prev_pack_align);
    glBindFramebuffer(GL_READ_FRAMEBUFFER, 0);
    glReadBuffer(GL_BACK);
    glPixelStorei(GL_PACK_ALIGNMENT, 1);
    glReadPixels(0, 0, width, height, GL_BGR, GL_UNSIGNED_BYTE, pixels.data());
    glPixelStorei(GL_PACK_ALIGNMENT, prev_pack_align);
    glBindFramebuffer(GL_READ_FRAMEBUFFER, prev_read_fb);

    if (!write_bmp_24(filename.c_str(), width, height, pixels)) {
        fprintf(hook_log, "[screenshot] failed to write %s\n", filename.c_str());
        fflush(hook_log);
        return;
    }
    fprintf(hook_log, "[screenshot] wrote %s (%dx%d)\n", filename.c_str(), width, height);
    fflush(hook_log);
}
