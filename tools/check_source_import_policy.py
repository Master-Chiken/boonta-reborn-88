#!/usr/bin/env python3
"""Reject known unreviewed Step 102 assets from a source-only public import."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXACT_EXCLUDES = {
    "data/reference/pc_track_import_manifest.json",
    "source/track_centerlines_pc.generated.h",
    "source/track_centerline.imported.h",
    "source/track_mesh.generated.h",
    "source/track_boundaries.generated.h",
}
PREFIX_EXCLUDES = (
    "assets/voice_en/",
    "roms/",
    "game-dumps/",
    "disc-images/",
    "private-assets/",
    "original-assets/",
    "extracted-game-data/",
)
SUFFIX_EXCLUDES = {
    ".iso", ".gcm", ".wbfs", ".nkit.iso", ".rvz",
    ".wav", ".mp3", ".ogg", ".flac",
    ".obj", ".mtl", ".png", ".jpg", ".jpeg", ".bmp", ".tga",
    ".dds", ".bin", ".rom", ".elf", ".dol", ".map",
}


def excluded(relative: str) -> bool:
    path = relative.replace("\\", "/")
    lower = path.lower()
    if lower in EXACT_EXCLUDES:
        return True
    if any(lower.startswith(prefix) for prefix in PREFIX_EXCLUDES):
        return True
    return any(lower.endswith(suffix) for suffix in SUFFIX_EXCLUDES)


def main() -> int:
    offenders = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT).as_posix()
        if ".git/" in relative or relative.startswith(".git/"):
            continue
        if excluded(relative):
            offenders.append(relative)

    if offenders:
        print("Source-only import policy failed. Review/exclude these paths:")
        for item in sorted(offenders):
            print(f" - {item}")
        return 1

    print("Source-only import policy passed: no known excluded asset paths found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
