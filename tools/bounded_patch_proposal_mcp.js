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
  const sourceRootRaw = process.env.BOONTA_TARGET_ROOT || '';
  const proposalPathRaw = process.env.BOONTA_PROPOSAL_PATH || '';
  if (!TASK_ID_RE.test(taskId)) reject('BOONTA_TASK_ID is missing or invalid');
  if (!SHA_RE.test(baseSha)) reject('BOONTA_BASE_SHA is missing or invalid');
  if (!path.isAbsolute(sourceRootRaw) || !path.isAbsolute(proposalPathRaw)) reject('source root and proposal path must be absolute');
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
  if (allowedPaths.some((item) => !readPaths.includes(item))) {
    reject('every owner-approved write path must also be in the task read-path allow-list');
  }
  if (!Array.isArray(readRanges) || readRanges.length < 1 || readRanges.length > 8) {
    reject('BOONTA_READ_RANGES must contain 1-8 exact source ranges');
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
    sourceRoot,
    proposalPath: proposalPathRaw,
    readPaths: new Set(readPaths),
    readRanges,
    allowedPaths: new Set(allowedPaths),
    successfulReads: new Set(),
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

function readApprovedFile(state, args) {
  if (!args || typeof args !== 'object' || Array.isArray(args) ||
      Object.keys(args).sort().join(',') !== 'end_line,file_path,start_line') {
    reject('read_approved_file requires exactly file_path, start_line and end_line');
  }
  const filePath = args.file_path;
  const start = args.start_line;
  const end = args.end_line;
  if (!state.readPaths.has(filePath)) reject('file path is not in the selected task read allow-list');
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 1 || end < start || end - start + 1 > 80) {
    reject('requested source range must be positive and contain at most 80 lines');
  }
  const range = state.readRanges.find((item) =>
    item.path === filePath && item.start_line === start && item.end_line === end
  );
  if (!range) reject('requested line range is not an exact owner-approved range');
  const rangeKey = filePath + ':' + start + ':' + end;
  if (state.successfulReads.has(rangeKey)) reject('this exact source range has already been read once');
  const fullPath = path.resolve(state.sourceRoot, filePath);
  ensureNoSymlinkParents(state.sourceRoot, fullPath);
  const stat = fs.lstatSync(fullPath);
  if (!stat.isFile() || stat.size > MAX_FILE_BYTES) reject('source file is not a regular file within the 96 KiB cap');
  const bytes = fs.readFileSync(fullPath);
  if (bytes.includes(0)) reject('binary source files are not readable');
  const text = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
  const lines = text.split(/\r?\n/);
  if (end > lines.length) reject('approved line range exceeds the source file length');
  const requestedLineCount = end - start + 1;
  if (state.totalBytesRead + bytes.length > MAX_TOTAL_BYTES ||
      state.totalLinesRead + requestedLineCount > MAX_TOTAL_LINES) {
    reject('aggregate source-read budget is exhausted');
  }
  state.successfulReads.add(rangeKey);
  state.totalBytesRead += bytes.length;
  state.totalLinesRead += requestedLineCount;
  return {
    file_path: filePath,
    start_line: start,
    end_line: end,
    content: lines.slice(start - 1, end).map((line, index) => String(start + index) + ': ' + line).join('\n'),
    file_bytes: bytes.length,
    aggregate_bytes_read: state.totalBytesRead,
    aggregate_lines_read: state.totalLinesRead
  };
}

function submitProposal(state, args) {
  if (state.submitted) reject('only one patch proposal may be submitted in this cycle');
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
    name: 'read_approved_file',
    description: 'Read one exact owner-approved line range from a task-scoped source file. Directories, other paths, other ranges and repeated reads are rejected.',
    inputSchema: {
      type: 'object',
      additionalProperties: false,
      required: ['file_path', 'start_line', 'end_line'],
      properties: {
        file_path: { type: 'string' },
        start_line: { type: 'integer', minimum: 1 },
        end_line: { type: 'integer', minimum: 1 }
      }
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
      if (name === 'read_approved_file') return { jsonrpc: '2.0', id: message.id, result: textResult(readApprovedFile(state, args)) };
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
