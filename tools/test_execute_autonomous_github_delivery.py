#!/usr/bin/env python3
"""Offline tests for the guarded deterministic GitHub draft-PR writer."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from autonomous_patch_proposal import ProposalError
from build_autonomous_delivery_plan import build_delivery_plan
from verify_autonomous_patch import MANDATORY_TEST_IDS
from execute_autonomous_github_delivery import (
    DeliveryExecutionError,
    execute_delivery,
    main as writer_main,
    require_execution_gates,
    validate_plan_against_sources,
)
from run_autonomous_patch_tests import TEST_REGISTRY

REPOSITORY = "Master-Chiken/boonta-reborn-88"
TASK_ID = "AUTOMATION-WRITER-FIXTURE"
SOURCE_PATH = "src/main.c"
APPROVAL = "https://github.com/Master-Chiken/boonta-reborn-88/pull/999"
TOKEN = "fixture-token-that-is-long-enough-for-tests"


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, stdin=subprocess.DEVNULL,
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


def git_bytes(root: Path, data: bytes, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, input=data,
        capture_output=True, check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr.decode("utf-8", errors="replace"))
    return result.stdout.decode("ascii").strip()


class WriterFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="boonta-github-writer-")
        self.parent = Path(self.temp.name).resolve()
        self.root = self.parent / "repo"
        self.root.mkdir()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Boonta Test")
        git(self.root, "config", "user.email", "boonta-test@example.invalid")

        source = self.root / SOURCE_PATH
        source.parent.mkdir(parents=True)
        source.write_text("int boonta(void) { return 0; }\n", encoding="utf-8")

        docs = self.root / "docs/automation"
        docs.mkdir(parents=True)
        self.ledger_path = docs / "task-ledger-summary.json"
        self.policy_path = docs / "patch-path-allowlist.json"
        self.ledger_path.write_text(json.dumps({
            "schema_version": 2,
            "source": "docs/automation/task-ledger.json",
            "tasks": [{
                "task_id": TASK_ID,
                "title": "Writer fixture task",
                "status": "active",
                "target_branch": "main",
            }],
        }), encoding="utf-8")
        self.policy_path.write_text(json.dumps({
            "schema_version": 1,
            "policy": {
                "owner_review_required": True,
                "path_mode": "exact",
                "max_paths_per_task": 20,
            },
            "tasks": [{
                "task_id": TASK_ID,
                "purpose": "Synthetic writer fixture",
                "approval_ref": APPROVAL,
                "allowed_paths": [SOURCE_PATH],
            }],
        }), encoding="utf-8")

        git(self.root, "add", SOURCE_PATH, "docs/automation")
        git(self.root, "commit", "-qm", "writer fixture base")
        self.base_sha = git(self.root, "rev-parse", "HEAD")

        base_source = "int boonta(void) { return 0; }\n"
        result_source = "int boonta(void) { return 7; }\n"
        result_bytes = result_source.encode("utf-8")
        result_blob_sha = git_bytes(self.root, result_bytes, "hash-object", "--stdin")
        base_blob_sha = git(self.root, "rev-parse", f"{self.base_sha}:{SOURCE_PATH}")
        mode = git(self.root, "ls-files", "-s", "--", SOURCE_PATH).split()[0]

        self.allowlist_path = self.parent / "allowlist.json"
        self.verified_path = self.parent / "verified.json"
        self.plan_path = self.parent / "plan.json"
        self.allowlist_path.write_text(json.dumps({
            "status": "READY",
            "task_id": TASK_ID,
            "base_sha": self.base_sha,
            "approval_ref": APPROVAL,
            "purpose": "Synthetic writer fixture",
            "allowed_paths": [SOURCE_PATH],
        }), encoding="utf-8")
        self.verified_path.write_text(json.dumps({
            "status": "VERIFIED",
            "task_id": TASK_ID,
            "base_sha": self.base_sha,
            "summary": "Update one fixture source file",
            "changed_paths": [SOURCE_PATH],
            "requested_test_ids": [MANDATORY_TEST_IDS[0]],
            "executed_test_ids": list(MANDATORY_TEST_IDS),
            "test_report": {
                "status": "PASSED",
                "results": [{
                    "test_id": test_id,
                    "status": "PASSED",
                    "exit_code": 0,
                    "duration_seconds": 0.1,
                    "stdout": "ok\n",
                    "stderr": "",
                } for test_id in MANDATORY_TEST_IDS],
                "stopped_after_first_failure": False,
            },
            "delivery_bundle": [{
                "path": SOURCE_PATH,
                "mode": mode,
                "base_blob_sha": base_blob_sha,
                "result_blob_sha": result_blob_sha,
                "content_sha256": hashlib.sha256(result_bytes).hexdigest(),
                "content_base64": base64.b64encode(result_bytes).decode("ascii"),
            }],
            "isolated_worktree": True,
            "source_checkout_modified": False,
            "commit_created": False,
            "branch_created": False,
            "network_accessed": False,
        }), encoding="utf-8")

        self.plan = build_delivery_plan(
            self.root,
            verified_report_path=self.verified_path,
            allowlist_report_path=self.allowlist_path,
            expected_task_id=TASK_ID,
            expected_base_sha=self.base_sha,
        )
        self.plan_path.write_text(json.dumps(self.plan), encoding="utf-8")

        self.env = {
            "BOONTA_DETERMINISTIC_DELIVERY_ENABLED": "true",
            "BOONTA_DETERMINISTIC_DELIVERY_OWNER_APPROVED": "true",
            "GITHUB_TOKEN": TOKEN,
            "GITHUB_REPOSITORY": REPOSITORY,
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def assert_repo_clean(self) -> None:
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), self.base_sha)
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    def validate_plan(self) -> None:
        validate_plan_against_sources(
            self.plan,
            repo_root=self.root,
            verified_report_path=self.verified_path,
            allowlist_report_path=self.allowlist_path,
            expected_task_id=TASK_ID,
            expected_base_sha=self.base_sha,
            repository=REPOSITORY,
        )

    def fake_api(
        self,
        *,
        branch_exists=False,
        duplicate_pr=False,
        duplicate_pr_after_create=False,
        moved_on_recheck=False,
        wrong_draft_response=False,
    ):
        calls = []
        base_calls = 0
        pr_list_calls = 0

        def request(token, method, path, *, payload=None, allowed_404=False, timeout=20):
            nonlocal base_calls, pr_list_calls
            calls.append((method, path, payload, allowed_404))
            if path == f"/repos/{REPOSITORY}/git/ref/heads/main":
                base_calls += 1
                sha = self.base_sha
                if moved_on_recheck and base_calls >= 2:
                    sha = "c" * 40
                return {"object": {"sha": sha}}
            if path == f"/repos/{REPOSITORY}/git/ref/heads/{self.plan['branch_name']}":
                return {"object": {"sha": "d" * 40}} if branch_exists else None
            if path == f"/repos/{REPOSITORY}/pulls?state=open&per_page=100&page=1":
                pr_list_calls += 1
                if duplicate_pr or (duplicate_pr_after_create and pr_list_calls >= 2):
                    return [{
                        "number": 123,
                        "body": f"Existing item\nBOONTA_TASK_ID: {TASK_ID}",
                    }]
                return []
            if path == f"/repos/{REPOSITORY}/git/trees":
                return {"sha": "a" * 40}
            if path == f"/repos/{REPOSITORY}/git/commits":
                return {
                    "sha": "b" * 40,
                    "tree": {"sha": "a" * 40},
                    "parents": [{"sha": self.base_sha}],
                }
            if path == f"/repos/{REPOSITORY}/git/refs":
                return {
                    "ref": self.plan["github_write_plan"]["create_ref"]["ref"],
                    "object": {"sha": "b" * 40},
                }
            if path == f"/repos/{REPOSITORY}/pulls":
                return {
                    "number": 456,
                    "html_url": f"https://github.com/{REPOSITORY}/pull/456",
                    "title": self.plan["pr_title"],
                    "draft": not wrong_draft_response,
                    "head": {"ref": self.plan["branch_name"]},
                    "base": {"ref": self.plan["target_branch"]},
                }
            raise AssertionError(f"Unexpected API call: {method} {path}")

        return request, calls

    def execute_with_fake(self, request):
        return execute_delivery(
            self.plan,
            repo_root=self.root,
            verified_report_path=self.verified_path,
            allowlist_report_path=self.allowlist_path,
            expected_task_id=TASK_ID,
            expected_base_sha=self.base_sha,
            repository=REPOSITORY,
            token=TOKEN,
            request=request,
        )

    def cli_args(self, *, execute=False):
        values = [
            "--repo-root", str(self.root),
            "--repository", REPOSITORY,
            "--plan", str(self.plan_path),
            "--verified-report", str(self.verified_path),
            "--allowlist-report", str(self.allowlist_path),
            "--expected-task-id", TASK_ID,
            "--expected-base-sha", self.base_sha,
        ]
        if execute:
            values.append("--execute")
        return ["execute_autonomous_github_delivery.py", *values]


class DeterministicGitHubWriterTests(WriterFixture):
    def test_cli_defaults_to_dry_run_without_any_network_request(self):
        output = io.StringIO()
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("execute_autonomous_github_delivery.urllib.request.urlopen", side_effect=AssertionError("network must stay unused")) as urlopen,
            patch("sys.argv", self.cli_args()),
            redirect_stdout(output),
        ):
            exit_code = writer_main()
        self.assertEqual(exit_code, 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["status"], "DRY_RUN_VALIDATED")
        self.assertFalse(report["remote_write_performed"])
        urlopen.assert_not_called()
        self.assert_repo_clean()

    def test_cli_execute_without_both_explicit_gates_fails_before_network(self):
        output = io.StringIO()
        with (
            patch.dict(os.environ, {"GITHUB_TOKEN": TOKEN, "GITHUB_REPOSITORY": REPOSITORY}, clear=True),
            patch("execute_autonomous_github_delivery.urllib.request.urlopen", side_effect=AssertionError("network must stay unused")) as urlopen,
            patch("sys.argv", self.cli_args(execute=True)),
            redirect_stdout(output),
        ):
            exit_code = writer_main()
        self.assertEqual(exit_code, 2)
        report = json.loads(output.getvalue())
        self.assertEqual(report["status"], "REJECTED")
        self.assertIn("BOONTA_DETERMINISTIC_DELIVERY_ENABLED", report["reason"])
        urlopen.assert_not_called()
        self.assert_repo_clean()

    def test_plan_is_revalidated_against_canonical_sources(self):
        self.validate_plan()
        self.assert_repo_clean()

    def test_success_creates_only_draft_pr_and_never_merges(self):
        request, calls = self.fake_api()
        with patch.dict(os.environ, self.env, clear=False):
            result = self.execute_with_fake(request)
        self.assertEqual(result["status"], "DRAFT_PR_CREATED")
        self.assertEqual(result["pull_request_number"], 456)
        self.assertTrue(result["draft"])
        self.assertFalse(result["auto_merge"])
        self.assertFalse(result["merge_performed"])
        self.assertEqual(
            [(method, path.split("/heads/", 1)[-1] if "/heads/" in path else path.rsplit("/", 1)[-1]) for method, path, _, _ in calls],
            [
                ("GET", "main"),
                ("GET", self.plan["branch_name"]),
                ("GET", "pulls?state=open&per_page=100&page=1"),
                ("POST", "trees"),
                ("POST", "commits"),
                ("POST", "refs"),
                ("GET", "main"),
                ("GET", "pulls?state=open&per_page=100&page=1"),
                ("POST", "pulls"),
            ],
        )
        tree_payload = next(payload for method, path, payload, _ in calls if method == "POST" and path.endswith("/trees"))
        self.assertIn("base_tree", tree_payload)
        self.assertIn("tree", tree_payload)
        self.assertEqual(tree_payload["tree"][0]["content"], "int boonta(void) { return 7; }\n")
        commit_payload = next(payload for method, path, payload, _ in calls if method == "POST" and path.endswith("/commits"))
        self.assertEqual(commit_payload["parents"], [self.base_sha])
        self.assertEqual(commit_payload["tree"], "a" * 40)
        ref_payload = next(payload for method, path, payload, _ in calls if method == "POST" and path.endswith("/refs"))
        self.assertEqual(ref_payload["sha"], "b" * 40)
        pr_payload = next(payload for method, path, payload, _ in calls if method == "POST" and path.endswith("/pulls"))
        self.assertIs(pr_payload["draft"], True)
        self.assertNotIn("auto_merge", pr_payload)
        self.assert_repo_clean()

    def test_stale_target_branch_refuses_before_any_write(self):
        request, calls = self.fake_api()
        def stale_request(token, method, path, **kwargs):
            if path.endswith("/git/ref/heads/main"):
                calls.append((method, path, kwargs.get("payload"), kwargs.get("allowed_404", False)))
                return {"object": {"sha": "e" * 40}}
            return request(token, method, path, **kwargs)
        with patch.dict(os.environ, self.env, clear=False):
            with self.assertRaisesRegex(DeliveryExecutionError, "moved since"):
                self.execute_with_fake(stale_request)
        self.assertFalse(any(method == "POST" for method, *_ in calls))
        self.assert_repo_clean()

    def test_existing_deterministic_branch_refuses_before_any_write(self):
        request, calls = self.fake_api(branch_exists=True)
        with patch.dict(os.environ, self.env, clear=False):
            with self.assertRaisesRegex(DeliveryExecutionError, "branch already exists"):
                self.execute_with_fake(request)
        self.assertFalse(any(method == "POST" for method, *_ in calls))
        self.assert_repo_clean()

    def test_existing_task_pr_refuses_before_any_write(self):
        request, calls = self.fake_api(duplicate_pr=True)
        with patch.dict(os.environ, self.env, clear=False):
            with self.assertRaisesRegex(DeliveryExecutionError, "open PR already exists"):
                self.execute_with_fake(request)
        self.assertFalse(any(method == "POST" for method, *_ in calls))
        self.assert_repo_clean()

    def test_target_movement_after_branch_creation_does_not_open_pr(self):
        request, calls = self.fake_api(moved_on_recheck=True)
        with patch.dict(os.environ, self.env, clear=False):
            with self.assertRaisesRegex(DeliveryExecutionError, "no PR was opened"):
                self.execute_with_fake(request)
        self.assertTrue(any(method == "POST" and path.endswith("/refs") for method, path, *_ in calls))
        self.assertFalse(any(method == "POST" and path.endswith("/pulls") for method, path, *_ in calls))
        self.assert_repo_clean()

    def test_concurrent_task_pr_appearing_after_branch_creation_stops_delivery(self):
        request, calls = self.fake_api(duplicate_pr_after_create=True)
        with patch.dict(os.environ, self.env, clear=False):
            with self.assertRaisesRegex(DeliveryExecutionError, "appeared for this task"):
                self.execute_with_fake(request)
        self.assertTrue(any(method == "POST" and path.endswith("/refs") for method, path, *_ in calls))
        self.assertFalse(any(method == "POST" and path.endswith("/pulls") for method, path, *_ in calls))
        self.assert_repo_clean()

    def test_writer_rejects_non_draft_api_confirmation(self):
        request, calls = self.fake_api(wrong_draft_response=True)
        with patch.dict(os.environ, self.env, clear=False):
            with self.assertRaisesRegex(DeliveryExecutionError, "exact draft pull request"):
                self.execute_with_fake(request)
        self.assertTrue(any(method == "POST" and path.endswith("/pulls") for method, path, *_ in calls))
        self.assert_repo_clean()

    def test_execution_gates_require_exact_true_and_a_token(self):
        cases = [
            ({**self.env, "BOONTA_DETERMINISTIC_DELIVERY_ENABLED": "TRUE"}, "exact string true"),
            ({**self.env, "BOONTA_DETERMINISTIC_DELIVERY_OWNER_APPROVED": "1"}, "exact string true"),
            ({**self.env, "GITHUB_TOKEN": ""}, "GitHub token"),
            ({**self.env, "GITHUB_REPOSITORY": "somewhere/else"}, "does not match"),
        ]
        for environment, message in cases:
            with self.subTest(message=message), patch.dict(os.environ, environment, clear=True):
                with self.assertRaisesRegex(DeliveryExecutionError, message):
                    require_execution_gates(REPOSITORY)

    def test_execute_delivery_itself_enforces_gates(self):
        request, calls = self.fake_api()
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(DeliveryExecutionError, "ENABLED"):
                self.execute_with_fake(request)
        self.assertEqual(calls, [])

    def test_tampered_plan_is_rejected_before_api(self):
        tampered = dict(self.plan)
        tampered["branch_name"] = "attacker/chosen"
        with self.assertRaisesRegex(DeliveryExecutionError, "differs from the freshly regenerated"):
            validate_plan_against_sources(
                tampered,
                repo_root=self.root,
                verified_report_path=self.verified_path,
                allowlist_report_path=self.allowlist_path,
                expected_task_id=TASK_ID,
                expected_base_sha=self.base_sha,
                repository=REPOSITORY,
            )
        self.assert_repo_clean()


if __name__ == "__main__":
    unittest.main(verbosity=2)
