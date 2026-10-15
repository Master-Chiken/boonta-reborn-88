# Reuse strategy: existing Racer work

**Goal:** avoid rebuilding research that the community has already done, while keeping the native GameCube/Wii target distinct from PC reverse-engineering and mod projects.

## Existing projects checked

### OpenSWE1R — PC-oriented open-source reimplementation
- Repository: https://github.com/OpenSWE1R/openswe1r
- Its README describes a Windows API/CPU compatibility layer and open-source replacements patched into the original PC game's binary at runtime.
- It still relies on the original game binary/assets, and its source is identified as GPL-2.0-or-later.
- **Reuse here:** study architecture, documented mechanics and behaviour notes as research leads. Attribute findings and independently implement platform-neutral behaviour.
- **Do not copy blindly:** its runtime/binary compatibility architecture is not a native GameCube port; review license obligations and dependencies before any code reuse.

### SW_RACER_RE — PC reverse-engineering / modding research
- Repository: https://github.com/tim-tim707/SW_RACER_RE
- Its stated goal is to document and reimplement selected functions for modding, not to provide a complete matching decompilation. It includes analysis notes, symbols/hooks and a separate DirectInput rendering-mod project.
- **Reuse here:** function names, symbol maps, reverse-engineering notes and behaviour hypotheses as research references, with source-specific license/provenance review.
- **Do not assume:** PC hooks and generated symbols are portable GameCube sources or a complete game engine. The upstream project reports AGPL-3.0; do not copy its code into this project without an explicit compatibility decision.

### SWE1R-Mods / related format tooling
- Repository lead: https://github.com/louriccia/SWE1R-Mods
- Its current branch, license and file-level terms still need verification before relying on it.
- **Reuse here:** only documented file-format knowledge and tooling whose license/provenance is confirmed. Prefer metadata and conversion tools over copying extracted game assets.

## Current implementation status (2026-10-15)

The Step 102 source-only prototype has been imported on the branch associated with PR #22 (`work/step102-import-gate`). The import is no longer a future task. The current branch contains source, tests, tools, data and a Makefile; the import deliberately excludes ROM/disc images and uncleared proprietary media.

Reported automated results on this branch:
- Host regression tests and static source preflight: pass.
- devkitPPC/libogc native build: pass; produces a non-empty `swe1r_gc_port.dol` and ELF.
- Headless Dolphin process smoke: pass only in the limited sense that Dolphin remained active through the configured timeout without a detected fatal boot error.
- Visible in-game frame, controller interaction, complete race and physical-console behavior: **not verified**.
- Source provenance and redistribution rights: **not fully cleared**. A successful build does not resolve licensing or authorship questions.

See [the next-milestone checklist](NEXT_MILESTONE.md) for the current runtime diagnostic and acceptance gates. Treat the PR's current CI evidence—not older README claims—as the source of truth, and re-check the latest Actions run before relying on a status.

## Implementation order

1. **Keep the imported baseline reproducible.** Run the existing host tests before edits, record exact commands/results, and preserve fixtures.
2. **Keep the native build green.** Use the existing devkitPro/libogc workflow and verify the expected DOL/ELF outputs.
3. **Resolve runtime observability.** The current hosted Dolphin/Xvfb visual-capture route has failed even for a known minimal GX control. Diagnose emulator/session startup and capture a real in-game frame in a reliable Dolphin session or on hardware; do not interpret a missing screenshot as proof of a black frame.
4. **Verify one complete vertical slice.** Confirm visible course and pod, camera behavior, steering/throttle/brake/boost, boundaries/collision, rival movement, lap progression, finish state and restart. Record each result separately.
5. **Audit source provenance before merge.** Review ownership/license evidence by file group. Keep unclear material out of the public repository until distribution rights are established.
6. **Only then expand the existing gameplay systems.** Validate race flow before relying on championship progression, time trial, Mirror Cup, unlocks or save/progression scaffolding. These are prototype features until tested end-to-end.
7. **Use community PC research to fill gaps.** Turn findings into short, attributed behavior notes and platform-neutral tests; implement GameCube-specific code independently where architectures differ.

## Import and repository rules

- Do not add ROMs, disc images, BIOS, extracted proprietary textures/models/audio or uncleared PC-mod spline datasets.
- The repository's MIT license does not automatically cover imported third-party files.
- Record provenance/license by imported directory or file; keep unclear material outside the public repository.
- Keep `dreamcast/` separate from the GameCube/Wii milestone.
- Do not treat a clean compile, a live emulator process, or host tests as proof of playable gameplay.
- Keep changes on a review branch; do not bypass protected `main` or merge automatically.

## Acceptance checklist

- [x] Step 102 source-only prototype imported into a review branch and inventoried.
- [ ] Provenance and redistribution rights documented for every imported file group.
- [x] Host regression suite and static preflight pass in the recorded workflow.
- [x] devkitPPC/libogc build creates a non-empty DOL/ELF.
- [x] Limited headless Dolphin process smoke completes without a detected fatal boot error.
- [ ] A non-black in-game frame is captured and reviewed in a reliable emulator/session or on hardware.
- [ ] Controller navigation and driving controls are verified interactively.
- [ ] One race is completed end-to-end, including lap progression, finish and restart.
- [ ] README, milestone docs and PR description report host tests, native build and runtime verification separately.
