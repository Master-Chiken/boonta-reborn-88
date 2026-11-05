#!/usr/bin/env python3
"""Static guardrails for the free-only Gemini GitHub Actions integration.

This test makes no network calls, uses no API key, and never invokes an AI model.
"""
from pathlib import Path
import re
import sys

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
setup = read("docs/AI_AUTOMATION_SETUP.md")
ci_triage = read(".github/workflows/ci-failure-triage.yml")
gamecube_build = read(".github/workflows/gamecube-demo-build.yml")
wii64_tests = read(".github/workflows/wii64-tool-tests.yml")

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
if "secrets.openrouter_api_key" not in openrouter.lower():
    errors.append("OpenRouter reviewer must read its API key from the OPENROUTER_API_KEY secret")

# Keep the secret out of the step that downloads and inspects the untrusted PR diff.
call_step_marker = "      - name: Call OpenRouter free route"
if call_step_marker not in openrouter:
    errors.append("OpenRouter secret must be isolated in a dedicated model-call step")
else:
    preparation_step, model_call_step = openrouter.split(call_step_marker, 1)
    if "secrets.openrouter_api_key" in preparation_step.lower():
        errors.append("OpenRouter API key must not be available while preparing or scanning the PR diff")
    if "openrouter_api_key: ${{ secrets.openrouter_api_key }}" not in model_call_step.lower():
        errors.append("OpenRouter API key must be injected only into the dedicated model-call step")
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
    "OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}",
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
    'No paid model/provider fallback is available',
    'ghcr.io/github/github-mcp-server:v0.27.0',
    'GITHUB_TOOLS',
    'opencode run --model openrouter/openrouter/free --auto',
    'npm install --global opencode-ai@1.19.5',
):
    if required not in openrouter_fallback:
        errors.append(f"OpenRouter fallback is missing required free-only/safety setting {required!r}")
if 'OPENROUTER_FREE_TIER_CONFIRMED:-}" != "true"' not in openrouter_fallback:
    errors.append("OpenRouter fallback must require the owner's exact-true Free-tier attestation")
if 'GEMINI_AUTONOMOUS_ENABLED:-}" != "true"' not in openrouter_fallback:
    errors.append("OpenRouter fallback must inherit the master autonomous owner gate")
fallback_guard = openrouter_fallback.find("id: free_tier_guard")
fallback_mint = openrouter_fallback.find("name: Mint scoped GitHub App token")
fallback_checkout = openrouter_fallback.find("name: Checkout the protected default branch")
fallback_install = openrouter_fallback.find("name: Install pinned OpenCode CLI")
fallback_model = openrouter_fallback.find("name: Run OpenCode through the OpenRouter Free route")
if not (0 <= fallback_guard < fallback_mint < fallback_checkout < fallback_install < fallback_model):
    errors.append("OpenRouter fallback must pass all owner/free gates before token mint, checkout, installation and model call")
for guarded_step in (
    "name: Mint scoped GitHub App token\n        id: mint_identity_token\n        if: steps.free_tier_guard.outputs.allowed == 'true'",
    "name: Checkout the protected default branch\n        if: steps.free_tier_guard.outputs.allowed == 'true'",
    "name: Install pinned OpenCode CLI\n        if: steps.free_tier_guard.outputs.allowed == 'true'",
    "name: Run OpenCode through the OpenRouter Free route\n        if: steps.free_tier_guard.outputs.allowed == 'true'",
):
    if guarded_step not in openrouter_fallback:
        errors.append(f"OpenRouter fallback step is not fail-closed: {guarded_step.splitlines()[0]!r}")
# OpenRouter Free fallback receives its own autonomous daily failure cooldown.
or_cooldown_position = openrouter_fallback.find("id: openrouter_cooldown")
or_guard_position = openrouter_fallback.find("id: free_tier_guard")
or_mint_position = openrouter_fallback.find("name: Mint scoped GitHub App token")
or_checkout_position = openrouter_fallback.find("name: Checkout the protected default branch")
or_install_position = openrouter_fallback.find("name: Install pinned OpenCode CLI")
or_run_position = openrouter_fallback.find("name: Run OpenCode through the OpenRouter Free route")
or_record_position = openrouter_fallback.find("name: Record same-day OpenRouter cooldown after an invocation failure")
or_validate_position = openrouter_fallback.find("name: Validate OpenRouter autonomous cycle report")
if not (0 <= or_cooldown_position < or_guard_position < or_mint_position < or_checkout_position < or_install_position < or_run_position < or_record_position < or_validate_position):
    errors.append("OpenRouter daily cooldown must run before its gate/model call and record invocation failures before report validation")
for required in (
    "github.paginate(github.rest.issues.listComments",
    "BOONTA_OPENROUTER_FAILURE_COOLDOWN:",
    "new Date().toISOString().slice(0, 10)",
    "OPENROUTER_COOLDOWN_ACTIVE",
    "OPENROUTER_COOLDOWN_DATE",
    "steps.run_opencode.outcome == 'failure'",
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
    "needs.autonomous-cycle.result == 'failure'",
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
if "only the current-state/owner-direction sections" not in openrouter_fallback or "latest five relevant comments per issue" not in openrouter_fallback or "never ingest full appendices" not in openrouter_fallback:
    errors.append("OpenRouter prompt must bound historical issue context to reduce repeated prompt/token overhead")

tools_match = re.search(r'"GITHUB_TOOLS": "([^"]+)"', openrouter_fallback)
if not tools_match:
    errors.append("OpenRouter fallback must define an auditable GitHub MCP tool allow-list")
else:
    github_tools = tools_match.group(1).split(",")
    forbidden_github_tools = [
        tool for tool in github_tools
        if any(fragment in tool.lower() for fragment in ("merge", "delete", "secret", "variable", "repository_settings", "repository_ruleset", "update_pull_request"))
    ]
    if forbidden_github_tools:
        errors.append(f"OpenRouter GitHub MCP allow-list exposes forbidden capabilities: {forbidden_github_tools!r}")
    for required_tool in ("create_branch", "push_files", "create_pull_request", "issue_read", "pull_request_read"):
        if required_tool not in github_tools:
            errors.append(f"OpenRouter GitHub MCP allow-list is missing {required_tool!r}")
    if "get_workflow_job" in github_tools:
        errors.append("OpenRouter GitHub MCP allow-list contains a tool absent from the pinned v0.27.0 server")
    for required_tool in ("get_file_contents", "get_workflow_run", "get_job_logs", "list_workflow_jobs", "list_workflow_runs"):
        if required_tool not in github_tools:
            errors.append(f"OpenRouter GitHub MCP allow-list is missing pinned-server tool {required_tool!r}")
fallback_call_position = autonomous.find("openrouter-fallback:")
if fallback_call_position < 0:
    errors.append("Boonta Autonomous Loop is missing the OpenRouter fallback job")
else:
    fallback_call = autonomous[fallback_call_position:]
    for required in (
        "needs: autonomous-cycle",
        "needs.autonomous-cycle.result == 'failure'",
        "uses: ./.github/workflows/openrouter-plan-execute.yml",
        "autonomous_mode: true",
        "issue_number: 226",
        "secrets: inherit",
    ):
        if required not in fallback_call:
            errors.append(f"OpenRouter fallback caller is missing {required!r}")
    if "github.ref == 'refs/heads/main'" not in fallback_call or "github.actor == github.repository_owner" not in fallback_call:
        errors.append("OpenRouter fallback caller must remain pinned to main and owner/schedule-gated")

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
    if "gemini_api_key: '${{ secrets.GEMINI_API_KEY }}'" not in content:
        errors.append(f"{label} must use only the GEMINI_API_KEY secret")
    if (
        "id: free_tier_guard" not in content
        or "GEMINI_FREE_TIER_CONFIRMED" not in content
        or "if: steps.free_tier_guard.outputs.allowed == 'true'" not in content
        or content.find("id: free_tier_guard") > content.find("name: 'Mint identity token'")
        or content.find("name: 'Mint identity token'") > content.find("name: 'Checkout Code'")
        or content.find("name: 'Checkout Code'") > content.find("name: 'Prepare prompt context'")
        or content.find("name: 'Prepare prompt context'") > content.find("name: 'Run Gemini CLI'")
        or "steps.free_tier_guard.outputs.allowed == 'true' && vars.APP_ID" not in content
        or "name: 'Checkout Code'\n        if: steps.free_tier_guard.outputs.allowed == 'true'" not in content
        or "name: 'Prepare prompt context'\n        if: steps.free_tier_guard.outputs.allowed == 'true'" not in content
    ):
        errors.append(f"{label} must fail closed before token mint, checkout, prompt preparation, and Gemini model call")
    if "gemini_model: 'gemini-3.5-flash-lite'" not in content:
        errors.append(f"{label} must keep the configured model explicit for owner review")
    if "upload_artifacts: 'false'" not in content:
        errors.append(f"{label} must keep workflow artifact upload disabled")

if not re.search(r"(?m)^\s*description\s*=\s*[\"']Runs the Gemini CLI in read-only planning mode[\"']", invoke_prompt):
    errors.append("Gemini invoke prompt must be explicitly read-only")
if "Do not edit files or call write tools" not in invoke_prompt:
    errors.append("Gemini invoke prompt must prohibit file writes")
if "@{.gemini/context.json}" not in invoke_prompt:
    errors.append("Gemini invoke prompt must inject the dispatcher request context directly")
if "{{args}}" not in invoke_prompt:
    errors.append("Gemini invoke prompt must include the triggering request arguments")

if "prompt: '/gemini-invoke ${{ inputs.additional_context }}'" not in invoke:
    errors.append("Gemini invoke workflow must pass the triggering request into the custom command")

if '--arg context "${ADDITIONAL_CONTEXT}"' not in invoke:
    errors.append("Gemini invoke workflow must copy the triggering comment into context.json")

for required_phrase in (
    "Always prioritize the exact request in `.gemini/context.json` and the triggering issue/PR comment.",
    "Do not replace a requested comparison or audit with a generic repository overview.",
    "Before responding, check each requested item and either answer it with concrete evidence and links or explicitly name the blocker.",
):
    if required_phrase not in invoke_prompt:
        errors.append(f"Gemini invoke prompt is missing task-following safeguard: {required_phrase!r}")

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
if "gemini_api_key: ${{ secrets.GEMINI_API_KEY }}" not in daily:
    errors.append("Project coordinator must use the existing Gemini API-key secret only")
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
if "- cron: '17 */6 * * *'" not in autonomous_trigger:
    errors.append("Boonta autonomous loop must use the bounded six-hour schedule")
if "group: boonta-autonomous-loop" not in autonomous or "cancel-in-progress: false" not in autonomous:
    errors.append("Boonta autonomous loop must serialize writers without cancelling active work")
if "group: boonta-single-writer" not in execute or "cancel-in-progress: false" not in execute:
    errors.append("All manual and autonomous Gemini writers must share one non-cancelling concurrency group")
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
    "full historical appendices/comments",
    "compact inventory of all open pull requests",
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
    "['schedule', 'workflow_dispatch'].includes(run.event)",
    "run.name === 'Boonta Autonomous Loop'",
    "run.head_branch === 'main'",
    "targetIssueNumber = 226",
):
    if required_guard not in ci_triage:
        errors.append(f"CI failure triage is missing safe main/dev exact-head guard {required_guard!r}")
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

# The owner-only readiness workflow checks configuration and App access without
# calling a model or performing repository writes.
readiness_trigger = readiness.split("permissions:", 1)[0]
readiness_events = re.findall(r"(?m)^  ([a-zA-Z0-9_-]+):\s*$", readiness_trigger)
if readiness_events != ["workflow_dispatch"]:
    errors.append(
        "Autonomous readiness must be manually dispatched only; "
        f"found {readiness_events!r}"
    )
if "if: github.ref == 'refs/heads/main' && github.actor == github.repository_owner" not in readiness:
    errors.append("Autonomous readiness must be owner-only and pinned to protected main")
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
    "permission-contents: write",
    "permission-issues: write",
    "permission-pull-requests: write",
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
# A scheduled run is allowed; a manual run is owner-only; no other event may
# invoke the autonomous writer.
autonomous_events = re.findall(r"(?m)^  ([a-zA-Z0-9_-]+):\s*$", autonomous_trigger)
if autonomous_events != ["schedule", "workflow_dispatch"]:
    errors.append(
        "Boonta autonomous loop may declare only schedule and workflow_dispatch events; "
        f"found {autonomous_events!r}"
    )
if "if: github.ref == 'refs/heads/main' && (github.event_name == 'schedule' || github.actor == github.repository_owner)" not in autonomous:
    errors.append("Autonomous schedule/manual dispatch must be owner-only and pinned to protected main")
if "workflow_dispatch:\n    inputs:" in autonomous_trigger:
    errors.append("Manual autonomous dispatch must not accept user-controlled task/issue overrides")

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

autonomous_job = autonomous.split("jobs:", 1)[1]
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
    if job_permissions != expected_caller_permissions:
        errors.append(
            "Autonomous reusable-workflow job permissions must be exactly the contents/issues/PR write set; "
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
if "gemini_model: 'gemini-3.5-flash-lite'" not in execute:
    errors.append("Autonomous workflow must keep the explicitly reviewed Gemini 3.5 Flash-Lite model")
if "upload_artifacts: 'false'" not in execute:
    errors.append("Autonomous workflow must keep third-party workflow artifact upload disabled")

# Scheduled autonomous runs must not stream verbose model output into public Actions logs.
expected_gemini_debug = "gemini_debug: '${{ inputs.autonomous_mode != true && fromJSON(vars.GEMINI_DEBUG || vars.ACTIONS_STEP_DEBUG || false) }}'"
if expected_gemini_debug not in execute:
    errors.append("Autonomous Gemini runs must disable verbose debug streaming; manual runs may opt in")


# Failed autonomous Gemini invocations create one persistent same-day cooldown marker.
cooldown_check_position = execute.find("id: gemini_cooldown")
cooldown_guard_position = execute.find("id: free_tier_guard")
cooldown_model_position = execute.find("name: 'Run Gemini CLI'")
cooldown_record_position = execute.find("name: Record same-day Gemini cooldown after an autonomous model failure")
if not (0 <= cooldown_check_position < cooldown_guard_position < cooldown_model_position < cooldown_record_position):
    errors.append("Gemini daily cooldown must be checked before the free-tier guard/model call and recorded after an invocation failure")
for required in (
    "github.paginate(github.rest.issues.listComments",
    "BOONTA_GEMINI_FAILURE_COOLDOWN:",
    "new Date().toISOString().slice(0, 10)",
    "GEMINI_COOLDOWN_ACTIVE",
    "GEMINI_COOLDOWN_DATE",
    "steps.gemini_cooldown.outputs.active != 'true'",
    "if: always() && inputs.autonomous_mode == true && steps.run_gemini.outcome == 'failure'",
    "github.rest.issues.updateComment",
    "github.rest.issues.createComment",
    "continue-on-error: true",
    "until the next UTC day",
):
    if required not in execute:
        errors.append(f"Gemini daily cooldown is missing required failover/persistence behavior: {required!r}")
if "if: inputs.autonomous_mode == true" not in execute[:cooldown_guard_position]:
    errors.append("Gemini daily cooldown must apply only to autonomous invocations, not the manual writer path")

# Both autonomous prompts limit historical issue context to reduce repeated token/context costs.
for required in (
    "only the current-state/owner-direction sections at the top of canonical dashboard issue #156, native-target queue #226 and comparative evidence queue #279",
    "latest five relevant comments per issue",
    "Search older comments only when the selected task needs specific historical evidence",
    "do not ingest or reproduce full historical appendices/comments",
):
    if required not in autonomous_prompt:
        errors.append(f"Gemini autonomous prompt must bound historical issue context: {required!r}")

# Autonomous progress must be cycle-fresh, same-repository evidence at the exact live head.
for label, workflow in (("Gemini", execute), ("OpenRouter fallback", openrouter_fallback)):
    if "BOONTA_CYCLE_STATUS: PROGRESS" not in workflow:
        errors.append(f"{label} must require the machine-readable PROGRESS status")
    if "BOONTA_CYCLE_STATUS: BLOCKED" not in workflow:
        errors.append(f"{label} must support an explicit BLOCKED report")
    if "BOONTA_CYCLE_EVIDENCE_BASE" not in workflow or "evidenceBaseMatch" not in workflow:
        errors.append(f"{label} must require the declared evidence base")
    if "id: snapshot_pr_heads" not in workflow or "state: 'all'" not in workflow:
        errors.append(f"{label} must snapshot existing open and closed PR heads before the model call")
    if "github.paginate(github.rest.pulls.list" not in workflow:
        errors.append(f"{label} must capture the complete pre-cycle PR inventory")
    if "steps.snapshot_pr_heads.outputs.heads" not in workflow:
        errors.append(f"{label} must pass the pre-cycle head inventory to the progress validator")
    if "github.rest.pulls.get" not in workflow or "github.rest.repos.getCommit" not in workflow:
        errors.append(f"{label} must verify the live PR and reported head commit")
    if "pr.head.repo?.full_name !== 'Master-Chiken/boonta-reborn-88'" not in workflow:
        errors.append(f"{label} must reject progress PRs whose head comes from a fork")
    if "pr.head.sha !== evidence[2]" not in workflow or "headCommit.sha !== evidence[2]" not in workflow or "(pr.changed_files ?? 0) < 1" not in workflow:
        errors.append(f"{label} must require a non-empty PR at the exact reported head SHA")
    if "const unchangedAtStart = existedAtStart && baseline[String(pr.number)] === evidence[2]" not in workflow:
        errors.append(f"{label} must reject an unchanged PR that existed at cycle start")
    if "pr.base.ref !== evidenceBaseMatch[1]" not in workflow:
        errors.append(f"{label} must check the PR's actual base against its reported main/dev target")
    if "inputs.autonomous_mode == true" not in workflow and "steps.free_tier_guard.outputs.allowed == 'true'" not in workflow:
        errors.append(f"{label} must keep the pre-cycle snapshot behind the free-tier/owner gate")
if "exact-40-character-head-SHA" not in autonomous_prompt or "BOONTA_CYCLE_EVIDENCE_BASE: main|dev" not in autonomous_prompt:
    errors.append("Gemini autonomous prompt must require exact-head evidence and its main/dev target")
if "BOONTA_CYCLE_EVIDENCE_BASE: main|dev" not in openrouter_fallback:
    errors.append("OpenRouter fallback prompt must require the reported main/dev PR target")
if "tee \"$RUNNER_TEMP/opencode-cycle-report.txt\"" not in openrouter_fallback:
    errors.append("OpenRouter fallback must persist its final report for contract validation")
if "REPORT_PATH: ${{ runner.temp }}/opencode-cycle-report.txt" not in openrouter_fallback:
    errors.append("OpenRouter fallback must validate the report it just produced")
if "exact-40-character-head-SHA" not in autonomous_prompt:
    errors.append("Gemini autonomous prompt must show the exact PR-head evidence format")

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
