# RE-001 — Public lap/placement memory-code structure cross-check

**Date:** 2026-11-02  
**Scope:** public community code-list comparison against private, local static analysis. This note contains no ROM bytes, no disassembly, no private absolute addresses, and no extracted game data.

## New corroboration

TheForce.net's N64 code list publishes three Player 1/Player 2 address pairs for *Episode I Racer*:

- an **Always Place First** byte;
- a **Low Timer** halfword;
- a **Lap Modifier** halfword, with values 00–04 documented as laps 1–5.

For all three pairs, the Player 2 address is exactly **0x88 bytes** after the Player 1 address. The same page separately lists a conditional “Start on Lap” modifier using the lap field. Ethereal Games reproduces the lap and placement/timer entries and the same player spacing.

This is useful because local static analysis independently finds a participant-record array with a fixed **0x88-byte stride**. The lap-modifier location and the “Low Timer” location are consistent with, respectively, the participant's route-event counter and a progress-like accumulated float under one candidate record-base interpretation. This is a meaningful multi-field corroboration, but it is still not a direct pointer match.

## Field-role caution

The local participant record also contains a per-event history area. A separate rank query reads a halfword at a similar relative location in an associated object, but that does **not** establish that the public “Always Place First” code targets a rank field in the progress-manager record. That placement-code target remains **UNMAPPED**. The community label “Low Timer” is also not assumed to be the internal semantic name of the float it may overlap.

## What this does and does not establish

**Supported:** all three external P1/P2 address pairs share the same 0x88 spacing as the locally observed participant-record stride; two of the code locations are consistent with the relative positions of the privately observed progress-like value and event counter.

**Not established:** the absolute runtime base of the record array; direct pointer equality between either community address and the live roster; whether the “Low Timer” label accurately names the internal field; the target field for “Always Place First”; whether the lap-modifier value is the value read by the visible HUD; or the code path that formats/draws “FINAL LAP”.

The community code list is secondary documentation, not a substitute for a pointer trace or runtime watch. The absolute-base mapping therefore remains **CANDIDATE / NOT PROVEN**.

## Next bounded action

Trace the participant-array pointer from its Begn setup payload to the live roster allocation/initialization, looking for a direct connection to the public code-list address family. If that static path cannot establish the base, use a lawful local emulator memory watch on a private copy and record the exact emulator/version and race scenario. Keep ROM and all ROM-derived absolute addresses local.

## Public sources

- [TheForce.net — Episode I Racer N64 codes](https://www.theforce.net/videogames/codes/n64/racer.asp)
- [Ethereal Games — Episode I Racer GameShark Codes (US)](https://etherealgames.com/n64/s/star-wars-episode-i-racer/gameshark-codes-us/)
