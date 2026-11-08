#!/usr/bin/env python3
"""Integration tests for the production OpenRouter and Groq watchdogs.

The test extracts the production heredoc rather than maintaining a second
implementation. A fake OpenCode executable exercises real process-group
termination without making any network or provider request.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPENROUTER_WORKFLOW = ROOT / ".github/workflows/openrouter-plan-execute.yml"
GROQ_WORKFLOW = ROOT / ".github/workflows/groq-plan-execute.yml"
HEREDOC = (
    'python3 - "$PROMPT" "$RUNNER_TEMP/opencode-cycle-report.txt" '
    '"$REPO_ROOT" <<\'PY\'\n'
)

FAKE_OPENCODE = r'''#!/usr/bin/env python3
import os
import subprocess
import sys
import time
from pathlib import Path

mode = os.environ["WATCHDOG_TEST_MODE"]
heartbeat = Path(os.environ["WATCHDOG_HEARTBEAT"])
child_code = (
    "import sys,time\n"
    "path=sys.argv[1]\n"
    "while True:\n"
    " with open(path, 'a', encoding='utf-8') as stream:\n"
    "  stream.write('tick\\n'); stream.flush()\n"
    " time.sleep(0.03)\n"
)
child = subprocess.Popen([sys.executable, "-c", child_code, str(heartbeat)])
deadline = time.monotonic() + 3
while time.monotonic() < deadline:
    if heartbeat.exists() and heartbeat.stat().st_size:
        break
    time.sleep(0.01)
else:
    raise SystemExit("grandchild did not start its heartbeat")

print("grandchild-pid=" + str(child.pid), flush=True)
if mode == "refusal":
    print("HTTP 429 Too Many Requests", flush=True)
elif mode == "groq_refusal":
    print("tokens per minute (TPM) quota exceeded", flush=True)
elif mode == "groq_429_refusal":
    print("HTTP 429 Too Many Requests", flush=True)
elif mode == "groq_401_refusal":
    print("HTTP 401 Unauthorized", flush=True)
elif mode == "signal":
    print("WATCHDOG_READY", flush=True)
else:
    print("The Boonta racing line is wider at the next turn.", flush=True)
    print("TPM is just a project note, not a provider refusal.", flush=True)
    child.terminate()
    child.wait(timeout=3)
    raise SystemExit(0)

time.sleep(30)
'''


def production_watchdog_source(workflow: Path) -> str:
    source = workflow.read_text(encoding="utf-8")
    if source.count(HEREDOC) != 1:
        raise AssertionError(f"Expected exactly one production watchdog heredoc in {workflow.name}")
    body = source.split(HEREDOC, 1)[1].split("\n          PY", 1)[0]
    return textwrap.dedent(body)


class OpenRouterWatchdogIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if shutil.which("timeout") is None:
            raise RuntimeError("GNU timeout is required by the production OpenRouter workflow")
        cls.openrouter_watchdog_source = production_watchdog_source(OPENROUTER_WORKFLOW)
        cls.groq_watchdog_source = production_watchdog_source(GROQ_WORKFLOW)

    def launch(
        self, root: Path, mode: str, watchdog_source: str | None = None
    ) -> tuple[subprocess.Popen[str], Path, Path]:
        bin_dir = root / "bin"
        bin_dir.mkdir()
        fake_cli = bin_dir / "opencode"
        fake_cli.write_text(FAKE_OPENCODE, encoding="utf-8")
        fake_cli.chmod(0o755)

        watchdog = root / "watchdog.py"
        watchdog.write_text(watchdog_source or self.openrouter_watchdog_source, encoding="utf-8")
        report = root / "opencode-cycle-report.txt"
        heartbeat = root / "grandchild-heartbeat.txt"
        env = os.environ.copy()
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
        env["WATCHDOG_TEST_MODE"] = mode
        env["WATCHDOG_HEARTBEAT"] = str(heartbeat)
        process = subprocess.Popen(
            [sys.executable, str(watchdog), "integration-test-prompt", str(report), str(root)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            start_new_session=True,
        )
        return process, report, heartbeat

    @staticmethod
    def heartbeat_count(path: Path) -> int:
        if not path.exists():
            return 0
        return len(path.read_text(encoding="utf-8").splitlines())

    @staticmethod
    def grandchild_pid(report: Path) -> int:
        for line in report.read_text(encoding="utf-8").splitlines():
            if line.startswith("grandchild-pid="):
                return int(line.split("=", 1)[1])
        raise AssertionError("The production watchdog did not preserve the child PID in its report")

    def assert_heartbeat_stopped(self, heartbeat: Path) -> None:
        before = self.heartbeat_count(heartbeat)
        self.assertGreater(before, 0, "The grandchild heartbeat must start before termination")
        time.sleep(0.2)
        after = self.heartbeat_count(heartbeat)
        self.assertEqual(after, before, "A descendant kept running after the watchdog stopped")

    def test_first_provider_refusal_terminates_process_group_and_preserves_report(self) -> None:
        with tempfile.TemporaryDirectory(prefix="boonta-watchdog-refusal-") as directory:
            root = Path(directory)
            process, report, heartbeat = self.launch(root, "refusal")
            try:
                output, _ = process.communicate(timeout=10)
                self.assertEqual(process.returncode, 75, output)
                self.assertIn("HTTP 429 Too Many Requests", report.read_text(encoding="utf-8"))
                self.assertIn("terminating OpenCode immediately", output)
                self.assert_heartbeat_stopped(heartbeat)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                if report.exists():
                    try:
                        pid = self.grandchild_pid(report)
                        os.kill(pid, signal.SIGKILL)
                    except (AssertionError, ProcessLookupError, PermissionError):
                        pass

    def test_benign_project_output_completes_without_false_positive(self) -> None:
        with tempfile.TemporaryDirectory(prefix="boonta-watchdog-benign-") as directory:
            root = Path(directory)
            process, report, _heartbeat = self.launch(root, "benign")
            output, _ = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, output)
            saved = report.read_text(encoding="utf-8")
            self.assertIn("Boonta racing line", saved)
            self.assertIn("TPM is just a project note", saved)
            self.assertNotIn("terminating OpenCode immediately", output)

    def test_sigterm_terminates_process_group_and_preserves_report(self) -> None:
        with tempfile.TemporaryDirectory(prefix="boonta-watchdog-signal-") as directory:
            root = Path(directory)
            process, report, heartbeat = self.launch(root, "signal")
            try:
                self.assertIsNotNone(process.stdout)
                ready = False
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    line = process.stdout.readline()
                    if not line:
                        break
                    if "WATCHDOG_READY" in line:
                        ready = True
                        break
                self.assertTrue(ready, "The fake provider did not reach its ready state")
                os.kill(process.pid, signal.SIGTERM)
                output, _ = process.communicate(timeout=10)
                self.assertEqual(process.returncode, 128 + signal.SIGTERM, output)
                self.assertIn("WATCHDOG_READY", report.read_text(encoding="utf-8"))
                self.assert_heartbeat_stopped(heartbeat)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                if report.exists():
                    try:
                        pid = self.grandchild_pid(report)
                        os.kill(pid, signal.SIGKILL)
                    except (AssertionError, ProcessLookupError, PermissionError):
                        pass


    def test_groq_first_tpm_refusal_terminates_process_group_and_preserves_report(self) -> None:
        with tempfile.TemporaryDirectory(prefix="boonta-groq-watchdog-refusal-") as directory:
            root = Path(directory)
            process, report, heartbeat = self.launch(
                root, "groq_refusal", self.groq_watchdog_source
            )
            try:
                output, _ = process.communicate(timeout=10)
                self.assertEqual(process.returncode, 75, output)
                self.assertIn("tokens per minute (TPM)", report.read_text(encoding="utf-8"))
                self.assertIn("Groq provider quota/auth refusal detected", output)
                self.assert_heartbeat_stopped(heartbeat)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                if report.exists():
                    try:
                        pid = self.grandchild_pid(report)
                        os.kill(pid, signal.SIGKILL)
                    except (AssertionError, ProcessLookupError, PermissionError):
                        pass

    def test_groq_first_http_429_terminates_process_group_and_preserves_report(self) -> None:
        self.assert_groq_refusal_stops("groq_429_refusal", "HTTP 429 Too Many Requests")

    def test_groq_first_http_401_terminates_process_group_and_preserves_report(self) -> None:
        self.assert_groq_refusal_stops("groq_401_refusal", "HTTP 401 Unauthorized")

    def assert_groq_refusal_stops(self, mode: str, expected_report_line: str) -> None:
        with tempfile.TemporaryDirectory(prefix="boonta-groq-watchdog-refusal-") as directory:
            root = Path(directory)
            process, report, heartbeat = self.launch(
                root, mode, self.groq_watchdog_source
            )
            try:
                output, _ = process.communicate(timeout=10)
                self.assertEqual(process.returncode, 75, output)
                saved = report.read_text(encoding="utf-8")
                self.assertIn(expected_report_line, saved)
                self.assertIn("Groq provider quota/auth refusal detected", output)
                self.assert_heartbeat_stopped(heartbeat)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                if report.exists():
                    try:
                        pid = self.grandchild_pid(report)
                        os.kill(pid, signal.SIGKILL)
                    except (AssertionError, ProcessLookupError, PermissionError):
                        pass

    def test_groq_sigterm_terminates_process_group_and_preserves_report(self) -> None:
        with tempfile.TemporaryDirectory(prefix="boonta-groq-watchdog-signal-") as directory:
            root = Path(directory)
            process, report, heartbeat = self.launch(
                root, "signal", self.groq_watchdog_source
            )
            try:
                self.assertIsNotNone(process.stdout)
                ready = False
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    line = process.stdout.readline()
                    if not line:
                        break
                    if "WATCHDOG_READY" in line:
                        ready = True
                        break
                self.assertTrue(ready, "The fake Groq provider did not reach its ready state")
                os.kill(process.pid, signal.SIGTERM)
                output, _ = process.communicate(timeout=10)
                self.assertEqual(process.returncode, 128 + signal.SIGTERM, output)
                self.assertIn("WATCHDOG_READY", report.read_text(encoding="utf-8"))
                self.assert_heartbeat_stopped(heartbeat)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                if report.exists():
                    try:
                        pid = self.grandchild_pid(report)
                        os.kill(pid, signal.SIGKILL)
                    except (AssertionError, ProcessLookupError, PermissionError):
                        pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
