#!/usr/bin/env python3
"""Regression tests for the GameCube PR check selector."""
from __future__ import annotations

import unittest

from check_gamecube_ci_paths import MAX_PR_FILE_RECORDS, requires_gamecube_ci


def api_payload(*records: dict[str, object]) -> list[list[dict[str, object]]]:
    # gh api --paginate --slurp emits one array per response page.
    return [list(records)]


class GameCubePathSelectorTests(unittest.TestCase):
    def test_documentation_only_pr_skips_expensive_gamecube_jobs(self) -> None:
        needed, matching, count = requires_gamecube_ci(
            api_payload({"filename": "docs/ROADMAP.md"}, {"filename": "README.md"})
        )
        self.assertFalse(needed)
        self.assertEqual(matching, [])
        self.assertEqual(count, 2)

    def test_runtime_and_build_paths_require_gamecube_ci(self) -> None:
        for path in (
            "gamecube-demo/Makefile",
            "gamecube-demo/source/main.c",
            "gamecube-demo/tests/test_gameplay_state.c",
            "gamecube-demo/include/custom.h",
            "gamecube-demo/data/player_mesh.json",
            "gamecube-demo/tools/export_mesh.py",
            "tools/mesh_format/validate.py",
            "tests/test_track_format.py",
            ".github/workflows/gamecube-demo-build.yml",
        ):
            with self.subTest(path=path):
                needed, matching, _ = requires_gamecube_ci(api_payload({"filename": path}))
                self.assertTrue(needed)
                self.assertIn(path, matching)

    def test_prefixes_do_not_match_similar_unrelated_paths(self) -> None:
        for path in (
            "gamecube-demo/source-old/main.c",
            "gamecube-demo/toolshed/script.py",
            "tools/mesh_format_backup/format.py",
            "docs/gamecube-demo/README.md",
        ):
            with self.subTest(path=path):
                needed, matching, _ = requires_gamecube_ci(api_payload({"filename": path}))
                self.assertFalse(needed)
                self.assertEqual(matching, [])

    def test_rename_from_gamecube_runtime_to_docs_still_runs_ci(self) -> None:
        record = {
            "filename": "docs/old-main.c.txt",
            "previous_filename": "gamecube-demo/source/main.c",
        }
        needed, matching, _ = requires_gamecube_ci(api_payload(record))
        self.assertTrue(needed)
        self.assertIn("gamecube-demo/source/main.c", matching)

    def test_empty_api_result_fails_conservatively_toward_running_ci(self) -> None:
        needed, matching, count = requires_gamecube_ci([])
        self.assertTrue(needed)
        self.assertEqual(matching, [])
        self.assertEqual(count, 0)

    def test_three_thousand_records_fails_conservatively_toward_running_ci(self) -> None:
        payload = api_payload(*({"filename": f"docs/file-{index}.md"} for index in range(MAX_PR_FILE_RECORDS)))
        needed, matching, count = requires_gamecube_ci(payload)
        self.assertTrue(needed)
        self.assertEqual(matching, [])
        self.assertEqual(count, MAX_PR_FILE_RECORDS)

    def test_malformed_payload_is_not_silently_treated_as_documentation_only(self) -> None:
        with self.assertRaises(ValueError):
            requires_gamecube_ci([{"filename": ""}])
        with self.assertRaises(ValueError):
            requires_gamecube_ci("not-json-array")


if __name__ == "__main__":
    unittest.main()
