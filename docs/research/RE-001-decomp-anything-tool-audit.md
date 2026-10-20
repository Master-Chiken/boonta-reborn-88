# RE-001 companion — decomp.anything tool audit

**Research date:** 2026-10-20  
**Upstream revision inspected:** [giveen/decomp.anything `fd8c15ea975678ae32f70988440c1fdbeac1405c`](https://github.com/giveen/decomp.anything/tree/fd8c15ea975678ae32f70988440c1fdbeac1405c)  
**Decision:** Adopt it as a candidate *local analysis workbench* for the owned N64 reference ROM; do not treat it as a route-asset exporter or as evidence of GameCube parity. No source or game data was imported into Boonta.

## Executive finding

This tool is a better fit than a one-off asset script for the unanswered *code* side of RE-001: it can split an N64 ROM, expose automatically discovered functions/data, provide assembly and cross-reference context, and let an agent investigate functions with recorded notes. It also has a separate GameCube/Wii decomp workflow based on decomp-toolkit and CodeWarrior.

It does **not** remove the current data-format problem by itself. The project code inspected contains no identified Star Wars Racer `CompWolf`/course-spline decoder integration. The N64 import path uses `splat`/MIPS disassembly for code and data analysis; custom packed course chunks still need the already-audited independent decoder/format work. An automatically named function or an agent-generated pseudocode draft is a lead, not proof of its job.

## Verified capabilities in the inspected upstream revision

### N64 ROM path

Sources: [N64 guide](https://github.com/giveen/decomp.anything/blob/fd8c15ea975678ae32f70988440c1fdbeac1405c/src/decompnet/app/guide/n64.md), [ROM split pipeline](https://github.com/giveen/decomp.anything/blob/fd8c15ea975678ae32f70988440c1fdbeac1405c/src/decompnet/rom/split.py), [import pipeline](https://github.com/giveen/decomp.anything/blob/fd8c15ea975678ae32f70988440c1fdbeac1405c/src/decompnet/app/engine.py).

- The import code recognizes `.z64`, `.n64` and `.v64` byte orders and normalizes the image to big-endian.
- The ROM split pipeline invokes `splat`, reads its assembly/data output into function and data records, and records segment bounds and compiler guess.
- The app exposes function assembly, discovered data symbols, references/call relationships, analysis tasks and optional REA/Ghidra inspection. This is useful for identifying candidate code that loads course records, dispatches a packed-block decoder, updates route progress or handles lap state.
- Matching is built around compiling candidate C against the target's expected toolchain and comparing bytes. That can validate a proposed reconstruction of a *function* where the period compiler/toolchain is supported; it is not required to use the UI for basic assembly-led analysis.

**Known coverage limitation:** the N64 guide says that this import currently splits the main segment. It does not establish comprehensive coverage of every dynamically loaded overlay. A missing candidate in the first function map therefore would not prove that the behavior is absent from the game.

### GameCube/Wii path

Sources: [GameCube/Wii project creation](https://github.com/giveen/decomp.anything/blob/fd8c15ea975678ae32f70988440c1fdbeac1405c/src/decompnet/forks/scratch_dtk.py), [CodeWarrior guide](https://github.com/giveen/decomp.anything/blob/fd8c15ea975678ae32f70988440c1fdbeac1405c/src/decompnet/app/guide/mwcc.md).

- This is a separate route: it recognizes a GameCube/Wii DOL or disc image, uses `dtk-template`/decomp-toolkit, and sets up CodeWarrior builds with a hash check.
- For disc images, it also looks for REL modules and adds readable modules to the project. The code explicitly reports that modules packed with the noted `SaCompGC` format cannot currently be analysed.
- The project’s test for this route builds a *synthetic Demo Quest GC* executable with CodeWarrior and checks the project workflow. That demonstrates its GC path on the demo, not on Star Wars Racer.

**Relevance to Boonta:** the original reference game material we have been investigating is N64/PC/Dreamcast, while GameCube is our clean-room target. A GameCube project created from Boonta's own DOL can help inspect our implementation, but it cannot reveal the original game's unavailable GameCube internals. The N64 import is the more pertinent next experiment for original behavior.

### Runtime/external tools and operating-system limits

The upstream README says the app runs locally, targets Linux x86-64 or Windows through WSL 2, and does not support macOS natively. Python 3.12+ is required; REA/Ghidra are optional analysis dependencies, and CodeWarrior is proprietary and only installed after acceptance of its license. See the [pinned README](https://github.com/giveen/decomp.anything/blob/fd8c15ea975678ae32f70988440c1fdbeac1405c/README.md).

The project states that work is local-first and no original file is uploaded. Keep that separation in practice: do not commit a ROM, a full dump, extracted assets, or proprietary course payloads to the public Boonta repository.

## How to use it for the current route/spline question

This is the recommended *focused investigation*, not a claim that it has already been run. The current analysis container has the locally supplied US N64 ROM, but no installed `decomp.anything`/splat dependency set and no network access for fetching the upstream runtime. Accordingly, the tool itself has been source-audited, not executed against this ROM in this pass.

1. On a supported Linux/WSL 2 environment, install the pinned/current upstream tool and import the legally owned local `SW Racer 1999- (US).z64`. Confirm personal-copy ownership in the import workflow. Keep all ROM-derived outputs local.
2. Read the generated intake/report first; verify detected header, compiler guess, ROM hash, code segments, function counts and data symbols. Do not start with unrestricted autopilot or broad speculative renaming.
3. Create one bounded analysis task: **find the code path that consumes packed course/model blocks and advances the player's route/race progress**.
4. Inspect functions that reference the known packed-block marker/decoder path and course-selection/loading data; follow callers and callees, inspect data references, and record the assembly addresses. Where names are auto-generated, preserve those names until a semantic interpretation is supported.
5. Produce an evidence table containing: function address, callers/callees, memory/data operands, exact instruction pattern, hypothesis, counter-evidence and confidence. Separate (a) block decompression, (b) parsing course/spline metadata, (c) runtime route cursor/projection, and (d) lap/finish state. These may be different functions.
6. Only then compare the N64 findings with the PC reference. PC names and layouts are leads, not console fact; the reviewed PC implementation itself has unfinished route-advance/binding stubs. Verify any console claim independently before adapting our clean-room implementation.

### How this relates to our existing ROM scan

Our local read-only scan previously decoded 92 `CompWolf`-prefixed records successfully (tag counts `Trak` 19, `Pupp` 27, `Part` 44 and `Scen` 2), and found 25 top-level `Trak` headers. This gives us a useful asset-side starting point, but it did **not** identify the runtime route/spline structure. The `LStr` records sampled so far look like light-flare positions in the PC analogue; they must not be re-labelled as centerline points.

The research direction is therefore complementary:

- **decomp.anything + splat:** identify *which code* reads, decodes or uses route/course records;
- **local structural parser/audit:** characterise *which packed records/data* exist and how they link;
- **Dolphin/manual observation:** test the hypothesised runtime effect without claiming static analysis alone proves the behavior.

## License/provenance boundary

The decomp.anything repository itself declares MIT. Its dependencies/toolchains retain their own licenses. The PC reverse-engineering repository `SW_RACER_RE` declares AGPL-3.0; keep it a separately identified read-only reference and do not copy/adapt its code into Boonta under the guise of tool output. The retail ROM and derived assets are not covered by the tool's MIT license.

## Disposition

- [x] Upstream code path and declared platform limits inspected at a pinned commit.
- [x] Suitable for a focused N64 *code investigation*; not a one-click spline exporter.
- [x] GameCube/Wii workflow distinguished from analysis of original N64 behavior.
- [ ] Run the importer on the local N64 ROM in a supported environment; record its intake report and function map.
- [ ] Identify and document function addresses/call paths for packed course decoding, route progression and lap crossing.
- [ ] Establish any N64 route-data layout from verified evidence before implementing the runtime cursor.

No game code, ROM, extracted payload, asset or binary was added to the Boonta repository by this research item.
