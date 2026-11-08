#!/usr/bin/env python3
"""Offline checks for the one-provider-per-cycle autonomous handoff contract."""

from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "gemini": ROOT / ".github/workflows/gemini-plan-execute.yml",
    "openrouter": ROOT / ".github/workflows/openrouter-plan-execute.yml",
    "groq": ROOT / ".github/workflows/groq-plan-execute.yml",
    "loop": ROOT / ".github/workflows/boonta-autonomous-loop.yml",
    "gemini_prompt": ROOT / ".github/commands/gemini-autonomous-loop.toml",
    "budget": ROOT / "docs/automation/AUTONOMOUS_CONTEXT_BUDGET.md",
    "summary": ROOT / "docs/automation/task-ledger-summary.json",
    "context_builder": ROOT / "tools/build_autonomous_context.py",
    "context_builder_tests": ROOT / "tools/test_autonomous_context.py",
}


def read(name: str) -> str:
    path = FILES[name]
    if not path.is_file():
        raise SystemExit(f"Missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


gemini = read("gemini")
openrouter = read("openrouter")
groq = read("groq")
loop = read("loop")
gemini_prompt = read("gemini_prompt")
budget = read("budget")
context_builder = read("context_builder")
context_builder_tests = read("context_builder_tests")
errors: list[str] = []

# Provider invocations and validated reports must be separately observable.
for label, content in (("OpenRouter", openrouter), ("Groq", groq)):
    if "github_get_file_contents" in content or "github_get_pull_request" in content:
        errors.append(f"{label} prompt references a nonexistent GitHub MCP tool alias")

for content, needle, message in (
    (gemini, "value: ${{ jobs.plan-execute.outputs.invocation_outcome }}", "Gemini must expose its invocation result"),
    (gemini, "invocation_outcome: ${{ steps.run_gemini.outcome }}", "Gemini must publish its actual model-step outcome"),
    (openrouter, "value: ${{ jobs.openrouter-plan-execute.outputs.invocation_outcome }}", "OpenRouter must expose its invocation result"),
    (openrouter, "invocation_outcome: ${{ steps.run_opencode.outcome }}", "OpenRouter must publish its actual model-step outcome"),
    (groq, "value: ${{ jobs.groq-plan-execute.outputs.invocation_outcome }}", "Groq must expose its invocation result"),
    (groq, "invocation_outcome: ${{ steps.run_opencode.outcome }}", "Groq must publish its actual model-step outcome"),
    (gemini, "report_outcome: ${{ steps.validate_report.outcome }}", "Gemini must expose report validation"),
    (openrouter, "report_outcome: ${{ steps.validate_report.outcome }}", "OpenRouter must expose report validation"),
    (groq, "report_outcome: ${{ steps.validate_report.outcome }}", "Groq must expose report validation"),
):
    if needle not in content:
        errors.append(message)

# A provider that failed in this run must not immediately launch another model.
# The next provider is eligible only when its predecessor's persistent UTC
# cooldown was already active during the global preflight at this run's start.
openrouter_job = loop.split("  openrouter-fallback:", 1)[1].split("  groq-fallback:", 1)[0]
groq_job = loop.split("  groq-fallback:", 1)[1].split("  cycle-summary:", 1)[0]
openrouter_gates = (
    "needs.autonomous-cycle.result == 'skipped'",
    "needs.provider-cooldowns.outputs.gemini_active == 'true'",
    "needs.provider-cooldowns.outputs.openrouter_active != 'true'",
    "needs.autonomous-cycle.outputs.invocation_outcome != 'success'",
)
for needle in openrouter_gates:
    if needle not in openrouter_job:
        errors.append(f"OpenRouter next-cycle gate missing: {needle}")
if "needs.autonomous-cycle.result == 'failure'" in openrouter_job:
    errors.append("OpenRouter must not launch after a Gemini failure in the same run")

groq_gates = (
    "needs.autonomous-cycle.result == 'skipped'",
    "needs.provider-cooldowns.outputs.gemini_active == 'true'",
    "needs.openrouter-fallback.result == 'skipped'",
    "needs.provider-cooldowns.outputs.openrouter_active == 'true'",
    "needs.provider-cooldowns.outputs.groq_active != 'true'",
    "needs.openrouter-fallback.outputs.invocation_outcome != 'success'",
)
for needle in groq_gates:
    if needle not in groq_job:
        errors.append(f"Groq next-cycle gate missing: {needle}")
if "needs.openrouter-fallback.result == 'failure'" in groq_job:
    errors.append("Groq must not launch after an OpenRouter failure in the same run")

# The cooldown read path must use GitHub's updated-since filter so every
# six-hour run does not paginate the full append-only #226 comment history.
cooldown_readers = (
    ("global preflight", loop, "Read the three persistent UTC cooldown markers"),
    ("Gemini", gemini, "Check same-day Gemini failure cooldown"),
    ("OpenRouter", openrouter, "Check same-day OpenRouter failure cooldown"),
    ("Groq", groq, "Check same-day Groq failure cooldown"),
)
for label, workflow, step_name in cooldown_readers:
    step_position = workflow.find("name: " + step_name)
    call_position = workflow.find(
        "const comments = await github.paginate(github.rest.issues.listComments, {",
        step_position,
    )
    call_end = workflow.find("});", call_position) if call_position >= 0 else -1
    if step_position < 0 or call_position < 0 or call_end < 0:
        errors.append(f"{label} cooldown read must contain a bounded issue-comment query")
        continue
    call = workflow[call_position:call_end]
    if "since: todayUtc + 'T00:00:00Z'" not in call:
        errors.append(f"{label} cooldown read must filter comments updated since UTC day start")
    if "per_page: 100" not in call:
        errors.append(f"{label} cooldown read must retain bounded page sizing")

# A validated BLOCKED result is a task-level daily backoff, not a provider failure.
task_backoff_contracts = (
    ("Gemini", gemini, "Validate autonomous cycle report contract", "Sync the single-task daily backoff marker", "Record same-day Gemini cooldown after an autonomous model failure"),
    ("OpenRouter", openrouter, "Validate OpenRouter autonomous cycle report", "Sync the single-task daily backoff marker", "Record same-day OpenRouter cooldown after quota, authentication or invocation failure"),
    ("Groq", groq, "Validate Groq autonomous cycle report", "Sync the single-task daily backoff marker", "Record same-day Groq cooldown after an invocation failure"),
)
for label, workflow, validator_title, sync_title, failure_title in task_backoff_contracts:
    validator_position = workflow.find("name: " + validator_title)
    sync_position = workflow.find("name: " + sync_title)
    failure_position = workflow.find("name: " + failure_title)
    if not (0 <= validator_position < sync_position < failure_position):
        errors.append(f"{label} task backoff must follow report validation and precede provider failure cooldown")
    validator_block = workflow[validator_position:sync_position] if validator_position >= 0 and sync_position > validator_position else ""
    for required in ("core.setOutput('blocked_fingerprint'", "core.setOutput('cycle_status', 'blocked')", "require('crypto')"):
        if required not in validator_block:
            errors.append(f"{label} BLOCKED validator must produce a deterministic task fingerprint: {required!r}")
    sync_block = workflow[sync_position:failure_position] if sync_position >= 0 and failure_position > sync_position else ""
    for required in (
        "steps.validate_report.outcome == 'success'",
        "steps.validate_report.outputs.cycle_status == 'blocked'",
        "inputs.task_blocked_active == true",
        "BOONTA_TASK_BLOCKED_COOLDOWN:",
        "BOONTA_TASK_BLOCKED_COOLDOWN_CLEARED:",
        "steps.validate_report.outputs.blocked_fingerprint",
        "github.rest.issues.updateComment",
        "github.rest.issues.createComment",
    ):
        if required not in sync_block:
            errors.append(f"{label} task backoff sync is missing {required!r}")
    failure_block = workflow[failure_position:] if failure_position >= 0 else ""
    failure_condition = failure_block.split("continue-on-error:", 1)[0]
    if "cycle_status == 'blocked'" in failure_condition:
        errors.append(f"{label} valid BLOCKED report must not trigger a provider failure cooldown")
    if "task_queue_state_outcome: ${{ steps.sync_task_queue_state.outcome }}" not in workflow:
        errors.append(f"{label} workflow must expose task-backoff persistence outcome")

for required in (
    "task_blocked_active: ${{ steps.check.outputs.task_blocked_active }}",
    "BOONTA_TASK_BLOCKED_COOLDOWN:",
    "needs.provider-cooldowns.outputs.task_blocked_active != 'true' || github.event_name != 'schedule'",
    "TASK_BLOCKED_ACTIVE: ${{ needs.provider-cooldowns.outputs.task_blocked_active }}",
    "A validated BLOCKED report already exists for the single active task on this UTC day",
    "GEMINI_TASK_QUEUE_STATE",
    "OPENROUTER_TASK_QUEUE_STATE",
    "GROQ_TASK_QUEUE_STATE",
):
    if required not in loop:
        errors.append(f"Autonomous loop task backoff is missing {required!r}")
if loop.count("needs.provider-cooldowns.outputs.task_blocked_active != 'true' || github.event_name != 'schedule'") != 3:
    errors.append("All three provider routes must pause scheduled calls while task backoff is active")

# Report-format/semantic failures also consume an inference request. Record the
# daily cooldown after validation, but only for an actual invocation or report
# failure; a valid BLOCKED report is not a provider failure.
cooldown_contracts = (
    ("Gemini", gemini, "Validate autonomous cycle report contract", "Record same-day Gemini cooldown after an autonomous model failure"),
    ("OpenRouter", openrouter, "Validate OpenRouter autonomous cycle report", "Record same-day OpenRouter cooldown after quota, authentication or invocation failure"),
    ("Groq", groq, "Validate Groq autonomous cycle report", "Record same-day Groq cooldown after an invocation failure"),
)
for label, workflow, validation_title, cooldown_title in cooldown_contracts:
    validation_position = workflow.find("name: " + validation_title)
    cooldown_position = workflow.find("name: " + cooldown_title)
    if not (0 <= validation_position < cooldown_position):
        errors.append(f"{label} cooldown must be recorded after report validation")
    cooldown_block = workflow[cooldown_position:] if cooldown_position >= 0 else ""
    if "steps.validate_report.outcome == 'failure'" not in cooldown_block:
        errors.append(f"{label} cooldown must be recorded when its report validator fails after inference")

if "One model provider invocation at most per Boonta Autonomous Loop run" not in budget:
    errors.append("Shared context budget must enforce at most one model provider invocation per workflow run")
if "At most one provider invocation is allowed per workflow run" not in loop:
    errors.append("Autonomous loop summary must disclose the one-provider-per-run rule")
if "needs: [readiness, provider-cooldowns]" not in loop:
    errors.append("Gemini must depend on the global cooldown preflight")

# Keep all agents bounded to compact text-only context and the common policy.
for label, content, retrieval_budget in (
    ("Gemini", gemini_prompt, "1,500 tokens"),
    ("OpenRouter", openrouter, "1,000 tokens"),
    ("Groq", groq, "300 tokens"),
):
    for required in (
        "docs/automation/AUTONOMOUS_CONTEXT_BUDGET.md",
        "docs/automation/task-ledger-summary.json",
        retrieval_budget,
        "docs/REVERSE_ENGINEERING_FIRST.md",
    ):
        if required not in content:
            errors.append(f"{label} prompt must reference {required!r}")

# Parse the actual OpenCode configuration rather than relying on comment text.
def load_opencode_config(label: str, source: str) -> dict:
    marker = 'cat > "$RUNNER_TEMP/opencode.json" <<\'JSON\'\n'
    pieces = source.split(marker, 1)
    if len(pieces) != 2:
        errors.append(f"{label} OpenCode config is missing")
        return {}
    payload, delimiter, _rest = pieces[1].partition("\n          JSON")
    if not delimiter:
        errors.append(f"{label} OpenCode JSON closing delimiter is missing")
        return {}
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        errors.append(f"{label} OpenCode config is invalid: {exc}")
        return {}


openrouter_config = load_opencode_config("OpenRouter", openrouter)
groq_config = load_opencode_config("Groq", groq)
for label, config in (("OpenRouter", openrouter_config), ("Groq", groq_config)):
    if config.get("agent", {}).get("build", {}).get("steps") != 3:
        errors.append(f"{label} must be limited to three OpenCode build steps")

# OpenRouter must reserve enough daily Free requests for its complete bounded cycle.
openrouter_steps = openrouter_config.get("agent", {}).get("build", {}).get("steps")
reserve_match = re.search(r"(?m)^\s*MIN_REQUESTS_PER_CYCLE=(\d+)\s*$", openrouter)
if not reserve_match:
    errors.append("OpenRouter must declare a daily request reserve before model inference")
elif int(reserve_match.group(1)) != openrouter_steps:
    errors.append(
        f"OpenRouter daily request reserve ({reserve_match.group(1)}) must match its "
        f"configured maximum build steps ({openrouter_steps})"
    )
for required in (
    "if (( quota_remaining >= MIN_REQUESTS_PER_CYCLE )); then",
    "quota_required=$MIN_REQUESTS_PER_CYCLE",
    "QUOTA_REQUIRED: ${{ steps.openrouter_auth_check.outputs.quota_required }}",
    "below the ' + quotaRequired + '-request reserve",
):
    if required not in openrouter:
        errors.append(f"OpenRouter quota reserve must fail closed and report its threshold: {required!r}")

if "quota reserve is not a guarantee of cycle completion" not in budget:
    errors.append("OpenRouter documentation must distinguish the minimum reserve guard from guaranteed cycle completion")
if "watchdog stops on the first explicit" not in budget:
    errors.append("OpenRouter documentation must describe first-refusal process termination and hard-timeout cleanup")

# OpenRouter must stop on the first terminal provider refusal, not consume
# the remainder of its 180-second window in internal retries.
for required in (
    "terminal_provider_error = re.compile(",
    "HTTP\\s*429",
    "tokens per minute\\s*\\(TPM\\)",
    "HTTP\\s*401",
    "free-models-per-day",
    "rate[_ ]limit exceeded",
    "tokens per minute",
    "request too large for model",
    "missing authentication header",
    "terminal_provider_error.search(line)",
    "start_new_session=True",
    "os.killpg(process.pid, signal.SIGTERM)",
    "signal.signal(signal.SIGTERM, handle_shutdown)",
    '"timeout", "--signal=TERM", "--kill-after=5s", "180s"',
    "daily cooldown will be recorded",
):
    if required not in openrouter:
        errors.append(f"OpenRouter first-refusal watchdog is missing required behavior: {required!r}")


# Exercise the exact regex fragments embedded in the workflow against provider
# refusal examples and ordinary output so the guard cannot silently become inert.
regex_start = openrouter.find("terminal_provider_error = re.compile(")
regex_end = openrouter.find("re.IGNORECASE,", regex_start)
if regex_start < 0 or regex_end < 0:
    errors.append("OpenRouter watchdog regex must be extractable for behavior tests")
else:
    regex_block = openrouter[regex_start:regex_end]
    regex_fragments = re.findall(r'r"([^"]*)"', regex_block)
    if len(regex_fragments) != 4:
        errors.append("OpenRouter watchdog must retain exactly four regex fragments")
    else:
        try:
            watchdog = re.compile("".join(regex_fragments), re.IGNORECASE)
            for sample in (
                "Rate limit exceeded: free-models-per-day",
                "Request too large for model openrouter/free on tokens per minute (TPM)",
                "HTTP 429 Too Many Requests",
                "HTTP 401 Unauthorized",
                "Missing Authentication header",
            ):
                if not watchdog.search(sample):
                    errors.append(f"OpenRouter watchdog regex failed to detect a provider refusal: {sample!r}")
            if watchdog.search("The Boonta racing line is wider at the next turn."):
                errors.append("OpenRouter watchdog regex must not match ordinary game-development output")
        except re.error as exc:
            errors.append(f"OpenRouter watchdog regex must compile: {exc}")

openrouter_tools = set(
    openrouter_config.get("mcp", {}).get("github", {}).get("environment", {}).get("GITHUB_TOOLS", "").split(",")
)
groq_tools = set(
    groq_config.get("mcp", {}).get("github", {}).get("environment", {}).get("GITHUB_TOOLS", "").split(",")
)
required_writer_tools = {
    "get_file_contents", "search_pull_requests", "create_branch",
    "push_files", "create_pull_request",
}
for label, toolset in (("OpenRouter", openrouter_tools), ("Groq", groq_tools)):
    if toolset != required_writer_tools:
        errors.append(f"{label} must expose exactly the reviewed five-tool read/search/branch/PR contract")
    forbidden = {
        "issue_read", "list_issues", "list_pull_requests", "create_or_update_file",
        "list_branches", "list_commits", "merge_pull_request", "delete_branch",
        "update_pull_request", "add_issue_comment", "pull_request_read",
        "list_workflow_runs", "list_workflow_jobs", "get_workflow_run", "get_job_logs",
    }
    if forbidden.intersection(toolset):
        errors.append(f"{label} MCP allow-list exposes unnecessary or unsafe tools: {sorted(forbidden.intersection(toolset))}")

required_gemini_ci_tools = {
    "list_workflow_runs", "list_workflow_jobs", "get_workflow_run", "get_job_logs",
}
gemini_settings_match = re.search(r'"includeTools":\s*\[(.*?)\]', gemini, re.DOTALL)
if not gemini_settings_match:
    errors.append("Gemini MCP allow-list is missing")
else:
    gemini_tools = set(re.findall(r'"([^"]+)"', gemini_settings_match.group(1)))
    if not required_writer_tools.issubset(gemini_tools):
        errors.append("Gemini MCP allow-list is missing a bounded branch/PR editing tool")
    if not required_gemini_ci_tools.issubset(gemini_tools):
        errors.append("Gemini must retain bounded read-only PR/Actions CI diagnostic tools")
    if {"merge_pull_request", "delete_branch", "update_pull_request", "list_pull_requests"}.intersection(gemini_tools):
        errors.append("Gemini MCP allow-list exposes an unsafe or unavailable repository mutation/list tool")

# Both OpenCode providers must resolve the actual checked-out repository root,
# validate the selected task against schema v2, and preload policy/context before
# spending provider inference or scarce agent tool steps.
for label, content in (("OpenRouter", openrouter), ("Groq", groq)):
    required = (
        "id: prepare_context",
        "tools/build_autonomous_context.py",
        'git -C "$candidate" rev-parse --show-toplevel',
        'AUTONOMOUS_CONTEXT: ${{ steps.prepare_context.outputs.context }}',
        'REPO_ROOT: ${{ steps.prepare_context.outputs.repo_root }}',
        "steps.prepare_context.outcome == 'success'",
        '"$REPO_ROOT" <<' + "'PY'",
    )
    for needle in required:
        if needle not in content:
            errors.append(f"{label} must resolve the checked-out root and preload schema-v2 context: missing {needle!r}")
    if '"$GITHUB_WORKSPACE" <<' + "'PY'" in content:
        errors.append(f"{label} must not launch OpenCode from the ambiguous outer workspace root")

for required in (
    'summary.get("schema_version") != 2',
    'summary.get("source") != "docs/automation/task-ledger.json"',
    'task.get("title") != task_title or task.get("target_branch") != target_branch',
    'task.get("pr_url") or task.get("head_sha")',
    'task_id != "AUTOMATION-LEDGER-ACTIVATION"',
    'required_handoff_text',
    'task["question_excerpt"]',
    'task["next_action_excerpt"]',
    "if not all(item in bounded_task_context for item in required_handoff_text)",
    "truncates required question, acceptance-criteria or next-action excerpts",
):
    if required not in context_builder:
        errors.append(f"Schema-v2 context builder is missing fail-closed validation {required!r}")
if "tight context budget to reject truncated required task excerpts" not in context_builder_tests:
    errors.append("Schema-v2 context tests must prove required task excerpts are not silently truncated")
# Confirm the Groq cap is below the observed 8k TPM limit and its prompt has a
# pre-inference size guard. The workflow remains €0-only.
groq_limits = (
    groq_config.get("provider", {})
    .get("groq", {})
    .get("models", {})
    .get("openai/gpt-oss-20b", {})
    .get("limit", {})
)
if groq_limits.get("context") != 2048 or groq_limits.get("output") != 256:
    errors.append("Groq must remain capped at 2048 context / 256 output tokens after the observed 8k TPM refusal")
for required in (
    "start_new_session=True",
    "tokens per minute\\s*\\(TPM\\)",
    "free-models-per-day",
    "free-models-per-minute",
    "HTTP\\s*429",
    "HTTP\\s*401",
    "too many requests",
    "missing authentication header",
    "invalid api key",
    "os.killpg(process.pid, signal.SIGTERM)",
    "signal.signal(signal.SIGTERM, handle_shutdown)",
    "signal.signal(signal.SIGINT, handle_shutdown)",
    "sys.exit(75)",
    "report.flush()",
):
    if required not in groq:
        errors.append(f"Groq must stop on the first provider quota refusal: missing {required!r}")
for content, needle, message in (
    (groq, "if (( ${#PROMPT} > 4500 )); then", "Groq must enforce its 4,500-character prompt-size guard before inference"),
    (groq, '"timeout", "--signal=TERM", "--kill-after=5s", "90s"', "Groq must enforce the 90-second invocation timeout"),
    (openrouter, "if (( ${#PROMPT} > 7000 )); then", "OpenRouter must enforce its final-prompt-size guard before inference"),
    (openrouter, '"timeout", "--signal=TERM", "--kill-after=5s", "180s"', "OpenRouter must enforce the 180-second invocation timeout"),
    (groq, "€0 only: no billing, paid routes, credits, alternate providers or secret/settings changes.", "Groq must preserve the €0/no-paid-route rule"),
    (openrouter, "No paid model/provider fallback is available", "OpenRouter must preserve the €0/no-paid-route rule"),
    (openrouter, "Available GitHub tools (exact server names): get_file_contents, search_pull_requests, create_branch, push_files and create_pull_request.", "OpenRouter must document only the exact five exposed GitHub MCP tools"),
    (groq, "Use only these five GitHub tools (exact server names): get_file_contents, search_pull_requests, create_branch, push_files and create_pull_request.", "Groq must document only the exact five exposed GitHub MCP tools"),

):
    if needle not in content:
        errors.append(message)


# Keep autonomous prompts compact and aligned with the already-merged gameplay state.
# A stale rival-AI sequence caused agents to revisit superseded PRs #317/#318/#319.
if len(gemini_prompt) > 8500:
    errors.append(f"Gemini autonomous prompt exceeds the 8,500-character context ceiling: {len(gemini_prompt)}")
if gemini_prompt.count("Keep newly retrieved repository/issue text below 1,500 tokens total.") != 1:
    errors.append("Gemini autonomous prompt must state the 1,500-token retrieval budget exactly once")
for label, content in (("Gemini", gemini_prompt), ("OpenRouter", openrouter), ("Groq", groq), ("Autonomous loop", loop)):
    if "#317 → #318 → #319" in content:
        errors.append(f"{label} instructions still reference the superseded rival-AI PR chain")
    if "69deb6778f9383887118803428e7014686865a83" not in content:
        errors.append(f"{label} instructions must identify the merged PR #327 implementation")
    if "Do not reopen, replay or recreate that chain" not in content:
        errors.append(f"{label} instructions must forbid reopening/recreating superseded PRs #317/#318/#319")

# A provider request is permitted only when the compact ledger yields one eligible task.
for required in (
    "permissions:\n      contents: read\n      issues: read",
    "path: 'docs/automation/task-ledger-summary.json'",
    "ledgerSummary.schema_version !== 2",
    "ledgerSummary.source !== 'docs/automation/task-ledger.json'",
    "ledgerSummary.policy?.max_active_tasks !== 1",
    "new Set(taskIds).size !== taskIds.length",
    "activeTasks.length === 1",
    "activationTask.status === 'blocked'",
    "const usableTask = (task) => Boolean(",
    "Array.isArray(task.platform_scope) && task.platform_scope.length > 0",
    "!taskBlockedActive",
    "core.setOutput('task_ready', String(taskReady))",
):
    if required not in loop:
        errors.append(f"Task eligibility preflight is missing {required!r}")
if loop.count("needs.provider-cooldowns.outputs.task_ready == 'true'") != 3:
    errors.append("All three provider routes must require the same eligible-task preflight")

# The blocked-task marker is referenced during selection. It must be computed
# from today's bot comments before that first reference, not later in the script.
preflight_start = loop.find("      - name: Read the three persistent UTC cooldown markers")
preflight_script_start = loop.find("          script: |", preflight_start)
preflight_script_end = loop.find("\n  autonomous-cycle:", preflight_script_start)
if preflight_start < 0 or preflight_script_start < 0 or preflight_script_end < 0:
    errors.append("Task eligibility preflight script could not be isolated for ordering checks")
else:
    preflight_script = loop[preflight_script_start:preflight_script_end]
    declaration = preflight_script.find("const taskBlockedActive =")
    first_use = preflight_script.find("!taskBlockedActive")
    marker_date = preflight_script.find("const taskBlockedDate =")
    if not (0 <= marker_date < declaration < first_use):
        errors.append("Same-day task-blocked marker must be derived before the first task eligibility reference")
    if preflight_script.count("const taskBlockedActive =") != 1:
        errors.append("Task-blocked state must be initialized exactly once in the global preflight")
    for required in (
        "const taskBlockedDate = taskMarkerComment?.body?.match(taskMarker)?.[1] || '';",
        "const taskBlockedActive = taskBlockedDate === todayUtc;",
        "const botComments = comments.filter((comment) => comment.user?.login === 'github-actions[bot]');",
    ):
        if required not in preflight_script:
            errors.append(f"Task-blocked preflight derivation is missing {required!r}")

# Cycle-fresh reports may cite only PRs created or advanced after the snapshot.
for label, workflow in (("Gemini", gemini), ("OpenRouter", openrouter), ("Groq", groq)):
    for required in (
        "state: 'open'",
        "core.setOutput('snapshot_at', snapshotAt)",
        "PRE_CYCLE_PR_SNAPSHOT_AT",
        "const createdAfterSnapshot = !existedAtStart && Date.parse(pr.created_at || '') > snapshotAt",
        "const advancedDuringCycle = existedAtStart && baseline[String(pr.number)] !== evidence[2]",
    ):
        if required not in workflow:
            errors.append(f"{label} cycle-fresh PR gate is missing {required!r}")
    if "state: 'all'" in workflow:
        errors.append(f"{label} must not paginate closed-PR history before inference")

# Autonomous report identity and branch must match the exact task selected by preflight.
for label, workflow in (("Gemini", gemini), ("OpenRouter", openrouter), ("Groq", groq)):
    for required in (
        "SELECTED_TASK_ID:",
        "SELECTED_TASK_TARGET_BRANCH:",
        "reportedTaskId !== selectedTaskId",
        "evidenceBaseMatch[1] !== selectedTaskTargetBranch",
        "BOONTA_CYCLE_TASK_ID: ",
        "taskMarkers = new Set((pr.body || '').split",
        "taskMarkers.has('BOONTA_TASK_ID: ' + selectedTaskId)",
        "taskMarkers.has('BOONTA_TASK_TARGET_BRANCH: ' + selectedTaskTargetBranch)",
    ):
        if required not in workflow:
            errors.append(f"{label} report validator is missing selected-task integrity check {required!r}")
for label, prompt in (
    ("Gemini", gemini_prompt),
    ("OpenRouter", openrouter),
    ("Groq", groq),
):
    if "BOONTA_CYCLE_TASK_ID: <exact" not in prompt:
        errors.append(f"{label} report instructions must require the exact selected task ID")
    if "BOONTA_TASK_ID: <exact" not in prompt or "BOONTA_TASK_TARGET_BRANCH: <exact" not in prompt:
        errors.append(f"{label} PR instructions must require exact task/target markers in the PR body")

# Reject doubled shell escapes in fallback prompt construction.
for label, workflow in (("OpenRouter", openrouter), ("Groq", groq)):
    prompt_lines = [
        line for line in workflow.splitlines()
        if line.lstrip().startswith("PROMPT=") or line.lstrip().startswith("PROMPT+=")
    ]
    if any((chr(92) * 2 + "n") in line for line in prompt_lines):
        errors.append(f"{label} prompt handoff contains a literal double-escaped newline")

# Gemini Free-tier TPM protection: one model attempt and three session turns.
settings_marker = "          settings: |-\n"
settings_end_marker = "          prompt: ${{ inputs.autonomous_mode && '/gemini-autonomous-loop' || '/gemini-plan-execute' }}"
if settings_marker not in gemini or settings_end_marker not in gemini:
    errors.append("Gemini explicit bounded settings block is missing")
else:
    try:
        settings_text = gemini.split(settings_marker, 1)[1].split(settings_end_marker, 1)[0]
        settings = json.loads(settings_text)
        if settings.get("general", {}).get("maxAttempts") != 1:
            errors.append("Gemini must use one model attempt per invocation")
        if settings.get("model", {}).get("maxSessionTurns") != 3:
            errors.append("Gemini must use a three-turn session ceiling")
    except (json.JSONDecodeError, TypeError) as exc:
        errors.append(f"Gemini bounded settings JSON is invalid: {exc}")
if "exactly 1 attempt per invocation" not in budget or "maximum 3 session turns" not in budget:
    errors.append("Shared context budget must document Gemini's one-attempt/three-turn cap")
if "task-eligibility preflight" not in budget or "one eligible task" not in budget:
    errors.append("Shared context budget must document the pre-inference task gate")

if errors:
    print("Autonomous provider handoff checks FAILED:")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print("Autonomous provider handoff checks passed.")
print("- At most one model provider invocation is allowed per workflow run.")
print("- Fallbacks advance only on later cycles after a pre-existing UTC cooldown.")
print("- Provider limits, CI diagnostics, and €0-only restrictions are enforced.")
