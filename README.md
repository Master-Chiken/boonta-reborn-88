# Boonta Reborn — console research and clean-room prototypes

An unofficial fan research project investigating console options for a racing-game-inspired project. The repository contains research, build experiments, and a separate clean-room Sega Dreamcast starter. It is **not a completed port or remaster** of Star Wars: Episode I — Racer.

> Unofficial fan project. Not affiliated with or endorsed by Lucasfilm, Disney, Nintendo, Sega, or the original developers/publishers. Third-party names and trademarks belong to their respective owners.

## Current status

- **Dreamcast starter:** CI compilation succeeded using KallistiOS. [See the successful build and ELF artifact](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38568111117).
- **Dreamcast gameplay:** not implemented. The starter currently prints a console message and polls controller input; it has not yet been verified in an emulator or on real hardware.
- **GameCube/Wii research:** separate and experimental. No verified native port or working gameplay build is claimed.
- **Browser prototype:** developed separately in Replit; it is not a Dreamcast build.

## Project tracks

- [Dreamcast starter and build notes](dreamcast/README.md) — clean-room KallistiOS test program.
- [Dreamcast investigation plan](docs/DREAMCAST_PORT_PLAN.md) — status, limitations, and next milestones.
- [GitHub Actions build workflow](.github/workflows/dreamcast-build.yml) — compiles the Dreamcast starter and stores the ELF artifact.
- [Technical research](docs/TECHNICAL_RESEARCH.md) — background research and caveats.

## Legal and asset policy

This repository should contain original project code, documentation, scripts, build configuration, and lawful test assets only.

**Do not commit commercial game ROMs, disc images, BIOS files, extracted proprietary textures/models/audio, or other copyrighted game data.** Keep local dumps and generated disc images outside Git. Review licenses and provenance before copying or distributing third-party code or assets.

The repository's MIT license applies only to eligible original project material, not to third-party code, names, or assets.

## Next milestones

1. Add a visible original test screen to the Dreamcast starter.
2. Display controller input on screen and test it in an emulator if available.
3. Build a basic original 3D scene.
4. Continue the browser prototype as a separate playable experiment.
5. Only claim features as working when build or test evidence supports the claim.
