#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_autonomous_patch_cycle as cycle

TASK_ID = "PATCH-CYCLE-TEST"
REPOSITORY = "Master-Chiken/boonta-reborn-88"
PR_URL = f"https://github.com/{REPOSITORY}/pull/987"
HEAD_SHA = "a" * 40


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True,
        check=False, timeout=15,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class PatchCycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="boonta-patch-cycle-test-")
        self.parent = Path(self.temp.name).resolve()
        self.target = self.parent / "target"
        self.policy = self.parent / "policy"
        self.target.mkdir()
        self.policy.mkdir()
        for root, name in ((self.target, "target"), (self.policy, "policy")):
            git(root, "init", "-q")
            git(root, "config", "user.name", "Boonta Cycle Test")
            git(root, "config", "user.email", "boonta-cycle-test@example.invalid")
            (root / f"{name}.txt").write_text(name + "\n", encoding="utf-8")
            git(root, "add", f"{name}.txt")
            git(root, "commit", "-qm", name + " fixture")
        self.context = self.parent / "context.txt"
        self.context.write_text("Authoritative selected task context.", encoding="utf-8")
        self.report = self.parent / "cycle-report.txt"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def env(self, **extra: str) -> dict[str, str]:
        values = {
            "BOONTA_DETERMINISTIC_DELIVERY_ENABLED": "true",
            "GITHUB_REPOSITORY": REPOSITORY,
            "GITHUB_TOKEN": "scoped-test-token",
        }
        values.update(extra)
        return values

    def test_delivery_gate_blocks_before_sha_reads_or_provider_use(self):
        with patch.dict(os.environ, {"BOONTA_DETERMINISTIC_DELIVERY_ENABLED": "false"}, clear=True):
            with patch.object(cycle, "run_provider_patch") as provider:
                result = cycle.run_cycle(
                    target_root=self.target,
                    policy_root=self.policy,
                    context_path=self.context,
                    report_path=self.report,
                    task_id=TASK_ID,
                    target_branch="dev",
                    model="groq/openai/gpt-oss-20b",
                )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["provider_request_started"])
        self.assertIn("BOONTA_DETERMINISTIC_DELIVERY_ENABLED", self.report.read_text(encoding="utf-8"))
        provider.assert_not_called()

    def test_missing_owner_path_blocks_before_provider_and_writer_gate(self):
        with patch.dict(os.environ, self.env(), clear=True):
            with (
                patch.object(cycle, "build_allowlist", return_value={
                    "status": "WAITING_FOR_OWNER_APPROVED_PATHS",
                    "reason": "No exact owner-approved write path exists.",
                }) as allowlist,
                patch.object(cycle, "run_provider_patch") as provider,
                patch.object(cycle, "require_execution_gates") as gates,
            ):
                result = cycle.run_cycle(
                    target_root=self.target,
                    policy_root=self.policy,
                    context_path=self.context,
                    report_path=self.report,
                    task_id=TASK_ID,
                    target_branch="dev",
                    model="groq/openai/gpt-oss-20b",
                )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("No model request was made", self.report.read_text(encoding="utf-8"))
        allowlist.assert_called_once()
        provider.assert_not_called()
        gates.assert_not_called()

    def test_missing_independent_owner_gate_blocks_before_provider(self):
        with patch.dict(os.environ, self.env(), clear=True):
            with (
                patch.object(cycle, "build_allowlist", side_effect=lambda root, **kwargs: {
                    "status": "READY",
                    "task_id": TASK_ID,
                    "base_sha": git(self.target, "rev-parse", "HEAD"),
                    "policy_base_sha": git(self.policy, "rev-parse", "HEAD"),
                    "approval_ref": "https://github.com/Master-Chiken/boonta-reborn-88/pull/400",
                    "purpose": "Synthetic approved path",
                    "allowed_paths": ["target.txt"],
                }),
                patch.object(cycle, "run_provider_patch") as provider,
            ):
                result = cycle.run_cycle(
                    target_root=self.target,
                    policy_root=self.policy,
                    context_path=self.context,
                    report_path=self.report,
                    task_id=TASK_ID,
                    target_branch="dev",
                    model="groq/openai/gpt-oss-20b",
                )
                self.assertNotIn("BOONTA_DETERMINISTIC_DELIVERY_OWNER_APPROVED", os.environ)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("BOONTA_DETERMINISTIC_DELIVERY_OWNER_APPROVED", self.report.read_text(encoding="utf-8"))
        provider.assert_not_called()

    def test_verified_patch_creates_only_draft_non_merged_pr(self):
        target_sha = git(self.target, "rev-parse", "HEAD")
        policy_sha = git(self.policy, "rev-parse", "HEAD")
        allowlist_report = {
            "status": "READY",
            "task_id": TASK_ID,
            "base_sha": target_sha,
            "policy_base_sha": policy_sha,
            "approval_ref": "https://github.com/Master-Chiken/boonta-reborn-88/pull/400",
            "purpose": "Synthetic approved path",
            "allowed_paths": ["target.txt"],
        }
        verified_report = {"status": "VERIFIED", "task_id": TASK_ID}
        delivery_plan = {
            "status": "DELIVERY_PLAN_READY",
            "target_branch": "dev",
            "branch_name": "autonomous/patch-cycle-test",
        }
        writer_result = {
            "status": "DRAFT_PR_CREATED",
            "pull_request_url": PR_URL,
            "commit_sha": HEAD_SHA,
            "draft": True,
            "auto_merge": False,
            "merge_performed": False,
        }
        with patch.dict(os.environ, self.env(), clear=True):
            with (
                patch.object(cycle, "build_allowlist", return_value=allowlist_report) as allowlist,
                patch.object(cycle, "require_execution_gates", return_value="scoped-test-token") as gates,
                patch.object(cycle, "run_provider_patch", return_value={
                    "provider_model": "groq/openai/gpt-oss-20b",
                    "changed_paths": ["target.txt"],
                }) as provider,
                patch.object(cycle, "verify_in_isolated_worktree", return_value=verified_report) as verify,
                patch.object(cycle, "build_delivery_plan", return_value=delivery_plan) as plan,
                patch.object(cycle, "validate_plan_against_sources") as validate_plan,
                patch.object(cycle, "execute_delivery", return_value=writer_result) as execute,
            ):
                result = cycle.run_cycle(
                    target_root=self.target,
                    policy_root=self.policy,
                    context_path=self.context,
                    report_path=self.report,
                    task_id=TASK_ID,
                    target_branch="dev",
                    model="groq/openai/gpt-oss-20b",
                )
        self.assertEqual(result["status"], "PROGRESS")
        self.assertEqual(result["pull_request_url"], PR_URL)
        self.assertFalse(result["auto_merge"])
        self.assertFalse(result["merge_performed"])
        report = self.report.read_text(encoding="utf-8")
        self.assertIn("BOONTA_CYCLE_STATUS: PROGRESS", report)
        self.assertIn(f"BOONTA_CYCLE_EVIDENCE: {PR_URL} @ {HEAD_SHA}", report)
        self.assertIn("BOONTA_CYCLE_EVIDENCE_BASE: dev", report)
        allowlist.assert_called_once()
        gates.assert_called_once_with(REPOSITORY)
        provider.assert_called_once()
        verify.assert_called_once()
        plan.assert_called_once()
        validate_plan.assert_called_once()
        execute.assert_called_once()
        self.assertEqual(git(self.target, "status", "--porcelain"), "")
        self.assertEqual(git(self.policy, "status", "--porcelain"), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
