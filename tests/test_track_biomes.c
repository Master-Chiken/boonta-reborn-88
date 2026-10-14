#include "track_catalog.h"
#include <stdio.h>
#include <string.h>

#define CHECK(expr) do { \
    if (!(expr)) { \
        fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #expr); \
        return 1; \
    } \
} while (0)

int main(void)
{
    static const TrackBiome expected[TRACK_CATALOG_COUNT] = {
        TRACK_BIOME_SANDSTONE, TRACK_BIOME_JUNGLE, TRACK_BIOME_COASTAL,
        TRACK_BIOME_JUNGLE, TRACK_BIOME_JUNGLE,
        TRACK_BIOME_REFINERY, TRACK_BIOME_REFINERY, TRACK_BIOME_REFINERY,
        TRACK_BIOME_ASTEROID_FACILITY, TRACK_BIOME_ASTEROID_FACILITY,
        TRACK_BIOME_ASTEROID_FACILITY,
        TRACK_BIOME_ICE, TRACK_BIOME_ICE, TRACK_BIOME_ICE, TRACK_BIOME_ICE,
        TRACK_BIOME_VOLCANIC, TRACK_BIOME_VOLCANIC, TRACK_BIOME_VOLCANIC,
        TRACK_BIOME_COASTAL, TRACK_BIOME_COASTAL, TRACK_BIOME_COASTAL,
        TRACK_BIOME_SKYPORT, TRACK_BIOME_SKYPORT, TRACK_BIOME_SKYPORT,
        TRACK_BIOME_SANDSTONE
    };
    unsigned int i;
    CHECK(track_catalog_count() == TRACK_CATALOG_COUNT);
    for (i = 0U; i < TRACK_CATALOG_COUNT; ++i) {
        const RacerTrackInfo *info = track_catalog_get(i);
        CHECK(info != NULL);
        CHECK(info->planet != NULL && info->name != NULL);
        CHECK(track_catalog_biome(i) == expected[i]);
    }
    /* Out-of-range reads fall back through track_catalog_get() to Boonta. */
    CHECK(track_catalog_biome(TRACK_CATALOG_COUNT + 10U) == TRACK_BIOME_SANDSTONE);
    CHECK(track_catalog_biome(0U) == TRACK_BIOME_SANDSTONE);
    CHECK(strcmp(track_catalog_get(2U)->name, "BAROO COAST") == 0);
    puts("PASS: all 25 course entries map procedural scenery by planet metadata");
    return 0;
}
