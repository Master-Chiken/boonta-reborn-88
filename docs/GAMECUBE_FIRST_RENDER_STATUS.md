# GameCube first-render build status

Date: 2026-10-14

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

This is the first confirmed native GameCube DOL build in this repository's new clean-room demonstration path. It verifies that the sample can compile and link with devkitPPC/libogc, that a non-empty DOL/ELF is produced, and that the basic DOL/ELF structures satisfy the repository's artifact validator.

It does **not** verify that Dolphin or a console boots the DOL, that GX output is visible, or that controller behavior works in runtime. No Dolphin executable was available in the build-inspection environment, so runtime testing remains **NOT RUN**. The successful GitHub artifact is available until 2026-10-21 (seven-day retention).

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

The prototype now includes a rechargeable boost meter. Hold **A + X** to consume energy while accelerating; release the combination to recharge. Active boost increases the procedural course scroll rate and brightens the placeholder thrusters. The HUD shows the boost reserve separately from the speed meter.

- Source commit: `58aa78b002eb47b1f7ddf09e59d1320b784aea83`
- GitHub Actions run: [GameCube first-render prototype build #12](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38705937087)
- Native DOL/ELF build: **success**
- Automated artifact structure validation: **success**
- Dolphin/console runtime test of the boost mechanic: **not run**

The successful build establishes that the updated source compiles and produces structurally valid artifacts. It does not establish that the new meter renders correctly or that the controls behave as intended at runtime; those still require a visible emulator/console test.
