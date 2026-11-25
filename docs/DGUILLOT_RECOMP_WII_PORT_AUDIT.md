# Audit: dguillot-gh/star-wars-racer-recomp as a Wii/GameCube porting base

Date: 2026-11-25  
Scope: source review only. No ROM was built or run, no Wii/GameCube hardware was tested, and no changes were made to dguillot-gh's repository.

## Executive conclusion

`dguillot-gh/star-wars-racer-recomp` is the most useful technical reference found so far for a native recompilation path. It is not simply an Android launcher: it takes the original N64 MIPS program through N64Recomp, compiles the generated C, supplies an N64 OS/runtime layer, and sends graphics display lists through RT64's high-level RSP/RDP path.

The game is reported by that repository's README as playable through a complete Tournament race on a Pixel 8. That is the author's stated Android result, not a result independently reproduced during this audit.

**It is not a Wii-ready port.** The current runtime makes assumptions that directly conflict with the Wii environment: a 4 GB virtual address reservation, 512 MB of accessible RDRAM space, host `std::thread` workers, SDL, and RT64 configured for Vulkan or D3D12. The Wii target would need a smaller memory model, a libogc/LWP platform layer, endian-aware recompiled-memory access, and a new GX renderer.

The right strategy is to reuse the *recompilation knowledge and game-specific runtime fixes*, not to try to compile the Android application unchanged.

## Confirmed repository snapshot

Repository: https://github.com/dguillot-gh/star-wars-racer-recomp

- Default branch: `main`; the repository currently exposes one branch and no GitHub releases.
- Latest main commit inspected: `68d3d2709cf71c07b5abed3627e01b03696cefd2`, dated 2026-10-21.
- The top-level tree has 90 entries. It contains the recompiler configuration, symbol map, host runtime, Android application, tools and three submodules.
- The project README describes an Android 7+ arm64/Vulkan build and a Windows-based build process. It does not describe a Wii or GameCube target.
- The README says the code is built from a user's own ROM, and generated game code and APKs are not to be committed or shared.
- The repository has an MIT licence for its own code, but its licence explicitly excludes the original game and generated code derived from the ROM. Reuse of generic source still requires preserving notices and checking provenance.

Important upstream and pinned components:

| Component | Pinned revision in this project | Role |
|---|---|---|
| N64ModernRuntime | `dguillot-gh/N64ModernRuntime`, `63b808662fc8b604e09552f7c2c8cc7015e8313c` | N64 OS/runtime, memory, events, threads, input and saves |
| N64Recomp | `dguillot-gh/N64Recomp`, `36286fb9a96f325a64b3c600131ba00af44654fc` | MIPS-to-C static recompiler and RSP recompiler |
| RT64 | `dguillot-gh/rt64`, `9f6c5db2d2834c576358b491951d97498ba3736d` | RSP/RDP HLE and host graphics renderer |
| Plume | `dguillot-gh/plume`, `589f88f07dea9da260fb2d20ac505552433dc6d0` | RT64's graphics/window backend |
| SDL2 | `libsdl-org/SDL`, `5d249570393f7a37e037abf22cd6012a4cc56a71` | Window, input and audio host APIs |

The nested dependency revisions matter. Do not silently replace them with newer upstream branches while reproducing the Android behavior: the project relies on patches in its `racer-android` branches.

## What the project actually does

### 1. Static recompilation

- `symbols.toml` supplies the function map for the USA N64 game.
- `recomp.toml` configures N64Recomp and its stub/redirect decisions.
- N64Recomp emits C source into `RecompiledFuncs/` from the local ROM.
- `tools/fix_fallthroughs.py`, `tools/post_recomp_patches.py` and `tools/gen_lookup_table.py` apply project-specific corrections and generate the function lookup table.
- `src/section_table.cpp` maps N64 virtual addresses to the compiled C functions. The README/build instructions describe 1,409 function entries.
- `aspMain.toml` configures RSPRecomp for the game's audio microcode. Its output `rsp/aspMain.cpp` is also made locally from the ROM and is not committed.

This division is valuable: ROM analysis and C generation can happen on a PC. The Wii would only need to compile and run the generated C plus a Wii-compatible runtime. N64Recomp itself does not need to execute on the console.

### 2. Runtime and game-specific fixes

The host registers callbacks for rendering, RSP, audio, input, graphics/window lifecycle, events, errors and threads. N64ModernRuntime then provides the N64-style OS behavior expected by the recompiled functions.

The Android port documents and implements important Racer-specific corrections, including:
- routing the game's private copies of libultra routines to runtime implementations where necessary;
- initializing PI and VI state that the skipped boot/OS code would normally establish;
- implementing a controller-status response for SI DMA;
- providing a ROM word-read path for the game's PI asset loader;
- configuring the game as using 16-Kbit EEPROM;
- handling the game's audio microcode with RSPRecomp;
- splitting merged function symbols where the game's function-pointer tables target an address inside a merged function.

These findings are more useful to Boonta than the Android menus. They describe what must be true for the original game code to run correctly in a non-N64 host environment.

### 3. Graphics path

The important detail is in `SWE1RRenderContext::send_dl()`:

1. It takes the game's `OSTask` graphics task.
2. It extracts the N64 microcode and display-list addresses.
3. It resets RT64's HLE RSP state.
4. It calls RT64 to load the corresponding GBI command set.
5. It passes the display list to RT64's display-list interpreter.
6. `update_screen()` presents the framebuffer using the N64 VI registers.

In `src/main.cpp`, the RSP callback returns the recompiled `aspMain` routine for audio tasks and a no-op routine for other RSP tasks. Graphics are not being run as a complete software N64 RSP microcode implementation here; they are handled through RT64's high-level display-list path.

That is a major architectural distinction for Wii. A GX backend needs a way to consume the same GBI/RDP work and produce GX rendering. Merely compiling the generated MIPS functions does not draw the game.

## Wii/GameCube compatibility audit

| Area | What the Android project uses | Wii implication |
|---|---|---|
| Recompiled game code | C emitted by N64Recomp | **Plausibly reusable, not yet cross-compiled for PPC.** The generated functions and lookup-table model are the best candidate for a small proof-of-concept. |
| Memory layout | 4 GB virtual reservation; 512 MB enabled RDRAM region | **Must be redesigned.** The Wii cannot reserve or commit this host-style address space. |
| Memory endianness | N64 access macros use byte/halfword XOR lane adjustments | **Must be made target-endian aware.** The current Android/Windows host path is little-endian; Wii's Broadway PowerPC is big-endian. |
| Runtime threads | `std::thread`, semaphores, mutexes, event workers and a thread-cleaner worker | **Needs a Wii threading backend or compatibility layer**, likely using libogc LWP primitives. |
| Runtime events/timing | Host monotonic clock, VI worker thread, message queues and scheduler | **Needs porting and timing validation** against Wii VI/GX and the game scheduler. |
| Renderer | RT64 HLE with Vulkan on Android and D3D12 on Windows | **Not directly usable as-is.** Wii uses GX; this project has no GX renderer/backend selected in its host code. |
| Audio | SDL queued audio callback; RSPRecomp-generated audio microcode | Audio microcode is a useful starting point; output must be connected to Wii audio APIs and timing. |
| Input | SDL GameController plus Android touch input/JNI | Replace with PAD/WPAD input; keep the N64 button mapping, not the Android UI. |
| ROM/config/save I/O | `std::filesystem`, SDL paths and Android document picker | Replace with FAT/libogc file handling and Wii save paths. |
| Build | Windows host tools, Android Gradle/NDK, CMake and C++20 | Separate host-side recompiler build from a devkitPPC/libogc target build. |

### Critical blocker A — memory reservation

In the pinned N64ModernRuntime revision, `librecomp/include/librecomp/addresses.hpp` defines:

- `mem_size = 512 MiB`;
- `allocation_size = 4 GiB`.

`librecomp/src/recomp.cpp` reserves that region using `VirtualAlloc` on Windows or `mmap`/ `mprotect` elsewhere. The first 512 MiB are made read/write and the remaining virtual address space is left inaccessible to catch bad pointers.

This is a desktop memory model, not a Wii memory model. A Wii build needs a bounded RDRAM arena in real MEM1/MEM2 memory and explicit handling for all addresses outside the actual game RAM. The current implementation also places:
- a PI handle at N64 address `0x80800000` (8 MiB offset);
- patch data beginning at `0x80801000`;
- the mod/runtime heap starting at `0x81000000` (16 MiB offset).

The Wii implementation must either preserve these address relationships in a smaller arena or deliberately redesign the runtime's scratch/heap layout. Simply changing `allocation_size` to 8 MiB would break the current initialization assumptions.

### Critical blocker B — byte order

The pinned N64Recomp `include/recomp.h` defines memory operations with these patterns:

- `MEM_B` adjusts an address with XOR 3;
- `MEM_H` and `MEM_HU` adjust with XOR 2;
- `MEM_W` accesses the word directly.

This is the little-endian-host representation strategy used by the inspected Android/Windows targets. Wii's Broadway PowerPC is big-endian. The Wii build needs a target-specific memory access implementation and tests proving byte, halfword, word, unaligned and doubleword reads/writes match N64 big-endian semantics. Do not remove the XORs globally: retain the current behavior for the existing little-endian targets.

### Critical blocker C — graphics

The current render context explicitly selects Vulkan for Android and D3D12 for the other host path. RT64's HLE processing is coupled to its renderer and graphics backend. Wii GX is not a drop-in graphics API.

The useful reusable portion is the *command interpretation knowledge*:
- the game's GBI microcode selection;
- display-list traversal;
- command decoding and state tracking;
- RDP texture/TMEM/TLUT and framebuffer behavior;
- VI scaling, scissor and interlaced framebuffer observations.

The Wii port must either adapt enough of this HLE state machine to submit GX work, or take a different approach to executing N64 graphics tasks. A complete GX renderer is a substantial task; it should be prototyped before porting the full runtime.

### Critical blocker D — host concurrency and OS services

The runtime uses `std::thread` for the game, graphics, RSP task, VI, saving and cleanup workers. It also relies on semaphores, locks, condition variables and concurrent queues. The current CMake/runtime source has Windows, Linux/Android and Apple platform assumptions, but no Wii/libogc backend.

A Wii port should first inventory which threads are genuinely required for Racer, then map them onto libogc LWP threads/queues or a simpler cooperative scheduler. The N64 game scheduler must continue to receive the message and VI events it expects. This must be tested independently of graphics.

## What should be reused — and what should not

### High-value references

1. **`symbols.toml` and `recomp.toml`:** the best starting point for the game function map and N64Recomp configuration. Keep them versioned with the USA ROM revision they describe.
2. **`tools/post_recomp_patches.py`:** records game-specific redirects, splits and stub decisions. This is a high-value behavioral/engineering map.
3. **`src/section_table.cpp` generation:** the function-address-to-native-function lookup mechanism.
4. **`aspMain.toml`:** the audio microcode extraction/recompilation configuration. The locally generated output must remain private.
5. **Game bootstrap findings in `src/main.cpp`:** PI handle, VI scheduler state, controller SI response, ROM word reads and EEPROM configuration.
6. **Runtime interface design:** the callback separation in `ultramodern::Configuration` is a useful model for a Wii-specific platform layer.

### Do not carry over unchanged

- Android Java activities, touch pad, JNI and Gradle app packaging.
- SDL2 window, input and audio code.
- RT64's Vulkan/D3D12 renderer and Plume swap-chain backend.
- The 4-GB virtual memory reservation and 512-MB RDRAM allocation.
- Android-specific heap, Vulkan-surface, Mali shader and phone lifecycle fixes.
- Any ROM-derived generated function code or game assets in a public Boonta commit.

### Submodule patch burden

The pinned `racer-android` RT64 branch is not a tiny Android wrapper: compared with the fork's `main` branch, GitHub's comparison reports 77 commits ahead and 9 behind, with changes across HLE RSP/RDP, framebuffer, VI, texture handling, shaders and renderer code. The N64ModernRuntime branch is also game-patched, and N64Recomp has a modified memory header. These exact revisions should be preserved as references; blindly updating them to upstream would risk removing behavior required by Racer.

## Recommended implementation sequence for Boonta

### P0 — Freeze the known-good reference

- Record the exact commits and submodule revisions above.
- Keep the user's ROM local; do not add it, generated C, generated RSP source or an APK to Boonta.
- Maintain a separate reference track for the Not64/WiiFlow route. It is an immediate way to run the original N64 game, not a native port.

### P1 — Prove that the generated C can target PPC

Create a small private cross-compile experiment using devkitPPC:
- compile a synthetic source file that includes the pinned `recomp.h`;
- exercise representative 32-bit arithmetic, sign extension, 64-bit MIPS operations and memory macros;
- add explicit big-endian memory-access helpers and tests;
- verify compiler support for the recompiler's function attributes and 128-bit intermediate arithmetic.

Only after this passes should the project attempt to compile a small sample of locally generated game functions for PPC. The generated game C stays local.

**Exit condition:** a small native PPC test ELF/DOL links and its memory/arithmetic tests pass. This proves only the compiler/ABI layer, not the game.

### P2 — Build a small Wii runtime, not the whole desktop runtime

Implement and test a bounded RDRAM arena, bad-address/MMIO handling, PI ROM reads, EEPROM saves, message queues, VI timing and thread scheduling using libogc. Keep functions that only depend on generic C/C++ where possible; isolate every hardware-dependent operation behind a platform callback.

**Exit condition:** tests prove the game-memory model, PI reads, EEPROM behavior, SI/controller responses and scheduler/message flow without starting the renderer.

### P3 — Prove GX rendering with one small display-list path

Before trying the full game, build a minimal GX backend that can:
- receive a graphics task and decode its GBI display list;
- draw a basic triangle and textured triangle;
- support the texture formats and state transitions needed by the title/menu path;
- present a framebuffer with the game's VI width, scissor and scaling behavior.

Use the Android RT64 path as a reference for expected GBI/RDP behavior, not as the Wii renderer.

**Exit condition:** a controlled GX test scene renders deterministically, then a locally built game title/menu frame can be presented.

### P4 — Integrate input/audio and reach a race

- Map Wii PAD/WPAD inputs to the game's N64 controller bits.
- Connect the recompiled audio microcode output to a Wii audio backend.
- Validate saves, menu navigation, race entry, a complete lap and then a complete race.
- Record actual console model, controller, video mode, frame pacing and logs.

**Exit condition:** manual three-lap race completed on real Wii hardware, with reliable exit/restart and save persistence.

## Confirmed / probable / to verify

- **Confirmed:** dguillot's project uses static N64 recompilation, N64ModernRuntime, RT64 HLE, SDL2 and an Android app layer.
- **Confirmed:** the graphics render context uses RT64, selects Vulkan on Android and D3D12 otherwise; it does not contain a Wii GX backend.
- **Confirmed:** the pinned runtime reserves 4 GiB of virtual address space and makes 512 MiB read/write.
- **Confirmed:** the recompiler memory macros use XOR byte/halfword lane adjustments; the existing host targets are little-endian.
- **Confirmed:** graphics display lists go through RT64's HLE `loadUCodeGBI/processDisplayLists` path; the audio task uses RSPRecomp output.
- **Probable:** much of the generated C can be compiled for PPC once the memory macros, compiler features and ABI assumptions are adapted.
- **Probable:** the most economical route is a small Wii-specific runtime plus GX backend, reusing the game map and game-specific bootstrap knowledge.
- **To verify:** devkitPPC support for every intrinsic/attribute used by the generated code, including the 128-bit arithmetic helpers.
- **To verify:** the exact smallest safe RDRAM/scratch/heap allocation for Racer with the current bootstrap addresses.
- **To verify:** how much of RT64's GBI/RDP HLE state machine can be reused independently of its renderer.
- **To verify:** frame pacing and sound quality after the runtime is mapped to libogc.
- **Not tested:** building this repository for Wii, running generated C on PPC, rendering with GX, or booting a ROM on Wii hardware.

## Source index

- Main project and build/architecture description: https://github.com/dguillot-gh/star-wars-racer-recomp
- Android fixes and their diagnoses: https://github.com/dguillot-gh/star-wars-racer-recomp/blob/main/docs/ANDROID-FIXES.md
- Build/runtime integration: https://github.com/dguillot-gh/star-wars-racer-recomp/blob/main/CMakeLists.txt
- Game host, callbacks and bootstrap: https://github.com/dguillot-gh/star-wars-racer-recomp/blob/main/src/main.cpp
- RT64 HLE bridge: https://github.com/dguillot-gh/star-wars-racer-recomp/blob/main/src/rt64_render_context.cpp
- N64Recomp memory macros: https://github.com/dguillot-gh/N64Recomp/blob/racer-android/include/recomp.h
- RDRAM reservation: https://github.com/dguillot-gh/N64ModernRuntime/blob/racer-android/librecomp/include/librecomp/addresses.hpp and https://github.com/dguillot-gh/N64ModernRuntime/blob/racer-android/librecomp/src/recomp.cpp
- Runtime thread and event implementations: https://github.com/dguillot-gh/N64ModernRuntime/tree/racer-android/ultramodern/src
- RT64 Android/Racer branch: https://github.com/dguillot-gh/rt64/tree/racer-android
- Plume Android surface patch: https://github.com/dguillot-gh/plume/tree/racer-android
- Boonta's current roadmap: https://github.com/Master-Chiken/boonta-reborn-88/blob/main/docs/ROADMAP.md
