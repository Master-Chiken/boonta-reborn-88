# Dreamcast starter — Boonta Reborn 88

This directory is a **separate, clean-room Dreamcast homebrew starter**. It is not a port of the existing GameCube/Wii executable, and it contains no commercial game image or extracted proprietary assets.

## Build environment

Install and configure [KallistiOS (KOS)](https://github.com/KallistiOS/KallistiOS) for the Sega Dreamcast, then set `KOS_BASE` to the KOS installation directory and load the KOS environment as described by its documentation.

From this directory, run:

```sh
make
```

The exact output files depend on the installed KOS version and toolchain configuration. This starter has **not yet been compiled in CI**, so do not treat it as a validated binary.

## First milestone

- Build a minimal Dreamcast ELF with KOS.
- Print a startup message and poll the first controller.
- Add video output only after the KOS toolchain is confirmed.
- Keep gameplay logic separate from platform-specific input, video, audio and storage.

## Legal / asset boundary

Use only original code and assets you have the right to use. Do not commit a commercial disc image, BIOS, or extracted copyrighted game assets to this repository. Any testing with a game dump should remain local and comply with applicable law.
