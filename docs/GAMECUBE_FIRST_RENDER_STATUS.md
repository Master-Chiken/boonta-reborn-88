# GameCube prototype status

Last updated: 2026-10-16

## Current mainline

- **Current main commit:** `73cc2e1a1018af0e6c14df7e9aec7023d005e7ea` — merge commit for PR #161.
- **Latest post-merge CI:** [GameCube first-render prototype run #38902484737](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/38902484737) completed successfully on this exact commit.
- **Host regression tests:** passed, including the multi-frame rival-contact test added in PR #161.
- **Native build:** `boonta_gc_demo.dol` / `.elf` built successfully with devkitPPC/libogc.
- **Dolphin headless smoke:** passed. This confirms bounded startup/process behavior, not live controller response.
- **Software Renderer diagnostic:** passed. This confirms the scripted frame/render checks, not manual playability.
- **Branch inventory:** 78 branch references were visible in the GitHub API on 2026-10-16. This is a snapshot, not a cleanup target by itself; do not delete branches automatically.
- **Recent regression coverage:** finite-state guards, 50/60 Hz cadence, steering inertia, boost/overheat, lap boundaries, pause/reset, off-road/rail response, rival events and multi-frame rival collisions.

## Still pending — interactive acceptance

The prototype has **not** yet been declared fully playable. A person still needs to test the current mainline DOL in a visible Dolphin session with a configured controller and record the evidence described in [`NEXT_MILESTONE.md`](NEXT_MILESTONE.md).

Pending acceptance items:

- [ ] Scene starts without fatal error in a visible Dolphin session.
- [ ] Reset (Y) returns all race state to a clean start.
- [ ] Acceleration/brake (A/B) and coasting behave correctly.
- [ ] Stick and D-pad steering respond in the expected direction; inertia damps safely.
- [ ] Off-road slowdown and rail recovery work without freezing.
- [ ] Boost (X+A), energy recharge and overheat lockout behave correctly.
- [ ] Start pauses/resumes; reset while paused is clean.
- [ ] A live three-lap race reaches the finish, stops, and can be reset.
- [ ] Several minutes of play show no crash or sustained corruption.
- [ ] Dolphin version, video backend/mode, controller profile and screenshots/video + notes are recorded.

A CI-generated DTM or a rendered frame is useful evidence, but does not replace this interactive checklist. Dolphin results do not establish compatibility with physical GameCube/Wii hardware.

## Next engineering priorities

1. Run the interactive acceptance checklist and turn every reproducible failure into a regression test.
2. Fix any confirmed input, race-finish/reset, camera or collision defects.
3. Improve track/camera/collision feel as one coherent playable vertical slice before adding more content.
4. Continue branch intake by reviewing unique diffs against current `main`; do not merge stale branch histories wholesale or delete branch refs automatically.

## Restricted parallel track: Step 102

Step 102 source/archive imports remain on **provenance and licensing hold**. Keep this separate from the clean-room runtime. Do not merge uncertain source or commercial assets until origin, authorship and redistribution rights have been established.
