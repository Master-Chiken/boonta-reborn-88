# Cross-platform findings — 2026-10-20

These are preliminary source-backed findings, not runtime-verified facts.

| Topic | Finding | Status |
|---|---|---|
| Core gameplay | Official retrospective identifies overheating, shortcuts, hazards and local split-screen among defining features. | DOCUMENTED; broad features only. |
| Cinematics | Secondary history reports PC/Mac cinematics absent on N64 due to cartridge constraints; a contemporary Dreamcast preview advertised prerendered cinematics. | DOCUMENTED; verify exact regional releases. |
| Audio | Reviews report a reduced N64 soundtrack compared with PC/Dreamcast. | DOCUMENTED by reviews; no track-by-track comparison yet. |
| Graphics | N64 Expansion Pak supports a high-resolution mode; Dreamcast was advertised as higher resolution. | DOCUMENTED; does not prove shared assets or renderer. |
| Dreamcast online time comparison | Mentioned in a contemporary preview; actual implementation/service status not verified. | ANNOUNCED, not runtime-confirmed. |
| Exact track/racer/mode parity | Not inventoried by identified build/region. | UNKNOWN. |
| N64-specific data | Pinned OpenSWE1R/swe1r-tools README says its Comp model-block decompressor applies only to N64. | STATIC-DOCUMENTED; evidence of at least one platform-specific data path. |

## Sources

- Official overview: https://www.starwars.com/news/star-wars-episode-i-racer-legacy
- Contemporary Dreamcast preview: https://www.gamespot.com/articles/star-wars-episode-i-racer-preview/1100-2540691/
- N64 review: https://www.nintendolife.com/reviews/n64/star_wars_episode_i_racer
- Dreamcast review: https://www.gamespot.com/reviews/star-wars-episode-i-racer-review/1900-2557867/
- Pinned tooling README: https://github.com/OpenSWE1R/swe1r-tools/blob/239911513834e19d1530fc908b6dc40eabea25fc/README.md

## Next checks

1. Inspect version-pinned PC source files for track/racer/race-mode tables and record executable assumptions.
2. Build a version-specific N64 inventory, distinguishing region/revision and Expansion Pak settings.
3. Investigate Dreamcast file-layout/tooling evidence before assuming it follows PC or N64.
4. Record exact counts only when a named version-specific source supports them.
5. Do not change gameplay code until the inventory identifies a concrete discrepancy against Boonta.
