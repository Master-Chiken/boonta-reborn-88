# sp00nznet/racer — system-level transfer plan for GameCube/Wii

**Reviewed:** 2026-11-08  
**Reference snapshot:** [sp00nznet/racer at 694c5663b3a7c30e2862fc240344f34683f99a9c](https://github.com/sp00nznet/racer/tree/694c5663b3a7c30e2862fc240344f34683f99a9c)  
**Boonta target:** native GameCube/Wii PowerPC Gekko/Broadway + GX/libogc.

This note extracts implementation requirements from the N64 static-recomp project's public README, changelog and frontend. It is a behaviour/architecture transfer plan, **not an approval to copy the SDL/RT64/Ultramodern source into the Boonta console executable**.

## Current Boonta baseline

The clean-room prototype README currently reports:
- native GX startup and a visible, scrolling procedural course;
- original source-authored racer mesh and RGB565 texture upload;
- controller-driven steering, throttle, brake, pitch and slide;
- three scripted rival craft with simple collisions and overtakes;
- a three-lap race clock/HUD, boost/heat and pause toggle;
- automated host tests and a native DOL/ELF build.

The same README explicitly says audio, saves, a title menu and a full physics model are not implemented. The current input backend polls only GameCube PAD channel 0 or Wii WPAD Classic channel 0. It has good neutral-on-disconnect and Classic-probe logic, but not a multi-player device-assignment layer.

## Transfer matrix

| Upstream N64 feature/evidence | General lesson worth retaining | GameCube/Wii adaptation | Do not copy |
|---|---|---|---|
| Full boot -> title -> player/vehicle selection -> tournament/shop -> race -> pause/results/reload flow (upstream README v0.1.0 status) | Treat the game as a set of explicit screens and race lifecycle transitions, not one monolithic gameplay loop | Build a native GX screen/state controller; define menu, garage, tournament, race, pause, results and reload transitions with host-testable state functions | Generated N64 game functions, N64 event-manager internals, SDL launcher or ImGui/RT64 overlay |
| Controller support for two players, hot-plug/drop-out, keyboard and rebinding (upstream README/changelog) | Separate physical-device discovery from logical player assignment; preserve a neutral input state on disconnect; make bindings configurable | Extend the existing Boonta PAD/WPAD backend only when the player/camera model is ready. GameCube has four controller ports; Wii Classic is a distinct expansion type. Add per-port snapshots and explicit assignment without leaking libogc details into gameplay | SDL game-controller API, keyboard backend, N64 controller SI/PIF structures, direct copy of SDL configuration |
| Audio microcode plus volume setting; upstream changelog says a sound-queue backlog caused a mid-race freeze and was fixed | Audio queues must be bounded; producer/consumer rates must be explicit; handle full/empty queues and shutdown while audio is active | Select and test a native GameCube/Wii audio path (libogc/AESND or another approved library). Design a bounded PCM/sample ring with overrun/underrun counters, volume control and a deterministic shutdown contract before importing any audio assets | N64 RSP microcode, RSPRecomp output, AI registers/callbacks or the N64 audio ABI |
| Deterministic 2-player lockstep netplay over UDP (upstream frontend netplay source) | Snapshot local input once per simulation frame; assign a frame/retrace number; buffer remote input; use a small configurable input delay; resend recent frames; compare periodic state hashes; keep shared save state separate | First finish local controller abstraction and a repeatable single-player simulation. If network play is later required, design a platform-neutral input-frame protocol and tests independently; local split-screen is the nearer milestone | Upstream socket/thread implementation, Windows/Unix networking shims, N64 RDRAM hash assumptions, UDP packet structs or ultramodern scheduler callbacks |
| RT64 desktop rendering, texture packs and a launcher/menu overlay (upstream frontend UI and renderer context) | Keep UI state separate from world state; avoid rendering-thread/main-thread races; load optional content through a validated manifest | Render native GX menus/HUD on the console's render thread; keep menus independent of race simulation; continue using Boonta's source-authored mesh/texture pipeline until asset formats are independently understood | RT64, Vulkan, DirectX, Metal, desktop overlay hooks, renderer texture-pack directory format |
| Configuration file with graphics/audio/input settings and per-player device policies (upstream frontend config model) | Centralize defaults, validation, migration and per-player settings; persist only validated options | Use a small native config schema for input mappings, audio levels, video preference and gameplay options. Keep platform/console settings separate from game progression saves | Host JSON paths, desktop window resolution/AA options, RT64 renderer values and game-derived setting names |
| Shared save sent to the netplay peer before a session (upstream netplay source) | Deterministic multiplayer needs identical progression/unlock state; session sync must not overwrite the user's normal save silently | Decide an explicit GameCube/Wii persistence layer and versioned save schema; keep test fixtures synthetic and migration paths covered | N64 EEPROM implementation, host netplay save folder, ROM-specific save IDs |
| Shutdown crash fixed because game threads outlived the runtime (upstream changelog v0.2.0) | Stop producers, join workers, then release audio/graphics/game state; teardown order is testable | Apply to any future Boonta audio, loading or controller worker. No asynchronous worker should outlive GX/audio/heap state | ultramodern thread/event APIs or the upstream desktop window lifecycle |

## Suggested order for reducing future implementation work

1. **Finish the core race before adding host features.** Use the upstream feature list as a completeness checklist: title/selection, race lifecycle, pause/results/retry, audio, saves, device hot-plug, multiple players.
2. **Make the native audio contract first.** Add an audio abstraction with bounded queue semantics and tests for full queue, empty queue, underrun, overrun, volume and shutdown. Only then choose/import a concrete native library after license and libogc/Wii compatibility checks.
3. **Generalize input snapshots.** Preserve the existing logical button map and calibrated Classic axis conversion. Add a per-port read API and a tested player-assignment state machine; do not expose PAD/WPAD structs to gameplay.
4. **Create a clean menu/lifecycle state module.** Keep GX drawing separate from transitions. Pause must freeze simulation while UI navigation continues. Results and restart should be deterministic and resettable.
5. **Add local multiplayer only after one player is stable.** Start with two local input slots and split-screen cameras. Network lockstep is a later host feature and is not needed to prove the console core.
6. **Add saves only with an explicit persistence target.** Treat progression data as versioned state and test corruption/migration/recovery with synthetic save images.

## Concrete Boonta files to start from

- [GameCube/Wii prototype README](../../gamecube-demo/README.md) — actual implemented/missing feature baseline.
- [Native main loop and GX renderer](../../gamecube-demo/source/main.c) — world/render integration; currently one player.
- [Input adapter](../../gamecube-demo/source/input_backend.c) and [logical input contract](../../gamecube-demo/source/input_backend.h) — PAD/WPAD isolation and current Classic connection state.
- [Gameplay state](../../gamecube-demo/source/gameplay_state.h) — deterministic host-testable simulation transitions.
- [Native build](../../gamecube-demo/Makefile) — libogc/devkitPPC target, distinct from upstream desktop CMake.

## Upstream evidence

- [Pinned README / features and status](https://github.com/sp00nznet/racer/blob/694c5663b3a7c30e2862fc240344f34683f99a9c/README.md)
- [Pinned changelog / audio queue and shutdown issues](https://github.com/sp00nznet/racer/blob/694c5663b3a7c30e2862fc240344f34683f99a9c/CHANGELOG.md)
- [Input and controller assignments](https://github.com/sp00nznet/racer/blob/694c5663b3a7c30e2862fc240344f34683f99a9c/frontend/src/input.cpp)
- [Player device/config model](https://github.com/sp00nznet/racer/blob/694c5663b3a7c30e2862fc240344f34683f99a9c/frontend/src/config.hpp)
- [Audio callback/buffering](https://github.com/sp00nznet/racer/blob/694c5663b3a7c30e2862fc240344f34683f99a9c/frontend/src/audio.cpp)
- [Deterministic lockstep netplay](https://github.com/sp00nznet/racer/blob/694c5663b3a7c30e2862fc240344f34683f99a9c/frontend/src/netplay.cpp)
- [Menu and renderer integration](https://github.com/sp00nznet/racer/blob/694c5663b3a7c30e2862fc240344f34683f99a9c/frontend/src/ui.cpp)

**Disposition:** design/behaviour lessons retained; no N64 runtime/frontend code copied. Native GameCube/Wii implementations remain to be built and tested independently.
