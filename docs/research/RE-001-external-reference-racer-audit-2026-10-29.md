# RE-001 external reference audit — sp00nznet/racer

**Checked:** 2026-10-29  
**Purpose:** assess whether the public N64 static-recompilation project provides useful evidence for Boonta Reborn 88's research-first workflow, without treating it as proof of GameCube/Wii behavior.

## Source checked

- Repository: [sp00nznet/racer](https://github.com/sp00nznet/racer)
- Type: *Star Wars Episode I: Racer* Nintendo 64 static recompilation using N64Recomp.
- Revision checked: default branch `main`, tree `1197119fb6d4d1e60e9dfcc3d50d610475433af2`; latest visible commit at review time was dated 2026-10-25.
- Primary evidence: its [README/status and build instructions](https://github.com/sp00nznet/racer/blob/main/README.md), [source tree](https://github.com/sp00nznet/racer/tree/main/src), and [license](https://github.com/sp00nznet/racer/blob/main/LICENSE).

## What the project reports

The README describes a static recompilation, not a clean-room GameCube port or a completed decompilation. Its stated milestone status reports a booting game, visible intro/title/menu/race output, controller input, audio, and a playable tournament race on the Boonta Training Course. It also marks the overall playable build as in progress and widescreen as experimental. These are claims made by that project's README; this audit did not independently build or run it.

The documented engineering path is useful as a *process reference*: identify functions and symbols, maintain analysis tools, distinguish stubbed/misidentified OS functions from real implementations, wire scheduling/DMA/RSP/renderer behavior incrementally, and keep explicit milestone status. The repo also documents cross-platform packaging, but that is not a current blocker for Boonta's GameCube vertical slice.

## Relevance to Boonta — bounded conclusions

1. **Do not transplant its runtime or architecture into the GameCube prototype.** This repository targets N64 static recompilation and a PC runtime; Boonta's current target is a clean-room GameCube/Wii homebrew prototype. Similar game title and track names do not establish platform equivalence.
2. **Use it as a hypothesis/index source only.** Its public status and file organization can suggest questions to investigate, but any behavior claim relevant to the original PC version or N64/GC/Wii builds needs platform-specific evidence. It does not close RE-001's outstanding manager/intermediate-phase-to-results-screen call-path gap.
3. **Keep the current priority unchanged.** RE-001 remains the sole active research question. The next bounded step remains proving the missing edge from the post-race manager lifecycle to the concrete results-panel object/substate or a confirmed scene/resource transition. Do not open a parallel RE-002 task because of this reference.
4. **Do not claim validation from screenshots or README status.** No build, emulator, ROM, or executable was run as part of this audit. This is a repository/source-description review only.

## Provenance and licensing boundary

The repository's LICENSE identifies its tools/runtime/build files/documentation as MIT-licensed, while explicitly excluding the original game's code, art, audio, data, and generated derivatives from that grant. This audit imports no code, binary, assets, ROM bytes, raw disassembly, or generated output. It records only high-level observations with links to the source. Any future code reuse would require a separate file-level license/provenance review and must not include game-derived material.

## Result

**Useful as process context; not evidence of GameCube/Wii parity and not a substitute for the remaining RE-001 trace.** No implementation change is justified by this reference audit alone.


## Recheck — installer and local runtime feasibility (2026-11-01)

The current upstream `main` tip reviewed for this recheck is [`694c5663b3a7c30e2862fc240344f34683f99a9c`](https://github.com/sp00nznet/racer/commit/694c5663b3a7c30e2862fc240344f34683f99a9c). Its only changed file is `.github/workflows/installer.yml`: both installer jobs now pin `sp00nznet/recomp-launcher` to v0.6.0. This is an installer/toolchain update, not a new gameplay or results-screen implementation.

The current README still labels **Playable Build — IN PROGRESS**. Its recommended release installer locates the user's own USA `.z64` and builds the native game locally; it is not a ready-made game executable that bypasses the local build. The documented macOS route requires Xcode (including the Metal shader compiler), CMake, Ninja and SDL2 installed through Homebrew.

The separate optional Docker builds are heavier still: the published launcher manifest lists a roughly **1 GB** toolchain for Linux arm64 and **6 GB** for Android. On Apple silicon, the Linux arm64 build runs natively, but the Android x86 toolchain is emulated and can take hours. These are build-toolchain estimates from the project's manifest, not measured storage or runtime measurements from this audit.

### Updated decision

- Keep `sp00nznet/racer` as a source/process reference, not a local, zero-setup route to the Results-screen test.
- Do not recommend its optional Android/Linux Docker toolchains for the current low-storage machine.
- A native macOS run may still be possible on a suitable machine with the user's own legal ROM and the documented dependencies, but it requires a local build and has not been tested here.
- This repository remains an N64 static-recompilation project. Its status, installer, and screenshots do not prove the GameCube/Wii prototype's behavior or close RE-001's conditional finish-to-Results runtime question.

**Evidence boundary:** read-only review of the public README, launcher manifest and latest installer commit. No ROM, build, installer, emulator, executable, or gameplay test was run; no game-derived data was downloaded or uploaded.


## Correction and practical runtime option — macOS release installer (2026-11-01)

A direct check of the latest published [Racer v0.4.0 release](https://github.com/sp00nznet/racer/releases/tag/v0.4.0) and its pinned `launcher/launcher.json` refines the feasibility decision above:

- The release **does publish a macOS Apple Silicon installer**: `Racer-Installer-macos-arm64.zip`, approximately **9.6 MB**. This is only the installer application, not a precompiled game.
- The installer can fetch the project/toolkit and invoke the documented setup script. The setup script clones `N64Recomp`, `N64ModernRuntime` and `rt64` (with submodules), builds the N64 recompiler, recompiles the user's own ROM locally, and builds the native executable.
- The manifest explicitly requires an **Apple Silicon Mac**, Xcode including the Metal shader compiler, and estimates the first local game build at **20–40 minutes and about 6 GB**. It installs CMake, Ninja and SDL2 with Homebrew if missing. These are the PC/macOS target costs; they are distinct from the optional Docker targets (about 1 GB for Linux arm64 and 6 GB for Android).
- The setup script's README says the N64 watchpoint/stack-dump tools are Windows-only. Therefore a macOS build can potentially support a **manual visible-race/Results observation**, but it does not provide the documented native `SWE1R_WATCH` instrumentation on Mac.

### Revised decision

This is now a **conditional runtime-test route**, not a rejected one:

1. If the available Mac is Apple Silicon and at least 6 GB of temporary working space can be made available, the 9.6 MB installer is a simpler entry point than a manual source checkout. Keep the project’s 6 GB / 20–40 minute estimate as the advertised first-build requirement, not a measured guarantee.
2. Choose only **“This computer / pc”** in the installer. Do not select Linux arm64 or Android; those are extra Docker outputs and are irrelevant to the N64 Results observation.
3. Use the user's own legally held USA `.z64`. Do not upload or commit it or any generated game-derived output.
4. The useful test is a normal race through completion and a record of whether the Results/placement screen visibly appears. This would close a runtime-observation gap only for that tested Mac build/session; it would not give an instruction-level writer trace or prove GameCube/Wii parity.
5. If the Mac is Intel, does not have Xcode's Metal compiler, or cannot spare the required disk space, stop before starting the build. Do not install the optional Docker toolchains as a workaround.

**Installer asset:** [Racer-Installer-macos-arm64.zip (v0.4.0)](https://github.com/sp00nznet/racer/releases/download/v0.4.0/Racer-Installer-macos-arm64.zip). Its published asset size is about 9.6 MB; the locally generated game build is much larger and is estimated at about 6 GB.

**Evidence boundary:** verified public release metadata, the project's launcher manifest and `setup.sh`. No installer was run, no ROM was accessed, and no build/runtime test was performed in this session.


## Addendum — Ares v148 as a low-overhead local N64 diagnostic (2026-11-02)

A separate emulator route was checked after the earlier Apple-Silicon-only finding for the *sp00nznet/racer v0.4.0 installer*. That restriction belongs to the recompilation installer, **not** to the Ares emulator itself.

- The official [Ares download page](https://ares-emu.net/download) currently lists **v148**, released 2026-05-30. It says the macOS universal binary requires **macOS 10.15 (Catalina)** and runs natively on **Intel and Apple Silicon**. The official home page lists Nintendo 64 among supported systems and includes debugger functionality.
- Ares has supported a GDB server for its N64 core since v134. The documented workflow is to enable **Settings → Debug → Enabled**; Ares then reports a pending local server at **[::1]:9123**. A MIPS-capable GDB client connects with architecture **mips:4300** and the remote target **[::1]:9123**. See the [GDB connection guide](https://docs.starhaven.dev/papermario-dx/developing/gdb/) for the explicit commands and UI path.
- This means a Mac Intel system on Catalina is not excluded from a **local Ares visual run** merely because the separate Racer recompilation installer only publishes an Apple-Silicon build. No 6 GB N64 recompilation toolchain is needed just to load the owner's existing local .z64 in Ares.
- The prior Ares/GDB homebrew CTest fixture did not pass its continue phase on v139 and v148. That result remains a blocker for claiming a verified GDB session; this addendum does **not** repeat or reinterpret that failed test. A visible Ares race can still be attempted without GDB, and the GDB server/client path can be treated as a separate optional diagnostic after a minimal connection test.

### Correct scope and next test

1. Use the official Ares v148 macOS Universal binary to load the owner's existing US N64 ROM locally, if the machine can run macOS 10.15 or later. Keep the ROM, save states, captures and any game-derived debug output local.
2. Run an ordinary three-lap race and record continuously from the final lap through the first post-finish screen. This is a low-cost observation of the **N64 build under Ares**; it is not proof of Not64 behavior or Wii Classic Controller compatibility.
3. For optional instruction-level inspection, enable Ares GDB and attempt a minimal local connection to [::1]:9123 before relying on any breakpoint/continue workflow. Keep the existing failed CTest result visible; do not call the debugger proven until the actual connection, stop, inspect and continue sequence succeeds.
4. The required target-platform acceptance remains a separate ordinary three-lap run on **Wii + Not64 20260410 + the Wii Classic Controller profile**. Ares cannot substitute for that hardware test.

**Evidence boundary:** official Ares v148 platform/release metadata and N64 support were rechecked on 2026-11-02; the GDB UI/port/client sequence is supported by the linked developer guide. No Ares binary was downloaded or run here, no GDB session was established, and no race/Results screen was observed. No ROM bytes, disassembly, assets or other game-derived data were published.


### Ares v148 quick-start for the owner's Mac

This is the smallest useful next test; do not set up GDB first.

1. Download the official **macOS Universal** archive from [Ares v148](https://github.com/ares-emulator/ares/releases/download/v148/ares-macos-universal.zip), extract it, and move `ares.app` to Applications. Ares lists Catalina/macOS 10.15 as the minimum and supports both Intel and Apple Silicon.
2. Open Ares and load the owner's already-local US `.z64` in the Nintendo 64 core. The documented menu path for loading an N64 title is **Load → Nintendo → Nintendo 64**.
3. Open **Settings → Input**, select the Nintendo 64 core, and map the throttle, steering and required menu controls to the Mac keyboard. Ares uses configurable per-core input mappings; this is only for the desktop Ares diagnostic, not the Wii Classic profile.
4. Start an ordinary single-player race with the normal three-lap setting. Do not use cheats, save states, fast-forward or pause around the finish. Keep a continuous local capture from the final lap through the first Results frame. Hold accelerator A across the finish as the current static hypothesis requires; release only once Results is visibly on screen, then press A once to continue after the capture.
5. Record Ares version, ROM region, whether the race booted, whether the final-lap indicator appeared, whether Results appeared, and any freeze/black-screen point. Keep the ROM, save states, video and all game-derived debug data on the owner's machine.

### Historical compatibility lead — explicitly not a v148 pass

The Ares project's [N64 compatibility-list issue #143](https://github.com/ares-emulator/ares/issues/143) contains a contributor's 2022 report (updated through **ares 127 dev**) that lists *Star Wars Episode I: Racer* under “No issues found,” while explicitly saying speed/framerate were not evaluated. This is a useful reason to try Ares, but it is not an official current compatibility guarantee, it is not a full three-lap/Results report, and it does not validate v148. The v148 release notes later describe N64 CPU/RSP JIT rewrites, so the old result should not be silently carried forward as current proof.

**Evidence boundary:** this quick-start and compatibility lead are documentation only. No Ares app was installed or launched; no N64 race, save state, GDB session, video capture or Results screen was observed. The Ares run remains the next local action. The separate Wii + Not64 + Wii Classic Controller validation remains required and unchanged.


### Public N64 source snapshot refresh — bounded negative check (2026-11-02)

The public `sp00nznet/racer` repository was rechecked at current default-branch commit [`694c5663b3a7c30e2862fc240344f34683f99a9c`](https://github.com/sp00nznet/racer/commit/694c5663b3a7c30e2862fc240344f34683f99a9c), dated 2026-10-30. This refresh was limited to repository structure, the generated symbol manifest and bounded code-search queries; it did not build the project or inspect a ROM.

- The tracked `src/` directory contains `main.cpp` and the generated `section_table.cpp`; the latter maps addresses to recompiled function pointers. The current `symbols.toml` still labels the relevant range only as `func_80080BEC` at `0x80080BEC`, size `0x5F0`. No semantic name for the internal auto-detected label at `0x80080DB4` was found.
- Bounded searches at that exact snapshot returned only the generic symbol-manifest and section-table references for `func_80080BEC`; no code-search hit for `0x80080DB4`, `Locl`, or a game-code `Fini`/Results consumer was returned. The `Hang` matches were unrelated frontend/debug text. These search results are a limited negative check of the indexed public repository, not proof that no relevant instruction sequence exists in the original executable or in unindexed/private material.
- The latest visible public commit was an installer/launcher update, not a semantic decompilation update. The repository still describes itself as an N64 static recompilation; the public tree does not provide a newly named source-level finish-to-Results call chain.

**Conclusion unchanged:** this public refresh does not close the remaining N64 question and does not justify renaming the generic function, inferring a Results transition, or changing GameCube/Wii gameplay. The decisive next evidence remains a local ordinary three-lap runtime capture through the first Results frame on Ares or, separately, Wii + Not64 + the Wii Classic Controller. Keep the ROM and capture local. No game code, ROM data, disassembly, assets or generated game content were added to this repository.
