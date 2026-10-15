#!/usr/bin/env python3
"""Reject known unreviewed Step 102 assets from a source-only public import."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

# These files were explicitly identified in the Step 102 provenance audit.
# A CI rejection is a HOLD for review, not a claim that a file is infringing.
EXACT_EXCLUDES = {
    "data/reference/pc_track_import_manifest.json",
    "data/demo_track_points.csv",
    "data/demo_track_edges.csv",
    "source/track_centerlines_pc.generated.h",
    "source/track_centerline.imported.h",
    "source/track_centerline.generated.h",
    "source/track_mesh.generated.h",
    "source/track_boundaries.generated.h",
}

PREFIX_EXCLUDES = (
    "assets/",
    "roms/",
    "game-dumps/",
    "disc-images/",
    "private-assets/",
    "original-assets/",
    "extracted-game-data/",
    "models/",
    "textures/",
)

# Keep the source-only policy intentionally conservative. Review every
# generated-data file separately even when it has a text-based extension.
SUFFIX_EXCLUDES = (
    ".iso", ".gcm", ".wbfs", ".nkit.iso", ".rvz", ".wad",
    ".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a", ".aiff", ".mid", ".midi",
    ".bnk", ".wem", ".sng", ".mp4", ".mov", ".avi", ".webm",
    ".obj", ".mtl", ".png", ".jpg", ".jpeg", ".bmp", ".tga", ".dds",
    ".webp", ".gif", ".tif", ".tiff", ".fbx", ".glb", ".gltf", ".dae", ".stl",
    ".blend", ".uasset", ".unitypackage",
    ".bin", ".rom", ".elf", ".dol", ".map", ".pyc", ".pyo",
    ".zip", ".7z", ".rar", ".tar", ".gz", ".xz",
)

BLOCKED_BASENAMES = {
    "track_centerlines_pc.generated.h",
    "track_centerline.imported.h",
    "track_centerline.generated.h",
    "track_mesh.generated.h",
    "track_boundaries.generated.h",
}


def excluded(relative: str) -> bool:
    path = relative.replace("\\", "/")
    lower = path.lower()
    if lower in {item.lower() for item in EXACT_EXCLUDES}:
        return True
    if path.lower().startswith(tuple(prefix.lower() for prefix in PREFIX_EXCLUDES)):
        return True
    if "__pycache__" in {part.lower() for part in Path(path).parts}:
        return True
    if Path(path).name.lower() in BLOCKED_BASENAMES:
        return True
    return lower.endswith(SUFFIX_EXCLUDES)


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
        print("Source-only import policy failed. Review/exclude these held paths:")
        for item in sorted(offenders):
            print(f" - {item}")
        return 1

    print("Source-only import policy passed: no known held asset/data paths found.")
    print("This check does not establish authorship, license, or redistribution permission.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
