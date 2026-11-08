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

## Selected upstream GLTF safety update — 2026-11-08

The following first-party source changes were retained from `tim-tim707/SW_RACER_RE` commit `6be9bc02ec92e0efb06a0359df42c0d8835319b8` (AGPL-3.0):

- Added `dinput_hook/gltf_validate.cpp` and `.h`: bounds-checks renderer-consumed accessors, buffer views, embedded images, material/texture references, nodes and animation keyframes using 64-bit range arithmetic.
- Updated `gltf_utils.cpp/.h` to use a single open/parse/validate path and reject malformed replacement assets before renderer setup.
- Updated `renderer_utils.cpp` and `replacements.cpp` to use the validation result and avoid walking invalid assets.

The existing PC CMake source glob includes new `.cpp` / `.h` files in this directory. This is a **source-reference import, not a certified Windows build**: the snapshot intentionally omits third-party vendor trees and no PC Windows runtime test has been run here.

**Explicitly not imported:** the same upstream commit modifies the vendored `fastgltf-0.8.0/src/fastgltf.cpp` for malformed base64 data URIs, percent-decoding bounds, accessor min/max bounds and a node-weight parsing fix. Those are third-party dependency changes; keep them as a separately audited follow-up rather than silently modifying or vendoring the dependency.

## Next reconciliation

1. Compare the 42 upstream-only commits against the pinned fork and identify changes to PC analysis, loader safety, asset format tools and test infrastructure.
2. Retain fork-specific changes unless a specific upstream change is shown to improve them.
3. Do not copy upstream media, game data, symbol databases, trainer archives or vendor code without a separate rights/license audit.
4. Keep all imported PC material under this directory's AGPL-3.0 boundary and keep it out of the MIT GameCube/Wii build.


## 2026-11-08 — second upstream delta triage

Latest original upstream checked: [`tim-tim707/SW_RACER_RE` at `4f898953ecb31c9f02e7ab01e10f62cd9738df0d`](https://github.com/tim-tim707/SW_RACER_RE/tree/4f898953ecb31c9f02e7ab01e10f62cd9738df0d), dated 2026-11-05. The divergence remains 42 upstream-only commits versus 29 fork-only commits from the imported fork baseline `66120be334a3fd38c10a259f3528cffbfed8ddc5`. This is not a fast-forward candidate.

### Findings retained as references, not copied into the console runtime

- The upstream comparison contains PC-hook changes to its debug UI/ImGui, renderer hooks, performance stats, model replacement, track manifests/registry and virtual-block handling. These are specific to the Windows DirectInput/OpenGL mod and are not GameCube GX implementations.
- The upstream adds PC controller-rumble and sound-hook files. These may inform separately specified input/audio behaviour, but their Win32/game-hook dependencies prevent direct use in the GameCube/Wii executable.
- New Python utilities cover custom-track pack conversion, raw-asset extraction, content-store management and raw-model validation. They are useful leads for the PC format workflow only. Do not run them on game data in CI or publish any extracted or converted proprietary output.
- The local fork snapshot's policy-oriented `track_manifest.cpp`, `track_registry.cpp` and `virtual_block.cpp` are materially different from the current upstream versions (the reviewed copies are respectively 530/346, 159/126 and 754/468 lines). They carry fork-specific policy logic and are covered by the isolated tests in this branch. Do not overwrite them with shorter upstream files without a function-by-function diff and a replacement test.
- The selected first-party GLTF validator import remains present. The vendored fastgltf change remains excluded: it needs an independent dependency-version, license and regression review before any update.

### Decision

Keep the curated snapshot and the upstream repository as separate PC research references. Do not merge the 42-commit history, copy the vendor tree, or move AGPL PC code into the MIT GameCube/Wii runtime. The already imported, tested portable policy helpers are retained under this AGPL research boundary; no additional upstream source files were copied in this triage.

## 2026-11-08 — third upstream delta triage: asset pipeline utilities

The following first-party upstream scripts were inspected at the exact current `tim-tim707/SW_RACER_RE:master` file revisions:

- `scripts/convert_track_pack.py` (`aa540828258ddfbb4382df84c1f4ae245e8c1d2f`): compares PC custom-track model/spline/texture blocks against stock PC blocks, reads the Windows PE `TrackInfo[25]` table at virtual address `0x004BFEE8`, carves changed records and writes SHA-256-addressed blobs plus manifests. The useful architecture is content-addressed storage, explicit block-index texture references, and manifest-driven track assembly. The PE address, stock table, RAWM/RAWS/RAWT record layouts and PC block assumptions are **not** portable to N64 or GameCube/Wii without independent format proof.
- `scripts/extract_raw_asset.py` (`2af4a28696b5d47b3309e075d705b9a52628cc07`): extracts individual PC model/spline/texture records and offers a byte-for-byte round-trip check. The inspected upstream version trusts offset-table values and has fewer range/alignment checks than the hardened fork-side copy. **Do not replace the hardened fork copy with this upstream version.** The round-trip test concept is useful for future Boonta-owned formats.
- `scripts/validate_raw_model.py` (`dd554c3e6e4bb423477d35409ec5a783e59f4f51`): validates PC RAWM mask/model sizes, tags, pointer bounds and texture-reference markers. It assumes the PC loader's exact data contract; its low-level `be32` reads and optional stock-table reads are not comprehensively bounded in this upstream revision. Keep the hardened fork implementation as reference and do not treat RAWM as a GameCube GX asset format.
- `scripts/gc_content_store.py` (`31697dfa23bc003fbff1f7369eef0b5ca52dd483`): checks manifest references, missing blobs, orphan blobs and optional SHA-256 integrity. It is a useful design pattern for a future Boonta-owned content store. Its default is report-only; `--delete` is destructive and must never be used in an automated pipeline without a separate dry-run, explicit approval and backup policy.

### Disposition

**No additional script was copied or executed.** These tools require local PC game installation/block inputs and can emit extracted proprietary payloads. CI must remain synthetic-only. Retain only the architecture lessons (content-addressed assets, manifest references, lossless round-trip tests, integrity checks and report-only garbage collection) as research requirements. Before implementing a console asset pipeline, first establish the target format from independently sourced evidence and write synthetic fixtures; do not transplant PC offsets, record tags, pointer rules or file layouts.