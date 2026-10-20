# Source and artifact register

**Snapshot date:** 2026-10-14  
**Purpose:** connect files already supplied for this project to the public repository without accidentally publishing game binaries, unclear third-party code, or proprietary data.

The files in the first table were supplied in the ChatGPT conversation. They are **not** tracked files in this GitHub repository and are not automatically available to GitHub Actions, Gemini, or OpenRouter. File sizes below are attachment metadata, not a content or licensing audit.

## Previously supplied files

| File as supplied | Size | Project role / disposition |
|---|---:|---|
| Star_Wars_Racer_GameCube_Step102.zip | 1,337,413 bytes | Candidate native GameCube/Wii source prototype. Priority input for a path-by-path review. A prior note reports 359 archive entries and a successful temporary host-test run (including 91 Python unit tests), but that is not a native build and is not current main-branch CI evidence. No obvious license notice was found in the archive during the earlier review; do not publish its contents until provenance and redistribution rights are checked. |
| Game SW Racer 1999.zip | 475,680,870 bytes | Commercial game archive / reference input. Keep private; do not commit, attach to a public issue, include in a build artifact, or send to an external AI service. |
| SW Racer 1999- (US).z64 | 33,554,432 bytes | Nintendo 64 game ROM. Keep private and local to lawful user-controlled testing. Never commit it or add it to CI artifacts. |
| SW_RACER_RE-master.zip | 107,103,834 bytes | Snapshot of a third-party PC-version research/reimplementation project. Prefer reviewing the upstream repository and its current license instead of copying this ZIP into the project. Treat any reuse as unapproved until license and file provenance are checked. |
| swe1r-assets-main.zip | 12,616,153 bytes | Snapshot associated with SWE1R asset tooling/research. Verify its exact contents, upstream revision, dependencies, and license before adapting it. Asset parsers are not the same thing as permission to redistribute extracted game assets. |
| Star Wars - Episode I - Racer (USA).7z | 328,559,989 bytes | Compressed game archive whose exact internal contents should be verified before it is used. Treat it as private commercial game material unless proven otherwise; keep it out of this public repository and automated review prompts. |

## Existing owner-side Step 102 audit files

Two generated metadata files already exist in the owner's ChatGPT Library; neither is tracked by GitHub:

- **boonta_step102_file_manifest.csv** — 101,245 bytes; 359 archive-file rows plus a header. It records paths, sizes, per-file hashes, ZIP modes, categories, and cautious initial review decisions.
- **boonta_step102_inventory_summary.txt** — 891 bytes; archive totals and category/extension/action counts.

The manifest matches the audited ZIP identified by SHA-256 85a1a1d82426399e48ac5a7e41bd7e9e45fda82e832284e573c358641df24b12. Its current triage actions are: 25 HOLD_PROVENANCE, 4 REVIEW_DATA_PROVENANCE, 152 REVIEW_DOCUMENTATION, 7 REVIEW_INDIVIDUALLY, and 171 REVIEW_SOURCE_LICENSE. **No row is marked cleared for redistribution.** This is a metadata triage, not legal advice or license clearance.

Keep the CSV private for the file-by-file review until a deliberate decision is made about publishing any of its path/hash metadata. GitHub Actions and GitHub-hosted agents cannot read the ChatGPT Library file automatically. Do not treat the mere existence of the manifest as permission to import the archive.

## Upstream research links

These links connect the uploaded snapshots and earlier research to their original project context. They are research references, not an approval to copy code or data. SW_RACER_RE is now the top-priority external reference, but is still Windows-PC research and is not automatically reusable source or asset content.

| Upstream project | Connection to this project | Rule before reuse |
|---|---|---|
| [SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE) | **Tier 1 PC behavior/reverse-engineering reference** for race state, splines, model/object/rendering systems, resource loading, controls, camera, and symbol/function research. Reviewed master at commit `a9863edd4caaa573f89ff634fa7d1cd6d41738ab` (2026-10-05). | GitHub reports AGPL-3.0. Use links and summarized observations by default; do not import or adapt code without a deliberate license review. Treat assets and mod dependencies separately. Not a GameCube/Wii port. See [study plan](SW_RACER_RE_STUDY_PLAN.md) and [behavior matrix](SW_RACER_RE_BEHAVIOR_MATRIX.md). |
| [OpenSWE1R](https://github.com/OpenSWE1R/openswe1r) | PC-side open reimplementation useful for architecture and subsystem research. | Review its GPL-2.0 obligations and dependencies before copying or creating a derivative. |
| [swe1r-assets](https://github.com/akopetsch/swe1r-assets) | PC asset-block parsing, editing, and reserialization tools. | Confirm the data format matches the target version and review code/data licenses separately. |
| [SWE1R-Mods](https://github.com/louriccia/SWE1R-Mods) | PC-version mod/data research. | Do not assume extracted content is redistributable. |
| [swe1r-tools](https://github.com/OpenSWE1R/swe1r-tools) | Related asset-format and PC research tooling. | Review each tool's license/dependencies and validate against the actual target data format. |
| [Wii64 / Cube64](https://github.com/emukidid/Wii64) | Possible separate test of N64-version compatibility in a Wii homebrew environment. | Emulation is not a native port or HD enhancement; any test ROM must remain user-provided and private. |

## Reuse-first index — existing public tools checked 2026-10-20

This is a navigation aid to avoid rebuilding capabilities that already exist. It is not a license clearance or a recommendation to import whole repositories.

| Need | Existing candidate | What it already provides | Reuse decision for Boonta |
|---|---|---|---|
| Read/write PC game asset blocks | [swe1r-assets](https://github.com/akopetsch/swe1r-assets), reviewed at commit `922ef535f6598a1330ff93d6b07258956f990b34`) | .NET object models for model, spline, sprite and texture blocks; documents bit-perfect no-op reserialization | **First format cross-check.** Read its model and tests before designing a new parser. MIT license applies to its code, not to game assets or proof of target-console format parity. |
| Inspect an existing Unity asset workflow | [swe1r-assets-unity](https://github.com/akopetsch/swe1r-assets-unity) | Work-in-progress sample project built on swe1r-assets for importing, editing and re-exporting assets with bit-perfect no-op round-trips | **Useful existing experiment, not a finished editor.** Reuse its results and tests as format evidence; do not rebuild a Unity importer before checking this sample. Confirm its current license and dependencies before adapting. |
| Import/edit/export game assets and route splines in 3D | [blender-swe1r](https://github.com/OpenSWE1R/blender-swe1r), pinned parser/README references are linked in RE-001 | Blender import/export workflow for models and spline data; describes route roles, cyclic/open routes and alternate paths | **Reference for route semantics and authoring limitations.** Treat its constraints as tool/exporter constraints unless independently proven to be engine limits. Do not import the add-on code without a separate license review. |
| Extract PC spline, sprite and texture blocks; parse save/string formats | [swe1r-tools](https://github.com/OpenSWE1R/swe1r-tools) | Existing Python/C utilities including spline-to-OBJ, sprite/texture extraction, N64 model-block decompression, save-data parsing and string extraction | **Prefer existing tool as a read-only experiment** before implementing another extractor. GPL-2.0-or-later terms and exact target format must be checked before adapting code. |
| Inspect community asset modifications and repacking scripts | [SWE1R-Mods](https://github.com/louriccia/SWE1R-Mods) | Unpack/repack scripts and examples of track/texture modifications; README identifies dependencies on existing tools | **Use as a discovery index only.** Mods and extracted content have separate provenance; do not copy assets or scripts until each file's terms and origin are clear. |
| Understand legacy PC patching and version compatibility | [swe1r-patcher](https://github.com/JayFoxRox/swe1r-patcher) and [PCGamingWiki](https://www.pcgamingwiki.com/wiki/SWE1R) | Existing patch/loader and user-facing compatibility notes; the patcher documents a no-commercial-use / no-redistribution restriction | **Do not reuse patcher code or its output.** Use only as a behavior/compatibility lead; independently validate frame-rate/version claims against a pinned PC build. |
| Inspect an existing PC mod-loader design | [PitDroidModManager](https://github.com/OpenSWE1R/PitDroidModManager) | Public mod-loader project listed by OpenSWE1R; repository lists Apache-2.0 | **Reuse architecture ideas first.** Only adapt source after checking the exact revision, dependencies, and whether a PC DLL loader has any relevance to our native GameCube/Wii target. |
| Reuse an older open PC port for subsystem clues | [OpenSWE1R](https://github.com/OpenSWE1R/openswe1r) | GPL-2.0 PC port combining a subset of Windows API emulation, x86 CPU emulation, and open replacements for some original functions; still needs original game assets and code in places | **Study its architecture, do not treat it as a finished portable game engine.** The project marks itself deprecated; PC-specific code is not a native console implementation. |
| Track N64 hardware/version-specific behavior | [N64 documentation/community issue leads](https://github.com/TASEmulators/BizHawk/issues/2603) and [N64 Expansion Pak notes](https://github.com/supavgx/N64-Documentation/blob/main/WIP%20custom%20docs/ExpansionPakGames.md) | Public reports mention sync/capture behavior and an Expansion Pak high-resolution mode for N64 Racer | **Test hypotheses only.** Record emulator, ROM revision, hardware mode, and reproducible steps; never infer GameCube/Wii behavior directly from N64 observations.
| Recover missing PC function bodies/types | [swep1r_decomp](https://github.com/DeonPoncini/swep1r_decomp/tree/d988c6408a91aaf8a0e65dbdbe32b0dbb4b970ef) | Frozen Steam-PC Ghidra decompilation with addresses, assembly and C-like function bodies | **Read-only evidence source.** No root license was found in the reviewed snapshot; do not copy/adapt code. Continue pinning the exact function URL and address in the existing RE-001 dossier. |
| Understand the larger PC engine and hooks | [SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE/tree/a9863edd4caaa573f89ff634fa7d1cd6d41738ab) | Function/symbol map, PC subsystem research, tests, and mod-hook references for race state, physics, spline, objects, camera, assets and rendering | **Primary behavioral research index, not a port.** AGPL-3.0 review is required before any code reuse; many important route-advance functions remain stubs in the reviewed source. |
| Community-only observations and undocumented edge cases | [Star Wars Episode I: Racer community Discord](https://discord.com/servers/441839750555369474), [Racer Wiki](https://starwars-racer.fandom.com/wiki/Star_Wars_Episode_1:_Racer_Wiki), [PCGamingWiki](https://www.pcgamingwiki.com/wiki/SWE1R) | Modding discussions, version quirks, player observations and technical compatibility notes | **Lead generation only.** Record the specific claim, version/platform and independent corroboration before treating it as fact. Do not rely on community anecdotes alone for console parity. |

### Retrieval order before creating anything new

1. Search the existing Boonta docs and source register for the topic first; the project already has a study plan, behavior matrix, technical map, platform matrix and the RE-001 route dossier.
2. Check the pinned public sources above for an existing parser, test, symbol, function body or documented constraint.
3. If a relevant supplied/private archive is available, verify its identity and path-level provenance locally; do not assume the historical Step 102 bundle is a canonical source tree.
4. Record the exact source URL, commit/release, platform, what was observed, and confidence in the existing dossier/register.
5. Only then decide whether a small clean-room implementation or test is genuinely missing. Do not copy game assets, ROM/disc data, unclear source, or third-party code by default.

**Coverage boundary:** this pass verifies the existence and advertised purpose of these public tools; it does not run them against a target-platform binary, clear third-party licenses, or establish that PC/N64/Dreamcast formats match GameCube/Wii. The searches in this pass did not surface a dedicated public N64 or Dreamcast decompilation project; treat that as a current search result, not proof that no such work exists. The public OpenSWE1R organization also labels its older PC port, early decompilation and tooling as deprecated, so they remain secondary research sources rather than the default implementation baseline. Emulator compatibility lists and player/community reports are observation leads, not substitutes for target-platform source evidence.

## Source-of-truth and transfer rules

- The intended primary target is native GameCube/Wii homebrew. The Step 102 source archive is the candidate source baseline described in the planning documents.
- The gamecube/ tree proposed in [PR #13](https://github.com/Master-Chiken/boonta-reborn-88/pull/13) is a separate clean-room procedural demo. It does not contain the Step 102 source and must not be presented as an imported or completed version of that work.
- The repository's dreamcast/ directory is a separate KallistiOS experiment and must not be counted as GameCube/Wii progress.
- Only transfer a source file into GitHub after recording its path, origin, license/provenance, whether it contains copied/generated data, and the reason it is safe to distribute.
- The existing archive's route centerlines were reported to derive from a modded PC spline dataset. Keep those route data files out until their origin and redistribution rights are explicitly cleared.
- Do not upload the commercial PC archive, console ROMs/disc images, BIOS files, extracted models/textures/audio, or uncertain payloads to the public repo. Do not place them in GitHub Actions artifacts or send them to AI reviewers.
- Do not make a public manifest expose hashes or paths for private commercial payloads unless doing so is necessary and legally reviewed. The public register intentionally records only attachment names/sizes and disposition.
- If the source archive contains code with unclear provenance or incompatible terms, exclude those files and document the limitation rather than assuming the archive as a whole is open source.

## Audit record still needed for Step 102

PR #13's handoff notes that a 359-row metadata triage CSV was prepared separately for owner review. It is not committed in this public repository and must not be treated as a clearance decision. Reconcile any private copy against the archive checksum above before relying on it.

Create or complete a dedicated path-by-path manifest before importing:
- archive path and file type;
- origin/source and license evidence;
- whether it is original code, generated data, third-party code, a placeholder, or extracted commercial material;
- whether the file may be redistributed in a public repository;
- decision: include, rewrite clean-room, keep private, or omit;
- reviewer and date.

Acceptance condition: every file being imported has a recorded disposition, and the approved list can be reproduced from the archive without relying on memory or on an undocumented ChatGPT session.

## Reuse audit against current Boonta tooling — 2026-10-20

This is a bounded comparison of the pinned `swe1r-assets` revision (`922ef535f6598a1330ff93d6b07258956f990b34`) against the current `main` tree (`fa8cee047ae8e74c30c87cd94977c434bb1c7398`). It records reuse candidates; it does not import code or assets.

| Need | Already present in Boonta | Existing external work | Decision |
|---|---|---|---|
| Original track authoring / validation | `tools/track_format/`, `tests/test_track_format.py`, generated `gamecube-demo/source/generated_track.h` | `swe1r-assets` models PC game's binary spline blocks; `blender-swe1r` edits PC game splines | Keep the clean-room JSON track pipeline for original tracks. Evaluate external tools only as research/conversion aids; do not mistake a PC binary parser for a GameCube/Wii runtime parser. |
| Model and mesh data | `tools/mesh_format/`, `gamecube-demo/tests/test_mesh_data.c` | `swe1r-assets` has model types, mesh/vertex/material code, importers/exporters and format tests | Reuse as a PC-format reference or offline converter only after format and license checks; not drop-in GameCube/Wii asset support. |
| Texture conversion | `tools/texture_format/`, `gamecube-demo/tools/test_texture_format.py` | External command-line tools export model textures and sprites; the library includes texture/sprite structures | Prefer existing local validator and tests for the current demo. Compare conversion outputs before adopting any external dependency. |
| Binary round-trip assurance | Current tests validate Boonta's own neutral formats and native demo data | External repository includes dedicated model, spline and sprite re-serialization tests | Reuse the *test strategy* as a template. External test fixtures reference that project's original asset provider and are not proof that Boonta or console files round-trip. |
| Runtime route progression | Current prototype samples its own closed-loop track and uses distance-based lap counting | External PC reverse engineering documents a different original-game spline/cursor implementation | Keep RE-001 active. Do not replace the prototype route model until a console-relevant behavior comparison is evidenced. |

### Immediate conclusions

1. **There is already a substantial clean-room toolchain in Boonta.** Before adding a dependency, compare the exact input/output contract of the existing validator, exporter and tests with the external tool's capabilities.
2. **The external MIT library is a strong offline research candidate, not a ready-made console engine.** Its command-line interface lists models, splines, sprites and textures, and exports sprites/model textures. Its own spline re-serialization tests compare parsed PC-format items; they do not demonstrate GameCube/Wii compatibility.
3. **Do not import commercial game files or external test assets into the public repository.** Run format experiments only with legally obtained local files where permitted, or with already-public synthetic fixtures. Record file provenance separately from code license.
4. **No code has been copied and no dependency has been added by this audit.** The next validation should be a read-only capability/format comparison, then a minimal isolated experiment only if a concrete gap remains.

References:
- Boonta track format and validation: `tools/track_format/README.md`, `tests/test_track_format.py`.
- Boonta mesh and texture tooling: `tools/mesh_format/`, `tools/texture_format/`, `gamecube-demo/tests/`.
- External CLI documentation: https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks.CommandLine/README.md
- External spline round-trip tests: https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/src/SWE1R.Assets.Blocks.Original.Tests/Reserialization/SplineBlockItemsReserializationTest.cs
- External license: https://github.com/akopetsch/swe1r-assets/blob/922ef535f6598a1330ff93d6b07258956f990b34/LICENSE
