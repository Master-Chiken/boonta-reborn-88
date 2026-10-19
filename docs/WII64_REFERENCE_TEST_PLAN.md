# Wii64 on Wii — reference-game test plan

Date: 2026-10-15

## Why this matters

The supplied `wii64.zip` is the packaged Wii64 Nintendo 64 emulator intended to run N64 software on Wii (and includes variants labeled for WiiVC). For Boonta Reborn 88, this can be a useful **reference environment** for observing the original N64 racing game's behavior on the user's own setup. It is not the native GameCube/Wii build of Boonta, and the Wii64 binaries are not a replacement for the project's own engine.

Keep two tracks distinct:

- **Reference observation:** run a lawfully obtained local N64 game image in Wii64 and record behavior that can be described independently (controls, race flow, HUD layout at a high level, camera response, performance issues).
- **Boonta implementation:** implement original gameplay and procedural assets in this repository, then test the native DOL in Dolphin and, when possible, on hardware.

## Package variants in the supplied archive

The archive metadata labels four builds:

| Homebrew application path | Graphics label | Target label |
|---|---|---|
| `apps/wii64/` | glN64 GFX | Wii |
| `apps/wii64 Rice/` | Rice GFX | Wii |
| `apps/wii64_wiivc/` | glN64 GFX | WiiVC |
| `apps/wii64 Rice_wiivc/` | Rice GFX | WiiVC |

Treat these as separate test candidates. Do not assume that WiiVC-labeled builds work in every Wii U setup, or that one graphics plugin is universally more accurate. Record actual results on the target device.

## Suggested test protocol

1. **Record the environment.** Note Wii or Wii U Virtual Wii, console/video mode, Wii64 version shown in `meta.xml`, exact application variant, graphics plugin, controller type, and whether the game starts from SD or USB.
2. **Use a local game image you are legally entitled to use.** Keep commercial ROMs and disc images outside this public repository. Do not upload them to issues, pull requests, CI artifacts, or this conversation.
3. **Establish a reproducible baseline.** Use the same game region/revision and same controller for each comparison. Record any game-image identity locally; do not publish the image itself.
4. **Check basic stability.** Does the emulator launch? Does the game reach the title screen, enter a race, and remain running? Record crashes, freezes, missing graphics, and audio issues separately.
5. **Observe gameplay without extracting assets.** Record descriptive behavior: steering response, acceleration/braking, camera follow, lap/finish progression, rival behavior, and visible frame pacing. Use your own notes or original screenshots for technical observations; do not copy game textures, models, music, or other proprietary payload into Boonta.
6. **Repeat with the other graphics plugin only when useful.** Keep all other conditions constant and note the exact variant. This helps distinguish an emulator/plugin issue from a behavior that the Boonta prototype should independently reproduce.
7. **Compare against the native prototype.** Test Boonta's own DOL separately in Dolphin or on hardware. Record native build status, visible rendering, controller response, completed-lap behavior, and long-session stability as distinct results.

## Results template

Copy this table into a local test log for each run:

| Field | Result |
|---|---|
| Date/time | |
| Console and mode (Wii / Wii U Virtual Wii) | |
| Wii64 version and app path | |
| Graphics plugin (glN64 / Rice) | |
| Game region/revision (local note) | |
| Controller | |
| Emulator boot and title screen | |
| Race entry and sustained runtime | |
| Steering / acceleration / brake | |
| Camera / lap / finish behavior | |
| Graphics / audio / performance observations | |
| Repeatable steps and evidence filename | |

## Interpretation rules

- A game running successfully in Wii64 proves something about that emulator + game image + console configuration; it does not prove that Boonta's native DOL works.
- A Wii64 rendering or timing defect should not automatically be treated as the original game's intended behavior.
- N64 emulation performance is not a reliable direct benchmark for a native GameCube/Wii application.
- Only implement observations that can be described without copying protected source code or assets. Any proposed third-party code/data reuse needs a separate provenance and license review.

## Current status

This is a test plan, not a report of completed console testing. No ROM was included in or executed from the archive review, and no emulator behavior is claimed here. The next useful evidence is a short run log for each variant actually tested on the user's Wii setup.
