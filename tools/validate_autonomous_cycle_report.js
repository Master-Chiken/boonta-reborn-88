'use strict';

const REQUIRED_CHECKS = Object.freeze({
  main: [
    'Validate workflow YAML and embedded Python',
    'Verify Gemini free-only guardrails',
    'Reject known held assets and data',
    'Check proposed source paths using trusted base policy'
  ],
  dev: [
    'Host pause/resume state tests',
    'build-gamecube-demo',
    'Dolphin headless process smoke (not visual verification)'
  ]
});

function oneLine(lines, key) {
  const matches = lines.filter((line) => line.startsWith(key + ': '));
  return matches.length === 1 ? matches[0].slice(key.length + 2).trim() : null;
}

function fail(core, message) {
  core.setFailed(message);
  return { cycle_status: 'invalid' };
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function findBlockedReportContradictions(blockedText, evidence = {}) {
  const text = typeof blockedText === 'string' ? blockedText : '';
  const contradictions = [];

  if (evidence.openRouterAuthSucceeded === true) {
    const providerKeyUnavailable =
      /\b(?:no|without|missing|absent|unavailable|not available)\b.{0,100}\b(?:OpenRouter\s+)?(?:provider\s+)?(?:API\s+)?key\b/i.test(text) ||
      /\b(?:OpenRouter\s+)?(?:provider\s+)?(?:API\s+)?key\b.{0,100}\b(?:missing|absent|unavailable|not available|not configured|invalid)\b/i.test(text);
    const explicitAuthFailure =
      /(OPENROUTER_API_KEY|HTTP\s*401|OpenRouter.{0,80}(missing|invalid|unauthori[sz]ed|authentication failure|Free[- ]tier.{0,40}(missing|invalid|not verified)))/i.test(text);
    if (providerKeyUnavailable || explicitAuthFailure) {
      contradictions.push('claims OpenRouter credentials or Free-tier authentication are unavailable although same-run authentication succeeded');
    }
  }

  if (evidence.githubAppTokenMinted === true) {
    const tokenUnavailable =
      /\b(?:no|without|missing|absent|unavailable|not available|not verified)\b.{0,120}\b(?:verified\s+)?(?:live\s+)?GitHub App(?: installation)? token\b/i.test(text) ||
      /\bGitHub App(?: installation)? token\b.{0,100}\b(?:missing|absent|unavailable|not available|not minted|not verified)\b/i.test(text);
    const appCredentialsMissing =
      /\b(?:APP_ID|APP_PRIVATE_KEY)\b.{0,80}\b(?:missing|absent|not configured|unset)\b/i.test(text);
    if (tokenUnavailable || appCredentialsMissing) {
      contradictions.push('claims the GitHub App token or its credentials are unavailable although same-run token creation succeeded');
    }
  }

  return contradictions;
}


function findNextActionBranchContradictions(nextAction, expectedBase) {
  const text = typeof nextAction === 'string' ? nextAction : '';
  const mentionedBranches = new Set();
  const patterns = [
    /\bbranch\s+(?:named\s+)?[`'"]?(main|dev)\b/gi,
    /\b(main|dev)\s+branch\b/gi,
    /\b(?:use|work(?:ing)?\s+on|target(?:ing)?|push(?:ing)?\s+to|base(?:d)?\s+on|create(?:d)?\s+from|switch(?:ing)?\s+to|continue(?:d)?\s+on)\s+(?:the\s+)?[`'"]?(main|dev)\b/gi
  ];
  for (const pattern of patterns) {
    let match;
    while ((match = pattern.exec(text)) !== null) {
      mentionedBranches.add(match[1].toLowerCase());
    }
  }
  return [...mentionedBranches]
    .filter((branch) => branch !== expectedBase)
    .map((branch) => 'directs the next action to ' + branch + ' although the selected task target is ' + expectedBase);
}

async function validateAutonomousCycleReport(options) {
  const {
    github, context, core, summary, baseline, snapshotAt,
    expectedTaskId, expectedBase, provider,
    maxPolls = 32, pollIntervalMs = 15000, sleep = delay
  } = options;

  if (!github || !context || !core || typeof summary !== 'string') {
    return fail(core, 'Cycle-report validator received incomplete inputs.');
  }
  if (typeof expectedTaskId !== 'string' || !expectedTaskId.trim() ||
      !Object.prototype.hasOwnProperty.call(REQUIRED_CHECKS, expectedBase)) {
    return fail(core, 'The reserved task ID or required target branch is missing/invalid.');
  }

  const lines = summary.trim().split(/\r?\n/);
  const taskId = oneLine(lines, 'BOONTA_CYCLE_TASK_ID');
  if (taskId !== expectedTaskId) {
    return fail(core, 'Cycle report task ID does not match the exact task reservation.');
  }

  const statusLines = lines.filter((line) => line.startsWith('BOONTA_CYCLE_STATUS:'));
  if (statusLines.length !== 1 ||
      !['BOONTA_CYCLE_STATUS: PROGRESS', 'BOONTA_CYCLE_STATUS: BLOCKED'].includes(statusLines[0])) {
    return fail(core, 'Cycle report must contain exactly one valid PROGRESS or BLOCKED status.');
  }

  const valueExists = (key) => {
    const value = oneLine(lines, key);
    return typeof value === 'string' && value.length > 0;
  };

  if (statusLines[0] === 'BOONTA_CYCLE_STATUS: BLOCKED') {
    if (!valueExists('BOONTA_CYCLE_BLOCKER') || !valueExists('BOONTA_CYCLE_NEXT_ACTION')) {
      return fail(core, 'BLOCKED requires one named blocker and one concrete next action.');
    }
    const blocker = oneLine(lines, 'BOONTA_CYCLE_BLOCKER');
    const nextAction = oneLine(lines, 'BOONTA_CYCLE_NEXT_ACTION');
    const branchContradictions = findNextActionBranchContradictions(nextAction, expectedBase);
    if (branchContradictions.length > 0) {
      return fail(core, 'BLOCKED next action contradicts selected target branch: ' + branchContradictions.join('; ') + '.');
    }
    const fingerprint = require('crypto').createHash('sha256')
      .update(blocker + '\n' + nextAction, 'utf8').digest('hex').slice(0, 16);
    core.setOutput('blocked_fingerprint', fingerprint);
    core.setOutput('cycle_status', 'blocked');
    core.info(provider + ' reported a named blocker for task ' + expectedTaskId + '.');
    return { cycle_status: 'blocked', blocked_fingerprint: fingerprint };
  }

  const evidenceLines = lines.filter((line) => line.startsWith('BOONTA_CYCLE_EVIDENCE:'));
  const evidence = evidenceLines.length === 1
    ? evidenceLines[0].match(/^BOONTA_CYCLE_EVIDENCE: https:\/\/github\.com\/Master-Chiken\/boonta-reborn-88\/pull\/([1-9][0-9]*) @ ([0-9a-f]{40})$/)
    : null;
  const evidenceBase = oneLine(lines, 'BOONTA_CYCLE_EVIDENCE_BASE');
  if (!evidence || evidenceBase !== expectedBase) {
    return fail(core, 'PROGRESS must cite an exact same-repository PR/head and the reserved target branch ' + expectedBase + '.');
  }

  const baseSnapshot = baseline && typeof baseline === 'object' ? baseline : {};
  const snapshotTime = Date.parse(snapshotAt || '');
  if (!Number.isFinite(snapshotTime)) {
    return fail(core, 'The pre-cycle PR snapshot timestamp is missing or invalid.');
  }

  const owner = context.repo.owner;
  const repo = context.repo.repo;
  const pullNumber = Number(evidence[1]);
  const exactHead = evidence[2];
  const { data: pr } = await github.rest.pulls.get({ owner, repo, pull_number: pullNumber });
  const { data: headCommit } = await github.rest.repos.getCommit({ owner, repo, ref: exactHead });
  const existedAtStart = Object.prototype.hasOwnProperty.call(baseSnapshot, String(pullNumber));
  const createdAfterSnapshot = !existedAtStart && Date.parse(pr.created_at || '') > snapshotTime;
  const previousHeadSha = existedAtStart ? baseSnapshot[String(pullNumber)] : '';
  const advancedDuringCycle = existedAtStart && previousHeadSha !== exactHead;
  let contentChangedDuringCycle = !existedAtStart && (pr.changed_files ?? 0) >= 1;
  if (existedAtStart) {
    const { data: previousHeadCommit } = await github.rest.repos.getCommit({
      owner, repo, ref: previousHeadSha
    });
    const previousTreeSha = previousHeadCommit.commit?.tree?.sha;
    const exactTreeSha = headCommit.commit?.tree?.sha;
    contentChangedDuringCycle = Boolean(
      previousTreeSha && exactTreeSha && previousTreeSha !== exactTreeSha
    );
  }
  const commitTimestamp = Date.parse(headCommit.commit?.committer?.date || '');
  const commitCreatedDuringCycle = Number.isFinite(commitTimestamp) &&
    commitTimestamp >= snapshotTime &&
    commitTimestamp <= Date.now() + 5 * 60 * 1000;
  const taskMarker = 'BOONTA_TASK_ID: ' + expectedTaskId;
  const taskMarkerCount = (pr.body || '').split(/\r?\n/).filter((line) => line.trim() === taskMarker).length;
  const bodyHasTaskMarker = taskMarkerCount === 1;
  const targetBranchMarker = 'BOONTA_TASK_TARGET_BRANCH: ' + expectedBase;
  const targetBranchMarkerCount = (pr.body || '').split(/\r?\n/).filter((line) => line.trim() === targetBranchMarker).length;
  const bodyHasTargetBranchMarker = targetBranchMarkerCount === 1;

  if (
    pr.number !== pullNumber ||
    pr.state !== 'open' ||
    pr.merged_at ||
    pr.draft === true ||
    pr.head.repo?.full_name !== owner + '/' + repo ||
    pr.base.repo?.full_name !== owner + '/' + repo ||
    pr.head.sha !== exactHead ||
    headCommit.sha !== exactHead ||
    (pr.changed_files ?? 0) < 1 ||
    pr.base.ref !== expectedBase ||
    !bodyHasTaskMarker ||
    !bodyHasTargetBranchMarker ||
    (!createdAfterSnapshot && !advancedDuringCycle) ||
    !contentChangedDuringCycle ||
    !commitCreatedDuringCycle
  ) {
    return fail(core, 'PROGRESS requires a non-draft, non-empty same-repository PR tied to the reserved task, targeting ' +
      expectedBase + ', at its exact current head, created or advanced during this cycle, with changed file content and a cycle-fresh commit.');
  }

  const required = REQUIRED_CHECKS[expectedBase];
  let latestCheckRuns = [];
  let accepted = false;
  for (let attempt = 0; attempt < maxPolls; attempt += 1) {
    const { data } = await github.rest.checks.listForRef({
      owner, repo, ref: exactHead, per_page: 100
    });
    const runs = Array.isArray(data?.check_runs) ? data.check_runs : [];
    latestCheckRuns = required.map((name) => {
      const matching = runs
        .filter((run) => run.name === name && run.head_sha === exactHead && run.app?.slug === 'github-actions')
        .sort((a, b) => Date.parse(b.created_at || b.started_at || '') - Date.parse(a.created_at || a.started_at || ''));
      return { name, check: matching[0] || null };
    });

    const failed = latestCheckRuns.find(({ check }) =>
      check && check.status === 'completed' && check.conclusion !== 'success'
    );
    if (failed) {
      return fail(core, 'Exact-head required CI check failed: ' + failed.name + ' (' + failed.check.conclusion + ').');
    }
    accepted = latestCheckRuns.every(({ check }) =>
      check && check.status === 'completed' && check.conclusion === 'success'
    );
    if (accepted) break;
    if (attempt + 1 < maxPolls) await sleep(pollIntervalMs);
  }

  if (!accepted) {
    const state = latestCheckRuns.map(({ name, check }) =>
      name + '=' + (check ? (check.status === 'completed' ? check.conclusion : check.status) : 'not found')
    ).join('; ');
    return fail(core, 'Exact-head CI did not complete successfully within the bounded eight-minute verification window: ' + state);
  }

  // CI may take several minutes. Re-fetch the PR after polling so a head
  // update, close, merge or base change during that window cannot be accepted.
  const { data: finalPr } = await github.rest.pulls.get({ owner, repo, pull_number: pullNumber });
  const finalTaskMarkerCount = (finalPr.body || '').split(/\r?\n/)
    .filter((line) => line.trim() === taskMarker).length;
  const finalTargetMarkerCount = (finalPr.body || '').split(/\r?\n/)
    .filter((line) => line.trim() === targetBranchMarker).length;
  if (
    finalPr.number !== pullNumber ||
    finalPr.state !== 'open' ||
    finalPr.merged_at ||
    finalPr.draft === true ||
    finalPr.head.repo?.full_name !== owner + '/' + repo ||
    finalPr.base.repo?.full_name !== owner + '/' + repo ||
    finalPr.head.sha !== exactHead ||
    finalPr.base.ref !== expectedBase ||
    (finalPr.changed_files ?? 0) < 1 ||
    finalTaskMarkerCount !== 1 ||
    finalTargetMarkerCount !== 1
  ) {
    return fail(core, 'The cited PR changed while exact-head CI was running; refusing stale progress evidence.');
  }

  core.setOutput('cycle_status', 'progress');
  core.setOutput('evidence_pr_number', String(pullNumber));
  core.setOutput('evidence_head_sha', exactHead);
  core.setOutput('evidence_base', expectedBase);
  core.info('Verified task ' + expectedTaskId + ' via PR #' + pullNumber + ' at exact head ' + exactHead +
    '; required ' + expectedBase + ' checks passed: ' + required.join(', ') + '.');
  return {
    cycle_status: 'progress',
    evidence_pr_number: pullNumber,
    evidence_head_sha: exactHead,
    evidence_base: expectedBase
  };
}

module.exports = { REQUIRED_CHECKS, findBlockedReportContradictions, validateAutonomousCycleReport };
