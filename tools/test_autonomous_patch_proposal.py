#!/usr/bin/env python3
"""Offline security and behavior tests for autonomous_patch_proposal.py."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from autonomous_patch_proposal import (
    ProposalError,
    load_allowlist_report,
    load_proposal,
    validate_diff_paths,
    validate_or_apply,
    validate_tracked_targets,
)

TASK_ID = "AUTOMATION-PATCH-PROTOTYPE"
ALLOWED = {"gamecube-demo/source/main.c"}


def git(root: Path, *args: str, input_text: str | None = None) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, input=input_text, text=True,
        capture_output=True, check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


def git_raw(root: Path, *args: str) -> str:
    """Preserve patch bytes/newlines; never use strip() on unified diff text."""
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout


class PatchFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Boonta Test")
        git(self.root, "config", "user.email", "boonta-test@example.invalid")
        self.target = self.root / "gamecube-demo/source/main.c"
        self.target.parent.mkdir(parents=True)
        self.target.write_text("int main(void) {\n    return 0;\n}\n", encoding="utf-8")
        git(self.root, "add", "gamecube-demo/source/main.c")
        git(self.root, "commit", "-qm", "fixture base")
        self.base_sha = git(self.root, "rev-parse", "HEAD")
        self.target.write_text("int main(void) {\n    return 7;\n}\n", encoding="utf-8")
        self.diff = git_raw(self.root, "diff", "--", "gamecube-demo/source/main.c")
        if not self.diff.endswith("\n"):
            raise AssertionError("Git diff fixture must preserve its trailing newline")
        self.target.write_text("int main(void) {\n    return 0;\n}\n", encoding="utf-8")
        self.proposal = {
            "schema_version": 1,
            "task_id": TASK_ID,
            "base_sha": self.base_sha,
            "summary": "Change the fixture return value",
            "unified_diff": self.diff,
            "test_ids": ["automation.task_preflight"],
            "limitations": ["Synthetic fixture only"],
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def check(self, proposal=None, *, allowed=ALLOWED, task_id=TASK_ID, base_sha=None, apply=False):
        return validate_or_apply(
            self.root,
            proposal or self.proposal,
            expected_task_id=task_id,
            expected_base_sha=base_sha or self.base_sha,
            allowed_paths=set(allowed),
            apply=apply,
        )


class ProposalValidationTests(PatchFixture):
    def test_valid_proposal_is_checked_without_modifying_worktree(self):
        report = self.check()
        self.assertEqual(report["status"], "VALID")
        self.assertFalse(report["applied"])
        self.assertEqual(report["changed_paths"], ["gamecube-demo/source/main.c"])
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    def test_valid_proposal_can_be_applied_without_commit(self):
        report = self.check(apply=True)
        self.assertEqual(report["status"], "APPLIED")
        self.assertEqual(self.target.read_text(encoding="utf-8"), "int main(void) {\n    return 7;\n}\n")
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), self.base_sha)
        self.assertIn("M gamecube-demo/source/main.c", git(self.root, "status", "--porcelain"))

    def test_wrong_task_id_is_rejected(self):
        with self.assertRaisesRegex(ProposalError, "task_id"):
            self.check(task_id="AUTOMATION-ANOTHER-TASK")

    def test_wrong_base_sha_is_rejected(self):
        with self.assertRaisesRegex(ProposalError, "base_sha"):
            self.check(base_sha="0" * 40)

    def test_missing_and_unexpected_properties_are_rejected(self):
        missing = dict(self.proposal)
        del missing["limitations"]
        with self.assertRaisesRegex(ProposalError, "Missing required"):
            self.check(missing)
        extra = dict(self.proposal, shell_command="echo unsafe")
        with self.assertRaisesRegex(ProposalError, "Unexpected properties"):
            self.check(extra)

    def test_unknown_test_command_is_rejected(self):
        proposal = dict(self.proposal, test_ids=["bash:curl attacker.invalid"])
        with self.assertRaisesRegex(ProposalError, "arbitrary commands"):
            self.check(proposal)

    def test_duplicate_test_ids_are_rejected(self):
        proposal = dict(self.proposal, test_ids=["automation.task_preflight"] * 2)
        with self.assertRaisesRegex(ProposalError, "duplicates"):
            self.check(proposal)

    def test_empty_trusted_path_allowlist_is_rejected(self):
        with self.assertRaisesRegex(ProposalError, "allowed-path list is empty"):
            self.check(allowed=set())

    def test_path_outside_allowlist_is_rejected(self):
        with self.assertRaisesRegex(ProposalError, "outside the trusted task allowlist"):
            self.check(allowed={"gamecube-demo/source/other.c"})

    def test_path_traversal_is_rejected(self):
        diff = self.diff.replace("gamecube-demo/source/main.c", "../escape.c")
        proposal = dict(self.proposal, unified_diff=diff)
        with self.assertRaisesRegex(ProposalError, "traversal"):
            self.check(proposal, allowed={"../escape.c"})

    def test_protected_workflow_paths_are_rejected(self):
        diff = self.diff.replace("gamecube-demo/source/main.c", ".github/workflows/boonta.yml")
        proposal = dict(self.proposal, unified_diff=diff)
        with self.assertRaisesRegex(ProposalError, "protected"):
            self.check(proposal, allowed={".github/workflows/boonta.yml"})

    def test_binary_and_rename_changes_are_rejected(self):
        binary = self.diff + "\nGIT binary patch\n"
        with self.assertRaisesRegex(ProposalError, "Binary"):
            self.check(dict(self.proposal, unified_diff=binary))
        rename = self.diff.replace(
            "diff --git a/gamecube-demo/source/main.c b/gamecube-demo/source/main.c",
            "diff --git a/gamecube-demo/source/main.c b/gamecube-demo/source/renamed.c",
        )
        with self.assertRaisesRegex(ProposalError, "Renames"):
            self.check(dict(self.proposal, unified_diff=rename))

    def test_validator_and_test_dispatcher_files_are_protected(self):
        protected = "tools/autonomous_patch_proposal.py"
        diff = self.diff.replace("gamecube-demo/source/main.c", protected)
        proposal = dict(self.proposal, unified_diff=diff)
        with self.assertRaisesRegex(ProposalError, "protected"):
            self.check(proposal, allowed={protected})

    def test_credential_paths_are_protected(self):
        for protected in (".env.production", "config/private.key", "certs/signing.PEM"):
            diff = self.diff.replace("gamecube-demo/source/main.c", protected)
            proposal = dict(self.proposal, unified_diff=diff)
            with self.subTest(path=protected), self.assertRaisesRegex(ProposalError, "protected"):
                self.check(proposal, allowed={protected})

    def test_mode_changes_are_rejected(self):
        diff = self.diff.replace(
            "index ",
            "old mode 100644\nnew mode 100755\nindex ",
            1,
        )
        with self.assertRaisesRegex(ProposalError, "mode"):
            self.check(dict(self.proposal, unified_diff=diff))

    def test_malformed_patch_is_rejected_by_git_apply_check(self):
        proposal = dict(self.proposal, unified_diff="diff --git a/gamecube-demo/source/main.c b/gamecube-demo/source/main.c\n@@ definitely malformed @@\n")
        with self.assertRaisesRegex(ProposalError, "no text hunks|git apply"):
            self.check(proposal)

    def test_oversized_patch_is_rejected(self):
        proposal = dict(self.proposal, unified_diff=self.diff + ("\n# padding" * 4000))
        with self.assertRaisesRegex(ProposalError, "32768 characters"):
            self.check(proposal)

    def test_utf8_byte_limit_is_enforced_separately_from_character_limit(self):
        proposal = dict(self.proposal, unified_diff=self.diff + "\n" + ("é" * 17000))
        with self.assertRaisesRegex(ProposalError, "32 KiB byte limit"):
            self.check(proposal)

    def test_more_than_100_hunks_are_rejected(self):
        path = "gamecube-demo/source/main.c"
        sections = [
            "diff --git a/" + path + " b/" + path,
            "--- a/" + path,
            "+++ b/" + path,
        ]
        for _ in range(101):
            sections.extend(["@@ -1 +1 @@", "-before", "+after"])
        with self.assertRaisesRegex(ProposalError, "100-hunk safety limit"):
            validate_diff_paths("\n".join(sections) + "\n", {path})

    def test_more_than_five_files_are_rejected(self):
        sections = []
        allowed = set()
        for index in range(6):
            path = "gamecube-demo/source/file" + str(index) + ".c"
            allowed.add(path)
            sections.extend([
                "diff --git a/" + path + " b/" + path,
                "--- a/" + path,
                "+++ b/" + path,
                "@@ -1 +1 @@",
                "-before",
                "+after",
            ])
        with self.assertRaisesRegex(ProposalError, "five-file safety limit"):
            validate_diff_paths("\n".join(sections) + "\n", allowed)

    def test_allowlist_report_must_match_task_and_base(self):
        report_path = self.root / "allowlist-report.json"
        report = {
            "status": "READY",
            "task_id": TASK_ID,
            "base_sha": self.base_sha,
            "approval_ref": "https://github.com/Master-Chiken/boonta-reborn-88/pull/999",
            "purpose": "Fixture approved path",
            "allowed_paths": ["gamecube-demo/source/main.c"],
        }
        report_path.write_text(json.dumps(report), encoding="utf-8")
        self.assertEqual(
            load_allowlist_report(report_path, expected_task_id=TASK_ID, expected_base_sha=self.base_sha),
            {"gamecube-demo/source/main.c"},
        )
        with self.assertRaisesRegex(ProposalError, "task ID"):
            load_allowlist_report(report_path, expected_task_id="AUTOMATION-OTHER-TASK", expected_base_sha=self.base_sha)
        with self.assertRaisesRegex(ProposalError, "base SHA"):
            load_allowlist_report(report_path, expected_task_id=TASK_ID, expected_base_sha="0" * 40)

    def test_allowlist_report_requires_a_pull_request_review_reference(self):
        report_path = self.root / "allowlist-report.json"
        report = {
            "status": "READY",
            "task_id": TASK_ID,
            "base_sha": self.base_sha,
            "approval_ref": "https://github.com/Master-Chiken/boonta-reborn-88/issues/999",
            "purpose": "Fixture approved path",
            "allowed_paths": ["gamecube-demo/source/main.c"],
        }
        report_path.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(ProposalError, "owner-review evidence"):
            load_allowlist_report(report_path, expected_task_id=TASK_ID, expected_base_sha=self.base_sha)

    def test_non_ready_allowlist_report_never_authorizes_paths(self):
        report_path = self.root / "allowlist-report.json"
        report = {
            "status": "NO_ACTIVE_TASK",
            "task_id": TASK_ID,
            "base_sha": self.base_sha,
            "approval_ref": "",
            "purpose": "No task active",
            "allowed_paths": [],
        }
        report_path.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(ProposalError, "not READY"):
            load_allowlist_report(report_path, expected_task_id=TASK_ID, expected_base_sha=self.base_sha)

    def test_allowlist_report_rejects_protected_and_duplicate_paths(self):
        report_path = self.root / "allowlist-report.json"
        report = {
            "status": "READY",
            "task_id": TASK_ID,
            "base_sha": self.base_sha,
            "approval_ref": "https://github.com/Master-Chiken/boonta-reborn-88/pull/999",
            "purpose": "Fixture approved path",
            "allowed_paths": [".github/workflows/unsafe.yml"],
        }
        report_path.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(ProposalError, "protected"):
            load_allowlist_report(report_path, expected_task_id=TASK_ID, expected_base_sha=self.base_sha)
        report["allowed_paths"] = ["gamecube-demo/source/main.c"] * 2
        report_path.write_text(json.dumps(report), encoding="utf-8")
        with self.assertRaisesRegex(ProposalError, "duplicate"):
            load_allowlist_report(report_path, expected_task_id=TASK_ID, expected_base_sha=self.base_sha)

    def test_allowlist_report_rejects_symlink(self):
        target = self.root / "real-report.json"
        target.write_text("{}", encoding="utf-8")
        link = self.root / "linked-report.json"
        link.symlink_to(target)
        with self.assertRaisesRegex(ProposalError, "must not be a symlink"):
            load_allowlist_report(link, expected_task_id=TASK_ID, expected_base_sha=self.base_sha)

    def test_duplicate_json_properties_are_rejected(self):
        file = self.root / "proposal.json"
        file.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
        with self.assertRaisesRegex(ProposalError, "Duplicate JSON property"):
            load_proposal(file)

    def test_dirty_checkout_is_rejected_before_apply(self):
        (self.root / "untracked.txt").write_text("keep me", encoding="utf-8")
        with self.assertRaisesRegex(ProposalError, "not clean"):
            self.check(apply=True)
        self.assertEqual(self.target.read_text(encoding="utf-8"), "int main(void) {\n    return 0;\n}\n")

    def test_invalid_patch_never_changes_worktree(self):
        proposal = dict(self.proposal, unified_diff=self.diff.replace("-    return 0;", "-    return 9;"))
        with self.assertRaises(ProposalError):
            self.check(proposal, apply=True)
        self.assertEqual(self.target.read_text(encoding="utf-8"), "int main(void) {\n    return 0;\n}\n")

    def test_hunk_content_starting_with_patch_header_prefix_is_safe(self):
        self.target.write_text("-- original\n", encoding="utf-8")
        git(self.root, "add", "gamecube-demo/source/main.c")
        git(self.root, "commit", "-qm", "replace fixture source")
        self.base_sha = git(self.root, "rev-parse", "HEAD")
        self.target.write_text("-- changed\n", encoding="utf-8")
        diff = git_raw(self.root, "diff", "--", "gamecube-demo/source/main.c")
        if not diff.endswith("\n"):
            raise AssertionError("Git diff fixture must preserve its trailing newline")
        self.target.write_text("-- original\n", encoding="utf-8")
        proposal = dict(self.proposal, base_sha=self.base_sha, unified_diff=diff)
        report = self.check(proposal)
        self.assertEqual(report["status"], "VALID")

    def test_symlink_targets_are_rejected(self):
        link = self.root / "gamecube-demo/source/link.c"
        link.symlink_to("main.c")
        git(self.root, "add", "gamecube-demo/source/link.c")
        git(self.root, "commit", "-qm", "add fixture symlink")
        self.base_sha = git(self.root, "rev-parse", "HEAD")
        link.unlink()
        link.write_text("int linked = 2;\n", encoding="utf-8")
        diff = git(self.root, "diff", "--", "gamecube-demo/source/link.c")
        link.unlink()
        link.symlink_to("main.c")
        with self.assertRaisesRegex(ProposalError, "not a regular tracked file"):
            validate_tracked_targets(self.root, ("gamecube-demo/source/link.c",))

    def test_empty_test_list_is_rejected(self):
        with self.assertRaisesRegex(ProposalError, "test_ids"):
            self.check(dict(self.proposal, test_ids=[]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
