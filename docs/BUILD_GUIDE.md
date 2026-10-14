# Build guide and evidence record

This guide separates the default branch from draft pull requests and records exactly what each known build result proves.

## Current build status

- **Step 102 native GameCube/Wii source build on main:** not verified. The Step 102 source tree is not present on main yet.
- **Clean-room GameCube demo:** a native devkitPPC/libogc build succeeded on draft PR #13. This is a separate procedural demo and does not verify the Step 102 archive.
- **Dreamcast starter:** a KallistiOS ELF build succeeded for the separate experiment. It is not a GameCube build or a bootable Dreamcast disc image.
- **Interactive runtime validation:** no confirmed visual/controller/playable-race result is recorded here yet.

## Build evidence

| Date | Target and branch | Workflow/result | What is proved | What is not proved |
|---|---|---|---|---|
| 2026-10-14 | Clean-room GameCube demo, PR #13 branch | [CI run 54](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38615309738) succeeded | Portable race-logic host tests ran; devkitPPC/libogc built a demo DOL; artifact upload succeeded; headless Dolphin process smoke test succeeded. | Not a Step 102 build. Dolphin used a null video backend and a short process smoke test; no visual rendering, controller handling, or complete race was verified. Changes are still in a draft PR. |
| 2026-10-14 | Dreamcast/KallistiOS starter on main | [Build run](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38567436312) succeeded | The starter compiled to an ELF artifact in the cloud toolchain. | Not a GameCube/Wii target, not a bootable CDI/GDI image, and not visual/gameplay validation. |
| Earlier project note | Step 102 archive in a temporary environment | Host shell checks and 91 Python unit tests were reported as passing | A previous host-side test run was reported for the supplied source archive. | Not currently reproduced in this repository's CI; not a native cross-build or runtime result. |

## Next reproducible path: Step 102

1. Complete the file-by-file source/license/provenance manifest described in [the source register](SOURCE_AND_ARTIFACT_REGISTER.md).
2. Import only reviewed files into a review branch. Keep game archives, ROMs, disc images, BIOS, and unclear extracted assets outside the repository.
3. Confirm the actual source layout against the native workflow and update the workflow only when the reviewed source is present.
4. Run the archive's host test suite in GitHub Actions without weakening tests to obtain a green run.
5. Build with the documented devkitPPC/libogc container and record the exact command, toolchain version, compiler output, and artifact path.
6. Launch the produced DOL in an interactive Dolphin environment or on suitable hardware. Record boot, rendering, controls, race start, and any failure separately.
7. Build a small repeatable playable vertical slice before expanding features.

## Build policy

- Prefer free GitHub-hosted CI/cloud toolchains; no local install should be required for planning and documentation.
- Do not commit generated disc images, commercial game data, ROMs, BIOS files, or unclear third-party payloads.
- Record commands and test outcomes only after they actually run.
- Preserve the distinction between host tests, native compilation, emulator process smoke tests, visible output, controller input, and playable gameplay.
- Free API/model quotas can change. If a free route is unavailable, stop rather than enabling billing or a paid fallback.