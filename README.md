# Boonta Reborn 88

### A remaster for Star Wars: Episode I – Racer (1999) on GameCube and/or Wii.

[![GameCube demo CI](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-demo-build.yml/badge.svg?branch=main)](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-demo-build.yml)

**Boonta Reborn 88 aims to become a fan-made remaster of _Star Wars: Episode I – Racer_ (1999) for Nintendo GameCube and Wii.** The original 1999 release did not receive a dedicated native edition for either console; this project is building a new homebrew experience for those systems, not claiming that an existing GameCube/Wii port already exists. The immediate goal is one reliable, enjoyable racing experience; the larger goal is a substantial visual, gameplay, and content upgrade.

## Development order: gameplay first, always

The project follows this order without skipping ahead:

1. **Gameplay — absolute priority:** make controls, handling, collisions, boost/heat, rivals, camera, laps, finish, pause, reset/restart, and stability work reliably. The playable slice is not accepted until a complete three-lap race is verified with a real controller in visible Dolphin.
2. **Core original-game content:** establish the essential tracks, pods, racing flow, rivals, and progression, using only material with documented provenance and appropriate rights.
3. **Graphics and remaster polish:** improve models, textures, scenery, effects, and UI after gameplay is accepted and core content is underway.
4. **Bonus content and DLC-style expansions:** new tracks/pods, bonus modes, packs, and broader remake ideas come last and must not delay the core experience.

Apply “Make it work, make it good, make it fast” in that order.

## Longer-term possibilities

The longer-term direction may include better visuals and presentation, additional original or rights-cleared tracks and pods, expanded progression, bonus modes, and optional DLC-style packs. “HD++ Remaster” and “HD+++ Premium” are internal ambition labels for possible levels of polish and scope—not current deliverables or promises. A broader _Star Wars Racer_-inspired experience is only a distant possibility, subject to feasibility and rights.

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
2. **Build the essential original-game experience.** Define a provenance-cleared plan for recognizable tracks, pods, rivals, and racing progression before expanding into new content.
3. **Polish graphics after the gameplay gate.** Extend the existing mesh/texture path toward richer models, textures, track data, and collision once the first race is accepted and core content is underway. Follow [issue #181](https://github.com/Master-Chiken/boonta-reborn-88/issues/181).

After the gameplay gate, prioritize the essential original-game content. Graphics and remaster polish follow as the core content takes shape. Only after those foundations should development consider new tracks/pods, bonus modes, DLC-style packs, HD+++ Premium ideas, or a wider Star Wars Racer-style remake. These are future ambitions, not claims about the current prototype. See the [product priorities](https://github.com/Master-Chiken/boonta-reborn-88/issues/156) and [roadmap](docs/ROADMAP.md).

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

Near-term work is focused on turning the current prototype into one reliable, enjoyable race, then expanding the essential racing experience. Better visuals, additional original or rights-cleared content, bonus modes, and broader remaster ideas are longer-term possibilities—not claims about what is implemented today. Any native GameCube/Wii build must respect the hardware's limits; true HD output would require a different platform target. See the [roadmap](docs/ROADMAP.md) for priorities and acceptance criteria.

---

**Want to help make the first complete race happen?** Pick one small task, introduce yourself in an issue or on [Discord](https://discord.com/servers/star-wars-episode-i-racer-441839750555369474), and show us what you enjoy working on. I'm also building other projects and would love to meet thoughtful, reliable people who enjoy turning ambitious ideas into real things. A great collaboration here can be the start of more projects together.
