#!/usr/bin/env python3
"""Offline tests for trusted-main/task-target autonomous agent input preparation."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from check_task_ledger_summary import build_summary
from prepare_autonomous_agent_inputs import (
    AgentInputError,
    _compact_c_source_lines,
    _validate_read_contract,
    prepare_agent_inputs,
)

TASK_ID = "GC-RIVAL-ROUTE-PROGRESSION"
PREREQUISITE_ID = "GC-RACE-PROGRESSION"
APPROVAL = "https://github.com/Master-Chiken/boonta-reborn-88/pull/400"
SOURCE_PATH = "src/main.c"


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, stdin=subprocess.DEVNULL,
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class AgentInputFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="boonta-agent-inputs-")
        self.parent = Path(self.temp.name).resolve()
        self.source = self.parent / "dev-source"
        self.policy = self.parent / "trusted-main"
        self.output = self.parent / "allowlist.json"
        self.source.mkdir()
        self.policy.mkdir()
        for root, name, email in (
            (self.source, "Boonta Target", "target@example.invalid"),
            (self.policy, "Boonta Main", "main@example.invalid"),
        ):
            git(root, "init", "-q")
            git(root, "config", "user.name", name)
            git(root, "config", "user.email", email)

        target_file = self.source / SOURCE_PATH
        target_file.parent.mkdir(parents=True)
        target_file.write_text("int main(void) {\n  return 1;\n}\n", encoding="utf-8")
        git(self.source, "add", "src")
        git(self.source, "commit", "-qm", "dev target source")
        self.base_sha = git(self.source, "rev-parse", "HEAD")

        docs = self.policy / "docs/automation"
        docs.mkdir(parents=True)
        prerequisite = {
            "task_id": PREREQUISITE_ID,
            "title": "Race progression",
            "owner_role_id": "gameplay",
            "parent_objective_id": "BOONTA-COMPLETE-GAME",
            "depends_on": [],
            "owner_approved": True,
            "queue": "#226",
            "platform_scope": ["GameCube", "Wii"],
            "status": "completed",
            "target_branch": "dev",
            "read_paths": [],
            "read_ranges": [],
            "question": "Completed prerequisite",
            "acceptance_criteria": ["Race loop works"],
            "next_action": "Completed",
        }
        selected = {
            "task_id": TASK_ID,
            "title": "Rival route progress",
            "owner_role_id": "gameplay",
            "parent_objective_id": "BOONTA-COMPLETE-GAME",
            "status": "queued",
            "owner_approved": True,
            "target_branch": "dev",
            "depends_on": [PREREQUISITE_ID],
            "queue": "#226",
            "platform_scope": ["GameCube", "Wii"],
            "read_paths": [SOURCE_PATH],
            "read_ranges": [{"path": SOURCE_PATH, "start_line": 1, "end_line": 3}],
            "question": "Can rivals use native route progress?",
            "acceptance_criteria": ["Rivals finish deterministically"],
            "next_action": "Trace the current route cursor and implement bounded progress",
        }
        self.full_ledger = {
            "schema_version": 1,
            "updated_at": "2026-11-16",
            "policy": {"max_active_tasks": 1},
            "tasks": [prerequisite, selected],
        }
        self.summary_path = docs / "task-ledger-summary.json"
        self.ledger_path = docs / "task-ledger.json"
        self.policy_path = docs / "patch-path-allowlist.json"
        self.policy_doc = {
            "schema_version": 1,
            "policy": {
                "owner_review_required": True,
                "path_mode": "exact",
                "max_paths_per_task": 20,
            },
            "tasks": [{
                "task_id": TASK_ID,
                "purpose": "Owner-approved route-progress change",
                "approval_ref": APPROVAL,
                "allowed_paths": [SOURCE_PATH],
            }],
        }
        self._write_trusted_files()
        git(self.policy, "add", "docs/automation")
        git(self.policy, "commit", "-qm", "trusted main task and path policy")
        self.policy_sha = git(self.policy, "rev-parse", "HEAD")

    def _write_trusted_files(self) -> None:
        self.ledger_path.write_text(json.dumps(self.full_ledger), encoding="utf-8")
        self.summary = build_summary(self.full_ledger)
        self.summary_path.write_text(
            json.dumps(self.summary, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self.policy_path.write_text(json.dumps(self.policy_doc), encoding="utf-8")

    def commit_ledger_change(self, message: str) -> None:
        self._write_trusted_files()
        git(self.policy, "add", "docs/automation")
        git(self.policy, "commit", "-qm", message)
        self.policy_sha = git(self.policy, "rev-parse", "HEAD")

    def prepare(self, **overrides):
        return prepare_agent_inputs(
            self.source,
            self.policy,
            expected_base_sha=overrides.pop("expected_base_sha", self.base_sha),
            expected_policy_sha=overrides.pop("expected_policy_sha", self.policy_sha),
            task_id=overrides.pop("task_id", TASK_ID),
            allowlist_output=overrides.pop("allowlist_output", self.output),
            **overrides,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()


class AgentInputTests(AgentInputFixture):
    def test_ready_inputs_bind_exact_source_policy_and_task(self):
        report = self.prepare()
        self.assertEqual(report["task_id"], TASK_ID)
        self.assertEqual(report["target_branch"], "dev")
        self.assertEqual(report["base_sha"], self.base_sha)
        self.assertEqual(report["policy_sha"], self.policy_sha)
        self.assertEqual(report["read_paths"], [SOURCE_PATH])
        self.assertEqual(report["read_ranges"], [{
            "path": SOURCE_PATH, "start_line": 1, "end_line": 3,
        }])
        self.assertEqual(report["allowed_paths"], [SOURCE_PATH])
        self.assertEqual(report["approval_ref"], APPROVAL)
        self.assertFalse(report["model_has_github_write_tools"])
        self.assertEqual(json.loads(Path(report["allowlist_report"]).read_text())["allowed_paths"], [SOURCE_PATH])
        self.assertEqual(git(self.source, "status", "--porcelain"), "")
        self.assertEqual(git(self.policy, "status", "--porcelain"), "")

    def test_source_read_budget_estimate_is_returned(self):
        report = self.prepare()
        self.assertGreater(report["source_read_chars"], 1200)
        self.assertEqual(
            report["source_read_tokens_estimate"],
            (report["source_read_chars"] + 3) // 4,
        )

    def test_preloaded_source_context_is_exact_bounded_and_digest_bound(self):
        report = self.prepare()
        source_context = report["source_context"]
        self.assertIn("FILE: " + SOURCE_PATH, source_context)
        self.assertIn("[1-3]", source_context)
        self.assertIn("int main", source_context)
        self.assertEqual(report["source_context_chars"], len(source_context))
        self.assertEqual(
            report["source_context_tokens_estimate"],
            (len(source_context) + 3) // 4,
        )
        self.assertRegex(report["source_context_sha256"], r"^[a-f0-9]{64}$")
        self.assertNotIn("comment that should be removed", source_context)

    def test_c_source_compaction_drops_comments_but_preserves_quoted_urls(self):
        compacted = _compact_c_source_lines([
            "/* block comment starts",
            " * model context should omit this",
            " */",
            'const char *url = "https://example.invalid/a//b"; // trailing note',
            "return 1;",
        ])
        self.assertEqual(
            compacted,
            [
                "",
                "",
                "",
                'const char *url = "https://example.invalid/a//b";',
                "return 1;",
            ],
        )

    def test_accepts_six_unique_read_paths(self):
        paths = [SOURCE_PATH]
        for index in range(5):
            path = f"src/extra{index}.c"
            (self.source / path).write_text(f"int extra{index}(void) {{ return {index}; }}\n", encoding="utf-8")
            paths.append(path)
        task = {
            "read_paths": paths,
            "read_ranges": [{"path": path, "start_line": 1, "end_line": 1} for path in paths],
        }
        validated_paths, validated_ranges = _validate_read_contract(self.source, task)
        self.assertEqual(validated_paths, paths)
        self.assertEqual(len(validated_ranges), 6)

    def test_rejects_seven_read_paths(self):
        paths = [SOURCE_PATH]
        for index in range(6):
            path = f"src/extra{index}.c"
            (self.source / path).write_text(f"int extra{index}(void) {{ return {index}; }}\n", encoding="utf-8")
            paths.append(path)
        task = {
            "read_paths": paths,
            "read_ranges": [{"path": path, "start_line": 1, "end_line": 1} for path in paths],
        }
        with self.assertRaisesRegex(AgentInputError, "1-6 unique exact read_paths"):
            _validate_read_contract(self.source, task)

    def test_stale_target_sha_is_rejected(self):
        with self.assertRaisesRegex(AgentInputError, "selected task base SHA"):
            self.prepare(expected_base_sha="0" * 40)

    def test_stale_trusted_policy_sha_is_rejected(self):
        with self.assertRaisesRegex(AgentInputError, "policy SHA"):
            self.prepare(expected_policy_sha="0" * 40)

    def test_selected_task_absent_from_trusted_main_is_rejected(self):
        with self.assertRaisesRegex(AgentInputError, "exactly once"):
            self.prepare(task_id="GC-NOT-IN-LEDGER")

    def test_incomplete_task_dependency_does_not_grant_write_paths(self):
        self.full_ledger["tasks"][0]["status"] = "queued"
        self.full_ledger["tasks"][0]["owner_approved"] = False
        self.commit_ledger_change("remove completed prerequisite")
        with self.assertRaisesRegex(AgentInputError, "not READY|dependency"):
            self.prepare(expected_policy_sha=self.policy_sha)

    def test_missing_exact_line_ranges_are_rejected(self):
        self.full_ledger["tasks"][1]["read_ranges"] = []
        self.commit_ledger_change("remove source ranges")
        with self.assertRaisesRegex(AgentInputError, "1-13 exact read_ranges"):
            self.prepare(expected_policy_sha=self.policy_sha)

    def test_range_cannot_escape_exact_read_paths(self):
        self.full_ledger["tasks"][1]["read_ranges"][0]["path"] = "src/other.c"
        self.commit_ledger_change("widen source range")
        with self.assertRaisesRegex(AgentInputError, "exact bounded source contract"):
            self.prepare(expected_policy_sha=self.policy_sha)

    def test_read_path_traversal_is_rejected_before_filesystem_walk(self):
        self.full_ledger["tasks"][1]["read_paths"] = ["../outside.txt"]
        self.full_ledger["tasks"][1]["read_ranges"] = [{
            "path": "../outside.txt", "start_line": 1, "end_line": 1,
        }]
        self.commit_ledger_change("reject traversal read path")
        with self.assertRaisesRegex(AgentInputError, "traversal"):
            self.prepare(expected_policy_sha=self.policy_sha)
        self.assertFalse(self.output.exists())

    def test_absolute_and_ambiguous_read_paths_are_rejected(self):
        for unsafe in ("/etc/passwd", "src\\\\main.c", "src//main.c", "src/./main.c"):
            with self.subTest(path=unsafe):
                self.full_ledger["tasks"][1]["read_paths"] = [unsafe]
                self.full_ledger["tasks"][1]["read_ranges"] = [{
                    "path": unsafe, "start_line": 1, "end_line": 1,
                }]
                self.commit_ledger_change("reject unsafe read path")
                with self.assertRaisesRegex(AgentInputError, "read path|Read path"):
                    self.prepare(expected_policy_sha=self.policy_sha)
                self.output.unlink(missing_ok=True)

    def test_non_string_read_path_is_rejected_without_type_error(self):
        self.full_ledger["tasks"][1]["read_paths"] = [{"path": SOURCE_PATH}]
        self.full_ledger["tasks"][1]["read_ranges"] = [{
            "path": {"path": SOURCE_PATH}, "start_line": 1, "end_line": 1,
        }]
        self.commit_ledger_change("reject non-string read path")
        with self.assertRaisesRegex(AgentInputError, "read_paths"):
            self.prepare(expected_policy_sha=self.policy_sha)

    def test_range_budget_is_bounded(self):
        self.full_ledger["tasks"][1]["read_ranges"] = [
            {"path": SOURCE_PATH, "start_line": start, "end_line": start + 79}
            for start in (1, 81, 161, 241, 321, 401)
        ]
        self.commit_ledger_change("exceed 432-line aggregate budget")
        with self.assertRaisesRegex(AgentInputError, "432-line aggregate cap"):
            self.prepare(expected_policy_sha=self.policy_sha)

    def test_read_range_count_above_thirteen_is_rejected(self):
        self.full_ledger["tasks"][1]["read_ranges"] = [
            {"path": SOURCE_PATH, "start_line": index, "end_line": index}
            for index in range(1, 15)
        ]
        self.commit_ledger_change("reject excessive range count")
        with self.assertRaisesRegex(AgentInputError, "1-13 exact read_ranges"):
            self.prepare(expected_policy_sha=self.policy_sha)

    def test_dirty_source_checkout_is_rejected(self):
        (self.source / "dirty.txt").write_text("not allowed", encoding="utf-8")
        with self.assertRaisesRegex(AgentInputError, "source checkout must be clean"):
            self.prepare()

    def test_modified_canonical_policy_is_rejected(self):
        self.policy_doc["tasks"][0]["purpose"] = "tampered"
        self.policy_path.write_text(json.dumps(self.policy_doc), encoding="utf-8")
        with self.assertRaisesRegex(AgentInputError, "local changes"):
            self.prepare()

    def test_duplicate_output_is_not_overwritten(self):
        self.output.write_text("keep me", encoding="utf-8")
        with self.assertRaisesRegex(AgentInputError, "must be a new"):
            self.prepare()
        self.assertEqual(self.output.read_text(encoding="utf-8"), "keep me")

    def test_every_owner_approved_write_path_must_be_in_task_read_contract(self):
        extra_path = "src/other.c"
        extra = self.source / extra_path
        extra.write_text("int other(void) { return 2; }\\n", encoding="utf-8")
        git(self.source, "add", extra_path)
        git(self.source, "commit", "-qm", "add second writable fixture")
        self.base_sha = git(self.source, "rev-parse", "HEAD")
        self.policy_doc["tasks"][0]["allowed_paths"] = [SOURCE_PATH, extra_path]
        self.commit_ledger_change("approve an unreadable writable path")
        with self.assertRaisesRegex(AgentInputError, "not covered by the task's exact read_paths/read_ranges"):
            self.prepare(expected_policy_sha=self.policy_sha)
        self.assertFalse(self.output.exists())

    def test_write_paths_must_exist_on_the_target_branch(self):
        self.policy_doc["tasks"][0]["allowed_paths"] = ["src/not-tracked.c"]
        self.policy_path.write_text(json.dumps(self.policy_doc), encoding="utf-8")
        git(self.policy, "add", "docs/automation/patch-path-allowlist.json")
        git(self.policy, "commit", "-qm", "approve unavailable target path")
        self.policy_sha = git(self.policy, "rev-parse", "HEAD")
        with self.assertRaisesRegex(AgentInputError, "path policy is not ready|exactly one tracked file"):
            self.prepare(expected_policy_sha=self.policy_sha)


if __name__ == "__main__":
    unittest.main(verbosity=2)
