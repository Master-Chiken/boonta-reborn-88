"""Tests for the persistent Boonta task ledger validator."""
import copy
import importlib.util
import unittest
\nimport importlib.util
from pathlib import Path

AUDIT_PATH = Path(__file__).with_name("audit_task_ledger_github.py")
AUDIT_SPEC = importlib.util.spec_from_file_location("audit_task_ledger_github", AUDIT_PATH)
audit = importlib.util.module_from_spec(AUDIT_SPEC)
assert AUDIT_SPEC and AUDIT_SPEC.loader
AUDIT_SPEC.loader.exec_module(audit)
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("check_task_ledger.py")
SPEC = importlib.util.spec_from_file_location("check_task_ledger", MODULE_PATH)
ledger = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(ledger)


def valid_task(task_id="TASK-001", status="queued"):
    return {
        "task_id": task_id,
        "title": "Bounded research task",
        "queue": "#226",
        "platform_scope": ["GameCube/Wii"],
        "status": status,
        "question": "What does the pinned evidence establish?",
        "acceptance_criteria": ["Record exact source revision", "Separate facts from unknowns"],
        "evidence": [],
        "next_action": "Inspect the pinned source and update the dossier.",
        "updated_at": "2026-11-04",
    }


def valid_ledger():
    return {
        "schema_version": 1,
        "updated_at": "2026-11-04",
        "policy": {"max_active_tasks": 1},
        "tasks": [valid_task()],
    }


class TaskLedgerTests(unittest.TestCase):
    def test_accepts_valid_ledger(self):
        self.assertEqual(ledger.validate_ledger(valid_ledger()), [])

    def test_rejects_duplicate_ids(self):
        data = valid_ledger()
        data["tasks"].append(valid_task())
        self.assertTrue(any("duplicate task_id" in e for e in ledger.validate_ledger(data)))

    def test_enforces_single_active_task(self):
        data = valid_ledger()
        data["tasks"] = [valid_task("TASK-001", "active"), valid_task("TASK-002", "active")]
        self.assertTrue(any("at most one task" in e for e in ledger.validate_ledger(data)))

    def test_in_review_requires_pr_and_exact_head(self):
        data = valid_ledger()
        task = valid_task(status="in_review")
        task["pr_url"] = "https://github.com/Master-Chiken/boonta-reborn-88/pull/1"
        task["head_sha"] = "abc"
        data["tasks"] = [task]
        errors = ledger.validate_ledger(data)
        self.assertTrue(any("exact 40-character head SHA" in e for e in errors))

    def test_completed_requires_evidence(self):
        data = valid_ledger()
        task = valid_task(status="completed")
        task["pr_url"] = "https://github.com/Master-Chiken/boonta-reborn-88/pull/1"
        task["head_sha"] = "a" * 40
        data["tasks"] = [task]
        self.assertTrue(any("completed task requires evidence" in e for e in ledger.validate_ledger(data)))

    def test_rejects_missing_platform_scope(self):
        data = valid_ledger()
        data["tasks"][0]["platform_scope"] = []
        self.assertTrue(any("platform_scope" in e for e in ledger.validate_ledger(data)))

class LiveGitHubReconciliationTests(unittest.TestCase):
    def test_accepts_open_pr_with_exact_head(self):
        task = {"task_id": "TASK-001", "status": "in_review", "head_sha": "a" * 40}
        pr = {"state": "open", "merged_at": None, "head": {"sha": "a" * 40}}
        self.assertEqual(audit.reconcile_task(task, pr), [])

    def test_rejects_stale_head_sha(self):
        task = {"task_id": "TASK-001", "status": "in_review", "head_sha": "a" * 40}
        pr = {"state": "open", "merged_at": None, "head": {"sha": "b" * 40}}
        self.assertTrue(any("does not match live PR head" in e for e in audit.reconcile_task(task, pr)))

    def test_rejects_closed_unmerged_pr_marked_in_review(self):
        task = {"task_id": "TASK-001", "status": "in_review", "head_sha": "a" * 40}
        pr = {"state": "closed", "merged_at": None, "head": {"sha": "a" * 40}}
        self.assertTrue(any("open, unmerged PR" in e for e in audit.reconcile_task(task, pr)))

    def test_completed_requires_merged_pr(self):
        task = {"task_id": "TASK-001", "status": "completed", "head_sha": "a" * 40}
        pr = {"state": "closed", "merged_at": None, "head": {"sha": "a" * 40}}
        self.assertTrue(any("must point to a merged PR" in e for e in audit.reconcile_task(task, pr)))


if __name__ == "__main__":
    unittest.main()
