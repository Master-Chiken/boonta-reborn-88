#!/usr/bin/env python3
"""Fail-closed GitHub MCP transport and read-only repository-access preflight."""

from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from typing import Any


IMAGE = "ghcr.io/github/github-mcp-server:v0.27.0"
OWNER = "Master-Chiken"
REPOSITORY = "boonta-reborn-88"
READ_PATH = "docs/automation/task-ledger-summary.json"
READ_REF = "refs/heads/main"
TIMEOUT_SECONDS = 75


def fail(message: str) -> int:
    print(f"::error::{message}; no model request was sent.", file=sys.stderr)
    return 3


def _read_stdout(process: subprocess.Popen[str], messages: queue.Queue[str | None]) -> None:
    assert process.stdout is not None
    for line in process.stdout:
        messages.put(line)
    messages.put(None)


def _await_response(
    messages: queue.Queue[str | None],
    expected_id: int,
    deadline: float,
    diagnostics: list[str],
) -> dict[str, Any]:
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError
        try:
            line = messages.get(timeout=remaining)
        except queue.Empty as exc:
            raise TimeoutError from exc
        if line is None:
            raise RuntimeError("GitHub MCP closed stdout before returning response " + str(expected_id))
        try:
            candidate = json.loads(line)
        except json.JSONDecodeError:
            diagnostics.append(line.rstrip())
            continue
        if isinstance(candidate, dict) and candidate.get("id") == expected_id:
            return candidate


def _send(process: subprocess.Popen[str], message: dict[str, Any]) -> None:
    if process.stdin is None:
        raise RuntimeError("GitHub MCP stdin pipe is unavailable")
    process.stdin.write(json.dumps(message) + "\n")
    process.stdin.flush()


def _stop_process(process: subprocess.Popen[str]) -> None:
    if process.stdin is not None and not process.stdin.closed:
        try:
            process.stdin.close()
        except OSError:
            pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def main() -> int:
    token = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    allowed_tools = {
        item.strip()
        for item in os.environ.get("GITHUB_TOOLS", "").split(",")
        if item.strip()
    }
    required_tools = {
        item.strip()
        for item in os.environ.get(
            "GITHUB_MCP_REQUIRED_TOOLS", "get_file_contents,push_files"
        ).split(",")
        if item.strip()
    }

    if not token:
        return fail("GitHub MCP token environment is empty")
    if not allowed_tools or "get_file_contents" not in allowed_tools:
        return fail("GitHub MCP allow-list must include get_file_contents")
    if not required_tools or not required_tools.issubset(allowed_tools):
        return fail("GitHub MCP required tools are not a subset of its allow-list")

    if shutil.which("docker") is None:
        return fail("Docker CLI is unavailable for GitHub MCP")
    try:
        docker_info = subprocess.run(
            ["docker", "info"],
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return fail("Docker daemon preflight timed out")
    if docker_info.returncode != 0:
        return fail("Docker daemon is unavailable for GitHub MCP")

    command = [
        "docker",
        "run",
        "-i",
        "--rm",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "-e",
        "GITHUB_TOOLS",
        IMAGE,
    ]
    environment = os.environ.copy()
    messages: queue.Queue[str | None] = queue.Queue()
    diagnostics: list[str] = []
    process: subprocess.Popen[str] | None = None
    reader: threading.Thread | None = None
    deadline = time.monotonic() + TIMEOUT_SECONDS

    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            bufsize=1,
            env=environment,
        )
        reader = threading.Thread(
            target=_read_stdout,
            args=(process, messages),
            name="github-mcp-stdout",
            daemon=True,
        )
        reader.start()

        _send(
            process,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "boonta-mcp-preflight", "version": "1.0.0"},
                },
            },
        )
        initialize_response = _await_response(messages, 1, deadline, diagnostics)
        if "error" in initialize_response or not isinstance(initialize_response.get("result"), dict):
            raise RuntimeError("GitHub MCP initialize handshake failed")

        _send(
            process,
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        )
        _send(process, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        list_response = _await_response(messages, 2, deadline, diagnostics)
        if "error" in list_response:
            raise RuntimeError("GitHub MCP tools/list request failed")

        list_result = list_response.get("result")
        tools = list_result.get("tools", []) if isinstance(list_result, dict) else []
        if not isinstance(tools, list):
            raise RuntimeError("GitHub MCP tools/list response has an invalid tool catalog")
        names = {
            item.get("name")
            for item in tools
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        }
        missing = required_tools - names
        if missing:
            raise RuntimeError(
                "GitHub MCP tool catalog is missing required tools: "
                + ", ".join(sorted(missing))
            )

        read_tool = next(
            (
                item
                for item in tools
                if isinstance(item, dict) and item.get("name") == "get_file_contents"
            ),
            None,
        )
        schema = read_tool.get("inputSchema", {}) if isinstance(read_tool, dict) else {}
        properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
        required_fields = schema.get("required", []) if isinstance(schema, dict) else []
        schema_required = set(required_fields) if isinstance(required_fields, list) else set()
        if (
            not isinstance(properties, dict)
            or not {"owner", "repo"}.issubset(schema_required)
            or not {"path", "ref"}.issubset(properties)
        ):
            raise RuntimeError("GitHub MCP get_file_contents schema differs from the reviewed probe")

        _send(
            process,
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "get_file_contents",
                    "arguments": {
                        "owner": OWNER,
                        "repo": REPOSITORY,
                        "path": READ_PATH,
                        "ref": READ_REF,
                    },
                },
            },
        )
        read_response = _await_response(messages, 3, deadline, diagnostics)
        if "error" in read_response:
            raise RuntimeError("GitHub MCP read-only get_file_contents call failed")
        read_result = read_response.get("result")
        read_content = read_result.get("content", []) if isinstance(read_result, dict) else []
        if not isinstance(read_content, list):
            raise RuntimeError("GitHub MCP read-only call returned an invalid content envelope")
        read_text = "\n".join(
            item.get("text", "")
            for item in read_content
            if isinstance(item, dict)
            and item.get("type") == "text"
            and isinstance(item.get("text"), str)
        )
        if (
            not isinstance(read_result, dict)
            or read_result.get("isError") is True
            or '"schema_version"' not in read_text
        ):
            raise RuntimeError("GitHub MCP read did not return the expected task-ledger summary")

        # Only close stdin after all expected responses have been received. The
        # pinned Go SDK reports "server is closing: EOF" with exit 1 on normal
        # stdio EOF teardown; that shutdown result is safe only after id 1, 2
        # and 3 have all been received and validated above.
        assert process.stdin is not None
        process.stdin.close()
        exit_code = process.wait(timeout=10)
        if reader is not None:
            reader.join(timeout=5)
        while not messages.empty():
            line = messages.get_nowait()
            if line is not None:
                diagnostics.append(line.rstrip())
        safe_diagnostics = [line.replace(token, "[REDACTED]") for line in diagnostics]
        eof_shutdown = any("server is closing: EOF" in line for line in safe_diagnostics)
        if exit_code != 0 and not (exit_code == 1 and eof_shutdown):
            detail = " | ".join(safe_diagnostics[-8:])
            raise RuntimeError(
                f"GitHub MCP process exited {exit_code} after returning the expected protocol results"
                + (": " + detail if detail else "")
            )

        print("GitHub MCP tools/list returned: " + ", ".join(sorted(names)))
        print(
            "GitHub MCP token-backed read-only get_file_contents call passed for "
            "the canonical task-ledger summary."
        )
        print("GitHub MCP direct protocol preflight passed; required tools are present and the read path works.")
        return 0
    except subprocess.TimeoutExpired:
        return fail("GitHub MCP read-only tools preflight timed out")
    except TimeoutError:
        return fail("GitHub MCP read-only tools preflight timed out")
    except (OSError, RuntimeError, ValueError) as exc:
        message = str(exc).replace(token, "[REDACTED]")
        safe_diagnostics = [line.replace(token, "[REDACTED]") for line in diagnostics]
        detail = " | ".join(safe_diagnostics[-8:])
        return fail(message + (": " + detail if detail else ""))
    finally:
        if process is not None and process.poll() is None:
            _stop_process(process)


if __name__ == "__main__":
    raise SystemExit(main())
