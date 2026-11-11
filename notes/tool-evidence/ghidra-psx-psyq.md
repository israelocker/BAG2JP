---
id: tool-evidence-ghidra-psx-psyq
title: "Evidencias: Ghidra, PSX y PsyQ"
tags: ["tools", "evidence"]
summary: "Historial de Ghidra MCP y soporte PSX/PsyQ; no certifica identificación automática."
related: ["notes/assets.md", "AGENTS.md"]
created: "2026-11-06"
updated: "2026-11-06"
doc_kind: evidence
---

# Ghidra / PSX / PsyQ — historial

## 2026-11-07 — ghidra-037 — pitch sign of tone shift (corrects ghidra-034)

- Actual MCP: `tools.ghidra.get_program_info` (SLPM_862.19, sha ea5a1668…), decompile `_spu_note2pitch` 0x80039314 and `SsPitchFromNote` 0x8003ba78. Read-only. Also read result overlay state 4/5 (0x1909 then Win 0x100).
- Finding: semitones = note − center + (shift+fine)/128, so shift raises pitch; effective centre = center − shift/128. ghidra-034 stated the opposite sign. Independent validation: SPU dump of run `20261107T114911955759Z` showed voice-14 pitch 0x0465 vs expected 0x0416; after fixing `vab_budget.resample_samples`, run `20261107T120108356029Z` shows 0x0416 and recorded-audio NCC 0.643 (was 0.09). Outcome: useful (root cause of sharp resampled voices). Time unknown. Next: owner listening.

## 2026-11-07 — ghidra-036 — victory name cue and missing-cue behaviour

- Actual MCP: installed bridge `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/gaso/probe_call.py read_memory` at 0x80051424 → `_work/gaso/victory-table.json`; `probe_motion_binding.py 0x8002e2d0` (re-read) → `binding-0x8002e2d0.c`. get_program_info first: existing GUI 12.1.4 JP SLPM_862.19. Read-only.
- Finding: victory name table (u16 per character) gives chr9 cue 0x1909 (Heat 0x1007 … Shorty 0x1813), so the earlier 0x1907/0x1908 premise (copied from Heat's index) was wrong; FUN_8002e2d0 returns -1 without key-on when a cue is absent. Independent validation: faster-whisper transcripts of stock Bi-O 0x1909 ("BIO!"), 0x3090/0x3091 (VS names) and 0x1907 ("NOOOO", Bi-O's own line); rebuilt banks transcribe "Gas-O"; full double Gas-O match `20261107T005347685398Z` completes. Outcome: useful (correct cue targets). Time unknown. Next: owner in-game listening of VS intro and victory.

## 2026-11-06 — ghidra-035 — sound-table key-on path for announcer playback rate

- Actual MCP: installed bridge `_work/gaso/probe_pitch.py` (get_program_info first: existing GUI 12.1.4 JP SLPM_862.19) for `SsUtKeyOnV` 80039884, `_work/gaso/probe_xrefs.py 0x80039884` → `xrefs-0x80039884.json`, `probe_motion_binding.py 0x8002e2d0` → `binding-0x8002e2d0.c`. Read-only.
- Finding: only caller FUN_8002e2d0; sound table entries are 6×u16 (vab, prog, cue, vol=(w>>6)&0x7f, note=(w&0x3fff)>>7, fine=w&0x7f). Character cue records use note 60, so playback rate = 44100·2^((60−centre)/12). Independent validation: exported WAVs at that rate transcribed "Gas-O" by faster-whisper and confirmed by owner listening. Outcome: useful (correct WAV export, record reuse for `rename_cue`). Time unknown. Next: in-game owner listening of the Gas-O name calls.

## 2026-11-06 — ghidra-034 — VAB tone pitch fields before voice resampling

- Actual MCP: installed bridge `_work/gaso/probe_pitch.py Pitch Note Vm` (get_program_info first: existing GUI 12.1.4 JP SLPM_862.19; `search_functions_by_name`) then `probe_motion_binding.py 0x8003b9c4 0x8003ba10 0x80039314`. No writes/overlay/restart. Evidence `_work/gaso/pitch-ghidra.json`, `binding-0x8003ba10.c`, `binding-0x80039314.c`.
- Finding: `note2pitch2` passes tone attribute bytes +4 (center) and +5 (shift) to `SsPitchFromNote`; `_spu_note2pitch` computes semitones `center + (shift+fine)/128 - note`. A sample resampled by factor r therefore keeps pitch when center/shift rise by `12*log2(1/r)` semitones. Independent check pending: host decode/re-encode test and in-game listening. Same session: HeatBAG2 8MiB dump (`224838746523Z`) shows stage-dependent slot3 (16448 vs Strike 4336), free 79568; ghidra not needed for that dump read (bank table addresses from ghidra-032). Outcome: useful, defines the pitch compensation. Time/savings unknown. Next: implement dedup + resample in the Gas-O asset build.

## 2026-11-06 — ghidra-033 — SystemError caller from live capture

- Actual MCP: `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/gaso/probe_motion_binding.py 0x8002e058` (session catalog exposed no Ghidra tool; installed stdio bridge used, as before). get_program_info first: existing GUI 12.1.4 JP SLPM_862.19. No writes/overlay/restart. Evidence `_work/gaso/binding-0x8002e058.c`.
- Input: live observer log `20261106T223630963763Z-gaso-system-error-capture` a0=0x56 a1=1 ra=8002E060. Decompile of FUN_8002de5c maps code1 to `SsVabOpenHead<0`. Independent check: dump-based SPU arithmetic (pending 110144 > free 91664) and stock Bi-O VAB parse (64032 body). Outcome: useful, narrows cause to SPU budget; transfer-lock path not excluded. Time/savings unknown. Next: double Gas-O on native stage, then size reduction decision.

## 2026-11-06 — ghidra-032 — guarded SystemError observation and VAB predicates

- Actual MCP: installed `D:/Dev/Tools/ghidra-mcp-python/python.exe` running `_work/gaso/probe_system_error_word.py` (read_memory80049F94/16), `probe_vab_registration.py` (SsVabOpenHead/SsVabTransBody), then the latter with `_SsVabOpenHeadWithMode`. get_program_info first each time; existing GUI12.1.4 JP main SLPM_862.19 SHAea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe. No Ghidra writes, overlay, restart or configuration edits. All queries succeeded; reports system-error-word-mcp.json/vab-registration*.json under `_work/gaso/`.
- Confirmed original words240A00A0/01400008/240900A1, VAB head/body failure predicates and allocator limit80000. Decompiler continuation artifacts remain; predicates alone are not the live failure reason. Independent audit of preserved8MiB dump records five active banks in adjacent vab-allocations.json, not allocation-failure proof.
- Host diagnostic RED/GREEN test verifies one-shot argument logging, CPU preservation and restoration of an equivalent instruction substitution; diagnostic build/deploy passed, live capture pending. This is observation, not an error bypass or gameplay correction. Time/manual rework/savings unknown. Next: capture actual SystemError arguments/caller, then contrast with the predicates before any resource change.

## 2026-11-06 — ghidra-031 — candidate SystemError return

- Actual MCP: installed Python running `_work/gaso/probe_motion_binding.py 0x80049f94`; get_program_info first, existing Ghidra12.1.4 GUI JP SLPM_862.19 main SHA ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe. No writes/overlay/restart. Successful decompile identifies SystemError(char,long), BIOS call A0. Evidence binding-query-0x80049f94.json / binding-0x80049f94.c.
- Independent bounded check: scan_loader_stack_candidates.py uses original main JAL words and preserved8MiB dump, not a live debugger. Candidate saved returns include8002E060→SystemError and the preceding P2 bank-registration chain; evidence loader-stack-candidates.json in215858020561Z run. No known current SP/PC: not a validated unwind or proof of error code. An inline PowerShell attempt failed quoting before execution; dedicated script succeeded.
- Outcome: useful narrowing, no fix. Separate socket-only diagnostic failed because build has PSX_DEBUG_TOOLS=OFF, restored protected files/21cards; no registers captured. Time/manual rework/savings unknown. Next: guarded read-only observation of SystemError arguments and caller, not suppressing it.

## 2026-11-06 — ghidra-030 — loader boundary after P2 setup

- Actual MCP: `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/gaso/probe_motion_binding.py 0x80033c10`, get_program_info first; existing GUI12.1.4 JP SLPM_862.19 main SHA ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe. No writes/overlay/restart. Evidence binding-query-0x80033c10.json and binding-0x80033c10.c under `_work/gaso/`.
- Finding: following setup assumes both actor pointers exist and sets control flags, then advances resource allocation. Useful boundary context, not proof of which instruction stalls the live loader. Independent earlier dump has P2 pointer zero; causal PC still unknown. Query succeeded; timing/manual rework/savings unknown. Next: read-only live CPU/stack capture via existing runtime socket, preserving isolated session cleanup.

## 2026-11-06 — ghidra-029 — double Gas-O pre-actor boundary

- Purpose: narrow the double-Gas VS loading failure without speculative patches. Actual MCP commands: installed `D:/Dev/Tools/ghidra-mcp-python/python.exe` running `_work/gaso/probe_pair_loading.py` (xrefs800342DC/80033F14/80089215), then `probe_motion_binding.py` separately for8001E0F4,8002E08C,8002DE5C. Each connection calls get_program_info first. Existing GUI12.1.4 JP SLPM_862.19 main SHA256 ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe; no overlay, writes, restart or configuration changes.
- Evidence: pair-loading-references-ghidra.json and binding-query-<address>.json / binding-<address>.c under `_work/gaso/`. All queries succeeded. P2 setup registers its SEDT before actor initialization. Registration includes VAB operations, capacity checks and SystemError paths; no live PC proof of the path taken.
- Independent validation: preserved8MiB dump SHA25663136ec917643e882a22acfbc457c57b376b91b3824f7ed8ad0d9371064fc21c and adjacent loader-dump-audit.json/p2-model-comparison.json in the215858020561Z run. P2 DFS byte-exact, actor not initialized, six patched callbacks intact. Raw reads show global60voices/5banks and P2 SEDT13voices; visible count/byte-capacity predicates are not exceeded by those values. Not proof of VAB validity or a sound-caused stall.
- Outcome: partial/useful boundary narrowing, no fix or stability acceptance. No failed MCP call in this trial; no additional game run. Total elapsed, manual rework and savings unknown. Next: source-bank comparison and validated live CPU/stack context, not blind repetition.

## 2026-11-06 — ghidra-028 — double Gas-O loading boundaries

- Purpose: narrow the VS loading failure without changing the passing scale candidate.
- Command: `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/gaso/probe_motion_binding.py 0x800337b8 0x80033f14`; actual MCP `get_program_info` first, then both decompiles. Existing GUI12.1.4 JP main SLPM_862.19, SHA256 `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`; no overlay/writes/restart.
- Evidence: `_work/gaso/binding-query-0x800337b8-0x80033f14.json` and corresponding `binding-0x*.c`. P2 pack routine loads DBI at PTR80010CE8 and prepares resource pointers; P2 model setup calls80031D3C with side1 and actor destination8005F810. Historical loader800342DC explicitly reads each model in states6/8. This does not prove which step failed live.
- Independent check pending: one controlled doubleGas run with explicit frame9000 RAM capture; compare actual loader state, destinations and callback words. Outcome parcial: useful boundaries, no root cause or fix. No failed MCP query. Elapsed/manual rework/savings unknown. Next: preserve dump and inspect bounded state before editing.

## 2026-11-06 — ghidra-027 — scale build identity/table confirmation

- Purpose: confirm the intended main before deploying the scale-only candidate.
- Command: `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/gaso/probe_scale_build.py`;
  `get_program_info` first, then `read_memory 0x80051904 length19`. Both succeeded
  on existing Ghidra12.1.4 GUI JP SLPM_862.19 main; no overlay, writes or restart.
  Identity/hash and bytes retained in `_work/gaso/scale-build-mcp.json`.
- Independent validation: existing consumer decompile and scale host red/green
  evidence from ghidra-026 remain unchanged. This trial confirms access/context,
  not a new scale fidelity or game result. Outcome: parcial; time/manual rework
  and savings unknown. Next: experimental scale build and visual test.

## 2026-11-06 — 20261106-ghidra-026 — scale consumer and entrance particles

- MCP commands: installed `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/gaso/probe_motion_binding.py 0x8002d85c`, then `probe_scale_references.py` (get_xrefs_to80051904/8002D85C), then `probe_motion_binding.py 0x8002b5bc`. Every connection called get_program_info first: existing GUI12.1.4 JP SLPM_862.19 main, SHAea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe; no overlay/write/restart. Queries successful, per-address C/JSON plus scale-references-ghidra.json. Consumer confirms table indexing and scale storage, not a visual proportion measurement or BAG1 scale-consumer analysis.
- Complementary isolated headless, not original GUI: JAVA_HOME=D:/Dev/Tools/jdk-21.0.12.1+1; `D:/Dev/Tools/ghidra_12.1.4_PUBLIC/support/analyzeHeadless.bat D:/Dev/Recomp/BAG2JP/_work/gaso gaso-runtime-hooks -process native-gas-jp-relocated.dbi -noanalysis -scriptPath D:/Dev/Recomp/BAG2JP/_work/gaso -postScript AnalyzeGasHooks.java <output> <addresses>`. Two bounded trials: output native-smoke-decompile, addresses801D59A8/801D7C04; output native-smoke-lifecycle, addresses801D5BB0/801D5DE0/801D60C4/801D7E6C. Both save succeeded, no ERROR/WARN in logs native-smoke-headless.log/native-smoke-lifecycle.log. Input is JP Gas DBI imported earlier at file-byte base801D587C; source/provenance native-callback-layout.json. Hashes retained in scale-smoke-progress.json. Initial read of an assumed801d59a8.c path failed (not generated previously); used the known project and generated bounded outputs instead.
- Independent check `py -3.13 _work/gaso/audit_entrance_events.py`: original native62 and converted72/73 retain type1 event1902 at47; emitter handles76E and starts four groups; lifecycle consumes them and renders animated sprites. Native visual identity/texture mapping/BAG2 adaptation NOT verified. No reactivation of Bi-O handler or smoke deployment.
- Outcome: **útil**, identifies the preserved trigger and missing native effect lifecycle, plus BAG2 scale seam. Six host tests (real scale C and visual routing) pass after one new test went RED on98≠75; not live scale acceptance. Time/manual rework/savings unknown. Next: controlled scale build/game comparison; native particle adaptation and renderer/texture equivalence still pending.

## 2026-11-06 — event-patch validation: event dispatcher MCP

- Command: `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/gaso/probe_motion_binding.py 0x8003190c`; get_program_info first, existing Ghidra12.1.4 GUI JP SLPM_862.19 main SHAea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe, no overlay/writes/restart.
- Bounded event-dispatch decompile succeeded. Evidence `binding-query-0x8003190c.json`, `binding-0x8003190c.c` under `_work/gaso/`. Confirms dispatcher context only, not actual execution of the prior null-PC path. Earlier callback analysis reused; no fresh runtime instruction trace.
- Outcome: **parcial**, identity/dispatcher read confirmed; does not prove the event stub fixes the failure or preserves native Gas-O events. Time/manual rework/savings unknown. Next: complete the already running `gaso-event-full-review` and review motion plus song return; no duplicate run.

## 2026-11-06 — 20261106-ghidra-025 — native Gas-O callback variants

- MCP: `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/gaso/probe_motion_binding.py 0x8001f004`, get_program_info FIRST, existing12.1.4 GUI JP main SHAea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe. One decompile: rotation builder uses three12bit angles/trig/GTE; decompiler has register artifacts, not an exact numerical oracle. No GUI writes.
- Evidence correction: that scratch probe reused its fixed `binding-consumer-ghidra.json` filename, replacing the prior consumer wrapper with this new query. Moved the new wrapper to `binding-query-0x8001f004.json`; original consumer C/text remain intact as `binding-0x80012b9c.c/.txt` (use those for ghidra-024). Probe now names explicit-query reports by addresses to avoid this collision. No query rerun merely to reconstruct evidence.
- Native comparison: `compare_native_binding_variants.py` checks8source packs (USA/JP × A/Bcostume × A/Bside), hashes in `native-binding-variants.json`: init bytes equal within each region, differ across regions; both Ghidra init decompiles have identical35byte-store assignments. `compare_binding_initializers.py` now accounts for the JR delay slot (JP final store at36F3);21/30primary-map differences unchanged. Does not prove native preinitialization.
- Complementary headless in existing isolated task project only (original GUI preserved): `analyzeHeadless.bat <_work/gaso> gaso-runtime-hooks -import <native-gas-usa.dbi> -loader BinaryLoader -loader-baseAddr 0 -processor PSX:LE:32:default -noanalysis -scriptPath <_work/gaso> -postScript AnalyzeGasHooks.java <native-usa-hook-decompile> 0x50`; log `native-usa-hook-headless.log`. Then `-process native-gas-jp.dbi -noanalysis ...` over17stack-prologue candidates; `native-posthook-headless.log`. Several base0 outputs have bad-control-flow warnings due to absolute jumps; neither complete function discovery nor native runtime verification is claimed.
- Corrected-base trial: cross-call/prologue offset histogram suggested file-byte base801D587C; two native main table rows independently contain P1 init801D58CC (+50)/candidate postprocess801D6204 (+988), P2both displaced3AB8. `record_native_callback_layout.py` checks exact words, hashes main/DBI, saves `native-callback-layout.json`. Imported task-owned `native-gas-jp-relocated.dbi` at801D587C, same loader/options, postScript addresses801D58CC/801D6204; log `native-relocated-hook-headless.log`, outputs `native-relocated-hook-decompile/`. No bad-instruction warning in candidate postprocess; seven transform-copy blocks versus five in Bi-O. Caller role/order and node-layout translation still need verification before patching.
- Outcome: **útil** two specific compatibility differences, native regional/lateral initialization checked; no fixed gameplay. Time/manual rework/savings unknown. No build/deploy or game run in this trial. Next: native caller/preinit validation and guarded shared binding/postprocess adaptation, followed by live motion verification.

## 2026-11-06 — 20261106-ghidra-024 — binding consumer

- Purpose/command: `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/gaso/probe_motion_binding.py 0x80012b9c`. Ghidra12.1.4 GUI; get_program_info FIRST confirmed unchanged JP main SLPM_862.19 SHAea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe; then one bounded decompile. No overlay or writes. Evidence `_work/gaso/binding-consumer-ghidra.json`, `binding-0x80012b9c.c`.
- Observed: consumer iterates30bone positions, reads each mapping byte, skips FF/missing decoded channels, otherwise builds that bone's pose using the selected channel via8001F004. Confirms the map selects per-bone channels rather than being unused metadata.
- Independent live-map check `_work/gaso/audit_live_binding.py` failed safely: P1 actor+7CC=8025720C lies beyond the saved2MiB dump. No bytes guessed, no RAM read outside bounds, no report generated. This capture contains hook code but cannot establish the actor's actual map. Native omitted-store initialization and posthook remain unresolved.
- Outcome: **útil** consumer semantics, not a corrected skeleton. Query succeeded; bounded dump check failed as described. Time/manual rework/savings unknown. Next: inspect native bindings/posthook and obtain extended-RAM evidence if needed before guarded adaptation.

## 2026-11-06 — 20261106-ghidra-023 — Bi-O/Gas-O binding mismatch

- Purpose: investigate the rejected Gas-O skeleton using actual runtime hooks. MCP command `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/gaso/probe_motion_binding.py`, get_program_info FIRST each run, SLPM_862.19 JP main SHAea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe. Two grouped trials decompiled800126F8/80031D3C then added8002BD70/8002BF04 (both within8002BC38); first two unchanged queries repeated in the second script invocation, no new evidence from those repeats. Evidence `motion-binding-ghidra.json`, `binding-*.c/.txt`; no writes.
- Complement, not substitute for MCP: installed Ghidra12.1.4 headless/JDK21.0.12.1+1, NEW isolated project `_work/gaso/gaso-runtime-hooks`. Commands used `support/analyzeHeadless.bat <_work/gaso> gaso-runtime-hooks -import <input> -loader BinaryLoader -loader-baseAddr <base> -processor PSX:LE:32:default -noanalysis -scriptPath <_work/gaso> -postScript AnalyzeGasHooks.java <output> [0x50]`. Inputs: saved runtime2MiB SHA1c3e1a97867d57678088a533111e37e690c96d04f14c842e5ba64499bab092e7 at base80000000, decompile801CEDBC/801CF1B0; JP PLAYER1/P_GAS_A1.DFS member3 extracted as native-gas-jp.dbi at base0, decompile file+50. Native DBI hash in `binding-initializer-comparison.json`; base0 is NOT a claimed native runtime address. Both import/save logs succeeded (`runtime-hook-headless.log`, `native-hook-headless.log`); original GUI session/analysis preserved.
- Observed: Bi-O init writes actor+7CC map incompatible with Gas native map at21/30positions. Main loader preinitializes30slotsFF then calls character initializer; pose update feeds map to80012B9C. Bi-O post-model hook copies node19/22 transforms to23..27; full compatibility unresolved. Dump trace7500: WAIT71/native60, phase1/2/3, fever0. No gameplay correction or acceptance.
- Independent checks: bounded constant propagation in `compare_binding_initializers.py` agrees with decompiles; checks return and rejects unknown opcodes. Native omitted slots representedFF; native preinitialization/consumer still pending. A one-line PowerShell/Python word-print attempt failed parsing escaped quotes; no files changed, replaced by dedicated-script/simple hex extraction. Headless has no MCP-loaded overlay: only GUI main queries are MCP evidence.
- Outcome: **útil** concrete binding incompatibility, not proof of entire inversion cause or fixed movement. Elapsed headless total/manual rework/savings unknown; startup7847ms only is not total time. Next: native/consumer verification, guarded shared adaptation and live pose/animation regression.

Aplicar [criterios y plantilla](../assets.md#clasificación-y-medición-obligatorias).
El loader y los datos PsyQ se anotan por separado en cada ensayo cuando se utilicen;
su presencia no demuestra que una firma se haya aplicado correctamente.

## 20261106-ghidra-001 — antecedente de conexión y lectura
- Tipo: uso MCP histórico; transcrito el 2026-11-06, no reejecutado.
- Versión: Ghidra 12.1.4, loader PSX y datos PsyQ existentes.
- Entradas: ejecutable principal BAG2 JP `SLPM_862.19`, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
- Observado: backend inicialmente cerrado; el agente abrió la instalación y
  proyecto existentes, luego `get_program_info` y decompilación de `0x80035d98`
  respondieron. Advertencia de instrucción inválida al final, no ocultada.
- Evidencia: `_work/process-audit/ghidra-status.json` conserva fallo y recuperación.
- Contraste: identificación/hash y lectura MCP; no prueba semántica de overlays.
- Dictamen: **útil / buenos resultados** para verificar conexión/leer el programa;
  fidelidad de decompilación y eficacia de firmas PsyQ no evaluadas aquí.
- Medición: tiempos/ahorro no medidos. Siguiente: reutilizar sesión, validar cada rango.

## 20261106-ghidra-002 — comprobación para este registro
- Tipo: uso MCP real, 2026-11-06 UTC; tarea: crear historiales de herramientas.
- Versión/entrada: misma instalación y SHA-256 anteriores; ejecutable principal
  BAG2 JP, no overlay. No se aplicaron firmas ni se modificó análisis.
- Consultas: `get_program_info()` seguido de
  `list_functions({filter: "InitHeap", offset: 0, limit: 5})`.
- Observado: formato PSX, lenguaje PSX little-endian 32 bits, 1324 funciones;
  un resultado `InitHeap` en `0x80049f44`, `has_more: false`.
- Evidencia: `_work/tool-evidence/ghidra-mcp.json`, SHA-256
  `67eb2333eb700a07ce090d6f87ed2f6647f166245931af9cc417a0ee9f5107ba`;
  hash del programa igual al
  antecedente. Contraste limitado al dato previo y respuesta actual de MCP.
- Dictamen: **útil / buenos resultados** para disponibilidad y consulta del símbolo,
  no validación independiente de la función ni benchmark de decompilación.
- Medición: ejecución/preparación/revisión/ahorro no medidos.
- Siguiente: mantener sesión; evaluar semántica y firmas solo en una tarea pertinente.

## 20261106-ghidra-003 — consulta de estado Heat/Strike
- Tipo: comprobación MCP obligatoria al informar del estado, sin nueva prueba de juego.
- Entrada: instalación anterior; principal BAG2 JP `SLPM_862.19`, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
- Consultas: `get_program_info()` y `get_current_function()`; principal PSX LE32,
  1324 funciones; función seleccionada `main`, `0x8001e938`, cuerpo 952 bytes.
- Evidencia: respuestas MCP de esta consulta; sin archivo adicional ni cambios
  de análisis. Contraste: misma identidad que el registro 002.
- Dictamen: **inconcluso** para aceptación de las importaciones; confirma conexión
  y selección del principal, no módulos overlay ni comportamiento instalado.
  El estado comunicado procede de notas canónicas y evidencia histórica de juego.
- Medición: ejecución/preparación/revisión/ahorro no medidos.
- Siguiente: conservar sesión; no repetir partidas para contestar una consulta de estado.

## 20261106-ghidra-004 — preparación de revisión de llamas
- Tipo: uso MCP obligatorio; misma instalación y principal JP/hash del registro 003.
- Consultas: `get_program_info()` y `decompile_function_by_address({address: "0x8001e938"})`.
- Observado: principal correcto; `main` usa `DAT_8005d3d4` para despachar estados
  y reinicia `0x8005d3d8/dc/e0`. Decompilado completo, sin modificaciones.
- Evidencia: respuestas MCP de la sesión. Contraste limitado al contrato de estados
  que observa el harness; no certifica el callback del overlay `0x8009b084` ni efectos.
- Dictamen: **útil / buenos resultados** solo para revisar ese despacho del principal.
- Medición: tiempos y ahorro no medidos. Siguiente: aceptar llamas solo tras revisión humana.

## 20261106-ghidra-005 — eventos por puntaje del escenario Strike BAG1
- Tipo: uso MCP obligatorio; misma instalación, principal `SLPM_862.19` sha `ea5a1668…1efe`.
- Consultas: `get_program_info()`; `read_memory` de las tablas de callbacks
  `0x80051B88/BBC/BF0` y `0x80054C10` (56 bytes c/u) y de `0x80010CEC`;
  `get_xrefs_to` de `0x80051B88`, `0x80051BBC`, `0x80089200`, `0x8006D980`, `0x8005E2E8`;
  `decompile_function_by_address` de `0x800330FC`, `0x8003398C`, `0x80032A40`,
  `0x800342DC`, `0x8001E0F4`, `0x80017FD8`; `disassemble_function(0x800330FC)`.
  Fallos: `get_memory`, `get_references_to_address`, `get_symbols_at_address` e
  `get_instruction_at` no existen (sin efecto; se usaron `read_memory`/`get_xrefs_to`).
- Observado: id1 → callbacks `0x801E33D0/D8`, `0x801E3400`, `0x801E3420`, iguales al
  perfil `stages/strike.json`; todas las DBI de escenario cargan en `0x801DAF10`
  (`PTR_DAT_80010cec`); `*(*0x80089200)` es el id de escenario usado por
  `FUN_800330fc` (setup). `0x8006D980` tiene escrituras/lecturas en el principal
  (contador global). `0x8005E2E8` (beats de juego) no tiene xrefs en el principal:
  probablemente lo escribe un overlay; sin verificar.
- Contraste: perfil Strike y disasm JP `_work/stage_import/strike/bag1jp_strike_disasm.txt`.
- Dictamen: **útil** para descartar errores de base/callbacks; no prueba los eventos.
- Medición: no medida. Siguiente: partida 2P autoplay con volcado RAM tardío.

## 20261106-ghidra-006 — análisis de soporte de nodos tipo 2 en escenario
- Tipo: uso MCP obligatorio; misma instalación, principal `SLPM_862.19` sha `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
- Consultas: `get_program_info()`, `decompile_function_by_address` de `0x80032a40` (stage model init),
  `0x800227d4` (bone tree setup/allocation), `0x80022660` (bone node builder / type dispatcher),
  y `0x8003398c` (stage drawing setup).
- Observado: `0x80022660` maneja los tipos de hueso con switch: tipo 1 procesa malla directamente;
  tipo 2 hace `param_1[0x23] = param_1 + *piVar1 * 0x2c` (offset relativo en nodos de 0xb0 bytes).
  Sin embargo, en el pipeline de renderizado de escenario (`0x8003398c`), BAG2 asume que cada nodo
  visible tiene su propia estructura de malla independiente (como hacen todos los modelos nativos
  de BAG2). En BAG1 el modelo de Strike usaba nodos tipo 2 para instanciar las celdas y pasillos en
  4 tramos a lo largo de Z (Z = -29589, -9857, +9875, +29607), pero en BAG2 solo los nodos tipo 1
  maestros (con Z = +29607) estaban siendo dibujados, omitiendo los otros 30 nodos tipo 2.
- Contraste: auditoría de todos los modelos de escenario nativos de BAG2 en `assets/archive` (ninguno
  emplea tipo 2).
- Dictamen: **útil / solución identificada** para determinar que el conversor del modelo debe aplanar
  los nodos tipo 2 a tipo 1 independientes (`flatten_type2`).
- Medición: tiempo de sesión de análisis ~15 min. Siguiente: probar escenario con nodos aplanados.

## 20261106-ghidra-007 — prueba de visibilidad durante solos bloqueada
- Propósito: localizar la condición de descarte de estructuras laterales de Strike
  para una prueba A/B reversible autorizada por el propietario. Culling, clipping,
  orden de polígonos y reemplazo de VRAM siguen siendo hipótesis, no causas confirmadas.
- Consulta: descubrimiento de herramientas `search({namespace:"ghidra",limit:1})`
  devolvió `items=[]`, `remaining=0`. No es posible invocar `get_program_info`
  desde el catálogo actual; no se hizo ninguna lectura ni modificación del binario.
- Entorno: `Get-CimInstance Win32_Process` confirmó Ghidra existente, PID18524,
  Java de JDK21 y proyecto `D:/Dev/Recomp/BAG2JP/ghidra/BAG2JP.gpr`.
  No se abrió una segunda instancia. Programa seleccionado, módulo y hash:
  no verificados por MCP en este ensayo; no se reutiliza una identidad histórica
  como si fuera una comprobación actual.
- Contraste: proceso activo no acredita conexión MCP. Juego experimental PID1872
  preservado. Preflight pasó; conserva drift previo de netsync, sin cambio de recursos.
  Evidencia: `_work/workflow/20261106T082558662025Z-strike-solo-visibility/preflight.log`.
- Dictamen: **bloqueado**, falta la herramienta MCP en la sesión; no se demuestra
  fallo del backend de Ghidra ni se evalúa la utilidad de su análisis.
- Medición: tiempo y ahorro no medidos; sin parche, compilación ni nueva prueba A/B.
  Siguiente: recuperar exposición MCP, llamar `get_program_info` y leer el camino
  de dibujado relevante antes de decidir qué condición se puede desactivar con seguridad.

## 20261106-ghidra-008 — recuperación MCP sin reiniciar Ghidra
- Corrige el bloqueo de `20261106-ghidra-007`: falta exposición en el catálogo de
  la sesión, pero el puente local instalado sí funciona mediante cliente MCP stdio.
- Comando: `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/strike_ghidra_mcp_probe.py`.
  Usa `-m ghidra_mcp --ghidra-server http://127.0.0.1:8080/`, configuración existente
  documentada en `D:/Dev/Tools/claude_desktop_config.ghidra.json`; sin reinstalación.
- MCP: `get_program_info` confirmó Ghidra12.1.4, `SLPM_862.19`, ejecutable JP,
  SHA256 `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  Lecturas: `decompile_function_by_address` en `0x8003398c` y `0x80022660`.
  Alcance: ejecutable principal, no identidad de overlay Strike acreditada.
- Evidencia: `_work/strike-ghidra-mcp-probe.json` y
  `_work/strike-{0x8003398c,0x80022660}-decompile.txt`.
- Resultado: `0x8003398c` prepara recursos/modelo; `0x80022660` recorre nodos
  e incluye explícitamente `case 2`, llamando a `0x800201b0` vía malla referenciada.
  Esto obliga a limitar la anterior conclusión general de que BAG2 no soporta
  tipo2: el flattening tuvo evidencia visual favorable, pero no demuestra esa
  incompatibilidad global ni explica el pop-in durante solos.
- Contraste: consultas reales y hash confirmado; decompilación contiene `in_v0`
  no resuelto, requiere contraste de instrucciones antes de interpretar sus accesos.
- Dictamen: **útil** para recuperar acceso y acotar hipótesis; causa de pop-in
  todavía no identificada. Sin parche ni nueva prueba A/B, sesión del juego intacta.
- Tiempo/ahorro no medidos. Siguiente: trazar dibujado por fotograma y reproducir
  desaparición antes de elegir un guard de visibilidad reversible.
- Continuación del mismo ensayo: `get_xrefs_to(0x80089200,offset=0,limit=100)`
  entregó63 referencias, `has_more=false`. Lecturas acotadas adicionales de
  `0x80032f3c`, `0x800330fc`, `0x80030358`, `0x8003026c`, `0x800307a8`, guardadas
  en `_work/strike-<address>-decompile.txt`. Localizan inicialización de nodos,
  matrices y estado, no todavía la decisión de descarte durante el solo.
  La consulta fue demasiado amplia para aislar el render; no atribuir utilidad
   causal a esas referencias ni aplicar un parche sobre funciones de inicialización.

## 20261106-ghidra-009 — acotar render y presentación inicial de Strike
- Propósito: localizar el descarte de estructuras durante solos, sin desactivar
  clipping seguro ni confundir el render de personajes con el del escenario.
- Entorno: puente MCP stdio instalado, Ghidra12.1.4, `SLPM_862.19` JP;
  `get_program_info` primero en cada conexión. SHA256 del ejecutable:
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  Overlay005 no identificado como programa cargado: no se autoriza inferir sus
  direcciones como verificadas en Ghidra.
- Comando: `D:/Dev/Tools/ghidra-mcp-python/python.exe
  _work/strike_ghidra_mcp_probe.py <addresses>`; modo `--query` conserva catálogo
  y respuesta en `_work/strike-ghidra-query.json`. Decompilaciones individuales
  en `_work/strike-<address>-decompile.txt`; los JSON de consulta se sobrescriben.
- Consultas agrupadas: decompilación de `0x8002d85c`, `0x8002b5bc`,
  `0x8002c404`, `0x80014c3c`, `0x80016568`, `0x80016d4c`, `0x8001b5ec`,
  `0x8001e0f4`, `0x80017fd8`, `0x80018038`, `0x80012a94`, `0x80022800`,
  `0x80022410`, `0x80022888`, `0x80022908`, `0x800229f0`, `0x80022a84`,
  `0x80022bec`, `0x80022d64`, `0x80022e94`, `0x800201b0`, `0x800220b8`,
  `0x800133cc`, `0x80013144`, `0x80013544`, `0x80013780`, `0x8003353c`,
  `0x80033618`, `0x800337b8`, `0x80037af4`, `0x8001fbfc`, `0x8001ffbc`,
  `0x800326d4`, `0x80014044`, `0x80014520`, `0x80016268`.
  `list_functions` filtros80022/80020/80013/80011/80010/80033, limit100,
  sin páginas restantes; `get_function_calls` callers133cc/13144, limit50,
  sin páginas restantes. `read_memory`:3318c/944bytes,18280/768bytes,
  118fc/2600bytes; estas dos últimas respuestas en logs `_work/strike-ghidra-*-read.log`.
- Fallos: FUNCTION_NOT_FOUND para3318c/1835c/1fec4/11e38/120f8/118fc/12290.
  Una respuesta textual provocó JSONDecodeError; el cliente scratch ahora la
  conserva sin interpretarla como JSON. No se crearon funciones ni se cambió el programa.
- Contraste: `0x8002c404` aplica descarte a **personajes**, no acredita un guard
  del escenario.3318c reinicia dos personajes y llama inicialización de escenario;
  18280 y14044/16268 son cámara;37af4 es crescendo de audio;1fbfc/1ffbc son
  texto;118fc es estado de entradas. No parchear esas rutinas como culling.
  Las lecturas amplias resultaron mayormente irrelevantes para el descarte buscado.
- Dictamen: **irrelevante** para localizar el descarte del escenario; **útil**
  únicamente para excluir candidatos concretos. Causa pendiente; ningún A/B,
  cambio de runtime, compilación ni aceptación nueva. Tiempo/ahorro y retrabajo
  manual no medidos. Siguiente: trazar desde el llamador de dibujo por fotograma
  con identidad del módulo confirmada, en vez de ampliar búsquedas por global.

## 20261106-ghidra-010 — guard concreto del dibujo de escenario JP
- Comando/puente: mismo cliente MCP stdio de009, Ghidra12.1.4;
  `get_program_info` primero, `SLPM_862.19`, SHA256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
- Decompile2a000/2a090/30458: FUNCTION_NOT_FOUND;3190c devuelve dispatch de
  personaje, no el guard buscado. No se crearon funciones ni se cambió análisis.
  `read_memory(0x80030458,length=2048)` y
  `read_memory(0x80051a94,length=56)` sí entregan bytes sin gaps.
- Evidencia: `_work/strike-ghidra-30458-read.log`,
  `_work/strike-ghidra-stage-bounds-read.log`, `_work/strike-30458-asm.txt`.
  Validación independiente: los2048bytes MCP coinciden exactamente con el
  ejecutable JP local (cabecera2048, base80010000). Capstone5.0.7 decodifica
  esos bytes, no sustituye la lectura MCP. Solo ejecutable principal confirmado.
- Hallazgo:30458 carga stage global89200, llama30f4c, luz/callback de escenario;
  por grupo proyecta origen con44a04, rechaza profundidad fuera de[96,4191]
  en30578 y flag GTE negativo en30588. Después compara X/Y usando margen
  tabla51a94[stageID]/profundidad, pantalla512x240; byte de visibilidad alimenta
  dibujo mediante135f8 y8f0f4. Tabla stock stage1=0xc0000.
- Candidato A/B: sustituir SOLO30590 `0x0243001b` (divu s2,v1) por
  `0x0800c175` (j305d4), delay30594 `mflo a0` conservado (a0 muerto antes
  del siguiente uso). Mantiene guards previos de profundidad/GTE; no cambia
  mallas ni memoria. Esto prueba el descarte de pantalla, no otros descartes.
- Dictamen: **útil**, localizado guard contrastable. No demuestra aún que sea
  la causa observada ni fidelidad del renderer. Fixture opt-in en preparación,
  tests host rojo por writes==1, después verde; prueba visual A/B pendiente.
  Tiempo/ahorro y retrabajo no medidos.

### 2026-11-06 — seguimiento runtime de 20261106-ghidra-010

- Sin nuevas consultas MCP: prueba del candidato derivado de010; no repetir lectura sin cambios.
- Comando: `py -3.13 _work/strike_visibility_ab.py`; evidencia
  `_work/versus-runs/20261106T091810099713Z-strike-visibility-ab`. Total257,51s.
- Aplicacion/restauracion registradas(result1/2). Revision independiente de tres
  imagenes/checkpoints: Start no congela Fever; fases1/5/6 a1/7/0 a1/7/3,
  camaras distintas. Resultado visual inconcluso: no prueba de correccion ni ahorro.
- Ajustes y21 saves restaurados con hashes verificados. Siguiente: control
  comparable de camara/fotograma antes de repetir A/B; conservar clipping seguro.
- Intento de registro inline rechazado por shell scanner invalid-structure antes
  de ejecucion; sustituido por script acotado, sin cambiar permisos.

### 2026-11-06 — validacion humana del candidato de 20261106-ghidra-010

- Sin nuevas consultas MCP: seguimiento runtime del candidato derivado de010.
- Comando `py -3.13 _work/strike_live_visibility_bypass.py`; evidencia
  `_work/versus-runs/20261106T094126581420Z-strike-live-autoplay`.
  Activacion confirmada en visibility-activation.log; profundidad/GTE retenidos.
- Propietario: huecos persisten durante solos. Resultado negativo para suficiencia
  del bypass lateral, no diagnostico definitivo de clipping/orden/texturas.
  Pose inicial tambien persiste; informa proteccion del pecho ausente (causa no probada).
- Total323,359s; ajustes y21 saves restaurados, control temporal eliminado.
  Sin ahorro demostrado. No promover candidato; contrastar paquete/modelo e investigar
  evidencia de los demas descartes sin desactivar las protecciones seguras.

### 2026-11-06 — 20261106-ghidra-011: comprobacion de contexto, no diagnostico del pecho

- Comando: `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/strike_ghidra_mcp_probe.py 0x80022660`.
  MCP get_program_info primero: Ghidra12.1.4 GUI SLPM_862.19 JP, SHA256
  ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe.
  Consulta decompilado80022660 y xrefs80089200; resultado en
  `_work/strike-ghidra-mcp-probe.json` y txt individual. Sin cambios en Ghidra.
- Resultado redundante: esa funcion de inicializacion ya estaba leida, no contrasta
  la discrepancia visual del pecho ni identifica causa nueva. Repeticion innecesaria;
  no atribuir utilidad diagnostica ni ahorro. Tiempo/retrabajo no medidos.
- Validacion independiente pertinente: script determinista de bytes del payload,
  `_work/stage_import/strike/current-chest-audit.json`: parche de copia sigue presente,
  modelos/TIM iguales al baseline historico. No se restauran assets a ciegas.
- Siguiente: contraste VRAM en ejecucion con el atlas fuente; no repetir esta lectura.
# 20261106-ghidra-012 — Dance View music, non-causal table query

- Purpose: investigate the owner's report that imported Strike in Dance View keeps
  BAG2 music. Existing MCP bridge, Ghidra12.1.4 GUI `SLPM_862.19` JP; program info
  queried first on both calls. Main executable SHA256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
- Commands: installed Ghidra Python `_work/strike_ghidra_mcp_probe.py --query`
  with `get_xrefs_to(address=0x800553f4,limit=40)` (one reference, no more pages),
  then the same probe `0x800342dc` (decompile, incidental unchanged stage xrefs).
  Outputs: `_work/strike-ghidra-query.json`,
  `_work/strike-0x800342dc-decompile.txt`, `_work/strike-ghidra-mcp-probe.json`.
- Evidence: the reference resolves to UI primitive/text construction, not a
  demonstrated song-selection path. Do not treat the earlier table label as
  verification of audio semantics. No overlay identity or runtime music inputs
  verified. No writes or patches. Outcome: irrelevant for the causal question;
  elapsed time/manual rework/savings unknown. Next: observe XA extent/channel and
  imported-stage guards in Dance View, with coordinated session restart if needed.
# 20261106-ghidra-013 — Native XA song control, viewer diagnosis

- Actual MCP bridge, Ghidra12.1.4 GUI `SLPM_862.19` JP, program info first on
  every invocation; main SHA256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
- Queries: `get_xrefs_to(0x800555a8,limit=40)` returned one reference/no more;
  `decompile_function_by_address(0x80035bf8)` and `(0x800358bc)` through
  `_work/strike_ghidra_mcp_probe.py`. Per-address decompiles retained in `_work/`;
  generic probe/query JSON are overwritten by subsequent bounded trials.
- 35bf8 compares song-duration table entries to clock892ec/60; 358bc derives
  XA channel from song index&7, issues CdControlB filter and read commands, and
  writes selected song892e8, channel892f5 and clock. This supports new live
  watches, but main analysis alone does not identify Dance View overlay caller.
- Independent live diagnostic run `viewer-run/20261106T051213` confirms XA LBA37083
  channel1 lies inside37082..64242, shim54533142/root19/model800a5030, yet profile
  detection returns null. Source currently requires model ID0/1; actual raw ID
  still to observe. Log retained in that run. No audio-routing fix proven yet.
- Outcome: useful bounded native control evidence, no patches in Ghidra;
  elapsed/manual rework/savings unknown. Negative lookup of a historical
  `_work/strike-0x80032a40-decompile.txt` file did not yield source evidence.
## 2026-11-06 — 20261106-ghidra-014 — unselected Dance View transform investigation

- Purpose: distinguish model initialization from animated transforms for Strike's missing chest emblem with viewer `FFFF`.
- Actual MCP: installed Python bridge, `_work/strike_ghidra_mcp_probe.py 0x80012a94 0x80013144`, then `0x80022518`; each calls `get_program_info` first. Ghidra 12.1.4 GUI, JP `SLPM_862.19`, executable SHA256 `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`. Main executable only; no overlay identity established or modified.
- Evidence: `_work/strike-0x80012a94-decompile.txt`, `_work/strike-0x80013144-decompile.txt`, `_work/strike-0x80022518-decompile.txt`. Loader copies ten transform words into each node; animated path composes node matrices. The first two queries repeat earlier reads and do not establish a new cause. Incidental stage-global xrefs are not additional evidence.
- Independent check: `_work/inspect_strike_viewer_ram.py` reads the existing 2 MB dump from viewer run `20261106T051542`: root `0x19`, mode 4, viewer `FFFFFFFF`, player pointer `0x8025C3F8`. That address is outside the dump, so transforms cannot be recovered from it. Do not wrap the pointer into 2 MB or claim zero/bad transforms.
- Outcome: partial diagnostic evidence, not a fix. No measured elapsed time, manual savings or causal validation. Next: native BAG1 reference with explicitly loaded save, then compare unselected/NEUTRAL states; extended-memory capture only if still necessary.
- Follow-up independent runtime evidence: after `LOAD OK!`, native BAG1 run `native-combat-runs/20261106T053152` also lacks the visible S in the unselected state and displays it in NEUTRAL. This rejects the premise that this particular difference alone proves a port regression; it does not establish the underlying matrix/material cause. Owner decision required before deviating from the native default. No further Ghidra query was needed for this observation.

## 2026-11-06 — 20261106-ghidra-015 — Strike chest/WAIT render path

- Purpose: locate why the chest S disappears in unselected Dance View (WAIT slot 71) after the owner authorized a deliberate BAG2 deviation.
- Actual MCP via `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/strike_ghidra_mcp_probe.py`; `get_program_info` first in each session (Ghidra 12.1.4, JP `SLPM_862.19`, SHA256 `ea5a1668…087851efe`). Queries: decompile `0x800220b8` (BAG2 mesh parser), `0x800133cc` (recursive node matrix compose), `0x8002c404` (per-player update/render), xrefs `133cc ← 13144 ← 2c404`. Main executable only.
- Evidence: `_work/strike-0x800220b8-decompile.txt`, `_work/strike-0x800133cc-decompile.txt`, `_work/strike-0x8002c404-decompile.txt`.
- Limit: render `0x8008ef3c`/`0x8008e780` and emitter `0x80027fc8` have no valid function/bytes in this Ghidra program (runtime-loaded or unanalysed); read from the 8 MB RAM dump with Capstone (capstone-003). Recorded as a gap, not a silent substitution.
- Independent validation: 8 MB WAIT/NEUTRAL dumps; S polygons generated in both states; emitters sort per polygon by two-vertex depth; 88-frame WAIT breathing cycle measured from the watch log.
- Outcome: useful diagnostic (format and sort mechanism); no fix. Elapsed time and savings unmeasured. Next: motion interpreter in Ghidra before editing WAIT.

## 2026-11-06 - 20261106-ghidra-016 - Gas-O/Bi-O archive-entry tables

- Purpose: find Bi-O's BAG2 character id and archive entries for the Gas-O import.
- Actual MCP via `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/strike_ghidra_mcp_probe.py`; `get_program_info` first (Ghidra 12.1.4 GUI, JP `SLPM_862.19`). Queries: `get_xrefs_to 0x80055180` -> only `FUN_800342dc`; decompile `0x800342dc` (`_work/strike-0x800342dc-decompile.txt`). Main executable only.
- Finding: loader selects pack `*(u16*)(0x80055180 + (sel&0x1f)*2 + (sel>>5)*0x48)` (P1; P2 0x800551a4), models 0x80055258/0x8005527c, stage 0x80055360 + DAT_80089240*2; `sel` = byte 0x80089250/51.
- Independent validation: byte scan of `_work/mainexe/slpm.bin` with `_work/gaso/inventory_bio_entries.py` reproduces every Heat/Strike entry of the existing alt index exactly. Bi-O = id 9: packs A 53/54, B 125/126; models A 89/90, B 161/162; fever 17/35; stage 197.
- Outcome: useful; avoided guessing the target slot. Elapsed time and savings unmeasured. Next: Gas-O inventory and documented plan.

## 2026-11-06 — 20261106-ghidra-022 — Gas-O inverted pose, Bi-O hook pointers

- Purpose: locate slot9 per-character tables after actual gameplay visually rejected. Command `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/gaso/probe_skeleton_hooks.py`; two bounded related runs, second adds pointee reads. get_program_info first each time; existing Ghidra12.1.4 GUI JP main SLPM_862.19, SHA256 ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe. No writes or module loading.
- Queries: read_memory80053600/4,80053568/4,80053698/4; second run also80052824/64,801CEDBC/32,801CF1B0/32. Table pointers801CEDBC/80052824/801CF1B0;801C destinations returned uninitialized gaps, NOT usable code. Evidence `_work/gaso/skeleton-hooks-ghidra.json` retains second run. No decompilation or proof that these hooks cause inversion.
- Independent validation: deployed entry89 model and motions match converter/remapper, hierarchy unchanged, nine selected clips preserve native assigned motion-channel bytes (`model-motion-diagnosis.json`). This narrows provenance only, not runtime correctness.
- Outcome: parcial; concrete missing-module evidence. Time, savings and manual rework unknown. Next: task-owned runtime RAM snapshot and clip/phase correlation, then relevant module analysis through MCP; do not substitute guessed hook patches.

## 2026-11-06 - 20261106-ghidra-017 - character DFS loader and accessory member

- Purpose: find out who consumes the third member (1460-byte single-node model) of Gas-O's model DFS, and whether Bi-O's slot loads it.
- Actual MCP: same probe; `get_program_info` first on every call (Ghidra 12.1.4 GUI, JP `SLPM_862.19`). Decompile `0x80033d1c` and `0x80031d3c` (`_work/strike-0x80033d1c-decompile.txt`, `_work/strike-0x80031d3c-decompile.txt`); `get_xrefs_to 0x8005f7f8`.
- Finding: `FUN_80031d3c` reads member 0 = model (node tree player+0x28), member 1 = motions (table player+0x824), and then the accessory member 2 when the per-character count is >0: chars 3,4,5,8,9,10,0xb,0xc,0xe,0x10 -> 1 instance; 7,0xf -> 2; mode 5 only char 0x12. The result is stored at `0x8005f7f8` (side 0) / `0x8005f800`; per-character hooks via `PTR_DAT_800535dc`, `PTR_PTR_80053544` and `PTR_DAT_80053674` indexed `side*0x13+char`. Bi-O (id 9) loads exactly one accessory, so Gas-O's member 2 fits structurally.
- Limits: xrefs to `0x8005f7f8` are only the two WRITES in `FUN_80031d3c` (0x80032608, 0x80032630); no reader in the main executable (likely overlay/runtime or computed addressing). How Bi-O's hook attaches/renders the accessory, and Gas-O's BAG1 use of it, are not established (the project holds only the BAG2 SLPM).
- Independent validation: DFS inventory (`_work/gaso/gaso-dfs-inventory.json`, `_work/gaso/bio-native-entries.json`): Bi-O model DFS also has 3 members (third = 3-node model), Gas-O A2/A4 third member identical single-node type-1 model.
- Outcome: partial; member layout is compatible, accessory behaviour is unresolved and must be checked in game. Time/savings unmeasured. Next: phase 1 profile, then in-game observation of the accessory.

## 2026-11-06 - 20261106-ghidra-018 - Motion request mapping and role analysis

- Purpose: verify BAG2 motion request handler tables (`0x8002a090`) against BAG1 counterpart (`0x80030090`) for Gas-O animation contract and policy.
- Actual MCP: same bridge (`_work/strike_ghidra_mcp_probe.py`); `get_program_info` first (Ghidra 12.1.4 GUI, JP `SLPM_862.19`, SHA256 `ea5a1668…087851efe`). Read memory at `0x8002a090`..`0x8002a774` and tables at `0x8005180c` (r < 0x2b), `0x80051838` (10 overrides), `0x800518e4` (requests 200..299), `0x80051860` (requests 50..99). Counterpart verified in BAG1 `_work/bag1/scus.bin` at `0x80030090` (`0x80055830`, `0x80055854`, `0x800558ec`).
- Finding: BAG1 and BAG2 share the request-to-slot mapping architecture encoded in `tools/bag1import/reqmap.py`. Gas-O's 84 animations map cleanly to 52 mapped roles and 58 duplicate requests across 70 slots; remaining 14 slots are exact alternate dance transitions `B1_ALT`.
- Independent validation: `tools/bag1import/generate_gaso_contract.py` outputs `tools/bag1import/contracts/gaso-animation-contract.json` (110 entries, 0 empty, 0 unresolved). `tools/bag1import/anim_remap_gaso.py` generates 289,548 bytes with 99 active slots, verified in `_work/gaso/test_001.bin`.
- Outcome: complete; animation contract verified and exception marked verified in `tools/bag1import/profiles/gaso.json`. Elapsed time and savings unmeasured. Next: Phase 3 asset conversion.

## 2026-11-06 — 20261106-ghidra-019 — Gas-O stage callbacks and chart

- Purpose: independently verify stage9 target entry/callbacks before using the existing experimental profile.
- Actual MCP: `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/gaso/stage_mcp_probe.py`, installed stdio bridge `-m ghidra_mcp --ghidra-server http://127.0.0.1:8080/`. Catalog searches exposed no Ghidra tools; reused existing GUI, no restart/configuration changes. An initial inline Python attempt failed with SyntaxError before connecting; saved-script retry succeeded. First trial read stage entries; second added callbacks/chart, each calling `get_program_info` first.
- Version/input: Ghidra12.1.4, PSX LE32, JP main SLPM_862.19,1324functions, SHA256 `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`. No loaded-overlay identity verified.
- Queries: `read_memory`52bytes each at80055360,80051B88,80051BBC,80051BF0,80054C10,8004DF08. Evidence `_work/gaso/stage-ghidra-resume.json`; deterministic comparison `py -3.13 _work/gaso/audit_stage_resume.py` → `stage-profile-audit.json` (all under `_work/gaso/`).
- Observed: id9→197; callbacks801E25C4/25CC/25F8/2618; chart801E266C. Independent target-file regression checks literal init instructions and stock tail, while builder now rejects in-bounds callback mismatches. USA/JP ST_GAS inputs and all member hashes in report; only member0 differs.
- Outcome: **útil** for target-table validation, not proof of relocated function/global semantics or runtime stage behaviour. No Ghidra writes. Time/manual rework/savings unknown; inline quoting required one correction. Next: semantic mapping and native song-routing verification before deployment.

## 2026-11-06 — 20261106-ghidra-021 — deployed game-test identity check

- Purpose: required MCP confirmation before the deployed regional candidate game test.
- Command: `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/gaso/visual_mcp_probe.py`; get_program_info first, read_memory8001F874/96 and80055360/52. Ghidra12.1.4 GUI, JP main SLPM_862.19, SHA256ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe; no overlay or writes. Both reads succeeded.
- Evidence: `_work/gaso/visual-ghidra-resume.json`; previous report preserved as `visual-ghidra-pre-game-test.json`. Independent validation is the deployed payload/build hashes in deployment-backup/report.json; not a fresh semantic validation of these addresses.
- Outcome: partial, identity/read access confirmed; unchanged bounded reads provided no new semantic finding. Time/manual rework/savings unknown. Next: observe actual game flow with isolated saves; do not infer gameplay acceptance from MCP.

## 2026-11-06 — 20261106-ghidra-020 — regional-entry routing scope

- Purpose: confirm the existing JP main and bounded loader/stage-table context before changing regional DF2 index routing.
- Actual command: `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/gaso/visual_mcp_probe.py`, existing stdio bridge/GUI, no restart or configuration changes. `get_program_info` first; then `read_memory`8001F874 length96 and80055360 length52. Both succeeded; evidence `_work/gaso/visual-ghidra-resume.json`.
- Input: Ghidra12.1.4 GUI, SLPM_862.19, PSX LE32 main, SHA256 `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`. No overlay selected/verified; no writes. Loader role is historical analysis, not a fresh semantic decompile in this trial.
- Independent validation: real-C DF2 host harness compiled with actual generated index type; five host tests in `_work/gaso/visual-region-tests.json` (mock runtime, not live game). Confirms exact routing/ownership properties, not character-hook coherence or stage semantics. Index has no JP resources yet; no deployment.
- Outcome: **parcial**, useful identity/read-access confirmation; not evidence of full regional import. No MCP failure in this trial. Time, manual rework and savings unknown. Next: real JP resources and final assembled/runtime validation.

## 20261110-ghidra-044 — 2026-11-10 UTC — espacio y altura del tanque GAS-O
- Tipo: arranque recuperado y uso real. Ghidra 12.1.4; MCP exacto:
  `get_program_info()`, `decompile_function_by_address(address="0x8002c404")`.
  Identidad fresca: `SLPM_862.19`, main BAG2 JP, PSX LE32, imagebase
  `0x80000000`, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  No se afirma overlay cargado ni se modificó el análisis.
- Arranque: una sola ejecución de
  `D:/Dev/Tools/ghidra_12.1.4_PUBLIC/ghidraRun.bat D:/Dev/Recomp/BAG2JP/ghidra/BAG2JP.gpr`.
  Inicialmente `BACKEND_UNAVAILABLE` en `127.0.0.1:8080`. Reutilizada Java
  PID 7728; el modal Tip of the Day impedía abrir el programa. Cerrado ese modal
  tras verificar PID/título. Intentos de foreground rechazados por Windows;
  `AppActivate=True`, mensajes de doble clic y Java vivo no probaron apertura.
  Hubo además un SyntaxError de quoting y una aserción de foreground fallida;
  un ENTER no protegido no tuvo efecto confirmado. No repetir ese envío.
  Finalmente, topmost temporal sin activar, hit-test contra HWND/PID exactos,
  doble clic en el programa y restauración de cursor/topmost/foreground abrieron
  CodeBrowser. MCP siguió fallando durante la carga y luego respondió con la
  identidad anterior. Sin duplicados, instalaciones ni cambios de configuración.
- Resultado: el decompilado nativo compone cámara `0x8005d0f0` con matriz del
  actor `+0x14c4` antes de proyectar la raíz `+0x810/+0x814/+0x818`.
  Contraste independiente: RAM histórica inicializada
  `_work/versus-runs/20261110T034745727209Z-gaso-sign-early/sign-intro-31-ram.bin`,
  SHA-256 `e272fae7241f8e9e5261ad9cbe335376dee959aef53d9616a775714d4f645a9f`;
  pelvis Y positivas y cámara con Y invertida, coherentes con sumar altura local.
  `_work/gaso/tank-resume-space-audit-initialized.json`, SHA-256
  `9347228ab172ef427732f3e16f60fb0923d426007762f65bdc31121e5e6dd5b9`.
  El primer audit con `sign-intro-07-ram.bin` tenía punteros nulos: evidencia
  inválida, conservada en `tank-resume-space-audit.json`, no usada para concluir.
  Decompilado contrastado con `_work/strike-0x8002c404-decompile.txt` histórico.
- Dictamen: **útil** para matriz/convención vertical; no prueba pose congelada,
  anclaje visual ni aceptación del tanque. Tests posteriores ejecutan el C real.
  Ejecución, preparación, revisión/retrabajo y ahorro: **no medidos**.
  Siguiente: verificar el candidato de coordenadas en el juego experimental;
  reutilizar esta instancia y lectura mientras no cambie el binario.

## 20261110-ghidra-045 — Dependency check for full-fidelity attack planning

- Purpose: verify the existing BAG2 sound consumer before planning original BAG1
  tank audio. Installed Ghidra 12.1.4 / existing MCP session, no startup or edits.
- Exact queries: `get_program_info()` followed by
  `decompile_function_by_address(address="0x8002e2d0")`.
- Identity: `SLPM_862.19`, Japanese main executable, PSX LE32, entry `0x80035d98`,
  SHA-256 `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  No BAG1 binary or DBI module was selected or identified by this trial.
- Evidence: six-u16 sound-record stride; cue match at word2, bank/program words0/1,
  default volume from word3, pitch/fine from word4 and `SsUtKeyOnV` call. Missing
  cue returns -1. Existing globals also scale output volumes; raw sample equality
  alone cannot prove identical in-game sound.
- Independent validation: compared with the historical consumer description in
  `notes/gaso-import.md` (announcer section); no fresh attack-cue, PCM or live-audio
  validation. This is largely unchanged prior evidence, not discovery of tank audio.
- Outcome: redundant confirmation of a dependency during mandatory MCP use; useful
  boundary for planning only. Both queries succeeded. Preparation, execution,
  review/manual rework and savings unmeasured; no claimed efficiency gain.
- Next: identify/hash the actual BAG1 tank controller, resources and sound events;
  do not repeat this unchanged BAG2 query to claim original-effect fidelity.

## 20261110-ghidra-046 — Native tank controller and audio dependencies

- Purpose: F1 identity/inventory and bounded F2/F3 reads, without changing runtime.
  Installed Ghidra12.1.4/JDK21.0.12.1+1, retained GUI session and task-owned isolated
  `_work/gaso/gaso-runtime-hooks` project. No installation/configuration changes.
- MCP: `get_program_info()` confirmed BAG2 JP main `SLPM_862.19`, SHA
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`;
  `read_memory(address="0x80031d3c", length=48)` returned initialized accessory-loader
  bytes. This is a BAG2 dependency check, **not** MCP identification of BAG1 overlay.
- Supplementary headless commands: `py -3.13 _work/gaso/trace_native_tank.py` then
  `--label native-tank-lifecycle 0x801d67a0 0x801d6908 0x801d6c18 0x801d6de8
  0x801d6e70 0x801d7218`; scripts call `analyzeHeadless.bat ... gaso-runtime-hooks
  -process native-gas-jp-relocated.dbi -noanalysis -scriptPath _work/gaso
  -postScript AnalyzeGasHooks.java <fresh-output> <addresses>`. First default targets
  `0x801d6480/0x801d666c`. Exit0, 12.017s and7.218s; logs/trial JSON under same labels.
- Input: JP main SHA `9676a28c589e20829e5b43874c8534e49393337f4f5238610598b14257a778ff`,
  JP DBI SHA `05220579f3f84427f7e9744136561a3cc9cb437f3699765f01d06aaaf0f17eb4`.
  File-byte base `0x801d587c` includes12-byte header; independently checked against
  the original main's callback tables in `native-callback-layout.json`. No USA base
  equivalence claimed. Native mesh41 triples independently match source header.
- Main import trial: `py -3.13 _work/gaso/trace_native_tank_main.py`, 8.454s/exit0
  **not useful as decompile evidence**. `-loader-fileOffset 2048` loaded file0x2048,
  independently proved by `VerifyTankMain.java` memory bytes and exact source search.
  Decompiler had Pcode errors and misleading empty/partial functions. Retained wrong
  program `SLPS_012.32` and `native-tank-main-decompile/` as rejected evidence; do not
  reuse them. Offset behavior contradicted the decimal expectation from README.
- Corrected command `...trace_native_tank_main.py --corrected` imports the explicitly
  sliced original payload `native-main-jp-payload.bin` with BinaryLoader base80010000
  and no file-offset option. Header proves load80010000/payload315392. Exit0/7.876s,
  no Pcode errors. `--follow-up` reads that saved program, verifies24bytes at four
  addresses, then decompiles80032064/8002b138/80013e20; exit0/7.479s. Raw payload SHA
  `ec7f4b0ef8c1823e86baa72bf5813e88c0a13e560f60adc5add6e7228bb66faf` and all four
  memory ranges match original bytes after header. Command JSON/logs retain exact args.
- Evidence: acceleration/landing/dimension-dependent scale, saved rival-state restore,
  cues1806/180a and recurring particle sound; main matrix and sound-record consumers.
  Separate deterministic `audio-deployed.json` shows original cues' samples differ
  from resampled deployed6906/690a. No PCM/guest-frame/audio acceptance established.
- Outcome: useful partial static contract, with one counterproductive main import
  detected/corrected by byte validation. Native render/event/rival semantics remain
  incomplete. `funcmatch.py` deliberately not run: this trial traces JP main/overlay,
  not the script's hard-coded USA-main→BAG2 search; no unvalidated match used.
  Preparation/review/manual rework and savings unmeasured; no efficiency claim.
- Next: native primitive dispatch and event/dimension units, then source-derived RED
  tests. Do not replace remaining unknowns with another handcrafted approximation.
- Continuation of the same bounded trial: `trace_native_tank_main.py --follow-up
  --label native-tank-render-dispatch --addresses 0x8002ab3c` exit0/7.662s, then
  `--label native-tank-primitives --addresses 0x8002becc 0x8002c430 0x8002cf6c
  0x8002d020 0x8002d3e0 0x8002bbe8` exit0/7.758s. Corrected payload SHA above,
  four raw-memory checks retained with each trial; 44 records independently counted
  from original accessory. Establishes G3/G4/F3/F4 packet layouts, lighting and
  depth-based OT insertion, NOT yet the initialized blend opcode/prefix semantics.
- `trace_native_tank.py --label native-tank-init --addresses 0x801d58cc` was
  rejected by argparse (overlay wrapper takes positional addresses), no analysis
  occurred. Corrected `--label native-tank-init 0x801d58cc` exit0/7.027s; native
  node-role initialization only, not a new tank implementation or acceptance.
- Raw main pointer scan found GAS-O P1 event callback at80055130, inside table
  base8005510c; `trace_native_tank_main.py --follow-up --label
  native-tank-event-callbacks --addresses 0x80035d30 0x80035d80` exit0/7.982s.
  Direct JAL scan independently located caller8002f3f8 in prologue8002efc8;
  `--label native-tank-animation-dispatch --addresses 0x8002efc8` exit0/8.370s
  proves event16 frame crossing passes value and countdown to selected callback.
  Existing animlib extraction independently shows source63 event16/frame20/value1,
  source64 none; deployed conversion normalizes that value to0. No BAG2 fix inferred.
  Native table801d8280 extracted directly from original JP DBI at offset2a04.
- Updated outcome: useful native primitive/event contract, still missing buffer
  initialization/blend, rival-state and BAG2 dimension mappings, actual PCM/onset.
  No program/session in the GUI was replaced, no runtime changed, no acceptance
  claimed. Additional rework/savings unmeasured; individual headless times above
  exclude preparation and review. Reuse saved trial outputs for the next consumer.
- Packet-initializer continuation: deterministic opcode-store/JAL scan located
  original G3/G4 setters80048d00/80048d50 and shared constructor80025528.
  `trace_native_tank_main.py --follow-up --label native-tank-packet-initializer
  --addresses 0x80025528` exit0/7.097s; output26608bytes, only relevant branches
  read (lines30–35,143–148,568–579; other branches not claimed audited).
  `--label native-tank-packet-helpers --addresses 0x800489a4 0x80048eac
  0x80048c88 0x80048bd4 0x80048d00 0x80048d50` exit0/6.771s, same input/hash
  and independent memory checks. Establishes opaque metal0x38/G3cap0x30, glass0x3a
  with ABR(word-1)=0 and linked draw-mode prefix; PSX-standard branchE1000600,
  alternate GPU branch retained, active branch not live-probed. No textures invented.
  This resolves earlier missing static blend initialization, NOT lighting/runtime
  equivalence, particles/rival behavior, audio or owner acceptance. All saved programs
  remain in isolated task project. Next: rival-state consumer and dimension/particle
  bindings; no need to repeat completed primitive/headless trials unchanged.

## 20261111-ghidra-047 — Reconnect MCP and trace the native caught request

- Purpose: owner's request to reconnect Ghidra and continue approved GAS-O F2/F3.
  Initial `get_program_info()` returned BACKEND_UNAVAILABLE at127.0.0.1:8080.
  An earlier tasklist/name-only search was inconclusive; actual Java/javaw CIM
  inspection found no instance before launching once. Installed Ghidra12.1.4,
  JDK21.0.12.1+1, canonical `ghidra/BAG2JP.gpr`, wrapperPID41328/javaw15628.
  No duplicate instance, installation, extension upgrade or configuration edit.
- GUI recovery: closed only PID-verified Tip modal; two row-opening attempts used
  incorrectly assumed window dimensions and did not open a program. Capture via
  win32gui failed (module absent); first ctypes capture failed pointer conversion.
  Explicit64-bit Win32 signatures in `_work/gaso/reconnect_ghidra_window.py` fixed
  capture. Measured DPI-aware rect1000x750 atDPI120, scaled image640x480: row location
  derived proportionally, not hard-coded physical coordinates. Temporary topmost,
  WindowFromPoint/PID guards and distinct mouse events opened the row; cursor,
  topmost and previous foreground restored. MCP NO_PROGRAM during loading, then
  successful identity/read. The scratch script's old HWND/PID are not reusable.
- Successful MCP queries: `get_program_info()` => `SLPM_862.19`, JP main PSXLE32,
  entry80035d98, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  `decompile_function_by_address` at8002bd70 resolved containing8002bc38;
  `get_function_calls(address="0x8002bc38",direction="callers",limit=12)` found
  wrapper8002c060; decompiled wrapper,8002b5bc and8002d85c. Repeated identity and
  bounded8002d85c read confirmed the retained connection. Pose/dimension consumers,
  not proof of original tank freeze. Native overlay was NOT selected via MCP.
- Supplementary isolated headless uses the existing verified wrapper
  `py -3.13 _work/gaso/trace_native_tank_main.py --follow-up --label <label>
  --addresses <addresses>`; exact commands and memory checks in each trial JSON/log:
  `native-tank-rival-hit-timer`8001e030/8001f6a0/8002f780 exit0/12.394s;
  `native-tank-hit-request-routing`8001fc84/80020478 exit0/7.276s;
  `native-tank-hit-release-check`80024430/8002f788 exit0/7.106s.
  Original JP main SHA9676a28c589e20829e5b43874c8534e49393337f4f5238610598b14257a778ff,
  headerless input SHAec7f4b0ef8c1823e86baa72bf5813e88c0a13e560f60adc5add6e7228bb66faf,
  base80010000. Each trial verifies original bytes at four known addresses.
- Independent validation: original routing table byte8005168f=70 checked directly
  in the hashed payload; call/field chain in existing2efc8/2ed08/2d734 decompiles
  confirms tank writes an XZ-correction threshold, not animation-rate/slot.
  GAS-O-specific request123 and hit timer consumers identified. Inputs/outputs and
  hash retained in `full-fidelity-source-audit/reconnected-hit-routing.json`.
  Timer subtraction is state-update gated, not a proven per-render-frame duration.
- Unhelpful candidates retained:8002f780 is a tail wrapper,8002f788 empty; neither
  establishes native dimension initialization.80024430 handles character8 sound,
  not GAS-O release. Prior80022430 candidate is end/victory/fever state handling,
  not established tank main. Code-mode command quoting failed before execution once,
  corrected without side effects. No result omitted to make the trial look cleaner.
- Previously unlogged post046 bounded reads, retained as historical evidence:
  `native-tank-particle-binding` overlay7980/5de0 exit0/6.240s;
  `native-tank-freeze-rate` main2eee0/32bdc exit0/6.837s;
  `native-tank-rival-controller`2d734 exit0/8.254s;
  `native-tank-rival-motion`2ed08/1d2d8 exit0/7.999s;
  `native-tank-hit-transitions`22430 exit0/7.688s. Wrapper commands/inputs are in their
  trial JSON. Mesh/texture static equality does not prove runtime VRAM/pose fidelity.
- Outcome: MCP recovered and useful bounded native request/timer evidence; partial
  irrelevant candidates explicitly excluded. Fresh preflight PASS0.721s at
  `_work/workflow/20261111T024051754674Z-gaso-ghidra-reconnect/metrics.json`.
  No runtime/game/settings/save changes. Startup/review/manual rework and savings
  unmeasured; headless times exclude preparation. Next: native CAUGHT clip/transitions,
  BAG2 equivalent, dimension units and particles; no acceptance or100% claim.

## 20261111-ghidra-048 — CAUGHT playback and scale-unit correction

- Purpose: original CAUGHT versus BAG2 TIRED and native tank scale units. Retained
  Ghidra12.1.4 GUI; MCP get_program_info confirmed SLPM_862.19 JP PSXLE32 main,
  SHA `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
- MCP decompile8002bf04 resolved known8002bc38; callers8002c060→8002c404 only
  confirm rendering, not reaction dispatch (limited/redundant). Decompile8002d06c
  and get_function_by_address8002ae60 failed FUNCTION_NOT_FOUND; read_memory
  8002d06c/32bytes matched raw payload. Missing definitions are not missing code.
  read_memory80051897 lengths20/4 begins4e4f5051, confirming request123→78;
  repeated identity/table queries are not new discovery. Decompile8002d85c confirms
  initial BAG2 scale/bounds. No GUI names, analysis or selected program changed.
- Supplementary isolated gaso-runtime-hooks inputs: native JP headerless payload
  SHA `ec7f4b0ef8c1823e86baa72bf5813e88c0a13e560f60adc5add6e7228bb66faf`;
  BAG2 raw slpm.bin SHA
  `143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b`.
  BinaryLoader base80010000; no analysis sweep. Native wrapper verifies four raw
  memory ranges; target import independently matches32 MCP bytes at8002d06c.
- `py -3.13 _work/gaso/trace_bag2_caught.py` imported target and read8002d06c,
  exit0/7.556s; `--follow-up --label bag2-caught-request --addresses 0x8002a090`
  exit0/7.121s. Only relevant dispatch branches of22226-byte output read, not a
  full audit. No native overlay selection through MCP is claimed.
- Native command prefix `py -3.13 _work/gaso/trace_native_tank_main.py --follow-up`:
  `--label native-caught-transition --addresses 0x8002ec60` exit0/6.955s;
  `--label native-caught-actor-init --addresses 0x8002f7c0` exit0/7.316s;
  `--label native-caught-scale-consumer --addresses 0x8002e72c` exit0/7.339s;
  `--label native-caught-scale-matrix --addresses 0x8001397c` exit0/7.282s;
  `--label native-caught-scale-refresh --addresses 0x8002e64c` exit0/7.176s;
  `--label native-caught-effective-scale --addresses 0x8002e224` exit0/7.249s.
  Exact arrays/logs/decompiles retained per label. Last two disprove the scale-refresh
  hypothesis: pose interpolation only, no43b8 writes. Record exclusion, not success
  at identifying active scale. No need to repeat these unchanged queries.
- Independent deterministic audit_caught_motion.py/audit_caught_contract.py bind
  source/report/target/policy hashes,14 JP A/P1 clips, table123→70/78, policy78←69.
  CAUGHT2frames loops,13 static and Strike bone5 differs; TIRED34frames moves.
  Codec self-round-trip is not independent game validation. Native loop helper
  adjusts root anchor, state/next request governs release.
- Correction to earlier trial047/topic interpretation:43b8/bc/c0 initially hold
  masked R12 scale, like43a8/ac/b0. Model bounds are43d8/dc/e0; BAG2 bounds1534/38/3c
  must not replace scales14e4/e8/ec or1514/18/1c in the tank formula. Subsequent
  writes/active mapping unresolved. Preserve previous history with this correction.
- Outcome: useful partial playback contract and verified scale-unit correction;
  no runtime/payload/game/save/settings change or fidelity acceptance. Preparation,
  review/manual rework and savings unmeasured; times are execution only. Next:
  targeted scale writes, rival-specific selection and particle bindings.

## 20261111-ghidra-049 — Reference versus working scale

- Purpose: approved F2, targeted writes to native R12 scales and BAG2 scale tuples.
  Reused Ghidra12.1.4/JDK21 isolated project and running GUI, no startup/install.
- Exact MCP queries: `get_program_info()` confirmed SLPM_862.19, PSX LE32 JP main
  SHAea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe;
  `decompile_function_by_address(address="0x8003318c")` failed FUNCTION_NOT_FOUND;
  `read_memory(address="0x8003318c",length=32)` succeeded, bytes
  d0ffbd272c00bfaf2800b6af2400b5af2000b4af1c00b3af1800b2af1400b1af.
- Complementary command: `py -3.13 _work/gaso/trace_bag2_caught.py --follow-up
  --label bag2-tank-scale-writes --addresses 0x8003318c`, exit0/7.091s,
  output4678bytes read completely. Input `_work/mainexe/slpm.bin` SHA
  143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b;
  source32 bytes independently match MCP at3318c. Trial JSON's mcp_matched_address
  field still names its historical2d06c guard, not this new memory comparison.
- Deterministic scans saved scale-write-sites.json and scale-reference-sites.json.
  Native input headerless JP payload SHA
  ec7f4b0ef8c1823e86baa72bf5813e88c0a13e560f60adc5add6e7228bb66faf.
  Direct SW/SH scans found native43b8/bc/c0 only in init; no claim about aliases,
  memcpy or overlays. Nearest-stack-prologue labels are hints, not function bounds;
  native actor init is previously proven leaf2f7c0, not nearest prologue2efc8.
- BAG2 consumer copies reference1514/1518/151c to working14e4/14e8/14ec for main
  and secondary actors; native initializer/renderer reviewed unchanged for contrast.
  Literal1514 candidate80040e14 was independently rejected by fresh MCP decompile
 80040d9c (ISO9660 directory routine); irrelevant result retained, not scale proof.
- Outcome: useful bounded static distinction, not dynamic mapping acceptance or
  exhaustion of writers. No need for funcmatch (no USA-main equivalent search);
  no native overlay MCP claim. No runtime, payload, game or protected files changed.
  Execution7.091s excludes preparation/review; rework and savings unmeasured.
  Next: argument provenance and pointer-based scale writers, then CAUGHT selection.

## 20261111-ghidra-050 — Scale load arguments and host writer

- Purpose: finish the bounded static load-argument question, not repeat pose scans.
  Reused running GUI and Ghidra12.1.4/JDK21 isolated project, no startup/config edits.
- Exact MCP: `get_program_info()` confirmed SLPM_862.19 Japanese PSX LE32 main,
  SHAea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe;
  `decompile_function_by_address(address="0x8002b9f4")` resolved8002b5bc;
  `read_memory(address="0x80051904",length=48)` returned the initialized character,
  stage-spacing and offset tables. Queries succeeded; independent raw payload bytes
  match the returned48 bytes. This confirms a loader dependency, not live scale values.
- Native direct JAL scan found sole main call to2f7c0 at2e108. Supplementary command
  `py -3.13 _work/gaso/trace_native_tank_main.py --follow-up --label
  native-tank-scale-load --addresses 0x8002de94`, exit0/7.593s; output2855bytes
  read completely. Existing native JP payload SHA
  ec7f4b0ef8c1823e86baa72bf5813e88c0a13e560f60adc5add6e7228bb66faf,
  base80010000 and VerifyTankMain memory checks retained. No native GUI selection claim.
- Independent table/source audit saved `full-fidelity-source-audit/scale-load-arguments.json`:
  BAG1 table800516d8, BAG2 table80051904 and loader formulas. Native normal Gas-O116,
  special divisor8; BAG2 uses a signed runtime stage factor and per-character byte.
  Host `b1v_dancer_scale()` writes both saved/working triples with guarded Q12 adjustment;
  current source SHA0a41b94733438d74bd9074a6beca4ec1d833af529e01f1d29252751a567e3254.
- Bounded literal scan of original JP Gas DBI and saved Bi-O P1/P2 DBIs is not
  exhaustive alias/memcpy analysis. P1 hits801d14ec/801d151c are pointer data, not
  established instructions/writers; rejected as writer evidence. Hashes/hits in report.
- Outcome: useful static load contract plus a relevant host writer omitted by MIPS-only
  scans. Stage factor/frame order, indirect writers outside this scope and live tank
  scaling remain unverified. No runtime edits or new gameplay/audio acceptance.
  Preparation, manual rework and savings unmeasured;7.593s excludes those costs.
  Next: initialized RAM evidence for stage factor and before/after-host scales, reusing
  valid dumps and capturing only missing states; do not retrace the same load argument.
- Subsequent independent contrast reused existing initialized RAM, not a new game:
  sign-intro-31-ram.bin SHAe272fae7241f8e9e5261ad9cbe335376dee959aef53d9616a775714d4f645a9f
  and adjacent metadata bind runtime27dfebb4. Stage factor256, Gas-O saved/working
  triples75 and Heat85; same-run host log states Gas-O98→75. Added to the source
  report. Non-atomic historical snapshot, not current-runtime or before/after proof.
  Useful reuse avoids a duplicate capture for this historical state; time/savings
  still unmeasured. Next: effect/dancer coordinate-scale contract, not another loader scan.
- Later reconnection, same day: `get_program_info()` failed BACKEND_UNAVAILABLE
  (127.0.0.1:8080 unreachable); Get-CimInstance found no java/javaw. Launched once
  `ghidraRun.bat ghidra/BAG2JP.gpr` (javaw PID50896), closed Tip of the Day by
  PID-guarded WM_CLOSE and opened the SLPM_862.19 row with a temporary copy of
  `_work/gaso/reconnect_ghidra_window.py` updated with the fresh HWND and PID
  (copy deleted afterwards). Then `get_program_info()` returned SHA ea5a1668… and
  `read_memory(0x80051904,20)` matched the earlier bytes. No project data or
  configuration changed. About 60s of wall time spent recovering.

## 20261111-ghidra-051 — Tank versus dancer scale convention

- Purpose: approved F2, decide whether native tank R12 and BAG2 dancer scale share
  units before mapping the effect. Reused running GUI, no startup/config edits.
- Exact MCP: `get_program_info()` SLPM_862.19 SHA ea5a1668…;
  `decompile_function_by_address(address="0x80013144")` → FUN_80013144, same
  formula as native 8001397c (matrix S*node>>12, bone translations *S>>7, children
  +0x94/+0x98); `decompile_function_by_address(address="0x80023c38")` → 80023be4,
  memory-card routine using global 800514e4: rejected as false positive.
- No new headless run: reused saved native decompiles 801d6908, corrected 80013ed4,
  8001397c, 8002e72c. Candidate 80013144 found by deterministic `sra ...,7`
  cluster scan of raw `slpm.bin` SHA 143b4bf8… against native JP payload ec7f4b0e….
- Failed attempt: reading node+8 at historical RAM actor+0x14 returned pointers;
  layout assumption wrong, result discarded.
- Outcome: useful. BAG2 and BAG1 dancer scale convention matches (S/128); native
  tank uses R12. Tank node+8 unit, +0x43cc dependence and BAG2-only rival Y entries
  remain unverified. No runtime edits or acceptance; time/savings unmeasured.
  Next: verify tank node+8 unit and fall clamp, then CAUGHT per rival.

## 20261111-ghidra-052 — Node scale unit and tank/dancer space

- Purpose: approved F2, resolve tank versus dancer node+8 unit. Reused running GUI
  and isolated headless project; no startup, install or configuration change.
- Exact MCP: `get_program_info()` confirmed SLPM_862.19 SHAea5a1668…;
  `decompile_function_by_address("0x800220b8")` = mesh-section pointer relocation;
  `get_function_calls("0x800220b8", callers)` → sole caller80022518;
  `decompile_function_by_address("0x80022518")` copies the 10 xf words verbatim to
  node+0..+0x24 (node+8 = file scale) and recurses children +0x94/+0x98. Useful.
- Headless native JP (payload SHAec7f4b0e…, base80010000), all exit0:
  `--label native-tank-node-init --addresses 0x80026aec` 12.822s, mesh-header pointer
  relocation (false positive for node+8); `--label native-tank-node-build
  --addresses 0x80025528` primitive-packet builder (false positive for node+8, keep for
  F4 primitives); `--label native-model-node-parser --addresses 0x80029624` 7.572s,
  802 bytes: mid-function fragment because the address belongs to another build
  (irrelevant, rejected). No native JP parser identified.
- Independent checks: raw bytes of80013e20 show lwc2 IR0 + GPF sf=1 (ScaleMatrix R12).
  Inline file scan plus `_work/gaso/rest_pose_extents.py` (new scratch, rotations
  ignored): Gas-O000.bin 41 bones, size [17395,47826,15096]; tank002.bin xf scale4096,
  size [2160,4480,2160].
- Outcome: useful. Tank and dancer use the same R12 node scale; vertex ratio follows
  801d6908 formulas. Animation translation unit (`*S>>7`) is inferred, not traced.
  No runtime edits, captures or acceptance; time savings unmeasured.
  Next: fall clamp +0x43cc scale dependence, then CAUGHT per rival.
