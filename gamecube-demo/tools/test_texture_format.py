from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "texture_format"))

from export_texture_header import gx_tiled_pixels, pack_rgb565, render_header
from validate_texture import TextureValidationError, load_texture, validate_texture

SOURCE = ROOT / "gamecube-demo" / "data" / "textures" / "original_twin_engine_panel.json"
GENERATED = ROOT / "gamecube-demo" / "source" / "generated_texture_player_pod.h"
EXPORTER = ROOT / "tools" / "texture_format" / "export_texture_header.py"


class TextureFormatTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = json.loads(SOURCE.read_text(encoding="utf-8"))

    def assert_rejected(self, mutate) -> None:
        candidate = copy.deepcopy(self.raw)
        mutate(candidate)
        with self.assertRaises(TextureValidationError):
            validate_texture(candidate)

    def test_original_texture_validates_and_matches_generated_header(self) -> None:
        texture = load_texture(SOURCE)
        self.assertEqual(texture["format"], "boonta-rgb565-v1")
        self.assertEqual((texture["width"], texture["height"]), (16, 16))
        self.assertEqual(len(texture["pixels"]), 256)
        self.assertEqual(render_header(texture), GENERATED.read_text(encoding="utf-8"))

    def test_rgb565_packing_matches_channel_quantization(self) -> None:
        self.assertEqual(pack_rgb565([255, 255, 255]), 0xFFFF)
        self.assertEqual(pack_rgb565([0, 0, 0]), 0x0000)
        self.assertEqual(pack_rgb565([255, 0, 0]), 0xF800)
        self.assertEqual(pack_rgb565([0, 255, 0]), 0x07E0)
        self.assertEqual(pack_rgb565([0, 0, 255]), 0x001F)

    def test_gx_tiling_groups_each_4_by_4_tile(self) -> None:
        candidate = copy.deepcopy(self.raw)
        candidate["width"] = 8
        candidate["height"] = 8
        candidate["pixels"] = [[x * 28, y * 28, 0] for y in range(8) for x in range(8)]
        tiled = gx_tiled_pixels(candidate)
        source = candidate["pixels"]
        self.assertEqual(tiled[0], pack_rgb565(source[0 * 8 + 0]))
        self.assertEqual(tiled[1], pack_rgb565(source[0 * 8 + 1]))
        self.assertEqual(tiled[16], pack_rgb565(source[0 * 8 + 4]))
        self.assertEqual(tiled[32], pack_rgb565(source[4 * 8 + 0]))
        self.assertEqual(tiled[48], pack_rgb565(source[4 * 8 + 4]))

    def test_invalid_format_name_and_dimensions_are_rejected(self) -> None:
        self.assert_rejected(lambda data: data.update(format="unknown-v9"))
        self.assert_rejected(lambda data: data.update(name=" "))
        self.assert_rejected(lambda data: data.update(width=True))
        self.assert_rejected(lambda data: data.update(width=6))
        self.assert_rejected(lambda data: data.update(height=0))
        self.assert_rejected(lambda data: data.update(height=512))

    def test_invalid_pixel_count_and_rgb_channels_are_rejected(self) -> None:
        self.assert_rejected(lambda data: data.update(pixels=data["pixels"][:-1]))
        self.assert_rejected(lambda data: data["pixels"].__setitem__(0, [0, 0]))
        self.assert_rejected(lambda data: data["pixels"][0].__setitem__(0, -1))
        self.assert_rejected(lambda data: data["pixels"][0].__setitem__(1, 256))
        self.assert_rejected(lambda data: data["pixels"][0].__setitem__(2, True))
        self.assert_rejected(lambda data: data["pixels"][0].__setitem__(2, 1.5))

    def test_loader_rejects_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            invalid = Path(temp) / "bad.json"
            invalid.write_text("{not-json", encoding="utf-8")
            with self.assertRaises(TextureValidationError):
                load_texture(invalid)

    def test_exporter_cli_produces_deterministic_header(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "texture.h"
            completed = subprocess.run(
                [sys.executable, str(EXPORTER), str(SOURCE), str(output)],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                render_header(load_texture(SOURCE)),
            )

    def test_generated_header_compiles_as_strict_c99(self) -> None:
        cc = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
        if cc is None:
            self.skipTest("a C compiler is not installed")
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "texture_test.c"
            binary = Path(temp) / "texture_test"
            source.write_text(
                '#include "generated_texture_player_pod.h"\\n'
                'int main(void) { return '
                'BOONTA_GENERATED_TEXTURE_ORIGINAL_TWIN_ENGINE_PANEL_WIDTH == 16U && '
                '(sizeof(boonta_generated_texture_original_twin_engine_panel_pixels) / '
                'sizeof(boonta_generated_texture_original_twin_engine_panel_pixels[0])) == 256U '
                '? 0 : 1; }\\n',
                encoding="utf-8",
            )
            compiled = subprocess.run(
                [cc, "-std=c99", "-Wall", "-Wextra", "-Werror", "-pedantic",
                 "-I", str(GENERATED.parent), str(source), "-o", str(binary)],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            self.assertEqual(subprocess.run([str(binary)], check=False).returncode, 0)


if __name__ == "__main__":
    unittest.main()
