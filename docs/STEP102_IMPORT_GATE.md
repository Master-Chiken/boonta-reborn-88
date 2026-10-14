# Step 102 source import gate

**Status:** audit completed; source import is not yet authorized by the evidence currently recorded here.

## Why this gate exists

The Step 102 archive is the most promising starting point for the GameCube/Wii target, but a passing host test suite is not evidence that the native game builds or runs on hardware. The archive must be reviewed before its files are copied into this public repository.

## Audit recorded on 2026-10-14

The source-only bundle was unpacked into an isolated temporary directory and checked without importing it into the repository.

- Archive inventory: 123 entries.
- Reported host checks: 32 shell checks and 5 Python policy tests passed in the available environment.
- The release-check script's GameCube mode reran host checks, then stopped because `DEVKITPPC` / the devkitPPC GameCube toolchain was not configured.
- No native `.dol` was produced; no Dolphin or physical-console runtime test was performed.
- The bundle README excludes several categories from import, including PC-mod-derived track centerlines, generated/imported asset headers, voice audio, OBJ/MTL assets, commercial disc images, and reverse-engineering/extraction helpers.
- The source bundle has no root license file. The repository's MIT license does not automatically grant rights to third-party material included in a separate archive.

These results describe this source bundle and local audit only; they are not a claim that a native build or playable game exists.

## Required gates before import

1. **Establish provenance.** Record the archive's author, original source URL, version/commit, and redistribution terms.
2. **Review file manifest.** Classify every file as original project code, third-party code/tool, generated data, or game-derived asset. Do not publish files with unknown ownership.
3. **Exclude game payloads.** Never commit commercial ROM/disc images, BIOS files, proprietary extracted textures/models/audio, or other uncleared copyrighted payloads.
4. **Preserve attribution and licenses.** Keep third-party notices with their files and ensure the intended distribution complies with each license. Do not assume that the repository-level MIT license overrides other licenses.
5. **Import on this branch first.** Bring in only cleared source, docs, and tests. Keep uncertain assets and datasets out.
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
