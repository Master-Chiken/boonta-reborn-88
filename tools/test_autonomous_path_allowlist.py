#!/usr/bin/env python3
"""Offline tests for owner-reviewed autonomous task path allowlists."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from build_autonomous_path_allowlist import AllowlistError, build_allowlist

TASK_ID = "AUTOMATION-ALLOWLIST-TASK"
BASE_TASK = {
    "task_id": TASK_ID,
    "status": "active",
    "target_branch": "main",
    "title": "Offline fixture task",
}
PATH = "src/main.c"
APPROVAL = "https://github.com/Master-Chiken/boonta-reborn-88/pull/999"


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, stdin=subprocess.DEVNULL,
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class AllowlistFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Boonta Test")
        git(self.root, "config", "user.email", "boonta-test@example.invalid")
        self.source = self.root / PATH
        self.source.parent.mkdir(parents=True)
        self.source.write_text("int boonta(void) { return 1; }\n", encoding="utf-8")
        self.ledger_path = Path("fixture-ledger.json")
        self.policy_path = Path("fixture-policy.json")
        self.ledger = {
            "schema_version": 2,
            "source": "docs/automation/task-ledger-summary.json",
            "tasks": [dict(BASE_TASK)],
        }
        self.policy = {
            "schema_version": 1,
            "policy": {
                "owner_review_required": True,
                "path_mode": "exact",
                "max_paths_per_task": 20,
            },
            "tasks": [{
                "task_id": TASK_ID,
                "purpose": "Synthetic test path only",
                "approval_ref": APPROVAL,
                "allowed_paths": [PATH],
            }],
        }
        self.write_inputs()
        git(self.root, "add", PATH, str(self.ledger_path), str(self.policy_path))
        git(self.root, "commit", "-qm", "fixture base")
        self.base_sha = git(self.root, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_inputs(self) -> None:
        (self.root / self.ledger_path).write_text(
            json.dumps(self.ledger), encoding="utf-8",
        )
        (self.root / self.policy_path).write_text(
            json.dumps(self.policy), encoding="utf-8",
        )

    def call_allowlist(self, *, task_id=TASK_ID, expected_sha=None):
        return build_allowlist(
            self.root,
            expected_base_sha=expected_sha or self.base_sha,
            requested_task_id=task_id,
            ledger_path=self.ledger_path,
            policy_path=self.policy_path,
        )

    def commit_inputs(self, message="update fixture inputs"):
        self.write_inputs()
        git(self.root, "add", str(self.ledger_path), str(self.policy_path))
        git(self.root, "commit", "-qm", message)
        self.base_sha = git(self.root, "rev-parse", "HEAD")


class OwnerApprovedAllowlistTests(AllowlistFixture):
    def test_exact_owner_approved_active_task_is_ready(self):
        report = self.call_allowlist()
        self.assertEqual(report["status"], "READY")
        self.assertEqual(report["allowed_paths"], [PATH])
        self.assertEqual(report["base_sha"], self.base_sha)
        self.assertEqual(report["approval_ref"], APPROVAL)

    def test_empty_queue_fails_closed_without_paths(self):
        self.ledger["tasks"][0]["status"] = "completed"
        self.commit_inputs()
        report = self.call_allowlist()
        self.assertEqual(report["status"], "NO_ACTIVE_TASK")
        self.assertEqual(report["allowed_paths"], [])

    def test_blocked_task_never_receives_paths(self):
        self.ledger["tasks"][0]["status"] = "blocked"
        self.commit_inputs()
        report = self.call_allowlist()
        self.assertEqual(report["status"], "NO_ACTIVE_TASK")
        self.assertEqual(report["allowed_paths"], [])

    def test_missing_owner_approval_entry_returns_waiting(self):
        self.policy["tasks"] = []
        self.commit_inputs()
        report = self.call_allowlist()
        self.assertEqual(report["status"], "WAITING_FOR_OWNER_APPROVED_PATHS")
        self.assertEqual(report["allowed_paths"], [])

    def test_requested_task_must_match_unique_active_task(self):
        with self.assertRaisesRegex(AllowlistError, "does not match"):
            self.call_allowlist(task_id="AUTOMATION-ANOTHER-TASK")

    def test_multiple_active_tasks_are_rejected(self):
        self.ledger["tasks"].append({
            "task_id": "AUTOMATION-SECOND-ACTIVE",
            "status": "active",
            "target_branch": "main",
        })
        self.commit_inputs()
        with self.assertRaisesRegex(AllowlistError, "one-active-task"):
            self.call_allowlist()

    def test_noncanonical_target_branch_is_rejected(self):
        self.ledger["tasks"][0]["target_branch"] = "feature/unapproved"
        self.commit_inputs()
        with self.assertRaisesRegex(AllowlistError, "target branch"):
            self.call_allowlist()

    def test_stale_base_sha_is_rejected(self):
        with self.assertRaisesRegex(AllowlistError, "differs"):
            self.call_allowlist(expected_sha="0" * 40)

    def test_dirty_checkout_is_rejected(self):
        (self.root / "untracked.txt").write_text("dirty", encoding="utf-8")
        with self.assertRaisesRegex(AllowlistError, "must be clean"):
            self.call_allowlist()

    def test_path_traversal_is_rejected(self):
        self.policy["tasks"][0]["allowed_paths"] = ["src/../outside.c"]
        self.commit_inputs()
        with self.assertRaisesRegex(AllowlistError, "traversal"):
            self.call_allowlist()

    def test_protected_workflow_path_is_rejected(self):
        self.policy["tasks"][0]["allowed_paths"] = [".github/workflows/loop.yml"]
        self.commit_inputs()
        with self.assertRaisesRegex(AllowlistError, "protected"):
            self.call_allowlist()

    def test_secret_and_credential_paths_are_rejected(self):
        for path in (".env.production", "secrets/provider.json", "certs/signing.PEM"):
            with self.subTest(path=path):
                self.policy["tasks"][0]["allowed_paths"] = [path]
                self.commit_inputs("test protected path")
                with self.assertRaisesRegex(AllowlistError, "protected"):
                    self.call_allowlist()

    def test_untracked_file_cannot_be_approved(self):
        extra = "src/untracked.c"
        self.policy["tasks"][0]["allowed_paths"] = [extra]
        self.commit_inputs()
        exclude = self.root / ".git/info/exclude"
        exclude.write_text("\\n" + extra + "\\n", encoding="utf-8")
        (self.root / extra).write_text("int unsafe;\\n", encoding="utf-8")
        with self.assertRaisesRegex(AllowlistError, "exactly one tracked file"):
            self.call_allowlist()

    def test_symlink_target_cannot_be_approved(self):
        link = "src/link.c"
        (self.root / link).symlink_to("main.c")
        git(self.root, "add", link)
        git(self.root, "commit", "-qm", "add symlink fixture")
        self.base_sha = git(self.root, "rev-parse", "HEAD")
        self.policy["tasks"][0]["allowed_paths"] = [link]
        self.commit_inputs()
        with self.assertRaisesRegex(AllowlistError, "regular tracked file"):
            self.call_allowlist()

    def test_duplicate_task_ids_in_policy_are_rejected(self):
        self.policy["tasks"].append(dict(self.policy["tasks"][0]))
        self.commit_inputs()
        with self.assertRaisesRegex(AllowlistError, "duplicate task ID"):
            self.call_allowlist()

    def test_unknown_task_in_policy_is_rejected(self):
        self.policy["tasks"][0]["task_id"] = "AUTOMATION-UNKNOWN-TASK"
        self.commit_inputs()
        with self.assertRaisesRegex(AllowlistError, "unknown canonical task"):
            self.call_allowlist()

    def test_non_repository_approval_reference_is_rejected(self):
        self.policy["tasks"][0]["approval_ref"] = "https://example.invalid/approval"
        self.commit_inputs()
        with self.assertRaisesRegex(AllowlistError, "owner-review evidence URL"):
            self.call_allowlist()

    def test_duplicate_paths_are_rejected(self):
        self.policy["tasks"][0]["allowed_paths"] = [PATH, PATH]
        self.commit_inputs()
        with self.assertRaisesRegex(AllowlistError, "duplicate paths"):
            self.call_allowlist()

    def test_more_than_twenty_paths_are_rejected(self):
        self.policy["tasks"][0]["allowed_paths"] = [f"src/file{i}.c" for i in range(21)]
        self.commit_inputs()
        with self.assertRaisesRegex(AllowlistError, "between one and 20"):
            self.call_allowlist()

    def test_path_policy_requires_owner_review_and_exact_paths(self):
        self.policy["policy"]["owner_review_required"] = False
        self.commit_inputs()
        with self.assertRaisesRegex(AllowlistError, "require owner review"):
            self.call_allowlist()

    def test_duplicate_json_properties_are_rejected(self):
        (self.root / self.policy_path).write_text(
            '{"schema_version":1,"schema_version":1}', encoding="utf-8",
        )
        git(self.root, "add", str(self.policy_path))
        git(self.root, "commit", "-qm", "duplicate JSON property")
        self.base_sha = git(self.root, "rev-parse", "HEAD")
        with self.assertRaisesRegex(AllowlistError, "Duplicate JSON property"):
            self.call_allowlist()


if __name__ == "__main__":
    unittest.main(verbosity=2)
