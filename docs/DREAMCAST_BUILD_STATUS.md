# Dreamcast build status

## First successful automated build

- **Date:** 2026-10-14
- **Workflow run:** [Dreamcast KallistiOS build #38567436312](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38567436312)
- **Result:** successful
- **Artifact:** `boonta-reborn-dreamcast-elf`
- **Artifact size:** approximately 990 kB (uploaded by GitHub Actions)
- **Artifact expires:** 2027-01-12, according to GitHub Actions metadata.

This confirms that the current clean-room starter compiles into a KallistiOS ELF file in the CI container. It does **not** yet confirm execution on a real Dreamcast or emulator, and it is not a bootable disc image (`.cdi`/`.gdi`). The program currently reports startup/controller input through KOS console output; graphical video output and game systems are still future milestones.

## Next milestones

1. Add a simple visible video output using documented KallistiOS APIs.
2. Test controller input without repeated console flooding.
3. Add a minimal original 3D scene and camera.
4. Design a clean-room racing prototype: placeholder track geometry, a controllable vehicle, camera follow, acceleration/braking/steering.
5. Only later investigate lawful compatibility/data-import options; do not commit commercial game disc images or proprietary extracted assets.
