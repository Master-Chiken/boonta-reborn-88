# GameCube first-render build status

Last updated: 2026-10-15

## Latest CI visible-render verification (2026-10-15)

- Native build and visible-render evidence: [GameCube first-render prototype run #69](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38727969531).
- Relevant merged fixes: [PR #53 — DOL 32-byte section padding and Dolphin diagnostic](https://github.com/Master-Chiken/boonta-reborn-88/pull/53) and [PR #60 — GX per-vertex color pipeline](https://github.com/Master-Chiken/boonta-reborn-88/pull/60).
- Host gameplay/pause tests, DOL-padding tests, GX color-pipeline regression tests, native devkitPPC/libogc build, DOL/ELF structure validation and the 12-second Dolphin Null-backend process smoke: **success**.
- The [Software Renderer/Xvfb frame and runtime logs](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38727969531/artifacts/11970040471) show the curved procedural road, alternating road sections, cyan/orange edge rails, center markers, blue/orange player pod and rival pod.
- The DOL post-processing pads the final section from 139,932 to 139,936 bytes, satisfying Dolphin's 32-byte-rounded section reads.
- The color issue was caused by selecting a material register color rather than the per-vertex color stream. The current GX configuration uses `GX_SRC_VTX` for material color while keeping lighting disabled. A host regression test checks the expected color-channel/vertex-descriptor/TEV configuration.

This validates startup and a visible scene in Dolphin's Software Renderer CI environment. It does **not** prove controller response, long-session frame pacing, a completed race, or behavior on physical GameCube/Wii hardware. The [merged visual quality gate in PR #62](https://github.com/Master-Chiken/boonta-reborn-88/pull/62) rejects screenshots where the lower game viewport is predominantly near-white.

## Verified by GitHub Actions

- Workflow: [GameCube first-render prototype build](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38634127716)
- Source commit: `e24446ecc454473ce4557502e471ba5ed4065abb`
- Build result: **success**
- Automated artifact validation: **success** (`gamecube-demo/tools/validate_artifacts.py` checked DOL section ranges/entry point and ELF32 big-endian PowerPC identity).
- Toolchain: `devkitpro/devkitppc:latest` using libogc/GameCube rules
- Artifacts: `boonta_gc_demo.dol`, `boonta_gc_demo.elf`, and `build.log`
- Artifact size: 445,475 bytes (ZIP); DOL 135,180 bytes; ELF 876,488 bytes.

The artifact was downloaded and inspected. The DOL has a 0x100-byte header, two populated loadable sections whose file ranges are within the artifact, and an entry point that falls within the text section. The ELF is recognized as a big-endian 32-bit PowerPC executable.

DOL SHA-256: `88ea0fdb9ade47a305c3804c855be0363f157fb49d70df7bf909546a8e905a57`

ELF SHA-256: `a42cf06c5b7b9e8b93e1e5336d60bad93cfbde87d440409651251ed78116bf56`

## What this does and does not prove

This earlier run is the first confirmed native GameCube DOL build in the clean-room demonstration path. It verifies compilation/linking and basic artifact structure only. The latest CI runtime evidence is recorded above; it supersedes the historical statement below about Dolphin runtime testing not having been run. The remaining gaps are live controller validation, completed race validation, and hardware behavior.

## Latest headless Dolphin smoke test (2026-10-15)

- Workflow: [GameCube first-render prototype build — PR #49 run](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38722692467)
- Source/PR: [PR #49](https://github.com/Master-Chiken/boonta-reborn-88/pull/49), merged to `main` as `5acd893c0c618f746f16cb6a0af388ecd128637d`.
- Host gameplay-state tests: **success** (speed input, boost activation/energy bounds, lap-boundary crossing).
- Host pause/reset tests: **success**.
- Native devkitPPC/libogc DOL/ELF build: **success**.
- DOL/ELF structure validation: **success**.
- Dolphin process smoke: **success**; Dolphin remained active for the 12-second bounded window using `--batch --video_backend=Null`.
- Runtime log message: “Dolphin remained active for the 12-second process smoke window (elapsed: 12s).”

This smoke test establishes only that the built DOL can be launched and its Dolphin process remains active for the bounded test interval without the workflow's fatal/boot markers. Because the Null video backend is used, it does **not** verify visible GX output, controller response, race progression, frame pacing, or hardware behavior. The earlier experiment with the GUI/OpenGL capture remains inconclusive and is not upgraded to a pass by this headless result.

## Runtime smoke-test checklist

In Dolphin or compatible hardware, verify and record:

- [x] DOL boots in Dolphin without a core-init error.
- [x] The procedural road and placeholder craft are visible in a captured frame.
- [ ] Control Stick or D-pad steers left/right (requires interactive input testing).
- [ ] A accelerates and B brakes (requires interactive input testing).
- [ ] Y resets the demo's distance, steering, and speed (requires interactive input testing).
- [ ] No sustained graphical corruption or severe frame pacing issue (requires a longer session).

Record emulator version, video backend, console/video mode, and any error log when the test is performed. Do not label compile success as a playable full racer.

## Boost mechanic update (2026-10-15)

The prototype includes a rechargeable boost meter. Hold **A + X** to consume energy while accelerating; release the combination to recharge. Boost heat now rises while engaged and cools when released; at 98% heat it enters a latched lockout until heat falls to 60% or below, avoiding frame-to-frame activation oscillation. Host regressions exercise the heat bounds, lockout and cooldown transitions. Active boost increases the procedural course scroll rate and brightens the placeholder thrusters. The HUD shows the boost reserve separately from the speed meter. It now also stops after three counted lap crossings and shows a symbolic checkered flag; press **Y** to reset and start a fresh run. Rival contact/overtake thresholds and the collision speed/lateral response are covered by host unit tests.

- Source commit: `58aa78b002eb47b1f7ddf09e59d1320b784aea83`
- GitHub Actions run: [GameCube first-render prototype build #12](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38705937087)
- Native DOL/ELF build: **success**
- Automated artifact structure validation: **success**
- Dolphin/console runtime test of the boost mechanic: **not run**

The successful build establishes that the updated source compiles and produces structurally valid artifacts. It does not establish that the new meter renders correctly or that the controls behave as intended at runtime; those still require a visible emulator/console test.

## Off-road drag and rail-contact regression coverage

The existing driving loop's off-road speed loss (outside lateral position +/-3.15) and rail recovery (outside +/-3.85) are now factored into dependency-free gameplay helpers used by the live GameCube loop. Host tests cover exact boundaries, symmetric penalties, speed clamping, lateral-position clamping, and the attenuated velocity bounce-back.

These tests verify the programmed transitions only. A visible Dolphin/console run is still required to confirm that the road-edge positions and collision response feel correct in the rendered scene.

