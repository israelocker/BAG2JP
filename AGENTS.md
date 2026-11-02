# BAG2JP: owner-approved working method
The owner retained the existing local workflow on 2026-10-30 and approved the bounded work cycle below on 2026-11-02. Preserve its safety and acceptance gates.

## Start and scope
- Canonical project: D:/Dev/Recomp/BAG2JP.
- Build tree for Codex: D:/Dev/Recomp/BAG2JP-codex-build/BAG2JP. Historical ~/work paths describe Claude's previous VM.
- Check Git status before edits. Preserve prior edits, staged files, personal saves, settings and active sessions.
- Use English names for files, folders and variables. Communicate with the owner in Spanish.

## Minimal startup context
Read these files in order; sizes are measured, not assumed:

1. **AGENTS.md** (this file) — policies & workflow
2. **NOTES.md** — current index with frontmatter summaries
3. **_work/current-state.json** — inspect `active_task` as well as global `gaps`; if absent, use the task's canonical note
4. **IMPORT_STANDARD.md** — only for BAG1→BAG2 character import

Open only the source needed for the current phase. Read historical evidence for a specific disagreement, not as routine startup context. Do not load parallel indexes or clean/optimized/archive variants by default.

For sources >10 KB prefer a current digest in `notes/digests/`; check its source/hash before reuse. For already compact notes, read the canonical note rather than both note and digest.

If the index and current state answer the question, stop reading.

## Bounded work cycle (owner approved 2026-11-02)
1. Define one objective and its acceptance check.
2. Consult only the current phase's index/state/source, following the startup order above.
3. Preserve existing Git changes and run `tools/workflow/bag2_workflow.py preflight` with the recorded Python environment.
4. Contrast the requirement with code and evidence before editing. An obsolete test does not override the approved requirement; fix the test or code according to that requirement, never just to turn the suite green.
5. Make the smallest coherent change and verify at the relevant seam: documentation, host tests or actual game flow. Preserve required runtime acceptance.
6. Reuse successful searches/checks/builds/captures/reviews while their inputs/runtime remain unchanged and no new evidence contradicts them. Reuse the running process and its log; do not start a duplicate check to compensate for waiting.
7. Save small task-owned local checkpoints after appropriate verification. Label unaccepted candidates experimental/WIP, record failed or missing checks and never imply acceptance or deployment permission from a commit.
8. Update one canonical topic note when facts, procedure or task state change: result, evidence and next step. Keep NOTES.md as links, not a second status ledger.

Use a persisted plan and approval for broad changes, migrations or uncertain design decisions. For a small correction under an already approved objective, the objective/check above suffices; do not create another extensive planning round. New scope or a new consequential decision still needs approval.

## Implement and verify
- Make bounded changes in source/plugins or conversion tools. Verify original words and module/region before MIPS patches; keep guards and restoration.
- Keep framework/launcher pins. Save local framework changes as reproducible patches under patches/. Fix code generation at its source.
- Build with the verified WSL/llvm-mingw environment, two compile jobs, retaining the running process until it finishes.
- Default deployment/test target: D:/Games/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb.
- Preserve D:/Games/Bust A Groove 2 (Japan)/BAG2JP-win as the stable install; changes there require an explicit owner request.
- Back up and restore test settings. Preserve memory cards. Coordinate game instances with the task and the owner's session.
- Prefer D:/Dev/Tools/winshot/bag2_run.ps1 and tools/test/bag2_report.py. Verify actual behavior with frames, screenshots, logs and audio/cue analysis.
- A game-behavior change is complete after its relevant in-game flow passes, not merely after compilation. BAG1 tests include song end, applicable solo/duet fever and return to selection. Documentation-only changes need documentary checks/review, not a new game run; host-only tooling needs its own regression tests.
- Distinguish fresh test evidence, historical notes and untested behavior. Use human listening for subjective audio judgments.

## Save completed work
- Copy completed plugin/mod sources into mods-src/ and framework patches into patches/.
- Use Windows Git with an explicit project path; checkpoint scope and verification follow the bounded cycle above.
- Keep the existing sequential local Git workflow and branch arrangement. Generic imported skills do not impose a new branch/rebase/push/PR process on this project.
- The main project currently has no remote. A commit is a local checkpoint; uploading or publishing is separate work.
- Refresh BAG2JP-project-snapshot.tar.gz at the close of a verified milestone, not after every intermediate commit or Markdown edit. Build it from the build tree, excluding build directories, verify its contents and retain the previous snapshot. Intermediate work is protected by local Git checkpoints; heavy/generated assets outside Git require their own backups.
- Build release folders/installers when requested. Retain rejected or disabled experiments as such.

## Local efficiency (owner authorized 2026-10-30)
- Prefer verified local scripts and installed tools; use local models for bounded, reviewable bulk work, one GPU model at a time. Keep game-test GPU use separate.
- The workflow helper provides `preflight`, `build`, `test-stage-select` and `report --tag <tag>` with logs/timings in `_work/workflow/`. Drift is diagnostic: source/resource staging is still manual and must be verified before build/deploy. The exact payload generator's DUMMY capacity guard also needs an independent byte-capacity check until corrected; do not claim either safeguard is automated.
- Build reusable automation when it removes a demonstrated repeated step. Preserve the local Git, experimental deployment and in-game acceptance workflow above; measure improvements before claiming savings.

## Shared character standard (owner requested 2026-10-31)
- Follow notes/character-pipeline.md for every character. Route to bag-character-pipeline, bag-animation-matching and bag-reference-cache.
- Keep engines and orchestration shared. Character profiles carry data/capabilities; only demonstrated, scoped exceptions may introduce an adapter. Never clone Heat's pipeline for another character.
- Match meaning, beat timing, required events and predecessor transitions; unknown mappings remain unresolved. Track all source/target coverage and stock-empty/reused entries.
- Reuse visual evidence only when motion, catalog, profile, runtime and evidence hashes match. Re-audit changed packages. Preserve the single-GPU schedule.
- Distinguish configured rules, implemented tools, legacy Heat adapters and unimplemented general matching/graph optimization. Do not claim cross-character support without exercising a second profile.

## Coding Standards (applies to all new and modified code)

See `docs/coding-standards.md` for the complete standards (C, Python, TOML, documentation, testing).

Apply that canonical standard rather than copying it into more guides. Documentation updates change an existing source/index/digest, not a new parallel version. Evidence, requirements, hypotheses and historical results must remain distinguishable.

### Model Routing (Token Usage)

Use the cheapest model that can do the job well.

| Task Type | Model | Examples | Max Context |
|-----------|-------|----------|-------------|
| Light | Small/fast | Search, summarize, format, count | < 5 KB |
| Standard | General | Write code, fix bugs, docs, review | < 15 KB |
| Reasoning | Large | Architecture, design, complex debugging | < 25 KB |

**Session rotation:** New conversation when changing task, character, or when context exceeds 20 KB with irrelevant info.

**Measurement:** `py -3.13 tools/workflow/audit_docs.py inventory` reports bytes for explicit startup sets. Historical `measure_context.py` and `token-report.py` do not measure billed tokens or prove savings; use `docs/model-routing.md` for their limits.
