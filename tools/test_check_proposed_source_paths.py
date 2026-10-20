"""Regression tests for the trusted proposed-path import guard."""
from __future__ import annotations

import unittest

import check_proposed_source_paths as proposed


class ProposedPathTests(unittest.TestCase):
    def test_blocks_known_held_paths_across_paginated_api_payload(self) -> None:
        payload = [
            [
                {"filename": "source/main.c"},
                {"filename": "data/demo_track_points.csv"},
            ],
            [
                {"filename": "data/demo_track_edges.csv"},
                {"filename": "SOURCE/TRACK_CENTERLINE.GENERATED.H"},
            ],
        ]
        self.assertEqual(
            proposed.blocked_filenames(payload),
            [
                "SOURCE/TRACK_CENTERLINE.GENERATED.H",
                "data/demo_track_edges.csv",
                "data/demo_track_points.csv",
            ],
        )

    def test_blocks_all_current_exact_exclusions_case_insensitively(self) -> None:
        payload = [[
            {"filename": "DATA/REFERENCE/PC_TRACK_IMPORT_MANIFEST.JSON"},
            {"filename": "SOURCE/TRACK_CENTERLINE.IMPORTED.H"},
            {"filename": "source/track_mesh.generated.h"},
            {"filename": "SOURCE/TRACK_BOUNDARIES.GENERATED.H"},
        ]]
        self.assertEqual(
            proposed.blocked_filenames(payload),
            [
                "DATA/REFERENCE/PC_TRACK_IMPORT_MANIFEST.JSON",
                "SOURCE/TRACK_BOUNDARIES.GENERATED.H",
                "SOURCE/TRACK_CENTERLINE.IMPORTED.H",
                "source/track_mesh.generated.h",
            ],
        )

    def test_allows_normal_source_and_workflow_paths(self) -> None:
        payload = [
            {"filename": "source/main.c"},
            {"filename": ".github/workflows/source-import-policy.yml"},
            {"filename": "tools/check_proposed_source_paths.py"},
        ]
        self.assertEqual(proposed.blocked_filenames(payload), [])

    def test_flattens_paginated_and_single_page_payloads(self) -> None:
        self.assertEqual(
            proposed.proposed_filenames([[{"filename": "source/main.c"}], [{"filename": "README.md"}]]),
            ["README.md", "source/main.c"],
        )
        self.assertEqual(
            proposed.proposed_filenames([{"filename": "source/main.c"}]),
            ["source/main.c"],
        )

    def test_blocks_renames_away_from_a_held_filename(self) -> None:
        payload = [{
            "filename": "source/renamed_track_data.c",
            "previous_filename": "source/track_centerline.generated.h",
            "status": "renamed",
        }]
        self.assertEqual(
            proposed.blocked_filenames(payload),
            ["source/track_centerline.generated.h"],
        )

    def test_allows_empty_api_payloads(self) -> None:
        self.assertEqual(proposed.proposed_filenames([]), [])
        self.assertEqual(proposed.proposed_filenames([[]]), [])

    def test_rejects_malformed_api_payloads(self) -> None:
        for payload in ({}, [[{}]], [["not-a-file-object"]]):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    proposed.proposed_filenames(payload)

    def test_rejects_absolute_and_traversal_filenames(self) -> None:
        for filename in ("/source/main.c", "../outside.c", "source/../outside.c", "source//main.c"):
            with self.subTest(filename=filename):
                with self.assertRaises(ValueError):
                    proposed.proposed_filenames([{"filename": filename}])


if __name__ == "__main__":
    unittest.main()
