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
