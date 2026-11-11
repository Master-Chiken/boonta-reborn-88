#!/usr/bin/env python3
"""Static guardrails for the free-only Gemini GitHub Actions integration.

This test makes no network calls, uses no API key, and never invokes an AI model.
"""
from pathlib import Path
import json
import re
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[1]
errors = []


def read(path: str) -> str:
    file_path = ROOT / path
    if not file_path.is_file():
        errors.append(f"Missing required file: {path}")
        return ""
    return file_path.read_text(encoding="utf-8")


dispatch = read(".github/workflows/gemini-dispatch.yml")
invoke = read(".github/workflows/gemini-invoke.yml")
execute = read(".github/workflows/gemini-plan-execute.yml")
daily = read(".github/workflows/ai-daily-coordinator.yml")
daily_prompt = read(".github/commands/gemini-daily-coordinator.toml")
autonomous = read(".github/workflows/boonta-autonomous-loop.yml")
readiness = read(".github/workflows/boonta-autonomous-readiness.yml")
autonomous_prompt = read(".github/commands/gemini-autonomous-loop.toml")
invoke_prompt = read(".github/commands/gemini-invoke.toml")
execute_prompt = read(".github/commands/gemini-plan-execute.toml")
instructions = read("GEMINI.md")
selftest = read(".github/workflows/branch-automation-selftest.yml")
cycle_validator = read("tools/validate_autonomous_cycle_report.js")
cycle_validator_tests = read("tools/test_autonomous_cycle_report.js")

# The on-demand Gemini action installs its own default /gemini-invoke command,
# whose template uses shell substitutions. Invoke our read-only instructions
# directly through --prompt and keep shell/write tools unavailable to the model.
prompt_marker = "          prompt: |-\n"
if prompt_marker not in invoke:
    errors.append("Gemini on-demand workflow must pass a direct multiline read-only prompt")
else:
    prompt_block = invoke.split(prompt_marker, 1)[1].split(
        "\n      - name: Explain why Gemini was not called", 1
    )[0]
    for required in (
        "strictly read-only repository audit agent",
        "Do not run shell commands",
        "Do not edit files",
        "Budget is exactly €0",
        "BEGIN_UNTRUSTED_REQUEST",
        "${{ inputs.additional_context }}",
        "exact-head",
    ):
        if required not in prompt_block:
            errors.append(f"Gemini on-demand prompt is missing required safety/context text: {required!r}")
    for forbidden in (
        "/gemini-invoke",
        "!{echo $ADDITIONAL_CONTEXT}",
        "!{echo $TITLE}",
        "!{echo $DESCRIPTION}",
    ):
        if forbidden in prompt_block:
            errors.append(f"Gemini on-demand prompt must not invoke shell-backed custom-command content: {forbidden!r}")

if "name: 'Prepare prompt context'" in invoke:
    errors.append("Gemini on-demand workflow must not prepare an unused custom-command context file")

settings_marker = "          settings: |-\n"
settings_end_marker = "          # Pass the read-only instructions directly."
if settings_marker not in invoke or settings_end_marker not in invoke:
    errors.append("Gemini on-demand workflow is missing its explicit read-only tool configuration")
else:
    settings_text = invoke.split(settings_marker, 1)[1].split(settings_end_marker, 1)[0]
    try:
        settings = json.loads(textwrap.dedent(settings_text))
        github_tools = settings.get("mcpServers", {}).get("github", {}).get("includeTools", [])
        core_tools = settings.get("tools", {}).get("core", [])
        if "add_issue_comment" in github_tools:
            errors.append("Read-only Gemini MCP allow-list must not expose add_issue_comment")
        forbidden_tools = {
            "create_branch", "push_files", "create_or_update_file",
            "create_pull_request", "merge_pull_request", "update_pull_request",
        }
        if forbidden_tools.intersection(github_tools):
            errors.append("Read-only Gemini MCP allow-list exposes repository write tools")
        if core_tools != ["read_file", "glob", "grep_search", "list_directory"]:
            errors.append(f"Gemini core tools must remain read-only; found {core_tools!r}")
    except (json.JSONDecodeError, AttributeError, TypeError) as exc:
        errors.append(f"Gemini on-demand read-only settings are invalid: {exc}")

setup = read("docs/AI_AUTOMATION_SETUP.md")
ci_triage = read(".github/workflows/ci-failure-triage.yml")
gamecube_build = read(".github/workflows/gamecube-demo-build.yml")
wii64_tests = read(".github/workflows/wii64-tool-tests.yml")
groq_fallback = read(".github/workflows/groq-plan-execute.yml")

# Every provider invocation and report validator must be visible to the parent
# workflow so the final summary never confuses a cooldown skip with progress.
provider_outputs = (
    ("Gemini", execute, "plan-execute", "run_gemini"),
    ("OpenRouter", read(".github/workflows/openrouter-plan-execute.yml"), "openrouter-plan-execute", "run_opencode"),
    ("Groq", groq_fallback, "groq-plan-execute", "run_opencode"),
)
for provider, workflow, job_name, invocation_step in provider_outputs:
    expected_outputs = (
        f"value: ${{{{ jobs.{job_name}.outputs.invocation_outcome }}}}",
        f"value: ${{{{ jobs.{job_name}.outputs.report_outcome }}}}",
        f"value: ${{{{ jobs.{job_name}.outputs.cycle_status }}}}",
        f"invocation_outcome: ${{{{ steps.{invocation_step}.outcome }}}}",
        f"report_outcome: ${{{{ steps.validate_report.outcome }}}}",
        f"cycle_status: ${{{{ steps.validate_report.outputs.cycle_status }}}}",
        "validateAutonomousCycleReport",
        "expectedTaskId: process.env.SELECTED_TASK_ID",
        "expectedBase: process.env.SELECTED_TASK_TARGET_BRANCH",
    )
    for required in expected_outputs:
        if required not in workflow:
            errors.append(f"{provider} workflow must expose validated invocation/report status: {required!r}")

# A single read-only cooldown preflight avoids starting three provider runners
# when all providers are already suppressed for the current UTC day.
if "  provider-cooldowns:" not in autonomous:
    errors.append("Autonomous loop must precheck all provider cooldown markers before launching model workflows")
else:
    cooldown_job = autonomous.split("  provider-cooldowns:", 1)[1].split("  autonomous-cycle:", 1)[0]
    for required in (
        "needs: readiness",
        "permissions:\n      contents: read\n      issues: read",
        "github.rest.issues.listComments",
        "BOONTA_GEMINI_FAILURE_COOLDOWN:",
        "BOONTA_OPENROUTER_FAILURE_COOLDOWN:",
        "BOONTA_GROQ_FAILURE_COOLDOWN:",
        "new Date().toISOString().slice(0, 10)",
        "gemini_active:",
        "openrouter_active:",
        "groq_active:",
        "task_ready:",
        "task_id:",
        "task_reason:",
        "path: 'docs/automation/task-ledger-summary.json'",
        "ledgerSummary.schema_version !== 2",
        "ledgerSummary.policy?.max_active_tasks !== 1",
        "const usableTask = (task) => Boolean(",
        "typeof task.question_excerpt === 'string' && task.question_excerpt.trim()",
        "Array.isArray(task.acceptance_criteria_excerpt) && task.acceptance_criteria_excerpt.length > 0",
        "['main', 'dev'].includes(task.target_branch)",
        "!taskBlockedActive",
        "core.setOutput('task_ready', String(taskReady))",
        "core.setOutput('task_title', selectedTask?.title || '')",
        "core.setOutput('task_context', taskContext)",
        "core.setOutput('task_target_branch', selectedTask?.target_branch || '')",
    ):
        if required not in cooldown_job:
            errors.append(f"Read-only provider cooldown preflight is missing {required!r}")
if "needs: [readiness, provider-cooldowns]" not in autonomous:
    errors.append("Gemini job must depend on the global provider cooldown preflight")
for field in ("task_id", "task_title", "task_target_branch"):
    expected = f"{field}: ${{{{ needs.provider-cooldowns.outputs.{field} }}}}"
    if autonomous.count(expected) != 3:
        errors.append(f"All three providers must receive the same selected task field {field!r}")
if "task_description: ${{ needs.provider-cooldowns.outputs.task_context }}" not in autonomous:
    errors.append("Gemini must receive the compact selected-task question, acceptance criteria and next action")
if autonomous.count("needs.provider-cooldowns.outputs.task_ready == 'true'") != 3:
    errors.append("All three provider routes must require one eligible ledger task before invocation")
if "needs.provider-cooldowns.outputs.gemini_active != 'true'" not in autonomous:
    errors.append("Gemini job must not start while its UTC cooldown is active")
if "needs.provider-cooldowns.outputs.openrouter_active != 'true'" not in autonomous:
    errors.append("OpenRouter fallback must not start while its UTC cooldown is active")
if "needs.provider-cooldowns.outputs.groq_active != 'true'" not in autonomous:
    errors.append("Groq fallback must not start while its UTC cooldown is active")
if "needs.autonomous-cycle.result == 'skipped'" not in autonomous or "needs.provider-cooldowns.outputs.gemini_active == 'true'" not in autonomous:
    errors.append("OpenRouter must run only on a later cycle where Gemini was skipped by an already-active global cooldown")
if "needs.openrouter-fallback.result == 'skipped'" not in autonomous or "needs.provider-cooldowns.outputs.openrouter_active == 'true'" not in autonomous:
    errors.append("Groq must run only on a later cycle where OpenRouter was skipped by an already-active global cooldown")
if "needs.autonomous-cycle.result == 'failure'" in autonomous or "needs.openrouter-fallback.result == 'failure'" in autonomous:
    errors.append("A failed provider must not trigger another provider invocation in the same workflow run")

summary_marker = "  cycle-summary:"
if summary_marker not in autonomous:
    errors.append("Autonomous loop must always publish a final provider-outcome summary")
else:
    summary_job = autonomous.split(summary_marker, 1)[1]
    for required in (
        "needs: [readiness, provider-cooldowns, autonomous-cycle, openrouter-fallback, groq-fallback]",
        "if: always()",
        "permissions: {}",
        "COOLDOWN_CHECK_RESULT: ${{ needs.provider-cooldowns.result }}",
        "GEMINI_COOLDOWN_ACTIVE: ${{ needs.provider-cooldowns.outputs.gemini_active }}",
        "OPENROUTER_COOLDOWN_ACTIVE: ${{ needs.provider-cooldowns.outputs.openrouter_active }}",
        "GROQ_COOLDOWN_ACTIVE: ${{ needs.provider-cooldowns.outputs.groq_active }}",
        "GEMINI_INVOCATION: ${{ needs.autonomous-cycle.outputs.invocation_outcome }}",
        "GEMINI_REPORT: ${{ needs.autonomous-cycle.outputs.report_outcome }}",
        "OPENROUTER_INVOCATION: ${{ needs.openrouter-fallback.outputs.invocation_outcome }}",
        "GROQ_INVOCATION: ${{ needs.groq-fallback.outputs.invocation_outcome }}",
        "No provider completed a model invocation. No autonomous project progress is confirmed by this run.",
        "a valid BLOCKED report is not progress",
        "Budget remains €0.",
        "Skipped before launching the provider workflow: its same-day UTC cooldown is active.",
        "All three same-day UTC cooldowns are active. No provider workflows were launched and no project progress is claimed.",
    ):
        if required not in summary_job:
            errors.append(f"Autonomous final provider summary is missing {required!r}")

# The approval/write path must be closed unless the owner deliberately enables it.
if "needs.dispatch.outputs.command == 'approve' && vars.GEMINI_WRITE_ENABLED != 'true'" not in dispatch:
    errors.append("Missing locked/write-disabled approval gate in gemini-dispatch.yml")
if "needs.dispatch.outputs.command == 'approve' && vars.GEMINI_WRITE_ENABLED == 'true'" not in dispatch:
    errors.append("Missing exact-true write gate in gemini-dispatch.yml")
if "command = association === 'OWNER' ? 'approve' : 'approve-denied';" not in dispatch:
    errors.append("Only the repository owner may issue the /approve command")
if r"/^@gemini-cli\s+\/approve(?:\s|$)/" not in dispatch:
    errors.append("The /approve command matcher must use a whitespace-aware, anchored expression")
if "approval-denied:" not in dispatch or "The /approve command is restricted to the repository owner" not in dispatch:
    errors.append("Unauthorized approval attempts must be explicitly rejected")
if "GEMINI_WRITE_ENABLED" not in setup or "protect" not in setup.lower():
    errors.append("Setup documentation must require branch protection before enabling writes")

# OpenRouter is allowed only through the audited manual free-model PR reviewer.
openrouter = read(".github/workflows/openrouter-free-review.yml")
openrouter_fallback = read(".github/workflows/openrouter-plan-execute.yml")
workflow_dir = ROOT / ".github" / "workflows"
workflow_files = sorted({*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")})
allowed_openrouter_workflows = {"openrouter-free-review.yml", "openrouter-plan-execute.yml", "boonta-autonomous-readiness.yml"}
for path in workflow_files:
    if path.name in allowed_openrouter_workflows:
        continue
    content = path.read_text(encoding="utf-8").lower()
    if "openrouter_api_key" in content or "openrouter.ai" in content:
        errors.append(f"OpenRouter references are forbidden outside the allowlisted workflows: {path.name}")

trigger_block = openrouter.split("permissions:", 1)[0].lower()
if "workflow_dispatch:" not in trigger_block:
    errors.append("OpenRouter reviewer must be manually triggered with workflow_dispatch only")
if "if: github.actor != github.repository_owner" not in openrouter:
    errors.append("OpenRouter reviewer must restrict manual execution to the repository owner")
if "Only the repository owner may run this workflow." not in openrouter:
    errors.append("OpenRouter reviewer must explicitly reject unauthorized manual runs")
for forbidden_trigger in ("pull_request:", "pull_request_target:", "push:", "schedule:", "issues:", "issue_comment:", "workflow_run:"):
    if forbidden_trigger in trigger_block:
        errors.append(f"OpenRouter reviewer must not have automatic trigger {forbidden_trigger!r}")

# Assert the complete event list, not only a hand-picked denylist.
declared_events = re.findall(r"(?m)^  ([a-zA-Z0-9_-]+):\s*$", trigger_block)
if declared_events != ["workflow_dispatch"]:
    errors.append(f"OpenRouter reviewer must declare workflow_dispatch as its only event; found {declared_events!r}")

# Enforce the complete permission set so extra write capabilities cannot be added unnoticed.
permission_block = openrouter.split("permissions:", 1)[1].split("concurrency:", 1)[0]
declared_permissions = dict(re.findall(r"(?m)^  ([a-zA-Z-]+):\s*([a-zA-Z]+)\s*$", permission_block))
expected_permissions = {"contents": "read", "pull-requests": "read", "issues": "write"}
if declared_permissions != expected_permissions:
    errors.append(f"OpenRouter reviewer permissions must be exactly {expected_permissions!r}; found {declared_permissions!r}")
if 'model: "openrouter/free"' not in openrouter:
    errors.append("OpenRouter reviewer must use the explicit openrouter/free route only")
if "secrets.openrouter_api_key_02" not in openrouter.lower():
    errors.append("OpenRouter reviewer must prefer the OPENROUTER_API_KEY_02 secret (with legacy fallback)")

# Keep the secret out of the step that downloads and inspects the untrusted PR diff.
call_step_marker = "      - name: Call OpenRouter free route"
if call_step_marker not in openrouter:
    errors.append("OpenRouter secret must be isolated in a dedicated model-call step")
else:
    preparation_step, model_call_step = openrouter.split(call_step_marker, 1)
    if "secrets.openrouter_api_key" in preparation_step.lower():
        errors.append("OpenRouter API key must not be available while preparing or scanning the PR diff")
    if "openrouter_api_key: ${{ secrets.openrouter_api_key_02 || secrets.openrouter_api_key }}" not in model_call_step.lower():
        errors.append("OPENROUTER_API_KEY_02 must be preferred, with legacy fallback, only in the dedicated model-call step")
if "limit = 30000" not in openrouter:
    errors.append("OpenRouter reviewer must cap the diff at 30,000 bytes")
if "if grep -eiq" not in openrouter.lower():
    errors.append("OpenRouter reviewer must scan the transmitted diff for common credential patterns")
if not (0 <= openrouter.find("limit = 30000") < openrouter.lower().find("if grep -eiq") < openrouter.find("https://openrouter.ai/api/v1/chat/completions")):
    errors.append("OpenRouter reviewer must truncate and scan the diff before any API request")
if "base.ref" not in openrouter or "head.repo.full_name" not in openrouter:
    errors.append("OpenRouter reviewer must require an open PR targeting main from the same repository")
if "contents: read" not in openrouter or "pull-requests: read" not in openrouter or "issues: write" not in openrouter:
    errors.append("OpenRouter reviewer permissions must be read-only except for publishing issue comments")
if "contents: write" in openrouter or "pull-requests: write" in openrouter or "actions: write" in openrouter:
    errors.append("OpenRouter reviewer must not have repository, PR, or Actions write permissions")
if "No paid fallback will be attempted." not in openrouter:
    errors.append("OpenRouter reviewer must fail closed and never use a paid fallback")

# The result must stay bound to the exact, still-eligible PR reviewed before the external call.
head_binding_requirements = (
    "head_sha:.head.sha",
    "PR_HEAD_SHA: ${{ steps.prepare.outputs.head_sha }}",
    "current.data.state !== 'open'",
    "current.data.base.ref !== 'main'",
    "current.data.head.repo?.full_name !== expectedRepo",
    "current.data.head.sha !== process.env.PR_HEAD_SHA",
    "Reviewed head SHA:",
)
missing_head_binding = [requirement for requirement in head_binding_requirements if requirement not in openrouter]
if missing_head_binding:
    errors.append(f"OpenRouter reviewer is missing exact-head/eligibility safeguards: {missing_head_binding!r}")
head_recheck_position = openrouter.find("const current = await github.rest.pulls.get")
comment_publish_position = openrouter.find("await github.rest.issues.createComment")
if head_recheck_position < 0 or comment_publish_position < 0 or head_recheck_position >= comment_publish_position:
    errors.append("OpenRouter reviewer must re-check PR eligibility and exact head before publishing its comment")

# Revalidate the captured PR state and SHA immediately before any external model request.
if call_step_marker not in openrouter:
    errors.append("OpenRouter reviewer is missing its dedicated model-call step")
else:
    model_call = openrouter.split(call_step_marker, 1)[1]
    preflight_position = model_call.find("current-pr-before-call.json")
    request_position = model_call.find("https://openrouter.ai/api/v1/chat/completions")
    preflight_requirements = (
        "GH_TOKEN: ${{ github.token }}",
        "PR_NUMBER: ${{ steps.prepare.outputs.pr_number }}",
        "PR_HEAD_SHA: ${{ steps.prepare.outputs.head_sha }}",




        "current_state=",
        "current_base=",
        "current_repo=",
        "current_sha=",
        ".state // empty",
        ".base.ref // empty",
        ".head.repo.full_name // empty",
        ".head.sha // empty",
        '"$current_state" != "open"',
        '"$current_base" != "main"',
        '"$current_repo" != "$GH_REPO"',
        '"$current_sha" != "$PR_HEAD_SHA"',
        "Nothing was sent to OpenRouter",
    )
    missing_preflight = [requirement for requirement in preflight_requirements if requirement not in model_call]
    if missing_preflight:
        errors.append(f"OpenRouter model call is missing its pre-request PR state/head guard: {missing_preflight!r}")
    if preflight_position < 0 or request_position < 0 or preflight_position >= request_position:
        errors.append("OpenRouter reviewer must re-check PR eligibility and exact head before sending the diff externally")


# Readiness reports OpenRouter's optional secret/attestation presence without
# making an API request or exposing either value.
for required in (
    "OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY_02 || secrets.OPENROUTER_API_KEY }}",
    "OPENROUTER_FREE_TIER_CONFIRMED: ${{ vars.OPENROUTER_FREE_TIER_CONFIRMED }}",
    "No OpenRouter API request was made.",
    "Gemini remains the only active autonomous model path.",
):
    if required not in readiness:
        errors.append(f"Autonomous readiness is missing safe OpenRouter reporting: {required!r}")

# The autonomous OpenRouter writer is a reusable fallback only. It must not
# declare its own schedule or user-controlled entry point.
fallback_trigger = openrouter_fallback.split("jobs:", 1)[0]
fallback_events = re.findall(r"(?m)^  ([a-zA-Z0-9_-]+):\s*$", fallback_trigger)
if fallback_events != ["workflow_call"]:
    errors.append(f"OpenRouter fallback must be reusable-only; found {fallback_events!r}")
for required in (
    'model": "openrouter/openrouter/free"',
    'small_model": "openrouter/openrouter/free"',
    '"enabled_providers": ["openrouter"]',
    '"bash": "deny"',
    'GEMINI_AUTONOMOUS_ENABLED',
    'OPENROUTER_FREE_TIER_CONFIRMED',
    'OPENROUTER_API_KEY',
    'secrets.OPENROUTER_API_KEY_02 || secrets.OPENROUTER_API_KEY',
    'No paid model/provider fallback is available',
    'ghcr.io/github/github-mcp-server:v0.27.0',
    'GITHUB_TOOLS',
    '"opencode", "run", "--model", "openrouter/openrouter/free",',
    '"timeout", "--signal=TERM", "--kill-after=5s", "180s",',
    'npm install --global opencode-ai@1.19.5',
    'name: Verify OpenRouter Free key authentication without inference',
    'https://openrouter.ai/api/v1/key',
    'Authorization: Bearer ${OPENROUTER_API_KEY}',
    "jq -e '.data.is_free_tier == true'",
    "jq -er '.data.free_model_daily_requests.remaining | numbers'",
    "MIN_REQUESTS_PER_CYCLE=8",
    "quota_required=$MIN_REQUESTS_PER_CYCLE",
    "if (( quota_remaining >= MIN_REQUESTS_PER_CYCLE )); then",
    "Minimum reserve for one bounded OpenCode cycle",
    "quota_available=true",
    "quota_available=false",
    'OPENCODE_AUTH_CONTENT',
    'export OPENCODE_AUTH_CONTENT',
    "openrouter: {type: \"api\", key: $key}",
):
    if required not in openrouter_fallback:
        errors.append(f"OpenRouter fallback is missing required free-only/safety setting {required!r}")
if 'OPENROUTER_FREE_TIER_CONFIRMED:-}" != "true"' not in openrouter_fallback:
    errors.append("OpenRouter fallback must require the owner's exact-true Free-tier attestation")
if 'GEMINI_AUTONOMOUS_ENABLED:-}" != "true"' not in openrouter_fallback:
    errors.append("OpenRouter fallback must inherit the master autonomous owner gate")
fallback_guard = openrouter_fallback.find("id: free_tier_guard")
fallback_auth = openrouter_fallback.find("name: Verify OpenRouter Free key authentication without inference")
fallback_mint = openrouter_fallback.find("name: Mint scoped GitHub App token")
fallback_checkout = openrouter_fallback.find("name: Checkout the protected default branch")
fallback_install = openrouter_fallback.find("name: Install pinned OpenCode CLI")
fallback_model = openrouter_fallback.find("name: Run OpenCode through the OpenRouter Free route")
if not (0 <= fallback_guard < fallback_auth < fallback_mint < fallback_checkout < fallback_install < fallback_model):
    errors.append("OpenRouter fallback must verify Free bearer authentication before token mint, checkout, installation and model call")
for guarded_step in (
    "name: Verify OpenRouter Free key authentication without inference\n        id: openrouter_auth_check\n        if: steps.free_tier_guard.outputs.allowed == 'true'",
    "name: Mint scoped GitHub App token\n        id: mint_identity_token\n        if: steps.free_tier_guard.outputs.allowed == 'true' && steps.openrouter_auth_check.outcome == 'success' && steps.openrouter_auth_check.outputs.quota_available == 'true'",
    "name: Checkout the protected default branch\n        if: steps.free_tier_guard.outputs.allowed == 'true' && steps.openrouter_auth_check.outcome == 'success' && steps.openrouter_auth_check.outputs.quota_available == 'true'",
    "name: Install pinned OpenCode CLI\n        if: steps.free_tier_guard.outputs.allowed == 'true' && steps.openrouter_auth_check.outcome == 'success' && steps.openrouter_auth_check.outputs.quota_available == 'true'",
    "name: Snapshot open PR heads before OpenRouter cycle\n        if: steps.free_tier_guard.outputs.allowed == 'true' && steps.openrouter_auth_check.outcome == 'success' && steps.openrouter_auth_check.outputs.quota_available == 'true'",
    "name: Run OpenCode through the OpenRouter Free route\n        if: steps.free_tier_guard.outputs.allowed == 'true' && steps.openrouter_auth_check.outcome == 'success' && steps.openrouter_auth_check.outputs.quota_available == 'true'",
    "name: Validate OpenRouter autonomous cycle report\n        id: validate_report\n        if: steps.free_tier_guard.outputs.allowed == 'true' && steps.openrouter_auth_check.outcome == 'success' && steps.openrouter_auth_check.outputs.quota_available == 'true'",
):
    if guarded_step not in openrouter_fallback:
        errors.append(f"OpenRouter fallback step is not fail-closed: {guarded_step.splitlines()[0]!r}")
# OpenRouter Free fallback receives its own autonomous daily failure cooldown.
or_cooldown_position = openrouter_fallback.find("id: openrouter_cooldown")
or_guard_position = openrouter_fallback.find("id: free_tier_guard")
or_auth_position = openrouter_fallback.find("id: openrouter_auth_check")
or_mint_position = openrouter_fallback.find("name: Mint scoped GitHub App token")
or_checkout_position = openrouter_fallback.find("name: Checkout the protected default branch")
or_install_position = openrouter_fallback.find("name: Install pinned OpenCode CLI")
or_snapshot_position = openrouter_fallback.find("id: snapshot_pr_heads")
or_run_position = openrouter_fallback.find("name: Run OpenCode through the OpenRouter Free route")
or_validate_position = openrouter_fallback.find("name: Validate OpenRouter autonomous cycle report")
or_record_position = openrouter_fallback.find("name: Record same-day OpenRouter cooldown after quota, authentication or invocation failure")
if not (0 <= or_cooldown_position < or_guard_position < or_auth_position < or_mint_position < or_checkout_position < or_install_position < or_snapshot_position < or_run_position < or_validate_position < or_record_position):
    errors.append("OpenRouter daily cooldown and bearer-auth check must run before token mint/model invocation; invocation and report-validation failures must be recorded after validation")
for required in (
    "github.paginate(github.rest.issues.listComments",
    "BOONTA_OPENROUTER_FAILURE_COOLDOWN:",
    "new Date().toISOString().slice(0, 10)",
    "OPENROUTER_COOLDOWN_ACTIVE",
    "OPENROUTER_COOLDOWN_DATE",
    "steps.openrouter_auth_check.outcome == 'failure'",
    "steps.openrouter_auth_check.outputs.quota_available == 'false'",
    "below the ' + quotaRequired + '-request reserve",
    "steps.run_opencode.outcome != 'success' && steps.run_opencode.outcome != 'skipped'",
    "steps.validate_report.outcome == 'failure'",
    "github.rest.issues.updateComment",
    "github.rest.issues.createComment",
    "continue-on-error: true",
    "until the next UTC day",
):
    if required not in openrouter_fallback:
        errors.append(f"OpenRouter daily cooldown is missing required failover/persistence behavior: {required!r}")
if "id: run_opencode" not in openrouter_fallback:
    errors.append("OpenRouter invocation must expose a stable step ID for failure-only cooldown recording")

# A same-day Gemini cooldown must fail the reusable Gemini job deliberately so
# Boonta Autonomous Loop invokes its separately gated OpenRouter Free fallback.
gemini_cooldown_position = execute.find("id: gemini_cooldown")
gemini_guard_position = execute.find("id: free_tier_guard")
gemini_run_position = execute.find("id: 'run_gemini'")
gemini_fail_position = execute.find("name: Fail autonomous cycle when Gemini preflight blocks the model call")
if not (0 <= gemini_cooldown_position < gemini_guard_position < gemini_run_position < gemini_fail_position):
    errors.append("Gemini cooldown must be checked before its guard/model call and route a blocked autonomous cycle into fallback")
for required in (
    "GEMINI_COOLDOWN_ACTIVE",
    "GEMINI_COOLDOWN_DATE",
    "steps.gemini_cooldown.outputs.active != 'true'",
    "steps.free_tier_guard.outputs.allowed != 'true'",
    "core.setFailed(",
    "needs.autonomous-cycle.result == 'skipped'",
    "needs.provider-cooldowns.outputs.gemini_active == 'true'",
    "uses: ./.github/workflows/openrouter-plan-execute.yml",
):
    if required not in execute and required not in autonomous:
        errors.append(f"Gemini cooldown/fallback handoff is missing required behavior {required!r}")

# Keep the OpenRouter report validator to one unambiguous successful invocation guard.
if openrouter_fallback.count("steps.run_opencode.outcome == 'success'") != 1:
    errors.append("OpenRouter report validation must check the successful invocation outcome exactly once")

# Public issue comments cannot spoof provider cooldowns; only bot-authored markers are trusted.
for label, workflow, marker in (
    ("Gemini", execute, "<!-- BOONTA_GEMINI_FAILURE_COOLDOWN:"),
    ("OpenRouter", openrouter_fallback, "<!-- BOONTA_OPENROUTER_FAILURE_COOLDOWN:"),
):
    trusted_lookup = f"comment.user?.login === 'github-actions[bot]' && (comment.body || '').includes('{marker}')"
    if workflow.count(trusted_lookup) != 2:
        errors.append(f"{label} cooldown check and marker update must trust exactly bot-authored markers")
for required in (
    '"GITHUB_TOOLS": "get_file_contents,create_branch,push_files,create_pull_request"',
    "Do not enumerate all PRs/branches or retrieve attachments, media, binaries or the large route dossier",
    "Keep newly retrieved text below 1,000 tokens total; target below 700 tokens",
    "Stop on context, TPM, rate-limit, quota or authentication errors; never retry the same request",
):
    if required not in openrouter_fallback:
        errors.append(f"OpenRouter prompt must enforce bounded text-only context: {required!r}")

tools_match = re.search(r'"GITHUB_TOOLS": "([^"]+)"', openrouter_fallback)
if not tools_match:
    errors.append("OpenRouter fallback must define an auditable GitHub MCP tool allow-list")
else:
    github_tools = tools_match.group(1).split(",")
    forbidden_github_tools = [
        tool for tool in github_tools
        if any(fragment in tool.lower() for fragment in ("merge", "delete", "secret", "variable", "repository_settings", "repository_ruleset", "update_pull_request", "issue_read", "list_issues", "list_pull_requests", "create_or_update_file", "list_branches", "list_commits"))
    ]
    if forbidden_github_tools:
        errors.append(f"OpenRouter GitHub MCP allow-list exposes forbidden capabilities: {forbidden_github_tools!r}")
    expected_github_tools = [
        "get_file_contents",
        "create_branch",
        "push_files",
        "create_pull_request",
    ]
    if github_tools != expected_github_tools:
        errors.append(
            "OpenRouter GitHub MCP allow-list must match the minimal four-tool direct-delivery contract exactly"
        )
    if any(tool not in expected_github_tools for tool in github_tools):
        errors.append("OpenRouter GitHub MCP allow-list exposes tools outside the reviewed minimal contract")
fallback_call_position = autonomous.find("openrouter-fallback:")
if fallback_call_position < 0:
    errors.append("Boonta Autonomous Loop is missing the OpenRouter fallback job")
else:
    fallback_call = autonomous[fallback_call_position:]
    for required in (
        "needs: [readiness, provider-cooldowns, autonomous-cycle]",
        "needs.readiness.result == 'success'",
        "needs.readiness.outputs.writer_state == 'enabled'",
        "needs.autonomous-cycle.result == 'skipped'",
        "needs.provider-cooldowns.outputs.gemini_active == 'true'",
        "uses: ./.github/workflows/openrouter-plan-execute.yml",
        "autonomous_mode: true",
        "issue_number: 226",
        "secrets: inherit",
    ):
        if required not in fallback_call:
            errors.append(f"OpenRouter fallback caller is missing {required!r}")
    if "github.ref == 'refs/heads/main'" not in fallback_call or "github.actor == github.repository_owner" not in fallback_call:
        errors.append("OpenRouter fallback caller must remain pinned to main and owner/schedule/push-gated")

# Only the Gemini API key route is allowed; legacy cloud/billing routes are forbidden.
legacy_markers = (
    "google_api_key:",
    "use_vertex_ai:",
    "use_gemini_code_assist:",
    "gcp_location:",
    "gcp_project_id:",
    "gcp_service_account:",
    "gcp_workload_identity_provider:",
    "id-token: write",
)
for label, content in (
    ("gemini-invoke.yml", invoke),
    ("gemini-plan-execute.yml", execute),
    ("gemini-dispatch.yml", dispatch),
):
    normalized = content.replace("'", "").replace('"', "").lower()
    for marker in legacy_markers:
        if marker in normalized:
            errors.append(f"Forbidden legacy/paid-auth setting {marker!r} in {label}")

for label, content in (("gemini-invoke.yml", invoke), ("gemini-plan-execute.yml", execute)):
    expected_gemini_key_binding = (
        "gemini_api_key: '${{ secrets.GEMINI_API_KEY_DEUX || secrets.GEMINI_API_KEY }}'"
    )
    if expected_gemini_key_binding not in content:
        errors.append(f"{label} must use its explicitly allowed Gemini API-key binding")
    if label == "gemini-plan-execute.yml" and (
        "GEMINI_API_KEY: '${{ secrets.GEMINI_API_KEY_DEUX || secrets.GEMINI_API_KEY }}'" not in content
        or "GEMINI_API_KEY_DEUX" not in readiness
        or "GEMINI_API_KEY_DEUX" not in invoke
        or "GEMINI_API_KEY_DEUX" not in daily
    ):
        errors.append("Autonomous Gemini guard, CLI and readiness must prefer GEMINI_API_KEY_DEUX with legacy fallback")
    if (
        "id: free_tier_guard" not in content
        or "GEMINI_FREE_TIER_CONFIRMED" not in content
        or "if: steps.free_tier_guard.outputs.allowed == 'true'" not in content
        or content.find("id: free_tier_guard") > content.find("name: 'Mint identity token'")
        or content.find("name: 'Mint identity token'") > content.find("name: 'Checkout Code'")
        or "steps.free_tier_guard.outputs.allowed == 'true' && vars.APP_ID" not in content
        or "name: 'Checkout Code'\n        if: steps.free_tier_guard.outputs.allowed == 'true'" not in content
    ):
        errors.append(f"{label} must fail closed before token mint, checkout, and Gemini model call")
    if label == "gemini-invoke.yml":
        if content.find("name: 'Checkout Code'") > content.find("name: 'Run Gemini CLI'"):
            errors.append("Gemini invoke must check out source before running the CLI")
        if "name: 'Prepare prompt context'" in content:
            errors.append("Gemini invoke must not prepare the obsolete custom-command context file")
    else:
        if (
            content.find("name: 'Checkout Code'") > content.find("name: 'Prepare prompt context'")
            or content.find("name: 'Prepare prompt context'") > content.find("name: 'Run Gemini CLI'")
            or "name: 'Prepare prompt context'\n        if: steps.free_tier_guard.outputs.allowed == 'true'" not in content
        ):
            errors.append("Gemini plan-execute must fail closed before its prompt preparation and model call")
    if "gemini_model: 'gemini-3.8-flash'" not in content:
        errors.append(f"{label} must keep the configured model explicit for owner review")
    if "upload_artifacts: 'false'" not in content:
        errors.append(f"{label} must keep workflow artifact upload disabled")

if not re.search(r"(?m)^\s*description\s*=\s*[\"']Runs the Gemini CLI in read-only planning mode[\"']", invoke_prompt):
    errors.append("Gemini invoke prompt specification must be explicitly read-only")
if "Do not edit files or call write tools" not in invoke_prompt:
    errors.append("Gemini invoke prompt specification must prohibit file writes")
if "@{.gemini/context.json}" not in invoke_prompt or "{{args}}" not in invoke_prompt:
    errors.append("Gemini invoke prompt specification must document its direct request/context placeholders")

for required_phrase in (
    "Always prioritize the exact request in `.gemini/context.json` and the triggering issue/PR comment.",
    "Do not replace a requested comparison or audit with a generic repository overview.",
    "Before responding, check each requested item and either answer it with concrete evidence and links or explicitly name the blocker.",
):
    if required_phrase not in invoke_prompt:
        errors.append(f"Gemini invoke prompt specification is missing task-following safeguard: {required_phrase!r}")


# Plan execution may write on a branch, but must not have deletion/fork tools or merge powers.
for forbidden_tool in ('"delete_file"', '"fork_repository"'):
    if forbidden_tool in execute:
        errors.append(f"Forbidden write tool appears in plan-execute MCP allowlist: {forbidden_tool}")
for required_phrase in (
    "matching, explicitly approved plan",
    "Never push to the default branch",
    "merge a PR",
    "Open a pull request",
):
    if required_phrase not in execute_prompt:
        errors.append(f"Plan-execute prompt is missing required safeguard: {required_phrase!r}")

# Project-level instructions must retain the owner’s €0 condition.
if "€0" not in instructions:
    errors.append("GEMINI.md must preserve the strict €0 budget requirement")
if "GEMINI_WRITE_ENABLED" not in instructions or "exactly true" not in instructions:
    errors.append("GEMINI.md must document the exact write-enable gate")
if "payment method" not in instructions.lower():
    errors.append("GEMINI.md must forbid adding a payment method")

# The project coordinator is manual-only, read-only, and comments on the canonical tracking issue.
daily_trigger = daily.split("permissions:", 1)[0]
if "workflow_dispatch:" not in daily_trigger:
    errors.append("Project coordinator must be explicitly manually triggerable")
if re.search(r"(?m)^\s*(schedule|cron)\s*:", daily_trigger) or re.search(r"(?m)^\s*-\s*cron\s*:", daily_trigger):
    errors.append("Project coordinator must not run on a schedule")
if "contents: write" in daily or "pull-requests: write" in daily:
    errors.append("Project coordinator must not have repository/code write permissions")
if "issues: write" not in daily:
    errors.append("Project coordinator needs issue-comment permission to publish a manually requested report")
for forbidden in ('"create_branch"', '"create_or_update_file"', '"push_files"', '"delete_file"', '"create_pull_request"', '"merge_pull_request"'):
    if forbidden in daily:
        errors.append(f"Project coordinator must not expose write tool {forbidden}")
if "gemini_api_key: ${{ secrets.GEMINI_API_KEY_DEUX || secrets.GEMINI_API_KEY }}" not in daily:
    errors.append("Project coordinator must prefer GEMINI_API_KEY_DEUX with legacy fallback")
if (
    'GEMINI_FREE_TIER_CONFIRMED: ${{ vars.GEMINI_FREE_TIER_CONFIRMED }}' not in daily
    or '[[ "${GEMINI_FREE_TIER_CONFIRMED:-}" != "true" ]]' not in daily
):
    errors.append("Project coordinator must fail closed unless the exact free-tier attestation is present")

# Presence of the attestation is insufficient unless every live-data/model step is actually gated.
coordinator_snapshot_name = "      - name: Collect live branches, open PRs, and project issue metadata"
coordinator_model_name = "      - name: Run Gemini read-only coordinator"
coordinator_publish_name = "      - name: Publish the requested report to the canonical project issue"
if not all(name in daily for name in (coordinator_snapshot_name, coordinator_model_name, coordinator_publish_name)):
    errors.append("Project coordinator is missing a required gated data/model/publication step")
else:
    coordinator_snapshot_step = daily.split(coordinator_snapshot_name, 1)[1].split(coordinator_model_name, 1)[0]
    coordinator_model_step = daily.split(coordinator_model_name, 1)[1].split(coordinator_publish_name, 1)[0]
    coordinator_publish_step = daily.split(coordinator_publish_name, 1)[1]
    free_gate_position = daily.find("id: key")
    snapshot_position = daily.find(coordinator_snapshot_name)
    model_position = daily.find(coordinator_model_name)
    if not (0 <= free_gate_position < snapshot_position < model_position):
        errors.append("Project coordinator must evaluate its free-tier gate before live-data collection and model use")
    if "if: steps.key.outputs.available == 'true'" not in coordinator_snapshot_step:
        errors.append("Project coordinator must skip live-data collection unless the exact free-tier gate passes")
    if "if: steps.key.outputs.available == 'true'" not in coordinator_model_step:
        errors.append("Project coordinator model call must be conditional on the exact free-tier gate")
    if "if: always() && steps.key.outputs.available == 'true' && steps.coordinator.outcome != 'skipped'" not in coordinator_publish_step:
        errors.append("Project coordinator must publish a report only after the free-tier gate passes")
if 'gemini_model: "gemini-3.5-flash-lite"' not in daily:
    errors.append("Project coordinator must keep the explicitly selected free-tier model")
if (
    ('--arg num "156"' not in daily and '"issue_number": "156"' not in daily)
    or 'github_issue_number: "156"' not in daily
    or 'issue_number: 156,' not in daily
):
    errors.append("Project coordinator must publish reports to the canonical issue #156")
if '--arg num "23"' in daily or 'github_issue_number: "23"' in daily or re.search(r"(?m)^\s*issue_number:\s*23,?\s*$", daily):
    errors.append("Project coordinator must not post current reports to stale/closed issue #23")
if "READ ONLY" not in daily_prompt or "€0" not in daily_prompt:
    errors.append("Project coordinator prompt must enforce read-only and €0 constraints")
if "GEMINI_FREE_TIER_CONFIRMED" not in setup or "owner attestation" not in setup:
    errors.append("Setup documentation must explain the explicit free-tier owner attestation")

if (
    '"body": issue.get("body")' not in daily
    or "Current-state resolution: read the live bodies of #226 and #279 in the LIVE SNAPSHOT" not in daily
    or "RE-001 #226 and RE-002 #279" not in daily
    or "read-only PC/N64/Dreamcast" not in daily
    or "RE-002 (issue #279) is ACTIVE" not in daily_prompt
    or "no gameplay changes" not in daily_prompt
):
    errors.append("AI coordinator must preserve the separate native-target and comparative-evidence queues")
if "Never push" not in daily_prompt or "Never recommend publishing ROMs" not in daily_prompt:
    errors.append("Project coordinator prompt must preserve branch and provenance safety")

# The autonomous loop is scheduled, serialized, owner-authorized, and independently gated.
autonomous_trigger = autonomous.split("permissions:", 1)[0]
if "schedule:" not in autonomous_trigger or "workflow_dispatch:" not in autonomous_trigger:
    errors.append("Boonta autonomous loop must support scheduled and owner-manual execution")
if "- cron: '17 0,6,12,18 * * *'" not in autonomous_trigger:
    errors.append("Boonta autonomous loop must run every six hours, including immediately after UTC daily quota reset")
if "group: boonta-autonomous-loop" not in autonomous or "cancel-in-progress: false" not in autonomous:
    errors.append("Boonta autonomous loop must serialize writers without cancelling active work")
if "group: boonta-single-writer" not in execute or "cancel-in-progress: false" not in execute:
    errors.append("All manual and autonomous Gemini writers must share one non-cancelling concurrency group")

# Every autonomous provider must refresh its selected task after acquiring the
# shared non-cancelling writer slot, before checkout/setup or model invocation.
fresh_guard_providers = (
    ("Gemini", execute, "name: 'Mint identity token'", "name: 'Run Gemini CLI'"),
    ("OpenRouter", openrouter_fallback, "name: Mint scoped GitHub App token", "name: Run OpenCode through the OpenRouter Free route"),
    ("Groq", groq_fallback, "name: Mint scoped GitHub App token", "name: Run OpenCode through the Groq Free route"),
)
for label, workflow, mint_marker, invocation_marker in fresh_guard_providers:
    cooldown_position = workflow.find("id: " + ("gemini_cooldown" if label == "Gemini" else "openrouter_cooldown" if label == "OpenRouter" else "groq_cooldown"))
    free_guard_position = workflow.find("id: free_tier_guard")
    fresh_guard_position = workflow.find("id: fresh_task_guard")
    mint_position = workflow.find(mint_marker)
    invocation_position = workflow.find(invocation_marker)
    if not (0 <= cooldown_position < free_guard_position < fresh_guard_position < mint_position < invocation_position):
        errors.append(f"{label} must revalidate the selected task after its Free-only gate and before identity setup/model invocation")
    for required in (
        "if: inputs.autonomous_mode == true && steps.free_tier_guard.outputs.allowed == 'true'",
        "TASK_ID: ${{ inputs.task_id }}",
        "TASK_TARGET_BRANCH: ${{ inputs.task_target_branch }}",
        "taskIds.some((id) => typeof id !== 'string'",
        "ledgerSummary.policy?.max_active_tasks !== 1",
        "const duplicate = openPullRequests.find(",
        "core.setFailed('Fresh task revalidation blocked before provider invocation: '",
    ):
        if required not in workflow:
            errors.append(f"{label} post-queue task guard is missing {required!r}")
openrouter_fresh_guard_start = openrouter_fallback.find("      - name: Revalidate selected task after acquiring the shared writer slot")
openrouter_fresh_guard_end = openrouter_fallback.find("\n      - name:", openrouter_fresh_guard_start + 1)
openrouter_fresh_guard = openrouter_fallback[openrouter_fresh_guard_start:openrouter_fresh_guard_end]
if "steps.openrouter_auth_check.outcome == 'success' && steps.openrouter_auth_check.outputs.quota_available == 'true'" not in openrouter_fresh_guard:
    errors.append("OpenRouter fresh task guard must run only after its GET-only Free quota/authentication preflight passes")
if "test_autonomous_fresh_task_guard.py" not in selftest or "python3 tools/test_autonomous_fresh_task_guard.py" not in selftest:
    errors.append("Branch automation self-test must execute post-queue task guard regressions")
if "uses: ./.github/workflows/gemini-plan-execute.yml" not in autonomous or "autonomous_mode: true" not in autonomous:
    errors.append("Boonta autonomous loop must call the separately gated reusable writer in autonomous mode")
if "issue_number: 226" not in autonomous or "GEMINI_AUTONOMOUS_ENABLED" not in execute:
    errors.append("Autonomous writes must be restricted to the canonical queue and explicit owner gate")
if (
    "GEMINI_AUTONOMOUS_ENABLED" not in execute
    or "APP_PRIVATE_KEY" not in execute
    or "CALLER_WORKFLOW" not in execute
    or "CALLER_REF" not in execute
    or 'CALLER_REF:-}" != "refs/heads/main"' not in execute
):
    errors.append("Autonomous writer must require its separate gate, approved caller on protected main, and GitHub App identity")
if "permission-actions: 'read'" not in execute or '"list_workflow_runs"' not in execute or '"get_job_logs"' not in execute:
    errors.append("Autonomous writer must be able to inspect CI runs and failed-job logs using Actions read permission")
if "inputs.autonomous_mode && '/gemini-autonomous-loop'" not in execute:
    errors.append("Reusable writer must select the autonomous prompt only for the explicit autonomous input")
for required_phrase in (
    "without asking for another",
    "one bounded task",
    "Treat #279 as a separate read-only PC/N64/Dreamcast comparative evidence queue",
    "Never merge a PR",
    "strict project budget is €0",
    "Never push directly to either protected branch",
):
    if required_phrase not in autonomous_prompt:
        errors.append(f"Autonomous prompt is missing required safety/continuity rule: {required_phrase!r}")

# Enforce a reuse-first engineering method and efficient evidence-based validation.
for required_phrase in (
    "MAKE IT WORK → MAKE IT GOOD → MAKE IT FAST",
    "Extend the canonical implementation",
    "Never hand-edit generated headers or artifacts",
    "Optimize only a measured hot path",
    "Reuse passing checks for an unchanged exact SHA",
    "Group related file edits into one logical commit",
    "Do not read all historical comments",
    "compact inventory of directly related open pull requests",
    "Deep-inspect changed files and exact-head CI only for PRs",
    "Read logs only for failed jobs",
    "Reuse a successful check for an unchanged exact SHA",
    "without launching duplicate runs",
):
    if required_phrase not in autonomous_prompt:
        errors.append(f"Autonomous prompt is missing reuse/performance rule: {required_phrase!r}")
if "MAKE IT WORK → MAKE IT GOOD → MAKE IT FAST" not in instructions:
    errors.append("GEMINI.md must preserve the owner's make-it-work/good/fast engineering sequence")
if "contents: write" not in autonomous or "issues: write" not in autonomous or "pull-requests: write" not in autonomous:
    errors.append("Autonomous workflow must grant only the scoped repository/issue/PR permissions required by its gated writer")
if "GEMINI_AUTONOMOUS_ENABLED" not in setup or "Boonta Autonomous Loop" not in setup:
    errors.append("Setup documentation must explain the autonomous enable gate and scheduled loop")
if "Actions: read" not in setup:
    errors.append("Setup documentation must require GitHub App Actions read permission for CI feedback")

# Deterministic CI failure triage must cover the two protected integration targets.
triage_trigger = ci_triage.split("permissions:", 1)[0]
if "workflow_run:" not in triage_trigger:
    errors.append("CI failure triage must remain attached to completed workflow runs")
for workflow_name in (
    "GameCube first-render prototype build",
    "GameCube native build",
    "Wii64 tooling tests",
    "AI free-tier safety checks",
    "Branch automation self-test",
    "Step 102 source-import provenance guard",
    "Trusted source-import path guard",
    "Synthetic BRRES MDL0 probe",
    "Dreamcast KallistiOS build",
    "Boonta Autonomous Loop",
):
    if f"      - {workflow_name}" not in triage_trigger:
        errors.append(f"CI failure triage is missing workflow {workflow_name!r}")
for required_guard in (
    "['main', 'dev'].includes(item.base?.ref)",
    "['main', 'dev'].includes(pr.base.ref)",
    "item.head?.repo?.full_name === expectedRepo",
    "pr.state === 'open'",
    "pr.head.repo?.full_name === expectedRepo",
    "item.head?.sha === run.head_sha",
    "pr.head.sha === run.head_sha",
    "run.event === 'push'",
    "['main', 'dev'].includes(run.head_branch)",
    "github.rest.repos.getBranch",
    "branchInfo.commit?.sha !== run.head_sha",
    "targetBranch === 'dev' ? 226 : 156",
    "issue_number: prNumber || targetIssueNumber",
    "['push', 'schedule', 'workflow_dispatch'].includes(run.event)",
    "run.name === 'Boonta Autonomous Loop'",
    "run.head_branch === 'main'",
    "targetIssueNumber = 226",
):
    if required_guard not in ci_triage:
        errors.append(f"CI failure triage is missing safe main/dev exact-head guard {required_guard!r}")
triage_workflow_filters = ci_triage.split("    types:", 1)[0]
if "- .github/workflows/boonta-autonomous-loop.yml" not in triage_workflow_filters:
    errors.append("CI failure triage must match the autonomous loop's API-reported workflow path as well as its display name")
if "run.path === '.github/workflows/boonta-autonomous-loop.yml'" not in ci_triage:
    errors.append("CI failure triage must route path-named autonomous workflow failures to canonical queue issue #226")
provider_workflow_paths = (
    "- .github/workflows/gemini-plan-execute.yml",
    "- .github/workflows/openrouter-plan-execute.yml",
    "- .github/workflows/groq-plan-execute.yml",
)
for required_path in provider_workflow_paths:
    if required_path not in triage_workflow_filters:
        errors.append(f"CI failure triage must listen for reusable provider workflow path {required_path!r}")
for required_provider_route in (
    "const providerWorkflowPaths = new Set([",
    "const isProviderCycleRun = providerWorkflowPaths.has(run.path) || providerWorkflowNames.has(run.name);",
    "if (!prNumber && isProviderCycleRun && ['push', 'schedule', 'workflow_dispatch'].includes(run.event)",
    "targetIssueNumber = 226;",
):
    if required_provider_route not in ci_triage:
        errors.append(f"CI failure triage is missing reusable provider failure routing {required_provider_route!r}")
if "github.event.workflow_run.conclusion == 'startup_failure'" not in ci_triage:
    errors.append("CI failure triage must report startup_failure conclusions, not only job failures")
for required_triage_detail in (
    "const noJobs = !Array.isArray(data.jobs) || data.jobs.length === 0;",
    "const conclusion = String(run.conclusion || 'unknown');",
    "No workflow step or provider job ran",
    "no provider authentication result can be inferred",
    "'**Conclusion:** ' + conclusion",
    "'**Jobs returned:** ' + (Array.isArray(data.jobs) ? data.jobs.length : 0)",
):
    if required_triage_detail not in ci_triage:
        errors.append(f"CI failure triage is missing startup/no-job diagnosis detail {required_triage_detail!r}")
triage_permissions = ci_triage.split("permissions:", 1)[1].split("concurrency:", 1)[0]
if "contents: write" in triage_permissions or "pull-requests: write" in triage_permissions:
    errors.append("CI failure triage must not have code or pull-request write permission")
if "actions: read" not in triage_permissions or "issues: write" not in triage_permissions:
    errors.append("CI failure triage needs only Actions read and issue-comment write for diagnostics")

# Gameplay integration into dev must receive post-merge native validation too.
gamecube_push_trigger = gamecube_build.split("  push:", 1)[1].split("  pull_request:", 1)[0]
if "branches: [main, dev]" not in gamecube_push_trigger:
    errors.append("GameCube prototype CI must run after merges/pushes to both main and dev")
if "  build-gamecube-demo:\n    timeout-minutes: 15\n" not in gamecube_build:
    errors.append("Native GameCube CI build job must have a bounded 15-minute timeout")
gamecube_concurrency = gamecube_build.split("concurrency:", 1)[1].split("jobs:", 1)[0] if "concurrency:" in gamecube_build else ""
if "group: gamecube-demo-${{ github.event.pull_request.number || github.ref }}" not in gamecube_concurrency:
    errors.append("GameCube build workflow must serialize executions by PR/ref")
if "cancel-in-progress: true" not in gamecube_concurrency:
    errors.append("New GameCube commits must cancel stale same-PR/ref CI runs")

# The autonomous agent must use exact-head CI rather than invent local test results.
for required_phrase in (
    "intentionally has no general-purpose local shell",
    "exact PR head SHA",
    "Do not push empty commits",
    "read only the failing job logs",
    "no documented safe rerun action",
    "five minutes beyond that timeout",
    "likely stale runner/Actions state",
    "do not wait indefinitely",
    "optional `continue-on-error` diagnostics",
):
    if required_phrase not in autonomous_prompt:
        errors.append(f"Autonomous prompt is missing CI execution/recovery rule {required_phrase!r}")
if "GitHub Actions is the authoritative test executor" not in instructions:
    errors.append("GEMINI.md must state that GitHub Actions is the authoritative test executor for the autonomous agent")

# Keep Wii64 unit-test CI scoped to the files its tests actually exercise.
wii64_trigger = wii64_tests.split("permissions:", 1)[0]
wii64_branches = wii64_trigger.split("branches:", 1)[1].split("paths:", 1)[0]
wii64_paths = wii64_trigger.split("paths:", 1)[1]
wii64_concurrency = wii64_tests.split("concurrency:", 1)[1].split("jobs:", 1)[0] if "concurrency:" in wii64_tests else ""
if "group: wii64-tool-tests-${{ github.event.pull_request.number || github.ref }}" not in wii64_concurrency:
    errors.append("Wii64 test runs must be serialized per PR/ref to avoid duplicate runner usage")
if "cancel-in-progress: true" not in wii64_concurrency:
    errors.append("A newer Wii64 test run must replace a stale run on the same PR/ref")
if not all(branch in wii64_branches for branch in ('      - main', '      - "tools/**"', '      - "ci/**"')):
    errors.append("Wii64 push branch filters must retain main, tools/** and ci/**")
if '"tools/**"' in wii64_paths:
    errors.append("Wii64 tooling test path filters must remain narrower than all tools/**")
for required_path in (
    '      - "tools/compare_wii64_rice_ini.py"',
    '      - "tools/compare_wii64_rice_profiles.py"',
    '      - "tools/inspect_wii64_rice_ini.py"',
    '      - "tools/verify_wii64_archive.py"',
    '      - "tools/tests/**"',
    '      - ".github/workflows/wii64-tool-tests.yml"',
):
    if required_path not in wii64_trigger:
        errors.append(f"Wii64 tooling test path filters are missing {required_path!r}")

# Keep the one-item autonomous queue aligned with its live canonical issue and
# prevent the agent from repeating the already-merged route-graph contract.
if "PR #271" not in read("docs/PROJECT_OPERATING_RULES.md"):
    errors.append("Operating rules must identify the integrated route-graph contract PR #271")
if "41528877645" not in read("docs/PROJECT_OPERATING_RULES.md"):
    errors.append("Operating rules must record the successful post-merge validation of PR #271")
if "PR #274" not in read("docs/PROJECT_OPERATING_RULES.md"):
    errors.append("Operating rules must direct the next cycle to review the existing runtime candidate PR #274")
if "Do not create another route-runtime branch" not in read("docs/PROJECT_OPERATING_RULES.md"):
    errors.append("Operating rules must prevent duplicate route-runtime branches")
if "RE-002 is active only as read-only comparative evidence" not in read("docs/PROJECT_OPERATING_RULES.md"):
    errors.append("Operating rules must keep RE-002 limited to read-only comparative evidence")

# Every autonomous provider must consume the one exact task selected by the global preflight.
dynamic_task_prompts = (
    ("Gemini", autonomous_prompt),
    ("OpenRouter", openrouter_fallback),
    ("Groq", groq_fallback),
)
for label, prompt in dynamic_task_prompts:
    required_task_safeguards = (
        (
            "preloaded schema-v2 context is authoritative",
            "Global preflight is authoritative",
            "Do not search PR history",
            "€0 only",
        )
        if label == "Groq"
        else (
            (
                "AUTHORITATIVE SELECTED TASK",
                "Use exactly this task from docs/automation/task-ledger-summary.json",
                "acceptance_criteria_excerpt",
                "Do not substitute another task",
                "€0",
            )
            if label == "OpenRouter"
            else (
                "AUTHORITATIVE SELECTED TASK",
                "task-ledger-summary.json",
                "acceptance_criteria_excerpt",
                "Do not substitute another task",
                "€0",
            )
        )
    )
    for required in required_task_safeguards:
        if required not in prompt:
            errors.append(f"{label} autonomous prompt is missing dynamic selected-task safeguard {required!r}")
    if label == "Gemini":
        for required in ("task_id", "task_title", "task_description", "task_target_branch"):
            if required not in prompt:
                errors.append(f"Gemini autonomous prompt is missing selected-task context key {required!r}")
    else:
        for required in ("TASK_ID", "TASK_TITLE", "TASK_TARGET_BRANCH"):
            if required not in prompt:
                errors.append(f"{label} autonomous prompt is missing selected-task environment value {required!r}")
    if "Follow the newest owner direction dated 2026-11-06" in prompt or "After Phase 1" in prompt:
        errors.append(f"{label} autonomous prompt still contains an overriding dated task sequence")
# Provider handoff budgets must match their tested schema-v2 activation context.
# Groq has a deliberately smaller TPM-bounded handoff; offline builder tests
# reject truncation of required question, acceptance-criteria or next-action excerpts.
for label, workflow, expected_max_chars, expected_task_chars in (
    ("OpenRouter", openrouter_fallback, "2400", "2200"),
    ("Groq", groq_fallback, "1500", "1400"),
):
    if f"--max-task-context {expected_task_chars}" not in workflow:
        errors.append(f"{label} context builder must preserve the reviewed {expected_task_chars}-character task handoff")
    if f"--max-chars {expected_max_chars} --max-task-context {expected_task_chars}" not in workflow:
        errors.append(f"{label} context builder must match its documented verified-context ceiling")

for required in (
    "TASK_ID: '${{ inputs.task_id }}'",
    "TASK_TITLE: '${{ inputs.task_title }}'",
    "TASK_DESCRIPTION: '${{ inputs.task_description }}'",
    "TASK_TARGET_BRANCH: '${{ inputs.task_target_branch }}'",
    "task_id: $task_id",
    "task_target_branch: $task_target_branch",
):
    if required not in execute:
        errors.append(f"Gemini workflow context is missing selected-task binding {required!r}")
for label, workflow in (
    ("OpenRouter", openrouter_fallback),
    ("Groq", groq_fallback),
):
    required_task_bindings = (
        (
            "task_id:",
            "task_title:",
            "task_target_branch:",
            "TASK_ID: ${{ inputs.task_id }}",
            "TASK_TITLE: ${{ inputs.task_title }}",
            "TASK_TARGET_BRANCH: ${{ inputs.task_target_branch }}",
            "preloaded schema-v2 context is authoritative",
        )
        if label == "Groq"
        else (
            "task_id:",
            "task_title:",
            "task_target_branch:",
            "TASK_ID: ${{ inputs.task_id }}",
            "TASK_TITLE: ${{ inputs.task_title }}",
            "TASK_TARGET_BRANCH: ${{ inputs.task_target_branch }}",
            "Use exactly this task from docs/automation/task-ledger-summary.json",
        )
    )
    for required in required_task_bindings:
        if required not in workflow:
            errors.append(f"{label} reusable workflow is missing selected-task binding {required!r}")

# The owner-only readiness workflow checks configuration and App access without
# calling a model or performing repository writes.
readiness_trigger = readiness.split("permissions:", 1)[0]
readiness_events = re.findall(r"(?m)^  ([a-zA-Z0-9_-]+):\s*$", readiness_trigger)
if readiness_events != ["push", "workflow_dispatch", "workflow_call"]:
    errors.append(
        "Autonomous readiness must support a narrowly scoped main push, owner-only manual dispatch and reusable workflow calls; "
        f"found {readiness_events!r}"
    )
push_trigger = readiness_trigger.split("  push:", 1)[1].split("  workflow_dispatch:", 1)[0] if "  push:" in readiness_trigger else ""
if "    branches:\n      - main\n" not in push_trigger or "    paths:\n      - .github/workflows/boonta-autonomous-readiness.yml\n" not in push_trigger:
    errors.append(
        "Autonomous readiness push trigger must be restricted to main and changes to its own workflow file"
    )
if "value: ${{ jobs.readiness.outputs.writer_state }}" not in readiness:
    errors.append("Reusable readiness must expose the writer-enabled state to its caller")
if "writer_state: ${{ steps.owner_gates.outputs.writer_state }}" not in readiness:
    errors.append("Reusable readiness must derive its writer-enabled output from the owner-gate check")
if "WRITER_STATE: ${{ steps.owner_gates.outputs.writer_state }}" not in readiness:
    errors.append("Readiness must explicitly pass the owner-gate output to later steps")
if 'echo "writer_state=${writer_state}" >> "$GITHUB_OUTPUT"' not in readiness:
    errors.append("Readiness must export a non-boolean writer_state for reusable callers")
readiness_job_guard = re.search(r"(?ms)^  readiness:\n.*?^    if:\s*(?:>-\n)?(.*?)(?=^    runs-on:)", readiness)
if (
    "allow_scheduled:" not in readiness
    or "default: false" not in readiness
    or "type: boolean" not in readiness
    or not readiness_job_guard
    or "github.ref == 'refs/heads/main'" not in readiness_job_guard.group(1)
    or "inputs.allow_scheduled == true" not in readiness_job_guard.group(1)
    or "github.actor == github.repository_owner" not in readiness_job_guard.group(1)
):
    errors.append("Autonomous readiness must stay pinned to protected main, retain the owner guard, and allow only explicit scheduled-loop handoff")
if "allow_scheduled: " + "${{ github.event_name == 'schedule' }}" not in autonomous:
    errors.append("Only the scheduled autonomous loop may set the reusable readiness exception")
readiness_permission_block = readiness.split("permissions:", 1)[1].split("jobs:", 1)[0]
readiness_permissions = dict(
    re.findall(
        r"(?m)^  ([a-zA-Z-]+):\s*([a-zA-Z]+)\s*$",
        readiness_permission_block,
    )
)
expected_readiness_permissions = {
    "contents": "read",
    "issues": "read",
    "pull-requests": "read",
}
if readiness_permissions != expected_readiness_permissions:
    errors.append(
        "Autonomous readiness GITHUB_TOKEN permissions must be read-only and exact; "
        f"found {readiness_permissions!r}"
    )
if "gemini_api_key:" in readiness or "run-gemini-cli" in readiness or "gemini_model:" in readiness:
    errors.append("Autonomous readiness must never invoke a Gemini model or send an API request")
if "GEMINI_AUTONOMOUS_ENABLED" not in readiness or "GEMINI_FREE_TIER_CONFIRMED" not in readiness:
    errors.append("Autonomous readiness must report writer-gate state and check the Free-tier attestation")
if '[[ "${GEMINI_AUTONOMOUS_ENABLED:-}" == "true" ]]' not in readiness:
    errors.append("Readiness preflight must report when the autonomous writer gate is enabled")
if '[[ "${GEMINI_FREE_TIER_CONFIRMED:-}" == "true" ]]' not in readiness:
    errors.append("Readiness preflight must require the owner's exact Free-tier attestation")
if "neither changes the gate nor invokes a model" not in readiness:
    errors.append("Readiness report must state that preflight is read-only and leaves the autonomous gate unchanged")
for required_secret in ("GEMINI_API_KEY", "APP_ID", "APP_PRIVATE_KEY"):
    if required_secret not in readiness:
        errors.append(f"Autonomous readiness must verify presence of {required_secret}")
for required_permission in (
    "permission-contents: read",
    "permission-issues: read",
    "permission-pull-requests: read",
    "permission-actions: read",
):
    if required_permission not in readiness:
        errors.append(f"Autonomous readiness must test GitHub App permission {required_permission!r}")
for required_probe in (
    "/issues/156",
    "/issues/226",
    "/actions/runs?per_page=1",
    "/git/ref/heads/${branch}",
):
    if required_probe not in readiness:
        errors.append(f"Autonomous readiness is missing required read-only API probe {required_probe!r}")

if "No repository write was performed" not in readiness or "does not independently verify Google billing status" not in readiness:
    errors.append("Autonomous readiness must state that it performs no writes and cannot verify Google billing")
if "rulesets protect main and dev" not in readiness:
    errors.append("Autonomous readiness must remind the owner to verify main/dev branch protection manually")
if "curl --fail --silent --show-error" not in readiness or "-X POST" in readiness or "--request POST" in readiness:
    errors.append("Autonomous readiness API probes must remain GET-only")

# Freeze the autonomous entry points and least-privilege boundary.
# Scheduled runs, narrowly scoped main pushes after relevant owner merges, and
# owner-only manual dispatch are the only autonomous entry points.
autonomous_events = re.findall(r"(?m)^  ([a-zA-Z0-9_-]+):\s*$", autonomous_trigger)
if autonomous_events != ["push", "schedule", "workflow_dispatch"]:
    errors.append("Boonta autonomous loop may declare only scoped push, schedule and workflow_dispatch events; " + f"found {autonomous_events!r}")
autonomous_push = autonomous_trigger.split("  push:", 1)[1].split("  schedule:", 1)[0] if "  push:" in autonomous_trigger else ""
required_autonomous_push_paths = (
    ".github/workflows/boonta-autonomous-loop.yml",
    ".github/workflows/boonta-autonomous-readiness.yml",
    ".github/workflows/gemini-plan-execute.yml",
    ".github/workflows/openrouter-plan-execute.yml",
    ".github/workflows/groq-plan-execute.yml",
    "docs/automation/task-ledger.json",
)
if "    branches:\n      - main\n" not in autonomous_push or "    paths:" not in autonomous_push or any(path not in autonomous_push for path in required_autonomous_push_paths):
    errors.append("Autonomous main-push trigger must be restricted to main and the reviewed automation/ledger paths")
if "github.ref == 'refs/heads/main'" not in autonomous or "(github.event_name == 'schedule' || ((github.event_name == 'workflow_dispatch' || github.event_name == 'push') && github.actor == github.repository_owner))" not in autonomous:
    errors.append("Autonomous schedule/manual dispatch/main-push continuation must be owner-only and pinned to protected main")
if "workflow_dispatch:\n    inputs:" in autonomous_trigger:
    errors.append("Manual autonomous dispatch must not accept user-controlled task/issue overrides")

readiness_job_position = autonomous.find("  readiness:")
cycle_job_position = autonomous.find("  autonomous-cycle:")
fallback_job_position = autonomous.find("  openrouter-fallback:")
if not (0 <= readiness_job_position < cycle_job_position < fallback_job_position):
    errors.append("Autonomous loop must run read-only readiness before Gemini and OpenRouter")
if "uses: ./.github/workflows/boonta-autonomous-readiness.yml" not in autonomous:
    errors.append("Autonomous loop must call the reusable read-only readiness workflow")
if "needs: readiness" not in autonomous or "needs.readiness.result == 'success'" not in autonomous:
    errors.append("Gemini must run only after successful read-only readiness")
if "needs.readiness.outputs.writer_state == 'enabled'" not in autonomous:
    errors.append("Gemini must not run when the owner has left the autonomous writer disabled")
readiness_job = autonomous.split("  readiness:", 1)[1].split("  autonomous-cycle:", 1)[0]
readiness_job_permissions = dict(re.findall(r"(?m)^      ([a-zA-Z-]+):\s*['\"]?([a-zA-Z]+)['\"]?\s*$", readiness_job))
if readiness_job_permissions != {"contents": "read", "issues": "read", "pull-requests": "read"}:
    errors.append(f"Autonomous loop readiness caller must be read-only; found {readiness_job_permissions!r}")

caller_permission_block = autonomous.split("permissions:", 1)[1].split("concurrency:", 1)[0]
caller_permissions = dict(
    re.findall(r"(?m)^  ([a-zA-Z-]+):\s*([a-zA-Z]+)\s*$", caller_permission_block)
)
expected_caller_permissions = {
    "contents": "write",
    "issues": "write",
    "pull-requests": "write",
}
if caller_permissions != expected_caller_permissions:
    errors.append(
        "Autonomous caller permissions must be exactly the contents/issues/PR write set; "
        f"found {caller_permissions!r}"
    )

autonomous_job = autonomous.split("  autonomous-cycle:", 1)[1].split("  openrouter-fallback:", 1)[0]
job_permissions_match = re.search(
    r"(?ms)^    permissions:\n(?P<block>(?:      [^\n]*\n)+)",
    autonomous_job,
)
if not job_permissions_match:
    errors.append("Autonomous reusable-workflow job must declare an explicit least-privilege permission set")
else:
    job_permissions = dict(
        re.findall(
            r"(?m)^      ([a-zA-Z-]+):\s*([a-zA-Z]+)\s*$",
            job_permissions_match.group("block"),
        )
    )
    expected_provider_permissions = {**expected_caller_permissions, "checks": "read"}
    if job_permissions != expected_provider_permissions:
        errors.append(
            "Autonomous Gemini reusable-workflow permissions must be contents/issues/PR write plus checks read only; "
            f"found {job_permissions!r}"
        )

if "secrets: inherit" not in autonomous:
    errors.append("Autonomous caller must pass only the repository-scoped secrets required by its reusable workflow")
if "workflow_dispatch" in autonomous_trigger and "github.actor == github.repository_owner" not in autonomous:
    errors.append("Manual dispatch must remain owner-only")

# The autonomous model can create/update branches and PRs, but the MCP allowlist
# must never expose merge, deletion, repository administration, or secret tools.
tool_match = re.search(r'"includeTools":\s*\[(.*?)\]', execute, re.DOTALL)
if not tool_match:
    errors.append("Autonomous Gemini MCP allowlist is missing or cannot be audited")
else:
    mcp_tools = re.findall(r'"([^"]+)"', tool_match.group(1))
    forbidden_tool_fragments = (
        "merge",
        "delete",
        "repository_settings",
        "repository_ruleset",
        "secret",
        "variable",
    )
    forbidden_tools = [
        tool for tool in mcp_tools
        if any(fragment in tool.lower() for fragment in forbidden_tool_fragments)
    ]
    if forbidden_tools:
        errors.append(
            "Autonomous Gemini MCP allowlist must not expose merge/delete/admin/secret tools; "
            f"found {forbidden_tools!r}"
        )
    for required_tool in ("create_branch", "create_pull_request", "push_files", "get_job_logs"):
        if required_tool not in mcp_tools:
            errors.append(f"Autonomous Gemini MCP allowlist is missing required bounded capability {required_tool!r}")
    for required_tool in ("search_pull_requests", "list_workflow_runs", "list_workflow_jobs", "get_workflow_run", "get_job_logs"):
        if required_tool not in mcp_tools:
            errors.append(f"Autonomous Gemini MCP allowlist is missing supported inventory tool {required_tool!r}")
    for unsupported_tool in ("list_pull_requests", "create_or_update_file", "get_workflow_job"):
        if unsupported_tool in mcp_tools:
            errors.append(f"Autonomous Gemini MCP allowlist contains unsupported or redundant tool {unsupported_tool!r}")

# The autonomous agent's file-editing surface must match the actual workflow allow-list.
editing_contract_requirements = (
    "## Repository editing contract (mandatory)",
    "Use only the GitHub MCP `push_files` tool for all repository file writes",
    "Never call `replace`, `write_file`, `edit_file` or `apply_patch`",
    "If `push_files` is unavailable or a write fails, stop modifying files",
    "Do not create a self-referential `in_review` record",
    "after merge, finalize from `main` with the actual merged PR head SHA",
)
missing_editing_contract = [item for item in editing_contract_requirements if item not in autonomous_prompt]
if missing_editing_contract:
    errors.append(f"Autonomous prompt is missing its supported repository-editing/ledger contract: {missing_editing_contract!r}")

# The action must stop at the model/API boundary when the owner gates fail.
guard_position = execute.find("id: free_tier_guard")
mint_position = execute.find("name: 'Mint identity token'")
checkout_position = execute.find("name: 'Checkout Code'")
model_position = execute.find("name: 'Run Gemini CLI'")
if not (0 <= guard_position < mint_position < checkout_position < model_position):
    errors.append("Autonomous free-tier/owner gate must run before token mint, checkout, and model invocation")
for guarded_step in (
    "name: 'Mint identity token'\n        id: 'mint_identity_token'\n        if: |-",
    "name: 'Checkout Code'\n        if: steps.free_tier_guard.outputs.allowed == 'true'",
    "name: 'Prepare prompt context'\n        if: steps.free_tier_guard.outputs.allowed == 'true'",
    "name: 'Run Gemini CLI'\n        if: steps.free_tier_guard.outputs.allowed == 'true'",
):
    if guarded_step not in execute:
        errors.append(f"Reusable writer is missing a fail-closed condition on step: {guarded_step.splitlines()[0]!r}")
if "gemini_model: 'gemini-3.8-flash'" not in execute:
    errors.append("Autonomous workflow must use the explicitly reviewed Free-tier Gemini 3.8 Flash model")
if "upload_artifacts: 'false'" not in execute:
    errors.append("Autonomous workflow must keep third-party workflow artifact upload disabled")

# Pin the tested Gemini CLI release and cap automatic model/network retries.
if "gemini_cli_version: '0.67.0'" not in execute:
    errors.append("Autonomous Gemini CLI must remain pinned to the version verified with retry controls")
settings_marker = "          settings: |-\n"
settings_end_marker = "          prompt: ${{ inputs.autonomous_mode && '/gemini-autonomous-loop' || '/gemini-plan-execute' }}"
if settings_marker not in execute or settings_end_marker not in execute:
    errors.append("Autonomous Gemini workflow is missing its explicit CLI settings block")
else:
    settings_text = execute.split(settings_marker, 1)[1].split(settings_end_marker, 1)[0]
    try:
        gemini_settings = json.loads(textwrap.dedent(settings_text))
        general_settings = gemini_settings.get("general", {})
        if general_settings.get("maxAttempts") != 1:
            errors.append("Gemini CLI must make only one model attempt so terminal 503/TPM failures are not repeated")
        if general_settings.get("retryFetchErrors") is not False:
            errors.append("Gemini CLI must disable automatic retries for failed fetch requests")
        if gemini_settings.get("model", {}).get("maxSessionTurns") != 3:
            errors.append("Gemini CLI must retain the three-turn TPM safety ceiling")
    except (json.JSONDecodeError, TypeError) as exc:
        errors.append(f"Autonomous Gemini CLI settings must be valid JSON: {exc}")

# Scheduled autonomous runs must not stream verbose model output into public Actions logs.
if '"maxSessionTurns": 3' not in execute:
    errors.append("Autonomous Gemini writer must cap its session at three turns to bound Free-tier token use")
for label, content in (("gemini-invoke.yml", invoke), ("gemini-plan-execute.yml", execute)):
    if "run_shell_command" in content:
        errors.append(f"{label} must not expose the restricted shell tool to Gemini")
    if '"list_pull_requests"' in content:
        errors.append(f"{label} must not request the unavailable list_pull_requests MCP tool")

expected_gemini_debug = "gemini_debug: '${{ inputs.autonomous_mode != true && fromJSON(vars.GEMINI_DEBUG || vars.ACTIONS_STEP_DEBUG || false) }}'"
if expected_gemini_debug not in execute:
    errors.append("Autonomous Gemini runs must disable verbose debug streaming; manual runs may opt in")


# Failed autonomous Gemini invocations create one persistent same-day cooldown marker.
cooldown_check_position = execute.find("id: gemini_cooldown")
cooldown_guard_position = execute.find("id: free_tier_guard")
cooldown_model_position = execute.find("name: 'Run Gemini CLI'")
cooldown_validate_position = execute.find("name: Validate autonomous cycle report contract")
cooldown_record_position = execute.find("name: Record same-day Gemini cooldown after an autonomous model failure")
if not (0 <= cooldown_check_position < cooldown_guard_position < cooldown_model_position < cooldown_validate_position < cooldown_record_position):
    errors.append("Gemini cooldown must be checked before inference and recorded after report validation")
for required in (
    "github.paginate(github.rest.issues.listComments",
    "BOONTA_GEMINI_FAILURE_COOLDOWN:",
    "new Date().toISOString().slice(0, 10)",
    "GEMINI_COOLDOWN_ACTIVE",
    "GEMINI_COOLDOWN_DATE",
    "steps.gemini_cooldown.outputs.active != 'true'",
    "if: always() && inputs.autonomous_mode == true && (steps.run_gemini.outcome == 'failure' || steps.validate_report.outcome == 'failure')",
    "github.rest.issues.updateComment",
    "github.rest.issues.createComment",
    "continue-on-error: true",
    "until the next UTC day",
):
    if required not in execute:
        errors.append(f"Gemini daily cooldown is missing required failover/persistence behavior: {required!r}")
if "if: inputs.autonomous_mode == true" not in execute[:cooldown_guard_position]:
    errors.append("Gemini daily cooldown must apply only to autonomous invocations, not the manual writer path")

# Gemini autonomous context policy: compact supplied briefs, no full issue history or binary/media inputs.
for required in (
    "Do not fetch full issue bodies or full comment histories for #156, #226 and #279",
    "below 1,500 tokens total",
    "Do not retrieve attachments, images, media, artifacts, ROMs, disc images, BIOS, binaries",
    "never repeat the same request",
    "approximately 452 KB route dossier",
):
    if required not in autonomous_prompt:
        errors.append(f"Gemini autonomous prompt must enforce the current bounded text-only context: {required!r}")
for required in (
    "Facts established before this prompt can run",
    "Never claim that `GEMINI_AUTONOMOUS_ENABLED` is disabled, missing or needs enabling",
    "Never claim that `GEMINI_FREE_TIER_CONFIRMED`, `GEMINI_API_KEY`, `APP_ID` or `APP_PRIVATE_KEY` is absent or unset",
    "does **not** prove that the Google project truly has no linked Cloud Billing account",
):
    if required not in autonomous_prompt:
        errors.append(f"Gemini autonomous prompt must distinguish passed preflight gates from external verification: {required!r}")

# Autonomous progress is validated centrally so all providers share one exact-head contract.
for required in (
    "const REQUIRED_CHECKS = Object.freeze({",
    "'Validate workflow YAML and embedded Python'",
    "'Verify Gemini free-only guardrails'",
    "'Reject known held assets and data'",
    "'Check proposed source paths using trusted base policy'",
    "'Host pause/resume state tests'",
    "'build-gamecube-demo'",
    "'Dolphin headless process smoke (not visual verification)'",
    "async function validateAutonomousCycleReport(options)",
    "BOONTA_CYCLE_TASK_ID",
    "BOONTA_CYCLE_STATUS:",
    "BOONTA_CYCLE_STATUS: PROGRESS",
    "BOONTA_CYCLE_STATUS: BLOCKED",
    "BOONTA_CYCLE_EVIDENCE:",
    "BOONTA_CYCLE_EVIDENCE_BASE",
    "expectedBase",
    "github.rest.pulls.get",
    "github.rest.repos.getCommit",
    "github.rest.checks.listForRef",
    "pr.head.repo?.full_name !== owner + '/' + repo",
    "pr.base.repo?.full_name !== owner + '/' + repo",
    "pr.draft === true",
    "pr.head.sha !== exactHead",
    "headCommit.sha !== exactHead",
    "(pr.changed_files ?? 0) < 1",
    "pr.base.ref !== expectedBase",
    "bodyHasTaskMarker",
    "bodyHasTargetBranchMarker",
    "createdAfterSnapshot",
    "advancedDuringCycle",
    "contentChangedDuringCycle",
    "previousHeadCommit.commit?.tree?.sha",
    "exactTreeSha",
    "!contentChangedDuringCycle",
    "run.head_sha === exactHead",
    "run.app?.slug === 'github-actions'",
    "check.status === 'completed' && check.conclusion === 'success'",
    "core.setOutput('cycle_status', 'progress')",
    "core.setOutput('cycle_status', 'blocked')",
    "maxPolls = 32",
    "pollIntervalMs = 15000",
    "const { data: finalPr } = await github.rest.pulls.get",
    "finalPr.state !== 'open'",
    "finalPr.head.repo?.full_name !== owner + '/' + repo",
    "finalPr.base.repo?.full_name !== owner + '/' + repo",
    "finalPr.head.sha !== exactHead",
    "finalPr.base.ref !== expectedBase",
    "changed while exact-head CI was running",
):
    if required not in cycle_validator:
        errors.append(f"Shared autonomous report validator is missing exact-head safety contract: {required!r}")

if "test_autonomous_cycle_report.js" not in selftest:
    errors.append("Branch self-test must watch the shared cycle validator and its regression suite")
if "node tools/test_autonomous_cycle_report.js" not in selftest:
    errors.append("Branch self-test must execute the shared autonomous cycle report regression suite")
if "on:\n  pull_request:\n    branches:\n      - main\n  workflow_dispatch:" not in selftest:
    errors.append("Branch self-test must run on every main PR so exact-head progress can require its validator check")
for required in (
    "missing PR target-branch marker",
    "duplicate PR target-branch markers",
    "required check failed",
    "validator self-test check is required",
    "same-name check from an untrusted app is ignored",
    "wait for exact-head checks",
    "dev target uses native build/host/emulator checks",
    "named task blocker",
    "fresh empty commit on an existing PR is not progress",
    "existing PR with changed tree content is eligible for exact-head checks",
    "PR head updated while exact-head CI was polling",
    "PR closed while exact-head CI was polling",
    "PR head repository changed while exact-head CI was polling",
    "PR base changed while exact-head CI was polling",
):
    if required not in cycle_validator_tests:
        errors.append(f"Shared autonomous report tests are missing regression case {required!r}")

for label, workflow in (("Gemini", execute), ("OpenRouter fallback", openrouter_fallback), ("Groq fallback", groq_fallback)):
    report_name = "Validate autonomous cycle report contract" if label == "Gemini" else "Validate OpenRouter autonomous cycle report" if label == "OpenRouter fallback" else "Validate Groq autonomous cycle report"
    report_start = workflow.find("      - name: " + report_name)
    report_end = workflow.find("      - name: Sync the single-task daily backoff marker", report_start)
    report_step = workflow[report_start:report_end] if report_start >= 0 and report_end > report_start else ""
    for required in (
        "id: validate_report",
        "validateAutonomousCycleReport",
        "expectedTaskId: process.env.SELECTED_TASK_ID",
        "expectedBase: process.env.SELECTED_TASK_TARGET_BRANCH",
        "baseline: JSON.parse(process.env.PRE_CYCLE_PR_HEADS || '{}')",
        "snapshotAt: process.env.PRE_CYCLE_PR_SNAPSHOT_AT",
        "steps.snapshot_pr_heads.outputs.heads",
        "PRE_CYCLE_PR_SNAPSHOT_AT",
    ):
        if required not in report_step:
            errors.append(f"{label} must call the shared exact-head cycle validator with {required!r}")
    if "id: snapshot_pr_heads" not in workflow or "state: 'open'" not in workflow:
        errors.append(f"{label} must snapshot only currently open PR heads before the model call")
    if "github.paginate(github.rest.pulls.list" not in workflow:
        errors.append(f"{label} must capture the complete pre-cycle PR inventory")
    if "inputs.autonomous_mode == true" not in workflow and "steps.free_tier_guard.outputs.allowed == 'true'" not in workflow:
        errors.append(f"{label} must keep the pre-cycle snapshot behind the free-tier/owner gate")
    if ("SELECTED_TASK_ID: '${{ inputs.task_id }}'" not in report_step and "SELECTED_TASK_ID: ${{ inputs.task_id }}" not in report_step) or (
        "SELECTED_TASK_TARGET_BRANCH: '${{ inputs.task_target_branch }}'" not in report_step and
        "SELECTED_TASK_TARGET_BRANCH: ${{ inputs.task_target_branch }}" not in report_step
    ):
        errors.append(f"{label} must bind validation to the exact task and target branch selected by preflight")
if "github.rest.checks.listForRef" not in cycle_validator:
    errors.append("Autonomous progress must wait for the exact PR-head check runs before reporting progress")
if "The check runs must be from the GitHub Actions app" not in cycle_validator and "run.app?.slug === 'github-actions'" not in cycle_validator:
    errors.append("Autonomous exact-head checks must reject same-named runs from untrusted apps")
if "exact-40-character-head-SHA" not in autonomous_prompt or "BOONTA_CYCLE_EVIDENCE_BASE: main|dev" not in autonomous_prompt:
    errors.append("Gemini autonomous prompt must require exact-head evidence and its main/dev target")
if "BOONTA_CYCLE_EVIDENCE_BASE: ${TASK_TARGET_BRANCH}" not in openrouter_fallback:
    errors.append("OpenRouter fallback prompt must append the exact main/dev target reserved by task preflight")
for required in (
    '"$RUNNER_TEMP/opencode-cycle-report.txt"',
    'with open(report_path, "w", encoding="utf-8") as report:',
    'report.flush()',
):
    if required not in openrouter_fallback:
        errors.append(f"OpenRouter fallback must persist its final report for contract validation: {required!r}")
if "REPORT_PATH: ${{ runner.temp }}/opencode-cycle-report.txt" not in openrouter_fallback:
    errors.append("OpenRouter fallback must validate the report it just produced")
if "exact-40-character-head-SHA" not in autonomous_prompt:
    errors.append("Gemini autonomous prompt must show the exact PR-head evidence format")

# A BLOCKED report must not contradict facts already proven by the successful
# free-tier/owner preflight and GitHub App token creation in the same run.
for required in (
    "GEMINI_PREFLIGHT_ALLOWED: '${{ steps.free_tier_guard.outputs.allowed }}'",
    "GITHUB_APP_TOKEN_OUTCOME: '${{ steps.mint_identity_token.outcome }}'",
    "process.env.GEMINI_PREFLIGHT_ALLOWED === 'true'",
    "BLOCKED report contradicts successful Gemini preflight",
    "GITHUB_APP_TOKEN_OUTCOME === 'success'",
    "findBlockedReportContradictions(blockedText",
    "githubAppTokenMinted: process.env.GITHUB_APP_TOKEN_OUTCOME === 'success'",
    "GEMINI_AUTONOMOUS_ENABLED",
    "GEMINI_FREE_TIER_CONFIRMED",
    "GEMINI_API_KEY",
):
    if required not in execute:
        errors.append(f"Gemini report validator is missing its preflight-consistency guard: {required!r}")

# OpenRouter BLOCKED reports must agree with successful same-run preflight evidence.
# The shared validator catches both explicit auth errors and natural-language
# missing-key/token claims that would otherwise evade narrow string matching.
for required in (
    "OPENROUTER_PREFLIGHT_ALLOWED: ${{ steps.free_tier_guard.outputs.allowed }}",
    "OPENROUTER_AUTH_OUTCOME: ${{ steps.openrouter_auth_check.outcome }}",
    "GITHUB_APP_TOKEN_OUTCOME: ${{ steps.mint_identity_token.outcome }}",
    "findBlockedReportContradictions",
    "openRouterAuthSucceeded:",
    "githubAppTokenMinted:",
    "SAME-RUN VERIFIED EXECUTION FACTS",
    "Never ask the owner to replace the key.",
):
    if required not in openrouter_fallback:
        errors.append(f"OpenRouter report consistency guard is missing {required!r}")

for required in (
    "providerKeyUnavailable",
    "explicitAuthFailure",
    "tokenUnavailable",
    "appCredentialsMissing",
    "openRouterAuthSucceeded === true",
    "githubAppTokenMinted === true",
):
    if required not in cycle_validator:
        errors.append(f"Shared cycle validator is missing its preflight contradiction rule {required!r}")

for required in (
    "no provider key was available",
    "no verified live GitHub App token",
    "intentionally not exposed to the model",
    "successful authentication evidence is absent",
):
    if required not in cycle_validator_tests:
        errors.append(f"Cycle validator tests are missing credential-contradiction coverage {required!r}")

# The Groq Free fallback must remain useful under its observed 8k TPM limit.
# OpenCode supports per-model context/output limits; cap this agent well below TPM.
groq_config_match = re.search(
    r'cat > "\$RUNNER_TEMP/opencode\.json" <<\'JSON\'\n(.*?)\n\s*JSON',
    groq_fallback,
    re.DOTALL,
)
if not groq_config_match:
    errors.append("Groq fallback must expose a parseable OpenCode JSON config for bounded model limits")
else:
    try:
        groq_config = json.loads(groq_config_match.group(1))
        groq_model = (
            groq_config.get("provider", {})
            .get("groq", {})
            .get("models", {})
            .get("openai/gpt-oss-20b", {})
        )
        groq_limits = groq_model.get("limit", {})
        if groq_limits.get("context") != 1152 or groq_limits.get("output") != 384:
            errors.append(
                "Groq GPT-OSS 20B must remain capped at 1152 context / 384 output tokens so four direct-delivery steps stay below the observed TPM refusal"
            )
        if groq_model.get("temperature") is not True:
            errors.append("Groq GPT-OSS 20B must explicitly declare temperature support for deterministic tool-call settings")
        if groq_config.get("agent", {}).get("build", {}).get("temperature") != 0.2:
            errors.append("Groq build agent must request temperature 0.2 for focused structured tool calls")
        if groq_config.get("model") != "groq/openai/gpt-oss-20b":
            errors.append("Groq fallback must keep its fixed free-tier model")
        if groq_config.get("enabled_providers") != ["groq"]:
            errors.append("Groq fallback must keep its provider allow-list fixed to Groq")
    except (json.JSONDecodeError, AttributeError, TypeError) as exc:
        errors.append(f"Groq OpenCode config is invalid: {exc}")
for required in (
    "1,152/384 limits; max 4 steps (6,144 nominal tokens).",
    "No full bodies/comments for #156/#226/#279; new retrieved text below 300 tokens.",
    "new retrieved text below 300 tokens.",
    "Only MCP tools: create_branch, push_files, create_pull_request.",
    "Stop after the first quota, TPM, rate-limit, context or auth error; never retry.",
):
    if required not in groq_fallback:
        errors.append(f"Groq fallback must enforce its bounded text-only context: {required!r}")
if 'if (( ${#PROMPT} > 3600 )); then' not in groq_fallback:
    errors.append("Groq fallback must enforce the 3,600-character TPM prompt ceiling before inference")
if "€0 only" not in groq_fallback or "No paid routes, billing, credits, or provider/secret/settings changes." not in groq_fallback:
    errors.append("Groq fallback must explicitly preserve the €0/no-paid-route rule")


for required in (
    "OPENCODE_EXPERIMENTAL_CODE_MODE: 'false'",
    "Use FQNs: github_create_branch, github_push_files, github_create_pull_request.",
):
    if required not in groq_fallback:
        errors.append(f"Groq direct MCP tool contract is missing {required!r}")
for required in (
    "OPENCODE_EXPERIMENTAL_CODE_MODE: 'false'",
    "Model-visible top-level tools: github_get_file_contents, github_create_branch, github_push_files and github_create_pull_request.",
):
    if required not in openrouter_fallback:
        errors.append(f"OpenRouter direct MCP tool contract is missing {required!r}")

# Enforce the mandatory reverse-engineering-first reuse gate in project and provider instructions.
reverse_engineering_policy = read("docs/REVERSE_ENGINEERING_FIRST.md")
for label, content in (
    ("AGENTS.md", read("AGENTS.md")),
    ("GEMINI.md", instructions),
    ("PROJECT_OPERATING_RULES.md", read("docs/PROJECT_OPERATING_RULES.md")),
    ("Gemini autonomous prompt", autonomous_prompt),
    ("OpenRouter autonomous prompt", openrouter_fallback),
    ("Groq autonomous prompt", groq_fallback),
):
    if "docs/REVERSE_ENGINEERING_FIRST.md" not in content and label != "reverse-engineering policy":
        errors.append(f"{label} must explicitly reference the mandatory reverse-engineering-first policy")
for required in (
    "Never manually recreate",
    "DISCOVER → VERIFY → EXTRACT/CONVERT/REUSE → INTEGRATE → TEST",
    "licence/provenance",
    "manual recreation",
    "Reuse / reverse-engineering decision",
):
    if required not in reverse_engineering_policy:
        errors.append(f"Reverse-engineering-first policy is missing required decision-gate language: {required!r}")
if "REVERSE_ENGINEERING_FIRST.md" not in autonomous_prompt:
    errors.append("Gemini autonomous startup must read the reverse-engineering-first policy")
if "REVERSE_ENGINEERING_FIRST.md" not in openrouter_fallback:
    errors.append("OpenRouter autonomous prompt must read the reverse-engineering-first policy")
if "REVERSE_ENGINEERING_FIRST.md" not in groq_fallback:
    errors.append("Groq autonomous prompt must read the reverse-engineering-first policy")


if errors:
    print("AI free-tier safety checks FAILED:")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print("AI free-tier safety checks passed.")
print("- Manual writing remains owner-approved; scheduled autonomous writing has a separate exact-true owner gate.")
print("- Gemini manual and autonomous write paths use separate exact-true gates.")
print("- OpenRouter uses a capped manual reviewer and a separately gated free-only autonomous fallback; no paid model fallback, merge, or delete tools.")
print("- API-key route and artifact-upload disablement are present.")
print("- Read-only planning and branch/PR safeguards are present.")
print("- Project instructions retain the strict €0 requirement.")
print("- Project coordinator is on-demand only and posts to canonical issue #156.")
