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
