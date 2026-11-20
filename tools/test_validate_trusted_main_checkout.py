#!/usr/bin/env python3
"""Offline tests for trusted main validation with a regenerated compact summary."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from check_task_ledger_summary import build_summary
from validate_trusted_main_checkout import TrustedMainCheckoutError, validate_trusted_main_checkout


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, stdin=subprocess.DEVNULL,
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class TrustedMainFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="boonta-trusted-main-")
        self.root = Path(self.temp.name).resolve()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Boonta Trusted Main Test")
        git(self.root, "config", "user.email", "trusted-main@example.invalid")
        docs = self.root / "docs/automation"
        docs.mkdir(parents=True)
        self.ledger = {
            "schema_version": 1,
            "updated_at": "2026-11-16",
            "policy": {"max_active_tasks": 1},
            "tasks": [{
                "task_id": "FIXTURE-TASK",
                "title": "Trusted task",
                "owner_role_id": "test",
                "parent_objective_id": "fixture",
                "depends_on": [],
                "owner_approved": True,
                "queue": "#1",
                "platform_scope": ["GameCube"],
                "status": "queued",
                "target_branch": "dev",
                "read_paths": ["src/main.c"],
                "read_ranges": [{"path": "src/main.c", "start_line": 1, "end_line": 2}],
                "question": "Can this task be tested?",
                "acceptance_criteria": ["Criterion one"],
                "next_action": "Next: test one",
            }],
        }
        self.summary_path = docs / "task-ledger-summary.json"
        self.ledger_path = docs / "task-ledger.json"
        self.policy_path = docs / "patch-path-allowlist.json"
        self.ledger_path.write_text(json.dumps(self.ledger), encoding="utf-8")
        self.summary_path.write_text(json.dumps(build_summary(self.ledger)), encoding="utf-8")
        self.policy_path.write_text(json.dumps({
            "schema_version": 1,
            "policy": {
                "owner_review_required": True,
                "path_mode": "exact",
                "max_paths_per_task": 20,
            },
            "tasks": [],
        }), encoding="utf-8")
        git(self.root, "add", "docs/automation")
        git(self.root, "commit", "-qm", "trusted main fixture")
        self.sha = git(self.root, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.temp.cleanup()


class TrustedMainValidationTests(TrustedMainFixture):
    def test_clean_trusted_main_checkout_passes(self):
        self.assertEqual(validate_trusted_main_checkout(self.root, self.sha), self.root)

    def test_exact_derived_summary_refresh_is_allowed(self):
        stale = json.loads(self.summary_path.read_text(encoding="utf-8"))
        stale["tasks"][0]["next_action_excerpt"] = "stale"
        self.summary_path.write_text(json.dumps(stale), encoding="utf-8")
        self.assertEqual(validate_trusted_main_checkout(self.root, self.sha), self.root)

    def test_unrelated_runner_workspace_checkout_does_not_invalidate_trusted_authority(self):
        (self.root / ".boonta-target-source").mkdir()
        self.assertEqual(validate_trusted_main_checkout(self.root, self.sha), self.root)

    def test_modified_summary_that_does_not_match_ledger_is_rejected(self):
        self.summary_path.write_text('{"schema_version":2,"tasks":[]}\n', encoding="utf-8")
        with self.assertRaisesRegex(TrustedMainCheckoutError, "does not match"):
            validate_trusted_main_checkout(self.root, self.sha)

    def test_modified_canonical_ledger_is_rejected(self):
        ledger = dict(self.ledger, updated_at="tampered")
        self.ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
        with self.assertRaisesRegex(TrustedMainCheckoutError, "local changes"):
            validate_trusted_main_checkout(self.root, self.sha)

    def test_modified_owner_path_policy_is_rejected(self):
        self.policy_path.write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(TrustedMainCheckoutError, "local changes"):
            validate_trusted_main_checkout(self.root, self.sha)

    def test_stale_policy_sha_is_rejected(self):
        with self.assertRaisesRegex(TrustedMainCheckoutError, "HEAD differs"):
            validate_trusted_main_checkout(self.root, "0" * 40)

    def test_symlinked_authority_file_is_rejected(self):
        self.policy_path.unlink()
        self.policy_path.symlink_to(self.ledger_path)
        with self.assertRaisesRegex(TrustedMainCheckoutError, "missing or symlinked"):
            validate_trusted_main_checkout(self.root, self.sha)


if __name__ == "__main__":
    unittest.main(verbosity=2)
