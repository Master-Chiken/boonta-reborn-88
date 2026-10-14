# Project status and continuity map

**Snapshot date:** 2026-10-14  
**Purpose:** keep the project history, current GitHub state, earlier uploaded work, validation evidence, and next actions connected in one place.

This document is a navigation index, not a claim that every item listed is already merged or fully validated. Always distinguish the default branch from draft pull requests and private working inputs.

## Current truth at a glance

| Workstream | Current state | What this actually means |
|---|---|---|
| Main branch | Documentation, workflows, and a small Dreamcast/KallistiOS starter | The Step 102 GameCube/Wii source tree is not present on main. |
| Step 102 source archive | Previously supplied as a ChatGPT conversation attachment | Candidate baseline for the native GameCube/Wii work. It is not automatically accessible to GitHub Actions or GitHub AI workflows. |
| GameCube driving demo, PR #13 | Draft; latest checked CI run succeeded | A separate clean-room procedural prototype builds a DOL and passes host tests. It is not an import or port of Step 102. |
| OpenRouter Free reviewer, PR #14 | Merged into main on 2026-10-14 | Manual, comment-only review automation; it does not modify code or merge PRs. A repository secret is still needed to run it. |
| Gemini workflow safety work, PR #15 | Draft; not merged | Proposed workflow hardening. Do not assume the new write gates or instructions are active on main. |
| Dreamcast starter | Separate experimental track | An automated KallistiOS build produced an ELF artifact; visual/gameplay validation remains outstanding. |
| Finished playable GameCube/Wii game | Not achieved | No confirmed end-to-end playable build of the Step 102 project has been produced in the repository. |

## Links to the actual work

### Canonical planning and research
- [Project plan](PROJECT_PLAN.md) — phases, constraints, and acceptance criteria.
- [Technical research](TECHNICAL_RESEARCH.md) — external code research and platform options.
- [Next milestone](NEXT_MILESTONE.md) — source review, host tests, native build, and runtime validation.
- [Build guide](BUILD_GUIDE.md) — record actual target-specific build/test evidence.
- [Source and artifact register](SOURCE_AND_ARTIFACT_REGISTER.md) — inventory of previously supplied inputs and their permitted use.
- [AI agent workflow](AI_AGENT_WORKFLOW.md) and [AI automation setup](AI_AUTOMATION_SETUP.md) — automation behavior and safety rules.
- [Step 102 import audit draft in PR #13](https://github.com/Master-Chiken/boonta-reborn-88/blob/audit/step102-import-gate/docs/STEP102_IMPORT_AUDIT.md) and [Step 102 handoff/access draft](https://github.com/Master-Chiken/boonta-reborn-88/blob/audit/step102-import-gate/docs/STEP102_HANDOFF_AND_ACCESS.md) — detailed archive inventory and access boundaries. These are on the draft PR branch, not main, and do not clear the archive for redistribution.

### Pull requests and CI evidence
- [PR #13 — clean-room GameCube driving prototype](https://github.com/Master-Chiken/boonta-reborn-88/pull/13) — draft proposal; review its source, documentation, and test claims together before merging.
- [PR #13 CI run 53](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38613665560) — succeeded on the PR branch for portable C tests, a devkitPPC/libogc demo build, artifact upload, and a headless Dolphin process smoke test. This is not visual gameplay proof.
- [PR #14 — OpenRouter Free reviewer](https://github.com/Master-Chiken/boonta-reborn-88/pull/14) — merged. Manual trigger only, free route only, and comment-only permissions.
- [PR #15 — Gemini safety gates](https://github.com/Master-Chiken/boonta-reborn-88/pull/15) — draft; the proposed changes are not active on main until reviewed and merged.
- [Dreamcast build evidence](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38567436312) — successful KallistiOS ELF build for the separate starter, not a GameCube build or a bootable Dreamcast disc.

## How the previous work connects

1. **Step 102 archive → audit → controlled source import.** It is the previously supplied source prototype and the candidate main baseline. Before import, the file list and origins/licenses of code, route data, models, materials, and audio must be reviewed. The archive has been reported to contain 359 entries and no obvious LICENSE/COPYING/NOTICE file. A previous project note reports that the archive's host checks and 91 Python unit tests passed in a temporary environment; this has not yet been reproduced by the main-branch CI workflow.
2. **PR #13 demo → native-toolchain proof of concept.** Its gamecube/ code is newly written, clean-room procedural demo code. The CI result proves the shown C tests and demo build ran on that branch. It does not prove Step 102 compiles, because it does not import Step 102. The GameCube README and PR description were updated on the draft branch to document the three procedural rivals, the nine host test cases, and the limits of the headless smoke test. The demo remains separate from Step 102 and still needs interactive visual/input validation.
3. **Main-branch native workflow → future Step 102 CI.** The existing native workflow and its expected source layout must be matched to the actual Step 102 source tree after the import list is approved. Do not report its source-build status using the separate PR #13 demo result.
4. **Dreamcast → separate experiment.** The dreamcast/ directory and its ELF artifact demonstrate a separate KallistiOS starter only. They do not replace the GameCube/Wii milestone.
5. **External research → reference, not an automatic dependency.** The PC-focused reimplementation and asset-tool repositories listed in technical research can inform architecture and file-format research. Their code, data, and licenses are not automatically cleared for reuse.
6. **Private game archives/ROM → controlled local reference only.** User-provided commercial game files must stay out of the public repository and must not be supplied to automated reviewers. GitHub Actions can read repository content, not the user's ChatGPT uploads.

## Validation language to use

- **Host tests passed:** only the named host-side tests passed.
- **Native build passed:** the named source branch compiled with the named console toolchain.
- **Process smoke test passed:** the emulator process remained alive under the recorded test conditions.
- **Visual/input test passed:** only use after someone actually observes rendering and checks controller behavior in an interactive emulator or on hardware.
- **Playable vertical slice passed:** only use after a short race is repeatedly playable with track, pod control, camera, collisions, laps, and stable frame pacing.
- **Release-ready:** not applicable yet.

## Recommended order of work

1. Merge this documentation/continuity map only after reviewing this PR.
2. Review PR #13 and align its claims/docs with its actual clean-room demo; keep it separate from Step 102.
3. Complete the Step 102 path-by-path provenance and redistribution audit, then publish only files that have been cleared.
4. Connect the cleared Step 102 tree to host CI and the real GameCube/Wii build workflow.
5. Validate the generated executable interactively; record visual and controller results separately from compilation.
6. Build the first playable vertical slice before expanding features or claiming an HD remaster.

No local toolchain installation is required for documentation and source review. Do not add billing or a payment method to keep an automation working; stop if a free quota or free endpoint is unavailable.