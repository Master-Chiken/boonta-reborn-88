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

## 2026-11-08 — 42 upstream-only commits: graph-level disposition index

The exact comparison `Master-Chiken/SW_RACER_RE:master...tim-tim707/SW_RACER_RE:master` was re-run against upstream head `4f898953ecb31c9f02e7ab01e10f62cd9738df0d` and fork head `66120be334a3fd38c10a259f3528cffbfed8ddc5`. GitHub reports **42 upstream-only commits and 29 fork-only commits** from common ancestor `a9863edd4caaa573f89ff634fa7d1cd6d41738ab`.

This table is a **complete commit-graph triage index**, not a claim that every changed function has been reviewed or runtime-tested. It classifies all 42 commits by their subject and changed-path group so future work can target the relevant diffs without rediscovering the history. Source-level findings already established above and in the portable-systems note remain separate. An “architecture only” disposition is not authorization to copy AGPL code into the MIT console runtime.

| # | Upstream-only commit | Subject | Initial disposition |
|---:|---|---|---|
| 1 | `c1ac975adc5e590307227a1d1da30c9019e3f419` | Speed up boot: cache WAV headers and rate-limit boot progress presents | PC audio/startup hook; retain cache/invalidation idea only, inspect exact cache key and startup lifecycle before any design adoption |
| 2 | `d57d7e7b3cef6c72d02d0f21daa2f63852e5d5a0` | Add loose per-model replacement (RAWM chunk loader) | PC RAWM/model-block path; do not port format or global loader swap |
| 3 | `a817219683db8a845734ad5ba3ba5adf9ffeec21` | Normalize Blender SWE1R gSPVertex encoding in renderer hook | PC/OpenGL vertex-hook adaptation; not a GX geometry contract |
| 4 | `6be9bc02ec92e0efb06a0359df42c0d8835319b8` | Validate replacement models before renderer traversal | Selected AGPL PC GLTF safety reference already retained; no console code transfer |
| 5 | `694f2ee345f2a6d8500b3856c2db504501f0f71f` | Use named modelblock path pointer | PC loader refactor; keep separate from native resource handles |
| 6 | `09cd337029dfbc559e729166804667a35fa1b18f` | Carve splines and textures into discrete assets | PC extraction workflow; proprietary payload extraction excluded |
| 7 | `f86a2b1c403a441e84d2fa74798751f97b25d180` | Convert a packed track folder into discrete assets | PC pack converter; keep manifest/content-store concept, not PC offsets/layout |
| 8 | `b572eb798e60edeb98790899cf22777f86cb2a90` | Skip pack entries that only re-encode a stock track | PC stock-vs-custom comparison; no transfer without a clean-room owned fixture |
| 9 | `b1769ff07865a2827eba1408f412a7a6cac77603` | Virtual asset blocks at the swrLoader seam | PC virtual-block provider; review loader seam as an architecture pattern only |
| 10 | `9a4bb7fd4d1aabf305cd353dd3a10e04ede2acef` | Route decomp reimplementations at block deltas too | PC loader/decomp integration; keep out of GX runtime |
| 11 | `59aa6fdd600239683550c96b44d006ae8f680d36` | Collect content-store blobs with no manifest references | Content-store maintenance; report-only integrity/orphan checks are useful, destructive deletion excluded |
| 12 | `f1bd583ab51ba2b01086e3eab1314e644a698d76` | Build block views from discrete chunks | PC virtual block layout; no console binary-format assumption |
| 13 | `401b97eebae6b4a61a1bc62bd02a4ad1e9de6bf2` | Drop extract_raw_model.py | PC tooling maintenance; inspect removal rationale only if the script is reconsidered |
| 14 | `6a968a04573a6fffc9facf2e3e0d2f5f925afb44` | Use named block path pointers | PC loader refactor; not a portable API |
| 15 | `1754c26ab4425c72a6bb206a141b9498acb5b430` | Read track.json and install its views | PC custom-track registry/manifest; owned-manifest pattern only |
| 16 | `039a87c2fdb582fad7caa4e045f2ce35c7e61027` | Let track registry choose mapped track assets | PC registry semantics; compare with fork policy before any selective update |
| 17 | `fed12641ae4ded53f488471f62e98d28dcd54b32` | Name registry track by its custom ordinal | PC registry correctness fix; inspect with the adjacent registry commits |
| 18 | `5bbd53cd98956ebc3937e143fafb3b5d1ae42265` | Verify a content-store blob against its own hash | Integrity pattern is useful for Boonta-owned manifests; no PC blobs imported |
| 19 | `b0e0006e2198452d764119ecb4babe7eac5e55f5` | Bump vendored fastgltf 0.8.0 to 0.9.x | Third-party vendor update; excluded pending independent version, licence and regression audit |
| 20 | `6083b121772056d488f7a337c64dbd7e12b256fa` | Drop per-frame glFinish and reduce renderer work | OpenGL-specific performance change; do not infer GX benefit without GX profiling |
| 21 | `b078a31baed93b517f7a159ffa7848cc37f6a66e` | Defer translucent rendering with fewer GL state resets | OpenGL render scheduling; architecture idea only, not portable implementation |
| 22 | `77f63b5ce9acb1e2cafe115064e701b01cc5458d` | Show loaded profile track unlocks in free play immediately | Save/progression UX behavior; native save format and profile semantics not transferable |
| 23 | `3c70b7a88d91f0374439fdedc11beae01f4775d8` | Add render scale, low-end preset and performance overlay | Performance controls/telemetry concept; measure GX before adopting settings |
| 24 | `02b3279b65684d450286c26fed4e029e271f93a3` | Keep unplugged joystick at neutral | Input failure-mode lesson; check the existing PAD/WPAD neutral contract and tests, do not copy SDL/PC device code |
| 25 | `f5ff1285d03df15d4e9bfdabc4ecf9ce9a488286` | Add DualShock 4 / DualSense support | Desktop HID/controller mapping; no GameCube/Wii API reuse |
| 26 | `573384ab2d762857fdc6bde56da0344bfccb44c2` | Merge joystick unplug-neutral fix | Integration commit for row 24; no separate console implementation |
| 27 | `18b24149b0479c07d361ef55c28875de8a308ba` | Merge Sony pad layout support | Integration commit for row 25; controller concepts only |
| 28 | `1b643b540b585f46b5a5b3681d7fef1cfb1027ab` | Merge weak-GPU performance improvements | Integration of PC renderer optimizations; GX profile required |
| 29 | `4feabc6d0b3e3f294931a5c19831066c387111ed` | Merge low-end rendering mode | Integration of PC render-scale/profile controls; GX profile required |
| 30 | `b60376700205ef3d5d6aaa3eb46ddc2e32fbf03d` | Merge free-play unlocks on load | Integration of row 22; save UX idea only |
| 31 | `258f67aa858ba2e281ce8a6791e49c554b85fae0` | Merge startup-delay fix | PC startup integration; not a console timing fix without evidence |
| 32 | `c9b8d8cebf1f408c0a0795340ce90cb9a505ca2a` | Add debug toolbar and tabbed Settings window | PC ImGui debug UI; no native GX UI code reuse |
| 33 | `5e82e899d69f1aaab895142b217f1abae48d6d82` | Debug UI pre-PR review cleanup | PC UI maintenance; review only with rows 32–36 |
| 34 | `89b2e3c496c055bbd976399746a5d92e8b6c89e0` | Guard Win race click with in_race | PC debug UI null-dereference fix; generic state-guard lesson only |
| 35 | `c0b02e4ef14ccb216503782fa98881336077b942` | Keep Multiplayer debug window inside game window | Desktop ImGui window behavior; not relevant to GX runtime |
| 36 | `192d96a5a0c601b6f650a026d3135fdd0a431f3e` | Show F5 hint when toolbar is hidden | Desktop debug UI affordance; no console code transfer |
| 37 | `510caf54cac14ceb1f6a329a38300c1f1274e30d` | Merge debug-toolbar feature | Integration of rows 32–36; PC-only UI |
| 38 | `a9c83c2421eedfcd5b8ba69b1fcd4bdb26ee2e3f` | Merge GLTF validation | Integration of row 4; retain only within its AGPL PC research boundary |
| 39 | `f862fb31e25900edc5b5258f76642fb544045508` | Merge loose-model replacement | Integration of row 2; PC RAWM path excluded from native runtime |
| 40 | `9b81c80881bd055bcfc18c93d7ea6c2f78755bc1` | Merge discrete-asset tools | Integration of rows 6–8; extraction output remains excluded |
| 41 | `44150ba951acfb5beb0b30b2205ecda2823edf0c` | Merge virtual-block provider | Integration of rows 9–14; PC loader only |
| 42 | `4f898953ecb31c9f02e7ab01e10f62cd9738df0d` | Merge track-manifest registry | Integration of rows 15–18; inspect overlapping fork registry policies before any code-level reconciliation |

### What this index establishes — and what it does not

- **Established:** every commit returned by the exact 42-commit upstream-only comparison has an indexed subject, source SHA and initial category/disposition.
- **Not established:** complete per-function review of all changed source, a passing Windows build, in-game behavior, or safe direct portability to GameCube/Wii. The merge commits are integration points, not necessarily independent feature deltas.
- **Next source review:** resolve the highest-value overlaps first: track manifest/registry and virtual-block loader; then the audio/startup cache and GLTF validator; then PC renderer/input changes. Preserve fork-only policy and tests. Vendor fastgltf remains excluded until separately audited.
