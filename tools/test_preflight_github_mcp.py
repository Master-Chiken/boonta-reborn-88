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


def response_lines(*, include_push: bool = True, schema_ok: bool = True, read_error: bool = False, marker: bool = True) -> str:
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
    list_message = {"jsonrpc": "2.0", "id": 2, "result": {"tools": tools}}
    if read_error:
        call_message = {"jsonrpc": "2.0", "id": 3, "error": {"code": -32000, "message": "read denied"}}
    else:
        text = '{"schema_version": 2}' if marker else '{"wrong_schema": 2}'
        call_message = {
            "jsonrpc": "2.0",
            "id": 3,
            "result": {"content": [{"type": "text", "text": text}]},
        }
    return "\n".join(json.dumps(item) for item in (list_message, call_message)) + "\n"


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

    def run_probe(self, stdout: str | None = None, *, second_result: object | None = None):
        success = subprocess.CompletedProcess(["docker", "info"], 0, stdout="", stderr="")
        result = second_result or subprocess.CompletedProcess(
            ["docker", "run"], 0, stdout=stdout or response_lines(), stderr=""
        )
        docker = patch.object(probe.shutil, "which", return_value="/usr/bin/docker")
        runner_patch = patch.object(probe.subprocess, "run", side_effect=[success, result])
        docker.start()
        runner = runner_patch.start()
        self.addCleanup(docker.stop)
        self.addCleanup(runner_patch.stop)
        return runner

    def invoke(self, **kwargs):
        runner = self.run_probe(**kwargs)
        output = io.StringIO()
        errors = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = probe.main()
        return code, output.getvalue(), errors.getvalue(), runner

    def test_success_calls_only_read_only_repository_tool(self) -> None:
        code, output, errors, runner = self.invoke()
        self.assertEqual(code, 0, errors)
        self.assertIn("read-only get_file_contents call passed", output)
        self.assertEqual(len(runner.call_args_list), 2)
        payload = runner.call_args_list[1].kwargs["input"]
        requests = [json.loads(line) for line in payload.splitlines()]
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

    def test_mcp_timeout_fails_closed(self) -> None:
        timeout = subprocess.TimeoutExpired(["docker", "run"], probe.TIMEOUT_SECONDS)
        code, _, errors, _ = self.invoke(second_result=timeout)
        self.assertEqual(code, 3)
        self.assertIn("preflight timed out", errors)

    def test_missing_token_fails_before_docker(self) -> None:
        os.environ.pop("GITHUB_PERSONAL_ACCESS_TOKEN")
        with patch.object(probe.shutil, "which") as which, contextlib.redirect_stderr(io.StringIO()):
            code = probe.main()
        self.assertEqual(code, 3)
        which.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
