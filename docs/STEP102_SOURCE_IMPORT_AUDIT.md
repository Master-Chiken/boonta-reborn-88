# Step 102 source-import audit

## Current status

A reviewed source-only subset of the supplied Step 102 GameCube/Wii prototype has been imported on the draft branch `import/step102-source-only`. It remains in **PR #17, draft, not merged**. No source from this import has been added to `main`.

The import contains 123 selected source/build/test/tool files, plus this repository's separate review and CI scaffolding. The transport payload was deleted from the branch after verification; no `.import/` files remain in the resulting tree.

## Archive inspected

The supplied `Star_Wars_Racer_GameCube_Step102.zip` contains a native C prototype, a GameCube Makefile, host tests, tools and extensive milestone documentation. Its original README says the overall project is still a prototype; native build and runtime validation had been pending in the archive itself.

The archive's host-side checks were run in a temporary workspace. For the selected import, GitHub Actions also ran `bash tools/release_check.sh`, passed the source-only path checker and ran five source-bundle policy unit tests. Those results are host-test evidence, not a claim of full gameplay correctness.

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

- [Host checks and source-only import workflow](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38625862331) — passed.
- Host regression scripts and the source-only asset policy check — passed.
- Native devkitPPC/libogc build — passed; produced a non-empty `swe1r_gc_port.dol` reported as approximately 301 KiB.
- [Build workflow and artifacts](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38625862331) — artifact `swe1r-gc-step102-source-only` is available while GitHub retains the run artifacts (7 days).

The build explicitly uses `make USE_IMPORTED_SPLINE=0`, so it compiles against the bundled demo/procedural fallback track rather than the excluded PC-mod course centerlines. Compatibility shims in the importer update three API spellings/types for the current devkitPPC/libogc headers and corresponding host mocks: `CARDFileInfo` to `card_file`, `GX_TEXCOORD_NULL` to `GX_TEXCOORDNULL`, and `PAD_BUTTON_Z` to `PAD_TRIGGER_Z`.

**Compile success is not runtime success.** This workflow has not yet verified visible rendering, responsive controller input, race flow, performance, or stability in Dolphin or on hardware.

## Licensing boundary

The ZIP has no root or nested `LICENSE`, `COPYING`, or `NOTICE` covering the source tree as a whole. This repository has a root MIT license, so before merging PR #17 publicly, the repository owner should confirm that the imported source files are original/owned by the project or may lawfully be distributed under the repository's license. The presence of source code in the supplied archive alone is not a license grant. This is an engineering/provenance warning, not legal advice.

## Import guard and remaining gates

The workflow applies a checksum-pinned importer, rejects unsafe archive paths, blocks the identified third-party-derived source/assets, runs host checks, compiles the DOL, and only then commits to the draft PR branch.

Remaining work:
1. Review the complete diff and confirm the imported files' authorship/licensing.
2. Test the DOL with visible video output and a GameCube controller in Dolphin or on hardware.
3. Fix any observed runtime issues without weakening tests.
4. Keep PR #17 in draft until licensing and runtime review are complete. It must not be merged automatically.

Run the local path guard with:

```sh
python3 tools/check_source_import_policy.py
```

The checker is a guardrail, not a license scanner or a substitute for human provenance review.
