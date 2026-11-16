#!/usr/bin/env python3
"""Offline regression tests for exporting exact-path workspace diffs."""
from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from build_autonomous_patch_proposal import PatchBuildError, build_patch_proposal

TASK_ID = "AUTONOMOUS-PATCH-EXPORT"
BASE_SHA = "a" * 40
READ_PATHS = ["src/main.c", "tests/test_main.c", "docs/readme.md"]
ALLOWED = ["src/main.c", "tests/test_main.c"]
TEST_IDS = ["automation.task_preflight", "automation.provider_handoff"]


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, stdin=subprocess.DEVNULL,
        text=True, capture_output=True, check=False, timeout=20,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class PatchExportFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="boonta-patch-export-")
        self.parent = Path(self.temp.name).resolve()
        self.workspace = self.parent / "workspace"
        self.baseline = self.parent / "baseline"
        self.workspace.mkdir()
        self.baseline.mkdir()
        git(self.baseline, "init", "-q", "-b", "agent-work")
        git(self.baseline, "config", "user.name", "Boonta Test")
        git(self.baseline, "config", "user.email", "boonta-test@example.invalid")
        self.payloads = {
            "src/main.c": "int main(void) { return 0; }\n",
            "tests/test_main.c": "int test_main(void) { return 1; }\n",
            "docs/readme.md": "read only context\n",
        }
        for relative, content in self.payloads.items():
            baseline_file = self.baseline / relative
            baseline_file.parent.mkdir(parents=True, exist_ok=True)
            baseline_file.write_text(content, encoding="utf-8")
            baseline_file.chmod(0o644)
            workspace_file = self.workspace / relative
            workspace_file.parent.mkdir(parents=True, exist_ok=True)
            workspace_file.write_text(content, encoding="utf-8")
            workspace_file.chmod(0o644 if relative in ALLOWED else 0o444)
        for current, _dirs, _files in os.walk(self.workspace, topdown=False):
            Path(current).chmod(0o555)
        self.workspace.chmod(0o555)
        git(self.baseline, "add", ".")
        git(self.baseline, "commit", "-qm", "trusted patch baseline")
        self.scratch_sha = git(self.baseline, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def proposal(self, output: Path | None = None, **kwargs):
        return build_patch_proposal(
            workspace=kwargs.get("workspace", self.workspace),
            baseline_root=kwargs.get("baseline_root", self.baseline),
            expected_scratch_base_sha=kwargs.get("expected_scratch_base_sha", self.scratch_sha),
            expected_task_id=kwargs.get("expected_task_id", TASK_ID),
            expected_base_sha=kwargs.get("expected_base_sha", BASE_SHA),
            read_paths=kwargs.get("read_paths", READ_PATHS),
            allowed_paths=kwargs.get("allowed_paths", ALLOWED),
            test_ids=kwargs.get("test_ids", TEST_IDS),
            summary=kwargs.get("summary", "Update the source and its regression test"),
            output_path=output,
        )

    def change(self, relative: str, content: str) -> None:
        target = self.workspace / relative
        parent = target.parent
        parent.chmod(0o755)
        self.workspace.chmod(0o755)
        target.chmod(0o644)
        target.write_text(content, encoding="utf-8")
        for current, _dirs, _files in os.walk(self.workspace, topdown=False):
            Path(current).chmod(0o555)
        self.workspace.chmod(0o555)

    def test_exports_valid_diff_using_private_baseline_and_trusted_metadata(self):
        self.change("src/main.c", "int main(void) { return 42; }\n")
        output = self.parent / "proposal.json"
        report = self.proposal(output)
        self.assertEqual(report["status"], "PROPOSAL_READY")
        self.assertEqual(report["changed_paths"], ["src/main.c"])
        self.assertEqual(report["test_ids"], TEST_IDS)
        self.assertTrue(output.is_file())
        content = output.read_text(encoding="utf-8")
        self.assertIn('"task_id": "' + TASK_ID + '"', content)
        self.assertIn('"base_sha": "' + BASE_SHA + '"', content)
        self.assertIn("return 42", content)
        self.assertNotIn("docs/readme.md", content)
        self.assertFalse((self.workspace / ".git").exists())

    def test_rejects_modified_read_only_context_even_if_permissions_were_changed(self):
        docs_dir = self.workspace / "docs"
        self.workspace.chmod(0o755)
        docs_dir.chmod(0o755)
        readme = docs_dir / "readme.md"
        readme.chmod(0o644)
        readme.write_text("changed outside scope\n", encoding="utf-8")
        readme.chmod(0o444)
        for current, _dirs, _files in os.walk(self.workspace, topdown=False):
            Path(current).chmod(0o555)
        self.workspace.chmod(0o555)
        with self.assertRaisesRegex(PatchBuildError, "Read-only context file was modified"):
            self.proposal()

    def test_rejects_extra_file_created_in_workspace(self):
        tools_dir = self.workspace / "src"
        self.workspace.chmod(0o755)
        tools_dir.chmod(0o755)
        (tools_dir / "new-file.c").write_text("int new_file;\n", encoding="utf-8")
        for current, _dirs, _files in os.walk(self.workspace, topdown=False):
            Path(current).chmod(0o555)
        self.workspace.chmod(0o555)
        with self.assertRaisesRegex(PatchBuildError, "outside the exact read-path list"):
            self.proposal()

    def test_rejects_symlink_in_workspace(self):
        self.workspace.chmod(0o755)
        docs_dir = self.workspace / "docs"
        docs_dir.chmod(0o755)
        (docs_dir / "readme.md").unlink()
        (docs_dir / "readme.md").symlink_to(self.baseline / "docs/readme.md")
        for current, _dirs, _files in os.walk(self.workspace, topdown=False):
            Path(current).chmod(0o555)
        self.workspace.chmod(0o555)
        with self.assertRaisesRegex(PatchBuildError, "symlink"):
            self.proposal()

    def test_rejects_stale_private_baseline_sha(self):
        self.change("src/main.c", "int main(void) { return 42; }\n")
        with self.assertRaisesRegex(PatchBuildError, "HEAD differs"):
            self.proposal(expected_scratch_base_sha="0" * 40)

    def test_rejects_noop_workspace(self):
        with self.assertRaisesRegex(PatchBuildError, "no changes to any owner-approved"):
            self.proposal()

    def test_rejects_duplicate_or_invalid_fixed_test_ids(self):
        self.change("src/main.c", "int main(void) { return 42; }\n")
        with self.assertRaisesRegex(PatchBuildError, "empty, duplicated or too large"):
            self.proposal(test_ids=[TEST_IDS[0], TEST_IDS[0]])

    def test_rejects_write_allowlist_outside_read_paths(self):
        self.change("src/main.c", "int main(void) { return 42; }\n")
        with self.assertRaisesRegex(PatchBuildError, "exceed the exact task read-path list"):
            self.proposal(allowed_paths=["src/main.c", "src/new.c"])

    def test_rejects_proposal_output_inside_workspace_or_baseline(self):
        self.change("src/main.c", "int main(void) { return 42; }\n")
        with self.assertRaisesRegex(PatchBuildError, "outside both model workspace"):
            self.proposal(output=self.workspace / "proposal.json")


if __name__ == "__main__":
    unittest.main()
