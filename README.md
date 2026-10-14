# Boonta Reborn 88 — enhanced GameCube/Wii reconstruction

An unofficial reverse-engineering and homebrew project aiming to reconstruct the original *Star Wars: Episode I – Racer* (1999) as faithfully as possible, using documented PC research and comparisons with the PC, Dreamcast, and Nintendo 64 editions. The ambition is the best visual quality achievable with modern techniques while remaining playable natively on GameCube/Wii, plus bonus content. This is the destination, not the current completion status.

This is **not yet a finished remaster or verified port of the original game**. A separate clean-room GameCube prototype compiles to a DOL in GitHub Actions. A selective 123-file Step 102 source-only candidate exists on the separate `import/step102-source-only` branch in draft PR #17; it is not merged into `main`, and its source licensing/provenance and visible runtime behavior remain unresolved.

## Actual end goal

- **Final goal:** a faithful reconstruction of the original game's core experience, then the highest-quality visual remaster feasible on GameCube/Wii, using modern rendering/asset-production techniques adapted to the consoles' real limits, plus original extras and bonus content.
- **Important hardware distinction:** native GameCube/Wii output is standard-definition (typically up to 480p), not native 720p/1080p HD. The goal is therefore HD-inspired asset quality and the best possible rendering within console budgets—not a promise of true HD output or PC-class modern effects. A literal 720p/1080p build would require a different target platform or external upscaling.
- **Research inputs:** existing PC reverse-engineering documentation/code, the PC edition, and lawful local analysis of Dreamcast and Nintendo 64 editions. Compare versions to identify gameplay rules, data formats, track/vehicle differences and platform-specific behavior; do not assume one edition's formats match another.
- **Current source candidate:** `Star_Wars_Racer_GameCube_Step102.zip`, audited separately from this repository. It is the strongest existing GameCube/Wii-oriented prototype candidate, but its provenance and assets still require review. It contains C gameplay/rendering code, a GameCube Makefile, research/build tools, documentation, and host-side tests.
- **Prototype scope described by its README:** 25-course catalog, 23 vehicle presets/variants, racing physics, drift/boost/heat/damage, rival AI, pickups/hazards, single race, championship, time trial, Mirror Cup, HUD, and save/progression scaffolding.
- **Host tests:** I ran the archive's host release suite in a clean temporary environment. All host shell checks and 91 Python unit tests passed after restoring the executable bits encoded in the ZIP. This is not a native GameCube build and is not a runtime test.
- **First native DOL:** `gamecube/boonta_demo.dol` is built by CI from original procedural code. This verifies the toolchain and compilation only, not emulator boot or playability.
- **Separate exploratory track:** `dreamcast/` is a small clean-room KallistiOS starter. It is not the main game prototype and must not be confused with the GameCube/Wii code.

## Current repository limitation

The current `audit/step102-import-gate` branch is still far short of the final goal. The selective Step 102 candidate lives on the separate `import/step102-source-only` branch and remains under review in [draft PR #17](https://github.com/Master-Chiken/boonta-reborn-88/pull/17). Its archive has no license covering the whole source tree, and visible Dolphin rendering/playability has not been proven. The clean-room prototype in `gamecube/` remains a toolchain demo, not the final foundation. See [`gamecube/README.md`](gamecube/README.md).

## Legal and asset policy

- Do not commit commercial ROMs, disc images, BIOS files, extracted proprietary textures/models/audio, or other copyrighted game payloads.
- The source prototype documents that some course centerlines derive from a modded PC spline dataset; review provenance and redistribution rights before publishing those generated data files.
- Review the license and provenance of external reverse-engineering projects before reusing their code.
- Keep any lawful user-owned game images local. The repository should contain original code, documentation, tools, tests, and assets that are cleared for redistribution only.

## Reverse-engineering workbench

The [PC/Dreamcast/Nintendo 64 comparison matrix](docs/VERSION_COMPARISON_MATRIX.md) tracks the systems that must be measured or documented before implementation: physics, vehicles, tracks, AI, items, modes, UI, graphics, audio, progression, and performance. The [Step 102 path-review register](docs/STEP102_PATH_REVIEW_REGISTER.md) tracks provenance and redistribution clearance; all unreviewed paths remain on hold. The [platform decision note](docs/PLATFORM_DECISION.md) explains why GameCube versus Wii remains open and how the N64-on-Wii emulator can serve as a reference without being mistaken for the remaster itself. The goal is faithful reconstruction first, visual improvements and bonus content second.

## Next milestones toward the real goal

1. Complete the [path-by-path provenance review](docs/STEP102_PATH_REVIEW_REGISTER.md) of the Step 102 source archive and select only code/tools/docs with documented clearance.
2. Build the actual full GameCube/Wii-oriented prototype from that source, not treat the tiny procedural demo as the final foundation.
3. Reproduce the host tests, compile with devkitPPC/libogc, and validate boot/render/controller input in Dolphin.
4. Create a version-comparison matrix for PC, Dreamcast and Nintendo 64: physics, tracks, vehicle stats, AI, items, menus, modes, progression, and file formats. Mark each claim as measured, documented, or still unknown.
5. Reconstruct and validate original gameplay systems and content using documented reverse-engineering findings; keep proprietary ROMs/disc images and unclear extracted assets outside the public repository.
6. Once the faithful playable baseline works, improve graphics within GameCube/Wii limits, add original bonus content, and measure performance on both targets.
7. Package and document GameCube and Wii builds separately.

The Dreamcast test branch is separate and is not a substitute for these milestones.


## Cloud development (no local installation)

The repository includes a Codespaces dev-container for working in the browser with the devkitPPC/GameCube toolchain. See [Cloud development workflow](docs/CLOUD_DEV_WORKFLOW.md). Codespaces has usage quotas on free personal plans; stop or delete the cloud workspace when finished.

## Free development tools

The project is intended to stay at **€0**: see [Free tooling and setup requirements](docs/FREE_TOOLING.md) for GitHub Actions, the Codespaces quota, the optional Gemini agent, and the actions that still require the owner. Do not enable paid billing.

## Optional AI-assisted workflow

A GitHub-hosted Gemini agent can review the repository and help prepare code changes from GitHub comments. Setup and safety rules: [AI automation guide](docs/AI_AUTOMATION_SETUP.md). It only sees files committed to this repository; ChatGPT uploads of the original PC/N64 games are not automatically available to it.
