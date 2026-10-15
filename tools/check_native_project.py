#!/usr/bin/env python3
"""Static preflight for the native GameCube build; never pretends to compile."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def audit(root: Path) -> dict:
    makefile = root / "Makefile"
    source_dir = root / "source"
    include_dir = root / "include"
    issues: list[str] = []
    make_text = makefile.read_text(errors="replace") if makefile.is_file() else ""
    if not makefile.is_file():
        issues.append("Makefile is missing")
    if "include $(DEVKITPPC)/gamecube_rules" not in make_text:
        issues.append("Makefile does not include devkitPro gamecube_rules")
    if not re.search(r"^SOURCES\s*:?=\s*source\b", make_text, re.M):
        issues.append("Makefile SOURCES does not include source/")
    c_files = sorted(source_dir.glob("*.c")) if source_dir.is_dir() else []
    if not c_files:
        issues.append("No source/*.c files found")
    main_c = source_dir / "main.c"
    if not main_c.is_file() or not re.search(r"\bmain\s*\(", main_c.read_text(errors="replace")):
        issues.append("source/main.c does not contain a main() entry point")
    headers = sorted(source_dir.glob("*.h")) + (sorted(include_dir.rglob("*.h")) if include_dir.is_dir() else [])
    missing_local_includes = []
    for c_file in c_files:
        text = c_file.read_text(errors="replace")
        for include in re.findall(r'^\s*#\s*include\s*"([^"]+)"', text, re.M):
            if (c_file.parent / include).is_file() or (include_dir / include).is_file():
                continue
            # The imported centerline is an opt-in build mode; the default build
            # uses the generated centerline and must remain buildable without it.
            if include == "track_centerline.imported.h" and "SWE1R_USE_IMPORTED_CENTERLINE" in text:
                continue
            # Generated headers are allowed only when their checked-in output exists.
            if include.endswith(".generated.h") and (source_dir / include).is_file():
                continue
            missing_local_includes.append(f"{c_file.relative_to(root)} -> {include}")
    if missing_local_includes:
        issues.extend("Missing local include: " + item for item in missing_local_includes)
    return {
        "source_c_count": len(c_files),
        "source_headers_count": len(headers),
        "main_entrypoint_found": main_c.is_file() and bool(re.search(r"\bmain\s*\(", main_c.read_text(errors="replace"))) if main_c.is_file() else False,
        "makefile_uses_gamecube_rules": "include $(DEVKITPPC)/gamecube_rules" in make_text,
        "missing_local_includes": missing_local_includes,
        "issues": issues,
        "static_preflight_passed": not issues,
        "native_compilation_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = audit(args.root.resolve())
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("NATIVE PROJECT STATIC PREFLIGHT")
        print(f"C sources: {result['source_c_count']} | headers: {result['source_headers_count']}")
        print(f"main() entry point: {'found' if result['main_entrypoint_found'] else 'MISSING'}")
        print(f"gamecube_rules: {'referenced' if result['makefile_uses_gamecube_rules'] else 'MISSING'}")
        for issue in result['issues']:
            print(f"ERROR: {issue}")
        print("Static preflight: " + ("PASS" if result['static_preflight_passed'] else "FAIL"))
        print("Native compilation performed: NO")
    return 0 if result["static_preflight_passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
