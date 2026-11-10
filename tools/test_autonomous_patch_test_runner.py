#!/usr/bin/env python3
"""Offline tests for the fixed autonomous patch-test dispatcher."""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import run_autonomous_patch_tests as dispatcher


def git(root: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr)


class DispatcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Boonta Test")
        git(self.root, "config", "user.email", "boonta-test@example.invalid")
        (self.root / "tools").mkdir()
        (self.root / "tools/ok.py").write_text("print('fixed test ran')\n", encoding="utf-8")
        (self.root / "tools/secret_probe.py").write_text(
            "import os\nprint('clean' if not os.getenv('GITHUB_TOKEN') else 'leaked')\n",
            encoding="utf-8",
        )
        (self.root / "tools/fail.py").write_text("raise SystemExit(7)\n", encoding="utf-8")
        (self.root / "tools/should_not_run.py").write_text(
            "from pathlib import Path\nPath('second-test-ran').write_text('bad')\n",
            encoding="utf-8",
        )
        self.original_registry = dispatcher.TEST_REGISTRY.copy()

    def tearDown(self) -> None:
        dispatcher.TEST_REGISTRY.clear()
        dispatcher.TEST_REGISTRY.update(self.original_registry)
        self.temp.cleanup()

    def test_unknown_identifier_is_rejected(self):
        with self.assertRaisesRegex(dispatcher.TestDispatchError, "Unknown test"):
            dispatcher.run_test_ids(self.root, ["shell:echo unsafe"])

    def test_duplicate_identifiers_are_rejected(self):
        dispatcher.TEST_REGISTRY["test.ok"] = ("tools/ok.py",)
        with self.assertRaisesRegex(dispatcher.TestDispatchError, "Duplicate"):
            dispatcher.run_test_ids(self.root, ["test.ok", "test.ok"])

    def test_non_string_identifiers_are_rejected(self):
        with self.assertRaisesRegex(dispatcher.TestDispatchError, "must be a string"):
            dispatcher.run_test_ids(self.root, [{"command": "echo unsafe"}])

    def test_exact_checkout_root_is_required(self):
        dispatcher.TEST_REGISTRY["test.ok"] = ("tools/ok.py",)
        with self.assertRaisesRegex(dispatcher.TestDispatchError, "exact Git checkout root"):
            dispatcher.run_test_ids(self.root / "tools", ["test.ok"])

    def test_child_process_does_not_receive_github_token(self):
        dispatcher.TEST_REGISTRY["test.secret_probe"] = ("tools/secret_probe.py",)
        previous = os.environ.get("GITHUB_TOKEN")
        os.environ["GITHUB_TOKEN"] = "fixture-secret-must-not-be-forwarded"
        try:
            report = dispatcher.run_test_ids(self.root, ["test.secret_probe"])
        finally:
            if previous is None:
                os.environ.pop("GITHUB_TOKEN", None)
            else:
                os.environ["GITHUB_TOKEN"] = previous
        self.assertEqual(report["status"], "PASSED")
        self.assertEqual(report["results"][0]["stdout"], "clean\n")

    def test_first_failure_stops_later_tests(self):
        dispatcher.TEST_REGISTRY["test.fail"] = ("tools/fail.py",)
        dispatcher.TEST_REGISTRY["test.should_not_run"] = ("tools/should_not_run.py",)
        report = dispatcher.run_test_ids(
            self.root, ["test.fail", "test.should_not_run"],
        )
        self.assertEqual(report["status"], "FAILED")
        self.assertTrue(report["stopped_after_first_failure"])
        self.assertEqual(len(report["results"]), 1)
        self.assertFalse((self.root / "second-test-ran").exists())

    def test_registered_test_runs_without_shell(self):
        dispatcher.TEST_REGISTRY["test.ok"] = ("tools/ok.py",)
        report = dispatcher.run_test_ids(self.root, ["test.ok"])
        self.assertEqual(report["status"], "PASSED")
        self.assertEqual(report["results"][0]["stdout"], "fixed test ran\n")

    def test_timeout_is_bounded_and_stops_sequence(self):
        (self.root / "tools/sleep.py").write_text(
            "import time\ntime.sleep(3)\n", encoding="utf-8",
        )
        dispatcher.TEST_REGISTRY["test.sleep"] = ("tools/sleep.py",)
        report = dispatcher.run_test_ids(self.root, ["test.sleep"], timeout_seconds=1)
        self.assertEqual(report["status"], "FAILED")
        self.assertEqual(report["results"][0]["status"], "TIMEOUT")
        self.assertTrue(report["stopped_after_first_failure"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
