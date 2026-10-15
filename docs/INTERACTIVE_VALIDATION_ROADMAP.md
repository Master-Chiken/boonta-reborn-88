# Interactive validation roadmap — Boonta Reborn 88

Status: implementation plan; no runtime behavior is claimed by this document.

## Objective

Turn the clean-room GameCube/Wii prototype's current build and rendering checks into repeatable evidence that the game responds to input and can complete a three-lap run. Keep the €0 budget and keep the GameCube/Wii target primary.

## Verified baseline and remaining gaps

Current CI already covers host gameplay/pause helpers, native devkitPPC/libogc compilation, DOL/ELF structure validation, a bounded Dolphin Null-backend process smoke test, and a non-blocking Software Renderer screenshot diagnostic.

Those checks do **not** prove live controller response, sustained frame pacing, or completion of a race. Keep those as distinct acceptance gates.

## Work order

### 1. Investigate existing Dolphin input options before inventing tooling

- Record the exact Dolphin package/version available on the CI runner.
- Check documented CLI flags and supported input/movie/TAS mechanisms available in that build.
- Prefer a deterministic, maintained, free mechanism that can be used in GitHub Actions without GUI interaction or paid services.
- Do not assume a command-line flag injects controller input unless an experiment proves it.
- If automation is not viable in the hosted runner, document the exact limitation and a reproducible local interactive test.

**Acceptance:** a checked-in note names the tool/version, exact command, input source, observed effect, and limitations. No claim of input coverage from process survival alone.

### 2. Make meaningful input behavior observable

If the emulator can accept scripted input:

- Start the built DOL with a known input sequence.
- Exercise accelerate, left/right steering, brake, pause/resume and reset where feasible.
- Capture a before/after frame or a deterministic state signal.
- Assert meaningful changes and fail on missing evidence.

If emulator input cannot be automated reliably:

- Keep input and gameplay transitions in dependency-free helper functions where possible.
- Add host tests for both steering directions, acceleration/braking, pause freeze, reset, lap boundaries and finish state.
- Explicitly label these as logic tests, not proof of physical controller or emulator integration.

**Acceptance:** each test reports what it actually observed; no empty/blank screenshot or process-timeout result is mislabelled as gameplay verification.

### 3. Verify the complete race separately

- Run a deterministic three-lap sequence if scripted input is available.
- Verify lap progression, finish marker/state, pause behavior and reset.
- Keep screenshots/logs as workflow artifacts with short retention.
- If only host-level simulation is possible, mark the race as logic-tested but runtime-unverified.

**Acceptance:** an explicit three-lap result is observed, or the blocker and manual test procedure are documented.

### 4. Improve the playable vertical slice

After input validation, prioritize:
1. stable camera-follow behavior and camera timing tests;
2. controllable pod movement and predictable acceleration/braking;
3. track-edge collision and rail response;
4. one complete course and a stable frame loop;
5. a minimal title/pause/restart flow;
6. only then texture/geometry/lighting upgrades.

Avoid parallel Dreamcast work until the GameCube/Wii vertical slice is demonstrably playable.

### 5. Preserve legal and security boundaries

- Do not add ROMs, disc images, BIOS files, proprietary extracted textures/models/audio, or unclear-provenance course data.
- Keep Step 102 source import blocked until authorship/licence and redistribution rights are reviewed.
- Do not place API keys or personal data in issues, code, workflow logs, or artifacts.
- Do not enable paid APIs, billing, paid fallbacks, or auto-merge.
- Do not push directly to `main`; code changes must go through a reviewed pull request.

## Agent instructions

An AI coding agent should first inspect the current default branch and the existing `.github/workflows/gamecube-demo-build.yml`, `gamecube-demo/source/main.c`, `gamecube-demo/source/gameplay_state.h`, and host tests. It should reuse existing helpers and workflows rather than duplicating them. Before coding, report the smallest implementation that provides real evidence, the files to change, and its test plan. After coding, run all relevant host tests and the native build, publish a PR, and report any test it could not run.

## Human-only checks

A human still needs to verify the GitHub repository's branch protection, the free-only Gemini API secret/quota if Gemini is used, and an interactive Dolphin or physical-console session if hosted CI cannot supply reliable input. Never bypass these checks to make a green badge.
