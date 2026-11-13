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
    "readiness": ROOT / ".github/workflows/boonta-autonomous-readiness.yml",
    "gemini_prompt": ROOT / ".github/commands/gemini-autonomous-loop.toml",
    "budget": ROOT / "docs/automation/AUTONOMOUS_CONTEXT_BUDGET.md",
    "summary": ROOT / "docs/automation/task-ledger-summary.json",
    "cycle_validator": ROOT / "tools/validate_autonomous_cycle_report.js",
    "cycle_validator_tests": ROOT / "tools/test_autonomous_cycle_report.js",
    "context_builder": ROOT / "tools/build_autonomous_context.py",
    "context_builder_tests": ROOT / "tools/test_autonomous_context.py",
    "task_preflight_tests": ROOT / "tools/test_autonomous_task_preflight.py",
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
readiness = read("readiness")

groq_step_ids = re.findall(r"(?m)^        id:\s*([A-Za-z0-9_-]+)\s*$", groq)

gemini_prompt = read("gemini_prompt")
budget = read("budget")
cycle_validator = read("cycle_validator")
cycle_validator_tests = read("cycle_validator_tests")
context_builder = read("context_builder")
context_builder_tests = read("context_builder_tests")
task_preflight_tests = read("task_preflight_tests")
errors: list[str] = []

# Event-driven runs must wake when canonical queue, write-scope or execution
# contracts change. The scheduled cadence remains the backstop; push paths
# prevent these state changes waiting for the next cron window.
push_block = loop.split("  schedule:", 1)[0]
if "    branches:\n      - main\n" not in push_block:
    errors.append("Autonomous loop push trigger must remain restricted to main")
if "  push:\n" not in push_block or "    paths:\n" not in push_block:
    errors.append("Autonomous loop must retain a main-branch push trigger with explicit path filters")
else:
    push_paths = push_block.split("    paths:\n", 1)[1]
    required_push_paths = (
        "docs/automation/task-ledger-summary.json",
        "docs/automation/patch-path-allowlist.json",
        "tools/check_task_ledger.py",
        "tools/check_task_ledger_summary.py",
        "tools/build_autonomous_context.py",
        "tools/validate_autonomous_cycle_report.js",
        "tools/test_autonomous_task_preflight.py",
        "tools/test_autonomous_cycle_report.js",
    )
    for path in required_push_paths:
        if not re.search(r"(?m)^      - " + re.escape(path) + r"\s*$", push_paths):
            errors.append(f"Autonomous loop push trigger is missing canonical dependency {path!r}")

if "- cron: '17 0,6,12,18 * * *'" not in loop:
    errors.append("Autonomous loop must retain four bounded UTC opportunities per day")
if "  workflow_dispatch:\n" not in loop:
    errors.append("Autonomous loop must retain owner-authorized manual dispatch")
if "  repository_dispatch:\n    types: [boonta-provider-fallback]\n" not in loop:
    errors.append("Autonomous loop must expose only the named internal provider-fallback dispatch event")
if "allow_internal_dispatch" not in readiness or "inputs.allow_internal_dispatch == true" not in readiness:
    errors.append("Readiness must permit internal fallback only through its explicit read-only dispatch input")
if "allow_internal_dispatch" not in loop:
    errors.append("Autonomous loop must pass the internal-dispatch readiness input only for the named fallback event")
# Duplicate step IDs make GitHub Actions outputs ambiguous and can cause
# repeated validation/comment side effects. Keep this workflow single-pass.
if len(groq_step_ids) != len(set(groq_step_ids)):
    errors.append("Groq workflow must not contain duplicate step IDs")


# Every provider needs checks:read for the shared exact-head validator, with no
# broader permissions than its existing contents/issues/PR write operations.
for label, workflow in (("Gemini", gemini), ("OpenRouter", openrouter), ("Groq", groq)):
    permissions_match = re.search(
        r"(?ms)^    permissions:\n(?P<block>(?:      [^\n]*\n)+)",
        workflow.split("jobs:", 1)[1] if "jobs:" in workflow else "",
    )
    if not permissions_match:
        errors.append(f"{label} provider workflow must declare explicit least-privilege job permissions")
    else:
        permissions = dict(re.findall(
            r"(?m)^      ([a-zA-Z-]+):\s*['\"]?([a-zA-Z]+)['\"]?\s*$",
            permissions_match.group("block"),
        ))
        expected = {"contents": "write", "issues": "write", "pull-requests": "write", "checks": "read"}
        if permissions != expected:
            errors.append(f"{label} provider job permissions must be contents/issues/PR write plus checks read only; found {permissions!r}")


# The global scheduler hands providers a compact-summary excerpt, but the
# checkout may still contain the previously committed derived projection.
# Refresh that projection in the provider's ephemeral workspace immediately
# before building verified context; fail closed if the task index cannot be rebuilt.
provider_context_refreshes = (
    (
        "Gemini",
        gemini,
        'python3 "$GITHUB_WORKSPACE/tools/check_task_ledger_summary.py" --write',
        'VERIFIED_CONTEXT="$(python3 "$GITHUB_WORKSPACE/tools/build_autonomous_context.py"',
    ),
    (
        "OpenRouter",
        openrouter,
        'python3 "$repo_root/tools/check_task_ledger_summary.py" --write',
        'context="$(python3 "$repo_root/tools/build_autonomous_context.py"',
    ),
    (
        "Groq",
        groq,
        'python3 "$repo_root/tools/check_task_ledger_summary.py" --write',
        'context="$(python3 "$repo_root/tools/build_autonomous_context.py"',
    ),
)
for label, workflow, refresh_command, builder_command in provider_context_refreshes:
    refresh_position = workflow.find(refresh_command)
    builder_position = workflow.find(builder_command)
    if refresh_position < 0:
        errors.append(f"{label} must regenerate the derived task summary in its runner workspace")
    elif builder_position < 0 or refresh_position > builder_position:
        errors.append(f"{label} must refresh the compact task summary before building provider context")


# Gemini CLI exposes MCP tools as mcp_{serverName}_{toolName}. Derive the
# model-facing FQNs from the actual server alias and includeTools configuration.
gemini_settings_marker = "          settings: |-\n"
gemini_settings_end = "          prompt: ${{ inputs.autonomous_mode && '/gemini-autonomous-loop' || '/gemini-plan-execute' }}"
if gemini_settings_marker not in gemini or gemini_settings_end not in gemini:
    errors.append("Gemini MCP settings block is missing; cannot verify model-visible tool names")
else:
    try:
        gemini_settings_text = gemini.split(gemini_settings_marker, 1)[1].split(gemini_settings_end, 1)[0]
        gemini_settings = json.loads(gemini_settings_text)
        gemini_server_name, gemini_server = next(iter(gemini_settings.get("mcpServers", {}).items()))
        raw_gemini_tools = gemini_server.get("includeTools", [])
        expected_gemini_tools = {f"mcp_{gemini_server_name}_{tool}" for tool in raw_gemini_tools}
        missing_gemini_tools = sorted(name for name in expected_gemini_tools if name not in gemini_prompt)
        if gemini_server_name != "github":
            errors.append(f"Gemini GitHub MCP server alias must remain 'github'; found {gemini_server_name!r}")
        if len(raw_gemini_tools) != 11:
            errors.append(f"Gemini GitHub MCP allow-list must remain at 11 tools; found {len(raw_gemini_tools)}")
        if missing_gemini_tools:
            errors.append(f"Gemini autonomous prompt is missing model-visible MCP FQNs: {missing_gemini_tools!r}")
        if "Use GitHub MCP FQNs only:" not in gemini_prompt:
            errors.append("Gemini autonomous prompt must explicitly identify MCP fully qualified names")

        core_tools = gemini_settings.get("tools", {}).get("core", [])
        if core_tools != ["read_file"]:
            errors.append("Gemini autonomous local tools must be limited to read_file for the injected context file")

        for required in (
            "name: 'Checkout selected task target for bounded source context'",
            "ref: ${{ inputs.resume_mode == true && inputs.resume_task_target_branch || inputs.task_target_branch }}",
            "path: .boonta-target-source",
            "tools/build_autonomous_context.py",
            "--source-root \"$TARGET_ROOT\"",
            "--max-source-chars 1600",
            "--arg verified_context",
            "verified_context: $verified_context",
        ):
            if required not in gemini:
                errors.append(f"Gemini must preload bounded excerpts from the exact task target: missing {required!r}")
        for required in (
            "use its `verified_context` as the authoritative task handoff",
            "The only local file read permitted is `.gemini/context.json`",
            "default checkout is never gameplay source evidence",
        ):
            if required not in gemini_prompt:
                errors.append(f"Gemini target-branch context rule is missing {required!r}")
    except (json.JSONDecodeError, StopIteration, AttributeError, TypeError) as exc:
        errors.append(f"Gemini MCP tool-name contract is invalid: {exc}")

for required in (
    "No Explore/subagents/planning or repo-wide discovery; exact task-marker PR search only.",
    "Normal: reconcile, create branch, push one coherent change and open one marked PR.",
    "Resume exposes only `mcp_github_get_file_contents` and `mcp_github_push_files`",
    "Never create a branch/PR",
):
    if required not in gemini_prompt:
        errors.append(f"Gemini direct-execution contract is missing {required!r}")

# OpenCode 1.19.5 exposes MCP tools as top-level names prefixed with the
# sanitized server name. Keep direct mode explicit; do not request Code Mode.
provider_model_visible_tools = (
    ("OpenRouter", openrouter, (
        "github_create_branch",
        "github_push_files",
        "github_create_pull_request",
    )),
    ("Groq", groq, (
        "github_create_branch",
        "github_push_files",
        "github_create_pull_request",
    )),
)
for label, content, tool_names in provider_model_visible_tools:
    missing = [name for name in tool_names if name not in content]
    if missing:
        errors.append(f"{label} prompt is missing OpenCode model-visible GitHub tools: {missing!r}")
    if "OPENCODE_EXPERIMENTAL_CODE_MODE: 'false'" not in content:
        errors.append(f"{label} must explicitly select OpenCode direct MCP tool mode")

# OpenRouter's eight-step ceiling is a hard safety bound, not a discovery budget.
# The preflight performs task reservation and open-PR duplicate detection before inference.
for required in (
    "Do not invoke the Explore Agent, any subagent, Task agent, planning agent or repo-wide discovery.",
    "The global preflight already completed the exact task reservation and open-PR duplicate check.",
    "Do not spend model steps searching PR history, rereading the ledger, or rereading this budget document.",
    "No source reads are available in this mode.",
    "call push_files exactly once with one coherent patch",
    "the shared report validator re-fetches the live PR",
    "NO PROSE OR MARKDOWN FENCES",
):
    if required not in openrouter:
        errors.append(f"OpenRouter direct-execution contract is missing {required!r}")

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

resume_guard_specs = (
    ("Gemini", gemini, "      - name: Revalidate existing task PR after acquiring the shared writer slot", "\n      - name: 'Mint identity token'", "name: 'Run Gemini CLI'"),
    ("OpenRouter", openrouter, "      - name: Revalidate existing task PR after acquiring the shared writer slot", "\n      - name: Mint scoped GitHub App token", "name: Run OpenCode through the OpenRouter Free route"),
    ("Groq", groq, "      - name: Revalidate existing task PR after acquiring the shared writer slot", "\n      - name: Mint scoped GitHub App token", "name: Run OpenCode through the Groq Free route"),
)
for label, workflow, guard_marker, mint_marker, run_marker in resume_guard_specs:
    guard_start = workflow.find(guard_marker)
    guard_end = workflow.find(mint_marker, guard_start)
    guard = workflow[guard_start:guard_end] if guard_start >= 0 and guard_end > guard_start else ""
    if not guard:
        errors.append(f"{label} scheduled resume must have a separate post-queue PR revalidation step")
        continue
    mint_pos = workflow.find(mint_marker.lstrip("\n"), guard_start)
    run_pos = workflow.find(run_marker, guard_start)
    if not (0 <= guard_start < guard_end < mint_pos < run_pos):
        errors.append(f"{label} resume revalidation must complete before minting a write token or invoking the model")
    for required in (
        "inputs.resume_mode == true",
        "RESUME_TASK_ID: ${{ inputs.resume_task_id }}",
        "RESUME_PR_NUMBER: ${{ inputs.resume_pr_number }}",
        "pull.head?.sha !== expectedHeadSha",
        "pull.user?.login !== context.repo.owner",
        "pull.draft !== false",
        "task.pr_url || task.head_sha",
        "bodyLines.filter((line) => line === targetMarker).length !== 1",
    ):
        if required not in guard:
            errors.append(f"{label} resume preflight is missing {required!r}")

for required in (
    "pulls.listFiles({",
    "resumeFilePaths = [...new Set(changedFiles",
    "core.setOutput('resume_file_paths', JSON.stringify(resumeReady ? resumeFilePaths : []))",
):
    if required not in loop:
        errors.append(f"Groq resume preflight is missing verified changed-file handoff: {required!r}")

# Task identity is orchestration metadata: every provider binds the report to
# the exact preflight reservation before parsing or validating its status.
for label, workflow in (("Gemini", gemini), ("OpenRouter", openrouter), ("Groq", groq)):
    if "bindCycleReportToReservedTask" not in workflow:
        errors.append(f"{label} report must bind to the workflow-reserved task ID before validation")
    if "process.env.SELECTED_TASK_TARGET_BRANCH" not in workflow:
        errors.append(f"{label} report binder must receive the trusted target branch")
if "function bindCycleReportToReservedTask(report, expectedTaskId, expectedBase)" not in cycle_validator:
    errors.append("Shared cycle validator must provide the deterministic task-and-base metadata binder")
if "Object.prototype.hasOwnProperty.call(REQUIRED_CHECKS, expectedBase)" not in cycle_validator or "!trimmed.startsWith('BOONTA_CYCLE_EVIDENCE_BASE:')" not in cycle_validator:
    errors.append("Shared cycle validator must validate and bind the reserved evidence base")
if "omitted task ID from its trusted reservation" not in cycle_validator_tests:
    errors.append("Cycle-report tests must cover automatic binding of an omitted task ID")
for required in ("stale model-supplied orchestration metadata must be replaced", "duplicate model-supplied metadata cannot create ambiguity"):
    if required not in cycle_validator_tests:
        errors.append(f"Cycle-report tests must cover {required}")

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
    "needs.provider-cooldowns.outputs.task_ready == 'true'",
    "needs.provider-cooldowns.outputs.gemini_active == 'true'",
    "needs.provider-cooldowns.outputs.openrouter_active == 'true'",
    "needs.provider-cooldowns.outputs.groq_active != 'true'",
)
for needle in groq_gates:
    if needle not in groq_job:
        errors.append(f"Groq next-cycle gate missing: {needle}")
if any(token in groq_job for token in ("needs.autonomous-cycle.result ==", "needs.openrouter-fallback.result ==", "needs.openrouter-fallback.outputs.invocation_outcome")):
    errors.append("Groq eligibility must rely on preflight cooldown markers, never post-invocation provider results")
if re.search(r"openrouter_active == 'true'\s*&&\s*\)", groq_job):
    errors.append("Groq eligibility expression contains a dangling logical operator")
for required in (
    "needs.provider-cooldowns.outputs.task_ready == 'true'",
    "needs.provider-cooldowns.outputs.task_ready != 'true'",
    "needs.provider-cooldowns.outputs.resume_ready == 'true'",
    "resume_mode: ${{ needs.provider-cooldowns.outputs.task_ready != 'true' && needs.provider-cooldowns.outputs.resume_ready == 'true' }}",
    "resume_head_sha: ${{ needs.provider-cooldowns.outputs.resume_head_sha }}",
    "resume_file_paths: ${{ needs.provider-cooldowns.outputs.resume_file_paths }}",
    "needs.provider-cooldowns.outputs.gemini_active == 'true'",
    "needs.provider-cooldowns.outputs.openrouter_active == 'true'",
):
    if required not in groq_job:
        errors.append(f"Groq ordered scheduled-resume route is missing {required!r}")

gemini_resume_job = loop.split("  autonomous-cycle:", 1)[1].split("  openrouter-fallback:", 1)[0]
for required in (
    "needs.provider-cooldowns.outputs.resume_ready == 'true'",
    "needs.provider-cooldowns.outputs.gemini_active != 'true'",
    "resume_mode: ${{ needs.provider-cooldowns.outputs.task_ready != 'true' && needs.provider-cooldowns.outputs.resume_ready == 'true' }}",
    "resume_pr_number:",
    "resume_pr_url:",
):
    if required not in gemini_resume_job:
        errors.append(f"Gemini first-priority scheduled-resume route is missing {required!r}")

for required in (
    "needs.provider-cooldowns.outputs.resume_ready == 'true'",
    "needs.provider-cooldowns.outputs.gemini_active == 'true'",
    "needs.provider-cooldowns.outputs.openrouter_active != 'true'",
    "resume_mode: ${{ needs.provider-cooldowns.outputs.task_ready != 'true' && needs.provider-cooldowns.outputs.resume_ready == 'true' }}",
    "resume_pr_number:",
    "resume_pr_url:",
):
    if required not in openrouter_job:
        errors.append(f"OpenRouter second-priority scheduled-resume route is missing {required!r}")

resume_route = groq_job.split("needs.provider-cooldowns.outputs.task_ready != 'true' &&", 1)[1].split("\n        )", 1)[0] if "needs.provider-cooldowns.outputs.task_ready != 'true' &&" in groq_job else ""
if not resume_route or "needs.provider-cooldowns.outputs.resume_ready == 'true'" not in resume_route:
    errors.append("Groq must have a distinct existing-PR resume branch")
if (
    "github.event_name == 'schedule'" not in resume_route or
    "github.event_name == 'workflow_dispatch'" not in resume_route or
    "github.actor == github.repository_owner" not in resume_route or
    "github.event_name == 'repository_dispatch'" not in resume_route or
    "github.actor == 'github-actions[bot]'" not in resume_route or
    "github.event.action == 'boonta-provider-fallback'" not in resume_route or
    "github.event.client_payload.origin == 'boonta-provider-fallback'" not in resume_route
):
    errors.append("Groq resume must allow scheduled/manual runs and only the trusted internal fallback dispatch")
if (
    "github.event_name == 'schedule'" not in resume_route or
    "github.event_name == 'workflow_dispatch'" not in resume_route or
    "github.actor == github.repository_owner" not in resume_route or
    "github.event_name == 'repository_dispatch'" not in resume_route or
    "github.actor == 'github-actions[bot]'" not in resume_route or
    "github.event.action == 'boonta-provider-fallback'" not in resume_route or
    "github.event.client_payload.origin == 'boonta-provider-fallback'" not in resume_route
):
    errors.append("Groq resume must allow scheduled/manual runs and only the trusted internal fallback dispatch")
for provider_label, route_job in (("Gemini", gemini_resume_job), ("OpenRouter", openrouter_job), ("Groq", groq_job)):
    if "github.event_name == 'schedule'" not in route_job:
        errors.append(f"{provider_label} resume route must remain reachable from scheduled workflow runs")
if "resume_pr_number:\n        type: string\n        required: false" not in groq:
    errors.append("Groq resume PR number must accept the empty-string no-resume handoff and validate only in resume mode")
for required in (
    "resume_mode:",
    "resume_pr_number:",
    "resume_pr_url:",
    "resume_branch:",
    "resume_head_sha:",
    "resume_file_paths:",
    "pull.head?.sha !== expectedHeadSha",
    "bodyLines.filter((line) => line === targetMarker).length !== 1",
    'export GITHUB_TOOLS="get_file_contents,push_files"',
    '"GITHUB_TOOLS": "{env:GITHUB_TOOLS}"',
    "Groq Free, €0 only. Resume exactly one existing task PR.",
    "Only github_get_file_contents and github_push_files are exposed.",
    "Read exactly one listed path using the supplied existing branch as the ref",
):
    if required not in groq:
        errors.append(f"Groq exact-PR resume guard is missing {required!r}")
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
    validator_binding_requirements = (
        (
            "expectedTaskId: selectedTaskId",
            "expectedBase: selectedTargetBranch",
            "const selectedTaskId = process.env.RESUME_MODE === 'true' ? process.env.RESUME_TASK_ID : process.env.SELECTED_TASK_ID;",
            "const selectedTargetBranch = process.env.RESUME_MODE === 'true' ? process.env.RESUME_TASK_TARGET_BRANCH : process.env.SELECTED_TASK_TARGET_BRANCH;",
        )
        if label == "Gemini"
        else (
            "expectedTaskId: process.env.SELECTED_TASK_ID",
            "expectedBase: process.env.SELECTED_TASK_TARGET_BRANCH",
        )
    )
    for required in ("validateAutonomousCycleReport", *validator_binding_requirements):
        if required not in validator_block:
            errors.append(f"{label} must delegate BLOCKED/PROGRESS validation to the shared validator using the reserved task in both modes: {required!r}")
for required in ("core.setOutput('blocked_fingerprint'", "core.setOutput('cycle_status', 'blocked')", "require('crypto')", "const blocker = oneLine(lines, 'BOONTA_CYCLE_BLOCKER')", "const nextAction = oneLine(lines, 'BOONTA_CYCLE_NEXT_ACTION')"):
    if required not in cycle_validator:
        errors.append(f"Shared BLOCKED validator must produce a deterministic task fingerprint: {required!r}")
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
    "needs.provider-cooldowns.outputs.task_blocked_active != 'true' || ((github.event_name == 'workflow_dispatch' || github.event_name == 'push') && github.actor == github.repository_owner)",
    "TASK_BLOCKED_ACTIVE: ${{ needs.provider-cooldowns.outputs.task_blocked_active }}",
    "A validated BLOCKED report already exists for the single active task on this UTC day",
    "GEMINI_TASK_QUEUE_STATE",
    "OPENROUTER_TASK_QUEUE_STATE",
    "GROQ_TASK_QUEUE_STATE",
):
    if required not in loop:
        errors.append(f"Autonomous loop task backoff is missing {required!r}")
if loop.count("needs.provider-cooldowns.outputs.task_blocked_active != 'true' || ((github.event_name == 'workflow_dispatch' || github.event_name == 'push') && github.actor == github.repository_owner)") != 3:
    errors.append("All three provider routes must pause task backoff except for explicit owner push/manual re-evaluation")

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

# Provider failures advance through a new run, never a second model call in
# the failing run. The receiving run must validate its bot-only envelope and
# exact predecessor cooldown state before selecting the next provider.
trusted_dispatch_gate = "github.event_name == 'repository_dispatch' && github.actor == 'github-actions[bot]' && github.event.action == 'boonta-provider-fallback' && github.event.client_payload.origin == 'boonta-provider-fallback'"
if loop.count(trusted_dispatch_gate) != 5:
    errors.append("All main-loop gates must require the exact bot-authenticated fallback dispatch envelope")
for label, workflow, expected_provider, cooldown_id, dispatch_name in (
    ("Gemini", gemini, "gemini", "record_gemini_cooldown", "Dispatch OpenRouter in a separate"),
    ("OpenRouter", openrouter, "openrouter", "record_openrouter_cooldown", "Dispatch Groq in a separate"),
):
    dispatch_pos = workflow.find("      - name: " + dispatch_name)
    dispatch_block = workflow[dispatch_pos:] if dispatch_pos >= 0 else ""
    if (
        "github.rest.repos.createDispatchEvent" not in dispatch_block
        or "event_type: 'boonta-provider-fallback'" not in dispatch_block
        or "failed_provider: '" + expected_provider + "'" not in dispatch_block
        or "steps." + cooldown_id + ".outcome == 'success'" not in dispatch_block
        or "id: " + cooldown_id not in workflow
    ):
        errors.append(f"{label} must dispatch the next provider only after its persistent cooldown step succeeds")
if "github.rest.repos.createDispatchEvent" in groq:
    errors.append("Groq is the terminal provider and must not dispatch another provider")
if (
    "context.eventName === 'repository_dispatch'" not in loop
    or "context.actor === 'github-actions[bot]'" not in loop
    or "Number.isSafeInteger(payload.source_run_id)" not in loop
    or "results.gemini === 'ACTIVE' && results.openrouter === 'clear' && results.groq === 'clear'" not in loop
    or "results.gemini === 'ACTIVE' && results.openrouter === 'ACTIVE' && results.groq === 'clear'" not in loop
):
    errors.append("Global preflight must validate dispatch identity, source run ID and exact provider cooldown order")
for label, workflow, required_provider in (
    ("OpenRouter", openrouter, "gemini"),
    ("Groq", groq, "openrouter"),
):
    expected_env = "CALLER_DISPATCH_FAILED_PROVIDER: ${{ github.event.client_payload.failed_provider }}"
    expected_guard = 'CALLER_DISPATCH_FAILED_PROVIDER:-}" != "' + required_provider + '"'
    if (
        expected_env not in workflow
        or "CALLER_EVENT_ACTION: ${{ github.event.action }}" not in workflow
        or "CALLER_DISPATCH_ORIGIN: ${{ github.event.client_payload.origin }}" not in workflow
        or expected_guard not in workflow
    ):
        errors.append(f"{label} provider guard must bind its dispatch to the exact predecessor and origin")
if (
    "CALLER_EVENT: '${{ github.event_name }}'" not in gemini
    or 'CALLER_EVENT:-}" == "repository_dispatch"' not in gemini
):
    errors.append("Gemini must refuse to run on an internal fallback dispatch")

# Keep the global payload within the reviewed provider task-context ceiling.
if "if (taskReady && taskContext.length > 2500)" not in loop:
    errors.append("Global preflight must fail closed above the 2,500-character task-context limit")
if "task context exceeds the 2,500-character provider handoff budget" not in task_preflight_tests:
    errors.append("Mocked task preflight must test the 2,500-character context ceiling")

# Keep all agents bounded to compact text-only context and the common policy.
for label, content, retrieval_budget in (
    ("Gemini", gemini_prompt, "1,500 tokens"),
    ("OpenRouter", openrouter, "No source-read tool is exposed in new-task mode"),
    ("Groq", groq, "1,800 characters"),
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
if openrouter_config.get("agent", {}).get("build", {}).get("steps") != 8:
    errors.append("OpenRouter must have eight bounded build steps to complete read/branch/push/PR work")
if groq_config.get("agent", {}).get("build", {}).get("steps") != 4:
    errors.append("Groq must have four bounded write/PR/report steps")
elif 4 * (1550 + 256) >= 8000:
    errors.append("Groq four-step nominal input/output budget must remain below the observed 8,000 TPM ceiling")
for label, config in (("OpenRouter", openrouter_config), ("Groq", groq_config)):
    task_permissions = config.get("agent", {}).get("build", {}).get("permission", {}).get("task", {})
    if task_permissions.get("*") != "deny":
        errors.append(f"{label} build agent must deny Task subagents to preserve bounded direct MCP execution")
for label, content in (("OpenRouter", openrouter), ("Groq", groq)):
    if "BOONTA_CYCLE_TASK_ID: " not in content or "TASK_ID}" not in content:
        errors.append(f"{label} must inject the literal preflight-reserved task ID into the final machine report")
    if "BOONTA_CYCLE_EVIDENCE_BASE: " not in content or "TASK_TARGET_BRANCH}" not in content:
        errors.append(f"{label} must inject the literal reserved target branch into the final machine report")

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
if "1,550 context tokens and 256 output tokens" not in budget or "caps verified context at 3,000 characters and task handoff at 1,100 characters" not in budget:
    errors.append("Groq shared budget documentation must match its bounded multi-file context and handoff ceilings")

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

openrouter_config_tools = openrouter_config.get("mcp", {}).get("github", {}).get("environment", {}).get("GITHUB_TOOLS", "")
groq_config_tools = groq_config.get("mcp", {}).get("github", {}).get("environment", {}).get("GITHUB_TOOLS", "")
required_openrouter_normal = {"create_branch", "push_files", "create_pull_request"}
required_resume_tools = {"get_file_contents", "push_files"}
required_groq_tools = {"create_branch", "create_pull_request", "push_files"}
required_writer_tools = {
    "get_file_contents", "search_pull_requests", "create_branch",
    "push_files", "create_pull_request",
}
for label, config_tools, workflow in (
    ("OpenRouter", openrouter_config_tools, openrouter),
    ("Groq", groq_config_tools, groq),
):
    if config_tools != "{env:GITHUB_TOOLS}":
        errors.append(f"{label} must bind its MCP tool list to the explicit mode-specific GITHUB_TOOLS environment")
    else:
        modes = {frozenset(item.split(",")) for item in re.findall(r'(?m)^\s*export GITHUB_TOOLS="([^"]+)"$', workflow)}
        expected = {frozenset(required_resume_tools), frozenset(required_openrouter_normal if label == "OpenRouter" else required_groq_tools)}
        if modes != expected:
            errors.append(f"{label} must expose its normal delivery tools and only targeted read plus push for existing-PR resume")
    if '"GITHUB_TOOLS": "{env:GITHUB_TOOLS}"' not in workflow:
        errors.append(f"{label} container must inherit the exact workflow-selected tool allow-list")

for label, workflow in (("Gemini", gemini),):
    if "GITHUB_TOOLS: ${{ inputs.resume_mode == true && 'get_file_contents,push_files'" not in workflow:
        errors.append("Gemini must reduce its MCP server to targeted read plus push during existing-PR resume")
    if '"GITHUB_TOOLS": "${GITHUB_TOOLS}"' not in workflow or '"-e",\n                    "GITHUB_TOOLS"' not in workflow:
        errors.append("Gemini container must inherit the exact workflow-selected tool allow-list")

for label, toolset in (("OpenRouter", set().union(required_openrouter_normal, required_resume_tools)), ("Groq", set().union(required_groq_tools, required_resume_tools))):
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
    'status == "queued"',
    'task.get("owner_approved") is not True',
    'patch-path-allowlist.json',
    'Exact owner-reviewed write paths (no others): ',
    'Task is not owner-approved, dependency-complete, or the single-writer slot is occupied',
    'required_handoff_text',
    'task["question_excerpt"]',
    'task["next_action_excerpt"]',
    "if not all(item in task_context for item in required_handoff_text)",
    "Verified task excerpts exceed the configured",
):
    if required not in context_builder:
        errors.append(f"Schema-v2 context builder is missing fail-closed validation {required!r}")
if "tight context budget to reject truncated required task excerpts" not in context_builder_tests:
    errors.append("Schema-v2 context tests must prove required task excerpts are not silently truncated")
if "Queued context must fail closed while any dependency is incomplete" not in context_builder_tests:
    errors.append("Schema-v2 context tests must reject queued work with incomplete dependencies")
if "Queued context must fail closed without explicit owner approval" not in context_builder_tests:
    errors.append("Schema-v2 context tests must reject queued work without owner approval")
if "Blocked activation must not reach inference without owner-reviewed write paths" not in context_builder_tests:
    errors.append("Schema-v2 context tests must reject blocked activation without explicit write paths")
if "blocked activation without an owner-reviewed write scope is not sent to a provider" not in task_preflight_tests:
    errors.append("Production task preflight tests must prove missing write scope blocks provider selection")
for label, prompt in (("Gemini", gemini_prompt), ("OpenRouter", openrouter), ("Groq", groq)):
    if "Exact owner-reviewed write paths (no others)" not in prompt:
        errors.append(f"{label} prompt must restrict every model write to the owner-reviewed exact-path list")
# Confirm the Groq cap is below the observed 8k TPM limit and its prompt has a
# pre-inference size guard. The workflow remains €0-only.
groq_limits = (
    groq_config.get("provider", {})
    .get("groq", {})
    .get("models", {})
    .get("openai/gpt-oss-20b", {})
    .get("limit", {})
)
if groq_limits.get("context") != 1550 or groq_limits.get("output") != 256:
    errors.append("Groq must remain capped at 1550 context / 256 output tokens; four invocations reserve 7,224 nominal tokens below the observed 8k TPM ceiling")
groq_model_config = (
    groq_config.get("provider", {})
    .get("groq", {})
    .get("models", {})
    .get("openai/gpt-oss-20b", {})
)
if groq_model_config.get("temperature") is not True:
    errors.append("Groq model must explicitly declare temperature support so OpenCode does not silently drop the build-agent setting")
if groq_config.get("agent", {}).get("build", {}).get("temperature") != 0.2:
    errors.append("Groq build agent must use temperature 0.2 for more deterministic structured tool-call generation")
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
    (groq, "if (( ${#PROMPT} > 5500 )); then", "Groq must enforce its 5,500-character TPM prompt-size guard before inference"),
    (groq, '"timeout", "--signal=TERM", "--kill-after=5s", "90s"', "Groq must enforce the 90-second invocation timeout"),
    (openrouter, "if (( ${#PROMPT} > 7000 )); then", "OpenRouter must enforce its final-prompt-size guard before inference"),

    (openrouter, '"timeout", "--signal=TERM", "--kill-after=5s", "180s"', "OpenRouter must enforce the 180-second invocation timeout"),
    (groq, "No paid routes, billing, credits, or provider/secret/settings changes.", "Groq must preserve the €0/no-paid-route rule"),
    (openrouter, "No paid model/provider fallback is available", "OpenRouter must preserve the €0/no-paid-route rule"),
    (openrouter, "Model-visible top-level tools in new-task mode: github_create_branch, github_push_files and github_create_pull_request.", "OpenRouter must document the exact OpenCode 1.19.5 normal-mode GitHub tool names"),
    (groq, "Normal tools: github_create_branch, github_push_files, github_create_pull_request only.", "Groq normal mode must expose branch, push and PR tools without a source-read tool"),

):
    if needle not in content:
        errors.append(message)


# Measure the actual de-indented heredoc sent to each provider. The prior
# guards only rejected oversized prompts after assembling them; they did not
# prove that the configured maximum context could fit below those guards.
def actual_provider_prompt(label: str, workflow: str) -> str:
    start_marker = "          PROMPT=\"$(cat <<'PROMPT'\n"
    end_marker = "\n          PROMPT\n          )\""
    start = workflow.find(start_marker)
    end = workflow.find(end_marker, start + len(start_marker)) if start >= 0 else -1
    if start < 0 or end < 0:
        errors.append(f"{label} provider prompt heredoc is missing")
        return ""
    body = workflow[start + len(start_marker):end]
    return "\n".join(line[10:] if line.startswith("          ") else line for line in body.splitlines())

def context_limits(label: str, workflow: str, expected_chars: int, expected_task: int) -> None:
    match = re.search(r"--max-chars (\d+) --max-task-context (\d+)", workflow)
    if not match or (int(match.group(1)), int(match.group(2))) != (expected_chars, expected_task):
        errors.append(f"{label} context builder must use the reviewed {expected_chars}/{expected_task}-character limits")

actual_groq_prompt = actual_provider_prompt("Groq", groq)
actual_openrouter_prompt = actual_provider_prompt("OpenRouter", openrouter)
resume_start_marker = "          PROMPT=\"$(cat <<'RESUME_PROMPT'\n"
resume_end_marker = "\n          RESUME_PROMPT\n          )\""
resume_start = groq.find(resume_start_marker)
resume_end = groq.find(resume_end_marker, resume_start + len(resume_start_marker)) if resume_start >= 0 else -1
if resume_start < 0 or resume_end < 0:
    errors.append("Groq compact resume-only prompt is missing")
else:
    resume_body = groq[resume_start + len(resume_start_marker):resume_end]
    resume_body = "\n".join(line[10:] if line.startswith("          ") else line for line in resume_body.splitlines())
    if len(resume_body) > 1400:
        errors.append(f"Groq resume prompt leaves insufficient room under the 5,500-character TPM cap: {len(resume_body)}")
if len(actual_groq_prompt) > 2100:
    errors.append(f"Groq static prompt leaves insufficient room under its 5,500-character TPM cap: {len(actual_groq_prompt)}")
if len(actual_openrouter_prompt) > 3600:
    errors.append(f"OpenRouter static prompt leaves insufficient room under its 7,000-character cap: {len(actual_openrouter_prompt)}")
context_limits("Groq", groq, 3000, 1100)
if "_build_source_excerpt" not in context_builder or "MAX_TOTAL_RANGE_LINES" not in context_builder:
    errors.append("Schema-v2 context builder must validate and preload exact bounded multi-file source ranges")
if "--max-source-chars 1800" not in openrouter or "--source-root \"$GITHUB_WORKSPACE/.boonta-target-source\"" not in openrouter:
    errors.append("OpenRouter must preload exact target-branch source ranges within its 950-character source excerpt budget")
if "--max-criteria 4 --max-next-action 100" not in openrouter:
    errors.append("OpenRouter must retain four bounded acceptance criteria in the compact handoff")
if "No source-read tool is exposed in new-task mode" not in actual_openrouter_prompt or "if they are insufficient, report BLOCKED" not in actual_openrouter_prompt:
    errors.append("OpenRouter normal mode must rely on preloaded excerpts and report BLOCKED when they are insufficient")
if "--max-source-chars 1800" not in groq or "--source-root \"$GITHUB_WORKSPACE/.boonta-target-source\"" not in groq:
    errors.append("Groq must preload exact target-branch source ranges within the 1,800-character source excerpt budget")
if "--max-criteria 4 --max-next-action 100" not in groq:
    errors.append("Groq must use the reviewed compact four-criteria/100-character next-action handoff")
if "No source-read tool is exposed in new-task mode" not in actual_groq_prompt or "if they are insufficient, report BLOCKED" not in actual_groq_prompt:
    errors.append("Groq normal mode must rely on preloaded excerpts and report BLOCKED when they are insufficient")
if "write only the exact owner-reviewed paths listed in context" not in actual_groq_prompt:
    errors.append("Groq normal prompt must restrict every write to explicit owner-reviewed paths")
if "waitingForOwnerApprovedPaths" not in loop or "docs/automation/patch-path-allowlist.json" not in loop:
    errors.append("Global task preflight must block provider launch until exact owner-reviewed write paths exist")
if "_owner_approved_write_paths(root, task_id)" not in context_builder or "blocked activation bootstrap receives write scope" not in context_builder:
    errors.append("Blocked activation context must require an explicit exact-path owner policy entry")
context_limits("OpenRouter", openrouter, 2200, 1000)
if len(actual_groq_prompt) + 3000 + 400 > 5500:
    errors.append("Groq worst-case prompt plus bounded multi-file context and report exceeds its 5,500-character cap")

# Budget the complete normal OpenRouter prompt, not just its static heredoc.
# The runtime appends verified context, same-run provider/App facts, and a
# machine-readable report envelope after the heredoc.
openrouter_facts_start_marker = (
    '          PROMPT="' + "$" + "{PROMPT}\n\n"
    "          SAME-RUN VERIFIED EXECUTION FACTS (authoritative workflow metadata):\n"
)
openrouter_facts_end_marker = (
    "\n          if [[ \"" + "$" + "{RESUME_MODE:-false}\" == \"true\" ]]; then"
)
facts_start = openrouter.find(openrouter_facts_start_marker)
facts_end = (
    openrouter.find(openrouter_facts_end_marker, facts_start + len(openrouter_facts_start_marker))
    if facts_start >= 0 else -1
)
if facts_start < 0 or facts_end < 0:
    errors.append("OpenRouter same-run execution-facts prompt block is missing or malformed")
    openrouter_facts_chars = 0
else:
    facts_block = openrouter[facts_start + len('          PROMPT="' + "$" + "{PROMPT}"):facts_end]
    if facts_block.endswith('"'):
        facts_block = facts_block[:-1]
    facts_block = "\n".join(
        line[10:] if line.startswith("          ") else line
        for line in facts_block.splitlines()
    )
    for token, maximum_value in (
        ("$" + "{OPENROUTER_PREFLIGHT_ALLOWED:-unknown}", "false"),
        ("$" + "{OPENROUTER_AUTH_OUTCOME:-unknown}", "cancelled"),
        ("$" + "{GITHUB_APP_TOKEN_OUTCOME:-unknown}", "cancelled"),
    ):
        facts_block = facts_block.replace(token, maximum_value)
    openrouter_facts_chars = len(facts_block)

openrouter_context_command = re.search(
    r"--max-chars (\d+) --max-task-context (\d+) --max-source-chars (\d+)", openrouter
)
if not openrouter_context_command:
    errors.append("OpenRouter context builder limits cannot be measured for the complete prompt budget")
    openrouter_context_chars = 10_000
else:
    context_max_chars, task_max_chars, source_max_chars = map(int, openrouter_context_command.groups())
    context_prefix = "\n".join((
        "VERIFIED CONTEXT:",
        "€0; no commercial game data; preserve AGPL/MIT and platform provenance.",
        "Canonical ledger v2 verified.",
        "Task:",
    ))
    openrouter_context_chars = min(
        context_max_chars,
        len(context_prefix) + 2 + task_max_chars + source_max_chars,
    )

# Reserve the longest valid task ID, a ten-digit PR number, and a full SHA.
openrouter_report_reserve = len(
    "\n\nBOONTA_CYCLE_TASK_ID: " + "A" * 64
    + "\nBOONTA_CYCLE_STATUS: PROGRESS or BLOCKED"
    + "\nBOONTA_CYCLE_EVIDENCE: https://github.com/Master-Chiken/boonta-reborn-88/pull/"
    + "9" * 10 + " @ " + "a" * 40
    + "\nBOONTA_CYCLE_EVIDENCE_BASE: main"
    + "\nFor BLOCKED, omit the two evidence lines and output exactly one BOONTA_CYCLE_BLOCKER and one BOONTA_CYCLE_NEXT_ACTION."
)
openrouter_total_worst_case = (
    len(actual_openrouter_prompt)
    + openrouter_facts_chars
    + openrouter_context_chars
    + openrouter_report_reserve
)
if openrouter_total_worst_case > 6950:
    errors.append(
        "OpenRouter worst-case complete prompt exceeds the 6,950-character design budget "
        "(7,000-character runtime ceiling with at least 50 characters of headroom): "
        + str(openrouter_total_worst_case)
    )


# Free-tier agents must complete the bounded task without soliciting code from the owner.
for label, prompt in (
    ("Gemini", gemini_prompt),
    ("OpenRouter", actual_openrouter_prompt),
    ("Groq", actual_groq_prompt),
):
    if (
        "Never ask owner for code or file contents." not in prompt
        or "Patch from excerpts or report BLOCKED with the exact gap and next action." not in prompt
    ):
        errors.append(f"{label} prompt must infer a bounded patch or report a concrete blocker without asking the owner")

# Keep Gemini post-merge ledger evidence ranges explicitly bounded.
for required in (
    "1-4 safe paths",
    "1-8 ranges",
    "<=80 lines each",
    "<=240 total",
    "<=256 KiB",
):
    if required not in gemini_prompt:
        errors.append(
            f"Gemini post-merge reconciliation must preserve bounded ledger evidence ranges: {required!r}"
        )


# Keep autonomous prompts compact and aligned with the already-merged gameplay state.
# A stale rival-AI sequence caused agents to revisit superseded PRs #317/#318/#319.
if len(gemini_prompt) > 8500:
    errors.append(f"Gemini autonomous prompt exceeds the 8,500-character context ceiling: {len(gemini_prompt)}")
if gemini_prompt.count("Keep retrieved repo/issue text below 1,500 tokens total.") != 1:
    errors.append("Gemini autonomous prompt must state the 1,500-token retrieval budget exactly once")
for label, content in (("Gemini", gemini_prompt), ("OpenRouter", openrouter), ("Groq", groq), ("Autonomous loop", loop)):
    if "#317 → #318 → #319" in content:
        errors.append(f"{label} instructions still reference the superseded rival-AI PR chain")
    if "69deb6778f9383887118803428e7014686865a83" not in content:
        errors.append(f"{label} instructions must identify the merged PR #327 implementation")
    required_reopen_rule = (
        "never reopen/replay/recreate superseded #317/#318/#319"
        if label == "Gemini"
        else ("Do not reopen, replay or recreate that chain." if label == "Groq" else "Do not reopen, replay or recreate that chain")
    )
    if required_reopen_rule not in content:
        errors.append(f"{label} instructions must forbid reopening/recreating superseded PRs #317/#318/#319")

# Free-agent preflight has already reserved the exact ledger row and rejected a
# matching open task PR. Do not spend scarce inference steps repeating that lookup.
for label, prompt in (("OpenRouter", openrouter), ("Groq", groq)):
    for required in (
        "Global preflight is authoritative",
        "Do not search PR history",
        "pr_url",
        "head_sha",
        "older merged automation PRs",
    ):
        if required not in prompt:
            errors.append(f"{label} prompt is missing preflight-owned task-state rule {required!r}")
for required in (
    "Post-merge reconciliation",
    "exact `BOONTA_TASK_ID: <task_id>` PR-body matches",
    "including merged/closed results",
    "closed-unmerged is not completion",
    "verify live `merged_at`",
    "final `head.sha`",
    "record that original PR URL and exact head SHA as evidence",
    "Never use the ledger-update PR's own SHA as task evidence",
):
    if required not in gemini_prompt:
        errors.append(f"Gemini prompt is missing the post-merge task reconciliation rule {required!r}")

# A provider request is permitted only when the compact ledger yields one eligible task.
for required in (
    "permissions:\n      contents: read\n      issues: read\n      pull-requests: read",
    "path: 'docs/automation/task-ledger-summary.json'",
    "ledgerSummary.schema_version !== 2",
    "ledgerSummary.source !== 'docs/automation/task-ledger.json'",
    "ledgerSummary.policy?.max_active_tasks !== 1",
    "new Set(taskIds).size !== taskIds.length",
    "activeTasks.length === 1",
    "activationTask.status === 'blocked'",
    "const usableTask = (task) => Boolean(",
    "Array.isArray(task.platform_scope) && task.platform_scope.length > 0",
    "ledgerSummary.completed_task_ids",
    "const completedTaskIds = new Set(ledgerSummary.completed_task_ids)",
    "const eligibleQueuedTask = activeTasks.length === 0",
    "task.owner_approved === true",
    "task.depends_on.every((dependencyId) =>",
    "completedTaskIds.has(dependencyId)",
    "const { data: openPullRequests } = await github.rest.pulls.list({",
    "state: 'open'",
    "page: 1",
    "openPullRequests.length >= 100",
    "const openTaskPullRequest = (task) =>",
    "const markerLine = 'BOONTA_TASK_ID: ' + task.task_id",
    "const activationTaskOpenPr = openTaskPullRequest(activationTask)",
    "!activationTaskOpenPr",
    "activeTaskOpenPr",
    "!taskBlockedActive",
    "core.setOutput('task_ready', String(taskReady))",
):
    if required not in loop:
        errors.append(f"Task eligibility preflight is missing {required!r}")
if loop.count("needs.provider-cooldowns.outputs.task_ready == 'true'") != 3:
    errors.append("All three provider routes must require the same eligible-task preflight")

# A skipped provider cycle must explain whether the queue is empty, blocked,
# waiting for task promotion, or waiting for PR reconciliation.
for required in (
    "queue_state: ${{ steps.check.outputs.queue_state }}",
    "queued_count: ${{ steps.check.outputs.queued_count }}",
    "const queuedTasks = ledgerSummary.tasks.filter((task) => task.status === 'queued');",
    "const blockedTasks = ledgerSummary.tasks.filter((task) => task.status === 'blocked');",
    "queueState = 'EMPTY_QUEUE';",
    "queueState = 'QUEUED_TASKS_WAITING_FOR_PROMOTION';",
    "queueState = 'BLOCKED_TASKS_ONLY';",
    "core.setOutput('queue_state', queueState)",
    "QUEUE_STATE: ${{ needs.provider-cooldowns.outputs.queue_state }}",
    "EMPTY_QUEUE — WAITING_FOR_OWNER_APPROVAL",
    "No AI provider was invoked, no provider cooldown was written",
):
    if required not in loop:
        errors.append(f"Autonomous queue-state reporting is missing {required!r}")
for required_case in (
    '"name": "empty canonical ledger reports EMPTY_QUEUE"',
    '"name": "queued task is visible but not silently promoted until its dependency is completed"',
    '"name": "first owner-approved queued task is promoted only after every dependency is completed"',
    '"name": "queued task without explicit owner approval is not promoted"',
    '"name": "blocked non-activation tasks are not auto-unblocked"',
    '"name": "activation same-day backoff is reported separately from empty queue"',
    '"name": "open task PR is reported as waiting for reconciliation"',
):
    if required_case not in task_preflight_tests:
        errors.append(f"Offline task-preflight tests are missing queue-state scenario {required_case!r}")
if 'outputs.queue_state !== testCase.expected_queue_state' not in task_preflight_tests:
    errors.append("Offline task-preflight tests must assert the queue-state output")
if '"name": "open PR with exact task marker blocks duplicate activation"' not in task_preflight_tests:
    errors.append("Offline task-preflight tests must prove an open PR with the exact task marker blocks duplicate inference")
if '"name": "open PR for a different task does not block activation"' not in task_preflight_tests:
    errors.append("Offline task-preflight tests must prove unrelated task markers do not block the selected task")
if '"name": "100 open PRs fail closed at the bounded inventory ceiling"' not in task_preflight_tests:
    errors.append("Offline task-preflight tests must prove the open-PR inventory ceiling fails closed")
if 'options.state !== "open"' not in task_preflight_tests or "options.per_page !== 100" not in task_preflight_tests or "options.page !== 1" not in task_preflight_tests:
    errors.append("Offline task-preflight tests must enforce the bounded one-page open-PR query")

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
        "steps.snapshot_pr_heads.outputs.heads",
        "validateAutonomousCycleReport",
        "snapshotAt: process.env.PRE_CYCLE_PR_SNAPSHOT_AT",
    ):
        if required not in workflow:
            errors.append(f"{label} cycle-fresh PR gate is missing {required!r}")
    if "state: 'all'" in workflow:
        errors.append(f"{label} must not paginate closed-PR history before inference")
for required in (
    "'Validate workflow YAML and embedded Python'",
    "createdAfterSnapshot = !existedAtStart && Date.parse(pr.created_at || '') > snapshotTime",
    "previousHeadSha = existedAtStart ? baseSnapshot[String(pullNumber)] : ''",
    "advancedDuringCycle = existedAtStart && previousHeadSha !== exactHead",
    "commitCreatedDuringCycle",
    "commitTimestamp >= snapshotTime",
    "commitTimestamp <= Date.now() + 5 * 60 * 1000",
    "(!createdAfterSnapshot && !advancedDuringCycle)",
    "contentChangedDuringCycle",
    "previousHeadCommit.commit?.tree?.sha",
    "exactTreeSha",
    "!contentChangedDuringCycle",
    "!commitCreatedDuringCycle",
    "pr.head.sha !== exactHead",
    "headCommit.sha !== exactHead",
    "github.rest.checks.listForRef",
    "run.head_sha === exactHead",
    "run.app?.slug === 'github-actions'",
    "check.status === 'completed' && check.conclusion === 'success'",
    "const { data: finalPr } = await github.rest.pulls.get",
    "finalPr.state !== 'open'",
    "finalPr.head.repo?.full_name !== owner + '/' + repo",
    "finalPr.base.repo?.full_name !== owner + '/' + repo",
    "finalPr.head.sha !== exactHead",
    "finalPr.base.ref !== expectedBase",
    "changed while exact-head CI was running",
):
    if required not in cycle_validator:
        errors.append(f"Shared exact-head validator is missing the cycle-fresh PR gate {required!r}")

# Autonomous report identity and branch must match the exact task selected by preflight.
for label, workflow, report_title in (
    ("Gemini", gemini, "Validate autonomous cycle report contract"),
    ("OpenRouter", openrouter, "Validate OpenRouter autonomous cycle report"),
    ("Groq", groq, "Validate Groq autonomous cycle report"),
):
    report_start = workflow.find("name: " + report_title)
    sync_start = workflow.find("name: Sync the single-task daily backoff marker", report_start)
    report_block = workflow[report_start:sync_start] if report_start >= 0 and sync_start > report_start else ""
    report_binding_requirements = (
        (
            "expectedTaskId: selectedTaskId",
            "expectedBase: selectedTargetBranch",
            "const selectedTaskId = process.env.RESUME_MODE === 'true' ? process.env.RESUME_TASK_ID : process.env.SELECTED_TASK_ID;",
            "const selectedTargetBranch = process.env.RESUME_MODE === 'true' ? process.env.RESUME_TASK_TARGET_BRANCH : process.env.SELECTED_TASK_TARGET_BRANCH;",
            "RESUME_TASK_ID:",
            "RESUME_TASK_TARGET_BRANCH:",
        )
        if label == "Gemini"
        else (
            "expectedTaskId: process.env.SELECTED_TASK_ID",
            "expectedBase: process.env.SELECTED_TASK_TARGET_BRANCH",
            f"SELECTED_TASK_ID: ${{{{ inputs.resume_mode == true && inputs.resume_task_id || inputs.task_id }}}}",
            f"SELECTED_TASK_TARGET_BRANCH: ${{{{ inputs.resume_mode == true && inputs.resume_task_target_branch || inputs.task_target_branch }}}}",
        )
    )
    for required in ("SELECTED_TASK_ID:", "SELECTED_TASK_TARGET_BRANCH:", "validateAutonomousCycleReport", *report_binding_requirements):
        if required not in report_block:
            errors.append(f"{label} report validator handoff is missing dynamic preflight binding {required!r}")
gemini_report_start = gemini.find("name: Validate autonomous cycle report contract")
gemini_report_end = gemini.find("name: Sync the single-task daily backoff marker", gemini_report_start)
gemini_report_block = gemini[gemini_report_start:gemini_report_end] if gemini_report_start >= 0 and gemini_report_end > gemini_report_start else ""
for required in (
    "findBlockedReportContradictions",
    "githubAppTokenMinted: process.env.GITHUB_APP_TOKEN_OUTCOME === 'success'",
):
    if required not in gemini_report_block:
        errors.append(f"Gemini report consistency guard is missing {required!r}")

# Free-tier provider reports must not contradict a GitHub App token that
# was successfully minted earlier in the same cycle. OpenRouter also checks
# its authenticated provider-key preflight through the shared helper.
for required in (
    "GITHUB_APP_TOKEN_OUTCOME: ${{ steps.mint_identity_token.outcome }}",
    "findBlockedReportContradictions",
    "githubAppTokenMinted: process.env.GITHUB_APP_TOKEN_OUTCOME === 'success'",
):
    if required not in groq:
        errors.append(f"Groq report consistency guard is missing {required!r}")

groq_report_start = groq.find("name: Validate Groq autonomous cycle report")
groq_report_end = groq.find("name: Sync the single-task daily backoff marker", groq_report_start)
groq_report_block = groq[groq_report_start:groq_report_end] if groq_report_start >= 0 and groq_report_end > groq_report_start else ""
if r"const lines = summary.split(/\\r?\\n/);" in groq_report_block:
    errors.append("Groq report validator contains a double-escaped line-splitting regex")
if r"const lines = summary.split(/\r?\n/);" not in groq_report_block:
    errors.append("Groq report validator must split machine-readable reports on actual line endings")

for required in (
    "BOONTA_CYCLE_TASK_ID",
    "taskMarker = 'BOONTA_TASK_ID: ' + expectedTaskId",
    "targetBranchMarker = 'BOONTA_TASK_TARGET_BRANCH: ' + expectedBase",
    "bodyHasTaskMarker",
    "bodyHasTargetBranchMarker",
    "taskMarkerCount === 1",
    "targetBranchMarkerCount === 1",
    "evidenceBase !== expectedBase",
    "pr.base.ref !== expectedBase",
):
    if required not in cycle_validator:
        errors.append(f"Shared report validator is missing selected-task integrity check {required!r}")
for required in (
    "validator self-test check is required",
    "missing PR target-branch marker",
    "duplicate PR target-branch markers",
    "required check failed",
    "new PR points at a commit created before this cycle",
    "new PR points at a commit with an implausibly future timestamp",
    "same-name check from an untrusted app is ignored",
    "wait for exact-head checks",
    "dev target uses native build/host/emulator checks",
):
    if required not in cycle_validator_tests:
        errors.append(f"Shared report validator regression suite is missing {required!r}")

for required in (
    "fresh empty commit on an existing PR is not progress",
    "existing PR with changed tree content is eligible for exact-head checks",
    "PR head updated while exact-head CI was polling",
    "PR closed while exact-head CI was polling",
    "PR head repository changed while exact-head CI was polling",
    "PR base changed while exact-head CI was polling",
):
    if required not in cycle_validator_tests:
        errors.append(f"Shared exact-head regression suite is missing {required!r}")

for label, prompt in (
    ("Gemini", gemini_prompt),
    ("OpenRouter", openrouter),
    ("Groq", groq),
):
    if label == "Groq":
        if "copy reserved BOONTA_CYCLE_TASK_ID and EVIDENCE_BASE verbatim." not in prompt or 'REPORT_TASK_ID="BOONTA_CYCLE_TASK_ID: ${TASK_ID}"' not in prompt:
            errors.append("Groq report instructions must require the exact selected task ID")
        if "PR body has standalone BOONTA_TASK_ID and BOONTA_TASK_TARGET_BRANCH." not in prompt:
            errors.append("Groq PR instructions must require exact task/target markers in the PR body")
    else:
        if "BOONTA_CYCLE_TASK_ID: <exact" not in prompt and "The shell appends the exact reserved task ID" not in prompt and "literal reserved value appended below" not in prompt:
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
print("- Fallbacks advance only in separate runs after a fresh preflight confirms the prior provider cooldown.")
print("- Provider limits, CI diagnostics, and €0-only restrictions are enforced.")
