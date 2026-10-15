# Step 102 source-import audit

## Current status

A reviewed source-only subset of the supplied Step 102 GameCube/Wii prototype has been imported on the draft branch `import/step102-source-only`. It remains in **PR #17, draft, not merged**. No source from this import has been added to `main`.

The import contains 123 selected source/build/test/tool files, plus this repository's separate review and CI scaffolding. The transport payload was deleted from the branch after verification; no `.import/` files remain in the resulting tree.

## Archive inspected

The supplied `Star_Wars_Racer_GameCube_Step102.zip` contains a native C prototype, a GameCube Makefile, host tests, tools and extensive milestone documentation. Its original README says the overall project is still a prototype; native build and runtime validation had been pending in the archive itself.

The archive's host-side checks were run in a temporary workspace. For the selected import, GitHub Actions also ran `bash tools/release_check.sh`, passed the source-only path checker and ran six source-bundle policy unit tests. Those results are host-test evidence, not a claim of full gameplay correctness.

## Provenance and exclusions

The archive README explicitly says its 25 runtime course entries use centerlines derived from the `SWE1R-Mods / SizeMattersNot / RontoSized` PC mod variant. Redistribution rights and provenance for that dataset have not been established.

These paths were excluded from the import:

- `data/reference/pc_track_import_manifest.json`
- `source/track_centerlines_pc.generated.h`
- `source/track_centerline.imported.h`
- `source/track_mesh.generated.h` and `source/track_boundaries.generated.h`
- `assets/voice_en/`, audio, image and model files
- ROMs, disc images, extracted game data, binary dumps and PC/N64 extraction/reverse-engineering helpers

The archive contains `docs/third_party/SWE1R_ASSETS_MIT_LICENSE.txt` naming Alexander Kopetsch. That notice is not evidence that every file in the archive is covered by it. The associated asset/data files were excluded.

## Current build result

The import workflow succeeded:

- [Latest validation workflow](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38629261432) — **success**.
- Host regression scripts and the source-only asset policy check — passed.
- Native devkitPPC/libogc build — passed; produced a non-empty `swe1r_gc_port.dol` reported as approximately 301 KiB.
- Headless Dolphin process smoke test — passed: Dolphin accepted the DOL and remained active until a 12-second timeout.
- Experimental visible Dolphin/Xvfb preview — **not verified**. Multiple 1280×720 captures are nearly pure black (two unique pixel colors, mean RGB around 0.02); the image-content check fails.
- A diagnostic run with GDB caught `SIGBUS` in Dolphin's `Emuthread - Sta`; the current distro binary has no useful symbols in that stack frame, so this does not yet prove whether the cause is a host graphics/frontend issue or a graphics command/runtime defect in the DOL.
- [Latest diagnostic preview frames, GDB log, and screenshot](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38631056369/artifacts/11925279126) — retained for seven days.
- [Successful host/build/runtime checks](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38630233714) — host regressions, native devkitPPC build, and 12-second null-video Dolphin process smoke test passed. The visible frame job is a separate failing/inconclusive diagnostic.
- [Download/browse native build artifact](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38626905351/artifacts/11926156448) — `swe1r-gc-step102-source-only`, retained for 7 days.

The build explicitly uses `make USE_IMPORTED_SPLINE=0`, so it compiles against the bundled demo/procedural fallback track rather than the excluded PC-mod course centerlines. Compatibility shims in the importer update three API spellings/types for the current devkitPPC/libogc headers and corresponding host mocks: `CARDFileInfo` to `card_file`, `GX_TEXCOORD_NULL` to `GX_TEXCOORDNULL`, and `PAD_BUTTON_Z` to `PAD_TRIGGER_Z`.

**The headless Dolphin result is only a process smoke test.** The experimental visible preview remained almost black and failed its image-content check. As a result, visible rendering, responsive controller input, race flow, performance, and stability in Dolphin or on hardware remain unverified.

## Licensing boundary

The ZIP has no root or nested `LICENSE`, `COPYING`, or `NOTICE` covering the source tree as a whole. This repository has a root MIT license, so before merging PR #17 publicly, the repository owner should confirm that the imported source files are original/owned by the project or may lawfully be distributed under the repository's license. The presence of source code in the supplied archive alone is not a license grant. This is an engineering/provenance warning, not legal advice.

## Import guard and remaining gates

The workflow applies a checksum-pinned importer, rejects unsafe archive paths, blocks the identified third-party-derived source/assets, runs host checks, compiles the DOL, and only then commits to the draft PR branch.

Remaining work:
1. Review the complete diff and confirm the imported files' authorship/licensing.
2. Diagnose the Dolphin `SIGBUS` under Xvfb with a useful host stack trace and/or a local interactive emulator test. Current captures are nearly black, so visible graphics and gameplay remain unverified. Then verify controller input, steering, acceleration/braking/boost, race progression, and resets; record results separately from the headless smoke test.
3. Fix any observed runtime issues without weakening tests.
4. Confirm authorship/licensing for imported source files before public redistribution.
5. Keep PR #17 in draft until licensing and visual/runtime review are complete. It must not be merged automatically.

Run the local path guard with:

```sh
python3 tools/check_source_import_policy.py
```

The checker is a guardrail, not a license scanner or a substitute for human provenance review.
