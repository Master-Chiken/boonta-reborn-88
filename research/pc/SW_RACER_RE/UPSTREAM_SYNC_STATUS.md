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

## Local-only work not present in this snapshot

The owner's Mac working copy previously contained an uncommitted safety fix in `dinput_hook/game_deltas/swrRace_delta.cpp` and a locally built `dinput.dll`. Those local artifacts were not on the pinned GitHub fork commit, were not copied here, and the DLL was not validated in a running Windows game. Preserve and review that local work separately before committing or importing it.

## Next reconciliation

1. Compare the 42 upstream-only commits against the pinned fork and identify changes to PC analysis, loader safety, asset format tools and test infrastructure.
2. Retain fork-specific changes unless a specific upstream change is shown to improve them.
3. Do not copy upstream media, game data, symbol databases, trainer archives or vendor code without a separate rights/license audit.
4. Keep all imported PC material under this directory's AGPL-3.0 boundary and keep it out of the MIT GameCube/Wii build.
