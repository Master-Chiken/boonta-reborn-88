#!/usr/bin/env python3
"""Offline regression tests for disposable exact-path agent workspaces."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from prepare_autonomous_patch_workspace import WorkspaceError, prepare_workspace

TASK_ID = "AUTONOMOUS-WORKSPACE-FIXTURE"
APPROVAL = "https://github.com/Master-Chiken/boonta-reborn-88/pull/999"
READ_PATHS = [
    "tools/summary.py",
    "tools/test_summary.py",
    "tools/checker.py",
]
WRITE_PATHS = [
    "tools/summary.py",
    "tools/test_summary.py",
]


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        stdin=subprocess.DEVNULL,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class WorkspaceFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="boonta-workspace-test-")
        self.parent = Path(self.temp.name).resolve()
        self.policy_root = self.parent / "policy"
        self.source_root = self.parent / "target"
        self.policy_root.mkdir()
        self.source_root.mkdir()
        self._init_repo(self.policy_root, "main")
        self._init_repo(self.source_root, "dev")

        self.payloads = {
            "tools/summary.py": "def build_summary(value):\n    return value + 1\n",
            "tools/test_summary.py": "def test_summary():\n    assert True\n",
            "tools/checker.py": "def check():\n    return True\n",
        }
        for root in (self.policy_root, self.source_root):
            for relative, content in self.payloads.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

        docs = self.policy_root / "docs/automation"
        docs.mkdir(parents=True)
        self.summary_path = docs / "task-ledger-summary.json"
        self.policy_path = docs / "patch-path-allowlist.json"
        self.write_policy_inputs()
        git(self.policy_root, "add", ".")
        git(self.policy_root, "commit", "-qm", "owner policy fixture")
        git(self.source_root, "add", ".")
        git(self.source_root, "commit", "-qm", "target source fixture")
        self.policy_sha = git(self.policy_root, "rev-parse", "HEAD")
        self.target_sha = git(self.source_root, "rev-parse", "HEAD")

    def _init_repo(self, root: Path, branch: str) -> None:
        git(root, "init", "-q", "-b", branch)
        git(root, "config", "user.name", "Boonta Test")
        git(root, "config", "user.email", "boonta-test@example.invalid")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_policy_inputs(self, *, read_paths=None, write_paths=None) -> None:
        task = {
            "task_id": TASK_ID,
            "title": "Bounded isolated workspace fixture",
            "status": "active",
            "target_branch": "dev",
            "depends_on": [],
            "owner_approved": False,
            "read_paths": list(read_paths if read_paths is not None else READ_PATHS),
        }
        summary = {
            "schema_version": 2,
            "source": "docs/automation/task-ledger.json",
            "updated_at": "2026-11-16",
            "completed_task_ids": [],
            "policy": {
                "max_active_tasks": 1,
                "completed_requires_merged_pr": True,
            },
            "tasks": [task],
        }
        policy = {
            "schema_version": 1,
            "policy": {
                "owner_review_required": True,
                "path_mode": "exact",
                "max_paths_per_task": 20,
            },
            "tasks": [{
                "task_id": TASK_ID,
                "purpose": "Synthetic exact write scope for isolated workspace tests",
                "approval_ref": APPROVAL,
                "allowed_paths": list(write_paths if write_paths is not None else WRITE_PATHS),
            }],
        }
        self.summary_path.write_text(json.dumps(summary), encoding="utf-8")
        self.policy_path.write_text(json.dumps(policy), encoding="utf-8")

    def recommit_policy(self) -> None:
        git(self.policy_root, "add", "docs/automation/task-ledger-summary.json", "docs/automation/patch-path-allowlist.json")
        git(self.policy_root, "commit", "-qm", "update owner scope fixture")
        self.policy_sha = git(self.policy_root, "rev-parse", "HEAD")

    def prepare(self, workspace: Path, **overrides):
        return prepare_workspace(
            policy_root=overrides.get("policy_root", self.policy_root),
            policy_base_sha=overrides.get("policy_base_sha", self.policy_sha),
            source_root=overrides.get("source_root", self.source_root),
            target_base_sha=overrides.get("target_base_sha", self.target_sha),
            task_id=overrides.get("task_id", TASK_ID),
            target_branch=overrides.get("target_branch", "dev"),
            workspace=workspace,
        )


class PrepareAutonomousWorkspaceTests(WorkspaceFixture):
    def test_copies_only_exact_read_paths_and_preserves_owner_write_scope(self):
        workspace = self.parent / "agent-workspace"
        report = self.prepare(workspace)

        self.assertEqual(report["status"], "READY")
        self.assertEqual(report["task_id"], TASK_ID)
        self.assertEqual(report["target_branch"], "dev")
        self.assertEqual(report["read_paths"], READ_PATHS)
        self.assertEqual(report["allowed_write_paths"], WRITE_PATHS)
        self.assertFalse(report["github_credentials_copied"])
        self.assertFalse(report["repository_metadata_copied"])
        self.assertEqual(
            git(workspace, "ls-files").splitlines(),
            sorted(READ_PATHS),
        )
        self.assertEqual(
            git(workspace, "status", "--porcelain=v1", "--untracked-files=all"),
            "",
        )
        for relative, content in self.payloads.items():
            self.assertEqual((workspace / relative).read_text(encoding="utf-8"), content)

    def test_rejects_owner_write_path_missing_from_read_allowlist(self):
        self.write_policy_inputs(
            read_paths=["tools/summary.py", "tools/test_summary.py"],
            write_paths=["tools/summary.py", "tools/checker.py"],
        )
        self.recommit_policy()
        workspace = self.parent / "agent-workspace"
        with self.assertRaisesRegex(WorkspaceError, "must also be in the exact task read allow-list"):
            self.prepare(workspace)
        self.assertFalse(workspace.exists())

    def test_rejects_source_checkout_with_stale_head(self):
        workspace = self.parent / "agent-workspace"
        with self.assertRaisesRegex(WorkspaceError, "differs from the trusted preflight SHA"):
            self.prepare(workspace, target_base_sha="0" * 40)
        self.assertFalse(workspace.exists())

    def test_rejects_dirty_source_checkout(self):
        (self.source_root / "tools/summary.py").write_text("modified\n", encoding="utf-8")
        workspace = self.parent / "agent-workspace"
        with self.assertRaisesRegex(WorkspaceError, "must be clean"):
            self.prepare(workspace)
        self.assertFalse(workspace.exists())

    def test_rejects_wrong_target_branch(self):
        workspace = self.parent / "agent-workspace"
        with self.assertRaisesRegex(WorkspaceError, "target branch"):
            self.prepare(workspace, target_branch="main")
        self.assertFalse(workspace.exists())

    def test_rejects_read_path_missing_from_target_checkout(self):
        self.write_policy_inputs(read_paths=READ_PATHS + ["tools/missing.py"])
        self.recommit_policy()
        workspace = self.parent / "agent-workspace"
        with self.assertRaisesRegex(WorkspaceError, "not one tracked file"):
            self.prepare(workspace)
        self.assertFalse(workspace.exists())

    def test_rejects_preexisting_workspace(self):
        workspace = self.parent / "agent-workspace"
        workspace.mkdir()
        (workspace / "keep.txt").write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(WorkspaceError, "must not already exist"):
            self.prepare(workspace)
        self.assertEqual((workspace / "keep.txt").read_text(encoding="utf-8"), "keep")

    def test_rejects_workspace_nested_inside_source_checkout(self):
        workspace = self.source_root / ".agent-workspace"
        with self.assertRaisesRegex(WorkspaceError, "outside both trusted checkouts"):
            self.prepare(workspace)
        self.assertFalse(workspace.exists())

    def test_rejects_nonexistent_or_duplicate_read_path(self):
        self.write_policy_inputs(read_paths=["tools/summary.py", "tools/summary.py"])
        self.recommit_policy()
        workspace = self.parent / "agent-workspace"
        with self.assertRaisesRegex(WorkspaceError, "duplicates"):
            self.prepare(workspace)
        self.assertFalse(workspace.exists())


if __name__ == "__main__":
    unittest.main()
