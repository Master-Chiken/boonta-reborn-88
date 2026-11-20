#!/usr/bin/env python3
"""Obtain one strict JSON patch proposal from OpenCode without exposing write tools.

The provider receives only a bounded text prompt and cannot access GitHub MCP,
the shell, files, or subagents. The proposal is validated against the exact
target SHA and a separately pinned trusted policy checkout before it is saved.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import selectors
import shutil
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

from autonomous_patch_proposal import (
    ProposalError,
    load_allowlist_report,
    validate_checkout,
    validate_proposal,
)

MAX_PROMPT_BYTES = 32 * 1024
MAX_STREAM_BYTES = 256 * 1024
MAX_STDERR_BYTES = 64 * 1024
MAX_PROPOSAL_BYTES = 96 * 1024
MAX_TIMEOUT_SECONDS = 180
ALLOWED_MODELS = {
    "groq/openai/gpt-oss-20b",
    "openrouter/openrouter/free",
}
SAFE_ENV_KEYS = (
    "PATH", "HOME", "TMP", "TEMP", "TMPDIR", "SYSTEMROOT", "WINDIR",
    "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR", "NODE_EXTRA_CA_CERTS",
    "NODE_OPTIONS", "XDG_CACHE_HOME", "XDG_CONFIG_HOME",
    "OPENCODE_CONFIG", "OPENCODE_EXPERIMENTAL_CODE_MODE",
)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class ProviderPatchError(ValueError):
    """Raised when provider output cannot be accepted as a strict patch."""

    def __init__(self, message: str, *, provider_request_started: bool = False) -> None:
        super().__init__(message)
        self.provider_request_started = provider_request_started


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ProviderPatchError(f"Duplicate JSON property: {key}")
        value[key] = item
    return value


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _read_prompt(path: Path) -> str:
    if path.is_symlink():
        raise ProviderPatchError("Prompt file must not be a symlink")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ProviderPatchError("Prompt file could not be read") from exc
    if not raw or len(raw) > MAX_PROMPT_BYTES:
        raise ProviderPatchError("Prompt must be between 1 byte and 32 KiB")
    try:
        return raw.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ProviderPatchError("Prompt must be valid UTF-8") from exc


def _provider_environment(model: str) -> dict[str, str]:
    env = {key: os.environ[key] for key in SAFE_ENV_KEYS if key in os.environ}
    env["CI"] = "true"
    env["NO_COLOR"] = "1"
    env["OPENCODE_EXPERIMENTAL_CODE_MODE"] = "false"
    if model == "groq/openai/gpt-oss-20b":
        key = os.environ.get("GROQ_API_KEY", "")
        if len(key) < 20:
            raise ProviderPatchError("Groq credentials are unavailable")
        env["GROQ_API_KEY"] = key
    elif model == "openrouter/openrouter/free":
        auth = os.environ.get("OPENCODE_AUTH_CONTENT", "")
        if not auth:
            raise ProviderPatchError("OpenRouter credentials are unavailable")
        env["OPENCODE_AUTH_CONTENT"] = auth
    else:
        raise ProviderPatchError("Provider model is not in the €0-only allow-list")
    return env


def _validate_opencode_config() -> None:
    config_path = os.environ.get("OPENCODE_CONFIG", "")
    if not config_path:
        raise ProviderPatchError("A dedicated no-tools OpenCode config is required")
    path = Path(config_path)
    if path.is_symlink() or not path.is_file():
        raise ProviderPatchError("OpenCode config must be a regular non-symlink file")
    try:
        config = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProviderPatchError("OpenCode config is not valid JSON") from exc
    if not isinstance(config, dict):
        raise ProviderPatchError("OpenCode config root must be an object")
    permissions = config.get("permission")
    if (
        not isinstance(permissions, dict)
        or permissions.get("*") != "deny"
        or any(action != "deny" for action in permissions.values())
    ):
        raise ProviderPatchError("OpenCode config must deny every model tool without per-tool exceptions")
    if config.get("mcp") not in (None, {}):
        raise ProviderPatchError("OpenCode patch generation must not expose MCP servers")


def _build_prompt(
    context: str,
    *,
    task_id: str,
    target_sha: str,
    policy_sha: str,
    allowed_paths: set[str],
) -> str:
    paths = "\n".join(f"- {path}" for path in sorted(allowed_paths))
    schema = {
        "schema_version": 1,
        "task_id": task_id,
        "base_sha": target_sha,
        "summary": "Brief implementation summary, maximum 240 characters",
        "unified_diff": "A complete unified git diff for existing tracked files only",
        "test_ids": ["automation.task_preflight"],
        "limitations": [],
    }
    return "\n".join([
        "You are a patch proposer, not an autonomous tool-using agent.",
        "Return exactly one JSON object. No Markdown fences, prose, comments, or extra keys.",
        "You have no tools. Do not claim to have run tests or changed files.",
        "Implement only the task described in the supplied context.",
        "Use only these exact owner-approved write paths:",
        paths,
        "Do not create or delete files. Do not change task ledgers, automation policy, workflow files, secrets, settings, or permissions.",
        "The unified_diff must use standard git diff headers (diff --git a/PATH b/PATH, --- a/PATH, +++ b/PATH) and must apply to the exact target checkout.",
        "Choose test_ids only from: automation.task_preflight, automation.provider_handoff, automation.task_ledger.",
        "List uncertainty or incomplete verification in limitations. Never invent test success.",
        "Strict output shape (the example values are placeholders):",
        json.dumps(schema, ensure_ascii=False, separators=(",", ":")),
        f"Task ID: {task_id}",
        f"Target checkout base SHA: {target_sha}",
        f"Trusted policy checkout SHA: {policy_sha}",
        "Authoritative task context:",
        context,
    ])


def parse_event_stream(raw: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise ProviderPatchError("OpenCode produced an empty event stream")
    if len(raw.encode("utf-8")) > MAX_STREAM_BYTES:
        raise ProviderPatchError("OpenCode event stream exceeded the 256 KiB limit")
    texts: list[str] = []
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line, object_pairs_hook=_unique_object)
        except (json.JSONDecodeError, ProviderPatchError) as exc:
            raise ProviderPatchError(f"OpenCode emitted invalid NDJSON at line {line_number}") from exc
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise ProviderPatchError(f"OpenCode emitted an invalid event at line {line_number}")
        event_type = event["type"]
        if event_type in {"step_start", "step_finish", "reasoning"}:
            continue
        if event_type == "tool_use":
            raise ProviderPatchError("OpenCode attempted a tool call; patch proposal rejected")
        if event_type == "error":
            raise ProviderPatchError("OpenCode reported a provider or session error")
        if event_type != "text":
            raise ProviderPatchError(f"OpenCode emitted an unsupported event type: {event_type}")
        part = event.get("part")
        if not isinstance(part, dict) or part.get("type") != "text" or not isinstance(part.get("text"), str):
            raise ProviderPatchError("OpenCode text event did not match the expected event contract")
        if part["text"].strip():
            texts.append(part["text"])
    if len(texts) != 1:
        raise ProviderPatchError("OpenCode must return exactly one non-empty assistant text event")
    return texts[0].strip()



def _stop_process_group(process: subprocess.Popen[bytes]) -> None:
    """Terminate OpenCode and any descendants without leaving orphan processes."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        return
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass


def _run_bounded_provider_process(
    command: list[str], *, cwd: Path, env: dict[str, str], timeout_seconds: int
) -> bytes:
    """Capture bounded OpenCode stdout while draining (but not retaining) stderr."""
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            bufsize=0,
            start_new_session=True,
        )
    except OSError as exc:
        raise ProviderPatchError("OpenCode could not be launched; no provider request was started") from exc

    # A cooldown marker means the provider process actually started, not merely
    # that a GITHUB_OUTPUT file happened to exist during local preflight.
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        try:
            with open(output_path, "a", encoding="utf-8") as output:
                output.write("provider_request_started=true\n")
        except OSError as exc:
            _stop_process_group(process)
            raise ProviderPatchError(
                "Could not record provider-start state; OpenCode was stopped",
                provider_request_started=True,
            ) from exc

    stdout_data = bytearray()
    stderr_size = 0
    deadline = time.monotonic() + timeout_seconds
    selector = selectors.DefaultSelector()
    streams = ((process.stdout, "stdout"), (process.stderr, "stderr"))
    try:
        for stream, label in streams:
            if stream is None:
                raise ProviderPatchError("OpenCode output pipe was not created")
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)

        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ProviderPatchError("OpenCode provider invocation timed out; process group stopped without retry")
            ready = selector.select(remaining)
            if not ready:
                continue
            for key, _mask in ready:
                try:
                    chunk = os.read(key.fileobj.fileno(), 8192)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                if key.data == "stdout":
                    if len(stdout_data) + len(chunk) > MAX_STREAM_BYTES:
                        raise ProviderPatchError("OpenCode stdout exceeded the 256 KiB limit; process group stopped")
                    stdout_data.extend(chunk)
                else:
                    stderr_size += len(chunk)
                    if stderr_size > MAX_STDERR_BYTES:
                        raise ProviderPatchError("OpenCode stderr exceeded the 64 KiB limit; process group stopped")

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ProviderPatchError("OpenCode provider invocation timed out; process group stopped without retry")
        try:
            status = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as exc:
            raise ProviderPatchError("OpenCode provider invocation timed out; process group stopped without retry") from exc
    except ProviderPatchError as exc:
        _stop_process_group(process)
        exc.provider_request_started = True
        raise
    except (OSError, ValueError) as exc:
        _stop_process_group(process)
        raise ProviderPatchError(
            "OpenCode output could not be captured safely; process group stopped",
            provider_request_started=True,
        ) from exc
    finally:
        selector.close()
        for stream, _label in streams:
            if stream is not None and not stream.closed:
                stream.close()

    if status != 0:
        raise ProviderPatchError(
            f"OpenCode exited with status {status}; proposal rejected",
            provider_request_started=True,
        )
    return bytes(stdout_data)


def run_provider_patch(
    *,
    repo_root: Path,
    policy_root: Path,
    allowlist_report: Path,
    prompt_file: Path,
    output_proposal: Path,
    expected_task_id: str,
    expected_base_sha: str,
    expected_policy_sha: str,
    model: str,
    timeout_seconds: int = 90,
) -> dict[str, Any]:
    if model not in ALLOWED_MODELS:
        raise ProviderPatchError("Provider model is not in the €0-only allow-list")
    if not SHA_RE.fullmatch(expected_base_sha) or not SHA_RE.fullmatch(expected_policy_sha):
        raise ProviderPatchError("Target and policy SHAs must be exact 40-character lowercase hex values")
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= MAX_TIMEOUT_SECONDS:
        raise ProviderPatchError("Provider timeout must be between 1 and 180 seconds")

    target = repo_root.resolve()
    trusted = policy_root.resolve()
    if output_proposal.is_symlink():
        raise ProviderPatchError("Output proposal path must not be a symlink")
    destination = output_proposal.resolve()
    if destination.exists():
        raise ProviderPatchError("Output proposal path must be new")
    if _inside(destination, target) or _inside(destination, trusted):
        raise ProviderPatchError("Model proposal must be written outside both Git checkouts")

    validate_checkout(target, expected_base_sha)
    validate_checkout(trusted, expected_policy_sha)
    allowed_paths = load_allowlist_report(
        allowlist_report,
        expected_task_id=expected_task_id,
        expected_base_sha=expected_base_sha,
        expected_policy_sha=expected_policy_sha,
    )
    _validate_opencode_config()
    context = _read_prompt(prompt_file)
    prompt = _build_prompt(
        context,
        task_id=expected_task_id,
        target_sha=expected_base_sha,
        policy_sha=expected_policy_sha,
        allowed_paths=allowed_paths,
    )
    if len(prompt.encode("utf-8")) > MAX_PROMPT_BYTES:
        raise ProviderPatchError("Combined provider prompt exceeds the 32 KiB limit")

    env = _provider_environment(model)
    opencode = shutil.which("opencode", path=env.get("PATH"))
    if not opencode:
        raise ProviderPatchError("OpenCode CLI is unavailable; no provider request was started")
    command = [
        opencode, "run", "--format", "json",
        "--model", model,
        "--auto",
        "--dir", str(target),
        prompt,
    ]
    # The start marker is written once, by _run_bounded_provider_process,
    # immediately after Popen succeeds. Missing binaries and preflight errors
    # must never consume the provider cooldown.
    stdout_bytes = _run_bounded_provider_process(
        command,
        cwd=trusted,
        env=env,
        timeout_seconds=timeout_seconds,
    )
    try:
        stdout = stdout_bytes.decode("utf-8", errors="strict")
        proposal_text = parse_event_stream(stdout)
        if len(proposal_text.encode("utf-8")) > MAX_PROPOSAL_BYTES:
            raise ProviderPatchError("Assistant proposal exceeded the 96 KiB limit")
        proposal = json.loads(proposal_text, object_pairs_hook=_unique_object)
        if not isinstance(proposal, dict):
            raise ProviderPatchError("Assistant proposal root must be a JSON object")
        paths = validate_proposal(
            proposal,
            expected_task_id=expected_task_id,
            expected_base_sha=expected_base_sha,
            allowed_paths=allowed_paths,
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".tmp")
        if temporary.exists() or temporary.is_symlink():
            raise ProviderPatchError("Temporary proposal output already exists")
        temporary.write_text(
            json.dumps(proposal, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(destination)
    except ProviderPatchError as exc:
        exc.provider_request_started = True
        raise
    except (UnicodeError, json.JSONDecodeError, ProposalError, OSError) as exc:
        raise ProviderPatchError(
            "Provider response could not be decoded, validated or saved safely",
            provider_request_started=True,
        ) from exc
    return {
        "status": "PROPOSAL_VALIDATED",
        "task_id": expected_task_id,
        "base_sha": expected_base_sha,
        "policy_base_sha": expected_policy_sha,
        "changed_paths": list(paths),
        "summary": proposal["summary"],
        "provider_model": model,
        "provider_tools_exposed": False,
        "github_credentials_forwarded": False,
        "proposal_path": str(destination),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--policy-root", type=Path, required=True)
    parser.add_argument("--allowlist-report", type=Path, required=True)
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--output-proposal", type=Path, required=True)
    parser.add_argument("--expected-task-id", required=True)
    parser.add_argument("--expected-base-sha", required=True)
    parser.add_argument("--expected-policy-sha", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=90)
    args = parser.parse_args()
    try:
        report = run_provider_patch(
            repo_root=args.repo_root,
            policy_root=args.policy_root,
            allowlist_report=args.allowlist_report,
            prompt_file=args.prompt_file,
            output_proposal=args.output_proposal,
            expected_task_id=args.expected_task_id,
            expected_base_sha=args.expected_base_sha,
            expected_policy_sha=args.expected_policy_sha,
            model=args.model,
            timeout_seconds=args.timeout_seconds,
        )
    except (ProviderPatchError, ProposalError) as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
