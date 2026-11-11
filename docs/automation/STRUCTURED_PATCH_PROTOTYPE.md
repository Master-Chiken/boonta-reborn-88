# Structured patch and deterministic delivery pipeline

**Status:** the offline proposal validator, fixed test runner, isolated verifier and deterministic delivery planner are implemented. A separate GitHub writer is present but opt-in and draft-only. No AI provider or scheduled production workflow invokes this pipeline.

The canonical task ledger currently has no active task (two blocked tasks remain), and the owner-reviewed path policy is empty. Therefore the current repository state grants **zero model write paths** and cannot produce a deliverable plan.

## Architecture

1. **Trusted task and path scope.** \`tools/build_autonomous_path_allowlist.py\` reads the canonical schema-v2 task summary and \`docs/automation/patch-path-allowlist.json\`. It grants exact paths only to the unique active task when an explicit owner-reviewed policy entry exists. Paths must be existing regular tracked files. No globs, prefixes or model-selected paths are accepted.
2. **Strict proposal.** \`tools/autonomous_patch_proposal.py\` accepts a bounded JSON contract containing task ID, exact base SHA, summary, unified diff, fixed test IDs and limitations. Duplicate/unknown fields, stale identities, unsafe paths, credentials, symlinks, binary changes, oversized patches and unapproved tests are rejected.
3. **Isolated verification.** \`tools/verify_autonomous_patch.py\` creates a detached temporary Git worktree, applies the patch there and runs all mandatory checks plus requested registered tests. It verifies that tests did not alter approved output files, stage files, create commits, or leave unexpected files. The original source checkout remains unchanged.
4. **Deterministic plan.** \`tools/build_autonomous_delivery_plan.py\` revalidates canonical task and path policy, every test result, and the exact file bundle. It derives the branch name, commit message, PR title/body and task marker without asking the model to choose them.
5. **Guarded GitHub writer.** \`tools/execute_autonomous_github_delivery.py\` revalidates the plan and its source evidence again, then—only in explicit execution mode—creates a Git tree, one-parent commit, new branch ref and **draft PR**. It never force-updates a branch, merges a PR or enables auto-merge.

## Fixed test registry

The model can request only identifiers from this repository-owned registry:

- \`automation.task_preflight\`
- \`automation.provider_handoff\`
- \`automation.task_ledger\`

The isolated verifier always runs all three mandatory checks. The dispatcher uses argv execution without a shell, does not pass GitHub/provider secrets to child processes, uses non-interactive stdin, has a 120-second per-test timeout, and stops on first failure. No GameCube test ID is offered until a stable, bounded host-test command is verified.

List available test IDs:

\`\`\`bash
python3 tools/run_autonomous_patch_tests.py --list
\`\`\`

## Offline verification commands

Run the relevant synthetic regression suites:

\`\`\`bash
python3 tools/test_autonomous_patch_proposal.py
python3 tools/test_autonomous_patch_test_runner.py
python3 tools/test_autonomous_path_allowlist.py
python3 tools/test_verify_autonomous_patch.py
python3 tools/test_autonomous_delivery_plan.py
python3 tools/test_execute_autonomous_github_delivery.py
\`\`\`

The GitHub writer tests use a mocked API. They do not create remote refs, commits or PRs.

## Deterministic GitHub writer

The writer is **dry-run by default**. Without \`--execute\`, it revalidates the plan and prints \`DRY_RUN_VALIDATED\`; it does not call the GitHub API.

Live draft-PR creation additionally requires all of the following:

- the explicit \`--execute\` argument;
- \`BOONTA_DETERMINISTIC_DELIVERY_ENABLED=true\`;
- \`BOONTA_DETERMINISTIC_DELIVERY_OWNER_APPROVED=true\`;
- a \`GITHUB_TOKEN\` with the repository permissions needed to create Git trees, commits, refs and draft PRs;
- the exact task/base/path policy and verified report still passing revalidation.

A typical dry-run invocation is:

\`\`\`bash
python3 tools/execute_autonomous_github_delivery.py \
  --repo-root "$PWD" \
  --repository "Master-Chiken/boonta-reborn-88" \
  --plan /tmp/boonta-delivery-plan.json \
  --verified-report /tmp/boonta-verified.json \
  --allowlist-report /tmp/boonta-allowlist.json \
  --expected-task-id "$TASK_ID_FROM_PREFLIGHT" \
  --expected-base-sha "$BASE_SHA_FROM_PREFLIGHT"
\`\`\`

Adding \`--execute\` without both exact-true gates fails closed before any GitHub request. Successful execution creates only a draft PR. The writer checks that the target branch still equals the verified base SHA, the deterministic branch does not already exist, and no open PR already carries the task marker. It rechecks the base branch and open task PR immediately before opening the draft. A partial failure after ref creation leaves the branch for human reconciliation; the writer does not overwrite or delete it.

The writer is a separately callable tool. It is **not** invoked by Gemini, OpenRouter, Groq, Paperclip or the scheduled autonomous loop. No live writer execution has been performed as part of this prototype.

## Current operating constraints

- The canonical task ledger has 11 records: 9 completed and 2 blocked, with no active task.
- \`docs/automation/patch-path-allowlist.json\` has an empty \`tasks\` array.
- The workflow self-test explicitly asserts that an empty canonical queue returns \`NO_ACTIVE_TASK\` with an empty allowed-path list.
- No task has been activated and no owner-reviewed path scope has been added by this PR.
- No provider route, secret, billing option, GitHub App permission, branch protection rule or production schedule is changed.
- No auto-merge is enabled. Normal independent PR review and branch rules remain mandatory.
- A cross-runtime lease/lock and production provider integration are not implemented.

## Promotion requirements

Before any production integration, a separately reviewed change must provide a concrete active task and exact approved file list, and the full provider-independent path must prove: strict proposal → scope validation → disposable patch application → mandatory tests → integrity-checked bundle → revalidated delivery plan → mocked draft-PR write. Only after that should a separate owner-authorized change connect a provider and the scheduled loop. The two writer execution gates must remain disabled until that decision is made.

No paid service or new runtime package is required by this implementation.
