import unittest

from inspect_wii64_rice_ini import parse_profiles


class ParseProfilesTests(unittest.TestCase):
    def test_keeps_flags_unknown_keys_and_blank_lines(self):
        text = """{abc-45}
Name=STAR WARS EP1 RACER
ZHack

FutureSetting=7
{def-45}
Name=Mario Kart 64
"""
        profiles = parse_profiles(text)
        self.assertEqual(len(profiles), 2)
        self.assertEqual(profiles[0].name, "STAR WARS EP1 RACER")
        self.assertIn("ZHack", profiles[0].lines)
        self.assertIn("FutureSetting=7", profiles[0].lines)
        self.assertEqual(profiles[1].name, "Mario Kart 64")

    def test_ignores_text_before_first_section(self):
        profiles = parse_profiles("comment before\n{abc}\nName=Example\n")
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0].name, "Example")

    def test_name_key_is_case_insensitive(self):
        profiles = parse_profiles("{abc}\nnAmE=Case test\n")
        self.assertEqual(profiles[0].name, "Case test")


if __name__ == "__main__":
    unittest.main()
