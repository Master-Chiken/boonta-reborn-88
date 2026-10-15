# Step 102 import hold — provenance and generated-track data

**Decision: HOLD.** Do not merge the source-import candidates [PR #17](https://github.com/Master-Chiken/boonta-reborn-88/pull/17) or [PR #22](https://github.com/Master-Chiken/boonta-reborn-88/pull/22) as-is.

This hold is not a finding that every file is unlawful. It means the available evidence does not establish authorship, origin, license, or permission to redistribute the affected files in a public repository.

## Evidence-backed blockers

- The Step 102 archive has no top-level `LICENSE`, `COPYING` or `NOTICE` file identified in the audit. Individual source origin and redistribution rights remain unresolved.
- `source/track_centerline.generated.h` appears in the import candidates even though the bundle README says imported/generated centerline data is excluded. The exact derivation of this header and its inputs remain unverified.
- PR #22 includes `data/demo_track_points.csv` and `data/demo_track_edges.csv`. The available notes say to verify that demo track CSVs are synthetic/original and not extracted or mod-derived; that verification is not yet documented.
- PC-mod-derived course-centerline data is explicitly described in the source archive audit. Keep PC/N64/ROM-derived geometry and generated datasets out unless origin and redistribution permission are documented.
- A successful host test, native build or headless Dolphin process smoke test cannot establish authorship or legal redistribution permission, and does not verify visible gameplay.

## Guardrail workflow

The `Step 102 source-import provenance guard` scans known held paths, media/binary/model formats, generated-centerline files, archives and Python bytecode. It also has small unit tests for the path policy.

A pass is only a path-policy result. It is **not** a license audit, source originality check, complete malware scan, or approval to publish. Review every proposed source/data group individually and record path, hash, origin, derivation, license/permission, decision, and reviewer.

## Required before reconsidering either PR

- [ ] Explain the origin and authorship of each imported code family.
- [ ] Establish a license or explicit redistribution permission that covers each file.
- [ ] Prove how `source/track_centerline.generated.h` was produced and clear its exact inputs, or remove it.
- [ ] Verify the origin of `data/demo_track_points.csv` and `data/demo_track_edges.csv`, or remove them.
- [ ] Keep commercial ROMs, disc images, BIOS files, proprietary models/textures/audio, and uncleared third-party content out of Git.
- [ ] Re-run policy checks, host tests and native build on the exact proposed PR head.
- [ ] Record visible emulator/hardware rendering and controller validation separately from compilation.

Until the boxes above are resolved, continue the clean-room demo and build pipeline work without merging the Step 102 import. Budget remains €0; do not use a paid service to resolve the hold.
