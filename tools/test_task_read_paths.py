"""Tests for safe, existing and aggregate-bounded task-scoped source reads."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from check_task_read_paths import (
    MAX_READ_PATH_BYTES,
    MAX_TOTAL_READ_BYTES,
    validate_read_paths,
)


def ledger_with_paths(paths: list[str]) -> dict:
    task = {
        "task_id": "TASK-001",
        "title": "Bounded source read test",
        "queue": "#226",
        "platform_scope": ["automation"],
        "owner_role_id": "chief-of-staff",
        "parent_objective_id": "BOONTA-AUTONOMOUS-ENGINEERING",
        "status": "active",
        "target_branch": "main",
        "read_paths": paths,
        "read_ranges": [
            {"path": path, "start_line": 1, "end_line": 1}
            for path in paths
        ],
        "question": "Can these exact sources be read safely?",
        "acceptance_criteria": ["Use only exact UTF-8 source paths"],
        "evidence": [],
        "next_action": "Inspect bounded source excerpts.",
        "updated_at": "2026-11-11",
    }
    return {
        "schema_version": 1,
        "updated_at": "2026-11-11",
        "policy": {"max_active_tasks": 1},
        "tasks": [task],
    }


class TaskReadPathTests(unittest.TestCase):
    def test_accepts_existing_bounded_utf8_source_with_exact_range(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            (root / "tools/example.py").write_text("def example():\n    return True\n", encoding="utf-8")
            self.assertEqual(validate_read_paths(ledger_with_paths(["tools/example.py"]), root), [])

    def test_accepts_multiple_large_but_bounded_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "source").mkdir()
            paths = []
            for index, size in enumerate((64000, 42000, 800, 30000)):
                path = f"source/file{index}.c"
                (root / path).write_text("x" * size, encoding="utf-8")
                paths.append(path)
            self.assertEqual(validate_read_paths(ledger_with_paths(paths), root), [])

    def test_rejects_paths_without_bounded_ranges(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            (root / "tools/example.py").write_text("print('ok')\n", encoding="utf-8")
            data = ledger_with_paths(["tools/example.py"])
            data["tasks"][0]["read_ranges"] = []
            errors = validate_read_paths(data, root)
            self.assertTrue(any("read_ranges must contain" in error for error in errors))

    def test_rejects_range_outside_exact_path_allowlist(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            (root / "tools/example.py").write_text("print('ok')\n", encoding="utf-8")
            data = ledger_with_paths(["tools/example.py"])
            data["tasks"][0]["read_ranges"] = [
                {"path": "tools/other.py", "start_line": 1, "end_line": 1}
            ]
            errors = validate_read_paths(data, root)
            self.assertTrue(any("outside the exact read_paths allow-list" in error for error in errors))

    def test_rejects_uncovered_path(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            (root / "tools/a.py").write_text("print('a')\n", encoding="utf-8")
            (root / "tools/b.py").write_text("print('b')\n", encoding="utf-8")
            data = ledger_with_paths(["tools/a.py", "tools/b.py"])
            data["tasks"][0]["read_ranges"] = [
                {"path": "tools/a.py", "start_line": 1, "end_line": 1}
            ]
            errors = validate_read_paths(data, root)
            self.assertTrue(any("cover every exact read_paths entry" in error for error in errors))

    def test_rejects_range_past_end_of_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            (root / "tools/example.py").write_text("line one\nline two\n", encoding="utf-8")
            data = ledger_with_paths(["tools/example.py"])
            data["tasks"][0]["read_ranges"] = [
                {"path": "tools/example.py", "start_line": 1, "end_line": 3}
            ]
            errors = validate_read_paths(data, root)
            self.assertTrue(any("beyond tools/example.py's 2 lines" in error for error in errors))

    def test_rejects_range_over_line_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            (root / "tools/example.py").write_text("\n".join(["x"] * 81) + "\n", encoding="utf-8")
            data = ledger_with_paths(["tools/example.py"])
            data["tasks"][0]["read_ranges"] = [
                {"path": "tools/example.py", "start_line": 1, "end_line": 81}
            ]
            errors = validate_read_paths(data, root)
            self.assertTrue(any("per-range limit is 80" in error for error in errors))

    def test_rejects_missing_source(self):
        with tempfile.TemporaryDirectory() as temp:
            errors = validate_read_paths(ledger_with_paths(["tools/missing.py"]), Path(temp))
            self.assertTrue(any("does not exist" in error for error in errors))

    def test_rejects_source_over_per_file_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            (root / "tools/large.py").write_text("x" * (MAX_READ_PATH_BYTES + 1), encoding="utf-8")
            errors = validate_read_paths(ledger_with_paths(["tools/large.py"]), root)
            self.assertTrue(any("per-file source budget" in error for error in errors))

    def test_rejects_aggregate_source_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "source").mkdir()
            paths = []
            for index in range(4):
                path = f"source/file{index}.c"
                (root / path).write_text("x" * (MAX_TOTAL_READ_BYTES // 3), encoding="utf-8")
                paths.append(path)
            errors = validate_read_paths(ledger_with_paths(paths), root)
            self.assertTrue(any("aggregate source budget" in error for error in errors))

    def test_rejects_too_many_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "source").mkdir()
            paths = []
            for index in range(5):
                path = f"source/file{index}.c"
                (root / path).write_text("x", encoding="utf-8")
                paths.append(path)
            errors = validate_read_paths(ledger_with_paths(paths), root)
            self.assertTrue(any("1-4 unique safe repository text paths" in error for error in errors))

    def test_rejects_symlink_outside_repository(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            root = Path(temp)
            (root / "tools").mkdir()
            target = Path(outside) / "secret.py"
            target.write_text("not inside repository", encoding="utf-8")
            (root / "tools/linked.py").symlink_to(target)
            errors = validate_read_paths(ledger_with_paths(["tools/linked.py"]), root)
            self.assertTrue(any("must not be a symlink" in error for error in errors))

    def test_rejects_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            (root / "tools/bad.py").write_bytes(b"print('ok')" + bytes([255]))
            errors = validate_read_paths(ledger_with_paths(["tools/bad.py"]), root)
            self.assertTrue(any("valid UTF-8" in error for error in errors))

    def test_rejects_unsafe_read_path_before_filesystem_access(self):
        with tempfile.TemporaryDirectory() as temp:
            errors = validate_read_paths(ledger_with_paths(["../outside.py"]), Path(temp))
            self.assertTrue(any("read_paths" in error or "safe repository" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
