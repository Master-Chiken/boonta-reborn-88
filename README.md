# Boonta Reborn 88

### Bring podracing back to GameCube and Wii — one playable lap at a time.

[![GameCube demo CI](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-demo-build.yml/badge.svg?branch=main)](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-demo-build.yml)

**Boonta Reborn 88 is an unofficial, clean-room homebrew project inspired by _Star Wars: Episode I – Racer_ (1999).** The goal is bigger than a nostalgia trip: build a genuinely fun racer for classic Nintendo hardware, prove one complete race from start to finish, then grow it with original tracks, pods, and ideas.

The player-pod mesh/texture, varied canyon skyline, and readable finish banner are now integrated on `main` ([PR #202](https://github.com/Master-Chiken/boonta-reborn-88/pull/202), [PR #203](https://github.com/Master-Chiken/boonta-reborn-88/pull/203), [PR #204](https://github.com/Master-Chiken/boonta-reborn-88/pull/204)). The linked Dolphin captures are scripted diagnostics, not proof of manual-controller acceptance.

We're building it in public—and this is a great moment to join. Whether you enjoy low-level C, 3D art, gameplay feel, test automation, technical research, or simply putting a prototype through its paces, **you can make a visible difference**.

> **The goal isn't to collect features or make impressive promises. It's to get one complete, enjoyable race working — then build on a solid foundation.**

[Project roadmap](docs/ROADMAP.md) · [Current playable milestone](https://github.com/Master-Chiken/boonta-reborn-88/issues/126) · [Build & test guide](docs/BUILD_GUIDE.md) · [Join the community](https://discord.com/servers/star-wars-episode-i-racer-441839750555369474)

---

## What we're building

The mainline project is a clean-room GameCube prototype in `gamecube-demo/`. Its course, rivals and effects are original procedural work, alongside an original source-authored player mesh and texture—not imported commercial game code or assets.

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
3. **Grow the asset pipeline safely.** Extend the validated mesh/texture path to matching track and collision data without destabilizing driving. Follow [issue #181](https://github.com/Master-Chiken/boonta-reborn-88/issues/181).

More tracks, additional pods, expanded menus, audio, saves, progression, and bonus modes belong after the first race is reliable. See the [product priorities](https://github.com/Master-Chiken/boonta-reborn-88/issues/156) and [roadmap](docs/ROADMAP.md).

## Come build this with us

**You don't need to know everything or arrive with a huge feature.** Curiosity, clear communication, and the willingness to test an idea are valuable here. A useful bug report, a small fix, a model, a tool, or one careful test session can move the game forward.

| If you enjoy… | You could help with… |
| --- | --- |
| Playing and testing | Run the prototype in a visible Dolphin session, test the controls and full race, and report what works or breaks. |
| C and gameplay | Improve steering feel, race-state transitions, collisions, lap timing, or reset/restart behavior—with regression tests. |
| Graphics and 3D | Improve the GX scene, camera, course readability, or the validated mesh/texture path. |
| Python and tooling | Strengthen format validators, synthetic fixtures, artifact checks, and reproducible diagnostics. |
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

## Clean-room and source policy

This is a fan homebrew/research project, not an official Star Wars product and not a completed port of the commercial game.

- Do not commit commercial ROMs, disc images, BIOS files, extracted proprietary models/textures/audio, or other copyrighted payloads.
- The separate Step 102 source archive remains on hold until file-level authorship, license, and redistribution rights are clear.
- Review third-party source and assets before reuse. The root MIT license does not grant rights to Star Wars material or automatically relicense outside contributions.

Keep the public project reproducible, original, and safe to build. See the [source-import gate](docs/SOURCE_IMPORT_GATE.md) for details.

---

**Want to help make the first complete race happen?** Pick one small task, introduce yourself in an issue or on [Discord](https://discord.com/servers/star-wars-episode-i-racer-441839750555369474), and show us what you enjoy working on. I'm also building other projects and would love to meet thoughtful, reliable people who enjoy turning ambitious ideas into real things. A great collaboration here can be the start of more projects together.
