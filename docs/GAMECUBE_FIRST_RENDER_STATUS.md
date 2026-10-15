# GameCube first-render build status

Last updated: 2026-10-15

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

This section records the initial native-build milestone. At that point, runtime behavior was not yet confirmed. Subsequent DOL boot and visible-render validation are recorded below.

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

## Latest visible Dolphin render validation (2026-10-15)

- Workflow: [GameCube first-render prototype build, run #68](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38727757698)
- Source branch/PR: [PR #59 — GX vertex-color pipeline](https://github.com/Master-Chiken/boonta-reborn-88/pull/59)
- Host gameplay/pause tests, DOL padding unit tests, native devkitPPC/libogc build, and DOL/ELF structural validation: **success**.
- Dolphin headless process smoke (12 seconds): **success**.
- Dolphin Software Renderer/Xvfb visual capture: **success**; the DOL boots and the capture visibly shows the procedural curved road, alternating road surface, cyan/orange rails, center markings, the player placeholder pod, and a rival pod.
- [View the captured PNG and Dolphin logs in the run artifact](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38727757698/artifacts/11969630454). GitHub Actions artifacts have short retention (seven days).
- DOL output is now padded to the 32-byte boundaries used by Dolphin's section loader. The generated DOL is 139,936 bytes; before padding, the last section required four more bytes at the end of the file.
- The GX color path was corrected to source material colors from the per-vertex stream (GX_SRC_VTX) rather than the default register source (GX_SRC_REG). The prior white ground/road capture is the regression this new test is intended to catch.

This validates boot and one visible frame only. It does **not** yet prove controller response, the complete race loop, frame pacing over time, or operation on a physical GameCube/Wii. The follow-up CI capture guard rejects a lower viewport dominated by near-white pixels; its latest run is tracked on the [PR #59 checks](https://github.com/Master-Chiken/boonta-reborn-88/pull/59).

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

