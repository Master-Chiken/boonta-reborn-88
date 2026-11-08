from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from n64_reference.mips_function_inspector import (
    FunctionSymbol,
    SymbolMapError,
    disassemble_instruction,
    load_symbol_map,
    normalize_n64_rom,
    render_function,
    resolve_function,
)


class N64MipsReferenceTests(unittest.TestCase):
    def test_loads_section_relative_rom_offsets_from_toml(self) -> None:
        toml = '''
[[section]]
name = "code"
rom = 0x1000
vram = 0x80000400
size = 0x100

  [[section.functions]]
  name = "test_function"
  vram = 0x80000408
  size = 0x8
'''
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "symbols.toml"
            path.write_text(toml, encoding="utf-8")
            functions = load_symbol_map(path)

        symbol = functions["test_function"]
        self.assertEqual(symbol.rom_offset, 0x1008)
        self.assertEqual(symbol.vram, 0x80000408)
        self.assertEqual(symbol.size, 8)
        self.assertEqual(resolve_function(functions, "TEST_FUNCTION"), symbol)
        self.assertEqual(resolve_function(functions, "0x80000408"), symbol)

    def test_rejects_function_outside_section(self) -> None:
        toml = '''
[[section]]
name = "code"
rom = 0x1000
vram = 0x80000400
size = 0x20
  [[section.functions]]
  name = "outside"
  vram = 0x8000041C
  size = 0x8
'''
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "symbols.toml"
            path.write_text(toml, encoding="utf-8")
            with self.assertRaises(SymbolMapError):
                load_symbol_map(path)

    def test_normalizes_all_documented_n64_byte_orders(self) -> None:
        z64 = bytes.fromhex("80371240deadbeef")
        v64 = bytes.fromhex("37804012addeefbe")
        n64 = bytes.fromhex("40123780efbeadde")
        self.assertEqual(normalize_n64_rom(z64), z64)
        self.assertEqual(normalize_n64_rom(v64), z64)
        self.assertEqual(normalize_n64_rom(n64), z64)

    def test_disassembles_nop_and_lui(self) -> None:
        self.assertEqual(disassemble_instruction(0, 0x80001000), "nop")
        self.assertEqual(
            disassemble_instruction(0x3C088000, 0x80001004),
            "lui t0, 0x8000",
        )

    def test_branch_target_uses_pc_plus_four(self) -> None:
        # beq a0, zero, +2 instructions -> PC + 4 + 8.
        word = (0x04 << 26) | (4 << 21) | 2
        self.assertEqual(
            disassemble_instruction(word, 0x80001000),
            "beq a0, zero, 0x8000100C",
        )

    def test_render_checks_rom_bounds_and_prints_only_metadata_plus_words(self) -> None:
        symbol = FunctionSymbol(
            name="synthetic", vram=0x80000400, rom_offset=4, size=8, section="code"
        )
        rom = bytes.fromhex("803712403c08800000000000")
        rendered = render_function(rom, symbol)
        self.assertIn("Function: synthetic", rendered)
        self.assertIn("lui t0, 0x8000", rendered)
        self.assertIn("nop", rendered)
        with self.assertRaises(ValueError):
            render_function(rom[:8], symbol)

    def test_rejects_unknown_rom_header(self) -> None:
        with self.assertRaises(ValueError):
            normalize_n64_rom(bytes(64))


if __name__ == "__main__":
    unittest.main()
