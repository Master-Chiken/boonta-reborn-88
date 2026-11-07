# Contributing to SW_RACER_RE

Thank you for helping improve the Star Wars Episode I: Racer decompilation project.

## Project scope

The goal is to document and re-implement selected functions of the original game so the modding community can understand and extend it. The project does **not** aim for matching compilation or a complete decompilation of every original function.

Contributors are welcome to work on substantial changes, not just beginner tasks. Useful contributions include:
- implementing complete functions, systems, or features whose behaviour is sufficiently understood;
- analysing related groups of functions and global variables;
- improving architecture, C/C++ hooks, Python tooling, build/CI, tests, performance, and developer documentation;
- reproducing and fixing bugs and verifying the changes in the game;
- coordinating and maintaining a technical area after demonstrating reliable work.

You do not need permission for every small experiment in your own fork or feature branch. Coordinate before large architectural changes or work likely to overlap with someone else's task. The goal of review is to protect the official branch and keep changes understandable—not to prevent contributors from doing meaningful work.

## Contribution workflow

1. Read the project [README](README.md), [Governance](GOVERNANCE.md), and [Access Control](ACCESS_CONTROL.md), plus `NOTES.md`.
2. Search the source tree and existing pull requests before starting, to avoid duplicating work.
3. For a substantial reverse-engineering task, open an issue or discuss it in the [official Discord](https://discord.com/servers/star-wars-episode-i-racer-441839750555369474) before spending time on it.
4. Create a branch in your own fork and work there. This is the normal workflow and does not require direct write access to the official repository.
5. Open a draft pull request early when feedback on the approach would help; mark it ready when it is ready for full review.
6. The Project Owner reviews and personally merges changes into the official default branch. Contributors should not expect direct pushes or self-merges into the official branch.
7. Keep each pull request reviewable. A substantial feature is welcome; split it into dependent pull requests only when that makes implementation, testing, or review clearer.

The README identifies `data_symbols.syms` as the source of truth for global variables. Generated function hooks are written to `src/generated/hook_generated.c` by `scripts/GenerateHooks.py` from `hook_generated_c.j2`. Do not make a manual-only edit to a generated file; update the relevant source/template and regenerate the output when appropriate.

## Development setup

The tools currently documented by the project are:
- Git;
- Python 3 for project scripts;
- Ghidra 10.2.2 for the documented decompilation workflow;
- a Windows C compiler for the relevant game/decompilation workflow;
- for building the `dinput.dll` hook: CMake and an LLVM-MinGW toolchain. Ninja is needed when using the provided presets.

For the documented Clang release build, configure and build from the repository root:

```sh
cmake --preset clang-release -DGAME_DIR="<path to your legally obtained game directory>"
cmake --build --preset clang-release
```

See the README for alternatives, sanitizer builds, and static-analysis instructions. If you cannot build the project locally, say so in your issue or pull request and describe what you were able to verify.

## Reverse-engineering notes

When proposing or implementing a function:
- include its address and known name, if available;
- record the game version/build used for observations;
- describe the evidence behind the proposed behaviour (for example, relevant disassembly, callers, arguments, or observed runtime behaviour);
- distinguish confirmed behaviour from hypotheses;
- document unknowns rather than silently guessing;
- make sure the function prototype and calling convention match the evidence.

A short analysis with clear evidence can be submitted even if it does not yet include an implementation.

## Pull request checklist

Before submitting:
- [ ] Explain the problem and why the change is useful.
- [ ] Keep the change limited to one main purpose.
- [ ] State which commands or manual tests you ran and their results.
- [ ] Include a function address, reproduction steps, or other evidence where relevant.
- [ ] Update documentation when workflow or behaviour changes.
- [ ] Regenerate generated files when their source/template changes.
- [ ] Remove temporary logs, local paths, and unrelated formatting changes.
- [ ] Identify risks, assumptions, and any untested paths.
- [ ] Confirm no proprietary game binaries, assets, credentials, or secrets are included.

Please do not claim that a change has been tested if it has not been tested.

## Copyright and large files

Do not commit the original commercial game executable, proprietary game assets, unpacked game data, or other material you are not authorised to redistribute. Describe the version used for testing and keep any required local paths out of commits. Use the project to share your own code, analysis, tests, and documentation.

## Finding a first task

Look for a reproducible bug, a missing explanation, a script that needs tests, or a function/symbol that can be investigated independently. Contributors are also welcome to propose larger feature work. If you are unsure whether a task is suitable, open an issue using one of the repository's templates. Maintainers and contributors can then agree on its scope before implementation.
