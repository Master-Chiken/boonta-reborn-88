# Next milestone: visible runtime verification and provenance sign-off

## Current state (2026-10-14)

The Step 102 source-only subset now lives on draft PR #17 (branch import/step102-source-only). It has passed:
- the path/asset import policy and host regression suite in GitHub Actions;
- a devkitPPC/libogc cross-build that produced a non-empty swe1r_gc_port.dol of approximately 301 KiB;
- a 12-second headless Dolphin process smoke test using the null video backend.

[Latest validation run and build artifact](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38628014235).

Nothing from this import has been merged into main. Do not call this a finished or playable port yet: visible rendering, controller response and gameplay remain unverified.

## Immediate work

1. **Source rights:** verify the origin/ownership and redistribution terms for the imported C source, headers, build files, tests and documentation. The supplied ZIP does not contain a license covering the source tree as a whole.
2. **Visible emulator test:** open the generated DOL in Dolphin with a visible video backend and a mapped GameCube controller. Verify picture output, pod/track rendering, menus, steering, throttle, braking, boost, checkpoint/lap progression, finish, pause and restart.
3. **Record runtime evidence:** capture video/screenshots and logs, list exactly what was tested, and distinguish verified behavior from untested behavior.
4. **Fix only demonstrated issues:** preserve current host tests and CI gates. Add regression coverage for each gameplay or renderer defect discovered.
5. **Review before merge:** keep PR #17 in draft until the licensing boundary and visible runtime test are satisfactorily reviewed. Never merge automatically.

## Provenance exclusions

The first public source-only import intentionally excludes:
- PC-mod-derived course centerlines and their manifest;
- imported centerline and generated mesh/boundary headers;
- voice/audio, model/texture exports and unreviewed asset files;
- ROMs, disc images, extracted game data, binary dumps and PC/N64 extraction helpers.

Builds use USE_IMPORTED_SPLINE=0 with a demo/procedural track. The path guard is a safety net, not a license scanner.

## Reproducible CI commands

Host checks:

~~~sh
python3 tools/check_source_import_policy.py
bash tools/release_check.sh
~~~

Native build with devkitPro installed:

~~~sh
export DEVKITPRO=/opt/devkitpro
export DEVKITPPC="$DEVKITPRO/devkitPPC"
make clean
make USE_IMPORTED_SPLINE=0
~~~

CI currently uses the container image devkitpro/devkitppc:latest; pinning the exact image digest is a future reproducibility improvement.

## Later vertical-slice goal

Once visible rendering/controller behavior is confirmed, concentrate on one stable and satisfying race: one course, one controllable pod, functional camera follow, track boundaries/collision, reliable finish logic and stable frame timing. Only expand presentation, assets, additional courses and packaging after that vertical slice is verified.
