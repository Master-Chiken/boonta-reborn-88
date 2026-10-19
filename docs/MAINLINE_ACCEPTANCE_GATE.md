# Mainline acceptance gate

This checklist is required before merging source imports or describing the GameCube/Wii prototype as playable.

## Source and redistribution
- [ ] Record the origin, author/licensor, and license for every imported source group.
- [ ] Confirm the repository's license can legally cover each imported file; a root license does not relicense third-party material.
- [ ] Keep ROMs, disc images, BIOS files, extracted commercial textures/models/audio, and assets with unclear redistribution rights out of Git.
- [ ] Keep PC/N64-derived route data and generated geometry excluded until provenance and redistribution rights are documented.

## Reproducible validation
- [ ] Run host regression tests from a clean checkout and retain the CI run URL.
- [ ] Build the native DOL/ELF using the pinned devkitPPC/libogc toolchain; retain the build log and artifact hashes.
- [ ] Treat a successful build and a headless Dolphin process smoke test as compile/boot-process evidence only—not proof of visible rendering or gameplay.
- [ ] For a playable claim, capture a visible frame and record controller input, a completed race, and any runtime failures on a named emulator version or physical console.

## Merge decision
- [ ] Review the full PR diff against the intended base and resolve branch divergence.
- [ ] Confirm required CI checks pass on the exact PR head SHA.
- [ ] Obtain project-owner approval for provenance and merge readiness.
- [ ] Merge only after the checks above are complete; do not bypass a failed or missing gate.

## Reporting language
Use precise statuses: **host tests passed**, **native build passed**, **headless process smoke passed**, **visible rendering verified**, and **interactive race verified** are separate claims. Never infer a later status from an earlier one.
