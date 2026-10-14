# Step 102 source archive audit and import gate

**Status: reviewed at archive level; not cleared for wholesale publication.**

This note records a lightweight inventory of `Star_Wars_Racer_GameCube_Step102.zip` before importing it into this public repository. It is deliberately conservative: passing host tests does not establish ownership, licensing, or redistribution rights.

## Inventory

- Archive size: 1,337,413 bytes.
- Files: 359 files (excluding directory entries).
- Total uncompressed size: 2,645,491 bytes.
- Main contents: C source and headers, Python/shell tools, host tests, documentation, generated reference data, and a small set of audio/image/model assets.
- The archive contains 154 Markdown files, 57 C files, 33 headers, 42 Python files, and 44 shell scripts.
- No root or nested file named `LICENSE`, `COPYING`, or `NOTICE` was found in the archive inventory.

These counts describe the supplied ZIP, not the current GitHub repository.

## Findings that block a bulk import

1. **No explicit project license was found.** Do not assume that code in the archive is automatically cleared for public redistribution. Establish authorship and choose a suitable license before treating the code as reusable by third parties.
2. **Imported track data has a declared third-party origin.** The archive README identifies the `SWE1R-Mods / SizeMattersNot / RontoSized` PC mod variant as the source of the selected course centerlines. The generated header `source/track_centerlines_pc.generated.h` and manifest `data/reference/pc_track_import_manifest.json` reinforce this. Do not publish those generated centerlines or dependent generated data until their source, terms, and redistribution rights have been checked.
3. **The archive includes asset files.** Audio, image, OBJ/MTL, and other data files require individual provenance checks. Do not assume that an asset is original merely because it is stored in the prototype archive.
4. **Commercial game material must stay out of this repository.** Never commit ROMs, disc images, extracted proprietary models/textures/audio, BIOS files, or other commercial payloads.
5. **The README describes a prototype, not a verified port.** Its reported 91 Python tests and host shell checks are not evidence of a native GameCube build or runtime success. A devkitPPC/libogc build and Dolphin/console boot test remain separate acceptance gates.

## Recommended import plan

### Gate A — source and provenance

- [ ] Identify the author/source and applicable license for each source tree and any copied or adapted code.
- [ ] Review third-party reverse-engineering references and document what is independently written versus adapted.
- [ ] Exclude `source/track_centerlines_pc.generated.h`, `data/reference/pc_track_import_manifest.json`, and any other files derived from the modded spline dataset unless redistribution is explicitly cleared.
- [ ] Review every file under `assets/` and `data/`; exclude unclear audio, images, models, generated data, and binary payloads.
- [ ] Add a project license only after the project owner confirms the intended license and authority to apply it.

### Gate B — clean source import

- [ ] Import only files that pass Gate A, preserving executable bits for shell scripts.
- [ ] Keep ROMs, disc images, and extracted commercial game data outside Git.
- [ ] Record the exact source archive checksum and the import commit for reproducibility.
- [ ] Run the host regression suite in GitHub Actions from the imported tree.

### Gate C — native target validation

- [ ] Build `swe1r_gc_port.dol` using devkitPPC/libogc.
- [ ] Upload the DOL and build log as CI artifacts, not as a claim of runtime correctness.
- [ ] Test in Dolphin and record whether it boots, renders, accepts input, and remains stable.
- [ ] Track emulator/hardware execution separately from compile success.

## Decision

**Do not bulk-copy the archive into the public repository yet.** The safest next action is a provenance-cleared source-only import, starting with the build/test infrastructure and original code whose ownership can be established. Keep the generated track-centerline data and unclear assets excluded until reviewed.

This is a technical repository hygiene review, not legal advice or a definitive copyright determination.


## Reproducible inventory snapshot

- Archive SHA-256: `85a1a1d82426399e48ac5a7e41bd7e9e45fda82e832284e573c358641df24b12`
- Total: 359 file entries; 2,645,491 uncompressed bytes.
- Top-level counts (including everything nested under each directory): root 105; `tests/` 95; `docs/` 62; `source/` 49; `tools/` 29; `assets/` 11; `data/` 5; `jalon1/` 2; `include/` 1.
- These counts and the checksum describe the exact ZIP available during this audit. They are a reproducible snapshot, not a grant of permission to redistribute the contents.

### Explicit hold/review paths

| Path inside archive | Why it is held |
|---|---|
| `source/track_centerlines_pc.generated.h` | Generated centerlines declared to derive from a modded PC spline dataset; rights/provenance unresolved |
| `data/reference/pc_track_import_manifest.json` | Manifest of the same external PC-track import |
| `data/reference/pc_model_catalog.csv` | PC model catalog/reference data; establish origin and whether it encodes extracted commercial data |
| `data/reference/pc_spline_catalog.csv` | PC spline catalog; establish origin and redistribution rights |
| `docs/pc_mod_modelblock_audit_step87.json` | Audit data relating to a modded PC model block |
| `docs/pc_spline_audit_step87.json` | Audit data relating to PC spline extraction/import |
| `docs/ROM_TRACK_TRANSFORM_AUDIT_STEP81.json` | ROM-derived track-transform audit metadata; review before publishing |
| `docs/ROM_TRACK_BLOCK_AUDIT_STEP80.json` | ROM-derived track-block audit metadata; review before publishing |
| `docs/ROM_TRACK_COLLISION_AUDIT_STEP82.json` | ROM-derived collision audit metadata; review before publishing |
| `docs/N64_ROM_TRACK_INVENTORY.md` | Documentation about N64 ROM extraction; review content before public import |
| `assets/voice_en/*.wav` (8 audio files) | Voice/audio assets; origin and redistribution permission not established |
| `assets/geometry/prototype_pod.obj`, `assets/geometry/prototype_pod.mtl` | Model/material source may be prototype-authored, but authorship/origin must be confirmed |
| `docs/pod_model_preview.png`, `docs/track_mesh_preview.png` | Preview images may depict data derived from assets/geometry held above |
| `source/track_mesh.generated.h` | Generated mesh data; source route and regeneration provenance need review |
| `source/track_centerline.imported.h` | Imported centerline header; establish exact source before publishing |
| `source/track_centerline.generated.h`, `source/track_boundaries.generated.h` | Generated route/boundary data; verify generator and inputs before importing |
| `tools/extract_rom_assets.py`, `tools/export_n64_track.py`, `tools/scan_pc_assets.py` | Tools are code, not game payloads, but review their scope and documentation before making them part of the public baseline |

The root contains many step-by-step Markdown logs. Those may be useful for project history, but do not need to be imported wholesale into the runtime target. A smaller set of source/build/test documentation should be selected after the ownership/license question is settled.

### Import decision at this point

- **Candidates, not yet licensed for public redistribution:** original-looking C modules, headers, host test harnesses, build scripts, and project documentation.
- **Held pending specific review:** the paths listed above and any other files whose contents or origin cannot be established.
- **Do not add:** commercial ROMs, disc images, BIOS data, extracted proprietary models/textures/audio, or data that is known to derive from an external mod without redistribution clearance.

This section records the path-level hold list and archive checksum. A separate 359-row metadata triage manifest has now been generated for owner review. It includes each archive-relative path, file size, SHA-256, CRC32, ZIP mode, category, initial action, and reason. It is delivered separately to the owner rather than committed to the public repository before the path list has been reviewed. No row is marked approved for redistribution. The CSV is an inventory aid, not a legal determination.
