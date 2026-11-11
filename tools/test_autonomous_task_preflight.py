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


def task(
    task_id: str,
    status: str,
    *,
    complete: bool = True,
    target_branch: str = "main",
) -> dict:
    value = {
        "task_id": task_id,
        "title": "Offline fixture task",
        "status": status,
        "target_branch": target_branch,
        "question_excerpt": "Can the selected task be executed safely?",
        "acceptance_criteria_total": 2,
        "acceptance_criteria_excerpt": [
            "Use the canonical source of truth",
            "Verify the exact target branch",
        ],
        "next_action_excerpt": "Complete one small, source-verified automation task.",
        "platform_scope": ["automation"],
        "pr_url": "",
        "head_sha": "",
    }
    if not complete:
        value["next_action_excerpt"] = ""
    return value


activation = task("AUTOMATION-LEDGER-ACTIVATION", "blocked")
valid_queued = task("AUTOMATION-TEST-QUEUED", "queued")
valid_blocked = task("N64-COMPWOLF-PUPP-T2-PARSE-PROBE", "blocked")
valid_active = task("AUTOMATION-TEST-ACTIVE", "active")
incomplete_active = task("AUTOMATION-TEST-INCOMPLETE", "active", complete=False)
invalid_target = task("AUTOMATION-TEST-INVALID-TARGET", "active", target_branch="feature")
represented_active = task("AUTOMATION-TEST-REPRESENTED", "active")
represented_active["pr_url"] = "https://github.com/Master-Chiken/boonta-reborn-88/pull/999"
represented_active["head_sha"] = "0123456789abcdef0123456789abcdef01234567"
cases = [
    {
        "name": "empty canonical ledger reports EMPTY_QUEUE",
        "tasks": [],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "EMPTY_QUEUE",
    },
    {
        "name": "queued task is visible but not silently promoted",
        "tasks": [valid_queued],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "QUEUED_TASKS_WAITING_FOR_PROMOTION",
        "expected_queued_count": 1,
    },
    {
        "name": "blocked non-activation tasks are not auto-unblocked",
        "tasks": [valid_blocked],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "BLOCKED_TASKS_ONLY",
        "expected_blocked_count": 1,
    },
    {
        "name": "activation same-day backoff is reported separately from empty queue",
        "tasks": [activation],
        "marker_day_offset": 0,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": True,
        "expected_queue_state": "TASK_BACKOFF",
    },
    {
        "name": "open task PR is reported as waiting for reconciliation",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 356,
            "body": "BOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION"
        }],
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": False,
    },
    {
        "name": "trusted owner-authored same-repository task PR is identified as a resume candidate without launching a provider",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 388,
            "state": "open",
            "draft": False,
            "user": {"login": "Master-Chiken"},
            "head": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "AUTOMATION-LEDGER-ACTIVATION", "sha": "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2"},
            "base": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "main"},
            "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/388",
            "body": "BOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION"
        }],
        "expected_ready": false,
        "expected_task_id": "",
        "expected_blocked": false,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": True,
        "expected_resume_pr_number": "388",
    },
    {
        "name": "non-owner task PR is never marked resumable",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 389,
            "state": "open",
            "draft": False,
            "user": {"login": "external-contributor"},
            "head": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "task-branch", "sha": "d5b2fa770b6fed40c006dfbfb4a23949ecb83ae2"},
            "base": {"repo": {"full_name": "Master-Chiken/boonta-reborn-88"}, "ref": "main"},
            "html_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/389",
            "body": "BOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION"
        }],
        "expected_ready": false,
        "expected_task_id": "",
        "expected_blocked": false,
        "expected_queue_state": "WAITING_FOR_OPEN_TASK_PR",
        "expected_resume_candidate": False,
    },
    {
        "name": "activation opens after UTC reset",
        "tasks": [activation],
        "marker_day_offset": None,
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-LEDGER-ACTIVATION",
        "expected_blocked": False,
        "expected_queue_state": "READY",
    },
    {
        "name": "open PR with exact task marker blocks duplicate activation",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 356,
            "body": "Existing automation PR\nBOONTA_TASK_ID: AUTOMATION-LEDGER-ACTIVATION\nBOONTA_TASK_TARGET_BRANCH: main"
        }],
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "reason_contains": "open PR #356",
    },
    {
        "name": "open PR for a different task does not block activation",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{
            "number": 123,
            "body": "BOONTA_TASK_ID: AUTOMATION-OTHER-TASK\nBOONTA_TASK_TARGET_BRANCH: main"
        }],
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-LEDGER-ACTIVATION",
        "expected_blocked": False,
    },
    {
        "name": "100 open PRs fail closed at the bounded inventory ceiling",
        "tasks": [activation],
        "marker_day_offset": None,
        "open_task_prs": [{"number": number, "body": "Unrelated PR"} for number in range(100)],
        "expected_error": "100-item safety ceiling",
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
        "name": "same-day blocked marker allows owner manual re-evaluation",
        "tasks": [activation],
        "marker_day_offset": 0,
        "event_name": "workflow_dispatch",
        "actor": "Master-Chiken",
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-LEDGER-ACTIVATION",
        "expected_blocked": True,
    },
    {
        "name": "same-day blocked marker allows qualifying owner main push",
        "tasks": [activation],
        "marker_day_offset": 0,
        "event_name": "push",
        "actor": "Master-Chiken",
        "expected_ready": True,
        "expected_task_id": "AUTOMATION-LEDGER-ACTIVATION",
        "expected_blocked": True,
    },
    {
        "name": "same-day blocked marker rejects non-owner manual re-evaluation",
        "tasks": [activation],
        "marker_day_offset": 0,
        "event_name": "workflow_dispatch",
        "actor": "untrusted-contributor",
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": True,
        "reason_contains": "same-day UTC backoff",
    },
    {
        "name": "same-day blocked marker rejects non-owner main push",
        "tasks": [activation],
        "marker_day_offset": 0,
        "event_name": "push",
        "actor": "untrusted-contributor",
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": True,
        "reason_contains": "same-day UTC backoff",
    },
    {
        "name": "same-day blocked marker rejects unrelated pull request event",
        "tasks": [activation],
        "marker_day_offset": 0,
        "event_name": "pull_request",
        "actor": "Master-Chiken",
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": True,
        "reason_contains": "same-day UTC backoff",
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
        "expected_queue_state": "READY",
    },
    {
        "name": "multiple active tasks fail closed",
        "tasks": [valid_active, task("AUTOMATION-TEST-SECOND", "active")],
        "marker_day_offset": None,
        "expected_ready": False,
        "expected_task_id": "",
        "expected_blocked": False,
        "expected_queue_state": "ACTIVE_TASK_REQUIRES_RECONCILIATION",
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
        "name": "unsupported task target branch fails closed",
        "tasks": [invalid_target],
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
        "expected_queue_state": "ACTIVE_TASK_REQUIRES_RECONCILIATION",
        "reason_contains": "PR/head",
    },
    {
        "name": "duplicate task IDs fail closed",
        "tasks": [activation, activation],
        "marker_day_offset": None,
        "expected_error": "duplicate task IDs",
    },
    {
        "name": "legacy summary schema fails closed",
        "tasks": [valid_active],
        "marker_day_offset": None,
        "schema_version": 1,
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
    schema_version: testCase.schema_version === undefined ? 2 : testCase.schema_version,
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
      pulls: {{
        list: async (options) => {{
          if (options.state !== "open" || options.per_page !== 100 || options.page !== 1) {{
            throw new Error("unexpected open-PR query");
          }}
          return {{ data: testCase.open_task_prs || [] }};
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
    eventName: testCase.event_name || "schedule",
    actor: testCase.actor || "github-actions[bot]"
  }};
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
    if (testCase.expected_queue_state !== undefined && outputs.queue_state !== testCase.expected_queue_state) {{
      throw new Error(testCase.name + ": expected queue_state=" + testCase.expected_queue_state + ", got " + outputs.queue_state);
    }}
    if (testCase.expected_queued_count !== undefined && outputs.queued_count !== String(testCase.expected_queued_count)) {{
      throw new Error(testCase.name + ": expected queued_count=" + testCase.expected_queued_count + ", got " + outputs.queued_count);
    }}
    if (testCase.expected_blocked_count !== undefined && outputs.blocked_count !== String(testCase.expected_blocked_count)) {{
      throw new Error(testCase.name + ": expected blocked_count=" + testCase.expected_blocked_count + ", got " + outputs.blocked_count);
    }}
    if (testCase.expected_queue_state === "EMPTY_QUEUE" && (
      outputs.task_ready !== "false" || outputs.task_id !== "" || outputs.task_context !== ""
    )) {{
      throw new Error(testCase.name + ": EMPTY_QUEUE must not expose a provider task handoff");
    }}
    if (outputs.task_id !== testCase.expected_task_id) {{
      throw new Error(testCase.name + ": expected task_id=" + testCase.expected_task_id + ", got " + outputs.task_id);
    }}
    if (testCase.expected_resume_candidate !== undefined &&
      outputs.resume_pr_candidate !== String(testCase.expected_resume_candidate)) {{
      throw new Error(testCase.name + ": expected resume_pr_candidate=" + testCase.expected_resume_candidate + ", got " + outputs.resume_pr_candidate);
    }}
    if (testCase.expected_resume_pr_number !== undefined &&
      outputs.resume_pr_number !== testCase.expected_resume_pr_number) {{
      throw new Error(testCase.name + ": expected resume_pr_number=" + testCase.expected_resume_pr_number + ", got " + outputs.resume_pr_number);
    }}
    if (outputs.resume_pr_candidate === "true" && outputs.task_ready !== "false") {{
      throw new Error(testCase.name + ": resume discovery must not authorize a provider before provider-side resume support exists");
    }}
    if (testCase.expected_ready) {{
      if (String(outputs.task_context).length > 2500) {{
        throw new Error(testCase.name + ": task context exceeds the 2,500-character provider handoff budget");
      }}
      const selected = testCase.tasks.find((item) => item.task_id === testCase.expected_task_id);
      if (outputs.task_title !== selected.title || outputs.task_target_branch !== selected.target_branch) {{
        throw new Error(testCase.name + ": selected task title/target branch were not propagated");
      }}
      for (const expectedText of [selected.task_id, selected.title, selected.question_excerpt,
        ...selected.acceptance_criteria_excerpt, selected.next_action_excerpt]) {{
        if (!String(outputs.task_context).includes(expectedText)) {{
          throw new Error(testCase.name + ": task context omitted " + expectedText);
        }}
      }}
    }} else if (outputs.task_title !== "" || outputs.task_target_branch !== "" || outputs.task_context !== "") {{
      throw new Error(testCase.name + ": unselected task context must be empty");
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
