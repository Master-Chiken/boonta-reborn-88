# Wii64 test log template

Use one copy of this template for each test session. The aim is to distinguish a Wii64/plugin issue from an observation that should inform the independently implemented Boonta Reborn 88 prototype.

## Setup

- Date/time:
- Console: Wii / Wii U in vWii mode
- Wii64 version shown in Homebrew Channel:
- App path:
- Plugin: Rice / glN64
- Launch medium: SD / USB
- Controller:
- Game title and region/revision (local note only; do not upload the ROM):
- Video mode / display connection:

## Test sequence

| Check | Result (pass / fail / not tested) | Notes |
|---|---|---|
| Wii64 launches | | |
| Game reaches title screen | | |
| Race can be started | | |
| Stable for 5 minutes | | |
| Steering responds consistently | | |
| Acceleration and brake respond | | |
| Camera tracks the racer | | |
| HUD remains readable | | |
| Track/background rendering looks stable | | |
| Audio remains stable | | |
| Lap progression and finish are registered | | |
| Exit/relaunch works | | |

## Issue record

For every failure, record only one issue per entry.

- Short title:
- Exact steps to reproduce:
- Expected result:
- Actual result:
- Frequency: always / often / once
- Does changing Rice ↔ glN64 change the result?
- Does restarting Wii64 change the result?
- Evidence filename (keep private if it contains copyrighted game imagery):

## Comparing variants safely

1. Record the baseline first.
2. Change only one variable per run (plugin or app variant).
3. Keep console mode, controller, game revision and launch medium unchanged.
4. Do not edit multiple INI settings at once. If a setting is changed, preserve a backup and record the exact key/value.
5. Treat the result as an observation about this Wii64 build and setup—not proof of the original game's intended behavior.
6. Do not upload ROMs, save files, extracted textures/models/audio, or emulator binaries to the repository.

## Boonta Reborn 88 follow-up

Only translate a result into a prototype task if it can be described independently, for example:
- controller response feels delayed or inconsistent;
- camera loses the racer during a turn;
- lap/finish state does not progress;
- native prototype rendering or input fails in its own DOL.

Validate prototype behavior separately in host tests, Dolphin, and physical hardware when available. Wii64 performance is not a direct benchmark for a native GameCube/Wii build.

## Status

This template is for collecting future observations. Blank fields mean not tested; do not interpret them as successful results.
