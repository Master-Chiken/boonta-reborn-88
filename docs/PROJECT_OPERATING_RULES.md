# Project operating rules

This is the operating agreement for the public Racer repository. The canonical dashboard is [issue #156](https://github.com/Master-Chiken/boonta-reborn-88/issues/156).

## 1. Work allocation: 80% reverse engineering

The intended engineering effort is **80% reverse engineering and evidence-led research, 20% implementation, testing, integration, and project management combined**.

Measure this in comparable work blocks, not vague intentions: for every ten 45–60 minute blocks, target eight research blocks and at most two combined implementation/testing/management blocks. If a week has less time, keep the same ratio; do not create extra work to meet a quota. Record the block's task ID and result in the active issue. This is an effort target, not a claim that reverse engineering alone makes the game playable.

Reverse-engineering work includes:
- investigating the reviewed PC source/decompilation or an authorized local binary/runtime artifact;
- mapping symbols, functions, structures, formats, state transitions, physics, route/spline systems, and timing assumptions;
- comparing the PC reference with the candidate Step 102 source and the current clean-room GameCube implementation;
- creating evidence-linked behavior specifications with confidence levels, platform boundaries, unknowns, and reproducible follow-up tests.

Reading generic documentation, changing CI, mass-producing reports, and speculative coding do **not** count as reverse engineering. Install or use a tool such as REA/Ghidra only when a specific question requires binary/runtime evidence and the actual target format is supported. Do not spend a work block configuring a tool before confirming that it can analyze the chosen artifact.

## 2. Prevent overload: a one-item work queue

- Keep **one active task** at a time. Only one research question may be in progress; other ideas stay in the backlog.
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
4. **Implement only when justified:** spend part of the 20% engineering allocation on the smallest implementation that follows the evidence. A finding does not automatically require a code change.
5. **Validate:** run exact-head host tests and the native DOL/ELF build. Use visible Dolphin/controller checks for gameplay behavior and mark physical GameCube/Wii results separately.
6. **Record:** link the dossier, commits, tests and unresolved questions to the canonical issue #156.

## 4. Product direction and active tasks

The owner's clarified goal is a **faithful native GameCube/Wii port of the original Star Wars Episode I: Racer, followed by improvements**. Do not optimize the project around an original GameCube/Wii binary: the documented original releases are Windows, Nintendo 64, Mac, Dreamcast and Game Boy Color, with later modern ports; no retail GameCube or Wii edition has been identified. The GameCube/Wii executable is therefore our port target, not a source binary that can be decompiled to recover the original game.

Keep the existing `gamecube-demo/` as a reusable technical foundation: preserve the proven GX submission path, input abstraction, build files, generated original test mesh/texture, host tests and CI diagnostics. Do not mistake its procedural oval, toy rivals or synthetic v1 formats for the finished game, and do not discard or rewrite working infrastructure without evidence.

Use this source hierarchy:
1. **Windows PC** — primary public code/format/behavior reference (`SW_RACER_RE`, the frozen Steam-PC Ghidra reference, and audited PC format tools). Pin executable/repository versions; PC findings are evidence about PC, not automatically about consoles.
2. **Nintendo 64** — independent console behavior/code cross-check. Preserve the completed RE-001 static work and use it where it answers a specific port question; Not64/Ares observations remain emulator-specific.
3. **Dreamcast** — secondary console comparison when a traceable local artifact or reliable public evidence is available.
4. **GameCube/Wii** — native delivery targets. There is no identified retail Racer DOL/REL/ISO for these platforms; use the platform toolchain to build and profile our port, not to pretend a matching original GameCube/Wii decompilation exists.

- **Active research queue:** [issue #226](https://github.com/Master-Chiken/boonta-reborn-88/issues/226). The pinned PC source plus the frozen Steam Ghidra cross-check now document the route graph, split/rejoin progress bake, player cursor/binding, cross-track offset, lap crossing, and AI look-ahead/branch choice. The next single task is to finalize a versioned, platform-neutral route-graph contract and prove its invariants with synthetic host fixtures. Keep `boonta-track-v1` untouched as the existing playable test harness; do not import PC/N64 track data or wire an unproven parser into the runtime.
- The N64 finish-to-Results work remains preserved as historical, platform-specific static evidence with an unverified runtime edge. It is not the current blocker for the native GameCube/Wii port. N64 findings do not establish retail GameCube/Wii parity.
- After the graph contract/fixtures are complete, select one next research question at a time: target-surface/collision binding and coordinate transform; then race/lap/finish state; then pod physics/handling and AI progression. Do not run these tracks concurrently.
- **Existing validation gate:** [issue #126 — interactive three-lap Dolphin acceptance](https://github.com/Master-Chiken/boonta-reborn-88/issues/126). Keep its manual checks distinct from static research and exact-head CI.
- **Existing implementation candidates:** retain and review PRs #264/#268 as separate input work; do not allow controller enhancements to displace the 80/20 research queue. Do not merge, close, or retarget them automatically.
- **Step 102:** its historical 359-file inventory has no top-level license and flags PC-mod-derived centerlines plus assets/data of unclear provenance. The archive itself is not currently available in the active Library for file-by-file inspection. Keep its candidate code/data on HOLD; do not bulk-import or spend time recovering it unless a specific file is needed for the active research question and its provenance can be reviewed.

Tool selection must follow the artifact:
- Use PC disassembly/decompilation and PC format parsers for the original Windows build.
- Use N64Recomp/sp00nznet's symbol/disassembly workflow and local N64 observation for N64-only questions.
- Use `decomp-toolkit`, `objdiff` and CodeWarrior for GameCube/Wii DOL/REL build work, symbol/split work on our own target executable, and matching only when a real matching original binary/compiler pair exists. They do not reveal a nonexistent retail GameCube/Wii Racer build.
- `decompdecomp` lists GameCube/Wii as Beta and requires the original compiler; treat it as an experiment only after checking exact platform support, local requirements and the €0 budget. Do not install or configure tools before an identified artifact and question need them.

## 5. One responsible writer, no branch sprawl

- Use **one write-capable AI/agent at a time**. Read-only research can be parallelized only when it has non-overlapping, explicit questions; to avoid overload, prefer one investigator and one synthesis.
- A substantial change requires an approved scope, bounded file list, and observable acceptance criteria before writing begins.
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