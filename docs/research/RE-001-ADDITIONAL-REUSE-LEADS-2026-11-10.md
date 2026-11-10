# Targeted external reuse discovery — 2026-11-10

**Purpose:** add a small, verified set of external references that was not covered in sufficient detail by the existing toolchain and source audits. This is an incremental research note, not a new complete-game inventory.

**Repository baseline checked:** `main` at `730a49bd288db9bf749bbc7241d7a133cce891f9`.

**Disposition:** references only. No third-party source code, binaries, game data, ROMs, textures, models, audio, or extracted assets were copied into Boonta. No external tool was built or executed during this audit.

## Executive result

| Reference | Exact revision / status | Best use for Boonta | Decision |
|---|---|---|---|
| `zeldaret/tww` | `d217e2b5e1c1514e6f3f640835f83f01dd67aa72`; CC0-1.0; active GameCube decompilation | Compare generic Dolphin OS, DVD, GX, REL-linking, archive and decompression implementations | **High-value read-only reference**; inspect only the relevant component and its provenance |
| `devkitPro/gamecube-tools` | `3b7f914df771d4b779d88607ceed2ec9264ff93a`; GPL-2.0 | Independent TPL/GX texture conversion reference, including palettes and mipmaps | **Useful separate tool/reference**; do not copy GPL code into Boonta |
| `OpenSWE1R/openswe1r` | `1fcb4a8e8b5e031f0dde38b340cfca1b07e9738e`; GPL-2.0; last code push 2020-01-04 | Historical PC port architecture: x86/API emulation, platform abstraction, runtime patching | **Read-only PC reference**; not a GameCube/Wii port and not a current implementation base |
| `Star Wars: Galactic Racer` | Official launch 2026-10-06; official interviews/features | Modern design benchmark for vehicle-class identity, race-line choices, branching routes and progression | **Design reference only**; not a source-code, asset or 1999-game behavior reference |

## 1. `zeldaret/tww` — a strong GameCube SDK and resource-system reference

- Repository: [zeldaret/tww](https://github.com/zeldaret/tww)
- Pinned revision: [`d217e2b5e1c1514e6f3f640835f83f01dd67aa72`](https://github.com/zeldaret/tww/tree/d217e2b5e1c1514e6f3f640835f83f01dd67aa72)
- GitHub reports **CC0-1.0** for the repository.
- The project is a work-in-progress decompilation of **The Legend of Zelda: The Wind Waker for GameCube**. Its README states that the repository contains no game assets or assembly and that a user-owned copy is required to build it. It lists the GameCube IDs/revisions `GZLE01`, `GZLP01`, `GZLJ01`, and kiosk `D44J01`.
- The repository was pushed on 2026-11-07. This is a more recently maintained GameCube source reference than many older sample projects.

### Precisely relevant source areas

The pinned tree contains implementations and headers in these areas:

- Dolphin OS and module linking: `libs/dolphin/src/os/OSLink.c`, `libs/dolphin/include/dolphin/os/OSLink.h`.
- DVD and filesystem interfaces: `libs/dolphin/include/dolphin/dvd/`.
- GX texture and graphics interfaces: `libs/dolphin/include/dolphin/gx/`, including `GXTexture.h`; implementation examples include `libs/dolphin/src/gx/GXTexture.c`.
- JSystem archive and decompression code: `libs/JSystem/include/JSystem/JKernel/JKRArchive.h`, `JKRCompArchive.h`, `JKRDecomp.h`; implementations include `libs/JSystem/src/JKernel/JKRArchivePri.cpp` and `JKRDecomp.cpp`.

### Why it matters

This gives Boonta a concrete, GameCube-specific reference for how a large title organizes low-level OS services, DVD access, dynamically linked REL modules, GX texture interfaces, resource heaps, archives and decompression. It is more actionable for native GameCube runtime questions than trying to infer those interfaces from a Windows PC project or an N64/MIPS project.

It can help us answer narrow engineering questions such as:

1. Which OS/REL responsibilities belong in our clean-room runtime versus the facilities already provided by libogc?
2. What archive/resource-loading lifecycle should a native port support?
3. Which GX texture upload and palette concepts must our asset pipeline model?
4. Which archive/compression algorithms already have established GameCube implementations that we can compare against synthetic fixtures?

### Limits and safe reuse decision

- Wind Waker is **not** Star Wars: Episode I – Racer. Its game logic, assets, resource IDs, data layouts and game-specific assumptions are not evidence for Racer.
- The audited README lists GameCube releases; it does not establish Wii behavior or GameCube/Wii parity for Racer.
- The project is a matching decompilation that uses a local original game image. Its CC0 repository licence is useful, but it does not grant rights to redistribute Nintendo game assets or other third-party data. Before copying any individual implementation, review that file's authorship, history, dependencies and whether it is generic SDK/JSystem code or game-specific reconstructed code.
- Do not vendor the entire repository or its build system. Read the exact files required by a bounded Boonta task and prefer libogc where libogc already provides the needed service.

**Recommendation:** add `zeldaret/tww` to the first-reference list for a future, narrowly scoped GameCube resource-loading or GX compatibility question. Do not create a second archive loader or texture subsystem before comparing the existing Boonta code, libogc and these pinned references.

## 2. `devkitPro/gamecube-tools` — GX texture/TPL conversion benchmark

- Repository: [devkitPro/gamecube-tools](https://github.com/devkitPro/gamecube-tools)
- Pinned revision: [`3b7f914df771d4b779d88607ceed2ec9264ff93a`](https://github.com/devkitPro/gamecube-tools/tree/3b7f914df771d4b779d88607ceed2ec9264ff93a)
- GitHub reports **GPL-2.0**.
- The repository describes itself as tools for GameCube/Wii projects. Its `Makefile.am` builds `gxtexconv` and declares FreeImage plus bundled DXTn/Squish components as dependencies of the converter.

### What was verified in source

The `gxtool/gxtexconv.cpp` command-line entry point supports:

- direct image conversion to a `.tpl` output (`-i` / `-o`);
- a script-driven conversion mode (`-s`) with an optional dependency file;
- I4, I8, IA4, IA8, RGB565, RGB5A3, RGBA8, CI4, CI8 and CMPR texture formats;
- palette-format selection for indexed textures and optional mipmap/LOD settings.

The converter therefore covers more than Boonta's current authored RGB565 texture path. It is a useful independent reference for TPL layout, tiled formats, indexed palettes and mipmap production.

### What it does not establish

- It is an image-to-TPL converter, not a Star Wars: Episode I – Racer archive extractor.
- It does not prove that PC, N64 or any unidentified console Racer texture block can be read.
- The source was inspected, but this audit did **not** build or execute the tool, compare emitted TPL bytes, benchmark it, or audit every bundled dependency's licence.
- Its GPL-2.0 terms mean its implementation must not be copied into Boonta's existing codebase without an explicit licensing decision.

**Recommendation:** use it as a separate reference/benchmark only if Boonta next needs indexed or CMPR TPL output, mipmaps, or a test oracle for the current exporter. First compare a tiny synthetic fixture against the repo's existing generated RGB565 asset and CI checks. Do not replace the current path or add a build dependency solely because the tool exists.

Primary source links:

- [CLI and format list](https://github.com/devkitPro/gamecube-tools/blob/3b7f914df771d4b779d88607ceed2ec9264ff93a/gxtool/gxtexconv.cpp)
- [Texture conversion implementation](https://github.com/devkitPro/gamecube-tools/blob/3b7f914df771d4b779d88607ceed2ec9264ff93a/gxtool/converter.cpp)
- [Texture file writer](https://github.com/devkitPro/gamecube-tools/blob/3b7f914df771d4b779d88607ceed2ec9264ff93a/gxtool/tfbinarytdf.cpp)
- [Build/dependency declaration](https://github.com/devkitPro/gamecube-tools/blob/3b7f914df771d4b779d88607ceed2ec9264ff93a/Makefile.am)

## 3. `OpenSWE1R/openswe1r` — clarify its actual scope and age

- Repository: [OpenSWE1R/openswe1r](https://github.com/OpenSWE1R/openswe1r)
- Pinned revision: [`1fcb4a8e8b5e031f0dde38b340cfca1b07e9738e`](https://github.com/OpenSWE1R/openswe1r/tree/1fcb4a8e8b5e031f0dde38b340cfca1b07e9738e)
- Licence: **GPL-2.0-or-later** according to its README/GitHub metadata.
- Latest code push on the checked repository metadata: **2020-01-04**.

The README describes an interoperability-oriented PC port combining a subset of Windows API emulation, x86 CPU emulation and runtime patching of the original Windows game. It explicitly says that not all original functions have been replaced and that the original game binary and art assets are still required. Its documented target is the x86 Windows version. The CMake file requires Unicorn, OpenGL, GLEW, SDL2 and OpenAL, with optional ENet.

### Value and limits

This is a useful historical architecture reference for separating host APIs, CPU emulation, original-code replacement and platform rendering/audio/input glue. It may offer research leads when tracing the Windows game or comparing subsystem boundaries.

It is **not** a native GameCube/Wii implementation, not a complete clean-room game, and not evidence that its code or assets can be placed in Boonta. It is also an old and largely inactive codebase, so its build instructions and dependencies should not be treated as current setup guidance.

**Recommendation:** retain it as a read-only Windows-PC architecture reference. No code import, dependency adoption, porting assumption or asset import is proposed. This clarifies and pins the earlier brief mention in `docs/TECHNICAL_RESEARCH.md`.

## 4. `Star Wars: Galactic Racer` — modern gameplay/design reference

Official sources:

- [Official game feature page](https://www.starwars.com/games-apps/star-wars-galactic-racer)
- [Official launch article, 2026-10-06](https://www.starwars.com/news/star-wars-galactic-racer)
- [Official developer interview, 2026-04-30](https://www.starwars.com/news/star-wars-galactic-racer-reveal-trailer)

The official launch article says the game launched worldwide on **2026-10-06** for PS5, Xbox Series X|S and PC. The official feature page and interview describe ideas that may be useful as a modern design benchmark:

- branching routes and risk/reward choices;
- several repulsorcraft classes with distinct handling and tactical strengths;
- vehicle-specific racing lines and momentum/braking characteristics;
- vehicle upgrades, unlocks and event selection;
- a run-based campaign with consequential choices, rivalries and persistent progression elements.

The developer interview gives examples of different handling identities: speederbikes are described around heavy braking into corners and strong acceleration on exit, while skim speeders reward flowing lines, carrying momentum and negotiating narrow gaps. Those are **developer descriptions of Galactic Racer**, not measured physics values or evidence about the 1999 game.

### How to use this reference

Use it to ask design questions, not to copy expression or content:

- Are Boonta's craft classes meaningfully different in handling, not just statistics?
- Do branching route options trade distance, danger and surface/obstacle conditions in a readable way?
- Do upgrades change a vehicle's build and player decisions without erasing the importance of driving skill?
- Can event progression and rival behavior create stakes beyond a single lap timer?

This source is a contemporary design benchmark. It is **not** a reverse-engineering source for the 1999 Racer, not a source for proprietary code or assets, and not evidence that any feature existed in the original game. Do not copy footage, screenshots, models, audio, interface art or other commercial content into Boonta.

## Ranked next actions

1. **When the asset pipeline is next in scope:** compare our existing synthetic RGB565 exporter with the documented TPL/GX format behavior. Only add another conversion path if a concrete missing format (for example CI8/RGB5A3/CMPR) is required by a verified, legally usable input.
2. **When resource loading is next in scope:** inspect the exact `zeldaret/tww` OSLink/DVD/GX/JKernel files alongside libogc and Boonta's current runtime. Write a concise compatibility table before deciding whether to extend the existing loader.
3. **When vehicle/track design is next in scope:** translate Galactic Racer's publicly described concepts into clean-room design questions and testable Boonta mechanics; do not copy its art or claim equivalence with Racer 1999.
4. Keep OpenSWE1R as a PC-only GPL reference; do not use it as a GC/Wii implementation shortcut.

## Explicit non-actions and evidence limits

- No source code from any of these repositories was copied.
- No original-game ROM, disc image, DOL/REL, executable, model, texture, sound or extracted game data was accessed or added.
- No tool installation, native build, local conversion, Dolphin run or hardware test was performed for this note.
- Repository licence metadata is a starting signal, not a substitute for file-level provenance and dependency review.
- PC, N64, Dreamcast, GameCube and Wii findings remain separate. No original retail GameCube/Wii Racer executable is established by these references.

This note supplements, rather than replaces, the existing [GameCube/Wii toolchain reuse audit](GC-WII-RE-TOOLCHAIN-REUSE-AUDIT-2026-11-03.md), [N64 texture-block reuse audit](N64_TEXTURE_BLOCK_REUSE_AUDIT_2026-11-10.md), [PC/N64/Dreamcast source matrix](RE-002-platform-source-matrix.md), and [reverse-engineering-first policy](../REVERSE_ENGINEERING_FIRST.md).

## 5. `LagoLunatic/GCFT` + `gclib` — practical GameCube container and asset inspection

- GUI repository: [LagoLunatic/GCFT](https://github.com/LagoLunatic/GCFT)
- Exact inspected revision: [`22f36948909fb50580711463eff4b8ee33922841`](https://github.com/LagoLunatic/GCFT/tree/22f36948909fb50580711463eff4b8ee33922841)
- Library repository: [LagoLunatic/gclib](https://github.com/LagoLunatic/gclib)
- Exact library submodule revision used by that GCFT tree: [`4e8f48000b757defc05179e341c3a2b06dfaadee`](https://github.com/LagoLunatic/gclib/tree/4e8f48000b757defc05179e341c3a2b06dfaadee)
- GitHub repository metadata reports **MIT** for both repositories. The pinned GCFT revision's submodule entry resolves to the exact gclib commit above.
- GCFT was pushed on 2026-10-22 and its metadata reports ongoing repository updates in November 2026.

### What its documented format coverage actually includes

GCFT's README lists support for:
- GCM images, RARC archives and DOL section inspection;
- BTI textures and image conversion to/from PNG;
- many J3D model formats (including BMD/BDL) and their embedded textures;
- BMT material tables;
- JPC particle archives (versions 1-00 and 2-10);
- Yaz0 and Yay0 compression;
- BMG messages (with the README explicitly limiting its current BMG support to Wind Waker).

It can inspect/extract/replace individual files and folders in GCM/RARC, dump BTI images, replace textures embedded in BMD/BDL/BMT/JPC, view model previews, and compress/decompress Yaz0/Yay0.

The separate `gclib` README describes the underlying Python format implementations and distinguishes full from partial support:
- GCM and DOL: read/edit, no create;
- REL and RARC: read/edit/create;
- Yaz0/Yay0 and BTI: read/edit/create;
- J3D, JPC and BMG: partial read/edit support;
- BFN: read only.

### Why this is useful

This is a much more concrete *local inspection workbench* than a generic reverse-engineering list. If a legally obtained target disc contains any of these common Nintendo container formats, GCFT/gclib may help enumerate its structure, inspect DOL sections, unpack archives and understand standard BTI/J3D resources without building another parser from scratch.

It can also help us create and validate our **own** BTI/J3D-oriented test assets if those formats are selected for the clean-room engine. The library's MIT terms make it a better candidate for future dependency evaluation than GPL-only converters, subject to reviewing the exact source and dependency licenses before adoption.

### Strict limits

- The README does **not** claim support for Star Wars: Episode I – Racer's proprietary model, track, spline, sprite or texture blocks. A `.bin`, `.arc` or similar extension is not enough to establish that a file is GCM/RARC/BTI/J3D/Yaz0/Yay0.
- It is focused on common GameCube formats; do not assume that every Wii-specific format, REL variant, game-specific compression or Racer resource is supported.
- The `J3D` coverage in gclib is explicitly partial. GCFT's GUI features do not turn that partial coverage into a guarantee of correct round-trip preservation.
- GCFT uses Python 3.12 and several GUI/image dependencies. This audit inspected the dependency manifest but did not install or execute them.
- No local disc, game file or extracted resource was supplied or processed during this research pass.

**Recommendation:** keep GCFT/gclib as the first *candidate* local inspector when a specific GC/Wii input is identified as GCM/RARC/DOL/BTI/J3D/Yaz0/Yay0. Before relying on it for a Racer file, first test a tiny user-owned sample locally and retain only aggregate outcomes; for any format not explicitly supported, report UNKNOWN and return to the exact file signature/format investigation. Do not add a new parser or make gclib a Boonta runtime dependency until an actual target file demonstrates the need.

Primary references:
- [GCFT pinned README](https://github.com/LagoLunatic/GCFT/blob/22f36948909fb50580711463eff4b8ee33922841/README.md)
- [GCFT pinned dependencies](https://github.com/LagoLunatic/GCFT/blob/22f36948909fb50580711463eff4b8ee33922841/requirements.txt)
- [gclib format coverage](https://github.com/LagoLunatic/gclib/blob/4e8f48000b757defc05179e341c3a2b06dfaadee/README.md)
- [Exact GCFT gclib submodule entry](https://github.com/LagoLunatic/GCFT/tree/22f36948909fb50580711463eff4b8ee33922841/gclib)

## 6. `zeldaret/tp` — additional GameCube **and Wii** SDK/runtime reference

- Repository: [zeldaret/tp](https://github.com/zeldaret/tp)
- Exact inspected revision: [`c8fa8c9e2aab72cf4e5db0e5d1c84a9ea6ee6eb0`](https://github.com/zeldaret/tp/tree/c8fa8c9e2aab72cf4e5db0e5d1c84a9ea6ee6eb0)
- GitHub metadata reports **CC0-1.0**.
- The README identifies this as a work-in-progress decompilation of The Legend of Zelda: Twilight Princess. It explicitly lists several GameCube releases and Wii releases, including North America Rev 0/Rev 2, PAL and Japan. It states that the GC versions are completely matching while Wii matching work is continuing, and that multiple versions are built from one codebase using conditional compilation.
- The project says its repository does not contain game assets or assembly and requires a local copy of the game to build.

### Why it is useful

Unlike the Wind Waker reference above, this project explicitly covers **both GameCube and Wii** build variants. It can provide another target-specific comparison for:
- version/region configuration and conditional build separation;
- Dolphin OS interfaces and Wii/GameCube platform deltas;
- disc/resource loading, GX, DVD, controller and system libraries, where the exact relevant source files and provenance are checked;
- how a mature decompilation keeps multiple retail executable identities separate while using shared source.

This may help us make Boonta's native GameCube and Wii variants less error-prone. It is not a substitute for official devkitPro/libogc documentation and does not by itself mean a single binary or one platform's behavior is valid on the other.

### Limits and reuse decision

- Twilight Princess is not Racer. Its game code, assets, symbols, data layouts and resource IDs are not evidence for Racer.
- Its documented matching status applies to the relevant Twilight Princess binary versions, not to our game.
- Treat CC0 as a repository-level licence signal only; still inspect file-level provenance, generated files and any vendored dependency before copying an implementation. No original game data is licensed by CC0.
- Keep its original assets/assembly and private analysis inputs out of Boonta.

**Recommendation:** when a concrete Wii/GameCube platform difference arises in Boonta, compare the exact relevant source path in this pinned repository and libogc. Do not bulk-import Twilight Princess source or replace our engine architecture with a game's decompilation.

Primary references:
- [Pinned README and target-version table](https://github.com/zeldaret/tp/blob/c8fa8c9e2aab72cf4e5db0e5d1c84a9ea6ee6eb0/README.md)
- [Pinned repository tree](https://github.com/zeldaret/tp/tree/c8fa8c9e2aab72cf4e5db0e5d1c84a9ea6ee6eb0)

## 7. Candidates deliberately held back — licence or evidence not established

Two further repositories appeared relevant in broad search, but were **not** added to the reuse recommendation:

- [quatric/nintoolbox](https://github.com/quatric/nintoolbox) advertises many GameCube/Wii archive, texture, model and audio formats and was pushed on 2026-11-10. The repository metadata returned no detected SPDX licence and the root `LICENSE` file was not present at the inspected location. It is a discovery lead only: do not install, vendor, copy or depend on it until a clear licence, dependency provenance, exact format tests and project applicability are established.
- [RenolY2/SuperBMD](https://github.com/RenolY2/SuperBMD) documents BMD/BDL import/export and material/texture handling, but the repository metadata did not establish a licence and the inspected root `LICENSE` path returned not found. Do not copy or integrate it until the maintainers provide a clear licence and dependencies have been reviewed.

These are intentionally recorded as **HOLD**, not ranked as reusable software. A plausible feature list is not a licence grant or evidence that a tool works on Racer files.

