# Project operating rules

This is the operating agreement for the public Racer repository. The canonical dashboard is [issue #156](https://github.com/Master-Chiken/boonta-reborn-88/issues/156).

## Mandatory reverse-engineering-first gate

The detailed, binding decision procedure is [`docs/REVERSE_ENGINEERING_FIRST.md`](REVERSE_ENGINEERING_FIRST.md). It applies to every human and AI contributor and every subsystem. Before manual recreation or new implementation, agents MUST inspect existing project work and relevant reverse-engineering sources, establish whether the element can be recovered/extracted/decoded/converted/reused/automatically reproduced, verify platform/version and legal provenance, and document why a rebuild is necessary if reuse is impossible, incompatible, unsafe or legally unavailable. Skipping this gate, duplicating recoverable work, or guessing from another platform is not acceptable. Each task/PR must include the reuse decision and evidence. This is not an 80/20 research quota: investigate only enough to make a sound decision, then implement and test.

## 1. Work method: reuse-first reverse engineering → implementation

### Core doctrine: reuse first, then build in stages

The guiding principle is **reuse before rebuild**. Existing research, source code, prototypes, tools, fixtures, exporters, tests, CI workflows and open pull requests are project assets. Before creating a new subsystem, inspect what already exists, identify its exact revision and ownership, and decide whether it can be reused, extended or safely adapted. The aim is to save months of duplicated work without importing incompatible code or unverified assumptions.

Apply the sequence **MAKE IT WORK → MAKE IT GOOD → MAKE IT FAST**:
1. **Make it work:** deliver the smallest end-to-end behavior that meets a stated acceptance test.
2. **Make it good:** make the implementation understandable, maintainable, testable and integrated with the existing architecture; remove duplication rather than layering another parallel system on top.
3. **Make it fast:** optimize only after profiling or other measurable evidence identifies a real bottleneck. Do not trade correctness for speculative speed.

**Trust does not replace control.** Before reusing external or internal work, verify its exact revision, license scope, provenance, platform/API compatibility and the specific behavior we need. A README claim, an AI statement, a green badge, an old CI run or success on another platform is not proof that the current Boonta branch works. Validate the exact commit being reviewed; rerun affected checks after changes; distinguish host tests, native builds, emulator process/render checks, interactive gameplay and physical-hardware acceptance. Record uncertainty as unknown, never as fact. Preserve human review and never auto-merge.

The project uses evidence-led reverse engineering to avoid inventing systems that have already been studied. The initial broad discovery phase and complete-game inventory are sufficiently covered by PR #282 and the existing PC/N64/Dreamcast dossiers. The old 80% research / 20% implementation split is **not a permanent gate** and must not keep implementation blocked.

Use completed reverse engineering as a practical engineering input:
- `PC_AI_AND_CATCHUP_REFERENCE_2026-10-20.md` records PC-only AI pace targets, catch-up smoothing, rank/progress separation, route-cursor look-ahead and branch choice.
- `PC_POD_CONTROL_SPEED_TRACTION_2026-10-20.md` records the PC control → target-turn → speed → traction stages and their relationships.
- PR #284 and the RE-002 matrix preserve PC race-progress cursor/rebind/offset evidence and consumer mapping.
- PR #282 is the complete-game system inventory; do not reproduce it.
- PR #274 is the existing native route-runtime candidate; review/reuse it instead of creating another route graph.
- PR #278 preserves the audited GameCube/Wii static-analysis toolchain boundaries. It does not establish an original GameCube/Wii Racer binary.

Read only dossier sections that answer the selected implementation question. The large `RE-001-route-spline-progress.md` file is approximately 452 KB; never ingest the whole file when targeted excerpts suffice. Issue attachments, images, videos, downloadable artifacts, binaries, ROMs, disc images and BIOS files are not needed for ordinary gameplay work and must not be sent to model providers.

After the bounded matrix gate and the current one-active-task automation gate are cleared, target **at least 60% of work effort on gameplay implementation, integration and regression testing**. Keep reverse engineering targeted: answer concrete design questions, preserve source/version/license/evidence labels, and never treat PC/N64/Dreamcast findings as GameCube/Wii facts without target evidence. Prefer one compiling vertical slice with host tests and exact-head native build evidence over another broad report.

For each system: discover existing Boonta code and PRs; identify the relevant RE contract; write an independent behavior specification; implement the smallest testable slice; then validate host C tests, native DOL/ELF build and applicable Dolphin diagnostics. Keep human-operated Dolphin and physical hardware acceptance separate.

## 2. Prevent overload: bounded, non-overlapping queues

- The owner may authorize more than one research track only when scopes and deliverables do not overlap. As of 2026-11-03, #226 is the native GameCube/Wii research and implementation queue; #279 is a read-only comparative PC/N64/Dreamcast evidence queue.
- Keep **one write-capable task** at a time. Do not run two implementation tasks or two investigations of the same subsystem concurrently. A read-only #279 source audit may proceed while #226 owns native-target runtime work because the scopes are explicitly separated.
- Keep at most **three next-up items** visible in issue #156. Close or park duplicates instead of opening more tracking issues.
- Each research item must answer one concrete question and produce one bounded dossier. Do not begin implementation while the evidence is still ambiguous.
- A research dossier must record: question, exact source/revision, evidence links, observed facts, inferences, target-platform caveats, unknowns, Step 102 mapping status, and the next reproducible test.
- Finish each work block with a small note: what was established, what was not established, and the next action. Do not start an unrelated task mid-session.
- Do not create a branch for every note. Gather research evidence in the active issue/dossier; make one focused documentation PR when a coherent result is ready.
- No new CI/AI workflow or repository policy change unless it removes a demonstrated blocker to the active task. The read-only AI coordinator remains manual-only; scheduled autonomous engineering is permitted only through the separately gated Boonta Autonomous Loop.

## 3. Evidence-led study → map → implement → validate

1. **Study:** inspect the exact source, binary, format or observed runtime behavior needed to answer one question.
2. **Map:** compare findings against the actual candidate Step 102 files and the current GameCube prototype. Mark absent/unavailable inputs explicitly; never pretend a mapping was checked if the archive is unavailable.
3. **Specify:** write the behavior independently, state what is fact vs inference, and choose a measurable acceptance test.
4. **Implement when justified by the evidence:** build the smallest useful testable slice that follows the behavior contract. Once the current gates clear, gameplay implementation/integration/testing is the majority effort; a finding does not automatically require a code change.
5. **Validate:** run exact-head host tests and the native DOL/ELF build. Use visible Dolphin/controller checks for gameplay behavior and mark physical GameCube/Wii results separately.
   The maintained GameCube first-render workflow must run both on relevant PRs and on pushes to protected `main` and `dev`, so a gameplay merge receives post-merge validation as well as pre-merge PR validation.
6. **Record:** link the dossier, commits, tests and unresolved questions to the canonical issue #156.

## 4. Product direction and active tasks

The owner's clarified goal is a **faithful native GameCube/Wii port of the original Star Wars Episode I: Racer, followed by improvements**. Do not optimize the project around an original GameCube/Wii binary: the documented original releases are Windows, Nintendo 64, Mac, Dreamcast and Game Boy Color, with later modern ports; no retail GameCube or Wii edition has been identified. The GameCube/Wii executable is therefore our port target, not a source binary that can be decompiled to recover the original game.

Keep the existing `gamecube-demo/` as a reusable technical foundation: preserve the proven GX submission path, input abstraction, build files, generated original test mesh/texture, host tests and CI diagnostics. Do not mistake its procedural oval, toy rivals or synthetic v1 formats for the finished game, and do not discard or rewrite working infrastructure without evidence.

Use this source hierarchy:
1. **Windows PC** — primary public code/format/behavior reference (`SW_RACER_RE`, the frozen Steam-PC Ghidra reference, and audited PC format tools). Pin executable/repository versions; PC findings are evidence about PC, not automatically about consoles.
2. **Nintendo 64** — independent console behavior/code cross-check. Preserve the completed RE-001 static work and use it where it answers a specific port question; Not64/Ares observations remain emulator-specific.

   - **Static-recomp reference:** [sp00nznet/racer](https://github.com/sp00nznet/racer) is a high-value N64 behavior/runtime comparison. Its README at `694c5663b3a7c30e2862fc240344f34683f99a9c` reports menu-to-race execution, controls, EEPROM saves, audio and two-player netplay; the overall playable-build milestone remains in progress. Its ROM-generated game code is not tracked and is expressly outside its MIT grant. Use only observable N64 behavior/runtime lessons; never copy generated functions or infer GameCube/Wii parity.
   - **RE workbench:** [decomp.anything](https://github.com/giveen/decomp.anything) at `b410ac528ded6fa9adb7fad4f000cebbf5f341e6` supports MIPS/N64 and PowerPC/GameCube/Wii workflows (dtk-template, DOL/REL/disc splitting, m2c drafts, CodeWarrior matching and REA analysis). The app is local Linux x86-64/Windows WSL2, not macOS or hosted. Its app is MIT but bundled toolchains have separate licenses. It cannot supply a missing original Racer GameCube/Wii binary; Boonta already has dtk/objdiff CI, so use it only if it resolves a concrete analysis gap.
3. **Dreamcast** — secondary console comparison when a traceable local artifact or reliable public evidence is available.
4. **GameCube/Wii** — native delivery targets. There is no identified retail Racer DOL/REL/ISO for these platforms; use the platform toolchain to build and profile our port, not to pretend a matching original GameCube/Wii decompilation exists.

- **Native-target queue:** [issue #226](https://github.com/Master-Chiken/boonta-reborn-88/issues/226), GameCube/Wii-target research and implementation.
- **Comparative evidence queue:** [issue #279](https://github.com/Master-Chiken/boonta-reborn-88/issues/279), active read-only PC/N64/Dreamcast system/source matrix; no gameplay code or platform-parity claims. The platform-neutral route-graph contract and synthetic host fixtures are complete and were integrated by [PR #271](https://github.com/Master-Chiken/boonta-reborn-88/pull/271) into `dev` at `cdc4f35c7533fdefee428da5eabca324c247f618`. The exact post-merge validation [#41528877645](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/41528877645) completed successfully on 2026-11-03: host state/gameplay/route tests, native DOL/ELF build and artifact validation, Dolphin null-backend process smoke, and the optional scripted Software Renderer frame diagnostic all passed. This is automated evidence, not human-operated gameplay or hardware acceptance.
- **Next code task after the one active automation-ledger gate clears:** review the existing [PR #274](https://github.com/Master-Chiken/boonta-reborn-88/pull/274) as the single candidate for the native GameCube/Wii route-runtime hookup. Its latest inspected head is `f8c9488fa8bfe1f6434309c7b84c075304a43c54`; exact-head GameCube build, host pause/resume tests, Dolphin process smoke, optional software-render frame diagnostic and Wii64 tooling checks passed in [#41703965812](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/41703965812) and [#41703965867](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/41703965867). It remains open with no review; required human approval is still a merge gate. Review scope is to verify the runtime's use of the route graph/cursor, preserve the existing `boonta-track-v1` compatibility path, check whether branch history actually drives gameplay or remains test-only, and record the remaining collision/surface/finish gaps. Do not create another route-runtime branch or duplicate PR. Do not merge PR #274 automatically. If the review finds a gap, record one precise next test or blocker before changing code.
- Keep [PR #269](https://github.com/Master-Chiken/boonta-reborn-88/pull/269) separate as a draft input-backend candidate; physical Wii/Under Control Classic Controller acceptance remains outstanding. RE-002 is active only as read-only comparative evidence. Do not import PC/N64 track data or treat platform-specific observations as GameCube/Wii proof.
- The N64 finish-to-Results work remains preserved as historical, platform-specific static evidence with an unverified runtime edge. It is not the current blocker for the native GameCube/Wii port. N64 findings do not establish retail GameCube/Wii parity.
- **RE-001 next steps:** after the existing graph-contract work, select native-target questions one at a time (surface/collision binding, race/lap/finish, then pod physics/handling and AI). RE-002 does not implement these systems; it contributes PC/N64/Dreamcast comparative evidence as separately scoped in #279.
- **Existing validation gate:** [issue #126 — interactive three-lap Dolphin acceptance](https://github.com/Master-Chiken/boonta-reborn-88/issues/126). Keep its manual checks distinct from static research and exact-head CI.
- **Existing implementation candidates:** retain and review PRs #264/#268 as separate input work; do not allow controller enhancements to displace the route-runtime review and playable-race roadmap. Do not merge, close, or retarget them automatically.
- **Step 102:** its historical 359-file inventory has no top-level license and flags PC-mod-derived centerlines plus assets/data of unclear provenance. The archive itself is not currently available in the active Library for file-by-file inspection. Keep its candidate code/data on HOLD; do not bulk-import or spend time recovering it unless a specific file is needed for the active research question and its provenance can be reviewed.

Tool selection must follow the artifact:
- Use PC disassembly/decompilation and PC format parsers for the original Windows build.
- Use N64Recomp/sp00nznet's symbol/disassembly workflow and local N64 observation for N64-only questions.
- Use `decomp-toolkit`, `objdiff` and CodeWarrior for GameCube/Wii DOL/REL build work, symbol/split work on our own target executable, and matching only when a real matching original binary/compiler pair exists. They do not reveal a nonexistent retail GameCube/Wii Racer build.
- `decompdecomp` lists GameCube/Wii as Beta and requires the original compiler; treat it as an experiment only after checking exact platform support, local requirements and the €0 budget. Do not install or configure tools before an identified artifact and question need them.

## 5. One responsible writer, no branch sprawl

- Use **one write-capable AI/agent at a time**. Read-only research can be parallelized only when it has non-overlapping, explicit questions; to avoid overload, prefer one investigator and one synthesis.
- A substantial change requires a bounded scope, named files, and observable acceptance criteria before writing begins. Manual writers require owner approval; the separately authorized autonomous loop may select its scope only from the canonical queue and must record its criteria before editing.
- One implementation task normally means one short-lived branch and one PR. Base new branches on the current intended target.
- `main` is stable/release integration and must not receive direct pushes. Gameplay changes target protected `dev`; docs/policy may target `main`.
- `archive/branch-heads-20261019` is a protected recovery archive, never a development base and never merged wholesale.
- AI agents may open PRs but must not merge them, enable auto-merge, bypass branch rules, alter repository settings, force-push, or delete branch refs.
- Automatic deletion of merged PR head branches is enabled. Target a branch budget of 10 refs or fewer; a warning is a review trigger, not permission for unattended deletion.

## 6. AI and budget controls

- Project budget: **€0**. No paid model, billing, payment method, paid fallback, paid cloud resource or upgrade. If free quota is exhausted, stop.
- The read-only Gemini coordinator remains manual-only and posts requested reports to canonical issue #156.
- The owner has authorized scheduled autonomous task selection and branch/PR work through `.github/workflows/boonta-autonomous-loop.yml`; it is not a background process outside GitHub Actions. It runs on a six-hour schedule and serializes writer runs.
- Autonomous writes require `GEMINI_AUTONOMOUS_ENABLED=true`, `GEMINI_FREE_TIER_CONFIRMED=true`, the `GEMINI_API_KEY` secret, and the GitHub App `APP_ID` variable plus `APP_PRIVATE_KEY` secret. The manual plan/execute path remains separately gated by `GEMINI_WRITE_ENABLED=true` and its owner approval command.
- Agents may open or update focused PRs, but may not merge, enable auto-merge, alter settings/secrets/variables, force-push or delete branches. If free quota is unavailable, stop without a paid fallback.
- One agent-generated summary or green configuration check is not evidence that the game works.
- Never send secrets, ROMs, disc images, BIOS, commercial archives, extracted proprietary models/textures/audio, or uncertain-provenance data to hosted AI services, public issues, CI artifacts, or the repository.

## 7. Source, platform and licensing boundaries

- `SW_RACER_RE` is a Windows-PC reverse-engineering/decompilation reference, not a verified GameCube implementation. Its documented analysis coverage is not the same as complete implementation.
- Upstream `SW_RACER_RE` code is licensed AGPL-3.0 according to its repository; link to source and summarize observations by default. Do not copy/adapt source into the project's existing license without a deliberate license review and owner decision.
- Step 102 remains on hold until proposed files have a documented origin, license/provenance decision and redistribution disposition. Do not bulk-import its archive.
- Keep PC facts, Step 102 facts, and GameCube/Wii hypotheses in separate fields. A PC finding alone never proves console behavior.

## 8. Definition of done

A task is complete only when:
1. its question has been answered with traceable evidence, or the exact blocker is recorded;
2. its fact/inference/unknown distinctions and platform boundaries are explicit;
3. the dossier links to the relevant sources and next reproducible check;
4. any approved code change stays within scope and has exact-head tests;
5. the outcome and one next action are recorded in issue #156.

These rules prioritize deep understanding over parallel coding, automation churn, and a growing backlog.