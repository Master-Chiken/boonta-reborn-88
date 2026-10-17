# Boonta Reborn 88

### A future native GameCube/Wii remaster of Star Wars: Episode I – Racer (1999) — an HD++ vision with an HD+++ Premium stretch goal.

[![GameCube demo CI](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-demo-build.yml/badge.svg?branch=main)](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-demo-build.yml)

**Boonta Reborn 88 aims to become a fan-made remaster of _Star Wars: Episode I – Racer_ (1999) for Nintendo GameCube and Wii.** The original 1999 release did not receive a dedicated native edition for either console; this project is building a new homebrew experience for those systems, not claiming that an existing GameCube/Wii port already exists. The immediate goal is one reliable, enjoyable racing experience; the larger goal is a substantial visual, gameplay, and content upgrade.

## The ambition: HD++ first, HD+++ Premium as a stretch goal

- **HD++ Remaster — the primary vision:** a more polished presentation, more detailed original or rights-cleared pod and track assets, clearer scenery, improved effects and UI, better racing feel, new circuits and pods, richer audio, and bonus challenges or modes as the playable foundation grows.
- **HD+++ Premium — the aspirational tier:** push presentation and content as far as the chosen platforms, performance budget, development time, and rights allow. The long-range wish list includes a broader track and pod roster, more elaborate environments and effects, expanded progression, special events, bonus modes, and DLC-style content packs.
- **The ideal wider dream:** if it proves technically and practically feasible, grow beyond an _Episode I – Racer_-focused remaster toward a broader remake-style experience inspired by the wider _Star Wars Racer_ legacy. This is a long-term ambition, not a promise that other commercial games or their assets will be reproduced.

**Hardware reality:** “HD++” and “HD+++ Premium” describe the quality, detail, presentation, and breadth we aspire to—not a promise of true HD video output from GameCube or Wii. Native builds must respect their original hardware and video-output limits. A genuine HD-resolution Premium edition would require a separate, more capable platform target and remains an optional future possibility, not a current commitment.

The player-pod mesh/texture, varied canyon skyline, and readable finish banner are integrated on `main` ([PR #202](https://github.com/Master-Chiken/boonta-reborn-88/pull/202), [PR #203](https://github.com/Master-Chiken/boonta-reborn-88/pull/203), [PR #204](https://github.com/Master-Chiken/boonta-reborn-88/pull/204)). The linked Dolphin captures are scripted diagnostics, not proof of manual-controller acceptance.

We're building it in public—and this is a great moment to join. Whether you enjoy low-level C, 3D art, gameplay feel, test automation, or technical research, **you can make a visible difference**. Contributors with experience in the original game, its modding scene, file formats, asset pipelines, or console development are particularly welcome; describe your experience and the workflow you can contribute to.

[Project roadmap](docs/ROADMAP.md) · [Current playable milestone](https://github.com/Master-Chiken/boonta-reborn-88/issues/126) · [Build & test guide](docs/BUILD_GUIDE.md) · [Join the community](https://discord.com/servers/star-wars-episode-i-racer-441839750555369474)

---

## What we're building

The current GameCube development build lives in `gamecube-demo/`. It is an early racing foundation: a native GX scene, procedural course and rivals, and an original player mesh/texture path. The intended end product is much more ambitious than this prototype; full remaster visuals, broad game-asset compatibility, and a complete manually verified race are not finished yet.

### What's already here

- **A native GameCube build** using devkitPPC/libogc, producing a DOL and ELF.
- **A visible 3D racing scene** with a scrolling desert course, road markings, a varied canyon skyline, and an original low-poly twin-engine player craft with a source-authored RGB565 texture; the course, rivals and exhaust remain procedural.
- **Prototype racing systems** for steering inertia, throttle/brake, boost and heat, pitch/slide, off-road drag, rail recovery, rival interactions, lap timing, pause and reset.
- **Automated regression coverage** for gameplay state, input mapping, race/lap logic, and edge cases.
- **Dolphin diagnostics** that build and validate the native artifacts and have exercised scripted steering, reset, pause/resume, and finish-state checks.

These are meaningful foundations, but they are **not yet proof of a fully playable game**. In particular, the team still needs a visible, manual controller session that completes a three-lap race, finishes cleanly, resets, and starts another run. Sustained frame pacing and physical GameCube/Wii compatibility also need their own evidence.

See [the current acceptance checklist](docs/NEXT_MILESTONE.md) for the exact state and what still needs testing.

## The next big wins

We keep the work focused on a playable vertical slice rather than spreading effort across unfinished systems.

1. **Prove the race is playable.** In visible Dolphin, verify steering, acceleration/braking, boost and overheating, off-road/rail response, pause/resume, three-lap finish, reset and restart. Record the emulator version, controller setup, results, and any evidence. Start with [issue #126](https://github.com/Master-Chiken/boonta-reborn-88/issues/126).
2. **Make the course and racer feel convincing.** Improve the track silhouette, camera, handling, and collision response as one coherent experience.
3. **Build the remaster asset pipeline.** Extend the existing mesh/texture path toward richer models, textures, track data, and collision. Experience with the original game's modding scene, file formats, asset workflows, or reverse-engineering research is especially welcome. Follow [issue #181](https://github.com/Master-Chiken/boonta-reborn-88/issues/181).

Once the first race is reliable, development can move toward the HD++ remaster vision: upgraded presentation within the target hardware budget, more tracks and pods, expanded menus, audio, saves, progression, bonus modes, and DLC-style content packs. HD+++ Premium is the stretch goal for taking quality and content further; a wider Star Wars Racer-style remake remains the ideal long-range dream. These are future ambitions, not claims about the current prototype. See the [product priorities](https://github.com/Master-Chiken/boonta-reborn-88/issues/156) and [roadmap](docs/ROADMAP.md).

## Come build this with us

**You don't need to know everything or arrive with a huge feature.** Curiosity, clear communication, and the willingness to test an idea are valuable here. A useful bug report, a small fix, a model, a tool, or one careful test session can move the game forward.

| If you enjoy… | You could help with… |
| --- | --- |
| Playing and testing | Run the prototype in a visible Dolphin session, test the controls and full race, and report what works or breaks. |
| C and gameplay | Improve steering feel, race-state transitions, collisions, lap timing, or reset/restart behavior—with regression tests. |
| Graphics and 3D | Improve the GX scene, camera, course readability, or the validated mesh/texture path. |
| Python and tooling | Strengthen format validators, synthetic fixtures, artifact checks, and reproducible diagnostics. |
| Original-game modding and asset research | Investigate documented formats, modding workflows, compatibility, and model/texture conversion paths; share reproducible research. |
| Research and documentation | Document observed behavior, clarify formats, improve setup instructions, or help maintain the test checklist. |
| GameCube/Wii hardware | Reproduce the same checks on real hardware and clearly record the hardware, video mode, controls, and results. |

### Good places to start

- **Best first contribution:** follow the manual test plan in [issue #126](https://github.com/Master-Chiken/boonta-reborn-88/issues/126). Mark each check **PASS / FAIL / NOT TESTED**; include the Dolphin version, video backend, controller profile, and screenshots or a short video where useful.
- **Interested in rendering or asset formats?** Read [issue #181](https://github.com/Master-Chiken/boonta-reborn-88/issues/181) first so new work builds on the existing mesh and test foundations instead of duplicating them.
- **Not sure where to begin?** Open an issue or join the [Discord community](https://discord.com/servers/star-wars-episode-i-racer-441839750555369474). Explain what you would like to try and what environment you have. Small, focused experiments and well-documented findings are welcome.

### Why join now?

The foundations are real, but the most important part is still ahead: making the whole race feel right from the first launch to the finish line. Your work can have a visible impact—whether that means improving handling, shaping the world, strengthening a tool, or finding a bug no automated test has caught.

The longer-term vision reaches beyond a technical demo: an original, polished racing experience, with room for new circuits, distinctive pods, smarter rivals, sound, and bonus modes. I'm also working on other projects, and I'm interested in meeting creative, dependable collaborators who enjoy building things together. Start with one small contribution; the best partnerships can grow from there.

## Build and run the prototype

To build the current GameCube prototype, install the official [devkitPro GameCube/Wii toolchain](https://devkitpro.org/) with devkitPPC and libogc, open its configured shell, then run:

```sh
git clone https://github.com/Master-Chiken/boonta-reborn-88.git
cd boonta-reborn-88/gamecube-demo
make clean
make
```

The expected outputs are `boonta_gc_demo.dol` and `boonta_gc_demo.elf`.

You can run many host-side checks without a GameCube or Wii toolchain. From the repository root:

```sh
cc -std=c99 -Wall -Wextra -Werror -pedantic \
  gamecube-demo/tests/test_gameplay_state.c -lm -o /tmp/test_gameplay_state
/tmp/test_gameplay_state

cc -std=c99 -Wall -Wextra -Werror -pedantic \
  gamecube-demo/tests/test_pause_state.c -o /tmp/test_pause_state
/tmp/test_pause_state

python3 -m unittest discover -s gamecube-demo/tools -p 'test_*.py' -v
```

For artifact validation, Dolphin diagnostics, troubleshooting, and the full validation boundaries, use the [build guide](docs/BUILD_GUIDE.md) and [prototype instructions](gamecube-demo/README.md). A successful build or headless smoke test is not the same as a manually completed race.

## Copyright Disclaimer

The original game (Star Wars Episode 1 Racer) is a property of the LucasArts Entertainment Company LLC.

Boonta Reborn 88 is an unofficial fan project and is not affiliated with or endorsed by the original rights holders.

## About

Research and homebrew development toward a future native GameCube/Wii remaster of _Star Wars: Episode I – Racer_ (1999), with improved presentation, refined racing, new circuits and pods, bonus modes, and future DLC-style expansions.

**Primary ambition — HD++ Remaster:** raise visual clarity, asset detail, atmosphere, and overall polish as far as native GameCube/Wii hardware permits, then build out more racing content.

**Stretch ambition — HD+++ Premium:** pursue a richer premium-quality presentation and broader content offering if technical feasibility, time, contributors, and rights allow it. A true HD-resolution build would require a separate, more capable platform target.

**Ideal long-range dream:** explore a broader remake-style _Star Wars Racer_ experience, if a realistic and rights-compatible scope can be established.

These are aspirations, not claims that the full remaster, bonus modes, new content, or Premium tier are already implemented. “HD++” and “HD+++ Premium” describe project ambition and do not imply native 720p/1080p output from GameCube/Wii. Current status and the next playable milestone are documented above and in the [roadmap](docs/ROADMAP.md).

---

**Want to help make the first complete race happen?** Pick one small task, introduce yourself in an issue or on [Discord](https://discord.com/servers/star-wars-episode-i-racer-441839750555369474), and show us what you enjoy working on. I'm also building other projects and would love to meet thoughtful, reliable people who enjoy turning ambitious ideas into real things. A great collaboration here can be the start of more projects together.
