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
invoke_prompt = read(".github/commands/gemini-invoke.toml")
execute_prompt = read(".github/commands/gemini-plan-execute.toml")
instructions = read("GEMINI.md")
setup = read("docs/AI_AUTOMATION_SETUP.md")

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
workflow_dir = ROOT / ".github" / "workflows"
workflow_files = sorted({*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")})
for path in workflow_files:
    if path.name == "openrouter-free-review.yml":
        continue
    content = path.read_text(encoding="utf-8").lower()
    if "openrouter_api_key" in content or "openrouter.ai" in content:
        errors.append(f"OpenRouter references are forbidden outside the allowlisted reviewer: {path.name}")

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
    "RE-001 issue #226 is intentionally PAUSED" not in daily
    or "do not continue its research or start RE-002 unless an explicit owner instruction resumes it" not in daily
    or "RE-001 (issue #226) is explicitly PAUSED" not in daily_prompt
    or "must not recommend restarting it as the next task" not in daily_prompt
):
    errors.append("AI coordinator must preserve the owner's explicit RE-001 pause and must not restart that research autonomously")
if "Never push" not in daily_prompt or "Never recommend publishing ROMs" not in daily_prompt:
    errors.append("Project coordinator prompt must preserve branch and provenance safety")

if errors:
    print("AI free-tier safety checks FAILED:")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print("AI free-tier safety checks passed.")
print("- Only the repository owner can authorize the Gemini write workflow.")
print("- Gemini write path remains gated by GEMINI_WRITE_ENABLED=true.")
print("- OpenRouter uses only the manual, capped, free-route PR reviewer; no paid fallback or code-write permissions.")
print("- API-key route and artifact-upload disablement are present.")
print("- Read-only planning and branch/PR safeguards are present.")
print("- Project instructions retain the strict €0 requirement.")
print("- Project coordinator is on-demand only and posts to canonical issue #156.")
