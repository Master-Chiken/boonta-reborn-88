#!/usr/bin/env python3
"""Regression tests for the local track catalog server."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "serve_catalog", ROOT / "scripts" / "serve_catalog.py"
)
assert SPEC is not None and SPEC.loader is not None
serve_catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(serve_catalog)


class TrackCatalogServerTests(unittest.TestCase):
    def test_build_index_skips_malformed_and_mismatched_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tracks = root / "tracks"
            (tracks / "good").mkdir(parents=True)
            (tracks / "bad-json").mkdir()
            (tracks / "wrong-name").mkdir()
            (tracks / "bad-author").mkdir()
            (tracks / "bad-size").mkdir()

            good_manifest = {
                "schema": 1,
                "slug": "good",
                "name": "Good Track",
                "author": {"name": "Test Author"},
                "version": "1.0.0",
                "content_hash": "a" * 64,
                "model": {"sha256": "b" * 64, "size": 24, "format": "RAWM", "block_id": 115},
                "textures": [
                    {"sha256": "c" * 64, "size": 120, "format": "RAWT", "block_index": 12}
                ],
            }
            (tracks / "good" / "track.json").write_text(json.dumps(good_manifest), encoding="utf-8")
            (tracks / "bad-json" / "track.json").write_text("{", encoding="utf-8")
            (tracks / "wrong-name" / "track.json").write_text(
                json.dumps({**good_manifest, "slug": "../escape"}), encoding="utf-8"
            )
            (tracks / "bad-author" / "track.json").write_text(
                json.dumps({**good_manifest, "slug": "bad-author", "author": "not-an-object"}),
                encoding="utf-8",
            )
            (tracks / "bad-size" / "track.json").write_text(
                json.dumps({**good_manifest, "slug": "bad-size",
                            "model": {**good_manifest["model"], "size": "24"}}),
                encoding="utf-8",
            )

            index = serve_catalog.build_index(str(root))
            self.assertEqual(index["schema"], 1)
            self.assertEqual([track["slug"] for track in index["tracks"]], ["good"])
            self.assertEqual(index["tracks"][0]["download_bytes"], 144)
            self.assertEqual(index["tracks"][0]["manifest"]["model"]["block_id"], 115)


if __name__ == "__main__":
    unittest.main()
