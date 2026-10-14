# Reuse strategy: existing Racer work

**Goal:** avoid rebuilding research that the community has already done, while keeping the GameCube/Wii homebrew target distinct from PC reverse-engineering and mod projects.

## Existing projects checked

### OpenSWE1R — PC-oriented open-source reimplementation
- Repository: https://github.com/OpenSWE1R/openswe1r
- Its README describes a Windows API/CPU compatibility layer and open-source replacements patched into the original PC game's binary at runtime.
- It still relies on the original game binary/assets, and the README states GPL-2.0-or-later for its source.
- **Reuse here:** study architecture, game-behaviour notes, and documented mechanics as research leads. Cite findings and independently reimplement platform-neutral behaviour.
- **Do not copy blindly:** its runtime/binary compatibility architecture is not a native GameCube port; GPL obligations and dependencies need review before any code reuse.

### SW_RACER_RE — PC decompilation / modding research
- Repository: https://github.com/tim-tim707/SW_RACER_RE
- Its README says the aim is to document and reimplement selected functions for modding, not to fully decompile or matching-compile the game. It reports analysed functions and contains generated hooks / symbols plus a separate DirectInput rendering-mod project.
- **Reuse here:** function names, symbol maps, reverse-engineering notes and behaviour hypotheses as research references, after reviewing the relevant file's license and provenance.
- **Do not assume:** these are portable GameCube sources or a complete game engine. PC hooks and generated symbols are not a native GameCube build.

### SWE1R-Mods / related format tooling
- Repository lead: https://github.com/louriccia/SWE1R-Mods
- The checked `master` README URL was not available, so the repository's current branch, license and file-level terms still need verification before relying on it.
- **Reuse here:** only documented file-format knowledge and tooling whose license/provenance is confirmed. Prefer metadata and conversion tools over copying extracted game assets.

## Project implementation order

1. **Make the Step 102 bundle accessible in this work session.** It is not present in the GitHub repository tree. Import cannot be completed from a filename or an earlier audit alone; the actual archive bytes are required.
2. **Run the existing Step 102 host tests unchanged first.** Preserve their scripts and test fixtures, record exact commands and results in CI, and only then fix failures.
3. **Native build:** use the existing `.github/workflows/native-build.yml` and devkitPro container as the baseline. Confirm its expected output filename matches the prototype Makefile before declaring success.
4. **Dolphin smoke test:** preserve the DOL and build logs as artifacts. Record boot, video output, controller input and failure details separately; compile success is not a playable-game claim.
5. **Vertical slice:** one legally clear/procedural course, one controllable pod, stable camera, collision/bounds, lap/checkpoint/finish, minimal HUD and restart.
6. **Expand existing Step 102 features:** first make its single-race flow reliable, then connect championship progression, time trial, Mirror Cup and unlock/bonus scaffolding already described by the bundle. Do not rewrite these systems from scratch if their source is present and cleared.
7. **Use community PC research to fill gaps:** turn findings into short, attributed behaviour notes and platform-neutral tests; implement GameCube-specific code independently where architectures differ.

## Import rules

- Do not add ROMs, disc images, BIOS, extracted proprietary textures/models/audio or uncleared PC-mod spline datasets.
- The repository's MIT license does not automatically cover imported third-party files.
- Record provenance/license per imported directory or file; keep unclear material outside the public repository.
- Keep `dreamcast/` separate from the GameCube/Wii milestone.

## Acceptance criteria

- [ ] Actual Step 102 archive bytes are available and inventoried.
- [ ] Provenance and redistribution rights are documented for each imported file.
- [ ] Host regression suite runs in GitHub Actions.
- [ ] devkitPPC/libogc build creates a non-empty DOL.
- [ ] Dolphin boot/input/render/race-completion results are recorded.
- [ ] README reports host tests, native build, and runtime verification separately.
