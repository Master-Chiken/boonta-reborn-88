# Boonta Reborn 88

[![GameCube demo CI](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-demo-build.yml/badge.svg?branch=main)](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-demo-build.yml)

**Boonta Reborn 88 is a fan-made homebrew project inspired by _Star Wars: Episode I – Racer_ (1999).** The goal is to build an enhanced racing game for Nintendo GameCube and Wii. It is not an official Lucasfilm, Disney, or original-publisher project.

The work is still at the prototype stage. We want to build on public research and compatible tools, but we keep the game's commercial code and assets separate unless their reuse and redistribution rights are clearly established.

## The current state

The repository contains an original GameCube prototype in `gamecube-demo/`. It builds a native DOL/ELF and has automated tests plus Dolphin diagnostics for specific code paths and rendered frames.

**The prototype has not yet passed a manual playability test.** A person still needs to run it in a visible Dolphin session with a configured controller, complete a three-lap race, confirm the finish and reset, and try another run. Physical GameCube/Wii compatibility is also unverified.

### What is already working

- A native GameCube build using devkitPPC and libogc.
- An original 3D test scene with a procedural desert course, rival pods, canyon geometry, and a source-authored player mesh and texture.
- Prototype controls and race systems for steering, throttle/brake, boost/heat, lap timing, pause, and reset.
- Automated C/Python checks and scripted Dolphin diagnostics for selected behaviors.

### What is still missing

- A successful human-operated three-lap race in visible Dolphin.
- Stable, repeatable evidence for controller response, finish, reset/restart, and several minutes of play.
- Integration of real game tracks, models, textures, music, and other original-game content through a legally reviewed asset pipeline.
- Validation on physical GameCube/Wii hardware and a decision on broader platform-specific behavior.

## How you can help

You do not need to be an experienced programmer. Helpful contributions include testing, reporting exact reproduction steps, researching file formats and public technical references, checking documentation, and reviewing licensing and provenance. Small, evidence-backed contributions are more useful than large unverified changes.

- **Volunteer as a tester:** see [issue #250 — testers wanted](https://github.com/Master-Chiken/boonta-reborn-88/issues/250). Record detailed acceptance results in [issue #126](https://github.com/Master-Chiken/boonta-reborn-88/issues/126) and follow the [current milestone checklist](docs/NEXT_MILESTONE.md).
- **Follow the reverse-engineering work:** see [issue #226 — route/spline progress research](https://github.com/Master-Chiken/boonta-reborn-88/issues/226).
- **Build and test:** start with the [build guide](docs/BUILD_GUIDE.md) and [prototype README](gamecube-demo/README.md).
- **Contribute:** read [CONTRIBUTING.md](CONTRIBUTING.md) for beginner-friendly tasks, browser-based editing, build commands, and review rules.
- **Read the project plan:** see the [roadmap](docs/ROADMAP.md) and [project dashboard](https://github.com/Master-Chiken/boonta-reborn-88/issues/156).

The project is open to contributors who can explain what they tested and what the evidence does—and does not—prove. Please do not upload ROMs, disc images, extracted commercial assets, or private files to the repository, issues, or AI tools.

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

Once the first race is reliable, the roadmap opens up to the bigger remaster vision: upgraded visual presentation, more tracks and pods, expanded menus, audio, saves, progression, bonus modes, and DLC-style content packs. These are intended future features, not claims about the current prototype. See the [product priorities](https://github.com/Master-Chiken/boonta-reborn-88/issues/156) and [roadmap](docs/ROADMAP.md).

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

Research and homebrew development for an enhanced Star Wars: Episode I – Racer (1999) experience on Nintendo GameCube and Wii, with HD visuals, bonus features, and console-specific builds.

**Long-term goal:** create an HD++ remaster/remake that elevates the original racing experience with upgraded visuals and presentation, refined gameplay, bonus content, and future DLC-style expansions such as new circuits, pods, challenges, and game modes. GameCube and Wii-specific builds are part of the plan.

The complete remaster, all bonus features, and DLC-style content are future goals—not a claim that they are already implemented. The current development status and the next playable milestone are documented above and in the [roadmap](docs/ROADMAP.md).

---

**Want to help make the first complete race happen?** Pick one small task, introduce yourself in an issue or on [Discord](https://discord.com/servers/star-wars-episode-i-racer-441839750555369474), and show us what you enjoy working on. I'm also building other projects and would love to meet thoughtful, reliable people who enjoy turning ambitious ideas into real things. A great collaboration here can be the start of more projects together.
