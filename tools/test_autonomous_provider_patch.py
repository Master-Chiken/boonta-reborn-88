#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_autonomous_provider_patch as provider

TASK_ID = "PATCH-TEST-001"
APPROVAL = "https://github.com/Master-Chiken/boonta-reborn-88/pull/400"
MODEL = "groq/openai/gpt-oss-20b"


def git(root: Path, *args: str, input_text: str | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
        timeout=15,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class ProviderPatchFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="boonta-provider-patch-")
        self.parent = Path(self.temp.name).resolve()
        self.root = self.parent / "repo"
        self.root.mkdir()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Boonta Provider Test")
        git(self.root, "config", "user.email", "boonta-provider-test@example.invalid")
        source = self.root / "src/one.c"
        source.parent.mkdir(parents=True)
        source.write_text("int value = 1;\n", encoding="utf-8")
        git(self.root, "add", "src/one.c")
        git(self.root, "commit", "-qm", "provider fixture base")
        self.base_sha = git(self.root, "rev-parse", "HEAD")

        self.allowlist_path = self.parent / "allowlist.json"
        self.allowlist_path.write_text(json.dumps({
            "status": "READY",
            "task_id": TASK_ID,
            "base_sha": self.base_sha,
            "policy_base_sha": self.base_sha,
            "approval_ref": APPROVAL,
            "purpose": "Synthetic owner-reviewed source path",
            "allowed_paths": ["src/one.c"],
        }), encoding="utf-8")
        self.prompt_path = self.parent / "context.txt"
        self.prompt_path.write_text("Implement one controlled source change.", encoding="utf-8")
        self.output_path = self.parent / "proposal.json"
        self.config_path = self.parent / "opencode.json"
        self.config_path.write_text(json.dumps({
            "model": MODEL,
            "permission": {"*": "deny"},
        }), encoding="utf-8")
        self.fake_bin = self.parent / "bin"
        self.fake_bin.mkdir()
        self.diff = self.make_diff("int value = 2;\n")
        self.proposal = {
            "schema_version": 1,
            "task_id": TASK_ID,
            "base_sha": self.base_sha,
            "summary": "Update the controlled fixture value",
            "unified_diff": self.diff,
            "test_ids": ["automation.task_preflight"],
            "limitations": ["Provider output has not been executed"],
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def make_diff(self, replacement: str) -> str:
        source = self.root / "src/one.c"
        source.write_text(replacement, encoding="utf-8")
        diff = git(self.root, "diff", "--", "src/one.c")
        git(self.root, "checkout", "--", "src/one.c")
        return diff

    def event_stream(self, text: str | None = None, *, tool: bool = False, many: bool = False) -> str:
        events = [
            {"type": "step_start", "sessionID": "ses_test", "part": {"type": "step-start"}},
        ]
        if tool:
            events.append({
                "type": "tool_use",
                "sessionID": "ses_test",
                "part": {"type": "tool", "tool": "bash", "state": {"status": "completed"}},
            })
        else:
            payload = text if text is not None else json.dumps(self.proposal)
            events.append({
                "type": "text",
                "sessionID": "ses_test",
                "part": {"type": "text", "text": payload},
            })
            if many:
                events.append({
                    "type": "text",
                    "sessionID": "ses_test",
                    "part": {"type": "text", "text": payload},
                })
        return "".join(json.dumps(event) + "\n" for event in events)

    def install_fake_opencode(
        self, stream: str, *, exit_code: int = 0,
        stdout_padding: int = 0, stderr_padding: int = 0, sleep_seconds: float = 0.0,
    ) -> None:
        script = self.fake_bin / "opencode"
        script.write_text(
            "#!" + sys.executable + "\n"
            "import os, sys, time\n"
            "assert os.environ.get('GITHUB_TOKEN') is None\n"
            "assert os.environ.get('GITHUB_PERSONAL_ACCESS_TOKEN') is None\n"
            "assert os.environ.get('GROQ_API_KEY') == 'g' * 32\n"
            "assert '--format' in sys.argv and 'json' in sys.argv\n"
            "sys.stdout.buffer.write(" + repr(stream.encode("utf-8")) + ")\n"
            "sys.stdout.buffer.write(b'x' * " + str(stdout_padding) + ")\n"
            "sys.stderr.buffer.write(b'e' * " + str(stderr_padding) + ")\n"
            "time.sleep(" + repr(sleep_seconds) + ")\n"
            "sys.exit(" + str(exit_code) + ")\n",
            encoding="utf-8",
        )
        script.chmod(0o755)

    def invoke(self, *, model: str = MODEL, timeout_seconds: int = 90) -> dict:
        with patch.dict(os.environ, {
            "PATH": str(self.fake_bin) + os.pathsep + os.environ.get("PATH", os.defpath),
            "HOME": str(self.parent),
            "OPENCODE_CONFIG": str(self.config_path),
            "GROQ_API_KEY": "g" * 32,
            "GITHUB_TOKEN": "github-token-must-not-be-forwarded",
            "GITHUB_PERSONAL_ACCESS_TOKEN": "github-mcp-token-must-not-be-forwarded",
        }, clear=False):
            return provider.run_provider_patch(
                repo_root=self.root,
                policy_root=self.root,
                allowlist_report=self.allowlist_path,
                prompt_file=self.prompt_path,
                output_proposal=self.output_path,
                expected_task_id=TASK_ID,
                expected_base_sha=self.base_sha,
                expected_policy_sha=self.base_sha,
                model=model,
                timeout_seconds=timeout_seconds,
            )

    def test_valid_provider_text_becomes_one_bounded_proposal(self):
        self.install_fake_opencode(self.event_stream())
        report = self.invoke()
        self.assertEqual(report["status"], "PROPOSAL_VALIDATED")
        self.assertEqual(report["changed_paths"], ["src/one.c"])
        self.assertFalse(report["provider_tools_exposed"])
        self.assertFalse(report["github_credentials_forwarded"])
        self.assertTrue(self.output_path.is_file())
        saved = json.loads(self.output_path.read_text(encoding="utf-8"))
        self.assertEqual(saved, self.proposal)
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    def test_provider_attempt_marker_is_written_only_before_launch(self):
        marker = self.parent / "github-output.txt"
        self.install_fake_opencode(self.event_stream())
        with patch.dict(os.environ, {"GITHUB_OUTPUT": str(marker)}, clear=False):
            self.invoke()
        self.assertIn("provider_request_started=true", marker.read_text(encoding="utf-8"))

    def test_stdout_limit_is_enforced_while_streaming(self):
        self.install_fake_opencode(
            self.event_stream(), stdout_padding=provider.MAX_STREAM_BYTES + 8192,
        )
        with self.assertRaisesRegex(provider.ProviderPatchError, "stdout exceeded"):
            self.invoke()
        self.assertFalse(self.output_path.exists())

    def test_stderr_limit_is_enforced_while_streaming(self):
        self.install_fake_opencode(
            self.event_stream(), stderr_padding=provider.MAX_STDERR_BYTES + 8192,
        )
        with self.assertRaisesRegex(provider.ProviderPatchError, "stderr exceeded"):
            self.invoke()
        self.assertFalse(self.output_path.exists())

    def test_timeout_stops_provider_process_without_retry(self):
        self.install_fake_opencode(self.event_stream(), sleep_seconds=5.0)
        with self.assertRaisesRegex(provider.ProviderPatchError, "timed out"):
            self.invoke(timeout_seconds=1)
        self.assertFalse(self.output_path.exists())

    def test_missing_executable_does_not_mark_provider_started(self):
        self.install_fake_opencode(self.event_stream())
        (self.fake_bin / "opencode").unlink()
        marker = self.parent / "github-output-missing-executable.txt"
        with patch.dict(os.environ, {"GITHUB_OUTPUT": str(marker)}, clear=False):
            with self.assertRaisesRegex(provider.ProviderPatchError, "CLI is unavailable"):
                self.invoke()
        self.assertFalse(marker.exists())

    def test_tool_use_event_rejects_proposal(self):
        self.install_fake_opencode(self.event_stream(tool=True))
        with self.assertRaisesRegex(provider.ProviderPatchError, "tool call"):
            self.invoke()
        self.assertFalse(self.output_path.exists())

    def test_multiple_text_events_are_ambiguous_and_rejected(self):
        self.install_fake_opencode(self.event_stream(many=True))
        with self.assertRaisesRegex(provider.ProviderPatchError, "exactly one"):
            self.invoke()
        self.assertFalse(self.output_path.exists())

    def test_provider_nonzero_exit_is_rejected(self):
        self.install_fake_opencode(self.event_stream(), exit_code=75)
        with self.assertRaisesRegex(provider.ProviderPatchError, "status 75"):
            self.invoke()
        self.assertFalse(self.output_path.exists())

    def test_model_cannot_write_outside_the_allowlist(self):
        proposal = dict(self.proposal)
        proposal["unified_diff"] = self.make_diff("int value = 3;\n").replace(
            "src/one.c", "src/other.c"
        )
        self.install_fake_opencode(self.event_stream(json.dumps(proposal)))
        with self.assertRaisesRegex(provider.ProviderPatchError, "allowlist|allow-list|approved"):
            self.invoke()
        self.assertFalse(self.output_path.exists())

    def test_no_tools_config_is_mandatory(self):
        self.config_path.write_text(json.dumps({
            "permission": {"*": "allow"},
            "mcp": {"github": {"enabled": True}},
        }), encoding="utf-8")
        self.install_fake_opencode(self.event_stream())
        with self.assertRaisesRegex(provider.ProviderPatchError, "deny every model tool"):
            self.invoke()
        self.assertFalse(self.output_path.exists())

    def test_per_tool_allow_is_rejected_even_with_wildcard_deny(self):
        self.config_path.write_text(json.dumps({
            "permission": {"*": "deny", "read": "allow"},
        }), encoding="utf-8")
        self.install_fake_opencode(self.event_stream())
        with self.assertRaisesRegex(provider.ProviderPatchError, "without per-tool exceptions"):
            self.invoke()
        self.assertFalse(self.output_path.exists())

    def test_policy_sha_mismatch_stops_before_provider(self):
        self.install_fake_opencode(self.event_stream())
        with self.assertRaisesRegex(provider.ProposalError, "differs"):
            provider.run_provider_patch(
                repo_root=self.root,
                policy_root=self.root,
                allowlist_report=self.allowlist_path,
                prompt_file=self.prompt_path,
                output_proposal=self.output_path,
                expected_task_id=TASK_ID,
                expected_base_sha=self.base_sha,
                expected_policy_sha="0" * 40,
                model=MODEL,
            )
        self.assertFalse(self.output_path.exists())


class EventParserTests(unittest.TestCase):
    def test_duplicate_event_properties_are_rejected(self):
        raw = '{"type":"text","type":"reasoning","part":{"type":"text","text":"{}"}}\n'
        with self.assertRaisesRegex(provider.ProviderPatchError, "invalid NDJSON"):
            provider.parse_event_stream(raw)

    def test_markdown_fences_are_not_silently_stripped(self):
        raw = json.dumps({
            "type": "text",
            "part": {"type": "text", "text": "FENCE-json\n{}\nFENCE"},
        }) + "\n"
        self.assertEqual(provider.parse_event_stream(raw), "FENCE-json\n{}\nFENCE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
