"""Tests for the read-only Wii64 Rice profile comparison utility."""
import unittest

from inspect_wii64_rice_ini import parse_profiles
from compare_wii64_rice_profiles import find_profile, settings


class CompareProfilesTests(unittest.TestCase):
    def test_compare_preserves_flags_and_reports_literal_differences(self):
        profiles = parse_profiles(
            "{one}\nName=STAR WARS EP1 RACER\nZHack\nVIWidth=320\n"
            "{two}\nName=STAR WARS EP1 RACER (alternate)\nVIWidth=640\nOther=1\n"
        )
        a = find_profile(profiles, "STAR WARS EP1 RACER")
        b = find_profile(profiles, "alternate")
        self.assertIsNotNone(a)
        self.assertIsNotNone(b)
        self.assertEqual(settings(a)["[flag] ZHack"], [""])
        self.assertEqual(settings(a)["VIWidth"], ["320"])
        self.assertEqual(settings(b)["VIWidth"], ["640"])
        self.assertNotIn("Other", settings(a))

    def test_unique_substring_required(self):
        profiles = parse_profiles(
            "{one}\nName=Racer Alpha\n{two}\nName=Racer Beta\n"
        )
        self.assertIsNone(find_profile(profiles, "Racer"))
        self.assertEqual(find_profile(profiles, "Alpha").name, "Racer Alpha")

    def test_duplicate_keys_are_not_silently_discarded(self):
        profile = parse_profiles("{one}\nName=Example\nOption=1\nOption=2\n")[0]
        self.assertEqual(settings(profile)["Option"], ["1", "2"])


if __name__ == "__main__":
    unittest.main()
