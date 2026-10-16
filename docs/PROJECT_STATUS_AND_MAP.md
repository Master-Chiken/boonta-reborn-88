# Project status and continuity map

**Snapshot date:** 2026-10-16  
**Purpose:** connect the current public repository, earlier supplied inputs, validation evidence, research documents, and next actions without confusing implementation status with source-import permission.

This is a navigation index. Treat each status as time-bound and follow the linked pull request or CI run for the authoritative record. The clean-room demo and the separately supplied Step 102 source bundle are different workstreams.

## Current state

| Workstream | Current state | Meaning |
|---|---|---|
| Protected main | Current main commit: `4abe93624c9c16e2e37aca82b0d8936d66f5f612` at this snapshot | Keep changes reviewable through PRs; do not force-push or merge unreviewed stale branch histories. |
| Clean-room GameCube prototype | Integrated under `gamecube-demo/` | Procedural racing prototype with native DOL/ELF build and automated host/runtime diagnostics. It is not an import or port of Step 102. |
| Runtime CI evidence | [Run 38902484737](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38902484737) succeeded for the recorded host regression tests, native devkitPPC/libogc build, Dolphin headless smoke, and Software Renderer diagnostic | Automated evidence only; it does not establish interactive controller acceptance or physical-hardware behavior. |
| Interactive acceptance | Still pending | Verify reset, accelerate/brake, steering, boost, pause, three-lap completion, and extended-session stability in an interactive emulator or on hardware. |
| Step 102 source-only bundle | HOLD pending provenance and redistribution review | The separate 123-file bundle's earlier host-test report is historical evidence, not current CI or permission to publish the files. Keep unclear-provenance code and generated route data out of main. |
| SW_RACER_RE research | Documentation/reference only | Use pinned source links and summarized observations to derive hypotheses; do not copy AGPL source or third-party assets without a deliberate license review. |
| Wii64 archive research | Documentation/reference only | Variant inventory, hashes, and test plans are research records; do not commit emulator binaries, ROMs, or commercial assets. |
| Branch consolidation | Recovery-first | Compare divergent branches and recover unique docs/tests/scripts before considering deletion. A lower branch count is not the primary success metric. |

## Canonical documents

- [Technical research](TECHNICAL_RESEARCH.md) — public research references, platform distinctions, and current implementation caveats.
- [Source and artifact register](SOURCE_AND_ARTIFACT_REGISTER.md) — previously supplied input inventory and rules for keeping private/commercial materials out of the public repository.
- [SW_RACER_RE study plan](SW_RACER_RE_STUDY_PLAN.md) and [behavior matrix](SW_RACER_RE_BEHAVIOR_MATRIX.md) — PC research mapped to testable hypotheses without assuming console equivalence.
- [Next milestone](NEXT_MILESTONE.md) — interactive validation checklist and acceptance criteria.
- [Build guide](BUILD_GUIDE.md) — target-specific build and test evidence.
- [Step 102 source-import gate](SOURCE_IMPORT_GATE.md), [bundle audit](STEP102_BUNDLE_AUDIT.md), [provenance review](STEP102_SOURCE_PROVENANCE.md), and [host validation record](STEP102_HOST_VALIDATION.md) — scope, exclusions, and limits of the earlier bundle checks.
- [Wii64 archive review](WII64_ARCHIVE_REVIEW.md), [Episode I Racer profile note](WII64_EP1_RACER_PROFILE.md), [reference test plan](WII64_REFERENCE_TEST_PLAN.md), and [archive fingerprints](WII64_ARCHIVE_FINGERPRINTS.md) — reference-environment notes, not native Boonta implementation.

## Validation language

- **Host tests passed:** only the named host-side tests passed.
- **Native build passed:** the named source branch compiled with the named console toolchain.
- **Process smoke test passed:** the emulator process stayed alive under the recorded conditions.
- **Interactive visual/input test passed:** use only after a person actually observes rendering and tests controller input in an interactive emulator or on hardware.
- **Playable vertical slice passed:** use only after repeatable race completion with control, camera, collisions, laps, and stable frame pacing.
- **Release-ready:** not established.

## Recovery-first branch workflow

1. Inventory each divergent branch's unique paths and commits before making cleanup decisions.
2. Compare its documents, tests, scripts, and source against current main; distinguish genuinely new material from stale versions and already-integrated files.
3. Import unique low-risk documentation and test assets through a reviewable PR, preserving provenance and historical dates.
4. For source changes, extract small, understandable changes into current code and add tests rather than merging old branch histories wholesale.
5. Keep Step 102 source and generated data on hold until rights and provenance are established.
6. Delete a branch only after its useful contents have been recovered or proven redundant and its exact head is verified as safely integrated.

No entry in this map substitutes for a license review, interactive test, or current CI result.
