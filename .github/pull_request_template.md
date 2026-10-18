## Required pre-flight

- [ ] I read [AGENTS.md](../AGENTS.md) and followed the project-wide pre-flight rules.
- [ ] I checked current source/tests, relevant issues, and open PRs/branches to avoid duplicating existing work.
- [ ] This change advances a concrete project milestone; its scope is the smallest useful change.
- [ ] Platform/file-format assumptions and license/provenance risks have been checked; no uncleared assets or commercial game data are included.
- [ ] Acceptance criteria and validation steps were identified before implementation.

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


## Independent review (required)

- [ ] A contributor other than the author reviewed the actual diff; link or identify the review.
- [ ] Reviewer checked the implementation and whether tests genuinely exercise the changed behavior, including relevant edge/boundary cases.
- [ ] AI-generated summaries or test claims were verified against the source diff, actual CI results, and available evidence.
- [ ] Any blocking review feedback is resolved; no material code change was made after approval without revalidation.
- [ ] Unknowns and unrun checks are explicitly marked NOT VERIFIED; no claim exceeds the evidence.

If no independent reviewer or required runtime evidence is available, leave the PR unmerged and state what is blocking acceptance.

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
