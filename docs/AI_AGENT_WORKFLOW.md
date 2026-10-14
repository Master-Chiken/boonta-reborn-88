# AI agent workflow

This repository is designed for AI-assisted development with human approval at important checkpoints.

## Current automation

- GitHub Actions builds the Dreamcast KallistiOS starter when relevant files change and on manual dispatch.
- The workflow uploads the ELF as an artifact only when compilation succeeds.
- Build success proves compilation only; it does not prove the ELF runs in an emulator or on hardware.
- Repository-specific coding guidance lives in `.github/copilot-instructions.md`.

## Recommended agent loop

1. **Planner** — select one small task from `docs/PROJECT_PLAN.md` and define acceptance criteria.
2. **Coding agent** — implement the task in a branch and open a pull request. Prefer GitHub Copilot coding agent if it is enabled for this account/repository; another coding agent may be used if it can work directly with the GitHub repo.
3. **CI** — let GitHub Actions build the changed Dreamcast code.
4. **Reviewer** — inspect the diff, build logs, API choices, scope, and license/provenance risks.
5. **Human approval** — merge only after reviewing the pull request and the checks. Do not grant an agent permission to merge its own changes.
6. **Next task** — update the project plan and issue only after the previous task has evidence-backed results.

## First task

Use the existing issue: [Dreamcast: add a visible video-mode smoke test](https://github.com/Master-Chiken/boonta-reborn-88/issues/4).

If GitHub Copilot coding agent is enabled:
1. Open the issue.
2. Use the issue's **Assignees** control to select **Copilot** (the exact label may vary by GitHub UI).
3. Start the agent task and allow it to open a pull request.
4. Review the pull request and CI result before merging.

If Copilot is not offered in the Assignees control, it is not currently available to this repository/account or requires setup. Do not create personal access tokens or paste secrets into an issue to work around this.

## Agent safety rules

- Never commit ROMs, disc images, BIOS files, extracted proprietary assets, or copyrighted game data.
- Never claim emulator or hardware support without actual runtime evidence.
- Never disable or weaken CI just to get a green result.
- Keep changes small and reviewable; prefer a pull request over direct commits to `main`.
- Do not expose secrets in logs, prompts, issue comments, or commits.
- Do not automatically merge agent-generated pull requests.
- If toolchain APIs are uncertain, inspect the existing code and official KallistiOS documentation before implementing.

## Later automation options

After the first agent-produced pull request has been reviewed successfully, consider adding:
- automatic issue triage and labels;
- CI summaries on pull requests;
- dependency and secret scanning;
- scheduled project-status summaries;
- a second review agent that comments on pull requests.

Do not add an autonomous workflow that executes arbitrary code from untrusted issues or merges changes without review.
