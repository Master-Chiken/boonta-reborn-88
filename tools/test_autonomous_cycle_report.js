'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { validateAutonomousCycleReport, findBlockedReportContradictions, REQUIRED_CHECKS } = require('./validate_autonomous_cycle_report');

const owner = 'Master-Chiken';
const repo = 'boonta-reborn-88';
const taskId = 'AUTOMATION-LEDGER-ACTIVATION';
const head = 'a'.repeat(40);
const snapshotAt = new Date(Date.now() - 60_000).toISOString();
const context = { repo: { owner, repo } };

const missingOpenRouterKeyClaim = 'The provider blocker says no provider key was available in this invocation.';
assert.equal(
  findBlockedReportContradictions(missingOpenRouterKeyClaim, { openRouterAuthSucceeded: true }).length,
  1,
  'same-run successful OpenRouter authentication must reject a natural-language missing-key claim'
);
const missingGitHubTokenClaim = 'There is no verified live GitHub App token to drive the request.';
assert.equal(
  findBlockedReportContradictions(missingGitHubTokenClaim, { githubAppTokenMinted: true }).length,
  1,
  'same-run successful GitHub App token creation must reject a natural-language missing-token claim'
);
assert.equal(
  findBlockedReportContradictions('The provider key is intentionally not exposed to the model.', { openRouterAuthSucceeded: true }).length,
  0,
  'do not confuse credential isolation from the model with missing workflow authentication'
);
assert.equal(
  findBlockedReportContradictions(missingOpenRouterKeyClaim, { openRouterAuthSucceeded: false }).length,
  0,
  'do not reject the same claim when successful authentication evidence is absent'
);

function report(status = 'PROGRESS', base = 'main', task = taskId, nextAction = 'Record the verified owner result in the task ledger.') {
  if (status === 'BLOCKED') {
    return [
      'BOONTA_CYCLE_TASK_ID: ' + task,
      'BOONTA_CYCLE_STATUS: BLOCKED',
      'BOONTA_CYCLE_BLOCKER: Owner must verify the external toolchain account.',
      'BOONTA_CYCLE_NEXT_ACTION: ' + nextAction
    ].join('\n');
  }
  return [
    'BOONTA_CYCLE_TASK_ID: ' + task,
    'BOONTA_CYCLE_STATUS: PROGRESS',
    'BOONTA_CYCLE_EVIDENCE: https://github.com/' + owner + '/' + repo + '/pull/501 @ ' + head,
    'BOONTA_CYCLE_EVIDENCE_BASE: ' + base
  ].join('\n');
}

function makeCore() {
  const outputs = {};
  let failure = '';
  return {
    outputs,
    get failure() { return failure; },
    setOutput: (key, value) => { outputs[key] = String(value); },
    setFailed: (message) => { failure = String(message); },
    info: () => {}
  };
}

async function executeOpenRouterBlockedStep(blocker, nextAction, envOverrides = {}) {
  const workflow = fs.readFileSync('.github/workflows/openrouter-plan-execute.yml', 'utf8');
  const stepStart = workflow.indexOf('      - name: Validate OpenRouter autonomous cycle report\n');
  const stepEnd = workflow.indexOf('      - name: Sync the single-task daily backoff marker\n', stepStart);
  assert.ok(stepStart >= 0 && stepEnd > stepStart, 'OpenRouter validation step must exist');
  const step = workflow.slice(stepStart, stepEnd);
  const marker = '          script: |\n';
  const markerIndex = step.indexOf(marker);
  assert.ok(markerIndex >= 0, 'OpenRouter validation step must contain an embedded script');

  const scriptLines = step.slice(markerIndex + marker.length).split(/\r?\n/);
  const script = [];
  for (const line of scriptLines) {
    if (line.trim() === '') {
      script.push('');
      continue;
    }
    if (!line.startsWith('            ')) break;
    script.push(line.slice(12));
  }
  assert.ok(script.some((line) => line.includes('findBlockedReportContradictions')),
    'embedded OpenRouter script must exercise the shared contradiction guard');

  const env = {
    REPORT_PATH: 'report.txt',
    PRE_CYCLE_PR_HEADS: '{}',
    PRE_CYCLE_PR_SNAPSHOT_AT: new Date(Date.now() - 1000).toISOString(),
    OPENROUTER_PREFLIGHT_ALLOWED: 'true',
    OPENROUTER_AUTH_OUTCOME: 'success',
    GITHUB_APP_TOKEN_OUTCOME: 'success',
    SELECTED_TASK_ID: taskId,
    SELECTED_TASK_TARGET_BRANCH: 'main',
    GITHUB_WORKSPACE: 'repo-root',
    ...envOverrides
  };
  const machineReport = [
    'BOONTA_CYCLE_TASK_ID: ' + taskId,
    'BOONTA_CYCLE_STATUS: BLOCKED',
    'BOONTA_CYCLE_BLOCKER: ' + blocker,
    'BOONTA_CYCLE_NEXT_ACTION: ' + nextAction
  ].join('\n');
  const fakeFs = {
    readFileSync: (path, encoding) => {
      assert.equal(path, env.REPORT_PATH);
      assert.equal(encoding, 'utf8');
      return machineReport;
    }
  };
  const testCore = makeCore();
  const runtime = {
    require: (id) => {
      if (id === 'fs') return fakeFs;
      if (id === env.GITHUB_WORKSPACE + '/tools/validate_autonomous_cycle_report.js') {
        return require('./validate_autonomous_cycle_report');
      }
      throw new Error('Unexpected module requested by embedded OpenRouter validator: ' + id);
    },
    process: { env },
    core: testCore,
    github: {},
    context
  };
  const wrapped = '(async function () {\n' + script.join('\n') + '\n})()';
  await new vm.Script(wrapped, { filename: 'openrouter-blocked-validator.js' })
    .runInNewContext(runtime, { timeout: 1000 });
  return testCore;
}

function makeGithub(options = {}) {
  const previousHead = options.previousHead || 'b'.repeat(40);
  const pr = {
    number: 501,
    state: 'open',
    merged_at: null,
    draft: false,
    created_at: new Date(Date.now() - 30_000).toISOString(),
    changed_files: 2,
    body: 'Research result\nBOONTA_TASK_ID: ' + taskId + '\nBOONTA_TASK_TARGET_BRANCH: ' + (options.base || 'main') + '\n',
    head: { sha: head, repo: { full_name: owner + '/' + repo } },
    base: { ref: options.base || 'main', repo: { full_name: owner + '/' + repo } }
  };
  const successful = (REQUIRED_CHECKS[options.base || 'main'] || REQUIRED_CHECKS.main)
    .map((name, index) => ({
      name, head_sha: head, status: 'completed', conclusion: 'success',
      app: { slug: 'github-actions' },
      created_at: new Date(Date.now() - 1_000 + index).toISOString()
    }));
  let polls = 0;
  let prFetches = 0;
  const github = {
    rest: {
      pulls: {
        get: async () => {
          const sequence = options.prSequence || [options.pr || pr];
          const current = sequence[Math.min(prFetches, sequence.length - 1)];
          prFetches += 1;
          return { data: current };
        }
      },
      repos: {
        getCommit: async ({ ref }) => {
          if (ref === previousHead) {
            return {
              data: {
                sha: previousHead,
                commit: { tree: { sha: options.previousTreeSha || 'tree-before' } }
              }
            };
          }
          return {
            data: {
              sha: options.commitSha || head,
              commit: {
                tree: { sha: options.treeSha || 'tree-after' },
                committer: {
                  date: options.committerDate || new Date(Date.now() - 5_000).toISOString()
                }
              }
            }
          };
        }
      },
      checks: {
        listForRef: async () => {
          polls += 1;
          const list = options.checkRunsByPoll
            ? options.checkRunsByPoll[Math.min(polls - 1, options.checkRunsByPoll.length - 1)]
            : successful;
          return { data: { check_runs: list || [] } };
        }
      }
    }
  };
  return { github, get polls() { return polls; }, pr };
}

async function run(name, options = {}) {
  const core = makeCore();
  const fixture = makeGithub(options);
  await validateAutonomousCycleReport({
    github: fixture.github,
    context,
    core,
    summary: options.summary || report(options.status || 'PROGRESS', options.reportBase || options.base || 'main', options.reportTaskId || taskId, options.reportNextAction),
    baseline: options.baseline || {},
    snapshotAt: options.snapshotAt || snapshotAt,
    expectedTaskId: options.expectedTaskId || taskId,
    expectedBase: options.expectedBase || options.base || 'main',
    provider: 'Offline test',
    maxPolls: options.maxPolls || 2,
    pollIntervalMs: 0,
    sleep: async () => {}
  });
  if (options.expectFailure) {
    assert.ok(core.failure.includes(options.expectFailure), name + ': failure should contain ' + options.expectFailure + ', got ' + core.failure);
  } else {
    assert.equal(core.failure, '', name + ': unexpected failure ' + core.failure);
  }
  return { core, fixture };
}

(async () => {
  const openRouterMissingKey = await executeOpenRouterBlockedStep(
    'No provider key was available in this invocation.',
    'Record the verified dependency and next step.'
  );
  assert.ok(openRouterMissingKey.failure.includes('contradicts same-run preflight evidence'),
    'the actual embedded OpenRouter BLOCKED script must reject a missing-key claim after successful authentication');

  const openRouterMissingToken = await executeOpenRouterBlockedStep(
    'There is no verified live GitHub App token.',
    'Record the verified dependency and next step.'
  );
  assert.ok(openRouterMissingToken.failure.includes('contradicts same-run preflight evidence'),
    'the actual embedded OpenRouter BLOCKED script must reject a missing-token claim after successful App token creation');

  const openRouterCredentialIsolation = await executeOpenRouterBlockedStep(
    'The provider key is intentionally not exposed to the model.',
    'Record the verified owner result in the task ledger.'
  );
  assert.equal(openRouterCredentialIsolation.failure, '',
    'the actual embedded OpenRouter BLOCKED script must not confuse model credential isolation with missing workflow authentication');
  assert.equal(openRouterCredentialIsolation.outputs.cycle_status, 'blocked');

  const valid = await run('new main PR with exact checks');
  assert.equal(valid.core.outputs.cycle_status, 'progress');
  assert.equal(valid.core.outputs.evidence_pr_number, '501');

  await run('task mismatch', { reportTaskId: 'AUTOMATION-OTHER', expectFailure: 'task ID' });
  await run('duplicate status fields', {
    summary: report() + '\nBOONTA_CYCLE_STATUS: BLOCKED',
    expectFailure: 'exactly one valid'
  });
  await run('duplicate PR evidence fields', {
    summary: report() + '\n' + report().split('\n').find((line) => line.startsWith('BOONTA_CYCLE_EVIDENCE:')),
    expectFailure: 'exact same-repository PR/head'
  });
  await run('declared base differs from reservation', { reportBase: 'dev', expectedBase: 'main', expectFailure: 'reserved target branch' });
  await run('PR body missing task marker', { pr: { ...makeGithub().pr, body: 'Some PR body' }, expectFailure: 'tied to the reserved task' });
  await run('duplicate PR task markers', {
    pr: { ...makeGithub().pr, body: 'BOONTA_TASK_ID: ' + taskId + '\nBOONTA_TASK_ID: ' + taskId + '\nBOONTA_TASK_TARGET_BRANCH: main' },
    expectFailure: 'tied to the reserved task'
  });
  await run('missing PR target-branch marker', {
    pr: { ...makeGithub().pr, body: 'BOONTA_TASK_ID: ' + taskId },
    expectFailure: 'tied to the reserved task'
  });
  await run('duplicate PR target-branch markers', {
    pr: { ...makeGithub().pr, body: 'BOONTA_TASK_ID: ' + taskId + '\nBOONTA_TASK_TARGET_BRANCH: main\nBOONTA_TASK_TARGET_BRANCH: main' },
    expectFailure: 'tied to the reserved task'
  });
  await run('PR closed', { pr: { ...makeGithub().pr, state: 'closed' }, expectFailure: 'non-draft' });
  await run('head SHA mismatch', { commitSha: 'b'.repeat(40), expectFailure: 'non-draft' });
  await run('new PR points at a commit created before this cycle', {
    committerDate: new Date(Date.now() - 120_000).toISOString(),
    expectFailure: 'cycle-fresh commit'
  });
  await run('new PR points at a commit with an implausibly future timestamp', {
    committerDate: new Date(Date.now() + 10 * 60_000).toISOString(),
    expectFailure: 'cycle-fresh commit'
  });
  await run('old unchanged PR', {
    baseline: { '501': head },
    snapshotAt: new Date(Date.now() - 10_000).toISOString(),
    expectFailure: 'created or advanced'
  });
  const priorHead = 'b'.repeat(40);
  await run('fresh empty commit on an existing PR is not progress', {
    baseline: { '501': priorHead },
    previousHead: priorHead,
    previousTreeSha: 'unchanged-tree',
    treeSha: 'unchanged-tree',
    expectFailure: 'changed file content'
  });
  await run('existing PR with changed tree content is eligible for exact-head checks', {
    baseline: { '501': priorHead },
    previousHead: priorHead,
    previousTreeSha: 'old-tree',
    treeSha: 'new-tree',
    checkRunsByPoll: [REQUIRED_CHECKS.main.map(name => ({
      name, head_sha: head, status: 'completed', conclusion: 'success',
      app: { slug: 'github-actions' }
    }))]
  });
  const originalPr = makeGithub().pr;
  const movedPr = {
    ...originalPr,
    head: { ...originalPr.head, sha: 'c'.repeat(40) }
  };
  await run('PR head updated while exact-head CI was polling', {
    prSequence: [originalPr, movedPr],
    maxPolls: 1,
    expectFailure: 'changed while exact-head CI was running'
  });
  await run('PR closed while exact-head CI was polling', {
    prSequence: [originalPr, { ...originalPr, state: 'closed' }],
    maxPolls: 1,
    expectFailure: 'changed while exact-head CI was running'
  });
  await run('PR head repository changed while exact-head CI was polling', {
    prSequence: [originalPr, {
      ...originalPr,
      head: { ...originalPr.head, repo: { full_name: 'other-owner/boonta-reborn-88' } }
    }],
    maxPolls: 1,
    expectFailure: 'changed while exact-head CI was running'
  });
  await run('PR base changed while exact-head CI was polling', {
    prSequence: [originalPr, {
      ...originalPr,
      base: { ...originalPr.base, ref: 'dev' }
    }],
    maxPolls: 1,
    expectFailure: 'changed while exact-head CI was running'
  });
  await run('required check failed', {
    checkRunsByPoll: [[...REQUIRED_CHECKS.main.map((name) => ({
      name, head_sha: head, status: 'completed', conclusion: name === REQUIRED_CHECKS.main[0] ? 'failure' : 'success',
      app: { slug: 'github-actions' }
    }))]],
    expectFailure: 'required CI check failed'
  });

  await run('validator self-test check is required', {
    checkRunsByPoll: [[...REQUIRED_CHECKS.main
      .filter((name) => name !== 'Validate workflow YAML and embedded Python')
      .map((name) => ({
        name, head_sha: head, status: 'completed', conclusion: 'success',
        app: { slug: 'github-actions' }
      }))]],
    maxPolls: 1,
    expectFailure: 'did not complete successfully'
  });
  await run('same-name check from an untrusted app is ignored', {
    checkRunsByPoll: [[...REQUIRED_CHECKS.main.map((name) => ({
      name, head_sha: head, status: 'completed', conclusion: 'success',
      app: { slug: 'untrusted-app' }
    }))]],
    maxPolls: 1,
    expectFailure: 'did not complete successfully'
  });

  const pendingRuns = REQUIRED_CHECKS.main.map((name) => ({
    name, head_sha: head, status: 'in_progress', conclusion: null,
    app: { slug: 'github-actions' }
  }));
  const completedRuns = REQUIRED_CHECKS.main.map((name) => ({
    name, head_sha: head, status: 'completed', conclusion: 'success',
    app: { slug: 'github-actions' }
  }));
  const pending = await run('wait for exact-head checks', {
    checkRunsByPoll: [pendingRuns, completedRuns], maxPolls: 2
  });
  assert.equal(pending.fixture.polls, 2);
  assert.equal(pending.core.outputs.cycle_status, 'progress');

  const blocked = await run('named task blocker', { status: 'BLOCKED' });
  assert.equal(blocked.core.outputs.cycle_status, 'blocked');
  assert.equal(blocked.core.outputs.blocked_fingerprint.length, 16);
  await run('BLOCKED next action cannot direct a main task to dev', {
    status: 'BLOCKED',
    reportNextAction: 'Use branch dev for the next code change.',
    expectFailure: 'BLOCKED next action contradicts selected target branch'
  });
  await run('BLOCKED next action cannot direct a dev task to main', {
    status: 'BLOCKED',
    base: 'dev',
    expectedBase: 'dev',
    reportNextAction: 'Continue on the main branch.',
    expectFailure: 'BLOCKED next action contradicts selected target branch'
  });
  await run('BLOCKED next action recognizes development as the dev branch', {
    status: 'BLOCKED',
    reportNextAction: 'Continue on the development branch.',
    expectFailure: 'BLOCKED next action contradicts selected target branch'
  });
  await run('BLOCKED next action without an explicit branch remains valid', {
    status: 'BLOCKED',
    reportNextAction: 'Record the verified owner result in the task ledger.'
  });
  await run('BLOCKED next action may explicitly use its selected branch', {
    status: 'BLOCKED',
    reportNextAction: 'Use branch main for the next documentation change.'
  });
  await run('BLOCKED next action rejects conflicting branches in the same sentence', {
    status: 'BLOCKED',
    reportNextAction: 'Keep main as the base, but push to dev.',
    expectFailure: 'BLOCKED next action contradicts selected target branch'
  });

  const devChecks = REQUIRED_CHECKS.dev.map((name) => ({
    name, head_sha: head, status: 'completed', conclusion: 'success',
    app: { slug: 'github-actions' }
  }));
  const dev = await run('dev target uses native build/host/emulator checks', {
    base: 'dev', expectedBase: 'dev', checkRunsByPoll: [devChecks]
  });
  assert.equal(dev.core.outputs.cycle_status, 'progress');

  process.stdout.write('Autonomous cycle report tests passed: task binding, PR identity/base, exact SHA, cycle freshness, BLOCKED contract and all required exact-head CI checks including the validator self-test.\n');
})().catch((error) => {
  process.stderr.write(String(error.stack || error) + '\n');
  process.exitCode = 1;
});
