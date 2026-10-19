# Step 102 file-by-file clearance register

**Purpose:** make the source-only import review repeatable. This register records technical triage only; it is not a legal opinion or permission to redistribute.

**Default rule:** every path is **HOLD / UNVERIFIED** until its origin, authorship, license/permission, and content have been checked. A passing build or test does not change this status. Do not add ROMs, disc images, BIOS files, or extracted commercial game assets.

## Review states

- `HOLD` — not approved for public import; provenance or rights unresolved.
- `REVIEWED-NOT-CLEARED` — inspected, but permission/license is not established.
- `CLEARED` — evidence recorded for authorship and redistribution permission, with compatible project licensing confirmed.
- `EXCLUDE` — intentionally not imported into the public repository.

Do not mark a file `CLEARED` based only on its filename, its presence in the archive, generated output, or a successful test.

## Review record required for each file or tightly defined file group

| Field | Required evidence |
|---|---|
| Archive-relative path(s) | Exact paths; avoid vague labels such as “source files” |
| SHA-256 | Hash of the reviewed file(s), so later changes trigger re-review |
| Origin | Who wrote it, or exact upstream URL/commit/archive |
| Authorship | Original, adapted, generated, third-party, or unknown |
| License/permission | Exact license/version or written permission; link or record location |
| Dependencies | Any copied code, generated inputs, third-party assets or datasets |
| Public redistribution decision | HOLD / REVIEWED-NOT-CLEARED / CLEARED / EXCLUDE |
| Reviewer/date | Person who checked it and date |
| Notes | Scope limitations and any required attribution/notice |

## Initial path-group triage

Every row below starts as **HOLD**. These are review queues, not approvals.

| Path/group | Initial status | Reason / next check |
|---|---|---|
| `source/*.c`, `include/*.h` | HOLD | Establish author, origin, adaptations and license per file/group before redistribution |
| `tests/**` | HOLD | Check authorship and whether tests embed extracted game data or third-party material |
| `tools/**` | HOLD | Review code and documentation; especially ROM extraction, asset scanning, PC/N64 export utilities |
| `docs/**` | HOLD | Select useful project docs; inspect for copied text, ROM-derived details, proprietary data and third-party claims |
| `source/track_centerlines_pc.generated.h` | EXCLUDE pending permission | Declared as derived from a third-party PC mod spline dataset |
| `data/reference/pc_track_import_manifest.json` | EXCLUDE pending permission | Manifest for the PC-mod-derived track import |
| `data/reference/pc_model_catalog.csv` | HOLD | Determine whether it encodes extracted commercial model data |
| `data/reference/pc_spline_catalog.csv` | EXCLUDE pending permission | PC spline reference dataset; origin and redistribution terms unresolved |
| `source/track_mesh.generated.h` | HOLD | Trace exact generator and input provenance; do not infer clearance from generated status |
| `source/track_centerline.imported.h` | HOLD | Establish exact source and permissions |
| `source/track_centerline.generated.h`, `source/track_boundaries.generated.h` | HOLD | Trace generator and all input data |
| `assets/voice_en/*.wav` | EXCLUDE pending permission | Audio/voice rights and origin not established |
| `assets/geometry/prototype_pod.obj`, `assets/geometry/prototype_pod.mtl` | HOLD | Confirm creator and that geometry/materials are independently authored |
| `docs/pod_model_preview.png`, `docs/track_mesh_preview.png` | HOLD | Inspect what source assets/data the previews depict |
| `docs/ROM_TRACK_*_AUDIT_STEP*.json`, `docs/N64_ROM_TRACK_INVENTORY.md` | HOLD | Review whether the published contents disclose or reproduce ROM-derived data |
| ROMs, disc images, BIOS, extracted commercial models/textures/audio | EXCLUDE | Do not publish in this repository |

## Minimum evidence before importing a source group

1. Inspect the exact files and their history/origin.
2. Record authorship and license/permission evidence in this register or a linked review record.
3. Check compatibility with the repository's root license; do not silently apply MIT to files whose rights are unknown.
4. Search for embedded proprietary data, generated commercial-game content, third-party code, and asset payloads.
5. Add only the reviewed, cleared paths to an explicit allowlist in the import workflow.
6. Run policy tests, host regression tests, native build and runtime checks after the import.
7. Re-review when file hashes, upstream commits, generated inputs or licensing terms change.

## Current decision

The archive-level audit found no root or nested `LICENSE`, `COPYING`, or `NOTICE` file in the supplied ZIP. The 123-file source-only candidate in PR #17 is therefore still a **technical candidate, not a cleared redistribution**. Keep that PR as draft until source authorship/license review and interactive runtime validation are complete.

Related documents:
- [Archive audit and hold list](STEP102_IMPORT_AUDIT.md)
- [Next milestone and acceptance sequence](NEXT_MILESTONE.md)
- [Platform decision](PLATFORM_DECISION.md)
