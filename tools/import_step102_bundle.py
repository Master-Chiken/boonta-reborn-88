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
    # Exact blocked paths must be case-insensitive just like prefixes/suffixes.
    if low in {item.lower() for item in BLOCKED_EXACT} or any(
        low.startswith(p.lower()) for p in BLOCKED_PREFIXES
    ):
        raise ValueError(f"Blocked provenance path: {name}")
    if low.endswith(BLOCKED_SUFFIXES):
        raise ValueError(f"Blocked binary/media suffix: {name}")
    return normalized


def validate_unique_member(name: str, seen: set[str]) -> str:
    """Reject duplicate archive paths even when their case differs."""
    key = name.casefold()
    if key in seen:
        raise ValueError(f"Duplicate archive member rejected (case-insensitive): {name}")
    seen.add(key)
    return name


def preflight_destinations(
    planned: list[tuple[str, bytes]], root: Path = ROOT
) -> list[tuple[Path, str, bytes]]:
    """Validate every output path before writing any imported file."""
    destinations: list[tuple[Path, str, bytes]] = []
    root_resolved = root.resolve()
    for relative, content in planned:
        relative_path = PurePosixPath(relative)
        if (
            relative_path.is_absolute()
            or relative_path.as_posix() != relative
            or not relative_path.parts
            or ".." in relative_path.parts
        ):
            raise ValueError(f"Unsafe destination path: {relative!r}")
        destination = root.joinpath(*relative_path.parts)
        parent = root
        for component in relative_path.parts[:-1]:
            parent = parent / component
            if parent.is_symlink():
                raise ValueError(f"Refusing to write through a symlinked directory: {parent}")
        resolved_destination = destination.resolve(strict=False)
        if not resolved_destination.is_relative_to(root_resolved):
            raise ValueError(f"Destination escapes repository root: {relative}")
        if destination.exists() or destination.is_symlink():
            raise ValueError(f"Refusing to overwrite an existing repository file: {relative}")
        destinations.append((destination, relative, content))
    return destinations


def main() -> int:
    parts = sorted(BUNDLE_DIR.glob(PART_GLOB))
    source_tree_present = (ROOT / "Makefile").is_file() and (ROOT / "source" / "main.c").is_file()

    # The first successful workflow removes its transfer payload after commit.
    # Permit a validation/build rerun from the already-imported source tree.
    if not parts and source_tree_present:
        if READY.is_file():
            READY.unlink()
        try:
            BUNDLE_DIR.rmdir()
        except OSError:
            pass
        print("Source tree already imported; no transport payload remains. Skipping extraction.")
        return 0

    if not READY.is_file():
        print("Import bundle not marked ready; refusing to unpack.", file=sys.stderr)
        return 2
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
            try:
                validate_unique_member(name, seen)
            except ValueError as exc:
                raise SystemExit(str(exc)) from exc
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
            elif name == "source/main.c":
                # Align older symbol spellings with the current libogc headers.
                replacements = (
                    (b"GX_TEXCOORD_NULL", b"GX_TEXCOORDNULL"),
                    (b"PAD_BUTTON_Z", b"PAD_TRIGGER_Z"),
                )
                for old_symbol, new_symbol in replacements:
                    occurrences = content.count(old_symbol)
                    if occurrences != 1:
                        raise SystemExit(
                            f"main.c compatibility check expected one {old_symbol!r}, "
                            f"found {occurrences}"
                        )
                    content = content.replace(old_symbol, new_symbol)
            elif name == "tests/mockogc/ogc/card.h":
                # Keep the host-only libogc stub compatible with the current
                # card_file type while retaining its legacy CARDFileInfo API
                # signatures for the existing syntax test.
                marker = b"} CARDFileInfo;\n"
                occurrences = content.count(marker)
                if occurrences != 1:
                    raise SystemExit(
                        "mockogc card header compatibility check expected one "
                        f"CARDFileInfo typedef, found {occurrences}"
                    )
                content = content.replace(
                    marker, marker + b"typedef CARDFileInfo card_file;\n"
                )
            elif name == "tests/mockogc/ogc/gx.h":
                marker = b"#define GX_TEXCOORD_NULL 0\n"
                if content.count(marker) != 1:
                    raise SystemExit("mockogc gx.h expected the legacy texture-coordinate marker")
                content = content.replace(
                    marker, marker + b"#define GX_TEXCOORDNULL GX_TEXCOORD_NULL\n"
                )
            elif name == "tests/mockogc/ogc/pad.h":
                marker = b"#define PAD_BUTTON_Z 0x0010\n"
                if content.count(marker) != 1:
                    raise SystemExit("mockogc pad.h expected the legacy Z-button marker")
                content = content.replace(
                    marker, marker + b"#define PAD_TRIGGER_Z PAD_BUTTON_Z\n"
                )
            planned.append((name, content))

    if not planned:
        raise SystemExit("The import bundle is empty.")

    # Validate every destination before writing any file to avoid partial imports.
    try:
        destinations = preflight_destinations(planned)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    for destination, relative, content in destinations:
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
