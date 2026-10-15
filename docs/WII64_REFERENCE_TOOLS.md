# Wii64 reference tooling

These utilities support read-only investigation of Wii64's Rice plugin configuration and a locally supplied Wii64 archive. They do **not** modify Wii64, launch emulator binaries, validate a game ROM, or prove that one configuration is faster or more accurate.

## Requirements

- Python 3.10 or newer.
- A local file obtained and used lawfully. Keep game images and proprietary assets off the public repository.
- The Rice configuration parser defaults to `cp932` (Shift-JIS-compatible Windows encoding). Override it only if the local file uses another encoding.

Run the commands below from the repository root.

## 1. Inspect Rice profiles

Print the profile matching Episode I Racer:

```sh
python3 tools/inspect_wii64_rice_ini.py /path/to/RiceVideoLinux.ini
```

Search for a different profile name:

```sh
python3 tools/inspect_wii64_rice_ini.py /path/to/RiceVideoLinux.ini --query "Mario Kart 64"
```

List profile names and identifiers without printing every setting:

```sh
python3 tools/inspect_wii64_rice_ini.py /path/to/RiceVideoLinux.ini --list
```

## 2. Compare two configuration snapshots

Keep the original and comparison INI files separate; this command never writes to either file.

```sh
python3 tools/compare_wii64_rice_ini.py original.ini modified.ini --query "STAR WARS EP1 RACER"
```

The tool reports added, removed, and changed profiles by section identifier. Its output is a literal diff; it does not interpret plugin flags or recommend settings.

## 3. Compare two named profiles

```sh
python3 tools/compare_wii64_rice_profiles.py /path/to/RiceVideoLinux.ini "STAR WARS EP1 RACER" "Mario Kart 64"
```

A query must identify exactly one profile. If the name is absent or ambiguous—including duplicate exact names—the tool exits with an error instead of silently comparing an arbitrary entry. Repeated keys and standalone flags are retained in the comparison.

## 4. Check a local Wii64 archive fingerprint

```sh
python3 tools/verify_wii64_archive.py /path/to/wii64.zip
```

The verifier hashes the ZIP and four recorded `boot.dol` members incrementally, without extracting or executing them.

- Exit code `0`: every recorded fingerprint matched.
- Exit code `1`: at least one fingerprint was missing or mismatched.
- Exit code `2`: the input could not be inspected (for example, an unreadable or corrupt ZIP).

A matching hash identifies bytes only. It is **not** a security assessment, publisher-authenticity claim, or compatibility result. A mismatch alone does not prove malicious modification.

## 5. Run the tools' unit tests

```sh
cd tools
python3 -m unittest discover -s tests -v
```

GitHub Actions runs the same standard-library test suite for changes under `tools/`. No API key, paid service, emulator binary, or ROM is needed.

## 6. Record real Wii/vWii observations

Use [the test log template](WII64_TEST_LOG_TEMPLATE.md) for each actual console session. Keep plugin, build, launch medium, controller, display mode, and the tested race segment consistent when comparing runs. Repeat a run and mark anything not observed as `not tested`.

The log distinguishes Wii64 emulator behavior from Boonta Reborn 88's independently implemented native GameCube/Wii prototype. Emulator configuration experiments are reference research—not a substitute for validating the native DOL in Dolphin and, when available, on physical hardware.

## Clean-room boundary

Do not commit or upload commercial ROMs/disc images, BIOS files, extracted proprietary textures/models/audio, emulator binaries, save files, or local archives. The repository should contain only original code, documented research, test utilities, and content whose redistribution rights are clear.
