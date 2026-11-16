#!/usr/bin/env python3
"""Offline tests for the exact context file required by the proposal-only MCP."""
from __future__ import annotations

import json
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from write_autonomous_provider_context import ProviderContextError, write_provider_context


class ProviderContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="boonta-provider-context-")
        self.workspace = Path(self.temp.name)
        self.context = "Verified bounded task context from the workflow-owned builder."
        self.values = {
            "task_id": "GC-RIVAL-ROUTE-PROGRESSION",
            "task_title": "Rival route progress",
            "task_description": "Implement bounded deterministic rival route progress.",
            "target_branch": "dev",
            "verified_context": self.context,
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_writes_exact_mcp_context_contract(self):
        result = write_provider_context(self.workspace, **self.values)
        path = self.workspace / ".gemini/context.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "READY")
        self.assertEqual(payload, {
            "task_id": self.values["task_id"],
            "task_title": self.values["task_title"],
            "task_description": self.values["task_description"],
            "task_target_branch": self.values["target_branch"],
            "verified_context": self.context,
        })
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_refuses_to_overwrite_existing_context(self):
        write_provider_context(self.workspace, **self.values)
        with self.assertRaisesRegex(ProviderContextError, "already exists"):
            write_provider_context(self.workspace, **self.values)

    def test_refuses_symlinked_context_directory(self):
        target = self.workspace / "elsewhere"
        target.mkdir()
        (self.workspace / ".gemini").symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(ProviderContextError, "symlink"):
            write_provider_context(self.workspace, **self.values)

    def test_refuses_wrong_task_branch_or_oversized_context(self):
        with self.assertRaisesRegex(ProviderContextError, "Target branch"):
            write_provider_context(self.workspace, **{**self.values, "target_branch": "feature"})
        with self.assertRaisesRegex(ProviderContextError, "12 KiB"):
            write_provider_context(self.workspace, **{
                **self.values,
                "verified_context": "x" * (12 * 1024 + 1),
            })


if __name__ == "__main__":
    unittest.main()
