# Instructions for AI coding agents

## Project direction
- The current investigation target is Sega Dreamcast, using KallistiOS (KOS).
- Keep the existing GameCube/Wii prototype and its `.dol` build workflow separate.
- Do not describe a build as successful unless CI or a reproducible local command confirms it.
- Make small, testable changes and inspect CI logs after changing build files.

## Legal and asset constraints
- Never commit a commercial game disc image, BIOS, ROM, or extracted proprietary assets.
- Use original code and assets or material with documented permission.
- Keep analysis of user-supplied files local; commit only technical notes and clean-room code.

## Development workflow
1. Read `docs/DREAMCAST_PORT_PLAN.md` and `dreamcast/README.md`.
2. For Dreamcast work, edit only `dreamcast/` unless a shared document needs updating.
3. The Dreamcast CI workflow builds with a KallistiOS toolchain container and uploads the ELF artifact only after a successful build.
4. Prefer KOS APIs documented by the upstream KallistiOS project. Avoid inventing SDK calls.
5. If a test fails, diagnose from logs and fix the underlying issue rather than disabling the test.