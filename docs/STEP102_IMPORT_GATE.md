# Step 102 source import gate

**Status:** the actual source-only archive has now been recovered and re-tested in an isolated workspace. Import into the public repository remains gated on provenance and redistribution terms; the source has not been copied into GitHub yet.

## Why this gate exists

The Step 102 archive is the most promising starting point for the GameCube/Wii target, but passing host tests is not evidence that the native game builds or runs. The archive must be reviewed before its files are copied into this public repository.

## Audit recorded on 2026-10-14

The actual source-only bundle was recovered from the conversation attachment, decoded, and unpacked into an isolated temporary directory. It was checked without importing its source files into the repository.

- Archive inventory: 123 entries; one entry is a Python bytecode cache and should not be imported.
- Reproducible host result: all 32 `tests/*_host.sh` scripts and all 5 Python policy tests passed using `bash tools/release_check.sh`.
- The GameCube build path was not validated because `DEVKITPPC` / the devkitPPC GameCube toolchain is not configured in this environment.
- No native `.dol` was produced; no Dolphin or physical-console runtime test was performed.
- The bundle README says PC-mod-derived centerlines/manifests, imported centerline headers, generated mesh/boundary headers, voice audio, OBJ/MTL assets, ROM/disc images, extracted data, and PC/N64 extraction/reverse-engineering helpers were excluded. Keep the default `USE_IMPORTED_SPLINE=0` procedural/demo track path.
- The source bundle has no root license file. The repository's MIT license does not automatically grant rights to third-party material in a separate archive.

These results describe the source bundle and isolated host tests only. They do not establish native-build success, runtime success, or permission to redistribute every file publicly.

## Required gates before import

1. **Establish provenance.** Record the archive's author, original source URL, version/commit, and redistribution terms.
2. **Review file manifest.** Classify every file as original project code, third-party code/tool, generated data, or game-derived asset. Do not publish files with unknown ownership.
3. **Exclude game payloads.** Never commit commercial ROM/disc images, BIOS files, proprietary extracted textures/models/audio, or other uncleared copyrighted payloads.
4. **Preserve attribution and licenses.** Keep third-party notices with their files and ensure the intended distribution complies with each license. Do not assume that the repository-level MIT license overrides other licenses.
5. **Import on a working branch first.** Bring in only cleared source, docs, and tests; omit `__pycache__` and unclear assets/datasets.
6. **Run reproducible host checks.** Record the exact command, environment, and test counts in CI.
7. **Build natively.** Use devkitPPC/libogc and archive the build log and `.dol` artifact. Treat compile success as separate from runtime success.
8. **Test in Dolphin.** Record whether it boots, renders, reads controls, and can complete a race. Do not claim gameplay based only on a successful compile.

## First playable vertical slice

After import and native build are reproducible, prioritize this order:

1. Initialize video and controller input.
2. Render a simple track using cleared or procedural geometry.
3. Move one pod with stable frame-time-based physics.
4. Add camera follow and track boundaries/collision.
5. Add lap/checkpoint logic and a finish condition.
6. Add a minimal HUD and restart flow.
7. Only after this slice is verified, expand into championship progression, time trial, unlocks, bonuses, AI opponents, and content breadth.

## Release checklist

- [ ] Archive origin and redistribution terms recorded
- [ ] Every imported file has a provenance/license classification
- [ ] No uncleared proprietary game assets or images included
- [ ] Host regression suite passes in GitHub Actions
- [ ] Native devkitPPC/libogc build produces a DOL
- [ ] DOL boots in Dolphin
- [ ] Input, rendering, and race completion tested
- [ ] README reports tests/build/runtime separately
