# RE-001 — Public lap/placement memory-code structure cross-check

**Date:** 2026-11-02  
**Scope:** public community code-list comparison against private, local static analysis. This note contains no ROM bytes, no disassembly, no private absolute addresses, and no extracted game data.

## New corroboration

TheForce.net's N64 code list publishes three Player 1/Player 2 address pairs for *Episode I Racer*:

- an **Always Place First** byte;
- a **Low Timer** halfword;
- a **Lap Modifier** halfword, with values 00–04 documented as laps 1–5.

For all three pairs, the Player 2 address is exactly **0x88 bytes** after the Player 1 address. The same page separately lists a conditional “Start on Lap” modifier using the lap field. Ethereal Games reproduces the lap and placement/timer entries and the same player spacing.

This is useful because the local static participant iteration independently uses a fixed **0x88-byte record stride**. Private analysis also identified distinct per-participant ranking, progress-like, and route-event-count fields whose relative layout is consistent with the three public code families. This makes the hypothesis that the community codes target fields within the same participant-record array materially stronger than a simple one-field coincidence.

## What this does and does not establish

**Supported:** the external player-pair spacing matches the participant-record stride; multiple independent field roles align with the locally observed record layout.

**Not established:** the absolute runtime base of the record array; a direct pointer equality between either community address and the live roster; whether the community “Low Timer” label accurately names the field's internal semantic; whether the lap modifier is the value read by the visible HUD; or the code path that formats/draws “FINAL LAP”.

The community code list is secondary documentation, not a substitute for a pointer trace or runtime watch. The absolute-base mapping therefore remains **CANDIDATE / NOT PROVEN**.

## Next bounded action

Trace the participant-array pointer from its Begn setup payload to the live roster allocation/initialization, looking for a direct connection to the public code-list address family. If that static path cannot establish the base, use a lawful local emulator memory watch on a private copy and record the exact emulator/version and race scenario. Keep ROM and all ROM-derived absolute addresses local.

## Public sources

- [TheForce.net — Episode I Racer N64 codes](https://www.theforce.net/videogames/codes/n64/racer.asp)
- [Ethereal Games — Episode I Racer GameShark Codes (US)](https://etherealgames.com/n64/s/star-wars-episode-i-racer/gameshark-codes-us/)
