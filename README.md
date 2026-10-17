# Boonta Reborn 88

### Bring podracing back to GameCube and Wii — one playable lap at a time.

[![GameCube demo CI](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-demo-build.yml/badge.svg?branch=main)](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-demo-build.yml)

**Boonta Reborn 88 is an unofficial, clean-room homebrew project inspired by _Star Wars: Episode I – Racer_ (1999).** The ambition is to build an exciting, enhanced racing experience for native GameCube/Wii hardware, with Dolphin as a practical development and testing environment.

The latest visual work is documented in [the current racer/canyon PR chain](https://github.com/Master-Chiken/boonta-reborn-88/pull/204). Automated Dolphin captures there are scripted diagnostics, not proof of manual-controller acceptance.

We're building it in public. Whether you enjoy low-level C, rendering, gameplay feel, test automation, or simply putting a prototype through its paces, **there's a useful way to contribute**.

> **The goal isn't to collect features or make impressive promises. It's to get one complete, enjoyable race working — then build on a solid foundation.**

[Project roadmap](docs/ROADMAP.md) · [Current playable milestone](https://github.com/Master-Chiken/boonta-reborn-88/issues/126) · [Build & test guide](docs/BUILD_GUIDE.md) · [Join the community](https://discord.com/servers/star-wars-episode-i-racer-441839750555369474)

---

## What we're building

The mainline project is a clean-room GameCube prototype in `gamecube-demo/`. Its rendering and course geometry are original procedural work—not imported commercial game code or assets.

### What's already here

- **A native GameCube build** using devkitPPC/libogc, producing a DOL and ELF.
- **A visible 3D racing scene** with a scrolling desert course, road markings, canyon walls, and original procedural podracer and rival craft.
- **Prototype racing systems** for steering inertia, throttle/brake, boost and heat, pitch/slide, off-road drag, rail recovery, rival interactions, lap timing, pause and reset.
- **Automated regression coverage** for gameplay state, input mapping, race/lap logic, and edge cases.
- **Dolphin diagnostics** that build and validate the native artifacts and have exercised scripted steering, reset, pause/resume, and finish-state checks.

These are meaningful foundations, but they are **not yet proof of a fully playable game**. In particular, the team still needs a visible, manual controller session that completes a three-lap race, finishes cleanly, resets, and starts another run. Sustained frame pacing and physical GameCube/Wii compatibility also need their own evidence.

See [the current acceptance checklist](docs/NEXT_MILESTONE.md) for the exact state and what still needs testing.

## The next big wins

We keep the work focused on a playable vertical slice rather than spreading effort across unfinished systems.

1. **Prove the race is playable.** In visible Dolphin, verify steering, acceleration/braking, boost and overheating, off-road/rail response, pause/resume, three-lap finish, reset and restart. Record the emulator version, controller setup, results, and any evidence. Start with [issue #126](https://github.com/Master-Chiken/boonta-reborn-88/issues/126).
2. **Make the course and racer feel convincing.** Improve the track silhouette, camera, handling, and collision response as one coherent experience.
3. **Grow the asset pipeline safely.** Establish a documented, bounds-checked path for original test meshes and textures, then confirmed track/collision data. Follow [issue #181](https://github.com/Master-Chiken/boonta-reborn-88/issues/181).

More tracks, additional pods, expanded menus, audio, saves, progression, and bonus modes belong after the first race is reliable. See the [product priorities](https://github.com/Master-Chiken/boonta-reborn-88/issues/156) and [roadmap](docs/ROADMAP.md).

## Come contribute

**You don't need to be an expert in every part of the project—or write a huge feature to make a difference.** A clear test report can be just as useful as a code change.

| If you enjoy… | You could help with… |
| --- | --- |
| Playing and testing | Run the prototype in a visible Dolphin session, test the controls and full race, and report what works or breaks. |
| C and gameplay | Improve steering feel, race-state transitions, collisions, lap timing, or reset/restart behavior—with regression tests. |
| Graphics and 3D | Improve the GX scene, camera, course readability, or the validated mesh/texture path. |
| Python and tooling | Strengthen format validators, synthetic fixtures, artifact checks, and reproducible diagnostics. |
| Research and documentation | Document observed behavior, clarify formats, improve setup instructions, or help maintain the test checklist. |
| GameCube/Wii hardware | Reproduce the same checks on real hardware and clearly record the hardware, video mode, controls, and results. |

### Good places to start

- **Most valuable right now:** follow the manual test plan in [issue #126](https://github.com/Master-Chiken/boonta-reborn-88/issues/126). Mark each check **PASS / FAIL / NOT TESTED**; include the Dolphin version, video backend, controller profile, and screenshots or a short video where useful.
- **Interested in rendering or asset formats?** Read [issue #181](https://github.com/Master-Chiken/boonta-reborn-88/issues/181) first so new work builds on the existing mesh and test foundations instead of duplicating them.
- **Not sure where to begin?** Open an issue or join the [Discord community](https://discord.com/servers/star-wars-episode-i-racer-441839750555369474). Explain what you would like to try and what environment you have. Small, focused experiments and well-documented findings are welcome.

### Build and run the prototype

The clean-room demo can be built without bundling a commercial ROM or extracted game assets. For the native DOL/ELF build, install the official [devkitPro GameCube/Wii toolchain](https://devkitpro.org/) with devkitPPC and libogc, open its configured shell, then run:

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

## How we work

We follow one simple engineering order:

1. **Make it work:** prove the smallest useful end-to-end behavior.
2. **Make it good:** handle edge cases, keep the implementation understandable, and add regression tests.
3. **Make it fast:** optimize only after correctness is established, using measurements where practical.

Before implementing a change, read [`AGENTS.md`](AGENTS.md) and check the current issues/PRs. Prefer focused, reviewable pull requests and include the test commands and results. Be explicit about what was **not** tested—host tests, native builds, scripted Dolphin checks, manual controller play, and physical hardware prove different things.

## Clean-room and source policy

This is a fan homebrew/research project, not an official Star Wars product and not a completed port of the commercial game.

- Do not commit commercial ROMs, disc images, BIOS files, extracted proprietary models/textures/audio, or other copyrighted payloads.
- The separate Step 102 source archive remains on hold until file-level authorship, license, and redistribution rights are clear.
- Review third-party source and assets before reuse. The root MIT license does not grant rights to Star Wars material or automatically relicense outside contributions.

Keep the public project reproducible, original, and safe to build. See the [source-import gate](docs/SOURCE_IMPORT_GATE.md) for details.

---

**Want to help make the first complete race happen?** Pick a check or a small task, share what you find, and let's turn the prototype into a game one verified improvement at a time.
