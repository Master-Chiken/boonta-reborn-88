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
invoke_prompt = read(".github/commands/gemini-invoke.toml")
execute_prompt = read(".github/commands/gemini-plan-execute.toml")
instructions = read("GEMINI.md")
setup = read("docs/AI_AUTOMATION_SETUP.md")

# The approval/write path must be closed unless the owner deliberately enables it.
if "needs.dispatch.outputs.command == 'approve' && vars.GEMINI_WRITE_ENABLED != 'true'" not in dispatch:
    errors.append("Missing locked/write-disabled approval gate in gemini-dispatch.yml")
if "needs.dispatch.outputs.command == 'approve' && vars.GEMINI_WRITE_ENABLED == 'true'" not in dispatch:
    errors.append("Missing exact-true write gate in gemini-dispatch.yml")
if "GEMINI_WRITE_ENABLED" not in setup or "protect" not in setup.lower():
    errors.append("Setup documentation must require branch protection before enabling writes")

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
    "Never push a PR",
    "Never merge a PR",
    "open a pull request",
):
    if required_phrase not in execute_prompt:
        errors.append(f"Plan-execute prompt is missing required safeguard: {required_phrase!r}")

# Project-level instructions must retain the owner’s €0 condition.
if "€0" not in instructions:
    errors.append("GEMINI.md must preserve the strict €0 budget requirement")
if "GEMINI_WRITE_ENABLED=true" not in instructions:
    errors.append("GEMINI.md must document the exact write-enable gate")
if "payment method" not in instructions.lower():
    errors.append("GEMINI.md must forbid adding a payment method")

if errors:
    print("AI free-tier safety checks FAILED:")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print("AI free-tier safety checks passed.")
print("- Gemini write path is explicitly gated by GEMINI_WRITE_ENABLED=true.")
print("- Legacy Google Cloud / paid-auth configuration is absent.")
print("- API-key route and artifact-upload disablement are present.")
print("- Read-only planning and branch/PR safeguards are present.")
print("- Project instructions retain the strict €0 requirement.")
