# REA-assisted reverse-engineering workflow

**Reviewed:** 2026-10-19  
**Upstream:** [morluto/rea](https://github.com/morluto/rea)  
**Skill:** [reverse-engineer-anything](https://github.com/morluto/rea/blob/main/.agents/skills/reverse-engineer-anything/SKILL.md)

## Decision

Use REA as an optional, evidence-producing research tool for questions that depend on a shipped binary, package, or observed runtime behavior. Do not use it as a substitute for reading and testing this repository's source code. REA's own skill explicitly distinguishes binary/runtime investigations from ordinary source-repository analysis.

REA can help an agent move from artifact inspection to a documented explanation and then to a separately implemented, tested behavior. It does not guarantee recovery of original source code, prove that PC behavior matches GameCube/Wii behavior, or grant permission to reuse code or assets.

## Best-fit investigations for Boonta Reborn 88

Prioritize questions that can change a concrete implementation decision:

1. **PC behavior reference:** investigate a specific race-state, control, camera, or spline behavior in a supported local Windows build of the original PC game, when the operator has lawful access.
2. **SW_RACER_RE research:** use the public source repository first for ordinary code questions. Use REA only when a claim needs the shipped PC executable, runtime observation, or binary-level evidence that the source does not settle.
3. **Format reconnaissance:** inspect only supported, locally held artifacts to identify file/container structure and unknowns. Do not assume a PC format matches the GameCube or N64 release.
4. **Version comparison:** compare two authorized builds or captures when a specific behavioral difference needs explaining.

Do not start with a broad “reverse engineer the whole game” request. Select one feature, one target artifact, and one observable question.

## Investigation record

For each investigation, record:

- **Question and target:** exact feature, target platform/version, and artifact type.
- **Provenance:** where the artifact came from and why it may be examined; keep proprietary artifacts local.
- **Tool capability:** whether the installed REA version actually supports the artifact type and required analysis provider. Do not infer DOL, GameCube disc, or N64 ROM support from generic “native binary” wording.
- **Evidence:** relevant function/symbol/string/call graph or runtime observation, with the exact evidence supplied by the tool.
- **Conclusion confidence:** separate observed fact, source-backed fact, inference, and unknown.
- **Platform boundary:** label PC findings as PC findings; any GameCube/Wii behavior remains a hypothesis until independently validated.
- **Implementation:** write an independent behavioral specification, then implement on a review branch.
- **Tests:** add deterministic host regressions, run the native devkitPPC/libogc build, and perform a visible Dolphin/controller test where applicable.
- **Disposition:** link the resulting commit/PR and retain the evidence needed to reproduce the conclusion.

## Safety and licensing boundaries

- Never upload commercial game archives, ROMs, disc images, extracted proprietary assets, or private manifests to hosted services, AI reviewers, issues, or CI artifacts.
- REA describes its analysis as local on supported hosts, but confirm the actual execution path and any agent/provider data policies before using sensitive artifacts.
- Treat REA output as research evidence, not permission to copy code, data, textures, models, or audio.
- Review the applicable license and provenance before reusing any third-party implementation. The existing [source and artifact register](SOURCE_AND_ARTIFACT_REGISTER.md) and [SW_RACER_RE study plan](SW_RACER_RE_STUDY_PLAN.md) remain authoritative for project handling rules.
- Do not install analysis engines or alter agent configuration just to explore a source-code question. If REA is not connected or the required provider is missing, document that limitation and continue with supported repository/source research.

## Recommended first task

Use the existing [SW_RACER_RE study plan](SW_RACER_RE_STUDY_PLAN.md) to choose one unresolved PC behavior that materially affects the console prototype. First inspect the corresponding public source and behavior matrix. Only if those sources leave a binary/runtime-specific question unresolved should REA be used against a supported, authorized local PC artifact.

The immediate project acceptance gate is still a real controller-driven three-lap race in visible Dolphin, as specified in [NEXT_MILESTONE.md](NEXT_MILESTONE.md). REA research does not replace that test.
