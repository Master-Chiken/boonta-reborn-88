# AI agent workflow

This repository has a native GameCube/Wii goal, a separately maintained Dreamcast starter, and on-demand AI review helpers. AI output is advisory; a successful workflow is not proof that game code compiles or works at runtime.

## Current automation status

- **OpenRouter Free reviewer:** merged on main through [PR #14](https://github.com/Master-Chiken/boonta-reborn-88/pull/14). It is triggered manually from GitHub Actions for an open PR targeting main, sends a capped public diff through the openrouter/free route, and posts a review comment. It is comment-only and never writes code or merges. The repository secret OPENROUTER_API_KEY is required to run it; do not add billing or a payment method. Review [its setup guide](OPENROUTER_FREE_REVIEW.md) before sending any diff to an external model provider.
- **Gemini Actions workflows:** workflow files are present on main, but the proposed safety-hardening changes in [PR #15](https://github.com/Master-Chiken/boonta-reborn-88/pull/15) remain a draft. Do not assume the draft's write gate or other proposed controls are active until it is merged.
- **No paid fallback:** free service quota/availability can change. If a provider asks for payment, stop instead of enabling billing or a paid endpoint.

## Primary engineering blocker

The Step 102 GameCube/Wii source prototype is a separate supplied archive; it has not been imported to main. The clean-room procedural demo in [PR #13](https://github.com/Master-Chiken/boonta-reborn-88/pull/13) is a different workstream and does not replace or compile the Step 102 source. GitHub-hosted agents cannot read a ChatGPT attachment unless the relevant material is separately and safely made available to them.

## Safe workflow for substantial changes

1. Ask for a read-only assessment and a concrete plan with acceptance criteria.
2. Review the proposed plan and check whether it concerns main, the Step 102 source, the GameCube demo PR, or the Dreamcast experiment.
3. Keep work in a dedicated branch and reviewable pull request; never write directly to main or allow an agent to merge its own changes.
4. Inspect the diff, tests, dependency changes, and source/asset provenance before approval.
5. Confirm actual test/build evidence from the linked Actions run. Do not rely only on a natural-language report from an agent.
6. Keep commercial ROMs, disc images, BIOS files, private game archives, extracted proprietary assets, API keys, and personal data out of prompts and repository changes.

## Safe Step 102 import process

1. Inventory every archive path with file type, origin, license evidence, and redistribution decision.
2. Review generated route data and sample models/materials/audio separately; do not treat inclusion in a source ZIP as proof of permission.
3. Import only cleared source code, headers, build scripts, tests, and documentation.
4. Run host tests first, then the native devkitPPC/libogc build.
5. Test the resulting DOL interactively and record visual, controller, and gameplay results separately.
6. Exclude files with unclear provenance or incompatible licenses and document what is missing.

## Quality and security rules

- Never claim to have inspected an attachment unless its contents were accessible.
- Never invent compiler/test results or claim that a build is playable without runtime evidence.
- Never disable or weaken tests to obtain a green CI run.
- Never publish commercial game payloads or undocumented third-party assets.
- Never expose secrets in issues, logs, PR diffs, or AI prompts.
