# AI agent workflow

This repository uses GitHub-hosted Gemini for on-demand analysis and code assistance. The primary engineering goal is the native GameCube/Wii prototype; the original PC and Nintendo 64 releases are separate reference targets, and the Dreamcast/KallistiOS sample is a separate experiment.

## Current automation

- `@gemini-cli` comments on an issue or pull request trigger a GitHub Actions job.
- The workflow uses the `GEMINI_API_KEY` repository secret and currently selects `gemini-3.5-flash-lite` for the free-tier trial configuration.
- The Gemini response is published back to the triggering issue/PR. If no response is available, the workflow posts a diagnostic link to the Actions log.
- The reusable workflows keep general shell commands disabled; only the limited tools needed for context and repository reading are enabled in the invoke workflow. The plan-execute workflow has a separately scoped GitHub MCP tool set for file changes and PR creation.
- A successful Gemini workflow means only that the automation ran successfully. It does not prove a game build or runtime test succeeded.

## How to request work

Comment on an issue or pull request starting with `@gemini-cli`. Ask for one well-scoped task and tell the agent which files or behavior to investigate.

For substantial code changes, the intended sequence is:
1. Ask for a plan and acceptance criteria.
2. Review the plan in the GitHub discussion.
3. Approve only the intended work with `@gemini-cli /approve`.
4. Review the proposed diff, test results, provenance risks and any PR before merging.

Never ask the agent to merge its own code or bypass required tests. Start with read-only investigation until the source tree is imported.

## Primary engineering blocker

The repository currently contains the Dreamcast starter but does **not** contain the Step 102 GameCube/Wii source tree. The existing native workflow checks for `Makefile` and `source/` and stops if they are missing. Gemini cannot inspect an archive that exists only in ChatGPT's file library; the required files have to be made available to the repository or to a controlled import process first.

## Safe source-import procedure

1. Keep the original PC archive, Nintendo 64 ROM, and commercial disc images outside the public repository.
2. Inventory the Step 102 archive by file path, type, license/provenance and whether the data is original, generated, placeholder, or copied from a commercial game.
3. Review the route-centerline dataset, sample model/material files, audio samples and any generated data separately. Do not import unclear commercial content merely because it is bundled with source code.
4. Import only cleared source code, headers, Makefile, tests and documentation to a review branch.
5. Run the host tests in CI, then the devkitPPC/libogc build. Keep compile success separate from Dolphin/hardware runtime validation.
6. If code has an incompatible license or source provenance cannot be established, leave it out and record the blocker instead.

## Safety and quality rules

- Never commit or publish ROMs, disc images, BIOS files or unclear commercial assets (models, textures, audio or extracted data).
- Never claim to have inspected a file unless its contents were actually accessible.
- Never invent compiler or test results. Report commands, outcomes and evidence.
- Never disable or weaken tests to obtain a green CI run.
- Prefer small branches and pull requests with an explicit human review before merge.
