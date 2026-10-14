# Boonta Reborn 88 — GameCube/Wii prototype

An unofficial research and homebrew project aiming toward a playable racing prototype inspired by *Star Wars: Episode I – Racer* (1999), with native GameCube/Wii as the main target.

**Status: source imported on a draft PR, native DOL builds, visible gameplay not yet verified.** This is not a finished remaster, and a successful compile or headless emulator smoke test is not proof that rendering and controls work correctly.

## Current implementation

The draft [PR #17 — Step 102 source-only import](https://github.com/Master-Chiken/boonta-reborn-88/pull/17) now contains a selective source-only subset of the supplied Step 102 prototype: C gameplay/rendering modules, build configuration, selected host tests, mocks, and developer tools.

The source describes 25 named course entries, 23 pod presets/variants, arcade vehicle physics, rival AI, track pickups and hazards, multiple race modes, HUD, and save/progression scaffolding. These are prototype features, not a claim of parity with the commercial game.

## Verified in GitHub Actions

Latest completed validation on October 14, 2026:

- Source-only path/asset policy and host regression suite: **passed**.
- Native devkitPPC/libogc cross-build: **passed**.
- Non-empty `swe1r_gc_port.dol`: generated, about 301 KiB.
- Headless Dolphin process smoke test: **passed**; Dolphin accepted the DOL and remained active through a 12-second timeout using the null video backend.
- [Latest CI run and build artifact](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38626905351).

The import build uses `make USE_IMPORTED_SPLINE=0` and a bundled demo/procedural track. It excludes the identified PC-mod-derived route centerlines and manifests, imported centerline headers, generated mesh/boundary exports, audio, model/texture exports, ROMs, disc images, extracted commercial data, and related reverse-engineering helpers.

**Still outstanding:** a visible Dolphin or real-console test for picture output, controller input, steering, acceleration/braking/boost, race progression, reset/pause behavior, performance, and stability.

## Provenance and redistribution boundary

The supplied source ZIP does not contain a license covering the source tree as a whole. Its README also identifies a course-centerline dataset derived from a modded PC spline variant. That data is excluded from the first public import. Before the draft PR is merged into this public repository, confirm that the imported source files are original/owned by the project or may lawfully be redistributed under this repository's MIT license. The presence of source code in an archive is not itself a license grant.

Never commit commercial ROMs, disc images, BIOS files, proprietary assets, private dumps, or content whose redistribution rights are unclear. The automated path policy is a guardrail, not a license scanner.

## Next steps

1. Review the complete [PR #17 diff](https://github.com/Master-Chiken/boonta-reborn-88/pull/17) and establish source ownership/licensing.
2. Run the DOL in Dolphin with video enabled and a GameCube controller; capture actual results separately from CI's headless process smoke test.
3. Fix any demonstrated rendering/gameplay issues and add regression coverage.
4. Keep the PR in draft until the rights review and visible runtime check are complete. It is not merged; `main` remains unchanged.

## Cloud-only workflow

Host tests and native builds run in GitHub Actions so a local devkitPro installation and large local downloads are not required for this stage. The CI workflows do not use paid AI APIs or require billing. Build artifacts expire according to the retention displayed by the GitHub Actions run.

The separate `dreamcast/` folder is an exploratory KallistiOS starter. It is not the main GameCube/Wii prototype.

## Optional AI-assisted workflow

The repository includes an optional Gemini/OpenRouter integration plan. Keep it in free-only mode, never commit API keys, and do not paste confidential material into public-repo AI review workflows. See [AI automation setup](docs/AI_AUTOMATION_SETUP.md).
