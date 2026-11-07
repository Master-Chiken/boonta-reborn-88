#!/usr/bin/env python3
"""Static checks for the autonomous provider handoff contract.

This test is offline: it does not call a model, inspect credentials, or invoke
GitHub Actions. It prevents fallbacks from chaining after a provider call has
already completed and only its report validation failed.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "gemini": ROOT / ".github/workflows/gemini-plan-execute.yml",
    "openrouter": ROOT / ".github/workflows/openrouter-plan-execute.yml",
    "loop": ROOT / ".github/workflows/boonta-autonomous-loop.yml",
}

def read(name: str) -> str:
    path = FILES[name]
    if not path.is_file():
        raise SystemExit(f"Missing required workflow: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")

gemini = read("gemini")
openrouter = read("openrouter")
loop = read("loop")
errors = []

required = (
    (gemini, "value: ${{ jobs.plan-execute.outputs.invocation_outcome }}", "Gemini workflow_call must expose its invocation outcome"),
    (gemini, "invocation_outcome: ${{ steps.run_gemini.outcome }}", "Gemini job must publish the run_gemini step outcome"),
    (openrouter, "value: ${{ jobs.openrouter-plan-execute.outputs.invocation_outcome }}", "OpenRouter workflow_call must expose its invocation outcome"),
    (openrouter, "invocation_outcome: ${{ steps.run_opencode.outcome }}", "OpenRouter job must publish the run_opencode step outcome"),
    (loop, "needs.autonomous-cycle.outputs.invocation_outcome != 'success'", "OpenRouter fallback must not run after a successful Gemini invocation"),
    (loop, "needs.openrouter-fallback.outputs.invocation_outcome != 'success'", "Groq fallback must not run after a successful OpenRouter invocation"),
)
for content, needle, message in required:
    if needle not in content:
        errors.append(message)

# The Gemini guard must appear in both fallback conditions: a successful call
# with an invalid report is still a completed provider invocation.
if loop.count("needs.autonomous-cycle.outputs.invocation_outcome != 'success'") != 2:
    errors.append("Both OpenRouter and Groq fallback conditions must gate on the Gemini invocation outcome")

if "needs.openrouter-fallback.outputs.invocation_outcome != 'success'" not in loop:
    errors.append("Groq fallback must gate on the OpenRouter invocation outcome")

# Ensure every autonomous provider uses the compact context contract. The
# OpenRouter MCP allow-list must not expose full issue-body/listing tools.
gemini_prompt = (ROOT / ".github/commands/gemini-autonomous-loop.toml").read_text(encoding="utf-8")
groq = (ROOT / ".github/workflows/groq-plan-execute.yml").read_text(encoding="utf-8")
budget = ROOT / "docs/automation/AUTONOMOUS_CONTEXT_BUDGET.md"
summary = ROOT / "docs/automation/task-ledger-summary.json"
for label, content in (("Gemini", gemini_prompt), ("OpenRouter", openrouter), ("Groq", groq)):
    if "docs/automation/AUTONOMOUS_CONTEXT_BUDGET.md" not in content:
        errors.append(f"{label} prompt must reference the shared context budget")
    if "docs/automation/task-ledger-summary.json" not in content:
        errors.append(f"{label} prompt must use the compact task summary")
    if "1,500 tokens" not in content:
        errors.append(f"{label} prompt must state the 1,500-token retrieval budget")
if not budget.is_file() or not summary.is_file():
    errors.append("The shared context budget and compact task summary must exist")
tool_config = openrouter.split('"GITHUB_TOOLS": "', 1)
if len(tool_config) != 2:
    errors.append("OpenRouter MCP tool allow-list is missing")
else:
    exposed = sorted({"issue_read", "list_issues", "list_pull_requests", "create_or_update_file", "list_branches", "list_commits"}.intersection(
        tool_config[1].split('"', 1)[0].split(",")
    ))
    if exposed:
        errors.append("OpenRouter must not expose broad issue/listing or one-file write tools: " + ", ".join(exposed))

# Parse the exact OpenCode 1.19.5 runtime configs and enforce finite agent turns.
import json
import re

def load_opencode_config(label: str, content: str) -> dict:
    marker = 'cat > "$RUNNER_TEMP/opencode.json" <<\'JSON\'\n'
    parts = content.split(marker, 1)
    if len(parts) != 2:
        errors.append(f"{label} fallback must expose a parseable OpenCode JSON config")
        return {}
    payload, separator, _rest = parts[1].partition("\n          JSON")
    if not separator:
        errors.append(f"{label} OpenCode JSON config closing delimiter is missing")
        return {}
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        errors.append(f"{label} OpenCode JSON config is invalid: {exc}")
        return {}

groq_config = load_opencode_config("Groq", groq)
openrouter_config = load_opencode_config("OpenRouter", openrouter)
if groq_config.get("agent", {}).get("build", {}).get("steps") != 4:
    errors.append("Groq OpenCode build agent must be limited to exactly 4 agentic steps")
if openrouter_config.get("agent", {}).get("build", {}).get("steps") != 6:
    errors.append("OpenRouter OpenCode build agent must be limited to exactly 6 agentic steps")

# MCP tool descriptions contribute to every model request. Keep each provider's
# allow-list minimal and forbid broad history/file tools that are not needed.
openrouter_tools = set(
    openrouter_config.get("mcp", {}).get("github", {}).get("environment", {}).get("GITHUB_TOOLS", "").split(",")
)
groq_tools = set(
    groq_config.get("mcp", {}).get("github", {}).get("environment", {}).get("GITHUB_TOOLS", "").split(",")
)
for label, toolset in (("OpenRouter", openrouter_tools), ("Groq", groq_tools)):
    forbidden = {"issue_read", "list_issues", "list_pull_requests", "create_or_update_file", "list_branches", "list_commits"}
    exposed = sorted(forbidden.intersection(toolset))
    if exposed:
        errors.append(f"{label} MCP allow-list exposes unnecessary broad tools: " + ", ".join(exposed))
required_groq_tools = {
    "get_file_contents", "pull_request_read", "create_branch",
    "push_files", "create_pull_request", "add_issue_comment",
}
if groq_tools != required_groq_tools:
    errors.append("Groq MCP allow-list must remain the reviewed six-tool minimal set")
if openrouter_tools != {
    "get_file_contents", "search_issues", "search_pull_requests", "pull_request_read",
    "create_branch", "push_files", "create_pull_request", "add_issue_comment", "get_commit",
    "list_workflow_runs", "list_workflow_jobs", "get_workflow_run", "get_job_logs", "search_code",
}:
    errors.append("OpenRouter MCP allow-list must remain at the reviewed minimal tool set")

# Provider prompts must call the actual pinned MCP tool names, not guessed aliases.
for label, prompt in (
    ("OpenRouter", openrouter),
    ("Groq", groq),
):
    if "github_pull_request_read" not in prompt:
        errors.append(f"{label} prompt must name the supported github_pull_request_read tool")
    if "github_get_pull_request" not in prompt or "does not exist" not in prompt:
        errors.append(f"{label} prompt must explicitly reject the unavailable github_get_pull_request alias")

if errors:
    print("Autonomous provider handoff checks FAILED:")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print("Autonomous provider handoff checks passed.")
print("- A completed Gemini invocation prevents OpenRouter and Groq fallback calls.")
print("- A completed OpenRouter invocation prevents a Groq fallback call.")
print("- Failed report validation remains a failed cycle; it is not misreported as progress.")
