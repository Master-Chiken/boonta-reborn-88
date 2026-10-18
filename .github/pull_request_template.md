## Required pre-flight

- [ ] I read [AGENTS.md](../AGENTS.md) and followed the project-wide pre-flight rules.
- [ ] I checked current source/tests, relevant issues, and open PRs/branches to avoid duplicating existing work.
- [ ] This change advances a concrete project milestone; its scope is the smallest useful change.
- [ ] Platform/file-format assumptions and license/provenance risks have been checked; no uncleared assets or commercial game data are included.
- [ ] Acceptance criteria and validation steps were identified before implementation.

## Reuse-first review (required)

- [ ] Existing Boonta code, tools, tests, related branches/PRs and upstream/community solutions were checked before creating anything new.
- [ ] The PR reuses existing work where suitable, or explains the specific missing capability that requires new code.
- [ ] Any external code/tool is checked for exact target/format compatibility, revision, license, provenance, dependencies and test evidence.
- [ ] Any adapter or new implementation is the smallest change that closes the demonstrated gap; synthetic fixtures are not presented as original game data.

## Engineering order

- [ ] **Make it work:** The smallest end-to-end behavior meets stated acceptance criteria and relevant correctness tests run.
- [ ] **Make it good:** Maintainability, edge cases, errors, scope, and user/developer experience were reviewed without overengineering.
- [ ] **Make it fast:** Performance work (if any) is based on measurement/profile and has before/after evidence where practical; otherwise no speculative optimization was added.

The same standard applies to every author and reviewer, explicitly including Master-Chiken and Biddy-Pinky, as well as AI-assisted changes. No role or urgency-based exceptions.

If a stage was already satisfied or is not applicable, briefly explain why rather than checking it mechanically.

## Change summary

**Problem / goal:**


**Scope and non-goals:**


**Why this advances the playable vertical slice:**


## Validation evidence

**Checks run (include links to CI runs/artifacts where possible):**


**Manual/runtime checks completed:**


**Not tested / limitations / unresolved risks:**


## Integration

- [ ] Diff reviewed against current `main`; no unrelated changes or accidental generated/proprietary payloads.
- [ ] Regression tests added or updated for any reproduced bug.
- [ ] Documentation/status updated if project state or acceptance status changed.
- [ ] Claims distinguish host tests, native build, Dolphin headless smoke, scripted visible diagnostics, manual controller play, and physical hardware.

**Next smallest step:** 
