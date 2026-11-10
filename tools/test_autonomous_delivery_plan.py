#!/usr/bin/env python3
"""Offline tests for deterministic delivery planning."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from build_autonomous_delivery_plan import (
    DeliveryPlanError,
    build_delivery_plan,
)
from verify_autonomous_patch import MANDATORY_TEST_IDS

TASK_ID = "AUTOMATION-DELIVERY-FIXTURE"
APPROVAL = "https://github.com/Master-Chiken/boonta-reborn-88/pull/999"
SOURCE_PATH = "src/main.c"


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, stdin=subprocess.DEVNULL,
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class DeliveryPlanFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="boonta-delivery-plan-")
        self.parent = Path(self.temp.name).resolve()
        self.root = self.parent / "repo"
        self.root.mkdir()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Boonta Test")
        git(self.root, "config", "user.email", "boonta-test@example.invalid")

        source = self.root / SOURCE_PATH
        source.parent.mkdir(parents=True)
        source.write_text("int boonta(void) { return 1; }\n", encoding="utf-8")
        docs = self.root / "docs/automation"
        docs.mkdir(parents=True)
        self.ledger_path = docs / "task-ledger-summary.json"
        self.ledger = {
            "schema_version": 2,
            "source": "docs/automation/task-ledger.json",
            "tasks": [{
                "task_id": TASK_ID,
                "title": "Offline delivery fixture",
                "status": "active",
                "target_branch": "main",
            }],
        }
        self.ledger_path.write_text(json.dumps(self.ledger), encoding="utf-8")
        git(self.root, "add", SOURCE_PATH, "docs/automation/task-ledger-summary.json")
        git(self.root, "commit", "-qm", "delivery planner fixture base")
        self.base_sha = git(self.root, "rev-parse", "HEAD")

        self.allowlist_path = self.parent / "allowlist.json"
        self.verified_path = self.parent / "verified.json"
        self.write_allowlist()
        self.write_verified()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_allowlist(self, *, status="READY", task_id=TASK_ID, base_sha=None, paths=None):
        report = {
            "status": status,
            "task_id": task_id,
            "base_sha": base_sha or self.base_sha,
            "approval_ref": APPROVAL if status == "READY" else "",
            "purpose": "Synthetic exact-path grant",
            "allowed_paths": [SOURCE_PATH] if paths is None and status == "READY" else (paths or []),
        }
        self.allowlist_path.write_text(json.dumps(report), encoding="utf-8")

    def write_verified(self, **overrides):
        results = [
            {
                "test_id": test_id,
                "status": "PASSED",
                "exit_code": 0,
                "duration_seconds": 0.1,
                "stdout": "ok\n",
                "stderr": "",
            }
            for test_id in MANDATORY_TEST_IDS
        ]
        report = {
            "status": "VERIFIED",
            "task_id": TASK_ID,
            "base_sha": self.base_sha,
            "summary": "Update an offline fixture implementation",
            "changed_paths": [SOURCE_PATH],
            "requested_test_ids": [MANDATORY_TEST_IDS[0]],
            "executed_test_ids": list(MANDATORY_TEST_IDS),
            "test_report": {
                "status": "PASSED",
                "results": results,
                "stopped_after_first_failure": False,
            },
            "isolated_worktree": True,
            "source_checkout_modified": False,
            "commit_created": False,
            "branch_created": False,
            "network_accessed": False,
        }
        report.update(overrides)
        self.verified_path.write_text(json.dumps(report), encoding="utf-8")

    def plan(self):
        return build_delivery_plan(
            self.root,
            verified_report_path=self.verified_path,
            allowlist_report_path=self.allowlist_path,
            expected_task_id=TASK_ID,
            expected_base_sha=self.base_sha,
        )

    def assert_source_clean(self):
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), self.base_sha)
        self.assertEqual(git(self.root, "status", "--porcelain"), "")


class DeterministicDeliveryPlanTests(DeliveryPlanFixture):
    def test_valid_verified_report_produces_deterministic_plan(self):
        first = self.plan()
        second = self.plan()
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "DELIVERY_PLAN_READY")
        self.assertEqual(first["task_id"], TASK_ID)
        self.assertEqual(first["base_sha"], self.base_sha)
        self.assertEqual(first["target_branch"], "main")
        self.assertEqual(
            first["branch_name"],
            f"autonomous/{TASK_ID.lower()}-{self.base_sha[:12]}",
        )
        self.assertEqual(first["commit_subject"], f"chore(automation): deliver {TASK_ID}")
        self.assertEqual(first["pr_title"], f"Boonta automation: {TASK_ID}")
        self.assertIn(f"BOONTA_TASK_ID: {TASK_ID}", first["pr_body"])
        self.assertEqual(first["changed_paths"], [SOURCE_PATH])
        self.assertEqual(first["executed_test_ids"], list(MANDATORY_TEST_IDS))
        self.assertFalse(first["remote_write_performed"])
        self.assertFalse(first["commit_created"])
        self.assertFalse(first["branch_created"])
        self.assertFalse(first["pull_request_created"])
        self.assertFalse(first["auto_merge_enabled"])
        self.assertFalse(first["network_accessed"])
        self.assert_source_clean()

    def test_only_verified_status_can_create_delivery_plan(self):
        self.write_verified(status="FAILED")
        with self.assertRaisesRegex(DeliveryPlanError, "Only a VERIFIED"):
            self.plan()

    def test_exact_task_and_base_binding_are_required(self):
        self.write_verified(task_id="AUTOMATION-OTHER-TASK")
        with self.assertRaisesRegex(DeliveryPlanError, "task ID/base SHA"):
            self.plan()
        self.write_verified(base_sha="0" * 40)
        with self.assertRaisesRegex(DeliveryPlanError, "task ID/base SHA"):
            self.plan()

    def test_all_mandatory_test_ids_must_be_present(self):
        self.write_verified(executed_test_ids=[MANDATORY_TEST_IDS[0]])
        with self.assertRaisesRegex(DeliveryPlanError, "all mandatory"):
            self.plan()

    def test_every_test_result_must_be_successful_and_exact(self):
        report = json.loads(self.verified_path.read_text(encoding="utf-8"))
        report["test_report"]["results"][1]["status"] = "FAILED"
        self.verified_path.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(DeliveryPlanError, "successful fixed-ID"):
            self.plan()

    def test_paths_must_be_subset_of_owner_approved_scope(self):
        self.write_verified(changed_paths=["src/unauthorized.c"])
        with self.assertRaisesRegex(DeliveryPlanError, "exceed the owner-approved"):
            self.plan()

    def test_empty_queue_cannot_produce_delivery_plan(self):
        self.ledger["tasks"][0]["status"] = "blocked"
        self.ledger_path.write_text(json.dumps(self.ledger), encoding="utf-8")
        git(self.root, "add", "docs/automation/task-ledger-summary.json")
        git(self.root, "commit", "-qm", "block fixture task")
        self.base_sha = git(self.root, "rev-parse", "HEAD")
        self.write_allowlist(base_sha=self.base_sha)
        self.write_verified(base_sha=self.base_sha)
        with self.assertRaisesRegex(DeliveryPlanError, "exactly one canonical active task"):
            self.plan()

    def test_invalid_target_branch_is_rejected(self):
        self.ledger["tasks"][0]["target_branch"] = "feature/unreviewed"
        self.ledger_path.write_text(json.dumps(self.ledger), encoding="utf-8")
        git(self.root, "add", "docs/automation/task-ledger-summary.json")
        git(self.root, "commit", "-qm", "bad target branch")
        self.base_sha = git(self.root, "rev-parse", "HEAD")
        self.write_allowlist(base_sha=self.base_sha)
        self.write_verified(base_sha=self.base_sha)
        with self.assertRaisesRegex(DeliveryPlanError, "unsupported target branch"):
            self.plan()

    def test_nonready_owner_allowlist_is_rejected(self):
        self.write_allowlist(status="WAITING_FOR_OWNER_APPROVED_PATHS")
        with self.assertRaisesRegex(DeliveryPlanError, "not READY"):
            self.plan()

    def test_unknown_report_fields_are_rejected(self):
        self.write_verified(arbitrary_shell_command="echo no")
        with self.assertRaisesRegex(DeliveryPlanError, "exact pipeline report contract"):
            self.plan()


if __name__ == "__main__":
    unittest.main(verbosity=2)
