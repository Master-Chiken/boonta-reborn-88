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

## Addendum — live inventory refresh, 2026-10-21

This section is an addendum; the original eight-ref table above is a historical snapshot from 2026-10-20 and must not be used for current cleanup decisions. A fresh GitHub branch query returned **14 refs**. A fresh open-PR query returned **9 open PRs** (5 targeting `main`, 4 targeting `dev`). No branch was deleted and no PR was merged as part of this refresh.

### Current remote refs

| Branch | Current head | Notes / safe next step |
|---|---|---|
| `main` | `fa8cee047ae8e74c30c87cd94977c434bb1c7398` | Protected stable base |
| `dev` | `c22bf27e0aca621ea735a85e9fedb92fd1933754` | Protected integration base |
| `archive/branch-heads-20261019` | `a6fd522ed97323d73981dd03aab8dba4753edf49` | Protected recovery snapshot; preserve |
| `docs/branch-audit-20261020` | `bb31ddeafdc793d4a0b992e1fbc23829209cdaa9` | This audit branch / PR #245; refresh only with a dated addendum |
| `docs/project-onboarding-20261021` | `dd29d62896e2aa860c56ff440d34e746b81e9b81` | PR #251; reviewer integration remains unmerged |
| `docs/reuse-inventory-20261020` | `a084a2317f396ab70b1aa2d7fd61654894c61127` | PR #246; reuse inventory only, not vendored code |
| `docs/reverse-engineering-80-20-20261020` | `e860f456a84138d67624746e5d68b1d2adb1bcb1` | PR #242; RE-001 dossier/priority docs |
| `fix/steering-stick-deadzone-14890725910744431762` | `5bc59d178a16ab69899589911665c84ba07eee7c` | PR #247 to `main`; competes with #243/#233 |
| `fix/steering-stick-deadzone-20261019-14221623089412890411` | `0fe5dba576bd823208cd3e9aff9e282b30025c05` | PR #233 to `dev`; includes unrelated cleanup automation; do not merge wholesale |
| `fix/steering-stick-deadzone-clean-20261020` | `6b31321294e8238b836e7d1807c0ef006835f377` | PR #243 to `dev`; focused two-file version |
| `fix/width-aware-rail-collision-20261017` | `db1f9747b8193d6cc4e77e0f69a073cd5e210eb5` | PR #214 to `dev`; visible three-lap manual acceptance still outstanding |
| `jules/re-001-public-source-crosscheck-5621653419986752281` | `de33cca64ce8eeefc3c34260e3d413832b3fd666` | No open PR in the current open-PR query; investigate purpose/dependencies before any retirement |
| `re-001-ares-gdb-smoke-20261021` | `d87e5f509575253f185ed434c022456579f01dc6` | PR #252 to `main`; bounded public-homebrew GDB control, currently NOT PASSED |
| `test/ares-gdb-smoke-20261021` | `fa8cee047ae8e74c30c87cd94977c434bb1c7398` | Points at the current `main` head in this query; likely a test ref, but compare refs/events before proposing any deletion |

### Current open PR queue

| PR | Base | State and outstanding gate |
|---|---|---|
| [#252](https://github.com/Master-Chiken/boonta-reborn-88/pull/252) | `main` | Draft; v139/v148 launch comparison is running after several setup fixes. No valid end-to-end GDB pass yet; RE-001 game-specific transition remains unproven. |
| [#242](https://github.com/Master-Chiken/boonta-reborn-88/pull/242) | `main` | Draft; research dossier. Keep RE-002 parked until RE-001 is resolved or explicitly blocked. |
| [#246](https://github.com/Master-Chiken/boonta-reborn-88/pull/246) | `main` | Open, non-draft; inventory/reference only. Review sources before any reuse/vendor work. |
| [#251](https://github.com/Master-Chiken/boonta-reborn-88/pull/251) | `main` | Draft; guarded OpenRouter Free reviewer, not activated on `main`. |
| [#247](https://github.com/Master-Chiken/boonta-reborn-88/pull/247) | `main` | Open, non-draft; steering deadzone; duplicate implementation with #243/#233 needs consolidation decision. |
| [#233](https://github.com/Master-Chiken/boonta-reborn-88/pull/233) | `dev` | Draft; deadzone plus branch-cleanup workflow (`contents: write`); keep parked and separate the concerns. |
| [#243](https://github.com/Master-Chiken/boonta-reborn-88/pull/243) | `dev` | Open, non-draft; focused deadzone patch. Do not merge alongside equivalent #247/#233. |
| [#214](https://github.com/Master-Chiken/boonta-reborn-88/pull/214) | `dev` | Draft; automated checks are not the same as visible human-driven three-lap Dolphin acceptance in issue #126. |
| [#245](https://github.com/Master-Chiken/boonta-reborn-88/pull/245) | `dev` | Draft; this snapshot refresh. Inventory is updated here but still requires owner review before any branch-retirement decision. |

### Decisions that are still intentionally not made

1. Do not merge duplicate steering deadzone PRs; choose one authoritative scoped change only after review.
2. Do not merge #214 as “visually accepted” without a human-operated race against the exact DOL/head.
3. Do not mark #252 passed from build success or a TCP listener alone; require the actual GDB breakpoint/continue transcript. Even a homebrew tooling pass does not prove the commercial SWE1R finish-to-results path.
4. Do not retire `jules/re-001-public-source-crosscheck-5621653419986752281` or `test/ares-gdb-smoke-20261021` based only on this inventory; compare merge bases, open references, workflow history and unique commits first.

No merges, branch deletion, force-pushes, destructive workflow dispatches, or gameplay code edits were performed by this inventory refresh.

### Follow-up validation refresh — 2026-10-21 14:10 UTC

The remote branch inventory remains **14 refs**, and the live open-PR query remains **9 open PRs**. No refs were retired and no PR was merged.

- **#252 / RE-001:** current head at this refresh is `3df2aedeccaef904c48637710eedc88699db7acb`. Matrix [run #39613630406](https://github.com/Master-Chiken/boonta-reborn-88/actions/runs/39613630406) built Ares v139 and v148, but both runtime cases failed. v139 loaded ctest, initialized paraLLEl-RDP and connected GDB, then hit `SIGTRAP` in `__rsp_check_assert()` before `main`. v148 hit the `main` breakpoint, then stopped at `SIGTRAP` in `joybus_exec()`. The listener and GDB handshake are demonstrated, but a clean bounded continue is **not**. Keep #252 draft and unmerged; do not equate connection success with successful execution.
- **Steering deadzone overlap:** #247 targets `main`, #243 targets `dev`, and #233 also targets `dev`. The changed-code hunk in #247 and #243 is identical for the steering input helper/tests; #233 bundles unrelated branch-cleanup automation with the same idea. Do not merge more than one. #243 is the focused `dev` candidate, but it still needs independent maintainer review and interactive controller-feel acceptance.
- **Other live gates:** #246 is the non-draft documentation-only reuse inventory with green listed CI checks; #242 remains draft research-priority/dossier documentation; #251 remains draft and its OpenRouter Free workflow is not active on `main`; #214 remains draft until visible human-operated three-lap Dolphin acceptance is recorded; #245 remains draft and needs owner review before any cleanup decision.

This addendum is a status snapshot only. It does not authorize branch deletion, force-push, workflow dispatch, or merge.
