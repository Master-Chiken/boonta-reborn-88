# Step 102 handoff and access boundaries

## Archive available in this ChatGPT conversation

The file `Star_Wars_Racer_GameCube_Step102.zip` is attached to the active ChatGPT conversation. I can inspect that upload during this session. GitHub Actions and the Gemini agent cannot see ChatGPT attachments automatically: they can see only files made available to the GitHub workflow or another explicitly connected storage service.

- Archive size: 1,337,413 bytes
- SHA-256: `85a1a1d82426399e48ac5a7e41bd7e9e45fda82e832284e573c358641df24b12`
- Entries: 359 files
- Uncompressed content: 2,645,491 bytes
- No `LICENSE`, `COPYING`, or `NOTICE` file was found in the ZIP.

A 359-row metadata triage CSV has been prepared separately for the owner. It contains paths, sizes, SHA-256 hashes, ZIP modes, categories, and conservative initial review decisions. It is not committed to this public repository at present. The manifest does not mark any source or asset as cleared for redistribution.

## Most important folders in the archive

| Location | Contents | Recommended use |
|---|---|---|
| `source/` (49 files) | Main game loop, pod physics, rivals, race flow, catalogs, track and geometry code | Core implementation to review first; every source file still needs provenance/license review |
| `tests/` (95 files) | Host-side C and Python regression tests plus shell checks | Very valuable for preserving behavior during a filtered import |
| `tools/` (29 files) | Build/preflight scripts, geometry and spline exporters, data inspection, asset extraction and converters | Review each tool; some explicitly process ROM- or PC-game-derived data |
| `docs/` (62 files) | Step-by-step history, current status, audits, technical handoffs and model previews | Use the most relevant handoff/audit documents; do not import the whole history automatically |
| `data/` (5 files) | Demo track CSV and PC catalog/import reference data | Separate procedural demo data from PC-derived or ROM-derived reference data |
| `assets/` (11 files) | Voice WAV files and model/material assets | Hold until each asset's author/source and redistribution permission are established |
| `jalon1/` (2 files) | An earlier viewer/build milestone | Historical reference, not the primary runtime target |
| Root | `Makefile`, `README.md`, `README_STEP102.md`, other step logs and `.gitignore` | Read README/build handoff first; preserve the host tests and real native build recipe selectively |

### Start with these files

1. `README.md` — overall prototype scope and declared data sources.
2. `README_STEP102.md` — native-build handoff and preflight notes.
3. `docs/STEP102_NATIVE_BUILD_HANDOFF.md` — detailed native-build status and limitations.
4. `Makefile` and `tools/native_build_status.py` — how the archive expects to build and diagnose its toolchain.
5. `source/main.c`, `source/racer_physics.c`, `source/rival_ai.c`, `source/track_catalog.c` — core areas to inspect once import permissions are addressed.
6. `tests/` — regression coverage to map to source modules before importing.

## Important inconsistency to resolve

The owner has declared the archive original, written or generated for this project. However, the archive's own `README.md` and `docs/STEP102_NATIVE_BUILD_HANDOFF.md` describe the live route catalog as using PC centerlines derived from the `SWE1R-Mods / SizeMattersNot / RontoSized` variant. The ZIP also contains PC/ROM audit reports and tools with explicit extraction-related names.

These findings do not necessarily mean every source file is third-party, but they do mean the whole ZIP cannot safely be published as one original, cleared source bundle. The safe path is to separate original code, original generated demo data, externally derived route/model/audio data, and research tools, then record the provenance and redistribution status for each relevant file.

## Current tools and what each can see

- **This ChatGPT conversation:** can read the attached ZIP and make a local metadata inventory while this upload is available.
- **GitHub connector:** can read public repository files, inspect pull requests and CI runs, and create commits on the working branch. It does not have permission from the current connection to change administrative repository settings, branch protection, secrets, or Actions variables.
- **GitHub Actions:** sees the repository checkout and workflow inputs/artifacts only. It cannot access arbitrary local folders or ChatGPT attachments.
- **Gemini workflow:** runs only inside GitHub Actions. It is not active until its API secret is configured by the owner. A repo write gate is present; write execution is intended to remain disabled until `main` is protected and the owner deliberately enables `GEMINI_WRITE_ENABLED`.
- **Other AI accounts:** I cannot sign into arbitrary AI services or hand one AI another service's private session. Claude has no direct connector available in this workspace and its API is billed per use, so the project is not connecting the Claude API under the €0 rule. A manual GitHub Copilot Free account can provide limited access to selected models, including a Claude Haiku model, but is not the same as an automated Claude integration. A second automated reviewer is prepared via OpenRouter Free; it requires the owner to add `OPENROUTER_API_KEY` as a repository secret. It sends only a public PR diff, uses the `openrouter/free` route, and is read-only. Free model providers and data practices can change.
- **Local computer:** I cannot browse all folders on the owner's Mac, inspect installed applications, or access local drives automatically. Only files uploaded here or deliberately shared through a connected service are available.
- **Cloud folders:** Google Drive is currently unavailable in the ChatGPT connector catalog for this workspace. A Dropbox connection option is available but is not confirmed connected. If a cloud connector is used, only the folders/files exposed by that account connection become available.

## Safety and cost gates

- Do not copy the archive wholesale to a public branch.
- Keep ROMs, disc images, BIOS files, extracted proprietary models/textures/audio and unclear derived data out of the public repository.
- Do not put API keys in issues, comments, source files, or chat.
- Do not attach billing, add a payment method, or upgrade a plan to make a workflow succeed. At the end of a free quota, stop that optional service.
- Keep PR #13 as draft and never merge to `main` without explicit human validation.
