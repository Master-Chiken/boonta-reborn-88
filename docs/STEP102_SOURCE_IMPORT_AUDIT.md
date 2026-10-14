# Step 102 source-import audit

## Purpose

Prepare a safe, reviewable path for bringing the user's GameCube/Wii prototype into this repository without publishing commercial game dumps or unverified third-party assets. This document is an audit gate, not a claim that the archive has already been imported.

## Archive inspected

The supplied `Star_Wars_Racer_GameCube_Step102.zip` contains a native C prototype, a GameCube Makefile, host tests, tools and extensive milestone documentation. Its README says the project is still a prototype; the native devkitPPC/libogc build and in-emulator/console runtime validation were still pending in the archive itself.

The archive's host-side checks were run in a temporary workspace: the release shell checks and 91 Python tests passed after restoring executable bits described by the archive. Those results do not prove a native build or gameplay correctness.

## Provenance and exclusions

The archive README explicitly says its 25 runtime course entries use centerlines derived from the `SWE1R-Mods / SizeMattersNot / RontoSized` PC mod variant, not a verified clean retail PC dump. The archive also includes media/model files whose redistribution provenance is not established by the archive's root-level licensing information.

For the first public import, keep these items out unless their redistribution rights and source provenance are separately verified:

- `data/reference/pc_track_import_manifest.json`
- `source/track_centerlines_pc.generated.h`
- `source/track_centerline.imported.h`
- `assets/voice_en/` and other audio/media files
- `assets/geometry/*.obj`, `*.mtl`, and other model/texture exports
- ROMs, disc images, extracted commercial data, binary dumps, generated files derived from them, and local private data

The archive contains `docs/third_party/SWE1R_ASSETS_MIT_LICENSE.txt` naming Alexander Kopetsch. That license is not, by itself, proof that every file in the archive is covered by it. Preserve third-party notices only for the specific files that can be shown to be covered.

## Safe import scope

A future source-only import may include original C source and headers, Makefile/build scripts, host tests, generic developer tools, and technical documentation once their authorship and dependencies are reviewed. Do not enable imported PC centerlines by default. Retain a procedural test track until a clean, independently authored track dataset is available.

## Current repository status

- The small clean-room prototype is tracked separately in PR #13; it is not the Step 102 port.
- The existing native build workflow expects a top-level `Makefile` and `source/` tree, and intentionally fails until they are actually present.
- This audit branch does not copy the archive or its source files into the repository.
- No change in this branch is merged into `main`.

## Next gates

1. Confirm the source files intended for import are original project code or have clear compatible licenses.
2. Import only reviewed text source, build configuration, tests, and documentation.
3. Run host tests in GitHub Actions.
4. Build a non-empty GameCube `.dol` with devkitPPC/libogc.
5. Test actual visible rendering and controller input in Dolphin or on hardware; report this separately from a successful compile.
6. Keep all actions free-only: GitHub-hosted public-repository CI, no paid API fallback, no billing activation.

## Reproducible local audit

Run:

```sh
python3 tools/check_source_import_policy.py
```

The checker rejects known excluded paths and risky binary/media extensions. It is a guardrail, not a license scanner or a substitute for human provenance review.
