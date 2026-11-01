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
