# GitHub AI agents — current operating rules

Last reviewed: 2026-10-15

## What is available

The repository has GitHub Actions workflows for:
- **Gemini on-demand review/invocation:** triggered by an authorized issue/PR comment or review beginning with `@gemini-cli`. Read-only review requests have been tested and can post a report back to the PR.
- **Gemini plan/execute:** a separate writer workflow exists, but code-writing is gated by an owner-only `@gemini-cli /approve` request and the repository Actions variable `GEMINI_WRITE_ENABLED=true`. The write path must remain disabled until the owner has deliberately verified main protection, the free-tier API setup, and the variable/secret configuration.
- **Daily project coordination:** scheduled read-only reporting. This is a scheduled workflow, not a permanent agent that independently works on code all day.
- **Deterministic CI failure triage:** summarizes failed workflow job/step metadata; it does not execute PR code or infer a root cause.
- **OpenRouter Free reviewer:** a separate manual, comment-only reviewer is documented in the repository. It requires its own provider key and has no right to merge or write code.

A green AI workflow proves only that the workflow ran and published a response. It does not prove that a code suggestion is correct, that tests passed, or that a game is playable.

## Safe request pattern

Start with a narrowly scoped read-only request:

```text
@gemini-cli Review this PR as read-only. Inspect the diff and tests, report concrete blockers only, and do not modify files, push commits, merge, change repository settings, or enable billing.
```

For substantial changes:
1. Ask for a written plan with acceptance criteria.
2. Keep implementation on a named branch and open a reviewable PR.
3. Review changed files, license/provenance, dependencies, and test commands.
4. Verify the relevant CI checks on the exact PR head before integration.
5. Only the repository owner may choose to enable a writer path; an agent must never approve or merge its own work.

## Current project context

- The active technical milestone is the clean-room procedural GameCube demo in `gamecube-demo/`.
- Host tests, a devkitPPC/libogc build, artifact checks, and a bounded Dolphin headless startup smoke have passed. A CI Software Renderer run captured a visible procedural scene.
- Interactive controller response, a completed three-lap run/restart, long-session stability, and physical hardware behavior remain unverified.
- The Step 102 source archive has not been imported into main. GitHub-hosted agents cannot automatically read files stored only in the ChatGPT conversation/library.
- Research on SW_RACER_RE is Windows-PC reference material, not automatically reusable GameCube/Wii code. Respect its reported AGPL-3.0 license and keep PC observations separate from console assumptions.

## Free-only and data boundaries

- Never attach billing, enter a payment method, or use a paid fallback to keep an agent working.
- If a free quota is unavailable, stop and report the blocker.
- Never send API keys, tokens, personal data, private game archives, ROMs/disc images, BIOS files, or extracted proprietary assets to an external reviewer.
- Do not commit private/commercial game content or files of unclear provenance.
- A source-import or license review must not be skipped just to get a green build.

## Evidence and status language

Always identify the exact commit and run link. Distinguish:
- host regression tests;
- native cross-compilation and artifact validation;
- emulator process smoke;
- visible frame capture;
- interactive controller test;
- complete race with finish/restart;
- longer-session and physical-hardware tests.

Do not report a lower-level check as proof of a higher-level outcome. No agent should push directly to main, delete branches/history, or merge its own code.


## Multi-agent routing — reviewed 2026-10-21

Use [the shared playbook](MULTI_AGENT_RESEARCH_PLAYBOOK.md) as the project-specific handoff contract. Jules previously created [PR #247](https://github.com/Master-Chiken/boonta-reborn-88/pull/247), the sole open steering-deadzone candidate. The overlapping [PR #243](https://github.com/Master-Chiken/boonta-reborn-88/pull/243) and [PR #233](https://github.com/Master-Chiken/boonta-reborn-88/pull/233) are now closed unmerged; preserve them as historical evidence, but do not describe them as open or merged. Do not start another coding task on the same control behavior until #247 is independently reviewed and the required interactive acceptance is recorded. Keep the single RE-001 question active; allow public-source research or read-only falsification only when it has a specific, non-duplicative question. Local N64 ROM analysis stays in the owner's local environment.

### Free-only role selection

- **Jules:** use one bounded task; review its existing PRs before starting another. Jules reads root AGENTS.md automatically according to its documentation: https://jules.google/docs/.
- **Gemini CLI:** request independent review by posting a comment beginning with @gemini-cli. For this RE task, ask for contradictions/unsupported inference only, no files or code changes, no billing, and no merge decisions.
- **Copilot cloud agent:** do not make it part of the default plan; GitHub documents it as available on paid Copilot plans (https://docs.github.com/en/copilot/how-tos/copilot-on-github/use-copilot-agents/kick-off-a-task).
- **OpenRouter Free:** optional and only if the manual reviewer is configured; text opinions cannot substitute for code, emulator or hardware validation.
- **Biddy-Pinky:** human independent review after a single candidate diff and exact-head CI are ready.

Do not add a scheduled coordinator or expand CI for this. The owner already has a manual read-only coordination workflow; the blocker is task routing and duplicate detection, not missing automation.
