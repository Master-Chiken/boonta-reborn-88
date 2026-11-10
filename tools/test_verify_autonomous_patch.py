#!/usr/bin/env python3
"""Offline end-to-end tests for isolated autonomous patch verification."""
from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import run_autonomous_patch_tests
from autonomous_patch_proposal import ProposalError
from verify_autonomous_patch import (
    MANDATORY_TEST_IDS,
    PipelineError,
    verify_in_isolated_worktree,
)

TASK_ID = "AUTOMATION-PIPELINE-FIXTURE"
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


def git_raw(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, stdin=subprocess.DEVNULL,
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout


class PipelineFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="boonta-pipeline-tests-")
        self.parent = Path(self.temp.name).resolve()
        self.root = self.parent / "repo"
        self.root.mkdir()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Boonta Test")
        git(self.root, "config", "user.email", "boonta-test@example.invalid")

        source = self.root / SOURCE_PATH
        source.parent.mkdir(parents=True)
        source.write_text("int boonta(void) {\n    return 0;\n}\n", encoding="utf-8")
        tools = self.root / "tools"
        tools.mkdir()
        (tools / "test_ok.py").write_text(
            "from pathlib import Path\n"
            "source = Path('src/main.c').read_text(encoding='utf-8')\n"
            "assert 'return 7;' in source\n"
            "print('patched source verified')\n",
            encoding="utf-8",
        )
        (tools / "test_fail.py").write_text(
            "raise SystemExit(9)\n", encoding="utf-8",
        )
        (tools / "test_untracked.py").write_text(
            "from pathlib import Path\n"
            "Path('untracked-from-test.txt').write_text('unexpected')\n"
            "print('fixture test passed')\n",
            encoding="utf-8",
        )
        git(self.root, "add", SOURCE_PATH, "tools")
        git(self.root, "commit", "-qm", "pipeline fixture base")
        self.base_sha = git(self.root, "rev-parse", "HEAD")

        source.write_text("int boonta(void) {\n    return 7;\n}\n", encoding="utf-8")
        self.diff = git_raw(self.root, "diff", "--", SOURCE_PATH)
        source.write_text("int boonta(void) {\n    return 0;\n}\n", encoding="utf-8")

        self.proposal_path = self.parent / "proposal.json"
        self.allowlist_path = self.parent / "allowlist.json"
        self.write_proposal()
        self.write_allowlist()

        self.original_registry = run_autonomous_patch_tests.TEST_REGISTRY.copy()
        for test_id in MANDATORY_TEST_IDS:
            run_autonomous_patch_tests.TEST_REGISTRY[test_id] = ("tools/test_ok.py",)

    def tearDown(self) -> None:
        run_autonomous_patch_tests.TEST_REGISTRY.clear()
        run_autonomous_patch_tests.TEST_REGISTRY.update(self.original_registry)
        self.temp.cleanup()

    def write_proposal(self, *, diff=None, task_id=TASK_ID, base_sha=None, test_ids=None):
        proposal = {
            "schema_version": 1,
            "task_id": task_id,
            "base_sha": base_sha or self.base_sha,
            "summary": "Update the synthetic fixture function",
            "unified_diff": self.diff if diff is None else diff,
            "test_ids": test_ids or ["automation.task_preflight"],
            "limitations": ["Synthetic test only"],
        }
        self.proposal_path.write_text(json.dumps(proposal), encoding="utf-8")

    def write_allowlist(self, *, status="READY", task_id=TASK_ID, base_sha=None, paths=None):
        report = {
            "status": status,
            "task_id": task_id,
            "base_sha": base_sha or self.base_sha,
            "approval_ref": APPROVAL if status == "READY" else "",
            "purpose": "Synthetic fixture approval",
            "allowed_paths": [SOURCE_PATH] if paths is None and status == "READY" else (paths or []),
        }
        self.allowlist_path.write_text(json.dumps(report), encoding="utf-8")

    def run_pipeline(self):
        return verify_in_isolated_worktree(
            self.root,
            proposal_path=self.proposal_path,
            allowlist_report_path=self.allowlist_path,
            expected_task_id=TASK_ID,
            expected_base_sha=self.base_sha,
        )

    def assert_source_checkout_untouched(self):
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), self.base_sha)
        self.assertEqual(git(self.root, "status", "--porcelain"), "")
        worktrees = git(self.root, "worktree", "list", "--porcelain").splitlines()
        self.assertEqual(len([line for line in worktrees if line.startswith("worktree ")]), 1)


class IsolatedPatchPipelineTests(PipelineFixture):
    def test_valid_patch_runs_mandatory_tests_and_leaves_source_clean(self):
        report = self.run_pipeline()
        self.assertEqual(report["status"], "VERIFIED")
        self.assertEqual(report["changed_paths"], [SOURCE_PATH])
        self.assertEqual(report["executed_test_ids"], list(MANDATORY_TEST_IDS))
        self.assertEqual(report["test_report"]["status"], "PASSED")
        self.assertFalse(report["source_checkout_modified"])
        self.assertFalse(report["commit_created"])
        self.assertFalse(report["branch_created"])
        self.assertFalse(report["network_accessed"])
        bundle = report["delivery_bundle"]
        self.assertEqual(len(bundle), 1)
        file_entry = bundle[0]
        self.assertEqual(file_entry["path"], SOURCE_PATH)
        self.assertEqual(file_entry["base_blob_sha"], git(self.root, "rev-parse", f"{self.base_sha}:{SOURCE_PATH}"))
        data = base64.b64decode(file_entry["content_base64"], validate=True)
        self.assertEqual(data.decode("utf-8"), "int boonta(void) {\n    return 7;\n}\n")
        self.assertEqual(hashlib.sha256(data).hexdigest(), file_entry["content_sha256"])
        expected_git_blob = hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
        self.assertEqual(expected_git_blob, file_entry["result_blob_sha"])
        self.assertIn(file_entry["mode"], {"100644", "100755"})
        self.assert_source_checkout_untouched()

    def test_test_failure_stops_pipeline_and_removes_worktree(self):
        run_autonomous_patch_tests.TEST_REGISTRY[MANDATORY_TEST_IDS[0]] = ("tools/test_fail.py",)
        report = self.run_pipeline()
        self.assertEqual(report["status"], "FAILED")
        self.assertEqual(report["test_report"]["results"][0]["exit_code"], 9)
        self.assertTrue(report["test_report"]["stopped_after_first_failure"])
        self.assert_source_checkout_untouched()

    def test_unexpected_test_artifact_rejects_verification_and_cleans_worktree(self):
        run_autonomous_patch_tests.TEST_REGISTRY[MANDATORY_TEST_IDS[0]] = ("tools/test_untracked.py",)
        # A successful test command is not enough: only the proposal's exact
        # tracked changes may remain in the disposable checkout.
        with self.assertRaisesRegex(PipelineError, "outside the exact validated patch"):
            self.run_pipeline()
        self.assert_source_checkout_untouched()

    def test_test_mutating_a_validated_file_is_rejected(self):
        (self.root / "tools/test_mutate.py").write_text(
            "from pathlib import Path\\n"
            "Path('src/main.c').write_text('int boonta(void) { return 99; }\\n', encoding='utf-8')\\n",
            encoding="utf-8",
        )
        run_autonomous_patch_tests.TEST_REGISTRY[MANDATORY_TEST_IDS[0]] = ("tools/test_mutate.py",)
        with self.assertRaisesRegex(PipelineError, "modified a validated patch file"):
            self.run_pipeline()
        self.assert_source_checkout_untouched()

    def test_non_ready_allowlist_is_rejected_before_worktree_creation(self):
        self.write_allowlist(status="NO_ACTIVE_TASK")
        with self.assertRaisesRegex(ProposalError, "not READY"):
            self.run_pipeline()
        self.assert_source_checkout_untouched()

    def test_allowlist_task_mismatch_is_rejected_before_worktree_creation(self):
        self.write_allowlist(task_id="AUTOMATION-ANOTHER-TASK")
        with self.assertRaisesRegex(ProposalError, "task ID"):
            self.run_pipeline()
        self.assert_source_checkout_untouched()

    def test_patch_outside_owner_allowlist_is_rejected(self):
        other = "src/other.c"
        diff = self.diff.replace(SOURCE_PATH, other)
        self.write_proposal(diff=diff)
        self.write_allowlist(paths=[SOURCE_PATH])
        with self.assertRaisesRegex(ProposalError, "outside the trusted task allowlist"):
            self.run_pipeline()
        self.assert_source_checkout_untouched()

    def test_dirty_source_checkout_is_rejected(self):
        (self.root / "dirty.txt").write_text("unexpected", encoding="utf-8")
        with self.assertRaisesRegex(ProposalError, "not clean"):
            self.run_pipeline()


if __name__ == "__main__":
    unittest.main(verbosity=2)
