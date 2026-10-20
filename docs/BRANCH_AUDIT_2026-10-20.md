# Branch audit — 2026-10-20

## Purpose and safety boundary

Current-state snapshot for review and cleanup planning. This document does not authorize merges, branch deletions, force-pushes, or workflow dispatches. No such actions were performed.

## Current remote refs

A fresh branch search returned 8 refs:

| Branch | Known role | Safe next step |
|---|---|---|
| `main` | Stable base | Protect |
| `dev` | Gameplay integration base for #214 and #243 | Protect |
| `archive/branch-heads-20261019` | Recovery snapshot | Preserve until recovery value is verified |
| `docs/branch-audit-20261020` | This audit; latest audit commit before this refresh: `f6bf3941cd65dc69989a1235b68a1ec568baeb51` | Keep while PR #245 is open |
| `docs/reverse-engineering-80-20-20261020` | PR #242 | Keep; draft/review pending |
| `fix/steering-stick-deadzone-20261019-14221623089412890411` | Legacy combined deadzone + cleanup workflow work; previously compared as 16 ahead / 1 behind dev | Do not merge wholesale; cleanup workflow needs separate security review |
| `fix/steering-stick-deadzone-clean-20261020` | Focused deadzone change; two gameplay/test files | Keep while #243 is under review |
| `fix/width-aware-rail-collision-20261017` | Rail collision, tests, Dolphin diagnostics, docs, workflow changes | Keep while #214 is under review |

The older 27-ref inventory in issue #235 is stale. The earlier 6-ref count is also stale. Do not delete branches based on either snapshot; compare unique commits and dependencies immediately before any proposed retirement.

## PR gates — live metadata checked 2026-10-20 20:40 CEST

### #214 — Fix track-width-aware rail collision alignment

- Open, draft, targets `dev`; head `db1f9747b8193d6cc4e77e0f69a073cd5e210eb5`; 10 files changed.
- Exact-head workflow run [39327379050](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39327379050) completed with four successful jobs: host pause/resume and gameplay tests, native GameCube DOL/ELF build, Dolphin headless smoke, and non-blocking software-renderer diagnostic.
- The patch is broader than gameplay code: it also changes the shared `.github/workflows/gamecube-demo-build.yml`, Dolphin diagnostic tooling and documentation. Independent review must include these workflow changes.
- No review submission or inline review thread was returned by the latest review queries.
- Human acceptance is outstanding in [issue #126](https://github.com/Master-Chiken/boonta-reborn-88/issues/126). The person testing must run the DOL built from this exact SHA in visible Dolphin and record PASS/FAIL/NOT TESTED for reset, acceleration/braking/coasting, analog/D-pad steering, rail/edge behavior, boost/overheat, pause/resume, three laps/finish, restart, and several minutes of stability. CI, a build, and headless smoke do not substitute for this.

### #243 — fix: filter analog steering deadzone

- Open, draft, targets `dev`; head `6b31321294e8238b836e7d1807c0ef006835f377`; two files changed.
- Patch remains scoped to `gamecube-demo/source/gameplay_state.h` and `gamecube-demo/tests/test_gameplay_state.c`.
- Previous head `d1c5bf755a587765908a152fbf8874231bf6fe75` had four successful jobs in run [39459255221](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39459255221). The new head adds explicit tests for the inclusive ±16 deadzone boundary and ±17 first nonzero values (commit `6b31321294e8238b836e7d1807c0ef006835f377`). The commit-run query returned no runs for this new SHA at the time of the audit; recheck PR Checks before claiming CI green.
- No review submission or inline review thread was returned. Controller-feel/interactive acceptance remains outstanding.
- Do not revive or merge the older combined #233 branch; its cleanup workflow changes are unrelated and require separate security review.

### #242 — docs: make reverse engineering the 80/20 priority

- Open, draft, targets `main`; live head `92e82dfc9c246663d9301ea666602b20b1f6bbdf`; 15 files changed. Its history is broad; do not change its base casually.
- Exact-head [Step 102 source-import provenance guard](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39476180227) and [AI free-tier safety checks](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39476180096) both completed successfully.
- The separate `source-import-trusted-path-guard.yml` workflow is configured for `pull_request_target` on PRs targeting `main`. The available commit-run connector filters to `pull_request` events, so its omission from that query does not establish failure or absence. Verify the actual run in the [workflow's Actions page](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/source-import-trusted-path-guard.yml) before claiming every required check is green. Do not dispatch a duplicate run just to fill this evidence gap.
- No review submission or inline review thread was returned. The owner must review the documentation/research claims and decide whether to merge.

### #245 — docs: record branch audit and safe cleanup gates

- Open, draft, targets `dev`; latest verified head before this refresh was `f6bf3941cd65dc69989a1235b68a1ec568baeb51`.
- Documentation-only audit; no branch operations were performed.

## Next actions — in order

1. **Close the evidence gap for #242:** inspect the [trusted-path workflow runs](https://github.com/Master-Chiken/boonta-reborn-88/actions/workflows/source-import-trusted-path-guard.yml) for the current PR/head and record its actual result.
2. **Finish #214 acceptance:** obtain independent review and have a person complete issue #126 in visible Dolphin against the exact DOL/head. Do not mark the manual gate passed without that evidence.
3. **Then #243:** obtain review and interactive controller-feel acceptance; preserve its two-file scope.

## Provenance and scope rules

- Current automated success is evidence only for the exact commit and workflow run cited.
- PC reverse-engineering observations do not prove GameCube behavior. Step 102 source import must be assessed file-by-file for provenance/licensing; the candidate archive was not available in the connected workspace during the documented RE-001 pass, so no Step 102 source correspondence is claimed.
- Keep the stated project priority: 80% reverse engineering, 20% everything else; one active RE question at a time.
- Never merge #233 wholesale. Never enable or run destructive branch-retirement automation without independent review, explicit owner approval, and a verified checkpoint.
- No merge, branch deletion, force-push, or manual workflow dispatch was performed in this audit refresh.


## Evidence update — 2026-10-20: scripted Dolphin artifact inspected

- On current #214 head `db1f9747b8193d6cc4e77e0f69a073cd5e210eb5`, workflow [39327379050](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39327379050) completed all four jobs successfully. Its software-renderer diagnostic artifact [12223576295](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39327379050/artifacts/12223576295) includes scripted left/right frames, reset/pause/resume captures, finish/reset detector outputs, and a full-race DTM/log set. The job log shows the built DOL was booted and the artifact uploaded.
- This strengthens automated evidence, but does not satisfy human interactive acceptance: controller/keyboard feel, driving behavior, and full manual three-lap completion/stability remain unverified by a human. Issue #126 has been updated with this exact-head evidence and the explicit distinction.
- The exact-head visible workflows for #242 remain successful (runs `39476180227` and `39476180096`); the separate `pull_request_target` guard run still needs confirmation via its Actions page.


### Latest PR #243 test update — 2026-10-20 20:47 CEST

- Focused branch advanced to `6b31321294e8238b836e7d1807c0ef006835f377`; PR still changes exactly two files: `gamecube-demo/source/gameplay_state.h` and `gamecube-demo/tests/test_gameplay_state.c`.
- Added explicit tests for the deadzone boundary at +16/-16 and first values outside it at +17/-17. Workflow run [39477710458](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39477710458) subsequently completed successfully. Human controller-feel acceptance and independent review remain open.


### Latest verification — 2026-10-20 20:52 CEST

- Refreshed live PR metadata: #214 remains draft on `db1f9747b8193d6cc4e77e0f69a073cd5e210eb5`; #243 remains draft on `6b31321294e8238b836e7d1807c0ef006835f377`; #242 remains draft on `92e82dfc9c246663d9301ea666602b20b1f6bbdf`. No submitted reviews are present for any of the three.
- #243 exact-head workflow `39477710458` completed successfully. The test boundary addition is now covered by green CI, but manual controller-feel validation and independent review are still open.
- Branch inventory remains eight refs. No deletions, merges, force pushes, or manual workflow dispatches were performed.
