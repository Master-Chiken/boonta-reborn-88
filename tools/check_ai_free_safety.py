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

# Workflow files must not reference OpenRouter; the secret may remain unused until audited.
workflow_text = "\n".join(
    path.read_text(encoding="utf-8")
    for path in (ROOT / ".github" / "workflows").glob("*.yml")
)
if "openrouter_api_key" in workflow_text.lower() or "openrouter.ai" in workflow_text.lower():
    errors.append("GitHub Actions workflows must not use OpenRouter in the €0-only setup")

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
    if "gemini_model: 'gemini-3.5-flash-lite'" not in content:
        errors.append(f"{label} must keep the configured model explicit for owner review")
    if "upload_artifacts: 'false'" not in content:
        errors.append(f"{label} must keep workflow artifact upload disabled")

if not re.search(r"(?m)^\s*description\s*=\s*[\"']Runs the Gemini CLI in read-only planning mode[\"']", invoke_prompt):
    errors.append("Gemini invoke prompt must be explicitly read-only")
if "Do not edit files or call write tools" not in invoke_prompt:
    errors.append("Gemini invoke prompt must prohibit file writes")

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

# The scheduled coordinator must remain read-only and run no more than once daily.
if 'cron: "15 7 * * *"' not in daily:
    errors.append("Daily coordinator must have one fixed daily schedule")
if "contents: write" in daily or "pull-requests: write" in daily:
    errors.append("Daily coordinator must not have repository/code write permissions")
if 'issues: write' not in daily:
    errors.append("Daily coordinator needs issue-comment permission to publish its report")
for forbidden in ('"create_branch"', '"create_or_update_file"', '"push_files"', '"delete_file"', '"create_pull_request"', '"merge_pull_request"'):
    if forbidden in daily:
        errors.append(f"Daily coordinator must not expose write tool {forbidden}")
if "gemini_api_key: ${{ secrets.GEMINI_API_KEY }}" not in daily:
    errors.append("Daily coordinator must use the existing Gemini API-key secret only")
if 'gemini_model: "gemini-3.5-flash-lite"' not in daily:
    errors.append("Daily coordinator must keep the explicitly selected free-tier model")
if "READ ONLY" not in daily_prompt or "€0" not in daily_prompt:
    errors.append("Daily coordinator prompt must enforce read-only and €0 constraints")
if "Never push" not in daily_prompt or "Never recommend publishing ROMs" not in daily_prompt:
    errors.append("Daily coordinator prompt must preserve branch and provenance safety")

if errors:
    print("AI free-tier safety checks FAILED:")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print("AI free-tier safety checks passed.")
print("- Only the repository owner can authorize the Gemini write workflow.")
print("- Gemini write path remains gated by GEMINI_WRITE_ENABLED=true.")
print("- OpenRouter and legacy Google Cloud / paid-auth routes are absent from workflows.")
print("- API-key route and artifact-upload disablement are present.")
print("- Read-only planning and branch/PR safeguards are present.")
print("- Project instructions retain the strict €0 requirement.")
