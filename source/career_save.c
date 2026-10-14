#include "career_save.h"
#include <stddef.h>
#include <string.h>
#include <math.h>

#define SAVE_MAGIC_0 'S'
#define SAVE_MAGIC_1 'W'
#define SAVE_MAGIC_2 'R'
#define SAVE_MAGIC_3 'P'
#define SAVE_VERSION_OFFSET 4U
#define SAVE_RACES_OFFSET 8U
#define SAVE_WINS_OFFSET 12U
#define SAVE_CHAMPIONSHIPS_OFFSET 16U
#define SAVE_BEST_MASK_OFFSET 20U
#define SAVE_TIMES_OFFSET 24U
#define SAVE_CREDITS_OFFSET 124U
#define SAVE_UPGRADES_OFFSET 128U
#define SAVE_CRC_OFFSET 136U

static void put_u32_be(unsigned char *p, uint32_t v)
{
    p[0] = (unsigned char)(v >> 24); p[1] = (unsigned char)(v >> 16);
    p[2] = (unsigned char)(v >> 8); p[3] = (unsigned char)v;
}

static uint32_t get_u32_be(const unsigned char *p)
{
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
           ((uint32_t)p[2] << 8) | (uint32_t)p[3];
}

static uint32_t crc32_bytes(const unsigned char *data, unsigned int count)
{
    uint32_t crc = 0xffffffffU;
    unsigned int i;
    for (i = 0U; i < count; ++i) {
        unsigned int bit;
        crc ^= data[i];
        for (bit = 0U; bit < 8U; ++bit)
            crc = (crc >> 1) ^ ((crc & 1U) ? 0xedb88320U : 0U);
    }
    return crc ^ 0xffffffffU;
}

void career_profile_init(CareerProfile *p)
{
    if (p != NULL) memset(p, 0, sizeof(*p));
}

static void record_best_lap(CareerProfile *p, unsigned int track_index,
                            float best_lap_seconds)
{
    uint32_t ms;
    if (!isfinite(best_lap_seconds) || best_lap_seconds <= 0.0f || best_lap_seconds >= 3600.0f)
        return;
    ms = (uint32_t)(best_lap_seconds * 1000.0f + 0.5f);
    if (!(p->best_lap_mask & (1U << track_index)) || ms < p->best_lap_ms[track_index]) {
        p->best_lap_ms[track_index] = ms;
        p->best_lap_mask |= 1U << track_index;
    }
}

int career_profile_record_race(CareerProfile *p, unsigned int track_index,
                               unsigned int place, float best_lap_seconds,
                               int championship_won)
{
    if (p == NULL || track_index >= CAREER_TRACK_COUNT || place < 1U || place > 8U)
        return 0;
    p->races_completed++;
    if (place == 1U) p->race_wins++;
    if (championship_won) p->championships_won++;
    record_best_lap(p, track_index, best_lap_seconds);
    return 1;
}

int career_profile_record_time_trial(CareerProfile *p, unsigned int track_index,
                                     float best_lap_seconds)
{
    if (p == NULL || track_index >= CAREER_TRACK_COUNT) return 0;
    p->races_completed++;
    record_best_lap(p, track_index, best_lap_seconds);
    return 1;
}

void career_save_encode(const CareerProfile *p, unsigned char out[CAREER_SAVE_BYTES])
{
    unsigned int i;
    if (out == NULL) return;
    memset(out, 0, CAREER_SAVE_BYTES);
    if (p == NULL) return;
    out[0] = SAVE_MAGIC_0; out[1] = SAVE_MAGIC_1;
    out[2] = SAVE_MAGIC_2; out[3] = SAVE_MAGIC_3;
    put_u32_be(out + SAVE_VERSION_OFFSET, CAREER_SAVE_VERSION);
    put_u32_be(out + SAVE_RACES_OFFSET, p->races_completed);
    put_u32_be(out + SAVE_WINS_OFFSET, p->race_wins);
    put_u32_be(out + SAVE_CHAMPIONSHIPS_OFFSET, p->championships_won);
    put_u32_be(out + SAVE_BEST_MASK_OFFSET, p->best_lap_mask & ((1U << CAREER_TRACK_COUNT) - 1U));
    for (i = 0U; i < CAREER_TRACK_COUNT; ++i)
        put_u32_be(out + SAVE_TIMES_OFFSET + i * 4U, p->best_lap_ms[i]);
    put_u32_be(out + SAVE_CREDITS_OFFSET, p->credits);
    for (i = 0U; i < 4U; ++i) out[SAVE_UPGRADES_OFFSET + i] = p->upgrade_levels[i] > 5U ? 5U : p->upgrade_levels[i];
    put_u32_be(out + SAVE_CRC_OFFSET, crc32_bytes(out, SAVE_CRC_OFFSET));
}

int career_save_decode(CareerProfile *p, const unsigned char in[CAREER_SAVE_BYTES])
{
    unsigned int i;
    CareerProfile tmp;
    if (p == NULL || in == NULL) return 0;
    if (in[0] != SAVE_MAGIC_0 || in[1] != SAVE_MAGIC_1 ||
        in[2] != SAVE_MAGIC_2 || in[3] != SAVE_MAGIC_3) return 0;
    if (get_u32_be(in + SAVE_VERSION_OFFSET) != CAREER_SAVE_VERSION) return 0;
    if (get_u32_be(in + SAVE_CRC_OFFSET) != crc32_bytes(in, SAVE_CRC_OFFSET)) return 0;
    career_profile_init(&tmp);
    tmp.races_completed = get_u32_be(in + SAVE_RACES_OFFSET);
    tmp.race_wins = get_u32_be(in + SAVE_WINS_OFFSET);
    tmp.championships_won = get_u32_be(in + SAVE_CHAMPIONSHIPS_OFFSET);
    tmp.best_lap_mask = get_u32_be(in + SAVE_BEST_MASK_OFFSET) & ((1U << CAREER_TRACK_COUNT) - 1U);
    tmp.credits = get_u32_be(in + SAVE_CREDITS_OFFSET);
    for (i = 0U; i < 4U; ++i) {
        if (in[SAVE_UPGRADES_OFFSET + i] > 5U) return 0;
        tmp.upgrade_levels[i] = in[SAVE_UPGRADES_OFFSET + i];
    }
    if (tmp.race_wins > tmp.races_completed || tmp.championships_won > tmp.races_completed) return 0;
    for (i = 0U; i < CAREER_TRACK_COUNT; ++i) {
        tmp.best_lap_ms[i] = get_u32_be(in + SAVE_TIMES_OFFSET + i * 4U);
        if ((tmp.best_lap_mask & (1U << i)) &&
            (tmp.best_lap_ms[i] == 0U || tmp.best_lap_ms[i] >= 3600000U)) return 0;
    }
    *p = tmp;
    return 1;
}

#ifdef GEKKO
#include <ogc/card.h>
#include <ogc/system.h>
#define CAREER_CARD_CHANNEL 0
#define CAREER_CARD_FILENAME "SWR1.SAV"
#define CAREER_CARD_WORKAREA_BYTES (5U * 8192U)
static unsigned char g_card_workarea[CAREER_CARD_WORKAREA_BYTES] __attribute__((aligned(32)));
static unsigned char g_card_buffer[CAREER_SAVE_BYTES] __attribute__((aligned(32)));

static int card_mount(void)
{
    CARD_Init("SWR1", "01");
    return CARD_Mount(CAREER_CARD_CHANNEL, g_card_workarea, NULL) >= 0;
}

int career_card_load(CareerProfile *p)
{
    CARDFileInfo file;
    s32 result;
    int ok = 0;
    if (p == NULL || !card_mount()) return 0;
    result = CARD_Open(CAREER_CARD_CHANNEL, CAREER_CARD_FILENAME, &file);
    if (result >= 0) {
        result = CARD_Read(&file, g_card_buffer, CAREER_SAVE_BYTES, 0);
        if (result >= 0 && career_save_decode(p, g_card_buffer)) ok = 1;
        CARD_Close(&file);
    } else {
        career_profile_init(p);
        career_save_encode(p, g_card_buffer);
        if (CARD_Create(CAREER_CARD_CHANNEL, CAREER_CARD_FILENAME, CAREER_SAVE_BYTES, &file) >= 0) {
            if (CARD_Write(&file, g_card_buffer, CAREER_SAVE_BYTES, 0) >= 0) ok = 1;
            CARD_Close(&file);
        }
    }
    CARD_Unmount(CAREER_CARD_CHANNEL);
    return ok;
}

int career_card_store(const CareerProfile *p)
{
    CARDFileInfo file;
    s32 result;
    int ok = 0;
    if (p == NULL || !card_mount()) return 0;
    result = CARD_Open(CAREER_CARD_CHANNEL, CAREER_CARD_FILENAME, &file);
    if (result < 0) {
        result = CARD_Create(CAREER_CARD_CHANNEL, CAREER_CARD_FILENAME, CAREER_SAVE_BYTES, &file);
    }
    if (result >= 0) {
        career_save_encode(p, g_card_buffer);
        if (CARD_Write(&file, g_card_buffer, CAREER_SAVE_BYTES, 0) >= 0) ok = 1;
        CARD_Close(&file);
    }
    CARD_Unmount(CAREER_CARD_CHANNEL);
    return ok;
}
#else
int career_card_load(CareerProfile *p) { (void)p; return 0; }
int career_card_store(const CareerProfile *p) { (void)p; return 0; }
#endif
