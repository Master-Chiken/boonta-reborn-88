#!/usr/bin/env python3
"""Safely unpack the project-authored Step 102 source-only handoff bundle."""
from __future__ import annotations

import base64
import io
import tarfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "source-bundle" / "step102-source-only-import.b64"
ALLOWED_ROOTS = {"Makefile", "STEP102_IMPORT_README.md", "data", "source", "tests", "tools"}


def main() -> int:
    encoded = BUNDLE.read_bytes()
    raw = base64.b64decode(encoded, validate=True)
    imported = 0
    skipped = 0
    seen: set[str] = set()

    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        members = archive.getmembers()
        for member in members:
            name = member.name
            while name.startswith("./"):
                name = name[2:]
            path = PurePosixPath(name)
            if not name or name == ".":
                continue
            if path.is_absolute() or ".." in path.parts:
                raise SystemExit(f"Unsafe archive path rejected: {member.name!r}")
            if path.parts[0] not in ALLOWED_ROOTS:
                raise SystemExit(f"Unexpected top-level path rejected: {member.name!r}")
            if name in seen:
                raise SystemExit(f"Duplicate archive path rejected: {member.name!r}")
            seen.add(name)
            if "__pycache__" in path.parts or name.endswith(".pyc"):
                skipped += 1
                continue
            if member.isdir():
                (ROOT / Path(*path.parts)).mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise SystemExit(f"Non-regular archive entry rejected: {member.name!r}")
            source = archive.extractfile(member)
            if source is None:
                raise SystemExit(f"Could not read archive entry: {member.name!r}")
            destination = ROOT / Path(*path.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read())
            imported += 1

    print(f"Imported {imported} source/project files; excluded {skipped} cache file(s).")
    print("No ROM, disc image, model, texture, or audio payload is expected in this source-only bundle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
