'use strict';

const assert = require('node:assert/strict');
const { validateAutonomousCycleReport, REQUIRED_CHECKS } = require('./validate_autonomous_cycle_report');

const owner = 'Master-Chiken';
const repo = 'boonta-reborn-88';
const taskId = 'AUTOMATION-LEDGER-ACTIVATION';
const head = 'a'.repeat(40);
const snapshotAt = new Date(Date.now() - 60_000).toISOString();
const context = { repo: { owner, repo } };

function report(status = 'PROGRESS', base = 'main', task = taskId) {
  if (status === 'BLOCKED') {
    return [
      'BOONTA_CYCLE_TASK_ID: ' + task,
      'BOONTA_CYCLE_STATUS: BLOCKED',
      'BOONTA_CYCLE_BLOCKER: Owner must verify the external toolchain account.',
      'BOONTA_CYCLE_NEXT_ACTION: Record the verified owner result in the task ledger.'
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

function makeGithub(options = {}) {
  const pr = {
    number: 501,
    state: 'open',
    merged_at: null,
    draft: false,
    created_at: new Date(Date.now() - 30_000).toISOString(),
    changed_files: 2,
    body: 'Research result\nBOONTA_TASK_ID: ' + taskId + '\n',
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
  const github = {
    rest: {
      pulls: {
        get: async () => ({ data: options.pr || pr })
      },
      repos: {
        getCommit: async () => ({ data: { sha: options.commitSha || head } })
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
    summary: options.summary || report(options.status || 'PROGRESS', options.reportBase || options.base || 'main', options.reportTaskId || taskId),
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
    pr: { ...makeGithub().pr, body: 'BOONTA_TASK_ID: ' + taskId + '\nBOONTA_TASK_ID: ' + taskId },
    expectFailure: 'tied to the reserved task'
  });
  await run('PR closed', { pr: { ...makeGithub().pr, state: 'closed' }, expectFailure: 'non-draft' });
  await run('head SHA mismatch', { commitSha: 'b'.repeat(40), expectFailure: 'non-draft' });
  await run('old unchanged PR', {
    baseline: { '501': head },
    snapshotAt: new Date(Date.now() - 10_000).toISOString(),
    expectFailure: 'created or advanced'
  });
  await run('required check failed', {
    checkRunsByPoll: [[...REQUIRED_CHECKS.main.map((name) => ({
      name, head_sha: head, status: 'completed', conclusion: name === REQUIRED_CHECKS.main[0] ? 'failure' : 'success',
      app: { slug: 'github-actions' }
    }))]],
    expectFailure: 'required CI check failed'
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

  const devChecks = REQUIRED_CHECKS.dev.map((name) => ({
    name, head_sha: head, status: 'completed', conclusion: 'success',
    app: { slug: 'github-actions' }
  }));
  const dev = await run('dev target uses native build/host/emulator checks', {
    base: 'dev', expectedBase: 'dev', checkRunsByPoll: [devChecks]
  });
  assert.equal(dev.core.outputs.cycle_status, 'progress');

  process.stdout.write('Autonomous cycle report tests passed: task binding, PR identity/base, exact SHA, cycle freshness, BLOCKED contract and exact-head CI polling.\n');
})().catch((error) => {
  process.stderr.write(String(error.stack || error) + '\n');
  process.exitCode = 1;
});
