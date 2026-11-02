# RE-001 — Public N64 memory-code fields mapped to active participant records

**Date:** 2026-11-02  
**Scope:** cross-check public community GameShark annotations against local static control/data-flow analysis. This public note omits the ROM-derived absolute table base, private field offsets, raw disassembly, ROM bytes and extracted game data.

## Result — direct field mapping restored

The earlier note incorrectly concluded that the public code-list region did not match the manager's live participant table. A re-check of the setup initializer's table base and its row initialization showed that conclusion was wrong.

The public Player 1 code targets fall inside the first record of the very same participant table built during race setup and passed through the Begn message to the race manager. The Player 2 targets fall inside the next record at the same field positions, exactly one 0x88-byte participant stride later.

The exact cross-check now links the three independently listed public code targets to three distinct fields used by the local static control flow:

1. **Always Place First** — the public byte write falls within the participant placement/rank halfword. The manager's ranking/placement helper reads and compares this record field while deriving placement order. The public code's value of one is consistent with first place.
2. **Low Timer** — the public halfword write falls on the floating-point progress accumulator used by the manager's participant update. The local update path adds route-progress deltas to this scalar. The community label “Low Timer” is retained as the published code name; the internal variable's exact intended semantic is not renamed from that label alone.
3. **Lap Modifier / Always on Lap** — the public halfword write falls on the lower half of the participant's route-event counter. The local update path increments that counter only when the route-progress event helper reports an event, then compares the new count against the manager's configured threshold. The public list documents values 00–04 as laps 1–5, consistent with a zero-based counter interpretation.

The manager table initializer independently clears the placement field, progress accumulator and event counter for each row, and advances by the same 0x88-byte stride. This is the decisive bridge: the public address pairs are not merely two values with a coincidental stride; they land in the same active record layout and match the corresponding fields consumed by manager code.

## What is supported vs still open

**High-confidence static mapping:**
- Player 1 public codes target the first live manager participant record.
- Player 2 equivalents target the next manager participant record at the same field offsets, separated by 0x88 bytes.
- Placement/rank helper reads the field targeted by “Always Place First”.
- Participant progress update reads/writes the float targeted by “Low Timer”.
- Route-event update increments the counter targeted by “Lap Modifier” and compares it with the configured manager threshold.

**Still not established:**
- the exact semantic meaning of the floating-point accumulator beyond its observed route-progress/event-delta use;
- whether the public “Lap Modifier” codes expose the same value as the visible HUD lap number at every stage (the static HUD adds one for display, but runtime boundary values still need observation);
- runtime appearance/timing of the lap HUD and FINAL LAP banner under the presentation guards;
- runtime behavior of the Results transition and the physical Wii/Not64 controller path.

## Next bounded action

The separate static HUD trace is now documented in Section BU of the route/spline dossier: it follows the participant counter into the one-based current/total lap formatter, the guarded FINAL LAP resource, the text queue and the frame-cycle glyph renderer. The remaining discriminator is a normal runtime race that records the lap fraction and final-lap banner, followed separately by the Results-screen test. Keep the ROM, absolute table base, private field offsets and all extracted data local.

## Public sources

- [TheForce.net — Episode I Racer N64 codes](https://theforce.net/videogames/codes/n64/racer.asp)
- [Ethereal Games — Episode I Racer GameShark Codes (US)](https://etherealgames.com/n64/s/star-wars-episode-i-racer/gameshark-codes-us/)


## Follow-up reference — current HUD trace

The current/total lap fraction and guarded FINAL LAP branch are no longer open static questions. See [RE-001 route/spline dossier Section BU](https://github.com/Master-Chiken/boonta-reborn-88/blob/docs/reverse-engineering-80-20-20261020/docs/research/RE-001-route-spline-progress.md) for the independently re-traced participant → formatter → text queue → frame-cycle drain → glyph-renderer chain. Runtime appearance and timing remain **NOT TESTED**.
