# PC AI and catch-up reference — 2026-10-20

**Queue status (2026-10-21): PARKED reference note.** This PC-only AI comparison is documented and is not the active next task. The sole active research blocker is tracked in [issue #226](https://github.com/Master-Chiken/boonta-reborn-88/issues/226): N64 all-finished state → manager phase/state transition → positively identified results UI/resource/scene. Resume this AI question only after RE-001 is resolved or explicitly handed off.

## Research question

What does the inspected PC reverse-engineering source actually say about opponent pacing, and how does that compare with the current Boonta GameCube prototype?

**Scope boundary:** this is a static code reading of the public PC reverse-engineering repository, not a runtime observation of the retail game and not evidence of N64, Dreamcast, GameCube or Wii internals. Do not copy implementation code into Boonta; the source repository is AGPL-3.0 and is used here as a behavioral reference.

## Pinned source evidence

Reference commit: [`a9863edd4caaa573f89ff634fa7d1cd6d41738ab`](https://github.com/tim-tim707/SW_RACER_RE/tree/a9863edd4caaa573f89ff634fa7d1cd6d41738ab)

- [`swrRace_AI`](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrRace.c): computes a per-racer target speed multiplier and pace offset. It does not directly simulate the pod's flight model.
- [`swrRace_UpdateCatchup`](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrRace.c): calls the AI routine for AI racers, applies a player-relative multiplier for a local human in multiplayer when the other local player is ahead, and copies `paceMultiplier` into `speedMultiplier`.
- [`InitAISettingsForTrack`](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/Swr/swrObj.c): selects per-planet/per-track base AI level and spread, adjusts for the AI Speed setting, and selects scripted-AI / alternate spline variants for several tracks.
- [`swrRace` type fields](https://github.com/tim-tim707/SW_RACER_RE/blob/a9863edd4caaa573f89ff634fa7d1cd6d41738ab/src/types.h): distinguishes `gapToLeader`, `gapToPacer`, `paceMultiplier`, `aiSpeedTarget` and `aiPaceOffsetTarget`, supporting the separation between race position, pacing target and applied speed scale.

## Reconstructed PC behavior (static analysis)

1. **Track-specific setup.** An 8-planet × 4-track table supplies base AI level and spread. The menu setting scales base level by 0.9 / 1.0 / 1.1 for Slow / Average / Fast. A few signature tracks select scripted steering and alternate spline variants. A special-event flag forces spread to 2.0.
2. **Two broad AI roles.** The `AI_SIMPLE` pace-setter uses coarse player-relative speed multipliers (1.06× when leading, 1.4× when the local player is sufficiently far ahead, otherwise 1.1×). Other AI racers derive a target position from rank and spread, with periodic rank-target changes and a pace offset relative to the pace-setter. A tethered AI path can pace directly against a local human's gap.
3. **Bounded catch-up.** The normal AI target is clamped to 0.5×–1.6× in the rank/spread path. The applied `paceMultiplier` approaches the target at 0.2 multiplier units per second, rather than changing instantly.
4. **Finish behavior.** Finished AI racers target 0.65× and reduce look-ahead distance toward a fixed floor.
5. **Local multiplayer path.** For a local human, `swrRace_UpdateCatchup` starts at 1.0× and can raise it up to 1.25× if another local player is ahead. This is distinct from the AI pacing calculation.

These are findings from the reconstructed source text. They should not be described as independently observed retail behavior until validated against a named PC build.

## Comparison with Boonta prototype

The inspected [Boonta GameCube demo source](https://github.com/Master-Chiken/boonta-reborn-88/blob/docs/reverse-engineering-80-20-20261020/gamecube-demo/source/main.c) has a much smaller synthetic rival system in its current race loop:

- rival lateral offsets are generated with a sinusoidal expression based on player distance and rival index;
- rival forward positions are advanced by `boonta_rival_z_after_frame` using player speed and frame scale;
- contact and overtake events cause speed/lateral responses and respawn the rival;
- the shown loop does not implement the PC reference's track-specific AI level/spread table, rank-target state, pace-setter, gap-based catch-up target or smoothed `paceMultiplier` pipeline.

This is an architectural comparison of the inspected source paths, not a claim that Boonta's test rivals are broken. The current prototype is a synthetic acceptance harness; it should not inherit the PC AI complexity until a track/race scenario requires it.

## Cross-platform status

| Platform | AI / catch-up evidence in this pass | Status |
|---|---|---|
| Windows PC | Pinned public source contains the routines and data flow described above. | STATIC-ANALYZED; runtime parity still unverified. |
| Nintendo 64 | No corresponding executable/code or controlled runtime trace inspected in this pass. | UNKNOWN. |
| Dreamcast | No corresponding executable/code or controlled runtime trace inspected in this pass. | UNKNOWN. |
| GameCube / Wii | Current Boonta prototype code inspected; it is not the original retail implementation. | TARGET SOURCE INSPECTED; retail parity UNKNOWN. |

Official StarWars.com retrospective material supports the broad importance of responsive handling, hazards, shortcuts and overheating, but does not specify opponent pacing internals. It cannot independently confirm this AI algorithm: https://www.starwars.com/news/star-wars-episode-i-racer-legacy

## Smallest useful validation scenario

When lawful access to identified original builds and a repeatable capture setup is available, record the same single-player track/scenario on PC, N64 and Dreamcast:

1. use the same track, difficulty, racer and upgrade state where versions permit;
2. record player and opponent race positions / lap transitions at fixed timestamps;
3. record speed changes when the player moves far ahead, falls behind, or passes the apparent pace-setter;
4. repeat with a different difficulty and a second track to separate global settings from track-specific tuning.

Do not claim exact numeric parity from video alone unless the needed state can be measured reliably. Mark platform/build, region, emulator or hardware, settings and repeat count. Keep proprietary executables, ROMs, disc images and extracted assets out of the public repository.

## Decision

**No gameplay code change justified.** The static PC source reveals a richer opponent-pacing model than the prototype's synthetic rivals, but console parity and target acceptance are unproven. PC pod-control/traction is a separate parked question; do not start it while the N64 finish-to-results blocker in issue #226 is active.
