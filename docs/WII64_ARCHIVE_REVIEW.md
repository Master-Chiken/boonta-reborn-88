# Wii64 archive review — relevance to Boonta Reborn 88

Date: 2026-10-15

## Executive summary

The supplied `wii64.zip` is useful as a reference for homebrew packaging and configuration review, but it is **not a drop-in codebase or rendering backend for Boonta Reborn 88**. The archive describes Wii64, a port of the Mupen64 0.5.1 Nintendo 64 emulator to Wii/GameCube. Boonta Reborn 88 is an original native GameCube/Wii racing prototype, so emulator-specific code and binaries should not be copied into the clean-room demo.

## Archive inventory observed

Archive SHA-256 recorded during the initial inspection:

```text
cf935283854f69210b52ce668b6aa78551ab6c1086e6b25be2290b0c8077d154
```

The archive contains four Homebrew Channel application variants, each with a `boot.dol` and `meta.xml`:

| Archive path | Metadata description | Distinction |
|---|---|---|
| `apps/wii64/boot.dol` | Wii64 | glN64 GFX | glN64 graphics plugin |
| `apps/wii64 Rice/boot.dol` | Wii64 | Rice GFX | Rice graphics plugin |
| `apps/wii64_wiivc/boot.dol` | Wii64 | glN64 GFX | WiiVC | Wii U Virtual Wii / WiiVC-targeted variant |
| `apps/wii64 Rice_wiivc/boot.dol` | Wii64 | Rice GFX | WiiVC | WiiVC-targeted variant with Rice graphics plugin |

The metadata identifies version `1.5.0` and includes release string `202609231942`. The archive also includes `wii64/RiceVideoLinux.ini` (1,364 lines; per-game Rice video settings), `wii64/boxart.bin`, icons, metadata, and macOS `__MACOSX` entries. It is primarily a binary/configuration package, not a complete source checkout.

## What is relevant to this repository

1. **Keep target variants explicit.** Wii64 packages distinguish graphics backend and WiiVC target in the application path and Homebrew Channel metadata. If Boonta later ships separate GameCube, Wii, or emulator-specific builds, encode the target in build outputs and metadata rather than silently mixing artifacts.
2. **Validate the final artifact, not just compilation.** This repository already has DOL/ELF structural checks and Dolphin smoke/render checks. Continue treating compilation, artifact structure, emulator process startup, visible rendering, interactive controller input, and a completed race as separate acceptance gates.
3. **Treat configuration as data with provenance.** The Rice INI demonstrates per-title configuration at scale, but its values are specific to N64 emulation and should not be transplanted into the racing prototype. Any Boonta course or handling configuration should have documented units, defaults, validation, and tests.
4. **Keep packaging clean.** Exclude `__MACOSX/`, `.DS_Store`, temporary build outputs, and unrelated emulator binaries from Boonta releases unless there is a clearly documented reason to include them.

## What should not be reused without separate review

- The four `boot.dol` files are compiled emulator binaries; they are not Boonta gameplay code and should not be linked into the clean-room demo.
- The Rice video settings are emulator/game-specific and do not configure GameCube GX rendering for this project.
- Do not copy Wii64 source, logos, icons, or other assets into this repository merely because they appear in the archive. Check the upstream source license and any separate trademark/asset restrictions first.
- The archive alone does not establish the source provenance or redistribution rights of every included file.

Upstream project reference from the archive metadata: https://github.com/emukidid/Wii64

## Recommended follow-up

- Keep the archive outside the public repository; this document records observations without redistributing its binaries.
- If a specific Wii64 behavior is proposed for reuse, identify the exact upstream source file and license first, then evaluate whether it solves a demonstrated Boonta requirement.
- For the current milestone, prioritize validating live controller response and a completed three-lap run in Dolphin or on hardware. Wii64 itself does not remove that acceptance gap.

## Verification limits

This is an inventory and relevance review based on the supplied ZIP and its metadata. The binaries were not executed as part of this review, and this document does not claim that any Wii64 variant works on a specific console or that its contents are safe to redistribute.
