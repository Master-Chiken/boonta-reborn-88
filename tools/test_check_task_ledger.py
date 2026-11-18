"""Tests for the persistent Boonta task ledger validator."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).with_name("check_task_ledger.py")
SPEC = importlib.util.spec_from_file_location("check_task_ledger", MODULE_PATH)
ledger = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(ledger)

AUDIT_PATH = Path(__file__).with_name("audit_task_ledger_github.py")
AUDIT_SPEC = importlib.util.spec_from_file_location("audit_task_ledger_github", AUDIT_PATH)
audit = importlib.util.module_from_spec(AUDIT_SPEC)
assert AUDIT_SPEC and AUDIT_SPEC.loader
AUDIT_SPEC.loader.exec_module(audit)

SUMMARY_MODULE_PATH = Path(__file__).with_name("check_task_ledger_summary.py")
SUMMARY_SPEC = importlib.util.spec_from_file_location("check_task_ledger_summary", SUMMARY_MODULE_PATH)
task_summary = importlib.util.module_from_spec(SUMMARY_SPEC)
assert SUMMARY_SPEC and SUMMARY_SPEC.loader
SUMMARY_SPEC.loader.exec_module(task_summary)

CONTEXT_MODULE_PATH = Path(__file__).with_name("build_autonomous_context.py")
CONTEXT_SPEC = importlib.util.spec_from_file_location("build_autonomous_context", CONTEXT_MODULE_PATH)
context_builder = importlib.util.module_from_spec(CONTEXT_SPEC)
assert CONTEXT_SPEC and CONTEXT_SPEC.loader
CONTEXT_SPEC.loader.exec_module(context_builder)


def valid_task(task_id="TASK-001", status="queued"):
    return {
        "task_id": task_id,
        "title": "Bounded research task",
        "queue": "#226",
        "platform_scope": ["GameCube/Wii"],
        "owner_role_id": "research",
        "parent_objective_id": "BOONTA-COMPLETE-GAME",
        "depends_on": [],
        "owner_approved": status == "queued",
        "status": status,
        "question": "What does the pinned evidence establish?",
        "acceptance_criteria": ["Record exact source revision", "Separate facts from unknowns"],
        "evidence": [],
        "next_action": "Inspect the pinned source and update the dossier.",
        "updated_at": "2026-11-04",
    }


def valid_ledger():
    return {
        "schema_version": 1,
        "updated_at": "2026-11-04",
        "policy": {"max_active_tasks": 1},
        "tasks": [valid_task()],
    }


class TaskLedgerTests(unittest.TestCase):
    def test_accepts_valid_ledger(self):
        self.assertEqual(ledger.validate_ledger(valid_ledger()), [])

    def test_rejects_duplicate_ids(self):
        data = valid_ledger()
        data["tasks"].append(valid_task())
        self.assertTrue(any("duplicate task_id" in e for e in ledger.validate_ledger(data)))

    def test_enforces_single_active_task(self):
        data = valid_ledger()
        data["tasks"] = [valid_task("TASK-001", "active"), valid_task("TASK-002", "active")]
        self.assertTrue(any("at most one task" in e for e in ledger.validate_ledger(data)))

    def test_in_review_requires_pr_and_exact_head(self):
        data = valid_ledger()
        task = valid_task(status="in_review")
        task["pr_url"] = "https://github.com/Master-Chiken/boonta-reborn-88/pull/1"
        task["head_sha"] = "abc"
        data["tasks"] = [task]
        errors = ledger.validate_ledger(data)
        self.assertTrue(any("exact 40-character head SHA" in e for e in errors))

    def test_completed_requires_evidence(self):
        data = valid_ledger()
        task = valid_task(status="completed")
        task["pr_url"] = "https://github.com/Master-Chiken/boonta-reborn-88/pull/1"
        task["head_sha"] = "a" * 40
        data["tasks"] = [task]
        errors = ledger.validate_ledger(data)
        self.assertTrue(any("completed task requires evidence" in e for e in errors))

    def test_rejects_missing_platform_scope(self):
        data = valid_ledger()
        data["tasks"][0]["platform_scope"] = []
        self.assertTrue(any("platform_scope" in e for e in ledger.validate_ledger(data)))

    def test_rejects_unknown_owner_role_when_registry_is_supplied(self):
        data = valid_ledger()
        data["tasks"][0]["owner_role_id"] = "unknown-role"
        errors = ledger.validate_ledger(data, {"research"}, {"BOONTA-COMPLETE-GAME"})
        self.assertTrue(any("unknown role" in error for error in errors))

    def test_rejects_unknown_parent_objective_when_registry_is_supplied(self):
        data = valid_ledger()
        data["tasks"][0]["parent_objective_id"] = "UNKNOWN-OBJECTIVE"
        errors = ledger.validate_ledger(data, {"research"}, {"BOONTA-COMPLETE-GAME"})
        self.assertTrue(any("unknown objective" in error for error in errors))

    def test_rejects_queued_task_without_explicit_owner_approval(self):
        data = valid_ledger()
        data["tasks"][0].pop("owner_approved")
        self.assertTrue(any("owner_approved must be true" in error for error in ledger.validate_ledger(data)))

    def test_rejects_unknown_task_dependency(self):
        data = valid_ledger()
        data["tasks"][0]["depends_on"] = ["TASK-404"]
        self.assertTrue(any("depends_on unknown task TASK-404" in error for error in ledger.validate_ledger(data)))

    def test_rejects_dependency_cycles(self):
        first = valid_task("TASK-001")
        second = valid_task("TASK-002")
        first["depends_on"] = ["TASK-002"]
        second["depends_on"] = ["TASK-001"]
        data = valid_ledger()
        data["tasks"] = [first, second]
        self.assertTrue(any("dependency cycle" in error for error in ledger.validate_ledger(data)))

    def test_active_task_requires_completed_dependencies(self):
        dependency = valid_task("TASK-001", "queued")
        active = valid_task("TASK-002", "active")
        active["read_paths"] = ["tools/check_task_ledger.py"]
        active["depends_on"] = ["TASK-001"]
        data = valid_ledger()
        data["tasks"] = [dependency, active]
        self.assertTrue(any("until dependency TASK-001 is completed" in error for error in ledger.validate_ledger(data)))

    def test_queued_task_may_wait_for_dependencies(self):
        dependency = valid_task("TASK-001", "queued")
        queued = valid_task("TASK-002", "queued")
        queued["depends_on"] = ["TASK-001"]
        data = valid_ledger()
        data["tasks"] = [dependency, queued]
        self.assertEqual(ledger.validate_ledger(data), [])

    def test_active_task_requires_bounded_read_paths(self):
        data = valid_ledger()
        active = valid_task(status="active")
        active["read_paths"] = ["tools/check_task_ledger.py", "tools/test_check_task_ledger.py"]
        data["tasks"] = [active]
        self.assertEqual(ledger.validate_ledger(data), [])

    def test_active_task_rejects_unsafe_read_paths(self):
        for path in ("../outside.py", "/absolute/file.py", "docs/automation/task-ledger.json", "assets/model.bin"):
            with self.subTest(path=path):
                data = valid_ledger()
                active = valid_task(status="active")
                active["read_paths"] = [path]
                data["tasks"] = [active]
                self.assertTrue(any("read_paths" in error for error in ledger.validate_ledger(data)))


class LiveGitHubReconciliationTests(unittest.TestCase):
    def test_accepts_open_pr_with_exact_head(self):
        task = {"task_id": "TASK-001", "status": "in_review", "head_sha": "a" * 40}
        pr = {"state": "open", "merged_at": None, "head": {"sha": "a" * 40}}
        self.assertEqual(audit.reconcile_task(task, pr), [])

    def test_rejects_stale_head_sha(self):
        task = {"task_id": "TASK-001", "status": "in_review", "head_sha": "a" * 40}
        pr = {"state": "open", "merged_at": None, "head": {"sha": "b" * 40}}
        self.assertTrue(any("does not match live PR head" in e for e in audit.reconcile_task(task, pr)))

    def test_rejects_closed_unmerged_pr_marked_in_review(self):
        task = {"task_id": "TASK-001", "status": "in_review", "head_sha": "a" * 40}
        pr = {"state": "closed", "merged_at": None, "head": {"sha": "a" * 40}}
        self.assertTrue(any("open, unmerged PR" in e for e in audit.reconcile_task(task, pr)))

    def test_completed_requires_merged_pr(self):
        task = {"task_id": "TASK-001", "status": "completed", "head_sha": "a" * 40}
        pr = {"state": "closed", "merged_at": None, "head": {"sha": "a" * 40}}
        self.assertTrue(any("must point to a merged PR" in e for e in audit.reconcile_task(task, pr)))


class LedgerSourceSelectionTests(unittest.TestCase):
    def write_ledger(self, directory: str, data: dict) -> Path:
        path = Path(directory) / "task-ledger.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_pull_request_without_ledger_change_uses_main_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            local_path = self.write_ledger(directory, {"source": "stale-merge-ref"})
            with patch.object(audit, "fetch_main_ledger", return_value={"source": "main"}) as fetch:
                result = audit.load_ledger("token", "pull_request", {"tools/example.py"}, local_path)
        self.assertEqual(result, {"source": "main"})
        fetch.assert_called_once_with("token")

    def test_pull_request_that_changes_ledger_uses_proposed_file(self):
        with tempfile.TemporaryDirectory() as directory:
            local_path = self.write_ledger(directory, {"source": "proposed"})
            with patch.object(audit, "fetch_main_ledger", side_effect=AssertionError("must use PR file")):
                result = audit.load_ledger(
                    "token", "pull_request", {audit.LEDGER_REPO_PATH}, local_path
                )
        self.assertEqual(result, {"source": "proposed"})

    def test_push_uses_checked_out_main_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            local_path = self.write_ledger(directory, {"source": "push"})
            with patch.object(audit, "fetch_main_ledger", side_effect=AssertionError("unexpected API read")):
                result = audit.load_ledger("token", "push", set(), local_path)
        self.assertEqual(result, {"source": "push"})

    def test_dispatch_uses_checked_out_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            local_path = self.write_ledger(directory, {"source": "dispatch"})
            with patch.object(audit, "fetch_main_ledger", side_effect=AssertionError("unexpected API read")):
                result = audit.load_ledger("token", "workflow_dispatch", set(), local_path)
        self.assertEqual(result, {"source": "dispatch"})

    def test_pull_request_event_fetches_changed_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            event_path = Path(directory) / "event.json"
            event_path.write_text(json.dumps({"number": 301}), encoding="utf-8")
            with patch.dict("os.environ", {"GITHUB_EVENT_PATH": str(event_path)}):
                with patch.object(
                    audit, "fetch_pull_request_files", return_value={audit.LEDGER_REPO_PATH}
                ) as fetch:
                    result = audit.fetch_event_changed_files("token", "pull_request")
        self.assertEqual(result, {audit.LEDGER_REPO_PATH})
        fetch.assert_called_once_with(301, "token")

    def test_non_pull_request_event_does_not_read_event_file(self):
        self.assertEqual(audit.fetch_event_changed_files("token", "push"), set())


class CompactTaskSummaryTests(unittest.TestCase):
    def activation_task(self):
        criteria = [
            "Ledger validator and regression tests pass in CI",
            "Gemini and OpenRouter prompts both reconcile the ledger with live GitHub state",
            "One active task maximum is enforced",
            "A post-merge cycle records exact PR state and continues the next unanswered research question",
            "Autonomous Gemini repository writes are constrained to the available GitHub MCP push_files tool; unavailable local editing tools are explicitly prohibited",
            "OpenRouter Free daily-quota preflight fails closed before any inference request",
        ]
        criteria.extend(f"Additional activation acceptance criterion {index}" for index in range(7, 16))
        return {
            "task_id": "AUTOMATION-LEDGER-ACTIVATION",
            "title": "Activate and validate persistent autonomous task tracking",
            "owner_role_id": "chief-of-staff",
            "parent_objective_id": "BOONTA-AUTONOMOUS-ENGINEERING",
            "depends_on": [],
            "owner_approved": False,
            "queue": "#226",
            "platform_scope": ["automation"],
            "status": "blocked",
            "target_branch": "main",
            "read_paths": [
                "tools/check_task_ledger.py",
                "tools/test_check_task_ledger.py",
                "tools/check_task_ledger_summary.py",
                ".github/workflows/boonta-autonomous-loop.yml",
            ],
            "read_ranges": [
                {"path": path, "start_line": 1, "end_line": 1}
                for path in [
                    "tools/check_task_ledger.py",
                    "tools/test_check_task_ledger.py",
                    "tools/check_task_ledger_summary.py",
                    ".github/workflows/boonta-autonomous-loop.yml",
                ]
            ],
            "question": (
                "Does the merged autonomous loop consistently reconcile the task ledger "
                "and avoid duplicate or stale work?"
            ),
            "acceptance_criteria": criteria,
            "next_action": (
                "Merged and validated: #374 owner re-evaluation gate; #375 direct preflight-owned delivery; "
                "#377 Groq four-step/1,152+384/three-tool profile; #378 supported temperature 0.2; "
                "#373 order-independent rival avoidance. Mainline checks passed. The 2026-11-10 UTC "
                "Gemini/OpenRouter/Groq cooldowns are active and scheduled loops correctly skipped provider "
                "calls. Next: after 2026-11-11 UTC reset, require one actual €0 provider invocation, a same-task "
                "PR and exact-head CI before completing this task. Only after the activation gate clears, "
                "perform the owner-directed Phase 1 cross-platform reuse/compatibility decision using #279 "
                "evidence in #226; defer #307 until the race slice is coherent."
            ),
            "pr_url": None,
            "head_sha": None,
            "updated_at": "2026-11-13",
        }

    def test_summary_preserves_four_top_criteria_and_actionable_next_step(self):
        task = self.activation_task()
        compact = task_summary.build_summary({
            "updated_at": "2026-11-13",
            "policy": {"max_active_tasks": 1},
            "tasks": [task],
        })["tasks"][0]

        self.assertEqual(compact["acceptance_criteria_total"], 15)
        self.assertEqual(len(compact["acceptance_criteria_excerpt"]), 4)
        self.assertEqual(compact["acceptance_criteria_excerpt"], task["acceptance_criteria"][:4])
        self.assertTrue(compact["next_action_excerpt"].startswith("after 2026-11-11 UTC reset"))
        self.assertIn("same-task PR and exact-head CI", compact["next_action_excerpt"])
        self.assertNotIn("Merged and validated:", compact["next_action_excerpt"])

    def test_github_actions_refreshes_only_the_derived_summary_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger_path = root / "task-ledger.json"
            summary_path = root / "task-ledger-summary.json"
            canonical_ledger = valid_ledger()
            original_ledger = json.dumps(canonical_ledger, indent=2)
            ledger_path.write_text(original_ledger, encoding="utf-8")
            summary_path.write_text("{ stale summary }\n", encoding="utf-8")

            with patch.object(task_summary, "LEDGER", ledger_path):
                with patch.object(task_summary, "SUMMARY", summary_path):
                    with patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}):
                        self.assertEqual(task_summary.main(), 0)

            expected = json.dumps(
                task_summary.build_summary(canonical_ledger),
                indent=2,
                ensure_ascii=False,
            ) + "\n"
            self.assertEqual(summary_path.read_text(encoding="utf-8"), expected)
            self.assertEqual(ledger_path.read_text(encoding="utf-8"), original_ledger)

    def test_local_summary_check_still_rejects_stale_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger_path = root / "task-ledger.json"
            summary_path = root / "task-ledger-summary.json"
            ledger_path.write_text(json.dumps(valid_ledger()), encoding="utf-8")
            stale = "{ stale summary }\n"
            summary_path.write_text(stale, encoding="utf-8")

            with patch.object(task_summary, "LEDGER", ledger_path):
                with patch.object(task_summary, "SUMMARY", summary_path):
                    with patch.dict("os.environ", {"GITHUB_ACTIONS": "false"}):
                        self.assertEqual(task_summary.main(), 1)

            self.assertEqual(summary_path.read_text(encoding="utf-8"), stale)

    def test_blocked_activation_context_fits_the_1100_character_workflow_budget(self):
        task = self.activation_task()
        compact_summary = task_summary.build_summary({
            "updated_at": "2026-11-13",
            "policy": {"max_active_tasks": 1},
            "tasks": [task],
        })
        compact_task = compact_summary["tasks"][0]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def write(relative_path, content):
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

            write("docs/REVERSE_ENGINEERING_FIRST.md", "DISCOVER VERIFY REUSE GameCube/Wii")
            write(
                "docs/automation/AUTONOMOUS_CONTEXT_BUDGET.md",
                "One model provider invocation at most; €0; 1,550 context tokens",
            )
            write("tools/check_task_ledger.py", "# exact source excerpt for the provider handoff\n")
            write("tools/check_task_ledger_summary.py", "# bounded write target\n")
            write("tools/test_check_task_ledger.py", "# bounded test target\n")
            write(".github/workflows/boonta-autonomous-loop.yml", "# exact workflow source excerpt\n")
            write(
                "docs/automation/patch-path-allowlist.json",
                json.dumps({
                    "schema_version": 1,
                    "policy": {
                        "owner_review_required": True,
                        "path_mode": "exact",
                        "max_paths_per_task": 20,
                    },
                    "tasks": [{
                        "task_id": "AUTOMATION-LEDGER-ACTIVATION",
                        "purpose": "Owner-authorized bounded activation test.",
                        "approval_ref": "https://github.com/Master-Chiken/boonta-reborn-88/pull/408",
                        "allowed_paths": [
                            "tools/check_task_ledger_summary.py",
                            "tools/test_check_task_ledger.py",
                        ],
                    }],
                }),
            )
            write(
                "docs/automation/agent-roles.json",
                json.dumps({
                    "schema_version": 1,
                    "status": "declarative_only",
                    "execution_plane": "github_actions",
                    "canonical_task_ledger": "docs/automation/task-ledger.json",
                    "policy": {
                        "max_active_missions": 1,
                        "max_provider_invocations_per_run": 1,
                        "repository_writers": ["github_actions"],
                        "model_agents_receive_write_credentials": False,
                        "paid_fallback": False,
                        "auto_merge": False,
                        "human_merge_approval_required": True,
                        "qa_must_be_independent": True,
                    },
                    "provider_order": ["gemini", "openrouter_free", "groq_free"],
                    "roles": [
                        {
                            "id": "chief-of-staff",
                            "title": "Chief of Staff",
                            "kind": "agent",
                            "unit": "automation",
                            "manager_id": "human-owner",
                        },
                        {
                            "id": "human-owner",
                            "title": "Human Owner",
                            "kind": "human",
                            "unit": "owner",
                            "manager_id": None,
                        },
                    ],
                    "objectives": [{
                        "id": "BOONTA-AUTONOMOUS-ENGINEERING",
                        "title": "Autonomous Engineering",
                    }],
                }),
            )
            write(
                "docs/automation/task-ledger-summary.json",
                json.dumps(compact_summary, ensure_ascii=False),
            )

            criteria = compact_task["acceptance_criteria_excerpt"]
            handoff = "\n".join([
                "Task ID: AUTOMATION-LEDGER-ACTIVATION",
                "Title: Activate and validate persistent autonomous task tracking",
                "Target branch: main",
                "Read-only source paths (select at most one): " + ", ".join(task["read_paths"]),
                "Question: " + compact_task["question_excerpt"],
                "Acceptance criteria (15; first 5):",
                *("- " + item for item in criteria),
                "Next: " + compact_task["next_action_excerpt"],
            ])

            self.assertIn(compact_task["next_action_excerpt"], handoff)
            self.assertEqual(len(compact_task["acceptance_criteria_excerpt"]), 4)

            verified = context_builder.build_context(
                root=root,
                task_id="AUTOMATION-LEDGER-ACTIVATION",
                task_title=task["title"],
                target_branch="main",
                task_context=handoff,
                max_chars=3000,
                max_task_context=1100,
                max_criteria=5,
                max_next_action=180,
                source_root=root,
                max_source_chars=1600,
            )

        self.assertIn("Acceptance criteria (15 total; first 4):", verified)
        self.assertIn("require one actual €0 provider invocation", verified)
        self.assertIn("same-task PR and exact-head CI", verified)
        self.assertNotIn("Merged and validated:", verified)




if __name__ == "__main__":
    unittest.main()
