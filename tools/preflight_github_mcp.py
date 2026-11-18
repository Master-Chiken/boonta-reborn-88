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
APPROVED_TOOL_MODES = {
    frozenset({"get_file_contents", "push_files"}),
    frozenset({"get_file_contents", "create_branch", "push_files", "create_pull_request"}),
}


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


def _safe_error_detail(value: Any, token: str, limit: int = 400) -> str:
    """Return a bounded, single-line MCP error detail with the active token redacted."""
    if isinstance(value, list):
        parts = [
            item.get("text", "")
            for item in value
            if isinstance(item, dict)
            and item.get("type") == "text"
            and isinstance(item.get("text"), str)
        ]
        detail = " | ".join(parts)
    elif isinstance(value, str):
        detail = value
    else:
        detail = json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)
    detail = detail.replace(token, "[REDACTED]") if token else detail
    return " ".join(detail.split())[:limit]


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


TOOL_SCHEMA_CONTRACTS: dict[str, dict[str, Any]] = {
    "get_file_contents": {
        "required": {"owner", "repo"},
        "properties": {"owner": "string", "repo": "string", "path": "string", "ref": "string"},
    },
    "create_branch": {
        "required": {"owner", "repo", "branch"},
        "properties": {"owner": "string", "repo": "string", "branch": "string"},
    },
    "push_files": {
        "required": {"owner", "repo", "branch", "files", "message"},
        "properties": {
            "owner": "string",
            "repo": "string",
            "branch": "string",
            "files": "array",
            "message": "string",
        },
    },
    "create_pull_request": {
        "required": {"owner", "repo", "title", "head", "base"},
        "properties": {
            "owner": "string",
            "repo": "string",
            "title": "string",
            "head": "string",
            "base": "string",
        },
    },
}


def _validate_tool_schema(name: str, tool: dict[str, Any]) -> None:
    contract = TOOL_SCHEMA_CONTRACTS.get(name)
    if contract is None:
        return
    schema = tool.get("inputSchema")
    if not isinstance(schema, dict) or schema.get("type") != "object":
        raise RuntimeError(f"GitHub MCP {name} schema must be an object")
    properties = schema.get("properties")
    required_fields = schema.get("required")
    if not isinstance(properties, dict) or not isinstance(required_fields, list):
        raise RuntimeError(f"GitHub MCP {name} schema is missing properties or required fields")
    missing = contract["required"] - set(required_fields)
    if missing:
        raise RuntimeError(
            f"GitHub MCP {name} schema is missing required fields: "
            + ", ".join(sorted(missing))
        )
    for field, expected_type in contract["properties"].items():
        field_schema = properties.get(field)
        if not isinstance(field_schema, dict) or field_schema.get("type") != expected_type:
            raise RuntimeError(
                f"GitHub MCP {name} schema field {field!r} must have type {expected_type}"
            )
    if name == "push_files":
        files_schema = properties["files"]
        items_schema = files_schema.get("items")
        if not isinstance(items_schema, dict) or items_schema.get("type") != "object":
            raise RuntimeError("GitHub MCP push_files files items schema must be an object")
        item_properties = items_schema.get("properties")
        item_required = items_schema.get("required")
        if not isinstance(item_properties, dict) or not isinstance(item_required, list):
            raise RuntimeError("GitHub MCP push_files file items schema is incomplete")
        missing_item_fields = {"path", "content"} - set(item_required)
        if missing_item_fields:
            raise RuntimeError(
                "GitHub MCP push_files file items schema is missing required fields: "
                + ", ".join(sorted(missing_item_fields))
            )
        for field in ("path", "content"):
            field_schema = item_properties.get(field)
            if not isinstance(field_schema, dict) or field_schema.get("type") != "string":
                raise RuntimeError(
                    f"GitHub MCP push_files file item field {field!r} must have type string"
                )


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
    if frozenset(allowed_tools) not in APPROVED_TOOL_MODES:
        return fail("GitHub MCP allow-list does not match a reviewed execution mode")
    if not required_tools or required_tools != allowed_tools:
        return fail("GitHub MCP required tools must exactly match the configured allow-list")

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
        unexpected = names - allowed_tools
        if unexpected:
            raise RuntimeError(
                "GitHub MCP tool catalog includes tools outside configured allow-list: "
                + ", ".join(sorted(unexpected))
            )

        tool_by_name = {
            item["name"]: item
            for item in tools
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        }
        for tool_name in sorted(required_tools):
            _validate_tool_schema(tool_name, tool_by_name[tool_name])

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
            detail = _safe_error_detail(read_response.get("error"), token)
            raise RuntimeError(
                "GitHub MCP read-only get_file_contents call failed"
                + (": " + detail if detail else "")
            )
        read_result = read_response.get("result")
        read_content = read_result.get("content", []) if isinstance(read_result, dict) else []
        if not isinstance(read_content, list):
            raise RuntimeError("GitHub MCP read-only call returned an invalid content envelope")
        text_parts: list[str] = []
        resource_text_parts: list[str] = []
        json_resource_parts: list[str] = []
        for item in read_content:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "text" and isinstance(item.get("text"), str):
                text_parts.append(item["text"])
            elif item.get("type") == "resource":
                resource = item.get("resource")
                if isinstance(resource, dict) and isinstance(resource.get("text"), str):
                    resource_text_parts.append(resource["text"])
                    mime_type = resource.get("mimeType", "")
                    if mime_type == "application/json" or (
                        isinstance(mime_type, str) and mime_type.endswith("+json")
                    ):
                        json_resource_parts.append(resource["text"])
        if not isinstance(read_result, dict):
            raise RuntimeError("GitHub MCP read-only call returned an invalid result envelope")
        if read_result.get("isError") is True:
            detail = _safe_error_detail(read_content, token)
            raise RuntimeError(
                "GitHub MCP get_file_contents tool returned isError"
                + (": " + detail if detail else "")
            )
        # Prefer the actual JSON resource over any informational text emitted
        # alongside it. Keep the legacy text-only response path for compatibility.
        candidate_parts = json_resource_parts or resource_text_parts or text_parts
        read_text = "\n".join(candidate_parts)
        try:
            ledger_summary = json.loads(read_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("GitHub MCP read did not return valid task-ledger JSON") from exc
        if not isinstance(ledger_summary, dict) or ledger_summary.get("schema_version") != 2:
            raise RuntimeError("GitHub MCP read did not return task-ledger schema_version 2")

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
