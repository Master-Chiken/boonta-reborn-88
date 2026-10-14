# Step 102 source-import gate

Status: **HOLD — provenance and redistribution review required**

This checklist governs the import of `Star_Wars_Racer_GameCube_Step102.zip` into this public repository. The archive has been catalogued in a separate file manifest; the manifest is an audit aid, not permission to redistribute its contents.

## Why the import is gated

The manifest identifies a mixture of candidate source/build/test files, documentation, generated or reference data, 3D geometry, and audio. It specifically flags PC-mod/ROM-derived audit data and spline/model catalog material for provenance review. File names, hashes, and successful tests do not establish authorship, originality, or redistribution rights.

## Import policy

### Eligible for review first
- C source and headers, Makefiles, host tests, and build scripts.
- Documentation that describes independently developed code and does not reproduce protected material.
- Small, synthetic test fixtures created specifically for this project.

Each candidate still needs a license/provenance check. Do not infer that a file is clear merely because it is source code.

### Keep out of the public repository unless rights are documented
- Commercial ROMs, disc images, BIOS files, or extracted game payloads.
- Models, textures, audio, voices, or other assets copied or extracted from a commercial game or third-party mod.
- PC/N64-derived track geometry, spline/centerline data, collision data, model catalogs, and generated audit datasets where the source or redistribution permission is unclear.
- Files whose license, author, origin, or derivation cannot be established.

Keep lawfully owned reference images local; ownership of a copy does not by itself grant redistribution rights.

## Required review for every imported file

Record the following in the manifest or a companion review log:

1. **Path and SHA-256** — identify the exact reviewed bytes.
2. **Type** — code, documentation, test fixture, generated data, or asset.
3. **Origin** — author/repository/source and, where applicable, the upstream commit or URL.
4. **Derivation** — whether it was independently written, generated from original inputs, extracted from a game, or adapted from a mod.
5. **License/permission** — exact license or written permission that covers public redistribution.
6. **Decision** — `ALLOW`, `HOLD`, or `EXCLUDE`, with reviewer and date.
7. **Dependencies** — third-party libraries and their licenses.

Do not mark a whole directory as approved based on a sample. Review individual files and generated datasets separately.

## Safe import sequence

1. Preserve the original archive outside the public Git repository.
2. Extract into a temporary working directory, not directly into `main`.
3. Compare extracted paths and hashes with the catalogued manifest.
4. Exclude all commercial game payloads and all files marked `HOLD_PROVENANCE` or `REVIEW_DATA_PROVENANCE` until reviewed.
5. Review source licenses, headers, embedded data, comments, and tool dependencies.
6. Import only the approved source-only subset on a dedicated branch or pull request.
7. Run host tests and the native devkitPPC/libogc build in CI.
8. Review the diff for accidental binary payloads and secrets before merge.
9. Report test results accurately: host tests passing is not proof of a native build, and a successful native build is not proof of a working game.
10. After a DOL is produced, test it in Dolphin and record boot, graphics, controls, and runtime issues separately.

## Current acceptance criteria

- [ ] Archive-to-manifest hashes verified.
- [ ] Code license and provenance reviewed.
- [ ] PC/N64/ROM-derived data reviewed individually.
- [ ] Models, textures, audio, and preview images cleared or excluded.
- [ ] No ROM, ISO, WBFS, BIOS, or proprietary game payload in the proposed diff.
- [ ] Source-only pull request reviewed.
- [ ] Host tests pass in GitHub Actions.
- [ ] Native GameCube build succeeds with logs retained.
- [ ] DOL boots in Dolphin; runtime status documented.

Until these checks are complete, the Step 102 archive is **not approved for bulk public import**. The immediate safe next step is to review source/build/test files and their provenance, while keeping flagged datasets and assets out of the PR.
