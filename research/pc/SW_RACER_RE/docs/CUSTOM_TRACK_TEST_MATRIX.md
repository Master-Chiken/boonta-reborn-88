# Custom-Track and Asset Validation Matrix

**Prepared:** 2026-10-16  
**Repository snapshot:** `Master-Chiken/SW_RACER_RE` default branch at audit time  
**Purpose:** Separate tests that can run on CI without a game installation from tests that require local game files or interactive runtime validation.

## Current coverage found

This inventory is based on the repository files and workflows inspected during the audit. “Found” means test code exists; it does not claim the current workflow passed unless a run is explicitly linked in an issue or Actions result.

| Area | Existing test / workflow | What it covers | Main limitation |
|---|---|---|---|
| RAW model and discrete assets | `tests/test_raw_model_validator.py`; `integrity_check.yml`; malformed offset-table regression tests merged via [PR #19](https://github.com/Master-Chiken/SW_RACER_RE/pull/19) on 2026-10-17 | Synthetic RAWM/RAWS/RAWT checks plus adversarial truncated tables, reversed/unaligned offsets, bad palette ranges, multi-entry model/spline/texture boundaries and invalid IDs; the recorded Linux suite and Windows Integrity Check runs on PR #19's head passed ([Linux run](https://github.com/Master-Chiken/SW_RACER_RE/actions/runs/38950301439), [Windows run](https://github.com/Master-Chiken/SW_RACER_RE/actions/runs/38950301662)). PR #19 is merged into `master`; these links are historical evidence for that change, not a claim about current workflow availability | Does not yet prove parity against a real packed stock block or an independent tool |
| Track catalog server | `tests/test_track_catalog_server.py`; `integrity_check.yml` | Valid index output; malformed JSON; path-like slug; wrong author type; wrong size type; download byte totals | Tests the local index-building helper, not a complete client-to-server download flow |
| Catalog URL policy | `tests/catalog_http_policy_test.cpp`; `catalog-http-policy-test.yml` | Localhost/loopback allow-list and rejection of public/lookalike hosts for plain HTTP; GCC/Clang and sanitizer matrix | The policy helper test alone does not prove redirect handling, download/hash validation, and manifest publication work end to end |
| Cursor policy | `tests/cursor_policy_test.cpp`; `cursor-policy-test.yml` | Software cursor visibility policy and scale factor checks | Does not replace visual testing across display modes in a running game |
| Cinematic audio volume | `tests/cinematic_audio_test.cpp`; `cinematic-audio-test.yml` and `integrity_check.yml` | Six cases for `-s` / enabled sound and volume scaling/clamping | Automated policy test is not proof of audible behavior in the Windows game |
| Manifest, registry, virtual blocks | [PR #18](https://github.com/Master-Chiken/SW_RACER_RE/pull/18) (open; latest head `95a8026bafb09374c7ab6efa91d8dfdd45a9cec6`); `tests/track_manifest_integration_test.cpp`; portable policy matrix | Shared policy tests plus Windows integration of the production C++ manifest parser: valid/invalid JSON/schema/slug/hash/placement, duplicate texture indices, invalid-entry scanning, content-store SHA-256/size enforcement, atomic view installation, and missing-spline-source validation added from issue #20. Earlier portable and Windows checks passed on an earlier PR head ([policy matrix](https://github.com/Master-Chiken/SW_RACER_RE/actions/runs/38949879654), [Windows run](https://github.com/Master-Chiken/SW_RACER_RE/actions/runs/38949879674)); the current head has zero GitHub check runs as of 2026-10-19 | Does not yet prove stock-entry fallback across every asset kind, full custom track selection/racing, or stock/custom cache switching inside the running game |
| In-game custom-track flow | Manual runtime / game assets required | Race selection, loading, pre-race camera, racing, return to stock track, save-record handling | Must be run in the target game; source-level tests cannot prove interactive correctness |

## Current PR coverage notes (2026-10-16)

PR #19 was merged on 2026-10-17, so its raw-asset offset tests are now included in `master`. PR #18 remains open; its current head includes the issue #20 spline-source fix, but the tests on that latest head have not been run and GitHub reports no check runs for it. Treat the linked PR #18 runs as historical evidence for an earlier head only. Do not describe the PR #18 changes as shipped in `master` until reviewed, validated, and merged.

## Prioritised test backlog

### P0 — isolate and test manifest validation

Test the smallest public, pure functions in `track_manifest.cpp` with temporary directories/files:
- valid minimal manifest is accepted;
- unknown schema, missing required fields, wrong JSON types, malformed SHA-256, and unsafe slug/path are rejected;
- absent blob and size-mismatched blob fail at asset-read time;
- a failed install does not leave partially installed virtual views;
- scanning ignores invalid manifests and continues to valid ones.

Use synthetic JSON and short synthetic blobs; no copyrighted game data is required.

### P0 — make virtual-block behavior testable

Introduce a seam around file reading / stock-block access if necessary so tests can verify:
- short headers, oversized counts, truncated offset tables and non-monotonic/out-of-range offsets fail safely;
- declared replacement entries override only their declared indices;
- undeclared entries fall back to the corresponding stock entries;
- failed validation leaves the previous/stock mapping intact rather than half-installing;
- removing a view restores the original stock path/data;
- model, spline and texture block handling are consistent.

Avoid refactoring the parser and runtime mapping in one giant change. Add a testable unit and tests first, then change integration code in a separate small PR.

### P1 — test catalog download as a transaction

With a local fake HTTP server and temporary content store, exercise:
- valid HTTPS catalog flow (plus loopback HTTP only for development);
- redirect response rejection, including redirects from catalog and blob requests;
- wrong hash, wrong size, truncated blob and malformed manifest rejection;
- existing valid cached blob reuse; corrupted cached blob rejection;
- interrupted download leaves no published partial manifest;
- successful fetch publishes the manifest atomically only after every declared blob validates.

Keep the server local and deterministic so CI requires no public network access.

### P1 — custom-track game regression checklist

For each candidate track, record the binary/build version, track slug, launch settings, logs, and exact outcome:
1. Launch into free play and select the custom track.
2. Load model, spline and textures; complete the pre-race sequence and start the race.
3. Finish or exit the race, return to menu and load a stock track.
4. Switch from a stock track to a custom track and back again to catch stale cache/path state.
5. Confirm no high-score/name-entry write occurs for a custom track without a save slot.
6. Repeat with a malformed or incomplete track and confirm clean rejection/fallback instead of a crash.

Use only legally obtained local stock data and community-created test tracks whose use is permitted. Do not commit the original executable, proprietary blocks, or asset dumps.

### P2 — differential asset round-trip

Use `swe1r-assets` as an independent oracle where compatible:
- record tool versions and SHA-256 of input/output;
- compare unchanged deserialise/serialise output byte-for-byte when the tool's documented bit-perfect property applies;
- compare metadata (entry count, offsets, ids, sizes) for model/spline/sprite/texture blocks;
- explain known unsupported cases instead of treating any mismatch as an automatic bug.

Do not add the external package as a production dependency just to run a validation experiment.

## CI command baseline

These Python tests are already invoked by `.github/workflows/integrity_check.yml`:

```sh
python tests/test_raw_model_validator.py
python tests/test_track_catalog_server.py
```

The small C++ policy tests are compiled with strict warnings and run in their dedicated workflows; for example:

```sh
g++ -std=c++20 -Wall -Wextra -Werror -pedantic tests/cinematic_audio_test.cpp -o cinematic_audio_test
./cinematic_audio_test
```

Equivalent commands exist for `tests/catalog_http_policy_test.cpp` and `tests/cursor_policy_test.cpp`; the dedicated workflows also run GCC/Clang and sanitizer variants where configured.

## Definition of done

- Every P0 item is either covered by an automated test or has a clear, documented reason why only manual runtime validation can test it.
- CI runs all portable tests without requiring the original game installation.
- Runtime-only checks have a repeatable checklist, required files clearly described, and evidence attached to the relevant issue/PR.
- The test report distinguishes **compiled**, **automated test passed**, and **verified in game**; these statuses must not be conflated.
