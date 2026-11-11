"""Tests for safe, existing and bounded task-scoped agent source reads."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from check_task_read_paths import MAX_READ_PATH_BYTES, validate_read_paths


def ledger_with_path(path: str) -> dict:
    task = {
        "task_id": "TASK-001",
        "title": "Bounded source read test",
        "queue": "#226",
        "platform_scope": ["automation"],
        "status": "active",
        "target_branch": "main",
        "read_paths": [path],
        "question": "Can this source be read safely?",
        "acceptance_criteria": ["Use only exact UTF-8 source paths"],
        "evidence": [],
        "next_action": "Inspect one bounded file.",
        "updated_at": "2026-11-11",
    }
    return {
        "schema_version": 1,
        "updated_at": "2026-11-11",
        "policy": {"max_active_tasks": 1},
        "tasks": [task],
    }


class TaskReadPathTests(unittest.TestCase):
    def test_accepts_existing_bounded_utf8_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            (root / "tools/example.py").write_text("def example():\n    return True\n", encoding="utf-8")
            self.assertEqual(validate_read_paths(ledger_with_path("tools/example.py"), root), [])

    def test_rejects_missing_source(self):
        with tempfile.TemporaryDirectory() as temp:
            errors = validate_read_paths(ledger_with_path("tools/missing.py"), Path(temp))
            self.assertTrue(any("does not exist" in error for error in errors))

    def test_rejects_source_over_context_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            (root / "tools/large.py").write_text("x" * (MAX_READ_PATH_BYTES + 1), encoding="utf-8")
            errors = validate_read_paths(ledger_with_path("tools/large.py"), root)
            self.assertTrue(any("agent read budget" in error for error in errors))

    def test_rejects_symlink_outside_repository(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            root = Path(temp)
            (root / "tools").mkdir()
            target = Path(outside) / "secret.py"
            target.write_text("not inside repository", encoding="utf-8")
            (root / "tools/linked.py").symlink_to(target)
            errors = validate_read_paths(ledger_with_path("tools/linked.py"), root)
            self.assertTrue(any("outside the repository" in error for error in errors))

    def test_rejects_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            (root / "tools/bad.py").write_bytes(b"print('ok')" + bytes([255]))
            errors = validate_read_paths(ledger_with_path("tools/bad.py"), root)
            self.assertTrue(any("valid UTF-8" in error for error in errors))

    def test_rejects_unsafe_read_path_before_filesystem_access(self):
        with tempfile.TemporaryDirectory() as temp:
            errors = validate_read_paths(ledger_with_path("../outside.py"), Path(temp))
            self.assertTrue(any("read_paths" in error or "safe repository" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
