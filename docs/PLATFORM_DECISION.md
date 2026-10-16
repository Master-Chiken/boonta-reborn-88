# Platform decision: GameCube vs Wii

## Decision status

**Open — do not lock the final target yet.** The project goal is a faithful *Star Wars: Episode I — Racer* reconstruction followed by the strongest visual remaster that can run reliably on the chosen hardware, with clearly identified bonus content. Evaluate GameCube and Wii using the same small playable vertical slice before choosing.

## Keep three different approaches separate

1. **Native GameCube build:** a homebrew DOL targeting GameCube hardware and its memory, GPU, CPU, controller and storage limits.
2. **Native Wii build:** a separately tested target. Wii hardware is closely related to GameCube hardware and offers additional capabilities, but a Wii build must not be assumed to run correctly merely because a GameCube build compiles.
3. **Original Nintendo 64 game through a Wii emulator:** a useful comparison and play/reference route, depending on the emulator and game compatibility. It is not the remaster itself and does not automatically expose the original game's assets or source code for modification.

Do not describe emulator upscaling as native GameCube/Wii HD output. If an emulator can render the N64 game at a higher output resolution, that is a separate presentation path and must be labelled accordingly.

## What the N64-on-Wii route can contribute

- Compare track layout, landmarks, lap flow, vehicle handling, rival behavior, pickups, menus and race progression against the PC and Dreamcast editions.
- Record differences that may be specific to the N64 edition rather than silently treating it as the canonical version.
- Use a local, lawful copy and compatible emulator for private observation where appropriate; keep ROMs, disc images, BIOS files and proprietary extracted payloads out of the public repository.
- Record the emulator name/version, settings, hardware, reproducible steps and confidence for each observation.
- Treat screenshots/video as reference evidence, not as permission to copy or redistribute commercial assets.

An emulator is not a substitute for source-code research, a native port, or a renderer rewrite. It may help validate reference behavior, but it does not by itself provide an HD remaster.

## Fair comparison test

Build the same minimal vertical slice for each viable native target and record:

- Does it boot consistently in an emulator and, when available, on real hardware?
- Does it draw a complete scene, read the controller, start a race and finish a lap?
- Is the frame rate and frame pacing stable with rivals, effects and collisions active?
- What are measured memory use, texture/geometry budget, loading behavior and worst-case performance?
- Which visual upgrades survive the hardware budget without damaging handling or readability?
- How practical are build, debugging, controller support, save data and packaging?
- What can be tested reliably for free through GitHub Actions and free tools, without paid APIs or services?

Do not choose based only on theoretical specifications or a headless emulator process staying alive. A successful compile is not proof of a playable game.

## Decision rule

Keep both targets open until the evidence is sufficient. Prefer the platform with a repeatable playable build, reliable rendering/input, acceptable performance and a sustainable free toolchain. If both are viable, decide whether to maintain both builds or designate one primary target and the other as a later port.

## Visual target language

For native GameCube/Wii, describe the goal as **HD-inspired assets and the best enhanced image quality achievable within the console budget**, not guaranteed native 720p/1080p. Separate:
- higher-detail source assets;
- in-game texture/geometry/rendering improvements;
- the console's actual output resolution;
- any emulator-side upscaling.

These are different technical outcomes and should be measured and reported separately.
