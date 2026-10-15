import sys
import unittest
from pathlib import Path

# Make the sibling tools directory importable when unittest discovers this file.
TOOLS_DIR = Path(__file__).parents[1]
sys.path.insert(0, str(TOOLS_DIR))
import compare_wii64_rice_ini as MODULE


class CompareRiceIniTests(unittest.TestCase):
    def test_matches_profiles_by_identifier_and_preserves_flags(self):
        before = MODULE.parse_profiles("{a}\nName=Racer\nZHack\nSetting=1\n")
        after = MODULE.parse_profiles("{a}\nName=Racer\nZHack\nSetting=2\n")
        self.assertEqual(set(before), set(after))
        self.assertIn("ZHack", before["{a}"].lines)
        self.assertNotEqual(before["{a}"].lines, after["{a}"].lines)

    def test_detects_added_and_removed_ids(self):
        before = MODULE.parse_profiles("{old}\nName=Old\n")
        after = MODULE.parse_profiles("{new}\nName=New\n")
        self.assertEqual(set(after) - set(before), {"{new}"})
        self.assertEqual(set(before) - set(after), {"{old}"})

    def test_duplicate_identifier_is_an_error(self):
        with self.assertRaises(ValueError):
            MODULE.parse_profiles("{a}\nName=One\n{a}\nName=Two\n")

    def test_name_key_is_case_insensitive(self):
        profile = MODULE.parse_profiles("{a}\nnAmE=Racer\n")["{a}"]
        self.assertEqual(profile.name, "Racer")


if __name__ == "__main__":
    unittest.main()
