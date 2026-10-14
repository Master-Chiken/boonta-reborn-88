# GameCube smoke test

This folder contains a small clean-room diagnostic program for the GameCube/Wii homebrew toolchain. It is intentionally independent of the Step 102 game prototype.

## What it proves

A successful GitHub Actions run proves that devkitPPC/libogc can compile this minimal program into a non-empty `boonta_smoke.dol`. If the artifact is downloaded and run in Dolphin, it can also test video output and controller input.

It does **not** prove that the full racing prototype builds, runs, or is playable.

## Build locally

With devkitPro's GameCube/Wii toolchain installed:

```sh
export DEVKITPRO=/opt/devkitpro
export DEVKITPPC="$DEVKITPRO/devkitPPC"
make
```

The expected output is `boonta_smoke.dol`.

## Next steps

1. Get a green CI build for this smoke test.
2. Download the artifact from the GitHub Actions run and boot it in Dolphin.
3. Separately review the Step 102 archive and import only source/code/assets with acceptable provenance.
4. Run the prototype's host tests, then attempt the full GameCube build.

No commercial ROM, disc image, or extracted game asset belongs in this folder.
