# Boonta Reborn 88

### An HD++ remaster/remake vision for Star Wars: Episode I – Racer (1999) on GameCube and Wii.

[![GameCube demo CI](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-demo-build.yml/badge.svg?branch=main)](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/gamecube-demo-build.yml)

**Boonta Reborn 88 aims to become an enhanced fan-made remaster/remake of _Star Wars: Episode I – Racer_ (1999)** for Nintendo GameCube and Wii. The long-term vision goes beyond a straight port: HD-style visuals, a major presentation upgrade, refined racing, new tracks and pods, bonus modes, and future DLC-style content—while building console-specific versions around the strengths of the original hardware.

The player-pod mesh/texture, varied canyon skyline, and readable finish banner are now integrated on `main` ([PR #202](https://github.com/Master-Chiken/boonta-reborn-88/pull/202), [PR #203](https://github.com/Master-Chiken/boonta-reborn-88/pull/203), [PR #204](https://github.com/Master-Chiken/boonta-reborn-88/pull/204)). The linked Dolphin captures are scripted diagnostics, not proof of manual-controller acceptance.

We're building it in public—and this is a great moment to join. Whether you enjoy low-level C, 3D art, gameplay feel, test automation, or technical research, **you can make a visible difference**. Contributors with experience in the original game, its modding scene, file formats, asset pipelines, or console development are particularly welcome; describe your experience and the workflow you can contribute to.

> **The vision is a full HD++ Racer experience: a remaster/remake with upgraded visuals, bonus content, and room to grow through new tracks, pods, modes, and DLC-style expansions.** The immediate milestone remains the same: make one complete, enjoyable race work reliably before expanding the content.

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

**Research-first working model: 80% reverse engineering, 20% implementation, tests and project management combined.** For every ten comparable work blocks, aim for eight spent understanding source, binaries/runtime behavior, formats and platform differences, and no more than two on all other engineering work. Keep one research question active at a time. Record evidence, confidence, unknowns and a reproducible next test before changing gameplay. The operating rules are in [docs/PROJECT_OPERATING_RULES.md](docs/PROJECT_OPERATING_RULES.md).

1. **Reverse-engineer route/progress before redesigning it.** Map the PC reference's spline cursor against the current GameCube test course and its distance-based lap counter. Keep PC facts, candidate Step 102 findings and GameCube/Wii hypotheses separate. Start with the [SW_RACER_RE study plan](docs/SW_RACER_RE_STUDY_PLAN.md) and [behavior matrix](docs/SW_RACER_RE_BEHAVIOR_MATRIX.md).

2. **Reverse-engineer pod handling and state transitions next.** Establish how input, turn rate, traction, boost/heat, collision and lap state work in the sources before choosing a change. Use evidence-linked notes, not copied upstream code. Keep unclear Step 102 files/data on provenance hold.

3. **Use the remaining 20% to verify and implement one bounded result.** Test the current rail/controls candidate in visible Dolphin, record the exact build and PASS / FAIL / NOT TESTED results, then implement only the smallest change justified by the research. Start the interactive acceptance with [issue #126](https://github.com/Master-Chiken/boonta-reborn-88/issues/126).

4. **Expand rendering/content later.** Richer models, textures, camera effects, extra tracks, rivals, sound and bonus modes follow after the relevant behavior and source formats are understood and the core race is reliable.

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
