from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from build_autonomous_context import ContextBuildError, build_context


class BuildAutonomousContextTests(unittest.TestCase):
    def make_repo(self, root: Path, tasks: list[dict] | None = None) -> None:
        (root / "docs" / "automation").mkdir(parents=True)
        reverse = """# Reverse-engineering first
        DISCOVER → VERIFY → EXTRACT/CONVERT/REUSE → INTEGRATE → TEST.
        The native GameCube/Wii target is not the same as PC or N64.
        """
        budget = """# Budget
        One model provider invocation at most per Boonta Autonomous Loop run.
        €0 only. Keep newly retrieved text below 1,500 tokens.
        """
        (root / "docs" / "REVERSE_ENGINEERING_FIRST.md").write_text(reverse, encoding="utf-8")
        (root / "docs" / "automation" / "AUTONOMOUS_CONTEXT_BUDGET.md").write_text(
            budget, encoding="utf-8"
        )
        summary = {
            "schema_version": 1,
            "updated_at": "2026-11-08",
            "policy": {
                "max_active_tasks": 1,
                "completed_requires_merged_pr": True,
            },
            "tasks": tasks or [],
        }
        (root / "docs" / "automation" / "task-ledger-summary.json").write_text(
            json.dumps(summary), encoding="utf-8"
        )

    def test_real_repository_context_is_bounded_and_contains_safety_rules(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        snapshot = build_context(repo_root, max_chars=1200)
        self.assertLessEqual(len(snapshot), 1200)
        self.assertIn("DISCOVER", snapshot)
        self.assertIn("PC/x86, N64/MIPS", snapshot)
        self.assertIn("€0 only", snapshot)
        self.assertIn("max active tasks=1", snapshot)

    def test_includes_active_and_blocked_task_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root, [
                {
                    "task_id": "PC-UPSTREAM-42-COMMIT-RECONCILIATION",
                    "title": "Reconcile source history",
                    "status": "active",
                    "next_action_excerpt": "Triage exact upstream commits in small, reviewed batches.",
                },
                {
                    "task_id": "N64-PUPP-T2",
                    "title": "Owner-local parser probe",
                    "status": "blocked",
                    "next_action_excerpt": "Install the pinned SDK locally and run the parser-only probe.",
                },
            ])
            snapshot = build_context(root, max_chars=1200)
            self.assertIn("PC-UPSTREAM-42-COMMIT-RECONCILIATION [active]", snapshot)
            self.assertIn("N64-PUPP-T2 [blocked]", snapshot)

    def test_fails_closed_on_multiple_actionable_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root, [
                {"task_id": "A", "status": "active", "title": "First task"},
                {"task_id": "B", "status": "in_review", "title": "Second task"},
            ])
            with self.assertRaisesRegex(ContextBuildError, "Single-writer policy violated"):
                build_context(root)

    def test_fails_closed_on_inconsistent_ledger_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            summary_path = root / "docs" / "automation" / "task-ledger-summary.json"
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            summary["policy"]["max_active_tasks"] = 2
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            with self.assertRaisesRegex(ContextBuildError, "single-writer/completion policy"):
                build_context(root)

    def test_rejects_unreasonably_small_output_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_repo(root)
            with self.assertRaisesRegex(ContextBuildError, "at least 600"):
                build_context(root, max_chars=500)


if __name__ == "__main__":
    unittest.main()
