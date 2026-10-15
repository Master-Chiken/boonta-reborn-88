# Wii64 profile note: Star Wars Episode I Racer

Date: 2026-10-15

## Finding

The supplied `wii64.zip` includes a Rice video-plugin profile explicitly named **STAR WARS EP1 RACER** in `wii64/RiceVideoLinux.ini`.

The exact record is:

```ini
{9803f7728ba95665-45}
Name=STAR WARS EP1 RACER
ZHack
VIWidth=320
VIHeight=480
```

This is a concrete, title-specific configuration record worth preserving as a test lead. It does **not** by itself explain the implementation or prove that these settings are optimal on every console.

## Encoding and file shape

- The INI is approximately 24.8 KB and contains 242 title sections in the supplied archive.
- The file is encoded in Windows Japanese code page 932 / Shift-JIS-compatible encoding; decoding it as UTF-8 produces mojibake in some `Name=` values.
- Each section starts with an identifier in braces and has a human-readable `Name=` entry, followed by optional key/value settings or standalone flags.
- This matters for future tooling: parse the file with an explicitly selected encoding and preserve unknown keys and flags rather than silently dropping them.

Archive SHA-256 recorded during inspection:

```text
cf935283854f69210b52ce668b6aa78551ab6c1086e6b25be2290b0c8077d154
```

## Comparison with other racing titles in the same file

The following are literal settings from the same archive, included only to show that Rice profiles are title-specific:

```ini
{b655503e52da922e-45}
Name=Mario Kart 64
AccurateTextureMapping=1
FastTextureCRC=1
NormalAlphaBlender=1
NormalColorCombiner=1
```

```ini
{d7d81095d20d1035-45}
Name=Stunt Racer 64
AccurateTextureMapping=1
FastTextureCRC=2
NormalAlphaBlender=2
NormalColorCombiner=1
FullTMEM=1
ForceScreenClear=1
ForceDepthBuffer=1
ScreenUpdateSetting=2
```

```ini
{7e260025cec37e2a-45}
Name=RIDGE RACER 64
```

Do not infer that settings from Mario Kart 64 or Stunt Racer 64 should be copied into the Star Wars Episode I Racer profile. The records differ, and this INI belongs to the **Rice N64 emulation plugin**, not to native GameCube GX rendering.

## Practical test plan for the user's Wii

1. Identify which executable is actually launched: `apps/wii64 Rice/boot.dol` or `apps/wii64/boot.dol`, versus either `*_wiivc` variant. The archive's metadata distinguishes Rice/glN64 and WiiVC builds.
2. Keep console mode, game region/revision, controller, and storage medium unchanged while comparing plugins.
3. Record the game reaching the title screen, entering a race, visible track geometry, sky/background, HUD, audio, frame pacing, and whether the emulator hangs or crashes.
4. If testing a setting change, change one setting at a time and preserve the original INI so the result can be reversed.
5. Do not assume the `ZHack` flag's exact effect from its name alone. Confirm its meaning in the matching Wii64/Rice source revision before describing or modifying it.
6. Keep commercial ROMs, save data, and extracted proprietary assets outside the public repository.

Suggested local result fields:

| Test field | Value |
|---|---|
| Wii / Wii U Virtual Wii | |
| Executable path / metadata title | |
| Plugin (Rice / glN64) | |
| Game region/revision | |
| Video mode and display ratio | |
| Title screen and race start | |
| Track/background/HUD observations | |
| Audio and frame pacing | |
| Reproducible issue and steps | |

## Relevance to Boonta Reborn 88

This record is useful as **reference-environment evidence** because the project is inspired by Star Wars Episode I – Racer. It can guide repeatable observations of the original game's behavior on the user's own Wii. It is not native renderer configuration and does not establish gameplay physics, timing, or intended visuals on its own.

For Boonta's clean-room GameCube/Wii prototype, implement independently authored behavior and validate it through the native DOL, host tests, Dolphin rendering/input checks, and eventually hardware. Do not import the emulator binary or proprietary game content.

## Sources and limits

- Supplied `wii64.zip` archive and `wii64/RiceVideoLinux.ini`.
- Wii64 upstream README: https://github.com/emukidid/Wii64/blob/master/README.md — describes the separate Rice and glN64 graphics plugins, and states that Wii64 is GPL-2.0 while its project name/logos are trademarks.
- The profile was read from the archive; this note does not claim that either plugin or this specific profile has been tested on physical hardware.
