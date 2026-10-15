#!/usr/bin/env python3
"""Verify a local Wii64 ZIP against fingerprints recorded from the reviewed archive.

The tool is read-only: it hashes bytes in-place and never extracts or executes files.
A matching digest identifies the bytes only; it does not establish safety or compatibility.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

EXPECTED_ARCHIVE_SHA256 = "cf935283854f69210b52ce668b6aa78551ab6c1086e6b25be2290b0c8077d154"
EXPECTED_FILES = {
    "apps/wii64/boot.dol": "1cc4a749a6019edd6fdd85c5f743fc275c539232845b55d2d56918c87a79fefb",
    "apps/wii64 Rice/boot.dol": "faddd5e59461bb2517571501b560aa0e201df28abc66bb70b9ebb8c77c2b5ced",
    "apps/wii64_wiivc/boot.dol": "cf80a1bfbbbd6e7f3f87ba8ec10e0f0dd8d4a38b2cd006a177ee7a19a4a5a37b",
    "apps/wii64 Rice_wiivc/boot.dol": "7c7aa017f348c8ae09becbb479abc5409638cb9f7da0dcd471e7977a1d1640ea",
}


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase SHA-256 hex digest of data."""
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Check:
    label: str
    expected: str
    actual: str | None

    @property
    def matches(self) -> bool:
        return self.actual == self.expected


def inspect_archive(path: Path) -> list[Check]:
    """Hash the ZIP and known boot.dol members without extracting the archive."""
    checks = [Check("archive", EXPECTED_ARCHIVE_SHA256, sha256_bytes(path.read_bytes()))]
    with zipfile.ZipFile(path) as archive:
        member_names = archive.namelist()
        counts = Counter(member_names)
        duplicated = sorted(name for name in EXPECTED_FILES if counts[name] > 1)
        if duplicated:
            raise ValueError(
                "duplicate archive member(s) make verification ambiguous: "
                + ", ".join(duplicated)
            )
        names = set(member_names)
        for member, expected in EXPECTED_FILES.items():
            actual = sha256_bytes(archive.read(member)) if member in names else None
            checks.append(Check(member, expected, actual))
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="path to a local wii64.zip")
    args = parser.parse_args(argv)
    try:
        checks = inspect_archive(args.archive)
    except (OSError, zipfile.BadZipFile, KeyError, ValueError) as exc:
        print(f"ERROR: cannot inspect archive: {exc}", file=sys.stderr)
        return 2

    for check in checks:
        if check.actual is None:
            status, actual = "MISSING", "(not present)"
        elif check.matches:
            status, actual = "MATCH", check.actual
        else:
            status, actual = "MISMATCH", check.actual
        print(f"{status:8} {check.label}: {actual}")
    failed = [check for check in checks if not check.matches]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} fingerprints matched.")
    if failed:
        print("Fingerprint differences do not by themselves prove tampering or risk.")
        return 1
    print("All recorded fingerprints match; this is not a safety or compatibility verdict.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
