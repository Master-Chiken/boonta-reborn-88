'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const SERVER = path.join(__dirname, 'bounded_patch_proposal_mcp.js');
const TASK_ID = 'TEST-GAMEPLAY';
const SOURCE_A = 'src/gameplay.h';
const SOURCE_B = 'src/test.c';

function git(root, ...args) {
  const result = spawnSync('git', args, { cwd: root, encoding: 'utf8' });
  if (result.status !== 0) throw new Error(result.stderr || 'git command failed');
  return result.stdout.trim();
}

function fixture(overrides = {}) {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'boonta-bounded-mcp-'));
  const root = path.join(temp, 'repo');
  const workspace = path.join(temp, 'workspace');
  const runnerTemp = path.join(temp, 'runner-temp');
  fs.mkdirSync(path.join(root, 'src'), { recursive: true });
  fs.mkdirSync(path.join(workspace, '.gemini'), { recursive: true });
  fs.mkdirSync(runnerTemp, { recursive: true });
  fs.writeFileSync(path.join(workspace, '.gemini', 'context.json'), JSON.stringify({
    task_id: TASK_ID,
    task_title: 'Rival route progress fixture',
    task_description: 'Trace player and rival route progress',
    task_target_branch: 'dev',
    verified_context: 'Owner-approved exact-path context and task acceptance criteria'
  }), 'utf8');
  fs.writeFileSync(path.join(root, SOURCE_A), 'int gameplay_value(void) {\n    return 1;\n}\n', 'utf8');
  fs.writeFileSync(path.join(root, SOURCE_B), 'int test_value(void) {\n    return 1;\n}\n', 'utf8');
  git(root, 'init', '-q');
  git(root, 'config', 'user.name', 'Boonta MCP Test');
  git(root, 'config', 'user.email', 'boonta-mcp-test@example.invalid');
  git(root, 'add', 'src');
  git(root, 'commit', '-qm', 'fixture base');
  const baseSha = git(root, 'rev-parse', 'HEAD');

  const env = {
    PATH: process.env.PATH,
    HOME: process.env.HOME,
    BOONTA_TASK_ID: TASK_ID,
    BOONTA_TARGET_BRANCH: 'dev',
    BOONTA_BASE_SHA: baseSha,
    BOONTA_TARGET_ROOT: root,
    BOONTA_CONTEXT_PATH: path.join(workspace, '.gemini', 'context.json'),
    BOONTA_PROPOSAL_PATH: path.join(runnerTemp, 'proposal.json'),
    GITHUB_WORKSPACE: workspace,
    RUNNER_TEMP: runnerTemp,
    BOONTA_READ_PATHS: JSON.stringify([SOURCE_A, SOURCE_B]),
    BOONTA_READ_RANGES: JSON.stringify([
      { path: SOURCE_A, start_line: 1, end_line: 3 },
      { path: SOURCE_B, start_line: 1, end_line: 3 }
    ]),
    BOONTA_ALLOWED_PATHS: JSON.stringify([SOURCE_A, SOURCE_B]),
    ...overrides
  };
  return { temp, root, workspace, runnerTemp, baseSha, env };
}

function validDiff(filePath = SOURCE_A) {
  return [
    'diff --git a/' + filePath + ' b/' + filePath,
    'index 1111111..2222222 100644',
    '--- a/' + filePath,
    '+++ b/' + filePath,
    '@@ -1,3 +1,3 @@',
    ' int gameplay_value(void) {',
    '-    return 1;',
    '+    return 2;',
    ' }'
  ].join('\n');
}

function validProposal(baseSha, overrides = {}) {
  return {
    schema_version: 1,
    task_id: TASK_ID,
    base_sha: baseSha,
    summary: 'Advance the deterministic gameplay helper',
    unified_diff: validDiff(),
    test_ids: ['automation.task_preflight'],
    limitations: [],
    ...overrides
  };
}

function rpc(method, params, id) {
  const message = { jsonrpc: '2.0', method };
  if (id !== undefined) message.id = id;
  if (params !== undefined) message.params = params;
  return JSON.stringify(message);
}

function runServer(fx, requests) {
  const input = [
    rpc('initialize', { protocolVersion: '2024-11-05', capabilities: {}, clientInfo: { name: 'test', version: '1' } }, 1),
    rpc('notifications/initialized'),
    ...requests
  ].join('\n') + '\n';
  const result = spawnSync(process.execPath, [SERVER], {
    cwd: __dirname,
    env: fx.env,
    input,
    encoding: 'utf8',
    timeout: 10000
  });
  const messages = result.stdout.split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
  return { ...result, messages };
}

function call(name, args, id) {
  return rpc('tools/call', { name, arguments: args }, id);
}

function toolResult(run, id) {
  const message = run.messages.find((item) => item.id === id);
  assert.ok(message, 'expected JSON-RPC response ' + id);
  assert.ok(message.result, 'expected successful JSON-RPC envelope for ' + id);
  return message.result;
}

function toolText(result) {
  return result.content?.[0]?.text || '';
}

function expectToolError(result, pattern) {
  assert.equal(result.isError, true, 'tool call must fail closed');
  assert.match(toolText(result), pattern);
}

function cleanup(fx) {
  fs.rmSync(fx.temp, { recursive: true, force: true });
}

(async () => {
  {
    const fx = fixture();
    try {
      const result = runServer(fx, [
        rpc('tools/list', undefined, 2),
        call('read_approved_sources', {}, 3),
        call('submit_patch_proposal', validProposal(fx.baseSha), 4)
      ]);
      assert.equal(result.status, 0, result.stderr);
      const listed = toolResult(result, 2);
      assert.deepEqual(listed.tools.map((item) => item.name), ['read_approved_sources', 'submit_patch_proposal']);
      const read = toolResult(result, 3);
      assert.equal(read.isError, false);
      assert.match(toolText(read), /return 1;/);
      const readPayload = JSON.parse(toolText(read));
      assert.deepEqual(readPayload.files.map((item) => item.file_path), [SOURCE_B, SOURCE_A].sort());
      assert.equal(readPayload.aggregate_lines_read, 6);
      assert.equal(readPayload.task_context.task_id, TASK_ID);
      assert.equal(readPayload.task_context.task_target_branch, 'dev');
      assert.match(readPayload.task_context.verified_context, /[Oo]wner-approved exact-path context/);
      const submitted = toolResult(result, 4);
      assert.equal(submitted.isError, false);
      assert.match(toolText(submitted), /PROPOSAL_STAGED/);
      const saved = JSON.parse(fs.readFileSync(fx.env.BOONTA_PROPOSAL_PATH, 'utf8'));
      assert.equal(saved.task_id, TASK_ID);
      assert.equal(saved.base_sha, fx.baseSha);
      assert.deepEqual(saved.changed_paths, [SOURCE_A]);
      assert.equal(saved.remote_repository_write_performed, undefined);
    } finally {
      cleanup(fx);
    }
  }

  {
    const fx = fixture();
    try {
      const result = runServer(fx, [
        call('read_approved_sources', { file_path: 'src/other.h', start_line: 1, end_line: 3 }, 2)
      ]);
      expectToolError(toolResult(result, 2), /accepts no arguments/);
      assert.equal(fs.existsSync(fx.env.BOONTA_PROPOSAL_PATH), false);
    } finally {
      cleanup(fx);
    }
  }

  {
    const fx = fixture({
      BOONTA_READ_RANGES: JSON.stringify([
        { path: SOURCE_A, start_line: 1, end_line: 80 },
        { path: SOURCE_B, start_line: 1, end_line: 3 }
      ])
    });
    try {
      const result = runServer(fx, [
        call('read_approved_sources', {}, 2)
      ]);
      expectToolError(toolResult(result, 2), /exceeds source file length/);
    } finally {
      cleanup(fx);
    }
  }

  {
    const fx = fixture();
    try {
      const result = runServer(fx, [
        call('read_approved_sources', {}, 2),
        call('read_approved_sources', {}, 3)
      ]);
      assert.equal(toolResult(result, 2).isError, false);
      expectToolError(toolResult(result, 3), /may be read only once/);
    } finally {
      cleanup(fx);
    }
  }

  {
    const fx = fixture();
    try {
      const contextPath = fx.env.BOONTA_CONTEXT_PATH;
      const context = JSON.parse(fs.readFileSync(contextPath, 'utf8'));
      context.task_id = 'OTHER-TASK';
      fs.writeFileSync(contextPath, JSON.stringify(context), 'utf8');
      const result = runServer(fx, [rpc('tools/list', undefined, 2)]);
      assert.notEqual(result.status, 0, 'server must reject a context for another task');
      assert.match(result.stderr, /does not match the trusted task ID/);
    } finally {
      cleanup(fx);
    }
  }

  {
    const fx = fixture();
    try {
      const contextPath = fx.env.BOONTA_CONTEXT_PATH;
      const actual = fs.readFileSync(contextPath);
      const external = path.join(fx.temp, 'external-context.json');
      fs.writeFileSync(external, actual);
      fs.unlinkSync(contextPath);
      fs.symlinkSync(external, contextPath);
      const result = runServer(fx, [rpc('tools/list', undefined, 2)]);
      assert.notEqual(result.status, 0, 'server must reject a symlink at the exact authorized context path');
      assert.match(result.stderr, /symbolic links are not allowed/);
    } finally {
      cleanup(fx);
    }
  }

  {
    const fx = fixture();
    try {
      fs.writeFileSync(fx.env.BOONTA_CONTEXT_PATH, JSON.stringify({
        task_id: TASK_ID,
        task_title: 'Rival route progress fixture',
        task_description: 'x',
        task_target_branch: 'dev',
        verified_context: 'x'.repeat(17 * 1024)
      }), 'utf8');
      const result = runServer(fx, [rpc('tools/list', undefined, 2)]);
      assert.notEqual(result.status, 0, 'server must reject an oversized task context');
      assert.match(result.stderr, /no larger than 16 KiB/);
    } finally {
      cleanup(fx);
    }
  }

  {
    const fx = fixture();
    try {
      fx.env.BOONTA_CONTEXT_PATH = path.join(fx.runnerTemp, 'context.json');
      fs.writeFileSync(fx.env.BOONTA_CONTEXT_PATH, '{}', 'utf8');
      const result = runServer(fx, [rpc('tools/list', undefined, 2)]);
      assert.notEqual(result.status, 0, 'server must reject a task context outside the one exact workspace path');
      assert.match(result.stderr, /must be exactly GITHUB_WORKSPACE/);
    } finally {
      cleanup(fx);
    }
  }

  {
    const fx = fixture({ BOONTA_READ_PATHS: JSON.stringify(['../outside.txt']) });
    try {
      const result = runServer(fx, [rpc('tools/list', undefined, 2)]);
      assert.notEqual(result.status, 0, 'server must reject traversal paths during startup');
      assert.match(result.stderr, /safe repository paths/);
    } finally {
      cleanup(fx);
    }
  }

  {
    const fx = fixture();
    try {
      const result = runServer(fx, [
        call('submit_patch_proposal', validProposal(fx.baseSha), 2)
      ]);
      expectToolError(toolResult(result, 2), /read_approved_sources must succeed/);
      assert.equal(fs.existsSync(fx.env.BOONTA_PROPOSAL_PATH), false);
    } finally {
      cleanup(fx);
    }
  }

  {
    const fx = fixture();
    try {
      const proposal = validProposal(fx.baseSha, { unified_diff: validDiff('src/other.h') });
      const result = runServer(fx, [call('submit_patch_proposal', proposal, 2)]);
      expectToolError(toolResult(result, 2), /outside the exact owner-approved write-path allow-list/);
      assert.equal(fs.existsSync(fx.env.BOONTA_PROPOSAL_PATH), false);
    } finally {
      cleanup(fx);
    }
  }

  {
    const fx = fixture();
    try {
      const diff = [
        'diff --git a/src/gameplay.h b/src/test.c',
        '--- a/src/gameplay.h',
        '+++ b/src/test.c',
        '@@ -1 +1 @@',
        '-old',
        '+new'
      ].join('\n');
      const result = runServer(fx, [call('submit_patch_proposal', validProposal(fx.baseSha, { unified_diff: diff }), 2)]);
      expectToolError(toolResult(result, 2), /renames and cross-path changes/);
    } finally {
      cleanup(fx);
    }
  }

  {
    const fx = fixture();
    try {
      const proposal = validProposal(fx.baseSha, { unified_diff: validDiff() + '\nnew file mode 100644' });
      const result = runServer(fx, [call('submit_patch_proposal', proposal, 2)]);
      expectToolError(toolResult(result, 2), /binary, mode, rename, copy and submodule/);
    } finally {
      cleanup(fx);
    }
  }

  {
    const fx = fixture();
    try {
      const result = runServer(fx, [call('submit_patch_proposal', validProposal('b'.repeat(40)), 2)]);
      expectToolError(toolResult(result, 2), /base_sha differs from the trusted target checkout/);
    } finally {
      cleanup(fx);
    }
  }

  {
    const fx = fixture();
    try {
      const result = runServer(fx, [call('submit_patch_proposal', validProposal(fx.baseSha, {
        task_id: 'OTHER-TASK'
      }), 2)]);
      expectToolError(toolResult(result, 2), /task_id differs from the trusted reservation/);
    } finally {
      cleanup(fx);
    }
  }

  {
    const fx = fixture();
    try {
      const result = runServer(fx, [call('submit_patch_proposal', validProposal(fx.baseSha, {
        test_ids: ['arbitrary.shell.command']
      }), 2)]);
      expectToolError(toolResult(result, 2), /repository-owned test identifiers/);
    } finally {
      cleanup(fx);
    }
  }

  {
    const fx = fixture();
    try {
      const result = runServer(fx, [
        call('submit_patch_proposal', validProposal(fx.baseSha), 2),
        call('submit_patch_proposal', validProposal(fx.baseSha), 3)
      ]);
      assert.equal(toolResult(result, 2).isError, false);
      expectToolError(toolResult(result, 3), /only one patch proposal/);
    } finally {
      cleanup(fx);
    }
  }

  {
    const fx = fixture({ BOONTA_ALLOWED_PATHS: JSON.stringify(['src/not-readable.h']) });
    try {
      const result = runServer(fx, [rpc('tools/list', undefined, 2)]);
      assert.notEqual(result.status, 0, 'server must refuse startup when a write path is not in the read allow-list');
      assert.match(result.stderr, /write path must also be in the task read-path allow-list/);
    } finally {
      cleanup(fx);
    }
  }

  {
    const fx = fixture({ BOONTA_BASE_SHA: 'c'.repeat(40) });
    try {
      const result = runServer(fx, [rpc('tools/list', undefined, 2)]);
      assert.notEqual(result.status, 0, 'server must refuse a stale target checkout');
      assert.match(result.stderr, /does not match the reserved base SHA/);
    } finally {
      cleanup(fx);
    }
  }

  process.stdout.write('Bounded patch proposal MCP tests passed: one-use bounded task/source context, exact write scope, stale-base rejection and no remote writer surface.\n');
})().catch((error) => {
  process.stderr.write(String(error.stack || error) + '\n');
  process.exitCode = 1;
});
