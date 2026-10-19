# Build guide and validation evidence

Last reviewed: 2026-10-15

This guide separates the **clean-room procedural GameCube demo** currently built in `gamecube-demo/` from the fuller Step 102 source archive, which remains on a separate provenance/license review track.

## Current mainline state

The clean-room demo now includes three staggered procedural rivals, race/current-lap/best-lap clocks, finite-state guards for speed/lap transitions, and elapsed-time-scaled gameplay updates that preserve the 60 Hz tuning while compensating for 50 Hz cadence. It has a native devkitPPC/libogc DOL/ELF build, artifact-structure validation, strict C99 gameplay/pause tests, and a bounded Dolphin headless process smoke test. A prior CI run captured a visible procedural scene using Dolphin's Software Renderer.

These checks are deliberately separate:
- **Host tests** validate the named deterministic functions and state transitions.
- **Native build** proves that the clean-room demo compiles and links for GameCube.
- **Artifact validation** checks the DOL/ELF structures and DOL padding.
- **Headless smoke** proves Dolphin boots the DOL and remains alive for the bounded null-video window; it does not prove graphics or controls.
- **Visible frame capture** proves that a frame containing the expected procedural scene colors was captured in the CI renderer; it does not prove controller response.
- **Interactive gameplay** requires a visible Dolphin session or hardware test with actual input and a complete race.

None of these results means the Step 102 archive itself has been imported or built.

## Reproduce the host checks

From the repository root:

```sh
cc -std=c99 -Wall -Wextra -Werror -pedantic \
  gamecube-demo/tests/test_gameplay_state.c -lm -o /tmp/test_gameplay_state
/tmp/test_gameplay_state

cc -std=c99 -Wall -Wextra -Werror -pedantic \
  gamecube-demo/tests/test_pause_state.c -o /tmp/test_pause_state
/tmp/test_pause_state

python3 -m unittest discover -s gamecube-demo/tools -p 'test_*.py' -v
```

The gameplay tests cover speed/boost inputs, analog-stick and D-pad mapping, steering inertia/damping, 50/60 Hz cadence consistency (including accelerate/coast/brake), lap boundaries and finish state, a deterministic simulated three-lap progression, rival collision/overtake thresholds, off-road drag, rail recovery, and non-finite speed/lap input guards. The simulation is not a controller test.

## Reproduce the native build

Use a configured devkitPro/devkitPPC environment with libogc:

```sh
cd gamecube-demo
make clean
make
python3 tools/pad_dol.py boonta_gc_demo.dol
cd ..
python3 gamecube-demo/tools/validate_artifacts.py \
  gamecube-demo/boonta_gc_demo.dol \
  gamecube-demo/boonta_gc_demo.elf
```

GitHub Actions runs the native build in the `devkitpro/devkitppc` container, pads the DOL for 32-byte-aligned section reads, validates the artifacts, and uploads the DOL/ELF plus build log as a short-retention artifact. The exact tested commit and the run URL should accompany any future release candidate.

## Evidence record

| Evidence | Result | Boundary |
|---|---|---|
| Current mainline after PR #100, commit `7d46e90de0e9db4e9ed36f88012ac15ab2491f18` | [Post-merge CI run 38744031286](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38744031286): host tests, native DOL/ELF build, artifact validation, and 12-second Dolphin null-video smoke succeeded; the optional Software Renderer job was still running when checked. | Confirms the required automated gates for the current timing/speed-guard mainline. It is not live-controller or complete-race proof. |
| Mainline native build on commit `adf4b596f18affa68dd70f33fb90cdfc60821824` | [CI run 38738237495 passed](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38738237495) | Host tests, DOL/ELF build, artifact validation, and headless smoke for the code then on main. |
| Visible procedural-scene capture | [CI run #69](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38727969531) | Visible road, edge rails, center markers, player pod, and rival pod in Dolphin Software Renderer. Not live input or a completed race. |
| Steering-inertia regressions | [PR #84 / run 38737739411](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38737739411), merged | Deterministic host tests, native build, artifact validation, headless smoke, and optional frame diagnostic passed on the exact PR head. |
| Distance/lap simulation | [PR #86 / run 38738545769](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38738545769), merged | Shared distance helper and a host simulation reach the three-lap finish using the prototype's transition helpers. This is not an actual interactive race. |

## Still-required runtime evidence

The following remain open acceptance gates and must not be inferred from CI compilation or host simulation:

1. In a visible Dolphin session, test reset (Y), accelerate (A), brake (B), analog steering, D-pad steering, boost (X+A), pause/resume (Start), and reset while paused.
2. Complete a real three-lap run, check the finish state, reset, and start another run.
3. Run a longer session and check crashes, graphics corruption, and severe frame-pacing problems.
4. Record Dolphin version/backend, controller profile, the exact tested commit, observed pass/fail results, and supporting screenshots/video/logs. Hardware compatibility remains unverified unless a physical GameCube/Wii test is performed.

See [the interactive milestone checklist](NEXT_MILESTONE.md) and the [current CI workflow](../.github/workflows/gamecube-demo-build.yml).

## Step 102 source/import boundary

The fuller Step 102 source archive remains separate from the clean-room demo. Before importing any of it, complete the path-by-path provenance/license review, including generated track centerlines, demo route data, models, materials, audio, and external dependencies. No successful clean-room build grants permission to redistribute those files.

## Repository safety

- Do not commit commercial ROMs/disc images, BIOS files, extracted copyrighted assets, or uncertain third-party payloads.
- Keep private game archives outside the repository, CI artifacts, and external AI review prompts.
- Prefer free CI/model routes; if a free quota is unavailable, stop rather than enabling paid billing or a paid fallback.
- Update this guide only with reproducible commands, exact commit SHAs, and observed CI/runtime results.
