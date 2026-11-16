#!/usr/bin/env python3
"""Offline tests for the workflow-owned provider verify/test/delivery pipeline."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import execute_autonomous_provider_cycle as cycle

TASK_ID = "GC-RIVAL-ROUTE-PROGRESSION"
BASE_SHA = "a" * 40
POLICY_SHA = "b" * 40


class ProviderCycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="boonta-provider-cycle-")
        root = Path(self.temp.name)
        self.source = root / "source"
        self.policy = root / "policy"
        self.source.mkdir()
        self.policy.mkdir()
        self.proposal = root / "proposal.json"
        self.proposal.write_text('{"fixture": true}\n', encoding="utf-8")
        self.allowlist = root / "allowlist.json"
        self.allowlist.write_text("{}\n", encoding="utf-8")
        self.verified = root / "verified.json"
        self.plan = root / "plan.json"
        self.report = root / "cycle-report.txt"
        self.original_env = {
            key: os.environ.get(key)
            for key in (
                "GITHUB_TOKEN",
                "GITHUB_REPOSITORY",
                "BOONTA_DETERMINISTIC_DELIVERY_ENABLED",
                "BOONTA_DETERMINISTIC_DELIVERY_OWNER_APPROVED",
            )
        }
        os.environ["GITHUB_TOKEN"] = "x" * 40
        os.environ.pop("BOONTA_DETERMINISTIC_DELIVERY_ENABLED", None)
        os.environ.pop("BOONTA_DETERMINISTIC_DELIVERY_OWNER_APPROVED", None)

    def tearDown(self) -> None:
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.temp.cleanup()

    def call(self, **overrides):
        args = {
            "source_root": self.source,
            "policy_root": self.policy,
            "proposal_path": self.proposal,
            "allowlist_report_path": self.allowlist,
            "verified_report_path": self.verified,
            "plan_path": self.plan,
            "cycle_report_path": self.report,
            "expected_task_id": TASK_ID,
            "expected_base_sha": BASE_SHA,
            "expected_policy_sha": POLICY_SHA,
            "repository": cycle.REPOSITORY,
            "preflight_allowed": True,
        }
        args.update(overrides)
        return cycle.execute_provider_cycle(**args)

    def test_missing_proposal_reports_blocked_without_any_github_writer(self):
        self.proposal.unlink()
        with (
            patch.object(cycle, "verify_in_isolated_worktree") as verify,
            patch.object(cycle, "build_delivery_plan") as plan,
            patch.object(cycle, "execute_delivery") as writer,
        ):
            result = self.call()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("did not submit", result["reason"])
        self.assertFalse(verify.called)
        self.assertFalse(plan.called)
        self.assertFalse(writer.called)
        report = self.report.read_text(encoding="utf-8")
        self.assertIn("BOONTA_CYCLE_STATUS: BLOCKED", report)
        self.assertIn("BOONTA_CYCLE_BLOCKER: ", report)
        self.assertIn("BOONTA_CYCLE_NEXT_ACTION: ", report)
        self.assertNotIn("{_safe_line", report)

    def test_verified_patch_creates_exact_progress_report_only_after_writer_success(self):
        verified = {
            "status": "VERIFIED",
            "task_id": TASK_ID,
            "base_sha": BASE_SHA,
            "executed_test_ids": ["automation.task_preflight", "gamecube.rival_host_tests"],
        }
        plan = {"status": "DELIVERY_PLAN_READY", "target_branch": "dev"}
        delivered = {
            "status": "PR_CREATED",
            "pull_request_url": "https://github.com/Master-Chiken/boonta-reborn-88/pull/777",
            "commit_sha": "c" * 40,
            "draft": False,
            "auto_merge": False,
            "merge_performed": False,
        }
        with (
            patch.object(cycle, "verify_in_isolated_worktree", return_value=verified) as verify,
            patch.object(cycle, "build_delivery_plan", return_value=plan) as build_plan,
            patch.object(cycle, "execute_delivery", return_value=delivered) as writer,
        ):
            result = self.call()

        self.assertEqual(result["status"], "PROGRESS")
        self.assertEqual(result["target_branch"], "dev")
        self.assertEqual(result["pull_request_url"], delivered["pull_request_url"])
        self.assertEqual(result["head_sha"], delivered["commit_sha"])
        report = self.report.read_text(encoding="utf-8")
        self.assertIn("BOONTA_CYCLE_STATUS: PROGRESS", report)
        self.assertIn("BOONTA_CYCLE_EVIDENCE: " + delivered["pull_request_url"] + " @ " + delivered["commit_sha"], report)
        self.assertIn("BOONTA_CYCLE_EVIDENCE_BASE: dev", report)
        verify.assert_called_once()
        build_plan.assert_called_once()
        writer.assert_called_once()
        self.assertTrue(cycle.os.environ["BOONTA_DETERMINISTIC_DELIVERY_ENABLED"])
        self.assertTrue(cycle.os.environ["BOONTA_DETERMINISTIC_DELIVERY_OWNER_APPROVED"])
        self.assertEqual(writer.call_args.kwargs["policy_root"], self.policy)
        self.assertEqual(writer.call_args.kwargs["expected_policy_sha"], POLICY_SHA)

    def test_verification_failure_never_calls_plan_or_writer(self):
        failed = {
            "status": "FAILED",
            "test_report": {
                "status": "FAILED",
                "results": [{
                    "test_id": "gamecube.rival_host_tests",
                    "status": "FAILED",
                }],
            },
        }
        with (
            patch.object(cycle, "verify_in_isolated_worktree", return_value=failed),
            patch.object(cycle, "build_delivery_plan") as plan,
            patch.object(cycle, "execute_delivery") as writer,
        ):
            result = self.call()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("gamecube.rival_host_tests", result["reason"])
        self.assertFalse(plan.called)
        self.assertFalse(writer.called)

    def test_writer_failure_is_reported_as_blocked_and_never_claims_progress(self):
        with (
            patch.object(cycle, "verify_in_isolated_worktree", return_value={"status": "VERIFIED", "executed_test_ids": []}),
            patch.object(cycle, "build_delivery_plan", return_value={"target_branch": "main"}),
            patch.object(cycle, "execute_delivery", side_effect=cycle.DeliveryExecutionError("deterministic branch already exists")),
        ):
            result = self.call()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("deterministic branch already exists", result["reason"])
        report = self.report.read_text(encoding="utf-8")
        self.assertIn("BOONTA_CYCLE_STATUS: BLOCKED", report)
        self.assertNotIn("BOONTA_CYCLE_EVIDENCE:", report)

    def test_wrong_repository_is_rejected_before_verification(self):
        with patch.object(cycle, "verify_in_isolated_worktree") as verify:
            with self.assertRaisesRegex(cycle.ProviderCycleError, "canonical Boonta repository"):
                self.call(repository="attacker/other")
        self.assertFalse(verify.called)

    def test_preflight_gate_must_be_true_before_verification(self):
        with patch.object(cycle, "verify_in_isolated_worktree") as verify:
            with self.assertRaisesRegex(cycle.ProviderCycleError, "preflight did not pass"):
                self.call(preflight_allowed=False)
        self.assertFalse(verify.called)


if __name__ == "__main__":
    unittest.main(verbosity=2)
