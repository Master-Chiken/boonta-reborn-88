#!/usr/bin/env python3
"""Safely unpack the pre-reviewed Step 102 source-only bundle.

The base64 transport is split across numbered parts to fit GitHub's text-file
API. The importer runs only once .import/READY appears after every part is
uploaded. No network requests or model/API calls are made.
"""
from __future__ import annotations

import base64
import hashlib
from io import BytesIO
from pathlib import Path, PurePosixPath
import tarfile
import sys

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_DIR = ROOT / ".import"
READY = BUNDLE_DIR / "READY"
PART_GLOB = "step102-part-*.b64part"
EXPECTED_SHA256 = "35f25fe160c70990768e3b407101b657dfda2ee7a8fac30d0bca743936b1e29b"
ALLOWED_TOP = {"Makefile", "STEP102_IMPORT_README.md", "data", "source", "tests", "tools"}
BLOCKED_EXACT = {
    "data/reference/pc_track_import_manifest.json",
    "source/track_centerlines_pc.generated.h",
    "source/track_centerline.imported.h",
    "source/track_mesh.generated.h",
    "source/track_boundaries.generated.h",
}
BLOCKED_PREFIXES = (
    "assets/", "roms/", "game-dumps/", "disc-images/", "private-assets/",
    "original-assets/", "extracted-game-data/",
)
BLOCKED_SUFFIXES = (
    ".iso", ".gcm", ".wbfs", ".nkit.iso", ".rvz", ".wav", ".mp3", ".ogg",
    ".flac", ".obj", ".mtl", ".png", ".jpg", ".jpeg", ".bmp", ".tga",
    ".dds", ".bin", ".rom", ".elf", ".dol", ".map",
)


def validate_member(name: str) -> str:
    path = PurePosixPath(name)
    normalized = path.as_posix()
    if path.is_absolute() or normalized != name or ".." in path.parts or not path.parts:
        raise ValueError(f"Unsafe archive path: {name!r}")
    if path.parts[0] not in ALLOWED_TOP:
        raise ValueError(f"Unexpected top-level path: {name}")
    low = normalized.lower()
    if normalized in BLOCKED_EXACT or any(low.startswith(p) for p in BLOCKED_PREFIXES):
        raise ValueError(f"Blocked provenance path: {name}")
    if low.endswith(BLOCKED_SUFFIXES):
        raise ValueError(f"Blocked binary/media suffix: {name}")
    return normalized


def main() -> int:
    if not READY.is_file():
        print("Import bundle not marked ready; refusing to unpack.", file=sys.stderr)
        return 2
    parts = sorted(BUNDLE_DIR.glob(PART_GLOB))
    if not parts:
        print("No numbered import bundle parts were found.", file=sys.stderr)
        return 2

    encoded = b"".join(part.read_bytes().strip() for part in parts)
    raw = base64.b64decode(encoded, validate=True)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"Bundle checksum mismatch: got {digest}")

    planned: list[tuple[str, bytes]] = []
    with tarfile.open(fileobj=BytesIO(raw), mode="r:gz") as archive:
        seen: set[str] = set()
        for member in archive.getmembers():
            if not member.isfile():
                raise SystemExit(f"Non-regular archive member rejected: {member.name}")
            name = validate_member(member.name)
            if name in seen:
                raise SystemExit(f"Duplicate archive member rejected: {name}")
            seen.add(name)
            src = archive.extractfile(member)
            if src is None:
                raise SystemExit(f"Could not read archive member: {name}")
            content = src.read()
            if name == "source/career_save.c":
                # Current devkitPPC/libogc uses card_file; the archive uses the
                # older CARDFileInfo name for the same GameCube memory-card type.
                old_type = b"CARDFileInfo"
                occurrences = content.count(old_type)
                if occurrences != 2:
                    raise SystemExit(
                        "career_save.c compatibility check expected exactly two "
                        f"CARDFileInfo declarations, found {occurrences}"
                    )
                content = content.replace(old_type, b"card_file")
            elif name == "tests/mockogc/ogc/card.h":
                # Keep the host-only libogc stub compatible with the current
                # card_file type while retaining its legacy CARDFileInfo API
                # signatures for the existing syntax test.
                marker = b"} CARDFileInfo;\\n"
                occurrences = content.count(marker)
                if occurrences != 1:
                    raise SystemExit(
                        "mockogc card header compatibility check expected one "
                        f"CARDFileInfo typedef, found {occurrences}"
                    )
                content = content.replace(
                    marker, marker + b"typedef CARDFileInfo card_file;\\n"
                )
            planned.append((name, content))

    if not planned:
        raise SystemExit("The import bundle is empty.")

    # Validate the full member list before writing any file.
    for relative, content in planned:
        destination = ROOT / relative
        if destination.exists():
            raise SystemExit(f"Refusing to overwrite an existing repository file: {relative}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    for part in parts:
        part.unlink()
    READY.unlink()
    try:
        BUNDLE_DIR.rmdir()
    except OSError:
        pass
    print(f"Imported {len(planned)} reviewed source-only files from bundle {digest}.")
    print("The bundle excluded PC-mod-derived centerlines, generated mesh/boundary data, audio, models, ROMs and disc images.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
