#!/usr/bin/env python3
"""Regression tests for the clean-room boonta-mesh-v1 source/export path."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import shutil
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
CHECKED_IN_HEADERS = {
    "original_synthetic_triangle.json": GENERATED,
    "original_synthetic_diamond.json": (
        ROOT / "gamecube-demo" / "source" / "generated_mesh_diamond.h"
    ),
}
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

    def test_every_original_fixture_matches_its_checked_in_generated_header(self) -> None:
        source_names = {source.name for source in SOURCES}
        self.assertEqual(source_names, set(CHECKED_IN_HEADERS))
        for source in SOURCES:
            with self.subTest(source=source.name):
                expected = render_header(load_mesh(source))
                generated_path = CHECKED_IN_HEADERS[source.name]
                self.assertEqual(
                    generated_path.read_text(encoding="utf-8"),
                    expected,
                    f"{generated_path.relative_to(ROOT)} is stale; regenerate it from {source.name}",
                )

    def test_coordinate_and_rgba_extremes_are_accepted(self) -> None:
        candidate = copy.deepcopy(self.raw)
        candidate["vertices"][0]["position"] = [-1_000_000, 0, 0]
        candidate["vertices"][1]["position"] = [1_000_000, 0, 0]
        candidate["vertices"][2]["position"] = [0, 1_000_000, 0]
        candidate["vertices"][0]["color"] = [0, 255, 0, 255]
        candidate["vertices"][1]["color"] = [255, 0, 255, 0]
        self.assertEqual(len(validate_mesh(candidate)["vertices"]), 3)

    def test_optional_uvs_normalize_and_export(self) -> None:
        legacy = copy.deepcopy(self.raw)
        for vertex in legacy["vertices"]:
            vertex.pop("uv", None)
        mesh = validate_mesh(legacy)
        self.assertEqual([vertex["uv"] for vertex in mesh["vertices"]], [[0.0, 0.0]] * 3)

        candidate = copy.deepcopy(self.raw)
        candidate["vertices"][0]["uv"] = [0.25, 0.75]
        candidate["vertices"][1]["uv"] = [1, 0]
        candidate["vertices"][2]["uv"] = [0, 1]
        normalized = validate_mesh(candidate)
        self.assertEqual(normalized["vertices"][0]["uv"], [0.25, 0.75])
        header = render_header(candidate)
        self.assertIn("255U, 70U, 50U, 255U, 0.250000f, 0.750000f", header)

    def test_invalid_uvs_are_rejected(self) -> None:
        self.assert_rejected(lambda data: data["vertices"][0].update(uv=[0.0]))
        self.assert_rejected(lambda data: data["vertices"][0].update(uv=[0.0, 0.0, 1.0]))
        self.assert_rejected(lambda data: data["vertices"][0].update(uv=[True, 0.0]))
        self.assert_rejected(lambda data: data["vertices"][0].update(uv=[float("nan"), 0.0]))
        self.assert_rejected(lambda data: data["vertices"][0].update(uv=[1_000_001.0, 0.0]))

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

    def test_generated_headers_pass_the_c_runtime_validator(self) -> None:
        compiler = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
        if compiler is None:
            self.skipTest("a C compiler is not installed")
        for source in SOURCES:
            mesh = load_mesh(source)
            suffix = "".join(ch.lower() if ch.isalnum() else "_" for ch in mesh["name"])
            header_name = f"mesh_{suffix}.h"
            with tempfile.TemporaryDirectory() as temp:
                temp_path = Path(temp)
                header = temp_path / header_name
                header.write_text(render_header(mesh), encoding="utf-8")
                view = f"boonta_generated_mesh_{suffix}_view"
                harness = temp_path / "validate.c"
                harness.write_text(
                    '#include <stdio.h>\n'
                    f'#include "{header_name}"\n'
                    'int main(void) {\n'
                    f'  return boonta_mesh_validate(&{view}) == BOONTA_MESH_VALID ? 0 : 1;\n'
                    '}\n',
                    encoding="utf-8",
                )
                binary = temp_path / "validate"
                compiled = subprocess.run(
                    [compiler, "-std=c99", "-Wall", "-Wextra", "-Werror",
                     "-I", str(ROOT / "gamecube-demo" / "source"),
                     str(harness), "-lm", "-o", str(binary)],
                    check=False, capture_output=True, text=True,
                )
                self.assertEqual(compiled.returncode, 0, compiled.stderr)
                executed = subprocess.run([str(binary)], check=False)
                self.assertEqual(executed.returncode, 0, f"C validator rejected {source.name}")

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
