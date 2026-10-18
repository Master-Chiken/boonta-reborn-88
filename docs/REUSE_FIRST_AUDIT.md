# Reuse-first audit: Boonta Reborn

**Snapshot date:** 2026-10-18  
**Status:** initial repository and community-tool inventory; no third-party code or commercial game assets imported by this audit.

## Binding rule

**Reuse-first is the project's primary engineering method, not an optional optimization.** Before creating a parser, converter, renderer subsystem, data format, test harness, or workflow, inspect existing Boonta code and relevant upstream projects. Prefer, in order:

1. Reuse an already working in-repository implementation.
2. Reuse a maintained and compatible upstream tool/library with acceptable licensing.
3. Add a thin adapter or narrowly scoped patch around an existing implementation.
4. Implement only the missing capability when evidence shows the first three options cannot meet the target requirements.

A tool is not reusable merely because it exists: verify its target platform, input format/version, output requirements, maintenance status, license, provenance and reproducible test coverage. If no suitable tool is found, record the search and reason before writing a replacement.

## What Boonta already has

| Existing path | What it already does | Reuse decision |
|---|---|---|
| `tools/mesh_format/` | Validates the project-owned `boonta-mesh-v1` JSON format and exports deterministic C headers. | Reuse for the synthetic clean-room demo and as a possible intermediate representation boundary. **Not** an original Racer asset parser. |
| `tools/texture_format/` | Validates/exports the project's existing texture source format. | Inspect and reuse for the current demo; do not treat it as an original game's texture-block decoder. |
| `tools/track_format/` | Validates and exports the project's original spline/track JSON format. | Reuse for the synthetic track harness. It does not decode original track files. |
| `tools/brres_probe/` | Reads a narrow BRRES/MDL0 header for Wii-format investigation. | Reuse only for BRRES-family inputs; this is not evidence that Racer's own PC/N64/GameCube data uses BRRES. |
| `gamecube-demo/tools/` | Existing Dolphin DTM generation/checking, artifact validation, controller-DOL patching and tests. | Extend these instead of creating parallel test scripts where their behavior matches the need. |
| `tools/inspect_wii64_rice_ini.py`, `tools/compare_wii64_rice_*.py`, `tools/verify_wii64_archive.py` | Read-only Wii64 Rice configuration comparison and archive fingerprint checks. | Keep for emulator/reference investigation; these tools do not recover Racer assets or port the original game runtime. |
| `docs/SOURCE_AND_ARTIFACT_REGISTER.md`, `docs/SOURCE_IMPORT_GATE.md`, `docs/STEP102_SOURCE_PROVENANCE.md` | Existing source/artifact inventory and import/provenance safeguards. | Update and reuse these registers; do not create duplicate source inventories. Unclear Step 102 material remains quarantined. |

## Upstream candidates

| Project | Potential time saved | Constraint before adoption | Current decision |
|---|---|---|---|
| [SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE) | PC executable analysis, symbols, Ghidra scripts, function research and asset-format knowledge. | AGPL-3.0; PC executable and Windows behavior are not a GameCube/Wii port. Review exact files and obligations before adapting code. | Highest-priority reverse-engineering reference; inspect documentation and data-format work first. |
| [swe1r-assets](https://github.com/akopetsch/swe1r-assets) | .NET block readers/writers for model, spline, sprite and texture blocks, with bit-perfect reserialization. | MIT, but target platform/version compatibility and conversion to GX-compatible output still need testing. | Highest-priority candidate for asset-format reuse; prototype against a lawfully supplied local sample before writing a new parser. |
| [SWE1R-Mods](https://github.com/louriccia/SWE1R-Mods) | Existing unpack/repack scripts and examples of community asset modifications. | PC `data/lev01` workflow; audit per-file provenance/license and verify format/version before using outputs on the target. | Reuse as a format reference or tool where practical; do not assume direct target compatibility. |
| [swe1r-tools](https://github.com/OpenSWE1R/swe1r-tools) | Existing scripts for extracting block resources, strings, save data and compressed model chunks. | Deprecated; GPL-2.0; audit exact tool and its dependencies before incorporating code. | Reference/last-resort tool candidate, not a default new dependency. |
| [OpenSWE1R/openswe1r](https://github.com/OpenSWE1R/openswe1r) | Historical open-source port architecture and knowledge about game behavior. | Deprecated and GPL-2.0; old PC-oriented implementation, not proven to build for GameCube/Wii. | Study architecture and algorithms; do not transplant wholesale. |
| [swep1r_decomp](https://github.com/DeonPoncini/swep1r_decomp) | Additional Ghidra-generated PC executable types/signatures and function notes. | PC-specific research; confirm provenance and license of each artifact. | Cross-reference only; compare against SW_RACER_RE before duplicating analysis. |

| [OpenSWE1R/blender-swe1r](https://github.com/OpenSWE1R/blender-swe1r) | Existing Blender importer/exporter for model, spline, texture, mesh, collision, and vertex-color data in the PC game's `data/lev01` block files. | GPL-3.0; Blender 4.0 add-on, work-in-progress, and no verified GameCube/Wii target support. Keep it as a linked format/structure reference unless the project owner explicitly reviews the license and integration implications. | Add to the research comparison alongside `swe1r-assets`; do not port the add-on or assume its exports are console-ready. |

## First practical target

Do **not** start by building another generic asset framework. First:

1. Choose the exact legally available source release and target platform path; record hashes and version evidence locally without committing game binaries.
2. Inspect `swe1r-assets` and `SW_RACER_RE` for the first useful block format and compare with existing Boonta parsers/tools.
3. Use one local, lawfully obtained sample to test whether the existing parser reads it correctly and whether its output exposes the fields needed by the GameCube/Wii renderer.
4. If it works, wrap/reuse it and write a deterministic conversion adapter plus a small regression fixture that contains no proprietary asset data.
5. If it fails, document the exact mismatch (platform/version, format, endianness, compression or missing feature) before extending the upstream tool or writing a small new component.

## Step 102 archive contents checked — 2026-10-18

The supplied `Star_Wars_Racer_GameCube_Step102.zip` was inspected by reading its ZIP directory only (no commercial game data was extracted). Its SHA-256 is `85a1a1d82426399e48ac5a7e41bd7e9e45fda82e832284e573c358641df24b12`; the archive contains 375 entries and 2,645,491 uncompressed bytes. It contains **no** `.bin`, `.iso`, `.gcm`, `.z64`, or `.dol` payloads. It does contain existing diagnostic tools such as `tools/inspect_blocks.py`, `tools/audit_pc_modelblock.py`, and `tools/scan_pc_assets.py`, plus PC-oriented model/spline audit reports and catalogues.

Consequences for the next step:

- Reuse `inspect_blocks.py` and `audit_pc_modelblock.py` first for **PC-format metadata validation** rather than creating a parallel block-table parser.
- The tools explicitly expect user-supplied `out_modelblock.bin`, `out_splineblock.bin`, or `out_textureblock.bin`; those original block files are not present inside this Step 102 source archive.
- Existing PC-derived spline/catalogue reports are useful research inputs but do not establish GameCube/Wii format compatibility or clear the underlying track data for redistribution.
- The first real-input test is therefore **blocked until a lawful local source block is selected**. A PC block can validate the existing parser against the PC format only; it cannot, by itself, prove a GameCube/Wii data path. Record platform/version and hash locally, and publish only non-sensitive structural metadata and tests—not the block or extracted assets.

## Definition of an accepted reuse

Every adopted tool or borrowed component needs a record of upstream URL/revision, license, relevant files, local changes, target compatibility evidence, test command/results and remaining limitations. Keep upstream code separable where possible. Never import commercial executables, disc images, ROMs or extracted proprietary assets into this public repository without clear redistribution authorization.

## Important boundary

The current mesh, texture and track formats demonstrate a working **synthetic test harness**. They are not proof that original Racer data has been extracted or converted. Progress toward the main objective requires a reproducible path from a documented original source format to a target-compatible asset and ultimately a manually playable race.

## Local Step 102 validation — 2026-10-18

The owner-supplied archive `Star_Wars_Racer_GameCube_Step102.zip` was tested locally in a temporary workspace. Its SHA-256 matched the existing source register: `85a1a1d82426399e48ac5a7e41bd7e9e45fda82e832284e573c358641df24b12` (359 files; 2,645,491 uncompressed bytes).

- Restored the executable permission bits recorded in the ZIP metadata in the temporary extracted copy; this was necessary because the extraction method used for this audit did not preserve them.
- Result: **91/91 Python unit tests passed**.
- Portable C host regression checks passed for physics, SWC1 collision reading, race flow, rival AI, track/vehicle/item catalogues, race feedback, pod mesh/model, native-source syntax using mock libogc declarations, scene assets and OBJ export.
- The wrapper then stopped with exit code 2 because `DEVKITPPC` is not configured in this environment. It explicitly did **not** start a real GameCube cross-build. Dolphin was also unavailable here, so this is not emulator or hardware acceptance.
- This is evidence that the private archive's existing host-side pipeline is testable—not evidence that it is licensed for public redistribution, that its PC-derived spline data is original retail data, or that the prototype is a native playable port.

**Reuse decision:** retain the Step 102 archive as a quarantined local research baseline for now. Do not import its source or assets into this public repository until the existing path-by-path provenance review clears each file. The next technical gate is to run the existing parser against one exact, locally available source block, record the source release/hash and parser output metadata, then compare its format coverage with `swe1r-assets` before writing any new decoder. A successful host suite does not remove the need for that real-input test.

