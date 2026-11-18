#!/usr/bin/env python3
"""Offline tests for the fail-closed GitHub MCP preflight."""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import unittest
from unittest.mock import patch

import preflight_github_mcp as probe


def response_lines(
    *,
    include_push: bool = True,
    schema_ok: bool = True,
    read_error: bool = False,
    marker: bool = True,
    include_initialize: bool = True,
    shutdown_error: bool = False,
) -> str:
    properties = {"owner": {}, "repo": {}, "path": {}, "ref": {}} if schema_ok else {"owner": {}, "repo": {}}
    required = ["owner", "repo"] if schema_ok else ["owner"]
    tools = [
        {
            "name": "get_file_contents",
            "inputSchema": {"type": "object", "properties": properties, "required": required},
        }
    ]
    if include_push:
        tools.append({"name": "push_files", "inputSchema": {"type": "object"}})
    messages = []
    if include_initialize:
        messages.append(
            {"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05"}}
        )
    messages.append({"jsonrpc": "2.0", "id": 2, "result": {"tools": tools}})
    if read_error:
        messages.append(
            {"jsonrpc": "2.0", "id": 3, "error": {"code": -32000, "message": "read denied"}}
        )
    else:
        text = '{"schema_version": 2}' if marker else '{"wrong_schema": 2}'
        messages.append(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "result": {"content": [{"type": "text", "text": text}]},
            }
        )
    rendered = "\n".join(json.dumps(item) for item in messages) + "\n"
    if shutdown_error:
        rendered += "error running server: server is closing: EOF\n"
    return rendered


class FakeStdin:
    def __init__(self) -> None:
        self.data = ""
        self.closed = False

    def write(self, value: str) -> int:
        if self.closed:
            raise ValueError("stdin is closed")
        self.data += value
        return len(value)

    def flush(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True


class FakeProcess:
    def __init__(self, stdout: str, exit_code: int = 0) -> None:
        self.stdin = FakeStdin()
        self.stdout = io.StringIO(stdout)
        self.exit_code = exit_code
        self.returncode = None

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        self.returncode = self.exit_code
        return self.exit_code

    def terminate(self):
        self.returncode = -15

    def kill(self):
        self.returncode = -9


class GitHubMcpPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.environment = patch.dict(
            os.environ,
            {
                "GITHUB_PERSONAL_ACCESS_TOKEN": "unit-test-token",
                "GITHUB_TOOLS": "get_file_contents,push_files",
                "GITHUB_MCP_REQUIRED_TOOLS": "get_file_contents,push_files",
            },
            clear=True,
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def run_probe(
        self,
        stdout: str | None = None,
        *,
        exit_code: int = 0,
    ):
        docker_info = subprocess.CompletedProcess(["docker", "info"], 0, stdout="", stderr="")
        process = FakeProcess(stdout if stdout is not None else response_lines(), exit_code)
        docker = patch.object(probe.shutil, "which", return_value="/usr/bin/docker")
        runner = patch.object(probe.subprocess, "run", return_value=docker_info)
        popen = patch.object(probe.subprocess, "Popen", return_value=process)
        docker.start()
        runner.start()
        popen.start()
        self.addCleanup(docker.stop)
        self.addCleanup(runner.stop)
        self.addCleanup(popen.stop)
        return process

    def invoke(self, **kwargs):
        process = self.run_probe(**kwargs)
        output = io.StringIO()
        errors = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = probe.main()
        return code, output.getvalue(), errors.getvalue(), process

    def test_success_keeps_stdio_open_and_calls_only_read_only_repository_tool(self) -> None:
        code, output, errors, process = self.invoke()
        self.assertEqual(code, 0, errors)
        self.assertIn("read-only get_file_contents call passed", output)
        self.assertTrue(process.stdin.closed)
        requests = [json.loads(line) for line in process.stdin.data.splitlines()]
        methods = [item.get("method") for item in requests]
        self.assertEqual(
            methods,
            ["initialize", "notifications/initialized", "tools/list", "tools/call"],
        )
        tool_calls = [item for item in requests if item.get("method") == "tools/call"]
        self.assertEqual(len(tool_calls), 1)
        self.assertEqual(tool_calls[0]["params"]["name"], "get_file_contents")
        self.assertEqual(
            tool_calls[0]["params"]["arguments"]["path"],
            "docs/automation/task-ledger-summary.json",
        )

    def test_missing_required_tool_fails_closed(self) -> None:
        code, _, errors, _ = self.invoke(stdout=response_lines(include_push=False))
        self.assertEqual(code, 3)
        self.assertIn("missing required tools", errors)

    def test_unexpected_input_schema_fails_closed(self) -> None:
        code, _, errors, _ = self.invoke(stdout=response_lines(schema_ok=False))
        self.assertEqual(code, 3)
        self.assertIn("schema differs", errors)

    def test_mcp_tool_error_fails_closed(self) -> None:
        code, _, errors, _ = self.invoke(stdout=response_lines(read_error=True))
        self.assertEqual(code, 3)
        self.assertIn("read-only get_file_contents call failed", errors)

    def test_unexpected_read_content_fails_closed(self) -> None:
        code, _, errors, _ = self.invoke(stdout=response_lines(marker=False))
        self.assertEqual(code, 3)
        self.assertIn("did not return the expected task-ledger summary", errors)

    def test_mcp_closing_before_tools_list_fails_closed(self) -> None:
        code, _, errors, _ = self.invoke(
            stdout=response_lines(include_initialize=True).splitlines()[0] + "\n"
        )
        self.assertEqual(code, 3)
        self.assertIn("closed stdout before returning response 2", errors)

    def test_expected_eof_shutdown_after_valid_responses_is_accepted(self) -> None:
        code, output, errors, _ = self.invoke(
            stdout=response_lines(shutdown_error=True),
            exit_code=1,
        )
        self.assertEqual(code, 0, errors)
        self.assertIn("read-only get_file_contents call passed", output)

    def test_unexpected_container_exit_fails_closed_and_redacts_token(self) -> None:
        code, _, errors, _ = self.invoke(
            stdout=response_lines() + "startup failed with unit-test-token\n",
            exit_code=2,
        )
        self.assertEqual(code, 3)
        self.assertIn("[REDACTED]", errors)
        self.assertNotIn("unit-test-token", errors)

    def test_missing_token_fails_before_docker(self) -> None:
        os.environ.pop("GITHUB_PERSONAL_ACCESS_TOKEN")
        with patch.object(probe.shutil, "which") as which, contextlib.redirect_stderr(io.StringIO()):
            code = probe.main()
        self.assertEqual(code, 3)
        which.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
