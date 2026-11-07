#!/usr/bin/env python3
"""Execute the production GitHub-script task preflight against offline fixtures."""

from pathlib import Path
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/boonta-autonomous-loop.yml"


def fail(message: str) -> None:
    raise SystemExit(f"Autonomous task preflight test failed: {message}")


if not WORKFLOW.is_file():
    fail("autonomous loop workflow is missing")
node = shutil.which("node")
if not node:
    fail("Node.js is required to execute the production GitHub-script preflight")

lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
try:
    step_index = next(
        index for index, line in enumerate(lines)
        if line.strip() == "- name: Read the three persistent UTC cooldown markers"
    )
    script_index = next(
        index for index in range(step_index, len(lines))
        if lines[index].strip() == "script: |"
    )
except StopIteration:
    fail("could not locate the global provider-cooldown GitHub script")

script_lines = []
for line in lines[script_index + 1:]:
    if line.strip() and len(line) - len(line.lstrip()) < 12:
        break
    script_lines.append(line[12:] if line.startswith("            ") else "")
script = "\n".join(script_lines).rstrip()
if not script or "const taskBlockedActive =" not in script:
    fail("extracted task preflight script is empty or incomplete")


def task(task_id: str, status: str, *, complete: bool = True) -> dict:
    value = {
        "task_id": task_id,
        "title": "Offline fixture task",
        "status": status,
        "next_action_excerpt": "Complete one small, source-verified automation task.",
        "platform_scope": ["automation"],
        "target_branch": "main",
        "pr_url": "",
        "head_sha": "",
    }
    if not complete:
        value["next_action_excerpt"] = ""
    return value


activation = task("AUTOMATION-LEDGER-ACTIVATION", "blocked")
valid_active = task("AUTOMATION-TEST-ACTIVE", "active")
incomplete_active = task("AUTOMATION-TEST-INCOMPLETE", "active", complete=False)
represented_active = task("AUTOMATION-TEST-REPRESENTED", "active")
represented_active["pr_url"] = "https://github.com/Master-Chiken/boonta-reborn-88/pull/999"
represented_active["head_sha"] = "0123456789abcdef0123456789abcdef01234567"
cases = [
    {
        "name": "activation opens after UTC reset",
        "tasks": [activation],
        "marker_day_offset": None,
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-LEDGER-ACTIVATION",
        "expected_blocked": False,
    },
    {
        "name": "same-day blocked marker suppresses activation",
        "tasks": [activation],
        "marker_day_offset": 0,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": True,
    },
    {
        "name": "yesterday marker expires at UTC reset",
        "tasks": [activation],
        "marker_day_offset": -1,
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-LEDGER-ACTIVATION",
        "expected_blocked": False,
    },
    {
        "name": "one complete active task is selected",
        "tasks": [valid_active],
        "marker_day_offset": None,
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-TEST-ACTIVE",
        "expected_blocked": False,
    },
    {
        "name": "multiple active tasks fail closed",
        "tasks": [valid_active, task("AUTOMATION-TEST-SECOND", "active")],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
    },
    {
        "name": "incomplete active task fails closed with precise reason",
        "tasks": [incomplete_active],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "reason_contains": "incomplete",
    },
    {
        "name": "three same-day provider cooldowns are detected",
        "tasks": [valid_active],
        "marker_day_offset": None,
        "provider_marker_offsets": {"gemini": 0, "openrouter": 0, "groq": 0},
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-TEST-ACTIVE",
        "expected_blocked": False,
        "expected_provider_cooldowns": {"gemini": True, "openrouter": True, "groq": True},
    },
    {
        "name": "previous-day provider cooldowns expire after UTC reset",
        "tasks": [valid_active],
        "marker_day_offset": None,
        "provider_marker_offsets": {"gemini": -1, "openrouter": -1, "groq": -1},
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-TEST-ACTIVE",
        "expected_blocked": False,
        "expected_provider_cooldowns": {"gemini": False, "openrouter": False, "groq": False},
    },
    {
        "name": "task with an existing PR or head is not re-selected",
        "tasks": [represented_active],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "reason_contains": "PR/head",
    },
    {
        "name": "duplicate task IDs fail closed",
        "tasks": [activation, activation],
        "marker_day_offset": None,
        "expected_error": "duplicate task IDs",
    },
    {
        "name": "unsupported summary schema fails closed",
        "tasks": [valid_active],
        "marker_day_offset": None,
        "schema_version": 2,
        "expected_error": "schema or one-active-task policy",
    },
    {
        "name": "a live foreign lease blocks the provider",
        "tasks": [valid_active],
        "marker_day_offset": None,
        "lease_payload": {
            "run_id": "1199",
            "task_id": "AUTOMATION-TEST-ACTIVE",
            "fingerprint": "computed-at-runtime",
            "expires_at": "2099-01-01T00:00:00.000Z"
        },
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-TEST-ACTIVE",
        "expected_blocked": False,
        "expected_candidate": "gemini",
        "expected_reserved": False,
        "reason_contains": "task lease is held by run"
    },
    {
        "name": "same workflow run retry reclaims its prior attempt lease",
        "tasks": [valid_active],
        "marker_day_offset": None,
        "run_id": 1200,
        "run_attempt": 2,
        "lease_payload": {
            "run_id": "1200",
            "run_attempt": 1,
            "task_id": "AUTOMATION-TEST-ACTIVE",
            "fingerprint": "computed-at-runtime",
            "expires_at": "2099-01-01T00:00:00.000Z",
            "comment_id": 321
        },
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-TEST-ACTIVE",
        "expected_blocked": False,
        "expected_candidate": "gemini",
        "expected_reserved": True,
        "expected_write": "update"
    },
    {
        "name": "an expired lease is reused instead of adding a comment",
        "tasks": [valid_active],
        "marker_day_offset": None,
        "lease_payload": {
            "run_id": "1111",
            "task_id": "AUTOMATION-TEST-ACTIVE",
            "fingerprint": "computed-at-runtime",
            "expires_at": "2000-01-01T00:00:00.000Z",
            "comment_id": 321
        },
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-TEST-ACTIVE",
        "expected_blocked": False,
        "expected_candidate": "gemini",
        "expected_reserved": True,
        "expected_write": "update"
    },
    {
        "name": "OpenRouter is selected only after Gemini cooldown",
        "tasks": [valid_active],
        "marker_day_offset": None,
        "provider_marker_offsets": {"gemini": 0},
        "openrouter_ready": True,
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-TEST-ACTIVE",
        "expected_blocked": False,
        "expected_candidate": "openrouter",
        "expected_reserved": True,
        "expected_write": "create"
    },
    {
        "name": "Groq remains available when OpenRouter is not configured",
        "tasks": [valid_active],
        "marker_day_offset": None,
        "provider_marker_offsets": {"gemini": 0},
        "openrouter_ready": False,
        "groq_ready": True,
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-TEST-ACTIVE",
        "expected_blocked": False,
        "expected_candidate": "groq",
        "expected_reserved": True,
        "expected_write": "create"
    },
    {
        "name": "all provider cooldowns prevent reservation",
        "tasks": [valid_active],
        "marker_day_offset": None,
        "provider_marker_offsets": {"gemini": 0, "openrouter": 0, "groq": 0},
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-TEST-ACTIVE",
        "expected_blocked": False,
        "expected_candidate": "",
        "expected_reserved": False
    },
    {
        "name": "same-day task backoff suppresses scheduled reservation",
        "tasks": [activation],
        "marker_day_offset": 0,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": True,
        "expected_candidate": "",
        "expected_reserved": False
    }
]

node_program = f"""
const fs = require("node:fs");
const script = {json.dumps(script)};
const cases = JSON.parse(fs.readFileSync(0, "utf8"));
const AsyncFunction = Object.getPrototypeOf(async function() {{}}).constructor;

async function runCase(testCase) {{
  const outputs = {{}};
  const todayUtc = new Date().toISOString().slice(0, 10);
  const comments = [];
  const leaseComments = [];
  if (testCase.marker_day_offset !== null) {{
    const markerDate = new Date(Date.now() + testCase.marker_day_offset * 86400000)
      .toISOString().slice(0, 10);
    const marker = {{
      user: {{ login: "github-actions[bot]" }},
      body: "<!-- BOONTA_TASK_BLOCKED_COOLDOWN: " + markerDate + " abcdef0123456789 -->"
    }};
    comments.push(marker);
    leaseComments.push(marker);
  }}
  const providerPrefixes = {{
    gemini: "BOONTA_GEMINI_FAILURE_COOLDOWN: ",
    openrouter: "BOONTA_OPENROUTER_FAILURE_COOLDOWN: ",
    groq: "BOONTA_GROQ_FAILURE_COOLDOWN: "
  }};
  for (const [provider, dayOffset] of Object.entries(testCase.provider_marker_offsets || {{}})) {{
    const prefix = providerPrefixes[provider];
    if (!prefix) throw new Error("unknown provider fixture: " + provider);
    const markerDate = new Date(Date.now() + dayOffset * 86400000)
      .toISOString().slice(0, 10);
    const marker = {{
      user: {{ login: "github-actions[bot]" }},
      body: "<!-- " + prefix + markerDate + " -->"
    }};
    comments.push(marker);
    leaseComments.push(marker);
  }}
  if (testCase.lease_payload) {{
    const payload = {{
      schema_version: 1,
      run_id: testCase.lease_payload.run_id,
      run_attempt: testCase.lease_payload.run_attempt || 1,
      task_id: testCase.lease_payload.task_id,
      fingerprint: testCase.lease_payload.fingerprint,
      provider: testCase.lease_payload.provider || "gemini",
      issued_at: new Date(Date.now() - 60000).toISOString(),
      expires_at: testCase.lease_payload.expires_at
    }};
    const markerName = testCase.lease_payload.released
      ? "BOONTA_TASK_RESERVATION_RELEASED"
      : "BOONTA_TASK_RESERVATION";
    const encoded = Buffer.from(JSON.stringify(payload), "utf8").toString("base64");
    leaseComments.push({{
      id: testCase.lease_payload.comment_id || 321,
      user: {{ login: "github-actions[bot]" }},
      created_at: new Date(Date.now() - 120000).toISOString(),
      updated_at: new Date(Date.now() - 120000).toISOString(),
      body: "<!-- " + markerName + ": " + encoded + " -->"
    }});
  }}
  const ledger = {{
    schema_version: testCase.schema_version === undefined ? 1 : testCase.schema_version,
    source: "docs/automation/task-ledger.json",
    updated_at: todayUtc,
    policy: {{ max_active_tasks: 1 }},
    tasks: testCase.tasks
  }};
  const expectedLeaseSince = Date.now() - 7 * 24 * 60 * 60 * 1000;
  const writes = [];
  const github = {{
    paginate: async (_endpoint, options) => {{
      if (options.issue_number !== 226) throw new Error("unexpected issue number");
      if (options.since === todayUtc + "T00:00:00Z") return comments;
      if (Math.abs(Date.parse(options.since) - expectedLeaseSince) < 5000) return leaseComments;
      throw new Error("unexpected issue-comment since filter: " + options.since);
    }},
    rest: {{
      issues: {{
        listComments: async () => ({{ data: comments }}),
        createComment: async (options) => {{
          writes.push({{ operation: "create", body: options.body }});
          leaseComments.push({{
            id: 777, user: {{ login: "github-actions[bot]" }},
            created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
            body: options.body
          }});
          return {{ data: {{ id: 777, body: options.body }} }};
        }},
        updateComment: async (options) => {{
          writes.push({{ operation: "update", id: options.comment_id, body: options.body }});
          return {{ data: {{ id: options.comment_id, body: options.body }} }};
        }}
      }},
      repos: {{
        getContent: async (options) => {{
          if (options.path !== "docs/automation/task-ledger-summary.json" || options.ref !== "main") {{
            throw new Error("unexpected canonical-ledger read");
          }}
          return {{
            data: {{
              encoding: "base64",
              content: Buffer.from(JSON.stringify(ledger), "utf8").toString("base64")
            }}
          }};
        }}
      }}
    }}
  }};
  const core = {{
    setOutput: (key, value) => {{ outputs[key] = String(value); }},
    info: () => {{}},
    summary: {{
      addHeading() {{ return this; }},
      addTable() {{ return this; }},
      addRaw() {{ return this; }},
      async write() {{ return this; }}
    }}
  }};
  const context = {{
    repo: {{ owner: "Master-Chiken", repo: "boonta-reborn-88" }},
    runId: String(testCase.run_id || 1200),
    runAttempt: Number(testCase.run_attempt || 1),
    eventName: testCase.event_name || "schedule"
  }};
  const process = {{
    env: {{
      WRITER_STATE: testCase.writer_state === undefined ? "enabled" : testCase.writer_state,
      OPENROUTER_READY: testCase.openrouter_ready === undefined ? "true" : String(testCase.openrouter_ready),
      GROQ_READY: testCase.groq_ready === undefined ? "true" : String(testCase.groq_ready)
    }}
  }};
  let error = "";
  try {{
    await new AsyncFunction("github", "context", "core", "process", "require", script)(github, context, core, process, require);
  }} catch (caught) {{
    error = String(caught.message || caught);
  }}
  return {{ outputs, error, writes }};
}}

(async () => {{
  const fingerprint = require("node:crypto").createHash("sha256")
    .update("AUTOMATION-TEST-ACTIVE", "utf8").digest("hex").slice(0, 16);
  for (const testCase of cases) {{
    if (testCase.lease_payload && testCase.lease_payload.fingerprint === "computed-at-runtime") {{
      testCase.lease_payload.fingerprint = fingerprint;
    }}
    const result = await runCase(testCase);
    if (testCase.expected_error) {{
      if (!result.error.includes(testCase.expected_error)) {{
        throw new Error(testCase.name + ": expected error containing " + testCase.expected_error + ", got " + result.error);
      }}
      process.stdout.write("PASS: " + testCase.name + "\\n");
      continue;
    }}
    if (result.error) throw new Error(testCase.name + ": unexpected preflight error: " + result.error);
    const outputs = result.outputs;
    if (outputs.task_ready !== String(testCase.expected_ready)) {{
      throw new Error(testCase.name + ": expected task_ready=" + testCase.expected_ready + ", got " + outputs.task_ready);
    }}
    if (outputs.task_id !== testCase.expected_task_id) {{
      throw new Error(testCase.name + ": expected task_id=" + testCase.expected_task_id + ", got " + outputs.task_id);
    }}
    if (outputs.task_blocked_active !== String(testCase.expected_blocked)) {{
      throw new Error(testCase.name + ": expected task_blocked_active=" + testCase.expected_blocked + ", got " + outputs.task_blocked_active);
    }}
    if (testCase.reason_contains &&
        ![outputs.task_reason, outputs.reservation_reason].some((reason) =>
          String(reason || '').includes(testCase.reason_contains)
        )) {{
      throw new Error(testCase.name + ": neither task nor reservation reason contained " + testCase.reason_contains);
    }}
    if (testCase.expected_candidate !== undefined && outputs.provider_candidate !== testCase.expected_candidate) {{
      throw new Error(testCase.name + ": expected provider_candidate=" + testCase.expected_candidate + ", got " + outputs.provider_candidate);
    }}
    if (testCase.expected_reserved !== undefined && outputs.reservation_acquired !== String(testCase.expected_reserved)) {{
      throw new Error(testCase.name + ": expected reservation_acquired=" + testCase.expected_reserved + ", got " + outputs.reservation_acquired);
    }}
    if (testCase.expected_write) {{
      const operation = result.writes[0]?.operation || "";
      if (operation !== testCase.expected_write) throw new Error(testCase.name + ": expected " + testCase.expected_write + " comment, got " + operation);
    }}
    for (const [provider, expected] of Object.entries(testCase.expected_provider_cooldowns || {{}})) {{
      if (outputs[provider + "_active"] !== String(expected)) {{
        throw new Error(testCase.name + ": expected " + provider + "_active=" + expected + ", got " + outputs[provider + "_active"]);
      }}
    }}
    process.stdout.write("PASS: " + testCase.name + "\\n");
  }}
}})().catch((error) => {{
  process.stderr.write(String(error.stack || error) + "\\n");
  process.exitCode = 1;
}});
"""

completed = subprocess.run(
    [node, "-e", node_program],
    input=json.dumps(cases),
    text=True,
    capture_output=True,
    check=False,
    timeout=20,
)
if completed.stdout:
    print(completed.stdout, end="")
if completed.returncode != 0:
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")
    fail(f"production preflight execution returned {completed.returncode}")
print(f"Production task preflight passed all {len(cases)} offline scenarios.")
