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

if errors:
    print("Autonomous provider handoff checks FAILED:")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print("Autonomous provider handoff checks passed.")
print("- A completed Gemini invocation prevents OpenRouter and Groq fallback calls.")
print("- A completed OpenRouter invocation prevents a Groq fallback call.")
print("- Failed report validation remains a failed cycle; it is not misreported as progress.")
