#!/usr/bin/env python3
"""Guard the HD model replacement default against accidental opt-in regressions.

Run from the repository root:
    python scripts/check_hd_replacement_default.py
"""

from pathlib import Path
import re
import sys

SOURCE = Path("dinput_hook/imgui_utils.cpp")


def main() -> int:
    if not SOURCE.is_file():
        print(f"FAIL: source file not found: {SOURCE}")
        return 2

    source = SOURCE.read_text(encoding="utf-8")

    checks = [
        (
            "fresh in-memory configuration defaults HD replacement to off",
            r"\.HD_replacement\s*=\s*false\s*,",
        ),
        (
            "missing INI setting defaults HD replacement to off",
            r'imgui_state\.HD_replacement\s*=\s*config::get_int\(\s*"settings"\s*,\s*"hd_replacement"\s*,\s*0\s*\)',
        ),
        (
            "user-selected HD replacement setting is still persisted",
            r'config::set_bool\(\s*"settings"\s*,\s*"hd_replacement"\s*,\s*imgui_state\.HD_replacement\s*\)',
        ),
    ]

    failures = 0
    for description, pattern in checks:
        if re.search(pattern, source):
            print(f"PASS: {description}")
        else:
            print(f"FAIL: {description}")
            failures += 1

    if failures:
        print(f"\n{failures} HD replacement default check(s) failed.")
        return 1

    print("\nAll HD replacement default checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
