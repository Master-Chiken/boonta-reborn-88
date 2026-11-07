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
errors: list[str] = []

# Provider invocations and validated reports must be separately observable.
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

if "One model provider invocation at most per Boonta Autonomous Loop run" not in budget:
    errors.append("Shared context budget must enforce at most one model provider invocation per workflow run")
if "At most one provider invocation is allowed per workflow run" not in loop:
    errors.append("Autonomous loop summary must disclose the one-provider-per-run rule")
if "needs: [readiness, provider-cooldowns]" not in loop:
    errors.append("Gemini must depend on the global cooldown preflight")

# Keep all agents bounded to compact text-only context and the common policy.
for label, content in (
    ("Gemini", gemini_prompt),
    ("OpenRouter", openrouter),
    ("Groq", groq),
):
    for required in (
        "docs/automation/AUTONOMOUS_CONTEXT_BUDGET.md",
        "docs/automation/task-ledger-summary.json",
        "1,500 tokens",
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

openrouter_tools = set(
    openrouter_config.get("mcp", {}).get("github", {}).get("environment", {}).get("GITHUB_TOOLS", "").split(",")
)
groq_tools = set(
    groq_config.get("mcp", {}).get("github", {}).get("environment", {}).get("GITHUB_TOOLS", "").split(",")
)
required_writer_tools = {
    "get_file_contents", "pull_request_read", "create_branch",
    "push_files", "create_pull_request", "add_issue_comment",
}
for label, toolset in (("OpenRouter", openrouter_tools), ("Groq", groq_tools)):
    if not required_writer_tools.issubset(toolset):
        errors.append(f"{label} is missing a required bounded branch/PR editing tool")
    forbidden = {
        "issue_read", "list_issues", "list_pull_requests", "create_or_update_file",
        "list_branches", "list_commits", "merge_pull_request", "delete_branch",
        "update_pull_request",
    }
    if forbidden.intersection(toolset):
        errors.append(f"{label} MCP allow-list exposes unnecessary or unsafe tools: {sorted(forbidden.intersection(toolset))}")

required_openrouter_ci_tools = {
    "search_pull_requests", "list_workflow_runs", "list_workflow_jobs",
    "get_workflow_run", "get_job_logs",
}
if not required_openrouter_ci_tools.issubset(openrouter_tools):
    errors.append("OpenRouter must retain bounded read-only PR/Actions CI diagnostic tools")
if groq_tools != required_writer_tools:
    errors.append("Groq must retain the reviewed six-tool minimal GitHub MCP allow-list")

gemini_settings_match = re.search(r'"includeTools":\s*\[(.*?)\]', gemini, re.DOTALL)
if not gemini_settings_match:
    errors.append("Gemini MCP allow-list is missing")
else:
    gemini_tools = set(re.findall(r'"([^"]+)"', gemini_settings_match.group(1)))
    if not required_writer_tools.issubset(gemini_tools):
        errors.append("Gemini MCP allow-list is missing a bounded branch/PR editing tool")
    if not required_openrouter_ci_tools.issubset(gemini_tools):
        errors.append("Gemini must retain bounded read-only PR/Actions CI diagnostic tools")
    if {"merge_pull_request", "delete_branch", "update_pull_request", "list_pull_requests"}.intersection(gemini_tools):
        errors.append("Gemini MCP allow-list exposes an unsafe or unavailable repository mutation/list tool")

# Confirm the Groq cap is below the observed 8k TPM limit and its prompt has a
# pre-inference size guard. The workflow remains €0-only.
groq_limits = (
    groq_config.get("provider", {})
    .get("groq", {})
    .get("models", {})
    .get("openai/gpt-oss-20b", {})
    .get("limit", {})
)
if groq_limits.get("context") != 3072 or groq_limits.get("output") != 512:
    errors.append("Groq must remain capped at 3072 context / 512 output tokens")
for content, needle, message in (
    (groq, "if (( ${#PROMPT} > 7000 )); then", "Groq must enforce its prompt-size guard before inference"),
    (groq, "timeout --signal=TERM --kill-after=5s 90s", "Groq must enforce the 90-second invocation timeout"),
    (openrouter, "if (( ${#PROMPT} > 7000 )); then", "OpenRouter must enforce its final-prompt-size guard before inference"),
    (openrouter, "timeout --signal=TERM --kill-after=5s 180s", "OpenRouter must enforce the 180-second invocation timeout"),
    (groq, "Never enable billing, paid routes", "Groq must preserve the €0/no-paid-route rule"),
    (openrouter, "No paid model/provider fallback is available", "OpenRouter must preserve the €0/no-paid-route rule"),
    (openrouter, "github_get_pull_request does not exist", "OpenRouter must name the supported PR read tool and reject an unavailable alias"),
    (groq, "github_get_pull_request does not exist", "Groq must name the supported PR read tool and reject an unavailable alias"),
):
    if needle not in content:
        errors.append(message)

if errors:
    print("Autonomous provider handoff checks FAILED:")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print("Autonomous provider handoff checks passed.")
print("- At most one provider can invoke a model in a workflow run.")
print("- Fallbacks advance only on later cycles after a pre-existing UTC cooldown.")
print("- Provider limits, CI diagnostics, and €0-only restrictions are enforced.")
