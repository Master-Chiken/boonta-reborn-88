#!/usr/bin/env python3
"""Regression tests for the clean-room boonta-mesh-v1 source/export path."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "mesh_format"))

from export_mesh_header import render_header
from validate_mesh import (
    FORMAT,
    MAX_INDICES,
    MAX_VERTICES,
    MeshValidationError,
    load_mesh,
    validate_mesh,
)

SOURCE = ROOT / "gamecube-demo" / "data" / "meshes" / "original_synthetic_triangle.json"
SOURCES = sorted((ROOT / "gamecube-demo" / "data" / "meshes").glob("*.json"))
GENERATED = ROOT / "gamecube-demo" / "source" / "generated_mesh.h"
EXPORTER = ROOT / "tools" / "mesh_format" / "export_mesh_header.py"


class MeshFormatTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = json.loads(SOURCE.read_text(encoding="utf-8"))

    def assert_rejected(self, mutate) -> None:
        candidate = copy.deepcopy(self.raw)
        mutate(candidate)
        with self.assertRaises(MeshValidationError):
            validate_mesh(candidate)

    def test_authored_example_validates_and_matches_generated_header(self) -> None:
        mesh = load_mesh(SOURCE)
        self.assertEqual(mesh["format"], FORMAT)
        self.assertEqual(mesh["name"], "original-synthetic-triangle")
        self.assertEqual(len(mesh["vertices"]), 3)
        self.assertEqual(mesh["indices"], [0, 1, 2])
        self.assertEqual(render_header(mesh), GENERATED.read_text(encoding="utf-8"))

    def test_all_original_fixtures_validate_and_export_independently(self) -> None:
        self.assertGreaterEqual(len(SOURCES), 2)
        names = set()
        for source in SOURCES:
            mesh = load_mesh(source)
            self.assertNotIn(mesh["name"], names)
            names.add(mesh["name"])
            with tempfile.TemporaryDirectory() as temp:
                output = Path(temp) / "mesh.h"
                completed = subprocess.run(
                    [sys.executable, str(EXPORTER), str(source), str(output)],
                    check=False, capture_output=True, text=True,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(output.read_text(encoding="utf-8"), render_header(mesh))

    def test_coordinate_and_rgba_extremes_are_accepted(self) -> None:
        candidate = copy.deepcopy(self.raw)
        candidate["vertices"][0]["position"] = [-1_000_000, 0, 0]
        candidate["vertices"][1]["position"] = [1_000_000, 0, 0]
        candidate["vertices"][2]["position"] = [0, 1_000_000, 0]
        candidate["vertices"][0]["color"] = [0, 255, 0, 255]
        candidate["vertices"][1]["color"] = [255, 0, 255, 0]
        self.assertEqual(len(validate_mesh(candidate)["vertices"]), 3)

    def test_name_limit_and_non_integer_indices_are_rejected(self) -> None:
        self.assert_rejected(lambda data: data.update(name="n" * 81))
        self.assert_rejected(lambda data: data.update(indices=[0, True, 2]))
        self.assert_rejected(lambda data: data.update(indices=[0, 1.0, 2]))

    def test_missing_or_wrong_root_fields_are_rejected(self) -> None:
        self.assert_rejected(lambda data: data.update(format="unknown-mesh-v9"))
        self.assert_rejected(lambda data: data.pop("format"))
        self.assert_rejected(lambda data: data.pop("name"))
        self.assert_rejected(lambda data: data.pop("vertices"))
        self.assert_rejected(lambda data: data.pop("indices"))
        self.assert_rejected(lambda data: data.update(name=" "))

    def test_vertex_positions_are_strict_and_finite(self) -> None:
        self.assert_rejected(lambda data: data["vertices"][0].update(position=[0.0, 0.0]))
        self.assert_rejected(lambda data: data["vertices"][0].update(position=[True, 0.0, 0.0]))
        self.assert_rejected(lambda data: data["vertices"][0].update(position=[float("nan"), 0.0, 0.0]))
        self.assert_rejected(lambda data: data["vertices"][0].update(position=[float("inf"), 0.0, 0.0]))
        self.assert_rejected(lambda data: data["vertices"][0].update(position=[1_000_001.0, 0.0, 0.0]))
        self.assert_rejected(lambda data: data["vertices"][0].update(position=[10**1000, 0.0, 0.0]))

    def test_rgba8_channels_are_strict(self) -> None:
        self.assert_rejected(lambda data: data["vertices"][0].update(color=[255, 0, 0]))
        self.assert_rejected(lambda data: data["vertices"][0].update(color=[255, -1, 0, 255]))
        self.assert_rejected(lambda data: data["vertices"][0].update(color=[256, 0, 0, 255]))
        self.assert_rejected(lambda data: data["vertices"][0].update(color=[True, 0, 0, 255]))
        self.assert_rejected(lambda data: data["vertices"][0].update(color=[1.5, 0, 0, 255]))

    def test_counts_and_triangle_shape_are_bounded(self) -> None:
        self.assert_rejected(lambda data: data.update(vertices=[]))
        self.assert_rejected(lambda data: data.update(indices=[]))
        self.assert_rejected(lambda data: data.update(indices=[0, 1, 2, 0]))
        self.assert_rejected(lambda data: data.update(vertices=data["vertices"] * (MAX_VERTICES + 1)))
        self.assert_rejected(lambda data: data.update(indices=[0, 1, 2] * ((MAX_INDICES // 3) + 1)))

    def test_indices_and_degenerate_triangles_are_rejected(self) -> None:
        self.assert_rejected(lambda data: data.update(indices=[0, 1, 3]))
        self.assert_rejected(lambda data: data.update(indices=[0, -1, 2]))

        def make_degenerate(data):
            data["vertices"][2]["position"] = list(data["vertices"][1]["position"])

        self.assert_rejected(make_degenerate)

    def test_loader_rejects_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            bad_file = Path(temp) / "invalid.json"
            bad_file.write_text("{not-json", encoding="utf-8")
            with self.assertRaises(MeshValidationError):
                load_mesh(bad_file)

    def test_exporter_cli_produces_deterministic_header(self) -> None:
        expected = render_header(load_mesh(SOURCE))
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "mesh.h"
            completed = subprocess.run(
                [sys.executable, str(EXPORTER), str(SOURCE), str(output)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), expected)


if __name__ == "__main__":
    unittest.main()
