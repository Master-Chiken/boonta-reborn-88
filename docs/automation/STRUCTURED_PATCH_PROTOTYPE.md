# Structured patch proposal prototype

**Status: isolated offline prototype; not connected to a live AI provider or production workflow.**

## Purpose

Reduce fragile model-controlled GitHub MCP sequences. The future model contract is one strict JSON patch proposal. Deterministic code validates and applies it in an isolated, clean checkout; ordinary repository tooling—not the model—would later own commits and PR creation.

This prototype performs no network access, inference, branch creation, commit, push, PR creation, merge, arbitrary shell execution, or test execution from model-supplied text.

## Contract

The authoritative schema is emitted by:

\`\`\`bash
python3 tools/autonomous_patch_proposal.py --print-schema
\`\`\`

Required properties:

- \`schema_version\`: integer 1.
- \`task_id\`: exact ID independently supplied by the trusted task preflight.
- \`base_sha\`: exact 40-character base commit SHA independently supplied by preflight.
- \`summary\`: bounded human-readable summary.
- \`unified_diff\`: one bounded UTF-8 unified Git diff.
- \`test_ids\`: identifiers from a fixed allowlist; no command strings, scripts or shell arguments.
- \`limitations\`: up to eight short caveats.

Unknown and duplicate JSON properties are rejected. The model cannot choose or widen the path allowlist: the caller must pass one or more \`--allowed-path\` arguments derived from the approved task's trusted scope.

## Guardrails

The validator rejects:

- wrong task ID or stale base SHA;
- malformed JSON, duplicate keys, unknown fields and unknown test identifiers;
- empty task path allowlist, paths outside that allowlist, path traversal and unsupported/quoted paths;
- changes to \`.github/\`, Git metadata, task-ledger source/summary, agent policy, code owners, credential paths, environment files or key/certificate files;
- binary, mode, rename, copy, submodule, new-file and delete-file changes;
- more than five files, 100 text hunks or 32 KiB of diff;
- untracked files, dirty worktrees, wrong checkout root or checkout HEAD that differs from the trusted base;
- symlink and non-regular tracked targets;
- patches rejected by \`git apply --check --whitespace=error\`.

Only pre-existing regular tracked files can be changed in this first prototype. This is deliberately conservative; support for new files is not allowed until a separate threat-model and test review.

The optional \`--apply\` flag applies the already validated patch to the disposable checkout. It does not stage files or create a commit.

## Offline use

Validation only:

\`\`\`bash
python3 tools/autonomous_patch_proposal.py \
  --repo-root "$PWD" \
  --proposal /tmp/boonta-proposal.json \
  --expected-task-id "TASK-ID-FROM-PREFLIGHT" \
  --expected-base-sha "40_CHAR_SHA_FROM_PREFLIGHT" \
  --allowed-path "gamecube-demo/source/main.c"
\`\`\`

Apply to a disposable clean checkout only:

\`\`\`bash
python3 tools/autonomous_patch_proposal.py \
  --repo-root "$PWD" \
  --proposal /tmp/boonta-proposal.json \
  --expected-task-id "TASK-ID-FROM-PREFLIGHT" \
  --expected-base-sha "40_CHAR_SHA_FROM_PREFLIGHT" \
  --allowed-path "gamecube-demo/source/main.c" \
  --apply
\`\`\`

Regression tests use temporary Git repositories and synthetic source files:

\`\`\`bash
python3 tools/test_autonomous_patch_proposal.py
\`\`\`

## Fixed test dispatcher

The repository-owned registry is listed with:

```bash
python3 tools/run_autonomous_patch_tests.py --list
```

Run the three approved offline checks together:

```bash
python3 tools/run_autonomous_patch_tests.py \
  --repo-root "$PWD" \
  --test-id automation.task_preflight \
  --test-id automation.provider_handoff \
  --test-id automation.task_ledger
```

The model may choose only IDs present in the registry. It cannot pass test arguments or commands. The runner uses argv execution without a shell, strips GitHub/provider secret variables from child environments, caps each test at 120 seconds, and stops after the first failure. Registered scripts and the validator/dispatcher themselves are protected from model-authored patches. No GameCube test ID is offered until a stable, bounded host-test command is confirmed.

## Not implemented yet

- No structured-output provider request or model route is configured.
- No trusted task-to-path allowlist generator exists yet.
- \`test_ids\` are validated identifiers, not yet a command dispatcher; a separate repository-owned dispatcher must map them to fixed commands.
- No build/test stage is wired between patch validation and GitHub writing.
- No deterministic writer, branch lease, PR creator or exact-head report is connected.
- No cross-runtime lock is implemented.

## Promotion criteria

Keep this prototype isolated until all offline tests pass on the exact PR head, reviewers inspect the threat model and path policy, and a provider-independent end-to-end fixture proves: strict JSON response → invalid patch rejection → valid patch application in a disposable checkout → fixed test-ID dispatch → deterministic mock branch/PR metadata. Only then consider a separately reviewed production integration. A failed schema or patch check must never be repaired with an automatic second provider request unless the quota budget explicitly permits it.

No provider invocation, new runtime dependency, secret, billing change or external service is required for the prototype.
