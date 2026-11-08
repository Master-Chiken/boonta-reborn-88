# SW_RACER_RE fork / upstream synchronization status

**Snapshot date:** 2026-11-07  
**Imported fork:** `Master-Chiken/SW_RACER_RE` at `66120be334a3fd38c10a259f3528cffbfed8ddc5`  
**Original upstream:** `tim-tim707/SW_RACER_RE` at `4f898953ecb31c9f02e7ab01e10f62cd9738df0d`  
**Common ancestor:** `a9863edd4caaa573f89ff634fa7d1cd6d41738ab`

At the comparison recorded on 2026-11-07, our fork was **29 commits ahead** and **42 commits behind** the original upstream. These counts describe divergent commit histories, not a line-by-line estimate of reusable code.

## Consolidation decision

- This snapshot preserves the Master-Chiken fork's state and custom work at the pinned commit above.
- The 42 upstream-only commits are **not** merged automatically. The histories have diverged and many files were changed on both sides; a blind merge could discard fork-specific fixes or introduce regressions.
- Review upstream-only work file-by-file and import only changes that are useful to Boonta's research, after checking tests, provenance and licensing.
- Keep the original `SW_RACER_RE` repository as the complete PC research source-of-truth. This Boonta subfolder is a curated text/source snapshot, not a replacement for its Git history.

## Local Mac source delta and binary artifact

The owner's Mac working copy contained a local safety fix in `dinput_hook/game_deltas/swrRace_delta.cpp`. Its source change is now carried in this Boonta snapshot: the favorite-pilot result path includes `tracks_delta.h`, bounds-checks the signed track index against both `trackCount` and `MAX_NB_TRACKS`, and reads `g_aNewTrackInfos` rather than indexing the 25-entry vanilla `g_aTrackInfos` table with a custom track ID. The locally built `dinput.dll` remains a separate artifact: it was not copied, and it has not been validated in a running Windows game.

## Additional fork PR work retained — PR #18

The curated PC snapshot also carries the useful code and test changes from `Master-Chiken/SW_RACER_RE` PR #18 at exact head `95a8026bafb09374c7ab6efa91d8dfdd45a9cec6`:

- `dinput_hook/track_manifest.cpp` and `dinput_hook/virtual_block.cpp` use extracted, header-only policy helpers.
- `dinput_hook/track_manifest_policy.h` and `dinput_hook/virtual_block_policy.h` contain portable validation/range policies.
- Four synthetic tests preserve manifest-policy, virtual-block-policy, manifest integration and virtual-block integration coverage.

**Validation status:** GitHub reported zero check runs on PR #18's exact head when this work was imported. The policy tests are source-only and portable; the integration tests depend on the PC project's Windows/simdjson context. The virtual-block integration test's current-head link/build status is not certified. These tests must be run and any unresolved link/build issue fixed before claiming validation. The PR's GitHub workflow files were not copied into Boonta; the source/test files are kept under this AGPL subtree only.

## Next reconciliation

1. Compare the 42 upstream-only commits against the pinned fork and identify changes to PC analysis, loader safety, asset format tools and test infrastructure.
2. Retain fork-specific changes unless a specific upstream change is shown to improve them.
3. Do not copy upstream media, game data, symbol databases, trainer archives or vendor code without a separate rights/license audit.
4. Keep all imported PC material under this directory's AGPL-3.0 boundary and keep it out of the MIT GameCube/Wii build.
