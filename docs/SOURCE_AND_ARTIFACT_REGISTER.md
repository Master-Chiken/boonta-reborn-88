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

## Upstream research links

These links connect the uploaded snapshots and earlier research to their original project context. They are research references, not an approval to copy code or data.

| Upstream project | Connection to this project | Rule before reuse |
|---|---|---|
| [SW_RACER_RE](https://github.com/tim-tim707/SW_RACER_RE) | Research/reimplementation focused on the Windows PC edition; may help understand engine behavior and data structures. | Confirm the current license, specific file origins, and platform relevance. It is not a GameCube/Wii port. |
| [OpenSWE1R](https://github.com/OpenSWE1R/openswe1r) | PC-side open reimplementation useful for architecture and subsystem research. | Review its GPL-2.0 obligations and dependencies before copying or creating a derivative. |
| [swe1r-assets](https://github.com/akopetsch/swe1r-assets) | PC asset-block parsing, editing, and reserialization tools. | Confirm the data format matches the target version and review code/data licenses separately. |
| [SWE1R-Mods](https://github.com/louriccia/SWE1R-Mods) | PC-version mod/data research. | Do not assume extracted content is redistributable. |
| [swe1r-tools](https://github.com/OpenSWE1R/swe1r-tools) | Related asset-format and PC research tooling. | Review each tool's license/dependencies and validate against the actual target data format. |
| [Wii64 / Cube64](https://github.com/emukidid/Wii64) | Possible separate test of N64-version compatibility in a Wii homebrew environment. | Emulation is not a native port or HD enhancement; any test ROM must remain user-provided and private. |

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