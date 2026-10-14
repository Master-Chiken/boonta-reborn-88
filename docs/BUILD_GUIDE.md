# Build guide (initial)

**Status:** no project build has been verified yet. This document intentionally does not invent a build command before the repository's source tree and target toolchain are known.

## Prerequisites decision

We will first inspect the prototype archive and select one of these directions:

### Route A — N64 playback smoke test on Wii
Use a compatible, existing Wii homebrew N64 emulator with a game copy the user is legally entitled to use.

This is only a compatibility test. It is not a native port, not an HD remaster, and not a custom WBFS build of this project.

### Route B — Native GameCube/Wii homebrew
Choose the development toolchain based on the actual code and dependencies found in the prototype. A minimal app should be built and launched before game code is adapted. Toolchain setup should prefer a reproducible container or cloud CI route where practical, especially if local storage is constrained.

## Build policy

- Don't upload ROMs, original game disc images, proprietary game data, or user-private dumps.
- Don't check in generated disc images or large binaries. .gitignore excludes common image and build-output extensions, but every proposed commit still needs review.
- Keep tool versions and commands in this file once actually tested.
- Record actual compiler errors and fixes; don't claim success based on an unexecuted command.
- Review licenses before copying external code into this repository.

## Test record

| Date | Target | Revision / tool versions | Command | Result |
|---|---|---|---|---|
| Not yet tested | — | — | — | No build evidence yet |

## First reproducible test checklist

- [ ] Inventory all source files in the prototype archive.
- [ ] Verify archive provenance and license.
- [ ] Select one target/toolchain.
- [ ] Add the smallest source file and build configuration needed for that target.
- [ ] Build it in a documented environment.
- [ ] Launch in a supported emulator or real hardware, if available.
- [ ] Record logs and actual result in this guide.
