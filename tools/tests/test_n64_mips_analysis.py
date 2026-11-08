from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from n64_reference.mips_callgraph import build_call_graph, decode_jal_target
from n64_reference.mips_function_inspector import FunctionSymbol
from n64_reference.mips_os_candidates import analyze_function
from n64_reference.mips_string_scanner import categorize_string, extract_strings


def put_word(buffer: bytearray, offset: int, word: int) -> None:
    buffer[offset : offset + 4] = word.to_bytes(4, "big")


def jal(target: int) -> int:
    return (0x03 << 26) | ((target >> 2) & 0x03FFFFFF)


class MipsCallGraphTests(unittest.TestCase):
    def test_decodes_jal_using_pc_plus_four_region(self) -> None:
        word = jal(0x90000000)
        self.assertEqual(decode_jal_target(word, 0x8FFFFFFC), 0x90000000)

    def test_resolves_direct_jal_and_incoming_callers(self) -> None:
        rom = bytearray(0x80)
        put_word(rom, 0x00, jal(0x80000020))
        put_word(rom, 0x04, 0x00000000)
        foo = FunctionSymbol("foo", 0x80000000, 0x00, 8, "code")
        bar = FunctionSymbol("bar", 0x80000020, 0x20, 4, "code")

        result = build_call_graph(bytes(rom), {"foo": foo, "bar": bar})

        self.assertEqual(result["direct_call_site_count"], 1)
        self.assertEqual(result["resolved_edge_count"], 1)
        self.assertEqual(result["resolved_edges"][0]["target"], "bar")
        self.assertEqual(result["incoming_call_sites"][0]["static_call_sites"], 1)
        self.assertEqual(result["incoming_call_sites"][0]["callers"], ["foo"])

    def test_reports_unknown_direct_target_without_inventing_a_symbol(self) -> None:
        rom = bytearray(0x80)
        put_word(rom, 0x00, jal(0x80000040))
        foo = FunctionSymbol("foo", 0x80000000, 0x00, 4, "code")
        result = build_call_graph(bytes(rom), {"foo": foo})

        self.assertEqual(result["unresolved_direct_target_count"], 1)
        self.assertEqual(result["unresolved_target_vrams"], ["0x80000040"])
        self.assertEqual(result["resolved_edges"], [])

    def test_counts_indirect_jalr_separately(self) -> None:
        rom = bytearray(0x20)
        put_word(rom, 0x00, 0x0320F809)  # jalr ra, t9
        symbol = FunctionSymbol("dispatcher", 0x80000000, 0x00, 4, "code")
        result = build_call_graph(bytes(rom), {"dispatcher": symbol})

        self.assertEqual(result["direct_call_site_count"], 0)
        self.assertEqual(result["indirect_call_site_count"], 1)
        self.assertEqual(result["indirect_call_sites"][0]["pc"], 0x80000000)

    def test_rejects_symbol_range_outside_rom(self) -> None:
        symbol = FunctionSymbol("bad", 0x80000000, 0x20, 8, "code")
        with self.assertRaises(ValueError):
            build_call_graph(bytes(0x24), {"bad": symbol})


class MipsStringScannerTests(unittest.TestCase):
    def test_extracts_and_categorizes_local_strings(self) -> None:
        rom = b"\x00MENU START\x00data/track.bin\x00Error: bad\x00"
        found = extract_strings(rom, start_offset=0, min_length=4, min_alpha=3)
        by_text = {item.text: item.category for item in found}

        self.assertEqual(by_text["MENU START"], "game")
        self.assertEqual(by_text["data/track.bin"], "files")
        self.assertEqual(by_text["Error: bad"], "debug")

    def test_category_rules_include_menu_dialogue_and_credits(self) -> None:
        self.assertEqual(categorize_string("~fSelect~c"), "menu")
        self.assertEqual(categorize_string("Welcome Anakin"), "dialogue")
        self.assertEqual(categorize_string("Lead Programmer"), "credits")
        self.assertEqual(categorize_string("unrelated readable phrase"), "other")

    def test_respects_scan_bounds_and_minimum_length(self) -> None:
        rom = b"skip\x00short\x00Longer string\x00tail"
        found = extract_strings(rom, 5, 22, min_length=8, min_alpha=3)
        self.assertEqual([item.text for item in found], ["Longer string"])

    def test_ignores_non_ascii_and_unterminated_strings(self) -> None:
        rom = b"\xffbad ascii\x00Valid string\x00unterminated"
        found = extract_strings(rom, 0, min_length=5)
        self.assertEqual([item.text for item in found], ["Valid string"])

    def test_rejects_invalid_scan_parameters(self) -> None:
        with self.assertRaises(ValueError):
            extract_strings(b"abc", 2, 1)
        with self.assertRaises(ValueError):
            extract_strings(b"abc", min_length=0)


class MipsOsCandidateTests(unittest.TestCase):
    def test_collects_cop0_mmio_fpu_and_stack_evidence(self) -> None:
        words = [
            0x27BDFFE0,  # addiu sp, sp, -0x20
            0x40024800,  # mfc0 v0, Count
            0x40886000,  # mtc0 t0, Status
            0x3C08A440,  # lui t0, 0xA440 (VI base candidate)
            0x44480000,  # cfc1 t0, FCSR
            0x44C80000,  # ctc1 t0, FCSR
            0xC4000000,  # lwc1 f0, 0(t0)
            0x03E00008,  # jr ra
        ]
        rom = b"".join(word.to_bytes(4, "big") for word in words)
        symbol = FunctionSymbol("candidate", 0x80000000, 0, len(rom), "code")

        result = analyze_function(rom, symbol)

        self.assertEqual(result["stack_frame_bytes_candidate"], 0x20)
        self.assertEqual(result["cop0_mfc0_register_counts"], {"9": 1})
        self.assertEqual(result["cop0_mtc0_register_counts"], {"12": 1})
        self.assertEqual(result["cop1_control_reads"], 1)
        self.assertEqual(result["cop1_control_writes"], 1)
        self.assertEqual(result["mmio_lui_candidates"][0]["hardware_candidate"], "VI")
        self.assertIn("COP0_COUNT_READ", result["evidence_tags"])
        self.assertIn("N64_MMIO_BASE_CANDIDATE", result["evidence_tags"])
        self.assertIn("FLOATING_POINT_ACTIVITY", result["evidence_tags"])
        self.assertEqual(result["jr_ra_return_sites"], ["0x8000001C"])

    def test_does_not_guess_function_name_from_no_evidence(self) -> None:
        rom = bytes.fromhex("000000000000000000000000")
        symbol = FunctionSymbol("unknown", 0x80000000, 0, len(rom), "code")
        result = analyze_function(rom, symbol)

        self.assertEqual(result["evidence_tags"], [])
        self.assertEqual(result["name"], "unknown")
        self.assertIn("evidence hints only", result["interpretation"])

    def test_rejects_invalid_function_rom_range(self) -> None:
        symbol = FunctionSymbol("bad", 0x80000000, 4, 8, "code")
        with self.assertRaises(ValueError):
            analyze_function(bytes(8), symbol)


if __name__ == "__main__":
    unittest.main()
