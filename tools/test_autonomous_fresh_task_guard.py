#!/usr/bin/env python3
"""Exercise the production post-queue task guard with offline GitHub API fixtures."""

from __future__ import annotations

from pathlib import Path
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = (
    ROOT / ".github/workflows/gemini-plan-execute.yml",
    ROOT / ".github/workflows/openrouter-plan-execute.yml",
    ROOT / ".github/workflows/groq-plan-execute.yml",
)


def fail(message: str) -> None:
    raise SystemExit(f"Fresh task guard test failed: {message}")


def extract_script(path: Path) -> str:
    if not path.is_file():
        fail(f"provider workflow is missing: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        step_index = next(
            index for index, line in enumerate(lines)
            if line.strip() == "- name: Revalidate selected task after acquiring the shared writer slot"
        )
        script_index = next(
            index for index in range(step_index, len(lines))
            if lines[index].strip() == "script: |"
        )
    except StopIteration:
        fail(f"post-queue task guard is missing from {path}")
    script_lines = []
    for line in lines[script_index + 1:]:
        if line.strip() and len(line) - len(line.lstrip()) < 12:
            break
        script_lines.append(line[12:] if line.startswith("            ") else "")
    script = "\n".join(script_lines).rstrip()
    if not script or "Fresh task revalidation blocked" not in script:
        fail(f"could not extract the production guard from {path}")
    return script


scripts = [extract_script(path) for path in WORKFLOWS]
if len(set(scripts)) != 1:
    fail("Gemini, OpenRouter and Groq must run the identical post-queue guard")

node = shutil.which("node")
if not node:
    fail("Node.js is required to execute the production GitHub-script guard")

def task(task_id: str, status: str = "active", target_branch: str = "main") -> dict:
    return {
        "task_id": task_id,
        "title": "Offline task fixture",
        "status": status,
        "target_branch": target_branch,
        "question_excerpt": "Can the selected work be executed safely?",
        "acceptance_criteria_excerpt": ["Use live task identity", "Check the exact target branch"],
        "next_action_excerpt": "Perform one bounded implementation step.",
        "platform_scope": ["automation"],
        "pr_url": None,
        "head_sha": None,
    }


def summary(tasks: list[dict]) -> dict:
    return {
        "schema_version": 2,
        "source": "docs/automation/task-ledger.json",
        "updated_at": "2026-11-10",
        "policy": {"max_active_tasks": 1, "completed_requires_merged_pr": True},
        "tasks": tasks,
    }


valid_active = task("AUTOMATION-TEST-ACTIVE")
activation = task("AUTOMATION-LEDGER-ACTIVATION", "blocked")
cases = [
    {
        "name": "valid active task passes after queue wait",
        "task_id": valid_active["task_id"],
        "branch": "main",
        "ledger": summary([valid_active]),
        "open_prs": [],
        "expected_allowed": True,
    },
    {
        "name": "activation bootstrap remains eligible when the queue is otherwise idle",
        "task_id": activation["task_id"],
        "branch": "main",
        "ledger": summary([activation]),
        "open_prs": [],
        "expected_allowed": True,
    },
    {
        "name": "task completed while waiting is rejected",
        "task_id": valid_active["task_id"],
        "branch": "main",
        "ledger": summary([task(valid_active["task_id"], "completed")]),
        "open_prs": [],
        "expected_allowed": False,
    },
    {
        "name": "task reassigned to another branch while waiting is rejected",
        "task_id": valid_active["task_id"],
        "branch": "main",
        "ledger": summary([task(valid_active["task_id"], "active", "dev")]),
        "open_prs": [],
        "expected_allowed": False,
    },
    {
        "name": "matching open task PR blocks duplicate provider call",
        "task_id": valid_active["task_id"],
        "branch": "main",
        "ledger": summary([valid_active]),
        "open_prs": [{
            "number": 456,
            "body": "Task details\nBOONTA_TASK_ID: " + valid_active["task_id"] + "\nBOONTA_TASK_TARGET_BRANCH: main",
        }],
        "expected_allowed": False,
    },
    {
        "name": "open PR for a different task does not block",
        "task_id": valid_active["task_id"],
        "branch": "main",
        "ledger": summary([valid_active]),
        "open_prs": [{
            "number": 123,
            "body": "BOONTA_TASK_ID: AUTOMATION-OTHER-TASK",
        }],
        "expected_allowed": True,
    },
    {
        "name": "multiple active tasks fail closed",
        "task_id": valid_active["task_id"],
        "branch": "main",
        "ledger": summary([valid_active, task("AUTOMATION-SECOND-ACTIVE")]),
        "open_prs": [],
        "expected_allowed": False,
    },
    {
        "name": "duplicate ledger IDs fail closed",
        "task_id": valid_active["task_id"],
        "branch": "main",
        "ledger": summary([valid_active, valid_active]),
        "open_prs": [],
        "expected_allowed": False,
    },
    {
        "name": "task with existing PR evidence is not re-executed",
        "task_id": valid_active["task_id"],
        "branch": "main",
        "ledger": summary([{**valid_active, "pr_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/999"}]),
        "open_prs": [],
        "expected_allowed": False,
    },
    {
        "name": "malformed selected task ID fails closed",
        "task_id": "automation-invalid-id",
        "branch": "main",
        "ledger": summary([valid_active]),
        "open_prs": [],
        "expected_allowed": False,
    },
    {
        "name": "invalid target branch input fails closed",
        "task_id": valid_active["task_id"],
        "branch": "feature",
        "ledger": summary([valid_active]),
        "open_prs": [],
        "expected_allowed": False,
    },
    {
        "name": "activation is blocked while a different task is active",
        "task_id": activation["task_id"],
        "branch": "main",
        "ledger": summary([activation, valid_active]),
        "open_prs": [],
        "expected_allowed": False,
    },
    {
        "name": "open PR inventory ceiling fails closed",
        "task_id": valid_active["task_id"],
        "branch": "main",
        "ledger": summary([valid_active]),
        "open_prs": [{"number": index + 1, "body": "Unrelated PR"} for index in range(100)],
        "expected_allowed": False,
    },
    {
        "name": "wrong canonical issue fails closed",
        "task_id": valid_active["task_id"],
        "branch": "main",
        "issue_number": 279,
        "ledger": summary([valid_active]),
        "open_prs": [],
        "expected_allowed": False,
    },
    {
        "name": "legacy ledger schema fails closed",
        "task_id": valid_active["task_id"],
        "branch": "main",
        "ledger": {**summary([valid_active]), "schema_version": 1},
        "open_prs": [],
        "expected_allowed": False,
    },
]

node_program = f"""
const fs = require("node:fs");
const script = {json.dumps(scripts[0])};
const cases = JSON.parse(fs.readFileSync(0, "utf8"));
const AsyncFunction = Object.getPrototypeOf(async function() {{}}).constructor;

async function runCase(testCase) {{
  const outputs = {{}};
  let failure = "";
  const github = {{
    rest: {{
      repos: {{
        getContent: async (options) => {{
          if (options.path !== "docs/automation/task-ledger-summary.json" || options.ref !== "main") {{
            throw new Error("unexpected canonical ledger request");
          }}
          return {{
            data: {{
              encoding: "base64",
              content: Buffer.from(JSON.stringify(testCase.ledger), "utf8").toString("base64")
            }}
          }};
        }}
      }},
      pulls: {{
        list: async (options) => {{
          if (options.state !== "open" || options.per_page !== 100 || options.page !== 1) {{
            throw new Error("unexpected open PR inventory request");
          }}
          return {{ data: testCase.open_prs }};
        }}
      }}
    }}
  }};
  const core = {{
    setOutput: (key, value) => {{ outputs[key] = String(value); }},
    setFailed: (message) => {{ failure = String(message); }},
    info: () => {{}}
  }};
  const context = {{ repo: {{ owner: "Master-Chiken", repo: "boonta-reborn-88" }} }};
  const process = {{ env: {{
    TASK_ID: testCase.task_id,
    TASK_TARGET_BRANCH: testCase.branch,
    ISSUE_NUMBER: String(testCase.issue_number === undefined ? 226 : testCase.issue_number)
  }} }};
  await new AsyncFunction("github", "context", "core", "process", script)(github, context, core, process);
  return {{ outputs, failure }};
}}

(async () => {{
  for (const testCase of cases) {{
    const result = await runCase(testCase);
    const allowed = result.outputs.allowed === "true" && !result.failure;
    if (allowed !== testCase.expected_allowed) {{
      throw new Error(testCase.name + ": expected allowed=" + testCase.expected_allowed +
        ", got allowed=" + result.outputs.allowed + ", failure=" + result.failure);
    }}
    if (!testCase.expected_allowed && !result.failure.includes("Fresh task revalidation blocked")) {{
      throw new Error(testCase.name + ": rejection did not fail closed visibly");
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
    fail("production post-queue guard did not satisfy the offline regression suite")
print(f"Validated {len(cases)} post-queue guard scenarios across all three providers.")
