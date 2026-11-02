# RE-001 — Public N64 code-list vs participant-table cross-check

**Date:** 2026-11-02  
**Scope:** compare public community code-list annotations with a locally traced participant-table lifecycle. This public note contains no ROM bytes, raw disassembly, private absolute addresses, or extracted game data.

## Public code-list observation

TheForce.net's N64 code list publishes three Player 1/Player 2 address pairs for *Episode I Racer*:

- an **Always Place First** byte;
- a **Low Timer** halfword;
- a **Lap Modifier** halfword, with values 00–04 documented as laps 1–5.

For all three pairs, the Player 2 address is exactly **0x88 bytes** after the Player 1 address. The same page separately lists a conditional “Start on Lap” modifier using the lap field. Ethereal Games reproduces the lap and placement/timer entries and the same player spacing.

## Participant-table lifecycle now traced locally

The local static trace now connects the active manager table back to race setup:

1. The race-setup path invokes a participant-table builder.
2. That builder prepares the participant records with a fixed **0x88-byte stride** and returns the table pointer.
3. The setup path places that pointer in the Begn message payload sent to the race manager.
4. The manager's Begn receiver forwards the payload pointer through its initialization path.
5. The manager initializer stores that same pointer as its active participant-table pointer and iterates the records with the same **0x88-byte stride**.

This proves the provenance of the manager's active roster pointer and links the setup-built records to the live manager iteration. The exact private pointer value is deliberately omitted from this public note.

## Critical correction: stride is not identity

The public code-list Player 1/Player 2 addresses are **not directly the same base region** as the manager table whose pointer was traced above. Therefore, the shared 0x88 spacing is corroboration of a repeated record size, but it does **not** prove that those GameShark codes address fields in the manager's active participant table.

Accordingly, the earlier candidate assignments of the public “Lap Modifier” and “Low Timer” fields to the manager record's event counter and progress-like accumulator are **withdrawn as a direct mapping**. They remain possible leads for a different player/runtime object, but no direct pointer or field cross-reference has been found.

The public “Always Place First” target also remains **UNMAPPED**. A separate rank-query path must not be conflated with the manager's event-history region.

## What is supported vs unresolved

**Supported:**
- the public Player 1/Player 2 code pairs use a consistent 0x88-byte separation;
- the manager's active participant table is built during race setup, passed through the Begn payload, and consumed with a 0x88-byte stride;
- the manager table lifecycle is now connected end-to-end at the static control/data-flow level.

**Not established:**
- whether the public code-list addresses target the same runtime object family or a separate player structure;
- the internal semantic field targeted by “Low Timer”;
- the internal target for “Always Place First”;
- whether the public lap-modifier value is the value read by the visible HUD;
- the code path that formats/draws “FINAL LAP”;
- the runtime-visible Results transition.

## Next bounded action

Trace the entity/object pointers held by each manager participant record to determine whether they reference the separate player-state region represented by the public code-list addresses. If the static pointer chain cannot establish that relation, use a lawful local emulator memory watch on a private copy and record the exact emulator/version and race scenario. Keep all ROM-derived addresses/data local.

## Public sources

- [TheForce.net — Episode I Racer N64 codes](https://www.theforce.net/videogames/codes/n64/racer.asp)
- [Ethereal Games — Episode I Racer GameShark Codes (US)](https://etherealgames.com/n64/s/star-wars-episode-i-racer/gameshark-codes-us/)
