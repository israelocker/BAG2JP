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

## Required Ghidra use (owner requested 2026-11-06)
- Always verify and use Ghidra through MCP during project work; do not silently substitute source inspection or offline disassembly for this requirement.
- Call `get_program_info` first. If Ghidra is closed, open the installed Ghidra and the existing project yourself; do not delegate startup back to the owner. Reuse a running instance instead of opening duplicates.
- Verified local startup: `D:/Dev/Tools/ghidra_12.1.4_PUBLIC/ghidraRun.bat D:/Dev/Recomp/BAG2JP/ghidra/BAG2JP.gpr`, then open `SLPM_862.19` in CodeBrowser. Check processes and MCP after launching: the batch wrapper can report an input-redirection error even though Java has started; do not launch it again on that message alone.
- Confirm the intended binary, region and loaded module, then perform a bounded, relevant read query. A running Java process or an open window alone does not prove that MCP works or that the correct program is selected.
- Preserve existing sessions, project data and analysis. If startup leaves MCP unavailable, diagnose the concrete failure and record it as a blocker; never claim successful use without a tool result. Installing/upgrading components or unrelated configuration changes still need permission.

## Function matching aid (owner requested 2026-11-06)
- Use `tools/bag1import/funcmatch.py` when looking for BAG1 main-executable function equivalents in BAG2, to reduce repeated manual searches. It complements mandatory Ghidra analysis; it does not replace it.
- **Experimental aid: not fully validated.** Its masked-byte matches need deeper testing for false positives and missed matches. Confirm each candidate's instructions, callers, role and region in Ghidra before relying on it or patching anything; no match does not prove that no equivalent exists.
- The current script hard-codes `_work/bag1/scus.bin`, `_work/mainexe/slpm.bin` and base `0x80010000`; verify those inputs and address/file layout before running from the canonical project root. It does not compare arbitrary regions or overlay modules. Invocation and scope are documented in the script and `notes/character-pipeline.md`.

## Tool effectiveness history (owner requested 2026-11-06)
- Use the installed tools when pertinent to the active task; consult the applicability table and per-tool history in `notes/assets.md` before choosing. Do not run every tool on every task or repeat unchanged checks just to add records. Mandatory Ghidra use above remains in force.
- After each use, append a dated entry to that tool's log under `notes/tool-evidence/`, including failures, irrelevant and counterproductive results. Record purpose, exact version/command or MCP query, input hashes/region/module, evidence, independent validation, outcome, measured time/manual rework and next action. Group related calls from one bounded trial in one entry; never silently omit a failed attempt.
- Follow the outcome definitions and entry template in `notes/assets.md`. Startup/help checks are not proof of practical utility; unknown time/savings must remain unknown. Preserve history and correct it with a new linked entry, not by rewriting a prior conclusion.
- If relevant use is blocked, unsafe, redundant with unchanged evidence or outside authorization, record the reason and evidence in that tool's log rather than forcing execution. Existing session/save protections, native PSXRecomp acceptance and tool-specific configuration prerequisites still apply.

## Resume shortcut (owner requested 2026-11-04)
When the owner only says "continúa", "sigue con lo pendiente" or similar:
1. Follow the startup order above; take `active_task.next_action` from `_work/current-state.json` as the task.
2. Read only the section of the canonical note that `next_action` names (or its digest), not the whole note.
3. State the task and its acceptance check in 2-3 lines; ask only if `next_action` requires an owner decision.
4. Token budget: keep tool output compact (details to `_work/`, 1-2 line summaries); use `headroom` for large decompiles/logs and local models/`local-vibes` for mechanical searches; crop and downscale screenshots before viewing; do not open attached images without asking what they show.
5. Before ending, update `next_action` so the next session can resume the same way.

## Bounded work cycle (owner approved 2026-11-02)
1. Define one objective and its acceptance check.
2. Consult only the current phase's index/state/source, following the startup order above.
3. Preserve existing Git changes and run `tools/workflow/bag2_workflow.py preflight` with the recorded Python environment.
4. Contrast the requirement with code and evidence before editing. An obsolete test does not override the approved requirement; fix the test or code according to that requirement, never just to turn the suite green.
5. Make the smallest coherent change and verify at the relevant seam: documentation, host tests or actual game flow. Preserve required runtime acceptance.
6. Reuse successful searches/checks/builds/captures/reviews while their inputs/runtime remain unchanged and no new evidence contradicts them. Reuse the running process and its log; do not start a duplicate check to compensate for waiting.
7. Save small task-owned local checkpoints after appropriate verification. Label unaccepted candidates experimental/WIP, record failed or missing checks and never imply acceptance or deployment permission from a commit.
8. Update one canonical topic note when facts, procedure or task state change: result, evidence and next step. Keep NOTES.md as links, not a second status ledger.
9. Cold review (owner request 2026-11-10): use the canonical trigger list in `notes/goldfish-review.md` for executable `tools/**`, `mods-src/**`, `patches/**`, payloads/manifests and the named policy files. Run its Goldfish review before closing an applicable change and record the verdict or omission in the topic note. It never replaces verification or acceptance. A `.md`-only tool note is not executable; a real payload/manifest is identified by its role, not just its filename.

Use a persisted plan and approval for broad changes, migrations or uncertain design decisions. For a small correction under an already approved objective, the objective/check above suffices; do not create another extensive planning round. New scope or a new consequential decision still needs approval.

## Continuación sin autorización (owner agreement 2026-11-12)

- La investigación interna (análisis con Ghidra, cambios de código guardados por `GASO_CAUGHT_CLIP_PUBLISHED=0`, pruebas de host, documentación) **no requiere autorización del owner** para continuar. El agent puede avanzar sin pausas ni preguntas intermedias.
- La autorización del owner **sí se requiere** solo al activar el ataque en el juego real (`CLIP_PUBLISHED=1`) y al realizar pruebas dentro de la partida (in-game flow).
- Ninguna regla existente en este archivo impide la continuación de la investigación interna sin pedir permiso.

## Uso obligatorio de herramientas disponibles (owner agreement 2026-11-12)

- Antes de iniciar cualquier tarea, el agent **debe revisar qué herramientas están disponibles** en el catálogo actual (skills, MCP servers, shell, FFmpeg, etc.) y **considerar usarlas** si son pertinentes a la tarea.
- Si una herramienta disponible puede acelerar, verificar o mejorar la calidad del trabajo (por ejemplo: `ffmpeg-skill` para grabar/analizar video, `ghidra` para reverse engineering, `bag2_run.ps1` + `bag2_report.py` para pruebas en juego, `bag2_shots.ps1` para capturas de frames), el agent **debe usarla** en lugar de trabajar solo con código o conversación.
- Si el agent decide **no usar** una herramienta disponible que es pertinente, debe **documentar por qué** en la nota del tema o en el log correspondiente.
- Esta regla se aplica en cada sesión, no solo la primera vez.

## Validación en juego grabada (owner agreement 2026-11-12)

- Toda validación dentro del juego se graba con video y el audio exacto del juego (skill `bag2-game-recording`, `tools/test/bag2_record.py`; inspección con `ffmpeg-skill`). Sin grabación válida no hay validación en juego.
- El agent revisa primero la grabación fotograma por fotograma en los momentos relevantes: Ghidra indica qué función o hook importa; los logs indican en qué fotograma/segundo revisar (el grabador sella con hora las líneas de `bag2jp_bag1_versions.log` y los latidos de fotograma; el trace y el watch se ubican por su número de fotograma). Solo cuenta una grabación con `manifest.json` `"accepted": true`.
- Solo después de su propia validación, el agent entrega video, fotogramas, logs y lo que no pudo verificar, y pregunta al owner únicamente si está conforme. No pide aprobación sin esa evidencia.
- Límites que deben declararse: no hay precisión garantizada de ±2 fotogramas. Se han observado desfases de unos 3–4, pero falta calibrar la latencia de pantalla para cada ruta; WGC puede repetir/omitir frames. La calidad subjetiva del audio sigue siendo juicio humano. La ventana debe estar visible, no minimizada y entera en el monitor principal (solo probado al 125 %); con gdigrab además debe estar sin tapar. Procedimiento y backends vigentes: notes/character-import-testing.md.

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
- The workflow helper provides `preflight`, `build`, `test-stage-select` and `report --tag <tag>` with logs/timings in `_work/workflow/`. Drift is diagnostic: source/resource staging is still manual and must be verified before build/deploy. Independently check DUMMY capacity in bytes; generator/build-copy guard status is revision-specific (see notes/character-alternate-entries.md). A correct comparison in one copy does not verify the deployed workflow; do not claim these safeguards are fully automated.
- Build reusable automation when it removes a demonstrated repeated step. Preserve the local Git, experimental deployment and in-game acceptance workflow above; measure improvements before claiming savings.

## Shared character standard (owner requested 2026-10-31)
- Follow notes/character-pipeline.md for every character. Route to bag-character-pipeline, bag-animation-matching and bag-reference-cache.
- Keep engines and orchestration shared. Character profiles carry data/capabilities; only demonstrated, scoped exceptions may introduce an adapter. Never clone Heat's pipeline for another character.
- Match meaning, beat timing, required events and predecessor transitions; unknown mappings remain unresolved. Track all source/target coverage and stock-empty/reused entries.
- Reuse visual evidence only when motion, catalog, profile, runtime and evidence hashes match. Re-audit changed packages. Preserve the single-GPU schedule.
- Distinguish configured rules, implemented tools, legacy Heat adapters and unimplemented general matching/graph optimization. Do not claim cross-character support without exercising a second profile.
- Apply the Gas-O retrospective in notes/character-pipeline.md: reuse the process, not Gas-O's IDs, constants or patches. CAUGHT acceptance covers every BAG1 import and every native BAG2 rival, both sides and all variants/companions; this is a requirement, not coverage already achieved.

## Coding Standards (applies to all new and modified code)

See `docs/coding-standards.md` for the complete standards (C, Python, TOML, documentation, testing).

Host configuration is mandatory for new/modified development code: follow its
"Configuración central obligatoria para desarrollo" section and `docs/data-dictionary.md`.
Reuse registered keys; keep configurable environment values out of consumers.
Native game constants and acceptance guards remain under their verified authorities,
not freely editable host settings. `system_config.md` records migration coverage.

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
