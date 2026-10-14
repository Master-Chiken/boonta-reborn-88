#!/usr/bin/env python3
"""Create a privacy-conscious diagnostic report for the native GameCube build.

This only inspects local toolchain paths and commands. It never installs software,
scans the user's home directory, or prints the full process environment.
"""
from __future__ import annotations
import argparse
import json
import os
import platform
import shutil
from pathlib import Path
from typing import Callable, Mapping

ROOT = Path(__file__).resolve().parents[1]


def _find_executable(candidates: list[Path], names: tuple[str, ...], lookup: Callable[[str], str | None]) -> str | None:
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    for name in names:
        found = lookup(name)
        if found:
            return found
    return None


def collect_status(
    root: Path = ROOT,
    environ: Mapping[str, str] | None = None,
    system: str | None = None,
    machine: str | None = None,
    command_lookup: Callable[[str], str | None] = shutil.which,
) -> dict:
    env = dict(os.environ if environ is None else environ)
    system_name = system or platform.system()
    machine_name = machine or platform.machine()
    root = root.resolve()

    devkitpro_text = env.get("DEVKITPRO", "").strip()
    devkitpro = Path(devkitpro_text) if devkitpro_text else Path("/opt/devkitpro")
    devkitppc_text = env.get("DEVKITPPC", "").strip()
    devkitppc = Path(devkitppc_text) if devkitppc_text else devkitpro / "devkitPPC"

    compiler = _find_executable(
        [devkitppc / "bin" / "powerpc-eabi-gcc", devkitppc / "bin" / "powerpc-gekko-gcc"],
        ("powerpc-eabi-gcc", "powerpc-gekko-gcc"), command_lookup,
    )
    gamecube_rules = (devkitppc / "gamecube_rules").is_file()
    libogc = devkitpro / "libogc"
    libogc_headers = (libogc / "include" / "gccore.h").is_file() or (libogc / "include" / "ogc" / "system.h").is_file()
    libogc_archives = []
    lib_dir = libogc / "lib"
    if lib_dir.is_dir():
        # Only search the SDK's own library directory, never the whole disk.
        libogc_archives = sorted(str(path.relative_to(libogc)) for path in lib_dir.rglob("libogc.a"))
    commands = {name: command_lookup(name) for name in ("make", "python3", "cc", "xcode-select", "dkp-pacman", "dolphin-emu")}
    dols = sorted({str(path.relative_to(root)) for pattern in ("*.dol", "build/**/*.dol") for path in root.glob(pattern) if path.is_file() and path.stat().st_size > 0})

    issues: list[str] = []
    if not commands["make"]:
        issues.append("make is not on PATH")
    if not commands["python3"]:
        issues.append("python3 is not on PATH")
    if system_name == "Darwin" and not commands["xcode-select"]:
        issues.append("xcode-select is not on PATH; install Apple's Xcode Command Line Tools")
    if not env.get("DEVKITPRO"):
        issues.append("DEVKITPRO is not set in the current shell")
    if not env.get("DEVKITPPC"):
        issues.append("DEVKITPPC is not set in the current shell")
    if not gamecube_rules:
        issues.append(f"{devkitppc}/gamecube_rules is missing")
    if not compiler:
        issues.append("PowerPC GameCube compiler (powerpc-eabi-gcc or powerpc-gekko-gcc) was not found")
    if not libogc_headers:
        issues.append(f"libogc headers were not found under {libogc}/include")
    if not libogc_archives:
        issues.append(f"libogc.a was not found under {libogc}/lib")

    native_ready = not issues
    return {
        "project": "Star Wars Racer GameCube/Wii source prototype",
        "host_system": system_name,
        "host_architecture": machine_name,
        "project_root": str(root),
        "commands": commands,
        "devkitpro_path": str(devkitpro),
        "devkitppc_path": str(devkitppc),
        "devkitppc_environment_set": bool(env.get("DEVKITPPC")),
        "gamecube_rules_found": gamecube_rules,
        "cross_compiler_path": compiler,
        "libogc_headers_found": libogc_headers,
        "libogc_archives_found": libogc_archives,
        "dolphin_command_found": bool(commands["dolphin-emu"]),
        "nonempty_dol_artifacts": dols,
        "native_build_ready": native_ready,
        "issues": issues,
        "native_build_performed": False,
        "privacy_note": "No full environment dump, credentials, ROM contents, or home-directory scan was included.",
    }


def format_report(status: dict) -> str:
    lines = [
        "STAR WARS RACER — NATIVE BUILD STATUS",
        f"Host: {status['host_system']} ({status['host_architecture']})",
        f"Project: {status['project_root']}",
        f"DEVKITPRO path: {status['devkitpro_path']}",
        f"DEVKITPPC path: {status['devkitppc_path']}",
        f"DEVKITPPC environment variable set: {'YES' if status['devkitppc_environment_set'] else 'NO'}",
        f"gamecube_rules: {'FOUND' if status['gamecube_rules_found'] else 'MISSING'}",
        f"PowerPC compiler: {status['cross_compiler_path'] or 'MISSING'}",
        f"libogc headers: {'FOUND' if status['libogc_headers_found'] else 'MISSING'}",
        f"libogc.a: {', '.join(status['libogc_archives_found']) if status['libogc_archives_found'] else 'MISSING'}",
        f"make: {status['commands']['make'] or 'MISSING'}",
        f"python3: {status['commands']['python3'] or 'MISSING'}",
        f"Xcode Command Line Tools launcher: {status['commands']['xcode-select'] or 'NOT FOUND'}",
        f"Dolphin command: {status['commands']['dolphin-emu'] or 'NOT FOUND (optional)'}",
        f"Non-empty DOL files: {', '.join(status['nonempty_dol_artifacts']) if status['nonempty_dol_artifacts'] else 'NONE'}",
        f"Native build ready: {'YES' if status['native_build_ready'] else 'NO'}",
        "",
    ]
    if status["issues"]:
        lines.append("BLOCKERS:")
        lines.extend(f"- {issue}" for issue in status["issues"])
        lines += [
            "",
            "macOS setup (official devkitPro workflow):",
            "1. Run: xcode-select --install",
            "2. Install devkitpro-pacman-installer.pkg from https://github.com/devkitPro/pacman/releases/latest",
            "3. Reopen Terminal (or log out and back in), then run: sudo dkp-pacman -Syu",
            "4. Install the GameCube/Wii toolchain: sudo dkp-pacman -S gamecube-dev",
            "5. Set DEVKITPRO=/opt/devkitpro and DEVKITPPC=$DEVKITPRO/devkitPPC in your shell startup file.",
            "6. Run this report again; only start the native build after all required checks pass.",
        ]
    else:
        lines += ["All native toolchain prerequisites were found.", "Native compilation was NOT run by this diagnostic."]
    lines += ["", status["privacy_note"]]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="project root")
    parser.add_argument("--output", type=Path, help="optional report path (default: build/native-build-report.txt)")
    parser.add_argument("--json", action="store_true", help="also print JSON instead of the human-readable report")
    args = parser.parse_args()
    status = collect_status(args.root)
    report = format_report(status)
    output = args.output or (args.root / "build" / "native-build-report.txt")
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(json.dumps(status, indent=2) if args.json else report, end="" if args.json else "")
    print(f"Report saved to: {output}")
    return 0 if status["native_build_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
