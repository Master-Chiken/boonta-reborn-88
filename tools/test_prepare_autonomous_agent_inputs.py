#!/usr/bin/env python3
"""Offline tests for trusted-main/task-target autonomous agent input preparation."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from prepare_autonomous_agent_inputs import AgentInputError, prepare_agent_inputs

TASK_ID = "GC-RIVAL-ROUTE-PROGRESSION"
APPROVAL = "https://github.com/Master-Chiken/boonta-reborn-88/pull/400"
SOURCE_PATH = "src/main.c"


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, stdin=subprocess.DEVNULL,
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class AgentInputFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="boonta-agent-inputs-")
        self.parent = Path(self.temp.name).resolve()
        self.source = self.parent / "dev-source"
        self.policy = self.parent / "trusted-main"
        self.output = self.parent / "allowlist.json"
        self.source.mkdir()
        self.policy.mkdir()
        for root, name, email in (
            (self.source, "Boonta Target", "target@example.invalid"),
            (self.policy, "Boonta Main", "main@example.invalid"),
        ):
            git(root, "init", "-q")
            git(root, "config", "user.name", name)
            git(root, "config", "user.email", email)

        target_file = self.source / SOURCE_PATH
        target_file.parent.mkdir(parents=True)
        target_file.write_text("int main(void) {\n  return 1;\n}\n", encoding="utf-8")
        git(self.source, "add", "src")
        git(self.source, "commit", "-qm", "dev target source")
        self.base_sha = git(self.source, "rev-parse", "HEAD")

        docs = self.policy / "docs/automation"
        docs.mkdir(parents=True)
        self.summary = {
            "schema_version": 2,
            "source": "docs/automation/task-ledger.json",
            "completed_task_ids": ["GC-RACE-PROGRESSION"],
            "tasks": [{
                "task_id": TASK_ID,
                "title": "Rival route progress",
                "status": "queued",
                "owner_approved": True,
                "target_branch": "dev",
                "depends_on": ["GC-RACE-PROGRESSION"],
                "read_paths": [SOURCE_PATH],
                "read_ranges": [{"path": SOURCE_PATH, "start_line": 1, "end_line": 3}],
            }],
        }
        self.policy_doc = {
            "schema_version": 1,
            "policy": {
                "owner_review_required": True,
                "path_mode": "exact",
                "max_paths_per_task": 20,
            },
            "tasks": [{
                "task_id": TASK_ID,
                "purpose": "Owner-approved route-progress change",
                "approval_ref": APPROVAL,
                "allowed_paths": [SOURCE_PATH],
            }],
        }
        (docs / "task-ledger-summary.json").write_text(json.dumps(self.summary), encoding="utf-8")
        (docs / "patch-path-allowlist.json").write_text(json.dumps(self.policy_doc), encoding="utf-8")
        (docs / "task-ledger.json").write_text(json.dumps({"schema_version": 1, "tasks": []}), encoding="utf-8")
        git(self.policy, "add", "docs/automation")
        git(self.policy, "commit", "-qm", "trusted main task and path policy")
        self.policy_sha = git(self.policy, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def prepare(self, **overrides):
        return prepare_agent_inputs(
            self.source,
            self.policy,
            expected_base_sha=overrides.pop("expected_base_sha", self.base_sha),
            expected_policy_sha=overrides.pop("expected_policy_sha", self.policy_sha),
            task_id=overrides.pop("task_id", TASK_ID),
            allowlist_output=overrides.pop("allowlist_output", self.output),
            **overrides,
        )


class AgentInputTests(AgentInputFixture):
    def test_ready_inputs_bind_exact_source_policy_and_task(self):
        report = self.prepare()
        self.assertEqual(report["task_id"], TASK_ID)
        self.assertEqual(report["target_branch"], "dev")
        self.assertEqual(report["base_sha"], self.base_sha)
        self.assertEqual(report["policy_sha"], self.policy_sha)
        self.assertEqual(report["read_paths"], [SOURCE_PATH])
        self.assertEqual(report["read_ranges"], [{
            "path": SOURCE_PATH, "start_line": 1, "end_line": 3,
        }])
        self.assertEqual(report["allowed_paths"], [SOURCE_PATH])
        self.assertEqual(report["approval_ref"], APPROVAL)
        self.assertFalse(report["model_has_github_write_tools"])
        self.assertEqual(json.loads(Path(report["allowlist_report"]).read_text())["allowed_paths"], [SOURCE_PATH])
        self.assertEqual(git(self.source, "status", "--porcelain"), "")
        self.assertEqual(git(self.policy, "status", "--porcelain"), "")

    def test_stale_target_sha_is_rejected(self):
        with self.assertRaisesRegex(AgentInputError, "target base SHA"):
            self.prepare(expected_base_sha="0" * 40)

    def test_stale_trusted_policy_sha_is_rejected(self):
        with self.assertRaisesRegex(AgentInputError, "policy SHA"):
            self.prepare(expected_policy_sha="0" * 40)

    def test_selected_task_absent_from_trusted_main_is_rejected(self):
        with self.assertRaisesRegex(AgentInputError, "exactly once"):
            self.prepare(task_id="GC-NOT-IN-LEDGER")

    def test_incomplete_task_dependency_does_not_grant_write_paths(self):
        self.summary["completed_task_ids"] = []
        summary_path = self.policy / "docs/automation/task-ledger-summary.json"
        summary_path.write_text(json.dumps(self.summary), encoding="utf-8")
        git(self.policy, "add", "docs/automation/task-ledger-summary.json")
        git(self.policy, "commit", "-qm", "remove completed prerequisite")
        self.policy_sha = git(self.policy, "rev-parse", "HEAD")
        with self.assertRaisesRegex(AgentInputError, "not READY|dependency"):
            self.prepare(expected_policy_sha=self.policy_sha)

    def test_missing_exact_line_ranges_are_rejected(self):
        self.summary["tasks"][0]["read_ranges"] = []
        summary_path = self.policy / "docs/automation/task-ledger-summary.json"
        summary_path.write_text(json.dumps(self.summary), encoding="utf-8")
        git(self.policy, "add", "docs/automation/task-ledger-summary.json")
        git(self.policy, "commit", "-qm", "remove source ranges")
        self.policy_sha = git(self.policy, "rev-parse", "HEAD")
        with self.assertRaisesRegex(AgentInputError, "1-10 exact read_ranges"):
            self.prepare(expected_policy_sha=self.policy_sha)

    def test_range_cannot_escape_exact_read_paths(self):
        self.summary["tasks"][0]["read_ranges"][0]["path"] = "src/other.c"
        summary_path = self.policy / "docs/automation/task-ledger-summary.json"
        summary_path.write_text(json.dumps(self.summary), encoding="utf-8")
        git(self.policy, "add", "docs/automation/task-ledger-summary.json")
        git(self.policy, "commit", "-qm", "widen source range")
        self.policy_sha = git(self.policy, "rev-parse", "HEAD")
        with self.assertRaisesRegex(AgentInputError, "exact bounded source contract"):
            self.prepare(expected_policy_sha=self.policy_sha)

    def test_range_budget_is_bounded(self):
        self.summary["tasks"][0]["read_ranges"] = [
            {"path": SOURCE_PATH, "start_line": i, "end_line": i + 79}
            for i in (1, 81, 161)
        ]
        summary_path = self.policy / "docs/automation/task-ledger-summary.json"
        summary_path.write_text(json.dumps(self.summary), encoding="utf-8")
        git(self.policy, "add", "docs/automation/task-ledger-summary.json")
        git(self.policy, "commit", "-qm", "exceed range budget")
        self.policy_sha = git(self.policy, "rev-parse", "HEAD")
        with self.assertRaisesRegex(AgentInputError, "240-line aggregate cap"):
            self.prepare(expected_policy_sha=self.policy_sha)

    def test_dirty_source_checkout_is_rejected(self):
        (self.source / "dirty.txt").write_text("not allowed", encoding="utf-8")
        with self.assertRaisesRegex(AgentInputError, "source checkout must be clean"):
            self.prepare()

    def test_dirty_policy_checkout_is_rejected(self):
        (self.policy / "dirty.txt").write_text("not allowed", encoding="utf-8")
        with self.assertRaisesRegex(AgentInputError, "policy checkout must be clean"):
            self.prepare()

    def test_duplicate_output_is_not_overwritten(self):
        self.output.write_text("keep me", encoding="utf-8")
        with self.assertRaisesRegex(AgentInputError, "must be a new"):
            self.prepare()
        self.assertEqual(self.output.read_text(encoding="utf-8"), "keep me")

    def test_write_paths_must_exist_on_the_target_branch(self):
        self.policy_doc["tasks"][0]["allowed_paths"] = ["src/not-tracked.c"]
        policy_path = self.policy / "docs/automation/patch-path-allowlist.json"
        policy_path.write_text(json.dumps(self.policy_doc), encoding="utf-8")
        git(self.policy, "add", "docs/automation/patch-path-allowlist.json")
        git(self.policy, "commit", "-qm", "approve unavailable target path")
        self.policy_sha = git(self.policy, "rev-parse", "HEAD")
        with self.assertRaisesRegex(AgentInputError, "not READY"):
            self.prepare(expected_policy_sha=self.policy_sha)


if __name__ == "__main__":
    unittest.main(verbosity=2)
