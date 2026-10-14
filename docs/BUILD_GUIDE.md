# Build guide — native GameCube/Wii prototype

**Status as of 2026-10-14:** a source-only Step 102 subset has been imported on draft PR #17. GitHub Actions has passed host-side regression tests, a real devkitPPC/libogc cross-build, and a limited headless Dolphin process smoke test. This is the first recorded native build from the imported sources.

## Verified CI path

- [Latest completed validation run](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38628014235)
- Build artifact: [swe1r-gc-step102-source-only](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38626905351/artifacts/11924766751)
- Output: swe1r_gc_port.dol, approximately 301 KiB.
- Toolchain environment: devkitpro/devkitppc:latest in a GitHub Actions container.
- Track mode: USE_IMPORTED_SPLINE=0, which uses the bundled demo/procedural track and does not enable the excluded PC-mod-derived centerline dataset.
- Dolphin smoke test: dolphin-emu --batch --video_backend=Null --exec=dist/swe1r_gc_port.dol; Dolphin remained active until a 12-second timeout. This checks only that the process accepts the DOL and stays running briefly.

The native-build CI container currently uses the mutable latest tag, so the successful run link above is the historical evidence for that toolchain environment; the image is not yet pinned by digest.

## Host checks

Run these in a Linux-like shell with Python and a C compiler available:

~~~sh
python3 tools/check_source_import_policy.py
bash tools/release_check.sh
~~~

The first rejects known excluded asset paths and formats. The second runs the portable C regression scripts and static/source checks. Neither alone proves correct native execution.

## Local native build

A local build requires devkitPro/devkitPPC and libogc. With the toolchain already installed:

~~~sh
export DEVKITPRO=/opt/devkitpro
export DEVKITPPC="$DEVKITPRO/devkitPPC"
make clean
make USE_IMPORTED_SPLINE=0
~~~

A successful build should create a non-empty swe1r_gc_port.dol. Do not set USE_IMPORTED_SPLINE=1: the corresponding PC-mod-derived route data and import headers are deliberately excluded from this source-only branch.

## Runtime validation still required

The headless Dolphin job uses a null video backend. It does **not** prove visible output or playability. Before describing the game as playable, launch the DOL in Dolphin with video enabled or on hardware and test:

- visible picture, track, pod, scenery and readable HUD;
- controller detection, selection menus, acceleration, braking, steering and boost;
- countdown, lap/checkpoint logic, race standings, finish prompt and reset/restart;
- pause/resume, course changes, crash-free operation and sustained frame timing.

Record each observed result with screenshots/logs. Do not substitute the headless process smoke test for this review.

## Provenance and licensing

The supplied source ZIP has no license covering the source tree as a whole. Some course centerlines described by its README are based on an external modded PC spline dataset; those centerline files and related generated mesh/boundary exports are excluded. Before merging PR #17 publicly, confirm that the selected source files may be redistributed under this repository's license. This is a required review gate, not a build-tool requirement.

## Build policy

- Never upload commercial ROMs, original disc images, BIOS files, private dumps, or unclear copyrighted assets.
- Do not commit generated DOL/ELF/map binaries; use the expiring Actions artifact instead.
- Keep API keys in GitHub Actions secrets; never place credentials in source or logs.
- Keep PR #17 in draft until licensing and visible runtime review are complete.
- CI actions for this workflow do not call paid AI APIs or require billing.
