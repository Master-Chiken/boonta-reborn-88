#!/usr/bin/env node
'use strict';

// Local stdio MCP server. It has no GitHub token, network client or repository write API.
// The only writable output is one workflow-owned proposal file outside the source checkout.
const fs = require('node:fs');
const path = require('node:path');
const readline = require('node:readline');
const { execFileSync } = require('node:child_process');

const TASK_ID_RE = /^[A-Z0-9][A-Z0-9-]{2,63}$/;
const SHA_RE = /^[0-9a-f]{40}$/;
const SAFE_PATH_RE = /^[A-Za-z0-9._/-]+$/;
const TEST_IDS = new Set([
  'automation.task_preflight',
  'automation.provider_handoff',
  'automation.task_ledger',
  'gamecube.rival_host_tests'
]);
const MAX_FILE_BYTES = 96 * 1024;
const MAX_TOTAL_BYTES = 256 * 1024;
const MAX_TOTAL_LINES = 240;
const MAX_READ_RANGES = 10;
const MAX_DIFF_BYTES = 32 * 1024;
const MAX_PROPOSAL_BYTES = 96 * 1024;

function reject(message) {
  throw new Error(message);
}

function parseEnvJson(name, fallback) {
  const raw = process.env[name];
  if (!raw) return fallback;
  try {
    return JSON.parse(raw);
  } catch {
    reject(name + ' is not valid JSON');
  }
}

function safePath(value) {
  if (typeof value !== 'string' || value.length < 1 || value.length > 120 ||
      !SAFE_PATH_RE.test(value) || value.startsWith('/') || value.includes('\\')) return false;
  const parts = value.split('/');
  return parts.every((part) => part && part !== '.' && part !== '..');
}

function ensureNoSymlinkParents(root, target) {
  const relative = path.relative(root, target);
  if (!relative || relative.startsWith('..') || path.isAbsolute(relative)) reject('path escapes the trusted source checkout');
  let current = root;
  for (const part of relative.split(path.sep)) {
    current = path.join(current, part);
    let stat;
    try {
      stat = fs.lstatSync(current);
    } catch (error) {
      if (error.code === 'ENOENT') reject('approved source path does not exist');
      throw error;
    }
    if (stat.isSymbolicLink()) reject('symbolic links are not allowed in approved source paths');
  }
}

function makeState() {
  const taskId = process.env.BOONTA_TASK_ID || '';
  const baseSha = process.env.BOONTA_BASE_SHA || '';
  const targetBranch = process.env.BOONTA_TARGET_BRANCH || '';
  const sourceRootRaw = process.env.BOONTA_TARGET_ROOT || '';
  const proposalPathRaw = process.env.BOONTA_PROPOSAL_PATH || '';
  const workspaceRaw = process.env.GITHUB_WORKSPACE || '';
  const contextPathRaw = process.env.BOONTA_CONTEXT_PATH || '';
  if (!TASK_ID_RE.test(taskId)) reject('BOONTA_TASK_ID is missing or invalid');
  if (!SHA_RE.test(baseSha)) reject('BOONTA_BASE_SHA is missing or invalid');
  if (!['main', 'dev'].includes(targetBranch)) reject('BOONTA_TARGET_BRANCH must be main or dev');
  if (!path.isAbsolute(sourceRootRaw) || !path.isAbsolute(proposalPathRaw) ||
      !path.isAbsolute(workspaceRaw) || !path.isAbsolute(contextPathRaw)) {
    reject('source root, workspace, context and proposal paths must be absolute');
  }
  const workspaceRoot = fs.realpathSync(workspaceRaw);
  const expectedContextPath = path.join(workspaceRoot, '.gemini', 'context.json');
  if (path.resolve(contextPathRaw) !== expectedContextPath) {
    reject('BOONTA_CONTEXT_PATH must be exactly GITHUB_WORKSPACE/.gemini/context.json');
  }
  ensureNoSymlinkParents(workspaceRoot, expectedContextPath);
  const contextStat = fs.lstatSync(expectedContextPath);
  if (!contextStat.isFile() || contextStat.isSymbolicLink() || contextStat.size > 16 * 1024) {
    reject('bounded task context must be a regular non-symlink file no larger than 16 KiB');
  }
  let rawContext;
  try {
    rawContext = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(fs.readFileSync(expectedContextPath)));
  } catch {
    reject('bounded task context is not valid UTF-8 JSON');
  }
  if (!rawContext || typeof rawContext !== 'object' || Array.isArray(rawContext)) {
    reject('bounded task context must be a JSON object');
  }
  const taskContext = {
    task_id: rawContext.task_id,
    task_title: rawContext.task_title,
    task_description: rawContext.task_description,
    task_target_branch: rawContext.task_target_branch,
    verified_context: rawContext.verified_context
  };
  if (taskContext.task_id !== taskId || taskContext.task_target_branch !== targetBranch ||
      typeof taskContext.task_title !== 'string' || !taskContext.task_title.trim() ||
      taskContext.task_title.length > 240 ||
      typeof taskContext.task_description !== 'string' || !taskContext.task_description.trim() ||
      taskContext.task_description.length > 6000 ||
      typeof taskContext.verified_context !== 'string' || !taskContext.verified_context.trim() ||
      Buffer.byteLength(taskContext.verified_context, 'utf8') > 12 * 1024) {
    reject('bounded task context does not match the trusted task ID/target branch or exceeds its size limits');
  }
  const sourceRoot = fs.realpathSync(sourceRootRaw);
  const rootStat = fs.lstatSync(sourceRoot);
  if (!rootStat.isDirectory() || rootStat.isSymbolicLink()) reject('target source root must be a real directory');
  const actualSha = execFileSync('git', ['rev-parse', 'HEAD'], {
    cwd: sourceRoot,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe']
  }).trim();
  if (actualSha !== baseSha) reject('target checkout HEAD does not match the reserved base SHA');

  const readPaths = parseEnvJson('BOONTA_READ_PATHS', []);
  const readRanges = parseEnvJson('BOONTA_READ_RANGES', []);
  const allowedPaths = parseEnvJson('BOONTA_ALLOWED_PATHS', []);
  if (!Array.isArray(readPaths) || readPaths.length < 1 || readPaths.length > 5 ||
      readPaths.some((item) => !safePath(item)) || new Set(readPaths).size !== readPaths.length) {
    reject('BOONTA_READ_PATHS must contain 1-5 unique safe repository paths');
  }
  if (!Array.isArray(allowedPaths) || allowedPaths.length < 1 || allowedPaths.length > 20 ||
      allowedPaths.some((item) => !safePath(item)) || new Set(allowedPaths).size !== allowedPaths.length) {
    reject('BOONTA_ALLOWED_PATHS must contain 1-20 unique safe repository paths');
  }
  if (!Array.isArray(readRanges) || readRanges.length < 1 || readRanges.length > MAX_READ_RANGES) {
    reject('BOONTA_READ_RANGES must contain 1-' + MAX_READ_RANGES + ' exact source ranges');
  }
  let totalRangeLines = 0;
  const seenRanges = new Set();
  for (const item of readRanges) {
    if (!item || typeof item !== 'object' || Array.isArray(item) ||
        !readPaths.includes(item.path) || !Number.isInteger(item.start_line) ||
        !Number.isInteger(item.end_line) || item.start_line < 1 ||
        item.end_line < item.start_line || item.end_line - item.start_line + 1 > 80) {
      reject('each read range must be an exact bounded range from BOONTA_READ_PATHS');
    }
    const key = item.path + ':' + item.start_line + ':' + item.end_line;
    if (seenRanges.has(key)) reject('duplicate exact source read range');
    seenRanges.add(key);
    totalRangeLines += item.end_line - item.start_line + 1;
  }
  if (totalRangeLines > MAX_TOTAL_LINES) reject('approved source ranges exceed the 240-line aggregate cap');
  const coveredPaths = new Set(readRanges.map((item) => item.path));
  if (readPaths.some((item) => !coveredPaths.has(item))) reject('every approved read path must have at least one exact line range');
  for (const item of readPaths) {
    const full = path.resolve(sourceRoot, item);
    ensureNoSymlinkParents(sourceRoot, full);
    const stat = fs.lstatSync(full);
    if (!stat.isFile() || stat.size > MAX_FILE_BYTES) reject('approved source path is not a regular bounded file: ' + item);
  }

  const proposalParent = path.dirname(proposalPathRaw);
  const proposalParentReal = fs.realpathSync(proposalParent);
  const runnerTemp = process.env.RUNNER_TEMP ? fs.realpathSync(process.env.RUNNER_TEMP) : '';
  if (!runnerTemp || (proposalParentReal !== runnerTemp && !proposalParentReal.startsWith(runnerTemp + path.sep))) {
    reject('proposal file must be located under RUNNER_TEMP');
  }
  if (proposalPathRaw === path.resolve(sourceRoot) || proposalPathRaw.startsWith(sourceRoot + path.sep)) {
    reject('proposal file must remain outside the checked-out source repository');
  }
  if (fs.existsSync(proposalPathRaw)) reject('proposal output already exists; refusing to overwrite it');

  return {
    taskId,
    baseSha,
    targetBranch,
    taskContext,
    sourceRoot,
    proposalPath: proposalPathRaw,
    readPaths: new Set(readPaths),
    readRanges,
    allowedPaths: new Set(allowedPaths),
    sourcesRead: false,
    totalBytesRead: 0,
    totalLinesRead: 0,
    submitted: false
  };
}

function validateDiff(diff, allowedPaths) {
  if (typeof diff !== 'string' || !diff.trim()) reject('unified_diff must be non-empty text');
  if (Buffer.byteLength(diff, 'utf8') > MAX_DIFF_BYTES) reject('unified_diff exceeds the 32 KiB byte limit');
  if (diff.includes('\0')) reject('unified_diff contains a NUL byte');
  const lines = diff.split(/\r?\n/);
  const changed = [];
  let current = null;
  let hasHunk = false;
  let totalHunks = 0;
  for (const line of lines) {
    if (line.startsWith('diff --git ')) {
      if (current && !hasHunk) reject('each diff file section must contain a text hunk');
      const match = /^diff --git a\/([^ ]+) b\/([^ ]+)$/.exec(line);
      if (!match) reject('diff header is malformed');
      const oldPath = match[1];
      const newPath = match[2];
      if (oldPath !== newPath) reject('renames and cross-path changes are not allowed');
      if (!safePath(oldPath) || !allowedPaths.has(oldPath)) reject('diff path is outside the exact owner-approved write-path allow-list: ' + oldPath);
      if (changed.includes(oldPath)) reject('diff contains a duplicate file section');
      changed.push(oldPath);
      current = oldPath;
      hasHunk = false;
      continue;
    }
    if (/^(new file mode |deleted file mode |old mode |new mode |rename from |rename to |copy from |copy to |GIT binary patch|Binary files |Subproject commit )/.test(line)) {
      reject('binary, mode, rename, copy and submodule changes are not allowed');
    }
    if (line.startsWith('--- ')) {
      if (!current || line !== '--- a/' + current) reject('old-file diff header does not match its exact path');
      continue;
    }
    if (line.startsWith('+++ ')) {
      if (!current || line !== '+++ b/' + current) reject('new-file diff header does not match its exact path');
      continue;
    }
    if (line.startsWith('@@ ')) {
      if (!current) reject('diff hunk appears before a file section');
      hasHunk = true;
      totalHunks += 1;
      if (totalHunks > 100) reject('diff exceeds the 100-hunk limit');
    }
  }
  if (changed.length < 1 || changed.length > allowedPaths.size) reject('diff must change 1 or more exact approved files');
  if (current && !hasHunk) reject('last diff file section has no text hunk');
  return changed.sort();
}

function readApprovedSources(state, args) {
  if (args !== undefined && (!args || typeof args !== 'object' || Array.isArray(args) || Object.keys(args).length !== 0)) {
    reject('read_approved_sources accepts no arguments; source scope is fixed by preflight');
  }
  if (state.sourcesRead) reject('approved task sources may be read only once in this cycle');

  let totalBytes = 0;
  let totalLines = 0;
  const files = [];
  for (const filePath of [...state.readPaths].sort()) {
    const fullPath = path.resolve(state.sourceRoot, filePath);
    ensureNoSymlinkParents(state.sourceRoot, fullPath);
    const stat = fs.lstatSync(fullPath);
    if (!stat.isFile() || stat.size > MAX_FILE_BYTES) reject('source file is not a regular file within the 96 KiB cap: ' + filePath);
    const bytes = fs.readFileSync(fullPath);
    if (bytes.includes(0)) reject('binary source files are not readable: ' + filePath);
    const sourceText = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
    const lines = sourceText.split(/\r?\n/);
    const ranges = state.readRanges
      .filter((item) => item.path === filePath)
      .sort((a, b) => a.start_line - b.start_line || a.end_line - b.end_line);
    if (!ranges.length) reject('approved source path has no exact source ranges: ' + filePath);

    const rangeResults = [];
    for (const item of ranges) {
      if (item.end_line > lines.length) reject('approved line range exceeds source file length: ' + filePath);
      const requestedLines = item.end_line - item.start_line + 1;
      totalLines += requestedLines;
      rangeResults.push({
        start_line: item.start_line,
        end_line: item.end_line,
        content: lines.slice(item.start_line - 1, item.end_line)
          .map((line, index) => String(item.start_line + index) + ': ' + line)
          .join('\n')
      });
    }
    totalBytes += bytes.length;
    files.push({
      file_path: filePath,
      file_bytes: bytes.length,
      ranges: rangeResults
    });
  }
  if (totalBytes > MAX_TOTAL_BYTES || totalLines > MAX_TOTAL_LINES) {
    reject('aggregate source-read budget is exhausted');
  }
  state.sourcesRead = true;
  state.totalBytesRead = totalBytes;
  state.totalLinesRead = totalLines;
  return {
    task_id: state.taskId,
    target_branch: state.targetBranch,
    base_sha: state.baseSha,
    task_context: state.taskContext,
    files,
    aggregate_bytes_read: totalBytes,
    aggregate_lines_read: totalLines
  };
}

function submitProposal(state, args) {
  if (state.submitted) reject('only one patch proposal may be submitted in this cycle');
  if (!state.sourcesRead) reject('read_approved_sources must succeed before a patch proposal can be submitted');
  const required = ['schema_version', 'task_id', 'base_sha', 'summary', 'unified_diff', 'test_ids', 'limitations'];
  if (!args || typeof args !== 'object' || Array.isArray(args) ||
      Object.keys(args).sort().join(',') !== required.slice().sort().join(',')) {
    reject('proposal must contain exactly the seven documented fields');
  }
  if (args.schema_version !== 1) reject('schema_version must equal integer 1');
  if (args.task_id !== state.taskId) reject('proposal task_id differs from the trusted reservation');
  if (args.base_sha !== state.baseSha) reject('proposal base_sha differs from the trusted target checkout');
  if (typeof args.summary !== 'string' || !args.summary.trim() || args.summary.length > 240) {
    reject('summary must contain 1-240 characters');
  }
  const changedPaths = validateDiff(args.unified_diff, state.allowedPaths);
  if (!Array.isArray(args.test_ids) || args.test_ids.length < 1 || args.test_ids.length > 6 ||
      args.test_ids.some((item) => typeof item !== 'string' || !TEST_IDS.has(item)) ||
      new Set(args.test_ids).size !== args.test_ids.length) {
    reject('test_ids must contain 1-6 unique repository-owned test identifiers');
  }
  if (!Array.isArray(args.limitations) || args.limitations.length > 8 ||
      args.limitations.some((item) => typeof item !== 'string' || !item.trim() || item.length > 240)) {
    reject('limitations must contain at most eight non-empty strings of at most 240 characters');
  }
  const proposal = {
    schema_version: 1,
    task_id: state.taskId,
    base_sha: state.baseSha,
    summary: args.summary.trim(),
    unified_diff: args.unified_diff,
    test_ids: args.test_ids,
    limitations: args.limitations,
    changed_paths: changedPaths
  };
  const raw = JSON.stringify(proposal, null, 2) + '\n';
  if (Buffer.byteLength(raw, 'utf8') > MAX_PROPOSAL_BYTES) reject('serialized proposal exceeds the 96 KiB limit');
  const tempPath = state.proposalPath + '.tmp';
  const fd = fs.openSync(tempPath, 'wx', 0o600);
  try {
    fs.writeFileSync(fd, raw, 'utf8');
    fs.fsyncSync(fd);
  } finally {
    fs.closeSync(fd);
  }
  fs.renameSync(tempPath, state.proposalPath);
  state.submitted = true;
  return {
    status: 'PROPOSAL_STAGED',
    task_id: state.taskId,
    base_sha: state.baseSha,
    changed_paths: changedPaths,
    test_ids: args.test_ids,
    proposal_bytes: Buffer.byteLength(raw, 'utf8'),
    remote_repository_write_performed: false
  };
}

const TOOL_DEFINITIONS = [
  {
    name: 'read_approved_sources',
    description: 'Read every exact owner-approved source range from the selected task in one bounded call. The source list and ranges are fixed by preflight; the entire set may be read only once.',
    inputSchema: {
      type: 'object',
      additionalProperties: false,
      properties: {}
    }
  },
  {
    name: 'submit_patch_proposal',
    description: 'Submit one unified-diff proposal for deterministic workflow verification. This tool does not create branches, commits, PRs or GitHub writes.',
    inputSchema: {
      type: 'object',
      additionalProperties: false,
      required: ['schema_version', 'task_id', 'base_sha', 'summary', 'unified_diff', 'test_ids', 'limitations'],
      properties: {
        schema_version: { type: 'integer', enum: [1] },
        task_id: { type: 'string' },
        base_sha: { type: 'string' },
        summary: { type: 'string', maxLength: 240 },
        unified_diff: { type: 'string', maxLength: MAX_DIFF_BYTES },
        test_ids: { type: 'array', minItems: 1, maxItems: 6, uniqueItems: true, items: { type: 'string', enum: [...TEST_IDS] } },
        limitations: { type: 'array', maxItems: 8, items: { type: 'string', maxLength: 240 } }
      }
    }
  }
];

function textResult(value) {
  return {
    content: [{ type: 'text', text: JSON.stringify(value, null, 2) }],
    isError: false
  };
}

function errorResult(error) {
  return {
    content: [{ type: 'text', text: String(error && error.message ? error.message : error) }],
    isError: true
  };
}

let state;
try {
  state = makeState();
} catch (error) {
  process.stderr.write('Boonta proposal MCP refused startup: ' + String(error.message || error) + '\n');
  process.exit(2);
}

async function handle(message) {
  if (!message || message.jsonrpc !== '2.0' || typeof message.method !== 'string') return null;
  if (message.method === 'notifications/initialized') return null;
  if (message.method === 'initialize') {
    return {
      jsonrpc: '2.0',
      id: message.id,
      result: {
        protocolVersion: message.params?.protocolVersion || '2024-11-05',
        capabilities: { tools: {} },
        serverInfo: { name: 'boonta-bounded-patch-proposal', version: '1.0.0' }
      }
    };
  }
  if (message.method === 'ping') return { jsonrpc: '2.0', id: message.id, result: {} };
  if (message.method === 'tools/list') {
    return { jsonrpc: '2.0', id: message.id, result: { tools: TOOL_DEFINITIONS } };
  }
  if (message.method === 'tools/call') {
    const name = message.params?.name;
    const args = message.params?.arguments;
    try {
      if (name === 'read_approved_sources') return { jsonrpc: '2.0', id: message.id, result: textResult(readApprovedSources(state, args)) };
      if (name === 'submit_patch_proposal') return { jsonrpc: '2.0', id: message.id, result: textResult(submitProposal(state, args)) };
      return { jsonrpc: '2.0', id: message.id, result: errorResult(new Error('unknown Boonta proposal tool')) };
    } catch (error) {
      return { jsonrpc: '2.0', id: message.id, result: errorResult(error) };
    }
  }
  if (message.id !== undefined) {
    return { jsonrpc: '2.0', id: message.id, error: { code: -32601, message: 'method not found' } };
  }
  return null;
}

const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
rl.on('line', async (line) => {
  let message;
  try {
    message = JSON.parse(line);
    const response = await handle(message);
    if (response) process.stdout.write(JSON.stringify(response) + '\n');
  } catch (error) {
    process.stdout.write(JSON.stringify({
      jsonrpc: '2.0',
      id: message && message.id !== undefined ? message.id : null,
      error: { code: -32700, message: String(error.message || error) }
    }) + '\n');
  }
});
rl.on('close', () => process.exit(0));
