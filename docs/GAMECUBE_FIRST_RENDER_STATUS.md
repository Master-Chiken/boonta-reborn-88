# GameCube first-render build status

Last updated: 2026-10-15

## Latest CI runtime verification (2026-10-15)

- Workflow: [GameCube first-render prototype build #66](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38727099044)
- Merged change: [PR #53](https://github.com/Master-Chiken/boonta-reborn-88/pull/53), merge commit `0ea50271e330dca51bf1caa8d9bd6f951593c86f`.
- Host gameplay, pause/reset, and DOL-padding/artifact utility tests: **success**.
- Native devkitPPC/libogc build and DOL/ELF structural validation: **success**.
- DOL post-processing: **success**; file grew from 139,932 to 139,936 bytes so the final section has the trailing bytes required for 32-byte-rounded reads.
- Dolphin Null-video process smoke: **success**; the DOL process stayed active for the 12-second window.
- Dolphin Software Renderer diagnostic capture: **success**; the [uploaded frame and runtime logs](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38727099044/artifacts/11968079385) are available through 2026-10-22.
- Visual review of that image: it shows the prototype's dark-blue background/horizon, light course surface and placeholder pod silhouette; it no longer shows the earlier “Failed to init core” dialog.

This is the first CI-confirmed visible frame from the clean-room DOL. It is a primitive procedural scene, not a finished racing game. The screenshot proves visible output in this Dolphin/Software Renderer CI environment; it does **not** establish controller response, consistent frame pacing over a long session, rival interactions during a live race, or a successfully completed three-lap run. No hardware test has yet been recorded.

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

- [ ] DOL boots without hanging or crashing.
- [ ] The procedural road and placeholder craft are visible.
- [ ] Control Stick or D-pad steers left/right.
- [ ] A accelerates and B brakes.
- [ ] Y resets the demo's distance, steering, and speed.
- [ ] No sustained graphical corruption or severe frame pacing issue.

Record emulator version, video backend, console/video mode, and any error log when the test is performed. Do not label compile success as a playable full racer.

## Boost mechanic update (2026-10-15)

The prototype includes a rechargeable boost meter. Hold **A + X** to consume energy while accelerating; release the combination to recharge. Active boost increases the procedural course scroll rate and brightens the placeholder thrusters. The HUD shows the boost reserve separately from the speed meter. It now also stops after three counted lap crossings and shows a symbolic checkered flag; press **Y** to reset and start a fresh run. Rival contact/overtake thresholds and the collision speed/lateral response are covered by host unit tests.

- Source commit: `58aa78b002eb47b1f7ddf09e59d1320b784aea83`
- GitHub Actions run: [GameCube first-render prototype build #12](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38705937087)
- Native DOL/ELF build: **success**
- Automated artifact structure validation: **success**
- Dolphin/console runtime test of the boost mechanic: **not run**

The successful build establishes that the updated source compiles and produces structurally valid artifacts. It does not establish that the new meter renders correctly or that the controls behave as intended at runtime; those still require a visible emulator/console test.

## Off-road drag and rail-contact regression coverage

The existing driving loop's off-road speed loss (outside lateral position +/-3.15) and rail recovery (outside +/-3.85) are now factored into dependency-free gameplay helpers used by the live GameCube loop. Host tests cover exact boundaries, symmetric penalties, speed clamping, lateral-position clamping, and the attenuated velocity bounce-back.

These tests verify the programmed transitions only. A visible Dolphin/console run is still required to confirm that the road-edge positions and collision response feel correct in the rendered scene.

