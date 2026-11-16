#!/usr/bin/env python3
"""Offline regression tests for exporting exact-path workspace diffs."""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from build_autonomous_patch_proposal import PatchBuildError, build_patch_proposal

TASK_ID = "AUTONOMOUS-PATCH-EXPORT"
BASE_SHA = "a" * 40
ALLOWED = ["src/main.c", "tests/test_main.c"]
TEST_IDS = ["automation.task_preflight", "automation.provider_handoff"]


def git(root: Path, *args: str, allowed=(0,)) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, stdin=subprocess.DEVNULL,
        text=True, capture_output=True, check=False, timeout=20,
    )
    if result.returncode not in allowed:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class PatchExportFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="boonta-patch-export-")
        self.parent = Path(self.temp.name).resolve()
        self.workspace = self.parent / "workspace"
        self.workspace.mkdir()
        git(self.workspace, "init", "-q", "-b", "agent-work")
        git(self.workspace, "config", "user.name", "Boonta Test")
        git(self.workspace, "config", "user.email", "boonta-test@example.invalid")
        for relative, content in {
            "src/main.c": "int main(void) { return 0; }\n",
            "tests/test_main.c": "int test_main(void) { return 1; }\n",
            "docs/readme.md": "read only context\n",
        }.items():
            path = self.workspace / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        git(self.workspace, "add", ".")
        git(self.workspace, "commit", "-qm", "scratch baseline")
        self.scratch_sha = git(self.workspace, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def proposal(self, output: Path | None = None, **kwargs):
        return build_patch_proposal(
            workspace=kwargs.get("workspace", self.workspace),
            expected_scratch_base_sha=kwargs.get("expected_scratch_base_sha", self.scratch_sha),
            expected_task_id=kwargs.get("expected_task_id", TASK_ID),
            expected_base_sha=kwargs.get("expected_base_sha", BASE_SHA),
            allowed_paths=kwargs.get("allowed_paths", ALLOWED),
            test_ids=kwargs.get("test_ids", TEST_IDS),
            summary=kwargs.get("summary", "Update the source and its regression test"),
            output_path=output,
        )

    def test_exports_valid_diff_with_trusted_identity_and_fixed_tests(self):
        (self.workspace / "src/main.c").write_text(
            "int main(void) { return 42; }\n", encoding="utf-8",
        )
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

    def test_rejects_changed_path_outside_owner_allowlist(self):
        (self.workspace / "docs/readme.md").write_text("changed outside scope\n", encoding="utf-8")
        with self.assertRaisesRegex(PatchBuildError, "outside the trusted task allowlist"):
            self.proposal()

    def test_rejects_untracked_files(self):
        (self.workspace / "new-file.c").write_text("int new_file;\n", encoding="utf-8")
        with self.assertRaisesRegex(PatchBuildError, "Untracked files are forbidden"):
            self.proposal()

    def test_rejects_staged_changes(self):
        (self.workspace / "src/main.c").write_text("int main(void) { return 42; }\n", encoding="utf-8")
        git(self.workspace, "add", "src/main.c")
        with self.assertRaisesRegex(PatchBuildError, "Staged changes are forbidden"):
            self.proposal()

    def test_rejects_stale_scratch_base_sha(self):
        (self.workspace / "src/main.c").write_text("int main(void) { return 42; }\n", encoding="utf-8")
        with self.assertRaisesRegex(PatchBuildError, "HEAD differs"):
            self.proposal(expected_scratch_base_sha="0" * 40)

    def test_rejects_noop_workspace(self):
        with self.assertRaisesRegex(PatchBuildError, "no tracked source changes"):
            self.proposal()

    def test_rejects_duplicate_or_invalid_fixed_test_ids(self):
        (self.workspace / "src/main.c").write_text("int main(void) { return 42; }\n", encoding="utf-8")
        with self.assertRaisesRegex(PatchBuildError, "empty or duplicated"):
            self.proposal(test_ids=[TEST_IDS[0], TEST_IDS[0]])

    def test_rejects_proposal_output_inside_workspace(self):
        (self.workspace / "src/main.c").write_text("int main(void) { return 42; }\n", encoding="utf-8")
        with self.assertRaisesRegex(PatchBuildError, "stored outside"):
            self.proposal(output=self.workspace / "proposal.json")


if __name__ == "__main__":
    unittest.main()
