# SW_RACER_RE — PC research source snapshot

This directory is a **source-only research snapshot**, imported from [`Master-Chiken/SW_RACER_RE`](https://github.com/Master-Chiken/SW_RACER_RE) at commit:

`66120be334a3fd38c10a259f3528cffbfed8ddc5`

The upstream project is a reverse-engineering and modding project for the **Windows PC** release of Star Wars: Episode I – Racer. Its source is useful for studying PC game systems, function hooks, data structures, game state, custom track tooling and file formats. It is not a GameCube/Wii implementation and must not be treated as a source of console addresses, layouts or behavior without independent verification.

## License boundary

- The code in this directory is retained under the upstream project's **GNU Affero General Public License v3.0 (AGPL-3.0)**. See [`LICENSE`](LICENSE).
- The root Boonta Reborn project remains MIT-licensed. This PC research subtree is an isolated, separately licensed reference; its code is not linked into the native GameCube/Wii build.
- Keep the AGPL notice and source available when conveying or distributing modified versions of this subtree as required by the license.
- Do not copy AGPL code into the MIT GameCube/Wii core or combine it with other modules without a separate license-compatibility review.

## What was imported

A curated set of **337 text/source files** from the pinned fork revision: first-party C/C++ source and headers, project build/configuration files, analysis scripts, tests and research documentation. An additional eight source/test files from fork PR [#18](https://github.com/Master-Chiken/SW_RACER_RE/pull/18) at head `95a8026bafb09374c7ab6efa91d8dfdd45a9cec6` are retained below: two production source updates, two policy headers and four synthetic tests. The upstream README is retained as [`UPSTREAM_README.md`](UPSTREAM_README.md), and its original root `.gitignore` is preserved as [`UPSTREAM.gitignore`](UPSTREAM.gitignore). The active `.gitignore` in this snapshot is a stricter local data-exclusion guard. The source paths are preserved below this folder.

This is a research snapshot, not a claim that the PC mod builds from this directory. Some upstream dependencies and data inputs are deliberately absent. It also retains first-party GLTF validation changes from upstream commit `6be9bc0` (see `UPSTREAM_SYNC_STATUS.md`). The associated third-party fastgltf parser patch was not imported pending separate license/source review. The PR #18 tests have zero check runs on their exact source head and are **unverified** here; their presence preserves the work, not a passing-test claim.

## What was deliberately excluded

No game content or extracted media is included. The import excludes:

- `assets/`, `assets_test/`, `archive/` and all binary PC block data, model/texture/spline blocks, textures, screenshots, fonts, sounds and other visual/audio material;
- trainer archives such as Cheat Engine tables;
- `data_symbols.syms`, `.pat` patterns and other raw symbol/pattern databases;
- executable/object outputs, private analysis databases, DOL/REL/ROM/ISO/GCM files, memory dumps and generated game assets;
- third-party vendor trees whose licensing and separate notices were not re-audited for this import: Detours, fastgltf, glad, GLFW, Dear ImGui, nv_dds, and the standalone stb_image header;
- upstream `.github` workflows, so PC-specific automation cannot accidentally become active in the Boonta repository.

The [`.gitignore`](.gitignore) in this folder blocks common asset, binary and local analysis outputs from being added later. Do not weaken it to publish commercial game data.

## Use and evidence rules

1. Use PC code as a PC reference only. Reimplement required GameCube/Wii behavior independently unless a specific source file's license and platform suitability have been reviewed.
2. Treat function addresses, structure offsets and type layouts as PC-specific.
3. Scripts that extract or convert game data may be studied as code, but run them only on lawful local files. Do not commit or upload their outputs.
4. A green host test or Windows build does not establish compatibility with the GameCube/Wii release.
5. Do not claim this snapshot is a standalone PC build: its upstream vendor dependencies and original data/assets are intentionally omitted.

See [`UPSTREAM_SYNC_STATUS.md`](UPSTREAM_SYNC_STATUS.md) for the fork/upstream divergence recorded at import time and [the repository reuse inventory](../../../REUSE.md) for project-wide reuse rules.
