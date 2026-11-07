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
  if (testCase.marker_day_offset !== null) {{
    const markerDate = new Date(Date.now() + testCase.marker_day_offset * 86400000)
      .toISOString().slice(0, 10);
    comments.push({{
      user: {{ login: "github-actions[bot]" }},
      body: "<!-- BOONTA_TASK_BLOCKED_COOLDOWN: " + markerDate + " abcdef0123456789 -->"
    }});
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
    comments.push({{
      user: {{ login: "github-actions[bot]" }},
      body: "<!-- " + prefix + markerDate + " -->"
    }});
  }}
  const ledger = {{
    schema_version: testCase.schema_version === undefined ? 1 : testCase.schema_version,
    source: "docs/automation/task-ledger.json",
    updated_at: todayUtc,
    policy: {{ max_active_tasks: 1 }},
    tasks: testCase.tasks
  }};
  const github = {{
    paginate: async (_endpoint, options) => {{
      if (options.issue_number !== 226 || options.since !== todayUtc + "T00:00:00Z") {{
        throw new Error("unexpected issue-comment query");
      }}
      return comments;
    }},
    rest: {{
      issues: {{ listComments: async () => ({{ data: comments }}) }},
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
  const context = {{ repo: {{ owner: "Master-Chiken", repo: "boonta-reborn-88" }} }};
  let error = "";
  try {{
    await new AsyncFunction("github", "context", "core", script)(github, context, core);
  }} catch (caught) {{
    error = String(caught.message || caught);
  }}
  return {{ outputs, error }};
}}

(async () => {{
  for (const testCase of cases) {{
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
    if (testCase.reason_contains && !String(outputs.task_reason).includes(testCase.reason_contains)) {{
      throw new Error(testCase.name + ": reason did not contain " + testCase.reason_contains);
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
