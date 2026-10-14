# Boonta Reborn — GameCube / Wii research

An unofficial fan research and homebrew project exploring whether **Star Wars: Episode I — Racer (1999)** can be brought to Nintendo GameCube and Wii with improved presentation and additional features.

This repository is currently at the **research and planning stage**. There is **no verified GameCube/Wii port or working build in this repository yet**.

> Unofficial fan project. Not affiliated with or endorsed by Lucasfilm, Disney, Nintendo, or the original developers/publishers. All third-party names and trademarks belong to their respective owners.

## Goals

- Determine which existing reverse-engineering work and tools are relevant to the console versions.
- Establish a small, reproducible homebrew proof of concept before attempting a large port.
- Investigate a native GameCube/Wii implementation, improved visuals, and optional bonus features.
- Document build steps, compatibility findings, limitations, and test results honestly.

## Important distinction: emulator test vs. native port

There are two possible tracks, and they should not be confused:

1. **Quick compatibility test:** run a legally obtained N64 copy in existing Wii N64 homebrew such as Wii64/Cube64 or a compatible derivative. This may help establish a quick playable baseline, but it is emulation—not a native remaster—and compatibility/performance must be tested.
2. **Native enhanced port:** implement or adapt an engine for the GameCube/Wii hardware and understand the relevant game data formats. This is a much larger research and engineering effort. PC reverse-engineering and asset tools may be useful references, but their compatibility with console builds is not assumed.

The project will prioritize the smallest concrete test first, then choose the longer-term path based on evidence.

## Current status

| Area | Status |
|---|---|
| Public repository and initial documentation | In progress |
| Audit of the existing prototype/archive | Pending; contents and provenance not yet verified |
| Console-version technical research | In progress |
| Bootable GameCube/Wii test build | Not yet verified |
| Native gameplay port | Not started / not verified |
| HD renderer and bonus features | Future work |
| Wii WBFS build / GameCube disc image | Packaging decision pending working builds |

We will only mark a feature as working after it has been built and tested, or after the test evidence is clearly documented.

## Repository layout

- docs/PROJECT_PLAN.md — phases and acceptance criteria
- docs/TECHNICAL_RESEARCH.md — existing projects and platform constraints
- docs/BUILD_GUIDE.md — current build approach and test checklist

## What belongs here

This repository should contain original project code, documentation, scripts, build configuration, and lawful test assets only.

**Do not commit game ROMs, disc images, extracted proprietary textures/models/audio, or other copyrighted game data.** Keep local dumps and generated disc images outside Git. The .gitignore is intended to reduce accidental commits; it is not a substitute for reviewing changes before pushing.

The repository's MIT license applies only to original project material that is actually eligible for that license. Third-party code and assets retain their own licenses and terms; review those before copying, linking, modifying, or distributing them.

## Research starting points

- [Star Wars Episode I: Racer decompilation research](https://github.com/tim-tim707/SW_RACER_RE) — analysis of the Windows version; not a completed console port.
- [OpenSWE1R](https://github.com/OpenSWE1R/openswe1r) — an older open-source PC-oriented port.
- [SWE1R asset library](https://github.com/akopetsch/swe1r-assets) — tooling for specific PC game asset block formats.
- [Wii64 / Cube64](https://github.com/emukidid/Wii64) — N64 homebrew emulator project; a possible quick compatibility-test route, not a remaster.

See [Technical Research](docs/TECHNICAL_RESEARCH.md) for caveats and license notes.

## Contributions

Early help is most useful in platform research, documenting exact hardware/version behavior, reviewing licensing and provenance, and testing a minimal homebrew build. Please describe the exact console model, homebrew environment, game revision, test steps, and observed result when reporting compatibility.

## Disclaimer

This is an independent, non-commercial research project. It does not include or provide copyrighted game content. No compatibility, performance, or finished remaster is promised at this stage.

## Dreamcast track (new investigation)

The project also has a separate exploratory Sega Dreamcast track in [`dreamcast/`](dreamcast/README.md), targeting the open-source [KallistiOS SDK](https://github.com/KallistiOS/KallistiOS). A GitHub Actions workflow attempts to compile this clean-room starter and, if successful, publishes the ELF as a workflow artifact: [Dreamcast build workflow](.github/workflows/dreamcast-build.yml).

**This is only a starter, not a port of the commercial game.** The Dreamcast build has not been confirmed successful until the workflow completes and produces the artifact. Keep the Dreamcast and GameCube/Wii tracks separate. Never upload the commercial disc image or extracted proprietary assets.
