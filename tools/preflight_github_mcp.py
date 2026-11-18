#!/usr/bin/env python3
"""Fail-closed, read-only GitHub MCP transport and repository-access preflight."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
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


def _jsonrpc_responses(stdout: str) -> dict[int, dict[str, Any]]:
    responses: dict[int, dict[str, Any]] = {}
    for line in stdout.splitlines():
        try:
            candidate = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and candidate.get("id") in (2, 3):
            responses[int(candidate["id"])] = candidate
    return responses


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
    messages = [
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
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
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
    ]
    payload = "".join(json.dumps(item) + "\n" for item in messages)
    environment = os.environ.copy()
    try:
        result = subprocess.run(
            command,
            input=payload,
            text=True,
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
            env=environment,
        )
    except subprocess.TimeoutExpired:
        return fail("GitHub MCP read-only tools preflight timed out")
    responses = _jsonrpc_responses(result.stdout)
    if result.returncode != 0:
        diagnostic = "\n".join(str(result.stderr or "").splitlines()[-20:])
        diagnostic = diagnostic.replace(token, "[REDACTED]") if token else diagnostic
        response_ids = ",".join(str(item) for item in sorted(responses)) or "none"
        detail = f" (exit code {result.returncode}; JSON-RPC response ids: {response_ids})"
        if diagnostic:
            detail += ": " + diagnostic
        return fail("GitHub MCP container failed during direct protocol preflight" + detail)

    responses = _jsonrpc_responses(result.stdout)
    list_response = responses.get(2)
    read_response = responses.get(3)
    if not isinstance(list_response, dict) or "error" in list_response:
        return fail("GitHub MCP did not return a valid tools/list response")

    list_result = list_response.get("result")
    tools = list_result.get("tools", []) if isinstance(list_result, dict) else []
    if not isinstance(tools, list):
        return fail("GitHub MCP tools/list response has an invalid tool catalog")
    names = {
        item.get("name")
        for item in tools
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    missing = required_tools - names
    if missing:
        return fail(
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
        return fail("GitHub MCP get_file_contents schema differs from the reviewed probe")

    if not isinstance(read_response, dict) or "error" in read_response:
        return fail("GitHub MCP read-only get_file_contents call failed")
    read_result = read_response.get("result")
    read_content = read_result.get("content", []) if isinstance(read_result, dict) else []
    if not isinstance(read_content, list):
        return fail("GitHub MCP read-only call returned an invalid content envelope")
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
        return fail("GitHub MCP read did not return the expected task-ledger summary")

    print("GitHub MCP tools/list returned: " + ", ".join(sorted(names)))
    print(
        "GitHub MCP token-backed read-only get_file_contents call passed for "
        "the canonical task-ledger summary."
    )
    print("GitHub MCP direct protocol preflight passed; required tools are present and the read path works.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
