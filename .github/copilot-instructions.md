# Instructions for AI coding agents

## Project direction
- The primary goal is a playable enhanced racing prototype targeting native GameCube/Wii homebrew.
- The audited source archive is `Star_Wars_Racer_GameCube_Step102.zip`. It contains a C source prototype, devkitPPC/libogc Makefile, tools, docs, and host tests, but it has not yet been imported into this repository.
- Prioritize importing/reviewing the source-only prototype and making `.github/workflows/native-build.yml` pass. Do not continue expanding the Dreamcast starter unless the project owner explicitly asks for Dreamcast work.
- The Dreamcast starter under `dreamcast/` is a separate technical experiment, not the primary game code.
- Do not describe the project as a completed remaster or verified native port.
- Host tests and mock-libogc syntax checks do not prove a real GameCube/Wii cross-build or runtime compatibility.

## Build and validation workflow
1. Review the source archive README and Step 102 native-build handoff before importing code.
2. Import source, headers, Makefile, tests, and build tools selectively. Exclude ROMs, disc images, BIOS files, and commercial game payloads.
3. Review every third-party dependency and asset for license/provenance before publication.
4. Run `bash tools/release_check.sh` in a suitable environment for host checks.
5. Run the native build with devkitPPC/libogc and verify that a non-empty `swe1r_gc_port.dol` is produced.
6. Test the DOL in Dolphin or on hardware when possible. Report compile, boot, rendering, and gameplay status separately.
7. Keep changes small, testable, and in a branch/PR. Do not auto-merge generated changes.

## Legal and asset constraints
- Never commit commercial game ROMs, disc images, BIOS files, extracted proprietary assets, or copyrighted game data.
- The prototype README says its imported route data derives from a modded PC `RontoSized` spline dataset. Do not publish those generated route headers without a provenance and redistribution-rights review.
- Use original code/assets or material with documented permission.
- Review licenses before copying code from external reverse-engineering or open-source game projects.
- Do not expose secrets or private dumps in logs, prompts, issues, or commits.

## Engineering constraints
- Keep GameCube/Wii platform code separate from the Dreamcast/KallistiOS starter.
- Prefer documented libogc/GX APIs and the official devkitPro template.
- Never disable or weaken tests merely to obtain a green build.
- If a native build fails, preserve the first compiler error and build log and fix the cause.
