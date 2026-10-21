# Contributing to Boonta Reborn 88

Thanks for wanting to help. You do not need to be an expert programmer. A careful test report, a well-sourced research note, a documentation fix, or a small reproducible test can be valuable.

## First, understand the current state

Boonta Reborn 88 is an unofficial clean-room homebrew project aiming to create an enhanced racing game inspired by *Star Wars: Episode I – Racer* for GameCube and Wii.

The current `gamecube-demo/` prototype builds a native GameCube DOL/ELF and has automated C/Python tests plus selected Dolphin diagnostics. It has **not yet passed a human-operated, full three-lap race in visible Dolphin**. Do not call it playable until that acceptance test has been completed and recorded.

The original game's commercial tracks, models, textures, music, voices, and other extracted content are not integrated into this clean-room prototype.

## Good first contributions

### 1. Test the prototype

Start with [issue #126 — interactive three-lap acceptance](https://github.com/Master-Chiken/boonta-reborn-88/issues/126) and the [milestone checklist](docs/NEXT_MILESTONE.md). Each item should be reported as **PASS**, **FAIL**, or **NOT TESTED**.

Please include:
- the exact commit SHA of the DOL/ELF build you tested;
- Dolphin version and video backend;
- video mode/resolution, if available;
- controller setup (physical controller or Dolphin's emulated controller, and input device);
- results for each test, plus a screenshot or short video where practical;
- reproduction steps for every failure.

Do not commit DOL/ELF builds, ROMs, disc images, BIOS files, or extracted game content.

### 2. Help with reverse-engineering research

The current research queue is [issue #226](https://github.com/Master-Chiken/boonta-reborn-88/issues/226). Before investigating a new angle, read the existing thread and [PR #242](https://github.com/Master-Chiken/boonta-reborn-88/pull/242) so work does not duplicate the active investigation.

A useful research report includes:
- the exact public URL and revision examined;
- the platform/version the evidence describes;
- direct observations with source locations;
- inference and unknowns explicitly separated;
- counter-evidence or limitations;
- one minimal next check.

Do not treat PC findings as proof of GameCube/Wii behavior. Do not label a function by guesswork just because an address, string, or generic symbol seems suggestive. Keep local ROM/disassembly files local; never upload them to issues, agents, or CI.

### 3. Improve documentation or small tests

Beginner-friendly tasks include:
- correcting a confusing sentence or broken link;
- adding reproducible steps to a test or research note;
- writing a host-side regression test for an already understood behavior;
- adding a synthetic fixture for a documented file-format hypothesis;
- checking source provenance and license notices without copying code/assets.

Before starting a new task, search the existing issues and PRs for overlapping work. The project keeps one active research queue and avoids parallel writers editing the same files.

## Working from a browser

You can contribute without cloning the repository or installing a compiler when the task is documentation-only or research based on public sources.

1. Open the relevant file or issue on GitHub.
2. For a small documentation edit, open the file and use the pencil (**Edit this file**) button.
3. Choose **Create a new branch for this commit**; do not commit directly to `main`.
4. Give the commit a short message describing one change.
5. Open a pull request and explain the reason for the change, the evidence, and anything still unknown.
6. Do not merge the pull request yourself unless the repository owner explicitly asks you to do so.

For larger tasks, use one dedicated branch and one reviewable pull request. Documentation normally targets `main`; gameplay changes must follow the repository's current branch and review rules (usually `dev`). Do not merge old branches wholesale, force-push, delete branches, or enable auto-merge as a workaround.

## Build and test locally

A native build requires a configured [devkitPro GameCube/Wii toolchain](https://devkitpro.org/) with devkitPPC and libogc. From a configured devkitPro shell:

```sh
git clone https://github.com/Master-Chiken/boonta-reborn-88.git
cd boonta-reborn-88/gamecube-demo
make clean
make
```

The expected native outputs are `boonta_gc_demo.dol` and `boonta_gc_demo.elf`.

From the repository root, the documented host checks are:

```sh
cc -std=c99 -Wall -Wextra -Werror -pedantic \
  gamecube-demo/tests/test_gameplay_state.c -lm -o /tmp/test_gameplay_state
/tmp/test_gameplay_state

cc -std=c99 -Wall -Wextra -Werror -pedantic \
  gamecube-demo/tests/test_pause_state.c -o /tmp/test_pause_state
/tmp/test_pause_state

python3 -m unittest discover -s gamecube-demo/tools -p 'test_*.py' -v
```

These are documented commands, not a claim that they were run for your contribution. Follow [the build guide](docs/BUILD_GUIDE.md) for artifact checks and current test boundaries. A passing host test, successful build, headless Dolphin smoke, scripted input movie, or screenshot does **not** prove that a person can complete a race.

If you cannot install the local toolchain, that is fine for a documentation or research contribution. For code changes, provide reproducible checks and rely on the project's CI for build evidence; record any tests you could not run.

## Code, assets, licenses, and AI tools

- Prefer original implementations and synthetic test data.
- Read the proposed reuse inventory in [PR #246](https://github.com/Master-Chiken/boonta-reborn-88/pull/246). Research use is not permission to copy code or assets.
- Check the exact source revision, file-level notices, dependencies, license compatibility, and redistribution obligations before importing any third-party code.
- Never commit or upload ROMs, disc images, BIOS files, extracted commercial models, textures, sounds, tracks, or other material of unclear provenance.
- Never send secrets, credentials, private game archives, or proprietary extracted content to AI tools or hosted services.
- Do not enable paid services or billing for project automation. If a required free quota is unavailable, stop and report the blocker.

## Pull request checklist

Before requesting review, confirm:

- [ ] The change addresses one clear task and does not duplicate existing work.
- [ ] The source of any copied code, data, or research is cited with an exact revision.
- [ ] License and provenance concerns are recorded; uncertain cases are left unresolved rather than guessed.
- [ ] Relevant tests were run on the exact commit, or unrun checks are marked **NOT RUN**.
- [ ] Claims are limited to the evidence actually collected.
- [ ] No ROM, disc image, BIOS, commercial asset, secret, or unrelated binary has been added.
- [ ] The PR description states what changed, what was tested, the results, and remaining limitations.

All public documentation and new issues should be written in English. Use concise, concrete language and preserve the distinction between verified facts, inference, and unknowns.

