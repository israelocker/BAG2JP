---
id: tool-evidence-ghidra-psx-psyq
title: "Evidencias: Ghidra, PSX y PsyQ"
tags: ["tools", "evidence"]
summary: "Historial de Ghidra MCP y soporte PSX/PsyQ; no certifica identificación automática."
related: ["notes/assets.md", "AGENTS.md"]
created: "2026-11-06"
updated: "2026-11-15"
doc_kind: evidence
---

# Ghidra / PSX / PsyQ — historial

## 20261115-ghidra-standards-recheck — consultas de los auditores documentales

- Tipo: uso acotado reportado por subagentes; sin análisis/instalación ni partidas.
- Ambos informes conservan MCP `get_program_info()` → `SLPM_862.19`, main PSX JP,
  SHA-256 `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  Auditor personajes: `get_function_by_address(0x800125fc)` → función
  `800125fc..8001262b`, confirma existencia, no semántica/lifecycle. Auditor escenarios:
  `read_memory(0x800555a8,8)` → `98 00 88 00 a4 00 98 00`; índice u16 1=136,
  compatible con duración stock citada. No overlay de escenario verificado.
- Evidencia: `_work/retro/standards-recheck/{characters,stages}.md`; contraste de
  referencias con fuentes documentales en esos informes. La primaria no presenta
  esos leads como prueba de ejecución/aceptación ni repite consultas sin pregunta.
  Auditor workflow omitió MCP por restricción documental y lo declaró; sin efecto
  sobre el uso efectivo de MCP por los otros auditores y las consultas previas de
  esta sesión. Captura/FFmpeg/intérprete no ejecutados: ningún cambio de media/código.
- Dictamen: inconcluso para comportamiento; identidad/bytes acotados, no utilidad
  universal. Tiempo, retrabajo y ahorro no medidos. Reutilizar mismos inputs y
  confirmar consumidores en la tarea de implementación, no por esta revisión.

## 20261115-ghidra-retro-standard — contraste documental CAUGHT

- Tipo: uso real acotado para contrastar una afirmación del nuevo estándar.
- MCP `get_program_info()` confirmó `SLPM_862.19`, main PSX JP, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`;
  `read_memory(address=0x80051897,length=1)` devolvió `4e`, sin gaps. No overlay
  seleccionado ni cambios de análisis. Version instalada registrada: Ghidra12.1.4.
- Contraste: inventario Block5 existente y fuente `assets/disc_files/SLPM_862.19`
  (comparación directa de hash/byte en evidencia `_work/retro/duet-entry35.json`).
  Demuestra el byte de routing request123→78, no aptitud de un clip ni reproducción.
- Dictamen: útil para evitar confundir slots BAG1/BAG2 en la norma. Tiempo de
  preparación/ejecución/retrabajo y ahorro no medidos. No nuevo juego/disassembly:
  sin parche ni cambio de comportamiento. Reutilizar con el mismo hash/contexto.
- Consulta posterior del owner sobre distancia: mismo main JP, MCP
  `read_memory(0x80051918,12)` = `82 82 82 82 82 56 82 82 82 82 82 82` y
  `read_memory(0x8002ba18,4)` = `17 b6 00 0c` (JAL0x8002d85c original). Contraste
  con `b1home_pair`/`b1v_home_hook`: el gate admite tabla130, excluye id>=11 e
  IDs10/14 de personajes; no es filtro de mapa Gas-O. Esto demuestra origen de
  guard/tabla, no ejecución del hook ni aceptación visual de cada escenario.
  Tiempo/ahorro no medidos; sin partidas ni cambios de fuente.

## 20261115-ghidra-block5-inventory — ruta CAUGHT BAG2 por rival

- get_program_info: SLPM_862.19, SHA ea5a1668…. read_memory(0x80051897,1)=4e:
  tabla 0x8005181c manda request123 al slot78 (reconfirma nota F2). read_memory
  (0x8005168f,1)=00 en este programa, distinto del 70 citado en la nota F2; no se
  interpreta aquí (posible otro binario/contexto), queda por contrastar.
- Útil: confirma que ningún rival stock tiene ruta CAUGHT nativa. El formato de 19
  pistas se midió con motion_codec, no con Ghidra. Tiempo/ahorro no medidos.

## 20261115-ghidra-process-game — identidad original para la toma

- get_program_info primero: SLPM_862.19 JP/main,PSXLE32,1324funciones,
  SHAea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe.
  read_memory(0x8002d06c,length16) devuelve
  c0ffbd272400b3af219880003400b7af,sin gaps; proyecto/análisis intactos.
- Útil como identidad/seamCAUGHT obligatorio, no nuevo matching ni parcheMIPS.
  Toma real confirma recoveredside2/gf8361/P2anim1 en trace, luego retirada y
  selector; audio nativo verificado por el grabador, no atribuido a Ghidra.
  Tiempo/ahorro no medidos. Resultado de toma y conformidad en notes/gaso-import.md.

## 20261115-ghidra-process-audio-adapter — identidad y seam original

- MCP get_program_info confirmó SLPM_862.19 JP/main, PSX LE32,1324funciones,
  SHA256ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe.
  read_memory(0x8002d06c,length16) sin gaps:
  c0ffbd272400b3af219880003400b7af. No cambios de análisis ni funciones.
- Útil para identidad/seam CAUGHT original obligatorio; no prueba de audio Win32.
  API de host contrastada con docs/ABI previas y ensayos propios independientes;
  funcmatch/PsyQ/offline disassembly no pertinentes: ningún matching/patchMIPS.
  Tiempo/ahorro no medidos; siguiente1toma experimental tras host/review.

## 20261114-ghidra-block3-rehit-audio - origen del sonido re-hit en Heat y despachador SPU

- Propósito: comprobar si el modo1 nativo de Heat dispara algún cue SPU en el re-hit que `mode0` (`gaso_caught_can_continue`) pudiera omitir.
- MCP stdio (`_work/gaso/probe_call.py`, `SLPM_862.19`, sin modificar análisis ni crear funciones):
  - `get_xrefs_to` sobre `0x8002e478` (`_work/gaso/block2/xrefs-2e478.json`, 28 llamadores en main).
  - `decompile_function_by_address` sobre `0x800342dc` (`dec-800342dc.c`), `0x8002e2d0`, `0x8002e478`, `0x8003190c`.
  - `read_memory` sobre `0x80025500` (1024 B, `mem-80025500.json`) y `0x80054fe4` / `0x80031900`.
- Validación independiente: Capstone sobre las tablas y callbacks de Heat/Gas-O en el volcado RAM `wider-initial-camera-ram.bin` y comparación continua de WAVs (`clamp` vs `r2` bit-idénticos `max_abs_diff = 0` en 367,500 muestras; `clamp_re - r3_re` correlaciona `1.0000` con `slide_diag_1st - clamp_1st` en `mode1` vs `mode1`).
- Resultado: útil; descartó falta de cues en `mode0` y probó que la diferencia de `r3` es una variante RNG nativa. Tiempo no medido.

## 20261114-ghidra-block2 - correa, intercambio de lados y fever sobre ±870

- Propósito: riesgos del Bloque 2 (ataques/CAUGHT/dueto) con homes ±870.
- MCP por el puente stdio (`_work/gaso/probe_call.py`, javaw 63424): `get_program_info`
  → `SLPM_862.19`; `get_xrefs_to` 0x8005F820 (1 PARAM en FUN_8001E0F4), 0x8005F848 (0),
  0x8002CD48 (llamada en 0x8002D81C, sin función definida); `get_function_by_address`
  0x8002D818/0x8002AD1C → FUNCTION_NOT_FOUND; `read_memory` 0x8002D500/880,
  0x8002AA40/512, 0x8002AC40/512 (salidas en `_work/gaso/block2/`).
- Validación independiente: Capstone sobre los mismos bytes (ver capstone.md).
- Resultado: útil. El clamp usa ctl+0x28/0x38 con banderas dancer+3 y ctl+0xC; en
  0x8002ABE4..AD44 hay un intercambio de home/radio entre lados solo para los personajes 10/14.
  No se crearon funciones ni se modificó el proyecto. Tiempo no medido.
- Siguiente: el código de fever del overlay 005 no está en el programa principal; el dueto se
  comprobará en juego.

## 20261114-ghidra-initial-anchor — offset nativo y referencia READY

- Puente stdio instalado, Ghidra12.1.4 e instancia existente preservados. Consultas con
  `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/gaso/probe_call.py`: siempre
  `get_program_info()` primero; main JP SLPM_862.19, SHA256
  ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe, sin overlay.
- `decompile_function_by_address(0x8002DA74)` confirma focal8006D98C; lecturas de
  80044480/192B y8002DCFC/12B contrastan SetGeomOffset/SetGeomScreen.
  La segunda devuelve `00 01 04 24 39 11 01 0c 78 00 05 24`: argumentos256/120.
  Evidencia `alignment-{gte-setup,geom-offset}-ghidra.json` y
  `alignment-measure3-offset-mcp.json`, en `_work/gaso/drift/end-center/`.
- Contraste independiente: código GTE del framework aplica factor horizontal0.75 para
  16:9; cámara y raíces muestreadas en grabación aceptada initial-alignment-measure3.
  El cálculo previo lo omitía: se corrige con nueva evidencia, no reescribiendo su historial.
  Modelo READY propone±1300; no certifica posición del cuerpo ni ausencia de recorte.
- Capstone se detuvo en ctc2 no soportado; repetición con skipdata mantuvo los bytes
  explícitos, sin interpretar datos omitidos como instrucciones. MCP verifica los bytes.
  Uso útil para corregir el modelo; tiempo/manual/ahorro no medidos. Siguiente: revisión grabada.

## 20261114-ghidra-wider-home-implementation — cámara y costura final

- Ghidra12.1.4 por puente stdio instalado, instancia existente preservada. Cada llamada
  de `_work/gaso/probe_call.py` ejecuta primero `get_program_info()`; main JP SLPM_862.19,
  SHA256 ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe; sin overlay.
- Decompilaciones80014E10→FUN80014C3C,80017AC0,8002C404 y8002DA78→FUN8002DA74:
  eye8005D158, target8005D0C8, matriz8005D0F0, focal8006D98C aplicado por FUN80044504.
  Salidas `wider-home-{camera,projection,pose,geom}-ghidra.json` en el directorio end-center.
- Verificación final `read_memory(address="0x8002BA08",length=32)` devuelve
  `03 3a 07 00 21 20 40 02 21 28 20 02 10 00 a6 27 17 b6 00 0c ff ff e7 30 38 00 42 8e 00 00 00 00`;
  a2=sp+10 y JAL8002D85C coinciden con pruebas y emisión AOT aislada.
- Intento con py3.13 falló antes de MCP: ModuleNotFoundError mcp. Repetido con
  D:/Dev/Tools/ghidra-mcp-python/python.exe y pwsh respondió, sin instalar ni reiniciar GUI.
  Evidencia `wider-home-seam-final-ghidra.json`.
- Independencia: ocho snapshots RAM de baseline grabado aceptado, fingerprints host y
  generación shard08. Útil para cálculo y orden de inicialización; offset geométrico256/120
  aún supuesto, no prueba alineación visual. Tiempo/manual/ahorro no medidos.
  Siguiente: revisar la partida experimental grabada, no repetir consultas sin nueva duda.

## 20261114-ghidra-wider-home — inicialización y separación de bailarines

- Propósito: localizar la referencia inicial que el owner pide abrir bajo cada barra,
  sin probar otra partida ni modificar el análisis. Ghidra12.1.4, GUI Java existente;
  el catálogo directo no exponía Ghidra y los puertos inspeccionados antes no respondían.
- Puente instalado: `D:/Dev/Tools/ghidra-mcp-python/python.exe
  _work/gaso/probe_call.py <tool> <json> <output>` con `pwsh.exe`;
  el script abre stdio `-m ghidra_mcp --ghidra-server http://127.0.0.1:8080/`.
  `get_program_info()` primero en cada conexión confirmó `SLPM_862.19`, JP/PSX LE32,
  SHA256 `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  No se identificó overlay ni se abrió otra GUI/reinició Java/cambió configuración.
- Consultas reales: `decompile_function_by_address(address="0x8002B5BC")`,
  `disassemble_function(address="0x8002B5BC",limit=320)`,
  `read_memory(address="0x80051918",length=12)`. Listado filtrado `?disass` del puente
  confirmó el schema de disassembly antes de usarlo. Salidas `wider-home-init-ghidra.txt`,
  `wider-home-init-disasm.json`, `wider-home-stage-table.json` en
  `_work/gaso/drift/end-center/`.
- Fallo retenido: primer comando con powershell.exe eliminó comillas del JSON y produjo
  `JSONDecodeError` antes de llamar MCP. Mismo comando con pwsh.exe respondió; no fue
  un fallo de Ghidra. La ausencia del catálogo directo no implicaba backend irrecuperable.
- Evidencia: home ordinario = ±tablaStage×4×zoom/256 (±520 para tabla0x82/zoom256);
  stage5 tabla0x56; stage0xB/modo4/personajes especiales tienen excepciones.
  Vector de inicialización en a2=sp+0x10 antes de JAL8002BA18 a8002D85C.
- Independencia: bytes originales de tabla/JAL y homes RAM históricos coinciden en
  `wider-home-audit.json` (hashes completos). Resultado útil para localizar seam y
  causa de cercanía; no resuelve proyección objetivo ni valida un nuevo home.
  Tiempo/manual/ahorro no medidos. Siguiente: calcular posición contra cámara inicial.

## 2026-11-13 — HUD Gas-O: consumidor y límites de la prueba UV

- Propósito: rótulo nativo BAG2 por lado, sin cambiar el descriptor compartido de Bi-O.
- Entorno: Ghidra 12.1.4 instalado; MCP `get_program_info()` confirmó main japonés
  `SLPM_862.19`, PSX LE32, SHA256 `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  Consultas relevantes: `decompile_function_by_address(0x800342dc)` (selección/carga
  de packs) y `decompile_function_by_address(0x800220b8)` (layout de nodos y type4).
- Fallo conservado: consulta por nombre supuesto `FUN_800274c4` devolvió
  `FUNCTION_NOT_FOUND`; no se creó una función ni se modificó análisis.
- Overlay005 no estaba cargado en el main del GUI. Se reutilizó la exportación aislada
  `_work/gaso/hud/descriptor-decompile/80093de0.c`; NO es una nueva descompilación MCP
  del overlay ni prueba del código residente. Archivo `assets/archive/system/005.dbi`
  SHA256 `bc5f3045084e4b3e19009910441627977863c8b5791b5cdb716a766e68b28fb2`,
  payload a `0x8008f890` después de 12 bytes; consumidor `0x80093de0`.
- Contraste independiente: Capstone WSL y palabras originales verificaron hook
  `0x80093f6c=3c0400ff`, JAL anterior `0c012649` y SH `a6220012`.
  Harness host prueba las cinco escrituras de sprite; no dispatcher real.
- Resultado: útil para delimitar carga, layout y hook; exclusión UV corporal NO
  acreditada. Inventario `bag2-font/corrected/model-inventory.json`: 16 miembros
  de modelos USA/JP parseados completos; cuerpos tienen 14 nodos type4. Un primer
  inspector limitado a type0/1/2 se detuvo con `ValueError: 4`; se amplió el inventario,
  no se interpretó el fallo como ausencia de UV. Sin modificar proyecto Ghidra.
- Tiempo, ahorro y retrabajo manual: desconocidos. Siguiente: identificar todos los
  layouts UV y selección de textura antes de integrar. No se usó funcmatch: no se
  buscaban equivalentes de funciones main BAG1→BAG2.

## 2026-11-07 — ghidra-040 — controlled native-reference session check

- Purpose: mandatory MCP identity check before renewing the native BAG1 FEVER2 reference. `get_program_info` confirmed JP main `SLPM_862.19`, PSX little-endian, SHA-256 `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`; `read_memory(address="0x80055130", length=4)` returned `11 00 23 00`, no gaps. Read-only; the native BAG1 capture is a separate runtime, not this selected binary.
- Independent validation: unchanged archive/table evidence in ghidra-038 resolves BAG2 chr9 solo/duet entries 17/35. Outcome: redundant confirmation of unchanged evidence, not native playback or visual-fidelity proof. Time, savings and manual rework unmeasured. Next: controlled native FEVER2 recording from a blank playlist, without changing the candidate mapping.

## 2026-11-07 — ghidra-039 — clean-fever session identity check

- Purpose: verify the selected binary before the clean solo-fever capture. Ghidra 12.1.4 MCP `get_program_info` confirmed JP main executable `SLPM_862.19`, PSX little-endian, SHA-256 `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`; `read_memory(address="0x80055130", length=4)` returned `11 00 23 00`, no gaps. No analysis or game memory modified.
- Independent validation: existing archive/table evidence in ghidra-038 still resolves chr9 solo/duet to entries 17/35. Outcome: redundant with unchanged table evidence, but mandatory session identity/query verified; not proof of visual fidelity. Time, savings and manual rework unmeasured. Next: review continuous captures and read-only loaded-candidate evidence, not another table query.

## 2026-11-07 — ghidra-038 — Gas-O solo/duet fever entries

- Purpose: confirm the JP chr9 choreography entries before accepting the solo-fever candidate. Ghidra 12.1.4 MCP `get_program_info` identified `SLPM_862.19`, PSX little-endian, SHA-256 `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`; `read_memory(address="0x80055130", length=4)` returned `11 00 23 00`, no gaps (main executable, not an overlay).
- Independent existing check: `fever_entries.py` and the archive inventory resolve those u16 entries 17/35 to `bi_o/choreography_a` / `choreography_b`. This confirms the candidate's entry 17 targets solo only; it does not validate movement, voices or duet in-game. Outcome: useful, bounded table confirmation. Preparation/execution/review time and savings unmeasured; no manual rework. Next: full-match evidence for the unchanged experimental runtime `165a2dce…`.

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

## 20261110-ghidra-041 — 2026-11-10 UTC — Gas-O sign occlusion, unavailable backend

- Tipo: arranque/diagnóstico bloqueado; no análisis semántico satisfactorio.
- Versión/entorno: Ghidra 12.1.4 instalado en `D:/Dev/Tools/ghidra_12.1.4_PUBLIC`,
  gestor de proyecto ya abierto, PID 57236, sesión Windows 2, HWND 1052560,
  proyecto `D:/Dev/Recomp/BAG2JP/ghidra/BAG2JP.gpr`. No se lanzó otra instancia.
- MCP exacto: `get_program_info()` primero, dos reintentos tras acciones GUI
  acotadas y una comprobación final; todos devolvieron `BACKEND_UNAVAILABLE`, backend
  `http://127.0.0.1:8080`. No hubo consulta de memoria/decompilación ni escritura.
- Entradas de la tarea: escenario BAG1 JP `_work/bag1_disc_full/STAGEE/ST_GAS.DFS`,
  SHA-256 `5da6d4a2ca56713bd88d71edcd377f4c4a0cb5fe3286184b37e73f9559f3efa9`;
  etapa desplegada 197, SHA-256
  `805872fadd6b214077e36dee28e2a2f234a73cf6b836767f55a0fefab5c883f6`.
  Objetivo previsto: `SLPM_862.19` (BAG2 JP), después renderer de escenario;
  identidad/hash y módulo cargado **no confirmados por MCP en este ensayo**.
- Evidencia GUI: `winshot.ps1 -Ids 57236 -Out ...` capturó el gestor con el
  programa en el árbol, no CodeBrowser; `_work/gaso/ghidra-sign-start.png` y
  `ghidra-sign-crop.png`. `_work/inspect_ghidra_ui.ps1` no enumeró elementos;
  `_work/open_ghidra_file.ps1` devolvió `SetForegroundWindow=False`.
  `_work/gaso/open_existing_ghidra_program.py` envió un doble clic acotado con
  `SendMessageTimeout` (también coordenadas DPI-aware): mensajes aceptados, pero
  sin apertura/MCP demostrados; la primera captura posterior fue idéntica.
- Límites: `OpenInputDesktop` de solo lectura abrió `Default`; no prueba una causa
  UIPI. No se ejecutó GhidraGo porque su fallback podría abrir otra instancia.
  No se instalaron componentes ni cambiaron configuración, análisis o proyecto.
- Contraste independiente: `_work/gaso/sign-candidate-audit.json`, generado con
  `py -3.13 _work/gaso/audit_sign_candidate.py`, acredita igualdad binaria del
  modelo desplegado y la conversión actual; no sustituye Ghidra ni prueba el
  renderer. Preflight en `_work/workflow/20261110T022054362906Z-gaso-sign-depth/`.
- Dictamen: **no ejecutado / bloqueado** para análisis requerido; intentos de
  arranque inconclusos. Éxitos históricos de otras entradas no prueban conexión
  actual. A no corregido, B no aceptado; ningún nuevo test de juego.
- Medición: preparación, ejecución y retrabajo no medidos; ahorro no medido.
- Siguiente paso: recuperar CodeBrowser/backend en la sesión existente, confirmar
  programa/región/módulo y realizar una lectura pertinente antes de parchear A.

## 20261110-ghidra-042 — 2026-11-10 UTC — recovered existing CodeBrowser, Gas-O mesh parser

- Propósito: desbloquear el análisis obligatorio de A sin duplicar Ghidra ni
  modificar configuración, instalación o datos de análisis. Complementa 041:
  aquel fallo sigue siendo histórico, pero ya no describe la conexión actual.
- Versión/identidad: Ghidra 12.1.4, mismo javaw PID 57236/sesión 2. MCP
  `get_program_info()` confirmó `SLPM_862.19`, PSX LE32, ejecutable BAG2 JP,
  SHA-256 `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`,
  1324 funciones. Programa principal, **no** overlay del escenario.
- Arranque acotado: el primer `get_program_info()` devolvió `BACKEND_UNAVAILABLE`.
  `py -3.13 _work/gaso/ghidra_ui_probe.py` verificó escritorio Default, sesión 2,
  integridad media de ambos procesos y acceso al cursor; por tanto no se confirmó
  el antiguo diagnóstico UIPI. `py -3.13 _work/gaso/open_ghidra_existing_input.py`
  verificó PID/HWND/foreground, adjuntó temporalmente hilos de entrada, abrió el
  programa con un doble clic real y restauró cursor/foreground. Primer MCP tras
  abrir: `NO_PROGRAM`; tras capturar CodeBrowser, identidad satisfactoria. Sin
  reinicio, nueva instancia, instalación ni escrituras MCP.
- Evidencia: `_work/gaso/ghidra-ui-probe.json`, `ghidra-recovery-start.png`,
  `ghidra-recovery-open.png` y miniatura `ghidra-recovery-open-small.png`.
- Consultas MCP: `read_memory(0x80027FC8,96)` satisfactoria, sin huecos;
  `decompile_function_by_address(0x80027FC8)` falló `FUNCTION_NOT_FOUND`.
  `list_segments(offset=0,limit=20)` devolvió 20/26; no se utilizó como inventario
  completo. Decompilaciones `0x800220B8` y `0x80022518`, xrefs de `0x800220B8`
  (un llamador 0x800225BC) satisfactorios. Confirman inicialización del header
  BAG2 de 0x48 palabras y referencias de malla, no la causa de oclusión.
- Consultas sin utilidad práctica para A: listados `filter=80023` (13 funciones)
  y `filter=80026` (3); decompilaciones `0x8002384C`, `0x80023FF8` y `0x80026FC8`
  resultaron ajenas al renderer buscado. `0x80027E98` también devolvió
  `FUNCTION_NOT_FOUND`. No se crearon funciones ni se supusieron límites.
- Contraste independiente: conversor `model_bag1_to_bag2.py` y auditoría binaria
  previa; `py -3.13 _work/gaso/inventory_sign_geometry.py` produjo
  `_work/gaso/sign-geometry.json`: 32 mallas tipo 1 y un nodo tipo 3, sin instancias
  tipo 2 en esta fuente. Se conservan vértices/transforms nativos. Hashes de fuente
  y etapa: los de 041. Corrección regional de 041: la ruta `bag1_disc_full` usada
  es la fuente USA; la comparación regional previa en la nota canónica informa
  modelos USA/JP idénticos, no autoriza etiquetar esa ruta como JP.
- Dictamen: **útil** para recuperar MCP y verificar el parser; **parcial** para A.
  No demuestra un parche, orden OT correcto ni aceptación en juego. La captura
  diagnóstica de paquetes GPU del candidato sin modificar se tramita por separado.
- Medición: tiempo, retrabajo y ahorro no medidos. Próximo paso: correlacionar
  textura/geometría GAS y paneles con paquetes/OT reales antes de modificar A.

## 20261110-ghidra-043 — 2026-11-10 UTC — lecturas acotadas de emisores GAS
- Tipo: uso real, continuación de 042 en la misma instancia recuperada, sin
  escrituras/análisis nuevos. Ghidra 12.1.4, SLPM_862.19 main BAG2 JP, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  Identidad obtenida en 042; no se afirma overlay cargado.
- MCP exacto: `read_memory(address="0x80027FC8",length=512)`,
  `read_memory(address="0x800281BC",length=1024)`,
  `read_memory(address="0x800285BC",length=1536)` y
  `read_memory(address="0x80028BD8",length=1536)`: todos sin huecos.
- Evidencia `_work/gaso/`, respectivamente: `sign-emitter-ghidra.json` SHA-256
  `86d917dab824f85932dae0f7a069f56da966d33784b687c7d5cc5fa75fe76541`,
  `sign-quad-emitter-ghidra.json`
  `a3c741563ef977191e667f54d25e04f8a95308fc7e01fdd423be8bf45c1edbdd`,
  `sign-ft4-emitter-ghidra.json`
  `2a9742963b113fe3259c9cd5e9cd198211caaaf66f4d3883ec76f109fb27c09f`,
  `sign-ft4-emitter-tail-ghidra.json`
  `ba54eac1b8bebc27ccf4a5d4bddf194c2cef837afa785ccd813ed9e15822176e`.
- Contraste: Capstone-006 (incluido NCLIP no decodificado), funcmatch-002 y
  comparación byte a byte con los payloads de los ejecutables originales.
  FT4 en 80028BDC y esquinas/profundidades coherentes con paquetes de GAS.
  No se crearon funciones en tramos sin definición; callers/ejecución exacta
  y causalidad de la oclusión siguen sin confirmar.
- Dictamen: **útil** para evidencia binaria y layout local; **inconcluso** como
  solución de A. Un candidato rojo posterior se descartó como causa al comprobar
  que solo comparte un borde rasterizado con GAS, sin área interior común.
  No sesgo OT ni geometría modificados. Medición de ejecución, preparación,
  revisión/retrabajo y ahorro: no medida. Siguiente: analizar capturas tempranas
  de la intro y localizar una superposición interior real antes del parche.

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


## 20261111-ghidra-053 — Native tank height ratio across characters

- Purpose: owner-approved method for BAG2-only rivals; measure native tank/rival
  height ratio on all 14 BAG1 characters. Static only.
- MCP: `get_program_info()` confirmed SLPM_862.19 SHA ea5a1668…, 1324 functions;
  reused running GUI, no startup. No further MCP query was needed: tables came from
  raw USA `scus.bin` (0x80059918 names, 0x800558fc scale = JP 800516d8) and the known
  JP Y table 801d8280.
- Scratch: member 0 extraction via `tools/bag1import/rebuild_dfs_members.read_members`,
  rest extents via `_work/gaso/rest_pose_extents.py`. All 14 models consumed fully.
  Report `full-fidelity-source-audit/tank-height-ratio.json` binds DFS/model SHAs.
- Error found and corrected: first report used +230 for the ID13 radius; fixed to
  +600 (437).
- Outcome: useful but non-constant ratio (distinct entries 1.119–1.228, median 1.164).
  Translation-only rest pose; xf[0] rotation consumer not traced. Time savings
  unmeasured. Next: BAG2-only rest heights, clamp +0x43cc, CAUGHT per rival.

## 20261111-ghidra-054 — BAG2 stock rest heights

- Purpose: finish the approved BAG2-only rival height measurement. Static only.
- MCP: `get_program_info()` confirmed SLPM_862.19 SHA ea5a1668..., 1324 functions;
  reused running GUI, no startup. No further MCP query: model table 0x80055258 and
  scale table 0x80051904 read from raw `_work/mainexe/slpm.bin` (SHA 143b4bf8...),
  both already MCP-verified in trials 049/050.
- Scratch: `_work/gaso/bag2_rest_heights.py` (BAG1 0x3C and BAG2 0x48 mesh headers via
  `tools/bag1import/model_bag1_to_bag2.py`). 18 BAG2 and 14 native models parse with
  0 trailing bytes; no type-2 instances in either game, so trial053 heights hold.
- Outcome: useful. Native entry x r is not proportion-preserving on BAG2 stock models
  (Shorty 0.98x, Strike 1.38x) and undefined for BAG2-only rivals; proposed rule
  ratio[ID] x real rival rest height (median 1.164 for BAG2-only) equals the native
  formula for imported native models. Translation-only rest pose, type-4 nodes ignored,
  no runtime check; time savings unmeasured. Next: clamp +0x43cc, CAUGHT per rival.

## 20261111-ghidra-055 — Tank fall contract and world ratio

- Purpose: approved F2 clamp/fall unit. Static only; no runtime or source edits.
- MCP: `get_program_info()` confirmed SLPM_862.19 SHA ea5a1668..., 1324 functions,
  reused GUI. `decompile_function_by_address(address="0x8002b5bc")` succeeded and
  gave the BAG2 dancer X formula (spacing*4*factor/256) and Y offsets.
- Reused, not rerun: native decompiles 801d5bb0 (smoke-lifecycle), 801d67a0
  (tank-lifecycle), 8002f7c0 (caught-actor-init), 8002de94 (tank-scale-load).
- Scratch: `_work/gaso/fall_contract.py` replays the fall integrator and writes
  `full-fidelity-source-audit/fall-contract.json`; payload SHAs asserted.
- Outcome: useful. +0x43cc is the rival spawn Y, not a scale. Drop 0x1000 and gravity
  32 are rival-independent; landing in 16 frames for dt 1 and 2. BAG2/native world
  ratio 520/784=0.663 from dancer separation. WIP drop 1200/12 frames contradicted.
  Limits: normal stage only, dt not measured, camera not compared. Time unmeasured.
   Next: CAUGHT selection per rival (pairs, BAG2-only), then particles and F3.

## 20261111-ghidra-056 — BAG2 hit selector and CAUGHT binding gap

- Purpose: approved F2 hit-reaction routing, bounded static research; no runtime edits.
  MCP `get_program_info()` succeeded, reused SLPM_862.19 Japanese PSX LE32 main,
  SHAea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe,1324functions.
  Fresh `read_memory(address="0x80051458",length=36)` returned
  ca01ca01ca00ca01ca01ca01cc00cb00c902ca01c800ca01ca01ca00c800cb00ca01c902.
- Earlier queries in this unit: sites8001fff8/8002005c resolved font-width code
  in FUN_8001ffbc, not
  reaction routing; decompile80035554 failed FUNCTION_NOT_FOUND (raw UI/rectangle
  argument pattern not a proven reaction issuer). Xrefs/callers to8002a090 were empty
  or FUNCTION_NOT_FOUND in this MCP database; table xrefs80051450/54/56/58/59 empty.
  The table-reference candidate80040bd0 is ISO9660/CdSearchFile, rejected. These
  negative main queries do not prove no caller exists in an overlay.
- Supplement: Capstone009 traces hashed JP005.dbi at8008f890, not MCP-loaded memory.
  `py -3.13 _work/gaso/audit_hit_selector.py` exit0; independent word decoding and
  full raw main/table SHA checks bind `hit-selector-contract.json` and verified.asm.
  Main SHA143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b;
  native JP SHAec7f4b0ef8c1823e86baa72bf5813e88c0a13e560f60adc5add6e7228bb66faf.
  Source role maps/policy hashes also recorded; legacy78←70 overridden by78←69
  for Heat/Strike/Gas-O; no alternate non-dance target for source70 in these maps.
- Outcome: useful. The selected source actor indexes80051458 at8009b5ac, pending
  request stored8009b5b4; Bi-O9=[202,1]. Consumer8009d0c0 dispatches then resets
  pending request. Other overlay branches explicitly issue123; no global78 change.
  Native GAS-O9 exception123→70 remains distinct. No proof of all reflection/guard
  branches, live ordering, pair/BAG2-only role equivalence or deployed clips.
- Time: consolidating audit0.012145s only; preceding exploration/manual rework and
  savings unmeasured. No new headless run; prior original/controller decompiles reused.
  Preflight20261111T110818458438Z passed0.714s, sources31match/resources no drift.
  Next: dedicated reversible CAUGHT clip binding, pair/stock skeleton adaptation,
  then remaining guards/restoration/particles. No runtime/gameplay acceptance.
- funcmatch.py not rerun: this is a verified JP overlay/table path, not a USA-main
  function-equivalence search supported by that experimental helper.

## 20261111-ghidra-057 — Actor clip tables and reversible binding constraints

- Purpose: approved F2, clip-table capacity and consumers before a dedicated CAUGHT
  binding. Ghidra12.1.4 running GUI reused; `get_program_info()` confirmed Japanese
  SLPM_862.19 PSX LE32 main,1324functions, SHA
  ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe. No restart.
- MCP `read_memory(address="0x8002d06c",length=32)` succeeded; bytes match the raw
  main independently. Existing253-line controller decompile read in full and reused.
  Fresh `decompile_function_by_address` queries succeeded at8002d85c,800319fc,
  800326d4,80031d3c,800125fc,8001262c,800126a4,8002ccc8,8002c404,8002c060,
  8002bc38 and800128b4. The2c404 read repeated an established renderer path to
  reach its pose consumer; no new scale finding claimed. No new headless run.
- Direct SW-immediate scan `py -3.13 _work/gaso/scan_clip_table_writers.py` found
  writes828/82c in319fc/31d3c/326d4. Nearest stack prologues were candidates, then
  confirmed by MCP decompiles; not an exhaustive alias/writer proof.
  An attempted read of bag2-caught-actor-init-decompile/8002d85c.c failed because
  that output does not exist; bounded filesystem search confirmed absence, then MCP
  supplied it. A tool-log read offset1120 exceeded1055lines; corrected to1022.
- Independent command `py -3.13 _work/gaso/audit_clip_table_contract.py` exit0,
  0.015301s, report full-fidelity-source-audit/clip-table-contract.json. Raw main SHA
  143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b;
  RAM SHAe272fae7241f8e9e5261ad9cbe335376dee959aef53d9616a775714d4f645a9f,
  metadata binds historical runtime27dfebb4, not current3145ba5b. All101 slots on
  each of Gas-O/Heat match raw-motion frames and metadata relocation. Table end
  equals actor+14, confirming packed reservation, not an available extra slot.
- Useful result: count820/raw824/lengths828/metadata82c; packed4N+2N+alignment+4N.
  Controller consumes old metadata before applying orders. Loader326d4 can share
  tables with a companion; decoder/pose cache and previous slot prevent a naive
  pointer-only restoration. Proposed privateN+1 tables need1020bytes atN101 plus
  clip/state, not an implemented allocation or proof of safe runtime scheduling.
- Limits: historical non-atomic initialized RAM, no pair actors measured; sharing
  branch proven statically only. No current payload/pose/skeleton/transaction test.
  Query/preparation/manual rework and savings unmeasured;0.015301s is audit only.
  Preflight20261111T110818458438Z reused: no source/resource/runtime changes here.
  funcmatch not applicable: actor field consumers, not a USA-main equivalent search.
- Next: converted native CAUGHT per current import/traje/lado and callback-safe
  entry/release seam; then pair/reflection/stock-skeleton adaptation and particles.
  No F2/F4 completion, deployment or gameplay acceptance from this documentary unit.

## 20261111-ghidra-058 — Existing empty animation slots, not assumed free

- Purpose: owner-approved audit of reusable entries for every character, instead of
  assuming that exact table allocation implies no existing holes. Static only.
- Fresh MCP `get_program_info()` confirmed existing SLPM_862.19 JP PSX LE32 main,
  SHAea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe;
  `read_memory(address="0x8005180c",length=248)` succeeded. No startup or overlay claim.
  Full returned248bytes independently match raw slpm.bin SHA
  143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b.
- Reused dispatcher8002a090 and role contract, not another decompile: Pander6 can
  select slot1 from nominal0/current0; request143 maps97/WIN4. Nominal request
  scans are not exhaustive reachability proofs, especially pairs/direct controllers.
- `py -3.13 _work/gaso/audit_reusable_slots.py` final exit0/0.095661s:
  reusable-slots.json covers72 stock lists and24 import-region lists; strict list
  bounds/terminator checks, frame-zero/empty distinctions and full-entry duplicates.
  Payload376287abd3ee2a13944deeafb0415da9b0f163a185dd3cad1540259596232f7e;
  hashed current source index/catalog and manifest offset checked against known layout.
  No claim that source index equals every live actor's compiled index.
- Scratch failures retained: first MCP hex transcription length assertion, then
  non-animation pack member misclassified by index kind; fixed by exact MCP bytes
  and catalog model-only selection. One corrective patch failed to match and made
  no change. Classifier first asserted wrong decompiler variable spelling; corrected
  after reading the exact Pander branch, not by relaxing the semantic condition.
- `py -3.13 _work/gaso/classify_reusable_slots.py` final exit0: inventory/source
  hashes and four variants checked; Pander1=56frames and Hiro97=218frames disprove
  a universal empty slot. Import Heat/Strike/Gas-O all have1/97 empty. Candidate1
  deserves bounded path checking; none is yet certified free. Extra stock holes and
  nominal requests are recorded separately. Pair/choreography tables may differ live.
- Outcome useful structural inventory and counterexamples, not runtime safety or
  all-character CAUGHT compatibility. Manual work/query time/savings unmeasured;
  0.095661s covers successful audit only. Preflight110818 reused unchanged.
  funcmatch omitted: slot/data audit, not USA-main equivalent search. Next: targeted
  slot1 controller/callback reachability for imports, reversible entry/release seam,
  then other profiles/partners and explicit BAG2-only skeleton adaptation.

## 20261111-ghidra-059 — Slot1 routes and combat-scoped reservation candidate

- Purpose: bounded existing-slot1 path audit for Heat/Strike/Gas-O, not another
  empty-list inventory or runtime modification. Reused running Ghidra12.1.4.
- Fresh MCP `get_program_info()` confirmed SLPM_862.19 JP PSX LE32 main SHA
  ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe.
  `read_memory(address="0x8002d06c",length=32)` matched raw target main SHA
  143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b.
  `decompile_function_by_address(address="0x8002cf44")` succeeded: timer-segment
  speed update, not a clip selector. `read_memory(address="0x800518ec",length=8)`
  returned56585a5d5d000000. `read_memory(address="0x80054fe4",length=152)` showed
  the per-side callback table; do not claim its handlers executed from that read.
- Reused full controller8002d06c, relevant dispatcher8002a090 and existing
  binding-0x8003190c.c (indirect character callback). Fresh MCP decompile319ac
  failed FUNCTION_NOT_FOUND; no offline result substituted as successful MCP.
- `py -3.13 _work/gaso/audit_slot1_routes.py` exit0/0.145204s, seven files:
  raw main plus six system DBIs, aligned literal J/JAL, function-pointer and
 154c/1550-store scan. Report slot1-routes.json preserves all input hashes/context.
  Main has seven controller calls inside dispatcher; three literal field stores.
 005 has dispatcher calls only;004 has direct controller calls file4b24/4c34
  with stack-loaded slot. No inferred004 base or proof of its argument values.
- `py -3.13 _work/gaso/audit_slot1_callbacks.py` exit0/0.198078s,72 stock character
  modules plus24 imported pack modules: no hits for those literal forms. Report
  slot1-callbacks.json hashes every module and imported member identity. DBI magic
  independently matched an archived Heat module; one DBI/member per imported pack
  asserted. Payload376287abd3ee2a13944deeafb0415da9b0f163a185dd3cad1540259596232f7e
  and source-index hash match trial058. No source-index/live-table equivalence claim.
- Independent struct opcode checks and MCP/raw byte comparison, not Capstone or
  a second headless pass. Literal scans can include data and miss aliases/computed
  offsets/indirect calls. Timer-table range beyond eight bytes not proven. funcmatch
  omitted: JP field/call audit, not a BAG1-USA/main function-equivalence search.
- Outcome: useful reduction of candidate routes, not proof slot1 globally free.
  Combat005-only actor/version-scoped loan and ownership-aware release are proposed
  requirements, not implemented behavior. No runtime/gameplay acceptance. Preflight
  20261111T110818458438Z reused with unchanged production inputs; manual time and
  savings unknown, reported seconds cover scripts only. Next: actual CAUGHT70 per
  import variant and host entry/yield/retirement seam; other profiles remain open.

## 20261111-ghidra-060 — Original CAUGHT variants versus imported models

- Purpose: verify source70 for Heat/Strike/Gas-O across costume, side and region,
  after bounded slot1 audit059. Reused running Ghidra12.1.4; no new capture/build.
- Fresh MCP `get_program_info()` confirmed SLPM_862.19 JP PSX LE32 main SHA
  ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe.
  `read_memory(address="0x800126a4",length=32)` returned
  1200c010213800000000828c000000000000438c000000000300601404008424,
  independently asserted against raw main SHA143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b.
  This verifies the metadata reader, not native overlay selection or live actors.
- Command `py -3.13 _work/gaso/audit_caught_variants.py`: first trial failed the
  assumption that target model parsing consumes its whole member (Heat). Diagnostic
  probes found Heat tails5112/4520bytes and an exact converted model prefix; the
  corrected audit requires exact native end and converted target prefix, retains
  target tails by hash, and separately reports full-member equality. No data deleted.
  Final trial exit0/0.20786s, report full-fidelity-source-audit/caught-variants.json.
- Inputs:24 native PLAYER2/PLAYER4 DFS from USA/JP full extracts; original source70;
 24 corresponding model containers in read-only deployed payload
  376287abd3ee2a13944deeafb0415da9b0f163a185dd3cad1540259596232f7e, current source
  index SHA c3ebf6898662b8d6a44fe3437c7b64454b476467befdd1d24069cbb2783e544f,
  and inventory058 SHA857e05e5e445450624719897de40844e4a5490d57194397895acaa64cccdf7b7.
  Report records every DFS/model/list/clip/tail and parsing-helper hash. Source index
  is not proof of current compiled index or all actor tables in RAM.
- Results: all24 parsed model prefixes match conversion; topology/transforms equal;
 16 complete model members equal (Strike/Gas-O), Heat appended bytes uninterpreted.
  CAUGHT has19tracks,2frames, no events, loop metadata byte5=0; one clip hash per
  character across eight variants. Heat/Gas-O static, Strike bone5 changes. Clip
  sizes348/352; scratch slot1 replacement grows lists344/348bytes, leaves the other
 100clips unchanged and reparses101entries. No package or asset written.
- Independent word-based metadata offset and source hash checks; codec round-trip
  is self-consistency, not independent runtime playback. Follow-up command
  `py -3.13 _work/gaso/check_caught_variant_result.py` passed all24 current source
  hashes, variant coverage, model flags, stream equality, loop and unchanged slots.
- Outcome: useful original-clip/model compatibility evidence for these imports,
  not entry/transition/decoder-retirement acceptance. funcmatch not applicable to
  this data audit. Preflight20261111T110818458438Z reused unchanged production
  inputs. Manual work/query time and savings unknown;0.20786s covers final script
  only. Next: host reservation entry/yield/retirement tests, then bounded integration;
  paired and BAG2-only rivals, particles and exact audio remain unresolved.

## 20261111-ghidra-061 — CAUGHT host decision seam, not guest integration

- Purpose: reuse the established JP controller contract for a bounded pure-policy
  implementation. Running Ghidra12.1.4 reused; no startup, headless or config edits.
- Exact MCP `get_program_info()` succeeded: SLPM_862.19 Japanese PSX LE32 main,
  SHAea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe,
  1324functions, entry80035d98. `read_memory(address="0x8002d06c",length=32)` returned
  c0ffbd272400b3af219880003400b7af3c00bfaf3800beaf3000b6af2c00b5af.
  Independent raw main SHA143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b
  and bytes match asserted by `_work/gaso/collect_caught_loan_evidence.py`.
- Reused prior controller/table/slot/24clip evidence, not fresh playback proof.
  Read failures: wrong `_work/gaso/clip-table-contract.json` path (correct directory
  full-fidelity-source-audit), log offset1210 past1207 corrected to its actual tail.
  No inference from either read failure. funcmatch not applicable: known JP contract,
  no BAG1 USA-main equivalent search. No Capstone or new decompile needed.
- Preflight `D:/Dev/Tools/ghidra-mcp-python/python.exe tools/workflow/bag2_workflow.py
  preflight --tag gaso-caught-loan-host` exit0/0.306s,20261111T120308686704Z:31sources
  matched before adding the unincluded host header. Not a post-staging/build check.
- Host commands/logs retained by `py -3.13 _work/gaso/run_caught_loan_tests.py <tag>
  [unittest args...]`: red8methods/25assertion failures12.991s; green8/8.427s;
  replay-red1assertion failure4.957s; verified19PASS13.949s (`-v tools.test.test_caught_loan
  tools.test.test_gaso_tank tools.test.test_bag1_dancer_scale`). Real C header with
  WSL Ubuntu gcc C11/Wall/Wextra/Werror, not a duplicate Python decision model.
- Full `discover -s tools/test -p test_*.py` verified-full exit1/33.910s:231tests,
  1failure31errors. All32names recorded in caught-loan-host-policy.json and full log;
  unchanged versus first same-session full run. Not a green suite or fresh runtime.
- Mutations: initial23/23; expanded run23/24 exposed a masked test gate, then newer
  B-hit regression produced24/24 in21.168s. Temporary headers only; source hashes
  and all unsuccessful/intermediate reports retained. Goldfish2reviewers found idle
  owner-reassignment replay; reproduced RED, fixed identity-pinning and expanded
  tests, final19PASS. Canonical topic note records CON HALLAZGOS, triaje and limits.
- Outcome: useful intermediate policy, no guest RAM reads/writes, clip publication,
  controller hook, decoder loop or deployment implemented. Safe-point/reference/
  exclusivity flags are trusted observations, not proved facts. Runtime acceptance
  and full F2-F8 remain open. Query/preparation/manual work/savings unmeasured;
  reported command times exclude those costs. Next: transactional guest adapter
  regression tests and actual safe-point proof, not another unchanged clip audit.

## 20261111-ghidra-062 — Paused byte-RAM CAUGHT transaction, controller still pending

- Purpose: next approved host adapter seam, reject partial table publication and
  preserve a legitimate replacement reaction; no game/runtime integration.
  Reused Ghidra12.1.4 GUI, no startup/config/headless/Capstone run required.
- Exact MCP `get_program_info()` confirmed SLPM_862.19 Japanese PSX LE32 main,
  SHAea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe;
  `read_memory(address="0x8002d4a0",length=64)` succeeded. Independent raw main
  SHA143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b
  matches all64bytes and SW8002d4b8 wordae08154c. Existing8002d06c decompile reused:
  old metadata/length processing precedes new slot. Not a proved callback-safe hook.
  `funcmatch.py` not applicable: no USA-main equivalent search in this byte-RAM seam.
- Preflight `bag2_workflow.py preflight --tag gaso-caught-binding-host`, verified
  Python environment, exit0/0.308s,20261111T123603008212Z,31sources matching/no drift.
  Before the unincluded new header; not build-tree staging or post-integration proof.
- New header is a stopped-VM byte-RAM transaction, not caller policy/controller.
  Four loaded-actor table spans, bounds, original/borrowed tuple and sampled refs
  are checked before ten bytes are written. Real generation/epoch/version, authentic
  clip, exclusive stop and quiescence remain caller obligations. Conservative
  foreign sharing rejection may reject companions; unlisted alias proof remains open.
- C11 gcc Wall/Wextra/Werror runner `_work/gaso/run_caught_loan_tests.py`: binding-red
  exit1/9.889s,4methods11assertion failures against reject stub; initial green16PASS.
  Goldfish alias RED exit1/3.363s; final binding-verified25PASS/22.215s. Full
  binding-current-full237tests exit1/42.624s,1failure31errors; all32names in
  caught-binding-host.json equal first same-session full235, no green suite claim.
- Mutation first16:15kills, RAW identity fixture masked by tuple guard; fixed fixture,
  retained failed report. Final16/16kills15.698s, temporary headers only.
  Own post-review ASAN test reproduced stack-buffer-overflow for absent owner plus
  four foreign actors; bounded inventory fix then51ASAN/UBSAN runs clean10.088s.
  All failed/intermediate logs retained; Goldfish two-reviewer findings/triage in
  canonical topic and `_work/goldfish/caught-binding-verdict.json`, no repeat review.
- Real-data host probe used immutable historical sign-intro-31 RAM SHA
  e272fae7241f8e9e5261ad9cbe335376dee959aef53d9616a775714d4f645a9f, runtime27dfebb4,
  and hashed348byte native Heat/Gas clips. Copied RAM plus synthetic scratch clip
  reservation; both N101 tables publish within ten bytes and restore exactly.
  Probe0.335639s excludes compile/prep; not a live allocation/stop/controller test.
- Outcome: useful tested publication/retirement primitive. No controller execution,
  safe-hook proof, policy composition/adoption, orphan teardown or runtime acceptance.
  Query/preparation/manual rework/savings unknown. Next: actual controller-safe
  boundary and composition, not repeat unchanged asset/slot audits. No game deployment.

## 20261111-ghidra-063 — Composed CAUGHT adapter verified in host, binary unchanged

- Purpose: close the two Goldfish reviews of the composed policy+transaction adapter
  (`b1ca_apply`) with real C tests; no game/runtime integration. One bounded MCP
  query reused the running CodeBrowser 12.1.4; no startup, configuration, headless
  or Capstone run.
- Fresh `get_program_info()` this unit still reports SLPM_862.19 Japanese PSX LE32
  main, SHA `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`,
  1324 functions, base 80000000. `read_memory(address="0x8002d4a0",length=64)`
  returned the identical sequence with SW `8002d4b8` = `ae08154c` already used by
  trials 047/056/062, matching the independent raw main SHA
  `143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b`. No new
  disassembly claim: the entry-tick order that the adapter encodes was proven by
  executing the original `FUN_8002d06c` on production sources (probe13), not by
  reading it again.
- `funcmatch.py` not applicable: this seam searches no USA-main function equivalent.
- Triage evidence, all host-only over 2 MB synthetic RAM: RED 45 cases, 38 real
  failures against a reject-only stub and 7 pure-refusal cases allowlisted with a
  written reason; GREEN 13/13 in 9.904 s; 42/42 mutants killed in 31.546 s across the
  three headers (occupied-slot guardian, binding/publication order, `committed`,
  identity, replay, poses A/B, exclusivity); 45 ASAN/UBSAN runs clean in 8.31 s;
  full suite 250 tests, 1 failure and 31 errors, the same 32 pre-existing names and
  none in `test_caught_*`. One equivalent mutant (`enter-binding-valid-gate`) is
  excluded and documented because the pure policy never decides ENTER while HELD.
- Both Goldfish verdicts were CON HALLAZGOS and their triage is recorded in
  `_work/goldfish/caught-adapter-verdict.json`. Findings 6 and 10 on
  `bag2jp_caught_binding.h` (span-only exclusivity comment, literal offsets) are
  recorded open rather than editing that header and invalidating the hashes
  verified in trial 062.
- Outcome: composed adapter host-proven but still included by no runtime `.c` and
  absent from `BAG2JP-codex-build`. No controller execution, safe hook, pause
  ownership, retargeting, particles, audio, build, deployment or in-game acceptance.
  Query/preparation/manual rework/savings unknown. Next: real hook integration and
  the 24-native-clip run, not another inventory of slots.

## 20261111-ghidra-064 — CAUGHT controller seam and request→slot tables

- Purpose: owner-chosen controller-hook path. `get_program_info()` SLPM_862.19, SHA
  ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe, 1324 functions.
- MCP: `get_xrefs_to` 8002d06c/8002a090 → 0 (no Ghidra functions there);
  `get_function_by_address` 8002ae60/8002b1e4 FUNCTION_NOT_FOUND; `list_functions`
  (1324); `read_memory` 8002ae60 (`1b b4 00 0c` = jal 8002d06c, matches raw main),
  8005180c(0x2b), 80051838(40), 80051859(0xef), no gaps.
- Finding: no table entry maps any mode-1 request to slot1 for IDs 0/1/9; delivery of
  slot1 through the pending request `+0x18` is impossible. Details:
  `notes/gaso-import.md` "seam real del controlador".
- Independent validation: Capstone listings of the raw main and 005.dbi (capstone-010).
  Outcome: a blocker found and a realizable seam identified; not runtime proof. Time,
  savings and manual rework not measured. Next: owner decision on the entry redirect.

## 2026-11-11 — clean-trace-mcp-20261111 — bounded controller identity/read

- Purpose/version: verify existing Ghidra 12.1.4 MCP session for the clean Gas-O controller trace; `get_program_info` confirmed main `SLPM_862.19`, NTSC-J PSX little-endian, entry `0x80035d98`, SHA-256 `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`. No new instance/configuration, analysis or guest writes.
- Actual queries: named decompile `FUN_8002a090` failed `FUNCTION_NOT_FOUND`; fallback bounded `read_memory(address="0x8002a090", length=64)` succeeded, main executable (not overlay). Returned bytes `28ffbd27c000b4af21a08000cc00b7af21b8a000b000b0af0680023c08f842240680033c6cf86324d400bfafd000beafc800b6afc400b5afbc00b3afb800b2af`.
- Independent validation/limit: prior controller decompilation `_work/gaso/bag2-caught-request-decompile/8002a090.c` is historical cross-reference only; no fresh independent raw-byte comparison in this trial. Outcome: identity and bounded read verified; named lookup failed, no new timing/routing conclusion. Preparation, execution, review time and savings unmeasured; manual rework unmeasured. Next: runtime request evidence, then address-based decompile if a specific controller ambiguity remains.

## 2026-11-11 — native-timing-contract: reloj, transferencia y duración005
- Pregunta/versión: Ghidra12.1.4, BAG1 JP native y BAG2 JP main/005; mismos hashes completos en `_work/gaso/native-timing-contract.json`. MCP `get_program_info()` primero: SLPM_862.19/NTSC-J, SHAea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe; `read_memory({address:"0x8002a0f0",length:112})` y `{address:"0x8002a1a0",length:96}`. Bytes idénticos a slpm.bin base80010000; son setup/reset, no atribuirles el decremento.
- Comandos exactos: `py -3.13 _work/gaso/trace_native_tank_main.py --follow-up --label native-caught-clock-writer --addresses 0x8001f32c`; igual con `--label native-caught-counter-transfer --addresses 0x8001ef9c`; `py -3.13 _work/gaso/trace_bag2_hit_duration.py`. Wrapper005 quita12B y carga8008f890; no modifica sesión GUI ni instala nada. TrialJSON conserva comandoheadless completo/hashes/salidas. Tiempos11.767s/7.888s/13.592s, exit0.
- Contraste independiente: instrucciones Capstone del original JP, inicialización3/transferencia ordenada/flag02;005 palabras b5b4=a6a20018,b5f0=24020003,c144=aea2001c y listas correspondientes. Semántica decompilada concuerda con estos caminos acotados; alineación temporal entre juegos y runtime no demostrados. `headroom peek.py` midió005C51117B/1357líneas; solo se leyeron fragmentos relevantes, no todo.
- Resultado Útil/buenos resultados en contratos estáticos delimitados. No acredita importación/fidelidad ni tiempos de juego. Preparación/revisión/retrabajo manual desconocidos; ahorro no medido. La lectura histórica80022430 fue irrelevante (fin de partida); no se repite. Siguiente: alineación de tablas/fase y residencia segura antes de escribir runtime.

## 2026-11-11 — sequence-residency: generador005 y decoder main
- Ghidra12.1.4; mismo nativeJP/mainJP/005 del ensayo native-timing-contract; hashes agrupados `_work/gaso/sequence-residency-contract.json` y `sequence-chart-audit.json`. MCP de esta sesión iniciado con get_program_info y bytes main contrastados según entrada anterior. Consultas nuevas exactas `decompile_function_by_address({address:"0x8002ccc8"})`, igual para80012a94/800128b4/800126f8: cuatro funciones correctas, sin truncado. Puntero raw cruza tabla824/root-motion/init/deltas sin máscara a mainRAM en esos caminos. No se llamó función guest ni escribió memoria.
- `py -3.13 _work/gaso/trace_bag2_sequence_generator.py`: payload005 verificado/c180916e…, proceso headless aislado ya existente, -process/-noanalysis/AnalyzeGasHooks.java800997ec, salida1548B/65líneas, exit0/7.343s. Hash/CLI completo en trialJSON. Genera432 entradas por redondeo entero, default phase5. Contraste: MIPS listado original, datos del convertidor/entry197 y cálculo independiente de321 entradas.
- Resultado Útil acotado: identifica fórmula y factibilidad estática del puntero. El test de arena/snapshots es independiente pero NO prueba decoder guest real. MCP/tiempo manual/retrabajo desconocidos; ahorro no medido. No aprobación/importación. Siguiente: acceso explícito a arena y decoder real antes del hook.


### owned-clip-decoder-mcp-20261111
Propósito: contrato de acceso a clip CAUGHT separado, BAG2 NTSC-J main SLPM_862.19, Ghidra 12.1.4/MCP existente. `get_program_info` primero: SHA `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`; `decompile_function_by_address` en `0x800126f8` (repetido para preparar firma exacta), `0x800128b4`, `0x80012a94`, completos/sin truncar. Confirma inicialización, delta, rewind y root-motion con punteros relativos, no prueba ejecución real ni seguridad de retiro. Contraste independiente Capstone5.0.7 de raw main `143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b` en `800126f8..80012ccc`: llamadas/init/rewind coinciden. Contraste adicional con el decoder MIPS original y bus/interpreter de producción: tres clips, frames 0/1/0/1, poses iguales en main y Expansion1; `_work/gaso/owned-decoder-probe10/trial.json`. No equivale a retiro/controller vivo. tiempo manual/ahorro desconocidos. Resultado útil para firma/ruta estática, no aceptación runtime.

## caught-entry-recovery-mcp-20261111 — 2026-11-11 UTC

- Tipo: uso real acotado; Ghidra 12.1.4/MCP existente, sin nueva instancia,
  escritura ni configuración. Main `SLPM_862.19`, NTSC-J, PSX LE32; no overlay.
- Consultas exactas: `get_program_info()` primero confirmó SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  `decompile_function_by_address({address:"0x8002d06c"})` falló
  `FUNCTION_NOT_FOUND`; `read_memory({address:"0x8002d06c",length:32})`
  devolvió sin gaps `c0ffbd272400b3af219880003400b7af3c00bfaf3800beaf3000b6af2c00b5af`.
- Contraste independiente: comparación determinista con `_work/mainexe/slpm.bin`,
  base `80010000`, SHA `143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b`;
  los 32 bytes coinciden. El contrato 202→89 procede de evidencia previa, no de
  estos 32 bytes. No se sustituyó silenciosamente un decompile inexistente.
- Dictamen: útil para identidad/acceso y verificación de entrada, no semántica
  nueva, quiescencia ni juego. Evidencia complementaria de cuarentena:
  `_work/gaso/caught-entry-recovery-report.json` y logs `entry-recovery-*`.
  Ejecución MCP/preparación/revisión/retrabajo y ahorro: no medidos.
- Siguiente: reutilizar identidad/bytes mientras no cambien inputs; implementar
  contrato de redirección seguro antes de build/despliegue, no repetir inventarios.

## caught-entry-contract-mcp-20261111 — 2026-11-11 UTC

- Propósito: confirmar binario y entrada para el contrato host `89→1`, no probar
  despacho real ni fidelidad. Instancia Ghidra 12.1.4/MCP existente, sin cambios.
- `get_program_info()` confirmó main JP `SLPM_862.19`, PSX LE32, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  `read_memory({address:"0x8002d06c",length:32})` devolvió sin gaps
  `c0ffbd272400b3af219880003400b7af3c00bfaf3800beaf3000b6af2c00b5af`.
  No se pidió decompile ni se cargó otro módulo en este ensayo.
- Contraste independiente determinista contra raw `slpm.bin`, base `80010000`,
  SHA `143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b`:
  32 bytes iguales; reporte `_work/gaso/caught-entry-contract-report.json`.
- Resultado: útil como identidad/lectura acotada; no descubre semántica nueva.
  La traducción 202→89 y disposición principal/compañero reutilizan investigación
  anterior. Los hechos de versión/procedencia/pausa siguen a cargo del llamador.
  Tiempo MCP/manual/retrabajo y ahorro desconocidos; no se infieren de tests.
- Siguiente: clips auténticos y observaciones del runtime; mantener callback
  inerte hasta verificar esas obligaciones. Sin build, deploy ni nueva partida.

## caught-clip-bank-mcp-20261111 — 2026-11-11 UTC

- Propósito: confirmar binario y acceso MCP a la entrada del decoder cuya evidencia
  anterior se reutiliza para la residencia del banco CAUGHT. Ghidra 12.1.4/MCP,
  instancia existente; main JP, sin cargar overlay ni modificar análisis/RAM.
- Consultas: `get_program_info()` confirmó `SLPM_862.19`, PSX LE32, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`;
  `read_memory({address:"0x800128b4",length:32})` devolvió sin gaps
  `e0ffbd271800b2af219080001400b1af1c00bfaf1000b0af0000428e2180c000`.
- Validación independiente: bytes idénticos al raw `_work/mainexe/slpm.bin`, base
  `80010000`, SHA `143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b`.
  Registro `_work/gaso/caught-clip-bank-report.json`. No decompile ni fallos MCP
  en este ensayo; no se repite el probe decoder previo con inputs sin cambios.
- Resultado útil para identidad/lectura acotada, no prueba nueva de semántica,
  temporización, ciclo runtime o fidelidad. Tiempo MCP/manual, retrabajo y ahorro
  desconocidos; los tiempos de tests no los sustituyen.
- Siguiente: conectar observaciones y ciclo real sin activar el callback hasta
  cerrar procedencia, exclusividad, retirada/reset/savestate y pruebas pertinentes.

## caught-dispatch-context-mcp-20261111 — 2026-11-11 UTC

- Propósito: confirmar el dispatcher main JP y su tabla/callsite al investigar
  observaciones CAUGHT. Ghidra 12.1.4/MCP, instancia existente; solo lectura,
  sin cargar overlay, cambiar análisis ni escribir RAM. `get_program_info()`:
  `SLPM_862.19`, PSX LE32, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
- Consultas `read_memory`, sin gaps:
  - `{address:"0x8002a090",length:32}`:
    `28ffbd27c000b4af21a08000cc00b7af21b8a000b000b0af0680023c08f84224`.
  - `{address:"0x8002ae50",length:24}`:
    `212080022128e002e400a78f213000021bb4000c1000b5af`.
  - `{address:"0x800518e4",length:16}`:
    `5557595b4700000056585a5d5d000000`.
- Validación independiente: tres lecturas iguales al raw `_work/mainexe/slpm.bin`,
  base `80010000`, SHA `143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b`.
  Registro `_work/gaso/caught-dispatch-context-report.json`; allí figuran también
  los ensayos separados del dispatcher/consumidor y sus límites. Overlay original
  `005.dbi` SHA `bc5f3045084e4b3e19009910441627977863c8b5791b5cdb716a766e68b28fb2`
  se leyó fuera de Ghidra, no se representa como módulo cargado aquí.
- Resultado útil para identidad y contraste de bytes, no prueba independiente
  de procedencia Gas-O, reflejos, generación, ciclo de vida o timing BAG1. No fallo
  MCP/decompile en este ensayo. Tiempo MCP/manual, retrabajo y ahorro desconocidos;
  3.557 s del probe de intérprete no mide esos conceptos.
- Siguiente: lector acotado y tests de observaciones con ABI confirmado, sin
  activar el hook antes de cerrar procedencia y ciclo de vida real.

## caught-context-reader-mcp-20261111 — 2026-11-11 UTC

- Uso real acotado: Ghidra 12.1.4/MCP, instancia existente, main JP
  `SLPM_862.19`, PSX LE32. `get_program_info()` confirmó SHA
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  `read_memory({address:"0x8002ae50",length:24})` devolvió sin gaps
  `212080022128e002e400a78f213000021bb4000c1000b5af`.
- Contraste independiente: mismos 24 bytes en `_work/mainexe/slpm.bin`, base
  `80010000`, SHA `143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b`.
  Evidencia `_work/gaso/caught-context-reader-report.json`. Reutiliza el ensayo
  anterior para semántica del dispatcher; esta lectura no vuelve a probarla.
- Resultado útil para confirmar identidad y bytes del callsite al escribir el
  lector. No se escribió ni modificó análisis; no overlay cargado ni decompile
  intentado en este ensayo, sin fallo MCP. No demuestra atacante, versión,
  exclusión de reflejos, generación, ciclo de vida o aceptación en juego.
- Medición MCP, preparación/revisión/retrabajo y referencia comparable:
  desconocidos; ahorro no medido. Siguiente: reutilizar identidad/callsite y
  mantener separado el contexto de llamada de la autorización del ataque.

## caught-hit-provenance-mcp-20261111 — 2026-11-11 UTC

- Propósito: contrastar la tabla de petición/auxiliar por personaje al investigar
  origen y reflejos. Ghidra 12.1.4/MCP, instancia conservada; primero
  `get_program_info()` confirmó `SLPM_862.19`, JP main PSX LE32, SHA
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
- `read_memory({address:"0x80051458",length:36})`, sin gaps:
  `ca01ca01ca00ca01ca01ca01cc00cb00c902ca01c800ca01ca01ca00c800cb00ca01c902`.
  Misma tabla en raw `_work/mainexe/slpm.bin`, base `80010000`, SHA
  `143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b`;
  contraste independiente en `_work/gaso/caught-hit-provenance-report.json`.
- Resultado útil: identidad y tabla verificadas, confirma petición compartida
  por varios IDs. El overlay original `005` no está cargado en este programa;
  sus spans se ejecutaron por separado con el intérprete productivo y fuente
  SHA `bc5f3045…`. La lectura MCP no demuestra esa semántica ni aceptación.
- Sin fallo MCP, decompile, escritura o cambio de análisis en este ensayo.
  Tiempo/manual rework y ahorro de MCP desconocidos; los 4.000 s de probe no
  son medida de ahorro. Siguiente: conservar procedencia real antes del borrado,
  sin equiparar contexto o petición 202 a autorización de CAUGHT.

## caught-p0-inert-mcp-20261112 — 2026-11-12 UTC

- Propósito: confirmar programa y punto de entrada antes de neutralizar el
  runtime CAUGHT (P0). Ghidra 12.1.4/MCP, instancia existente reutilizada.
- `get_program_info()`: `SLPM_862.19`, PSX LE32, SHA
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`, 1324
  funciones. `read_memory({address:"0x8002d06c",length:16})` =
  `c0ffbd27 2400b3af 21988000 3400b7af` (`addiu sp,sp,-0x40` + guardados);
  `get_xrefs_to("0x8002d06c")` = 0 (sin función definida; entrada indirecta).
- Validación independiente: no hacía falta otra; coincide con el contrato ya
  registrado en `caught-entry-contract-mcp-20261111`. No se repitieron probes.
- Resultado: útil como identidad y guardia; no aporta semántica nueva. La
  conclusión de inercia del despliegue sale de la fuente del runtime
  (`mod_runtime.cpp:368-394`), no de Ghidra. Sin fallos ni escrituras MCP.
  Tiempo y ahorro desconocidos. Siguiente: ninguno para P0.

## caught-observe-stack-mcp-20261112 - 2026-11-12 UTC

- Propósito: identidad y lectura acotada obligatorias al reanudar la corrección
  del filtro de pila de CAUGHT. Ghidra 12.1.4/MCP, instancia existente.
- `get_program_info()` confirmó `SLPM_862.19`, JP, PSX LE32, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`,
  base `80000000`, entrada `80035d98`. `read_memory(address="0x8002d06c",
  length=16)` devolvió `c0 ff bd 27 24 00 b3 af 21 98 80 00 34 00 b7 af`, sin
  huecos. Región: entrada del controlador en el ejecutable principal; no prueba
  de overlay cargado. Sin escrituras ni fallos MCP.
- Validación independiente: bytes iguales al registro P0 anterior; no se repitió
  el análisis del contrato. Resultado: confirmación redundante de identidad
  exigida por el flujo, no evidencia de la geometría de RAM en ejecución.
  Tiempo, ahorro y retrabajo no medidos. Siguiente: verificar el filtro con
  regresión de geometría y partida experimental, no con otro probe idéntico.

## caught-p2-research-mcp-20261112 - 2026-11-12 UTC

- Propósito: identidad y lectura acotada obligatorias antes de investigar P2;
  instancia Ghidra 12.1.4/MCP existente, sin escrituras ni arranque duplicado.
- `get_program_info()` confirmó `SLPM_862.19`, JP, PSX LE32, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`,
  base `80000000`, entrada `80035d98`. `read_memory(address="0x8002d06c",
  length=16)` devolvió `c0 ff bd 27 24 00 b3 af 21 98 80 00 34 00 b7 af`, sin
  huecos; región: main, entrada de controlador. No prueba de overlay cargado.
- Validación independiente: comparación con los bytes registrados en
  `caught-observe-stack-mcp-20261112`. Resultado: confirmación redundante exigida
  por el flujo, no semántica nueva de lifecycle o de selección del banco. Sin
  fallos MCP. Tiempo/retrabajo/ahorro desconocidos. Siguiente: reutilizar el
  contrato conocido; la carencia de generación debe investigarse en su cargador.

## caught-p2a-mcp-20261112 - 2026-11-12 UTC

- Propósito: confirmar identidad y lectura acotada obligatorias antes de P2a,
  mediante la instancia Ghidra 12.1.4/MCP existente.
- `get_program_info()` confirmó `SLPM_862.19`, JP, PSX LE32, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`,
  base `80000000`, entrada `80035d98`. `read_memory(address="0x8002d06c",
  length=16)` devolvió `c0 ff bd 27 24 00 b3 af 21 98 80 00 34 00 b7 af`,
  sin huecos; ejecutable principal, entrada de controlador, no overlay cargado.
- Validación independiente: bytes iguales al registro `caught-p2-research-mcp-20261112`.
  Resultado redundante exigido por el flujo; no demuestra selección ni lifetime.
  Sin fallos MCP, escrituras o cambios de sesión. Tiempo/retrabajo/ahorro no
  medidos. Siguiente: probar la consulta del banco en host y exp-8mb sin publicar.

## caught-p2b-generation-20261112 - 2026-11-12 UTC

- Propósito: identificar el evento de recarga por combate y el reinicio del
  `+0x18` pendiente, para fijar la invalidación de `captured[]`, sin escribir
  guest ni publicar. Ghidra 12.1.4/MCP, instancia existente.
- `get_program_info()` confirmó `SLPM_862.19`, JP, PSX LE32, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`,
  base `80000000`, entrada `0x80035d98`. Sin fallos MCP.
- Consultas acotadas: `get_function_by_address(0x8001e0f4)`/`(0x8001e938)`,
  `decompile_function(FUN_8001e744)` (resetea `DAT_8005d3dc=0`),
  `decompile_function(FUN_8001e0f4)` (máquina de fases 0→1→2→3→0 y fase 3
  reinicializa cuatro parejas controlador/actor), `disassemble_function(main)`
  (bss `DAT_8005d3dc=0` en `0x8001ea40`), referencias a `0x8005f808`
  (26 usos: actor fijo `0x800ddb18`/`0x80154db4` y acompañantes `+0x1728`),
  y `FUN_8002b5bc`/`FUN_8002d85c`/`FUN_80034210`/`FUN_800342dc` ya
  resumidos en la nota. Productor `0x8009b5b4` y entrada `0x8002d06c` no son
  funciones definidas (overlay 005), por lo que el anclaje fue sobre estructuras.
- Validación independiente: la decompilación de `FUN_8001e0f4` muestra la
  asignación explícita `+0x18=-1` en `FUN_8002d85c` y `actor+4=0xff` en
  `FUN_80034210`; `FUN_800342dc(1)` gobierna el paso a fase 3. No se repitió
  el probe de partida ni se invocaron herramientas irrelevantes.
- Resultado: contrato de generación definido como evento de fase 3, no como
  identidad de puntero ni como `generation=1/tick=0`. Sin escrituras ni
  cambios de sesión. Tiempo/retrabajo/ahorro no medidos. Siguiente: P3
  (ciclo de vida, reset, savestate, invalidación) sin publicar.

## caught-p3-lifecycle-20261112 - 2026-11-12 UTC

- Propósito: registrar callbacks de ciclo de vida (session_reset, savestate)
  para invalidar captured[] tras reset/load, sin escribir guest ni publicar.
  Análisis estático de mod_plugins.h y mod_runtime.cpp en el build tree;
  no se usaron consultas de memoria Ghidra para este paso.
- Framework API leído:
  - psx_mod_register_session_reset_plugin (mod_plugins.h:39-40): limpieza host
    antes de activar cada plan, emulación detenida, sin contexto de feature/
    recurso, nunca mutar estado guest.
  - psx_mod_register_savestate_plugin (mod_plugins.h:46-47): después de
    restaurar estado guest, antes de reanudar el PC; rebindar hooks, no avanzar
    juego.
  - mod_reset_plugin_sessions() (mod_packages.cpp:1518-1520): itera todos los
    plugins registrados e invoca su callback session_reset. Llamado en
    mod_runtime.cpp:1764 y 3166.
  - mod_invoke_savestate_plugin(plugin.id) (mod_runtime.cpp:2794): invocado
    para cada plugin del plan después de restaurar savestate.
- Implementación en
  mods-src/bag2jp.feature.bag1-content/bag2jp_gaso_caught.c:
  gaso_caught_session_reset() y gaso_caught_savestate() ponen
  captured[].available = 0 en ambos lados; ambos registrados en
  PSX_MOD_CONSTRUCTOR. Sin escrituras guest, sin asignaciones, sin publicación.
  CLIP_PUBLISHED=0.
- Prueba host: escenario 10 del harness (reset_and_savestate_invalidate_captured)
  verifica invalidación sin writes/alloc y que enter() no consume tras invalidar.
- Resultado: P3 callbacks implementados y verificados en host. Siguiente: estudio
  de publica/restore quiescente con guard, sujeto a aprobación del propietario.
  Tiempo/retrabajo/ahorro no medidos.

## caught-retire-contract-20261112 - 2026-11-12 UTC
- Use: Ghidra 12.1.4 MCP, `SLPM_862.19` sha256 `ea5a1668…851efe` (reopened this session with `ghidraRun.bat` + `BAG2JP.gpr`; Tip dialog closed via `_work/click.ps1`). Queries: `get_program_info`; `read_memory` 0x8002d4b8 (`4c 15 08 ae`) and 0x8002d6cc (`50 15 02 ae`); `get_xrefs_to` 0x8005f808/80c/810/814; `get_function_by_address` over 130 capstone hits; `disassemble_function` 0x8002bc38 (offset 10, 34 lines).
- Result: retirement points confirmed (current=a2 at 0x8002d4b8, previous=current at 0x8002d6cc). Static xrefs did not resolve 0x8005f80c/814 contents (RAM dump did). The 130 slot-table accesses group into 13 named functions plus the undefined controller region; FUN_8002bc38 reads previous only to compare with current. Useful: refuted Goldfish S2 for direct table reads. Limit: cached clip pointers elsewhere not proven absent.
- Time: about 10 min including restart; savings not measured. Next: reuse these addresses unless the main executable hash changes.

## 2026-11-12 - caught-active-reuse: contraste del retiro al revisar evidencia

- MCP `get_program_info()` confirmó `SLPM_862.19`, JP main,
  SHA `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`;
  `read_memory(0x8002d6cc,4)` devuelve `50 15 02 ae`, sin gaps:
  previous=current al salir. Instancia existente, sin arranque/configuración nuevos.
- Útil acotado: se mantiene el límite de retiro; el fallo del segundo golpe se
  localizó en el contrato host (VERIFY aplicaba reposo), no en esos bytes MIPS.
  Contraste independiente: trace gf8088 anim1/gf8292 anim89 y regresión host RED.
- Tiempo/manual/ahorro no medidos. Corrige la estimación temporal «about10min»
  anterior: no hubo cronometraje que la acreditara. Siguiente: reutilizar bytes
  mientras no cambie el ejecutable; no hace falta otra consulta idéntica.

## 2026-11-12 - caught-tank-timing: región y límite de procedencia

- Instancia existente Ghidra12.1.4; MCP get_program_info confirmó SLPM_862.19,
  main JP SHA256 ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe.
  Consultas anteriores de este ensayo: xrefs a 80087992/8798e/879a2/879a6
  vacíos; 8005cf24 tiene WRITE8001e47c en FUN_8001e0f4 (inicialización,
  no demuestra productor runtime). Decompile8001e0f4; segmentos y consulta
  de función/memoria8009b5b4 no demostraron overlay005 cargado.
- Hallazgo útil: los decompiles históricos8001e030/8001f6a0 son BAG1 JP,
  no funciones equivalentes de BAG2. Contraste con procedencia en gaso-import
  y función BAG2 contenedora FUN_8001f560. No reutilizar sus globals como BAG2.
- Al retomar: get_program_info() seguido de read_memory(8002d4b8,8) devolvió
  `4c 15 08 ae 1c 00 7e ae`, sin gaps: store slot actual actor+154c, consistente
  con el consumidor del visual. No se modificó proyecto/análisis ni abrió otra
  instancia. No identifica flag/counter de trap en overlay ni autoriza constantes.
- Resultado útil acotado para identidad/región y descarte de procedencia falsa;
  timer nativo y estrellas pendientes. Tiempo/manual/ahorro no medidos.
  Próximo: analizar overlay005 conservando el main y contrastar con trace.

## 2026-11-12 - caught-tank-state: palabra de slot y límite de análisis

- Ghidra12.1.4 MCP get_program_info confirmó instancia existente SLPM_862.19
  JP main, SHA256 ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe.
  `decompile_function_by_address(8002d06c)` devolvió FUNCTION_NOT_FOUND;
  no se creó función ni se alteró análisis para ocultar el fallo.
- Consulta acotada alternativa MCP `read_memory(8002d4a0,48)` sin gaps:
  el word8002d4b8 sigue `4c 15 08 ae` (store slot actor+154c).
  Contraste independiente: comentario existente de retiro en gaso_caught y
  trace histórico gaso-topmost-reuse-heat-bag1 observa P1 anim74 -> anim6 ->
  anim74. Justifica observar cambios de slot, no inferirlos comparando el reloj
  de animación con la edad del tanque. No acredita por sí solo fidelidad nativa
  del umbral38 ni detecta reinicios74->74 entre dos muestras.
- Resultado útil acotado/parte decompile bloqueada. Sin cambios a Ghidra,
  instalación, runtime ni partida; tiempo/manual/ahorro no medidos. Próximo:
  reutilizar identidad/bytes con el mismo main, investigar005 para estrellas.

## 2026-11-12 - caught-secondary-effect: selector paralelo al motion

- Instancia existente Ghidra12.1.4, MCP get_program_info SLPM_862.19 JP main
  SHA ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe.
  read_memory518e4/16,51458/32,19d70/32,19e34/32 sin gaps; comparación raw
  independiente en `_work/gaso/stars-research-report.json` (4/4 iguales).
- `decompile_function_by_address(80019d70)` falló FUNCTION_NOT_FOUND;
  get_function_by_address(80019e30) también falló (dirección del delay-slot de
  retorno, no inicio). get_function_by_address(80019888) encontró196d4;
  decompile196d4 pasó pero es otro efecto, irrelevante al selector1. Se conservó
  análisis/sesión; no se crearon funciones en GUI ni se cambió región.
- Complemento aislado, no sustitución MCP: `py -3.13
  _work/gaso/trace_bag2_caught.py --follow-up --label <label> --addresses <addr>`
  con bag2-hit-secondary-effect/80019d70 (13,848s),
  bag2-hit-secondary-stars/8001a8fc (7,773s),
  bag2-hit-secondary-update/80019e34 (7,798s),
  bag2-hit-star-particles/8001ab8c (7,739s), todos exit0. Ghidra headless usa
  proyecto task-owned gaso-runtime-hooks/slpm.bin, raw main SHA143b4bf8… base
  80010000; comandos completos y hashes en <label>-trial.json y reporte agregado.
  El campo heredado mcp_matched_address del wrapper dice2d06c: NO es la consulta
  nueva de este ensayo; las cuatro comprobaciones nuevas están en el agregado.
- Hecho estático: tabla atacante[9]=202,1; 0058009b5d0 lee la segunda columna,
  b5e4 llama19d70(rival,1), b5e8 es delay-slot `move a1,s0`. Selector actor+1724
  despacha init1a8fc y update1ab8c:8 partículas, separado de slot de motion.
  Reutilizado005bc5f3045… payload+12/base8008f890 y decompile99e90 anterior:
  no se repitió. Slot89/90 y timer de202 corroborados con tabla MCP/historial.
- Resultado útil estático; identidad de bitmap visible de estrellas y orden
  live no demostrados. No parche/guest write/build/deploy/partida. Tiempo manual
  y ahorro desconocidos. Próximo: probar identidad de sprite/supresión acotada
  a publicación propia; no desactivar selector1 global ni cambiar salida90.

## 2026-11-12 - caught-secondary-suppression: sprite y propiedad

- MCP get_program_info confirmó de nuevo SLPM_862.19 JP main SHAea5a1668…;
  consultas pertinentes nuevas get_xrefs_to80054c88 (10READ, sin writers) y
  80054c52 (14READ),54c50 (0). No interpretarlas como ausencia de loader:
  puede escribir el descriptor indirectamente. read_memory54c50/64 muestra
  campos inicialmente cero; NO representa la VRAM de una partida activa.
- read_memory8004e3c0/64 confirma tabla deUV40,56 y56,56 para partículas pares
  y ciclo de paletas8,9,10,11,10,9 para impares. Se reutilizó decompile1ab8c
  previo (sin otro headless): sprite impar UV72,56/16x16.
- Contraste independiente con assets/archive/system/010/001.tim: TIM4bpp,
  origen512,256 -> baseUV0,0,256x256,16 filasCLUT. Bitmap recortado desde bytes
  originales y paletas8..11 muestra estrella naranja/roja; SHA2560039c3d3…,
  SHA1 coincide con _container; PNG histórico también coincide con _png_sha1.
  `_work/gaso/secondary-star-identity.json` conserva100 píxeles no cero,
  hashes/crop/CLUT. No es captura live ni prueba del descriptor actual54c50.
- Útil para identidad del asset y alcance del canal (también cue0x0e).
  Sin modificaciones de Ghidra/runtime; tiempo/manual/ahorro no medidos.
  Próximo: regresiones host de supresión posterior a propiedad verificada y
  después validar audiovisual real; no afirmar que MCP validó la partida.

## 2026-11-13 - caught-tank-liquid: verificación MCP y decompiles reutilizados

- MCP `get_program_info`: `SLPM_862.19`, SHA `ea5a166863f1…`, 1324 funciones. Responde.
- El render nativo del tanque es del main/overlay BAG1 JP, que no está en esta sesión MCP. Se reutilizaron
  los decompiles contrastados `_work/gaso/native-tank-primitives-decompile/` (8002becc, 8002c430, 8002d3e0,
  8002cf6c, 8002d020: NCLIP y descarte <=0) y la nota F2 (cilindro 0x3A + E1000600, metal 0x38, tapa 0x30).
  No se repitió la extracción: entradas sin cambios.
- Resultado: útil (fijó culling, modo de mezcla y opacidad del metal). Sin modificaciones en Ghidra.
  Límite: iluminación GTE (8002bbe8) no reproducida, solo aproximada.

## 2026-11-13 - liquid7: cámara y deformación de burbujas

- Propósito: contrastar la proyección del anillo ovalado sin modificar el juego.
  Ghidra12.1.4/MCP, main JP `SLPM_862.19`, SHA256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`;
  `get_program_info()` antes de las lecturas, sesión existente reutilizada.
- Consultas exactas: `get_xrefs_to(address="0x8005d0f0",offset=0,limit=30)`:
  12 referencias, sin más páginas. `decompile_function_by_address` de
  8002c338,800198b8,80019e34,80019c38,8002dcf8 (última resuelve a8002dc9c).
  Consumidores confirman CompMatrix cámara×actor; no son escritores que
  demuestren escala/aspecto efectivos.8002dc9c fija offset256,120 y H0x180.
- Validación independiente: helper C `strike_project` aplica0,85 enX y los
  paquetes reales del host miden18×22; log de partida liquid7 dice aspecto16:9,
  y gpu_gl_renderer.c5921 explica el stretched present. Prototipo aislado
  `bubble-aspect-host.json` aproxima circunferencia bajo supuestos explícitos.
- Resultado: parcialmente útil; descartó asumir que un consumidor escribe la
  matriz y confirmó offset/H, **no** resolvió cómo consultar aspecto efectivo.
  Sin cambios en análisis/proyecto. Tiempo manual/ahorro no medidos. Próximo:
  contrato de aspecto; no repetir estas consultas sin nueva evidencia.

## 2026-11-13 - liquid8 candidate: contrato de aspecto y enlace sin partida

- Propósito: continuar radio dinámico sin confundir estado host con GTE MIPS.
  Ghidra12.1.4/MCP, sesión existente; get_program_info confirmó main JP
  SLPM_862.19 SHAea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe.
  Consulta acotada `decompile_function_by_address(address="0x8002dc9c")`:
  offset256,120 y H0x180, coherentes con la evidencia previa; sin cambios de análisis.
- La API necesaria no pertenece al MIPS original. Productor real leído en
  framework pin1a3fc0db303a: view_x_margin solo native-wide2, no squash1;
  display_info y clasificador alimentan extensión read-only guardada como parche
  `patches/psxrecomp-display-pixel-aspect.patch`, SHA0a25564a…; no función BAG1
  equivalente a buscar con funcmatch. No se vuelve a decompilar el render nativo.
- Validación independiente: RED/GREEN host49 tests,18 casos de API, patch replay,
  build Windows135s y llvm-nm confirma referencia desde plugin/definición en exe.
  Ghidra útil para encuadrar H/offset, no demuestra presentación host ni fidelidad.
  Sin partida nueva; FFmpeg/grabación omitidos hasta autorización. Tiempo de
  Ghidra/manual/ahorro no medido. Siguiente: autorización y comparación grabada.

## 2026-11-13 - bubble-aspect: despliegue autorizado y correlación de grabación

- Ghidra12.1.4/MCP existente: get_program_info confirma SLPM_862.19/main JP,
  SHAea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe;
  get_function_by_address(address="0x8002c404") → cuerpo8002c404..8002ccc7.
  Se reutiliza decompile previo (cámara×dancer), no cambia código MIPS/análisis.
- Propósito: fijar seam de proyección y revisar ataques en logs de runtime
  752e21f0. Spawn/corte gf7190/7329 y retiro después de slot1gf7611; grabador
  ubica vídeo, inspección independiente ve caída2,862 y cortes5,195/10,033s.
- Resultado: útil como identidad/seam, no mide por sí solo el aspecto host.
  Frames llegan~3-4 después de etiquetas en fronteras: latencia sin calibrar.
  Sin nuevas modificaciones de funciones. Tiempo/manual/ahorro no medidos;
  revisar tema y toma aceptada16:9, no repetir análisis MIPS sin cambio.

## 2026-11-13 deslizamiento del rival atrapado

- MCP SLPM_862.19 (ea5a1668…): `FUN_80012a94`, xrefs (caller único
  `FUN_8002ccc8`), `FUN_8002c404` (despacho por estado `+4`) y
  `list_functions`. Hueco sin función en 0x8002a090..0x8002b5bc; se completó
  con capstone.
- Resultado: útil como mapa (re-anclaje de la base y despacho por estado). No
  prueba por sí solo la causa en tiempo de ejecución. Sin renombres ni
  modificaciones.

## 2026-11-13 candidato hold: verificación MCP al retomar

- `get_program_info` → SLPM_862.19 JP, SHA256 ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe.
  `decompile_function_by_address(0x8002ccc8)` confirma base X/Z = raíz menos
  traslación/2 cuando actor+3 es distinto de cero. Sin cambios al proyecto.
- Contraste independiente: watch del diagnóstico f7593..8008 y toma aceptada
  del hold f7245..7663. El primer análisis confundía reloj de canción y frame
  global: se corrige en notes/gaso-import.md, no se reutiliza esa atribución.
- Útil para localizar seam nativo; no prueba por sí solo orden de vblank/render.
  Tiempo/ahorro desconocidos. Próximo: evitar mezcla residual, no repetir lectura
  inalterada sin nueva pregunta.

## 2026-11-13 clamp nativo CAUGHT

- MCP get_program_info: SLPM_862.19/ea5a1668. Decompile8002d06c falló
  FUNCTION_NOT_FOUND; read_memory(8002d06c,32) coincidió con trial histórico
  (raw143b4bf8). Decompile headless existente reutilizado; instancia intacta.
- Byte5 gobierna clamp/wrap; byte4 detecta vuelta. MIPS original/intérprete:
  101→1 reanclajes/200ticks, re-hit añade1; callees observados, no ejecutados.
  Toma aceptada confirma no oscilación periódica, pero re-hit(-4,+3) pendiente.
  Útil; tiempo/ahorro desconocidos. Próximo: contrato de reentrada y timers.

## 2026-11-13 reentrada CAUGHT: efectos exclusivos de modo1

- Propósito: saber qué omite pasar de modo1(entrada) a modo0(avance) en
  `FUN_8002d06c` y si esos efectos son inocuos para una pose ya asentada.
- Consultas MCP (programa SLPM_862.19/ea5a1668, sin escrituras ni reinicio):
  `decompile_function_by_address(0x8003190c)`, `decompile_function_by_address
  (0x8002ccc8)`, `decompile_function_by_address(0x80012a94)`,
  `decompile_function_by_address(0x8002cd48)`, `read_memory(0x80054fe4,80)` y
  `read_memory(0x80055030,80)`.
- Evidencia: 3190c despacha callbacks de personaje por byte+4/byte+5;
  8002ccc8 fija `+0x14b8/+0x14c0 = +0x810/+0x818 - traslación de raíz` (solo
  lee 0x810); 80012a94 evalúa la raíz del clip y no escribe posición; 8002cd48
  limita la distancia ancla-base y solo escribe el ancla. Modo1 (líneas
  125-207) además limpia +0x0a/+0x0b, copia param5 en +0x1c/+0x20 y el frame
  en +0x24, y llama a 3190c solo si controlador+0x0d==0.
- Límite: 3190c apunta a tablas por lado cuyo handler del lado2 vive en overlay
  no cargado en Ghidra (0x801d66e4 sin inicializar); no se ejecutó ningún
  callback ni callee de render.
- Resultado: útil para acotar las guardas del candidato modo0. Tiempo/ahorro
  desconocidos. Próximo: observar controlador +0x0a/+0x0b/+0x20/+0x24 en la
  próxima toma; no repetir el decompile sin una pregunta nueva.


## 2026-11-13 correccion de +0x24 en la guarda de reentrada

- Relectura del bloque param_2 != 0 en `FUN_8002d06c` (lineas 176-199): modo1 fija
  `pcVar8[0x1554]=0` (frame) y luego `param_1[9]=*(pcVar8+0x1554)` (linea 199), es
  decir +24=0, no 1. La guarda inicial (`== GASO_CAUGHT_LAST_FRAME`, 1) era falsa
  y habria dejado la conversion inerte. Corregida a `GASO_CAUGHT_ENTRY_FRAME_COPY` (0).
- Evidencia independiente: `8002d06c.asm:399` (`sw $v0,0x24($s3)`) es la unica
  escritura de +0x24 en esa funcion; no hay otro writer en el mismo bloque.
- Residuales declarados tras la correccion: modo0 tampoco reinicia +0x10 (linea 184)
  ni +0x20 (linea 128), ni ejecuta los callbacks 8003190c (lineas 131-167).

## 20261113-ghidra-hud — nombre del marcador Gas-O, candidato offline

- MCP get_program_info confirmó SLPM_862.19/main JP, SHA
  ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe.
  decompile_function_by_address(80032270) devolvió el contenedor80031d3c
  (carga texturas/modelos, no consumidor HUD). get_xrefs_to(80054c88)
  encontró lectores8001ab8c/8001a0a4; decompile8001a0a4 confirma uso de CLUT
  compartida, sin demostrar su contenido. get_xrefs_to(80054c40) no dio refs:
  negativo inconcluso, no prueba de ausencia de writer.
- Complemento headless12.255s, exit0: `py -3.13 _work/gaso/hud/trace_hud.py`,
  procesa solo programa aislado bag2-combat005-duration-payload.bin, sin tocar
  sesión GUI. Región JP/overlay005 SHA bc5f3045084e4b3e19009910441627977863c8b5791b5cdb716a766e68b28fb2,
  payload8008f890 tras12bytes. Export FUN80093de0 y comandos/hashes exactos
  en `_work/gaso/hud/descriptor-{decompile,trial.json,headless.log}`.
- Contraste independiente: descriptores originales a offsets ee52/eebe,
  bytes20702d070100, y tests de salida del constructor18DFS. Consumidor usa
  char*6+costume*0x6c, textura u16+4 y UV/width/height del registro.
- Goldfish2 revisores: MCP de ambos identificó main; una consulta a80093de0
  falló FUNCTION_NOT_FOUND y otra lectura dio memoria no inicializada (overlay
  no residente en ese programa). No se presenta como consulta MCP del overlay.
- Resultado útil para recuadro, no para CLUT efectiva ni visibilidad. Falta
  contraste del orden RGB del CLUT compartido. Tiempo total/manual/ahorro no
  medidos; no nueva partida. Siguiente: conservar límite en candidato B.

### Consultas de audio previas del mismo bloque, todavía WIP

- Mismo main JP/MCP: decompile8003190c mostró dispatcher por char+side,
  read_memory80054fe4,length160 devolvió tabla de handlers de overlay.
  decompile8002e478 y8002e2d0 confirmó wrapper con slot libre y tabla6*u16
  buscada por cue, retorno-1 si no existe. No se leyó un handler overlay cargado.
- Contraste con8002d06c exportado:779/782 son eventos para receptor char9,
  no identidad del sonido perdido con Heat. El handler Heat recibe1/4/12d/3e9.
  Atribución anterior a cue782 retirada en el ledger/estado; falta identificar
  el sonido real. Referencias nativas headless801d6480/666c/7218 reutilizadas,
  no consultas MCP nuevas de BAG1. Cola de audio candidata sin aceptación.
- Resultado útil para API/evitar una atribución falsa; tiempo/manual/ahorro
  desconocidos. Próximo A: verificar pulso/onset/banco real y Goldfish,
  sin presentar el build872e6753 como sonido correcto.

## 20261113-ghidra-fan — cálculo del giro y lectura del nivel

- MCP get_program_info confirmó main BAG2 JP SLPM_862.19, SHAea5a1668…
  (completo en ensayo HUD anterior). get_xrefs_to(8006d994,limit100):47refs,
  sin más páginas; writers8002db48/db54/dc2c en8002da74. Decompile8002da74
  confirma delta8006d994=8005d2dc salvo primer frame/pausa. Xrefs8005d2dc:
  writers main8001e938 y reset8001ecf0; decompiles confirman diferencia de
  contador y reset0, no un escalado8x. No se midió el delta efectivo en juego.
- Complemento headless `py -3.13 _work/gaso/stage-fan/trace_fan.py`: imports
  propios aislados native-usa-fan.bin a801e17b0, ported-fan.bin a801daf10.
  Export801e22c8/801dba28, exit0 en7.770/7.910s. Comandos exactos en
  `stage-fan/ghidra-trials.json`; bytes fuente y candidatos before/ bajo esa ruta.
  No se cambió el programa GUI. Son decompiles del nativo y port ANTERIOR a C.
- Overlay nativo USA SHA0d3a49731d5d44f62e108ce925aa37fafc044896a3e7ce5ab80f1efdc430a320.
  El giro es speed*delta/16; el port previo /2. Goldfish detectó además lectura
  80070108 en ruta nivel1: confirmada por decompile y MIPS. Candidato final
  corrige divisor y LUI, no todo el motor general de reubicación.
- Independencia: Capstone sobre bytes, pruebas de generador y ejecución de144
  casos originales/corregidos con intérprete PSXRecomp; port previo no coincide.
  Detalle en notes/gaso-import.md sección C. Resultado útil, no aceptación visual,
  ni prueba de cadencia/RPM. Tiempo/manual/ahorro global desconocidos.

## 2026-11-13 reanudación Gas-O: verificación MCP al iniciar sesión

- `get_program_info` → SLPM_862.19, SHA256 ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe,
  1324 funciones; MCP ya conectado (no se relanzó Ghidra).
- `get_function_by_address(0x8002d06c)` → FUNCTION_NOT_FOUND: la entrada CAUGHT
  usada por el plugin no está definida como función en el proyecto; no se creó.
  `get_function_by_address`/`disassemble_function(0x8003190c, limit4)` →
  FUN_8003190c 160 bytes, prólogo `addiu sp,-0x18`: coincide con el dispatcher
  de eventos del actor anotado en notes/gaso-import.md (plan A-E).
- Solo comprobación de conexión/programa; no es evidencia nueva de utilidad.
  Tiempo/ahorro desconocidos. Próximo: consultas acotadas cuando F o A lo requieran.

## 20261113-ghidra-cleanup-inventory — 2026-11-13 UTC — Inventario de conservación

- Tipo: arranque/identidad y lectura acotada, sin cambios de análisis.
- Entorno: Ghidra instalado 12.1.4; MCP `get_program_info()`, después
  `list_segments(offset=0, limit=12)` y `list_segments(offset=12, limit=14)`;
  paginación completa de 26 bloques, última respuesta `has_more=false`.
- Entrada: proyecto existente `/SLPM_862.19`, ejecutable japonés SLPM_862.19,
  PSX LE32, SHA-256 `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  CODE inicializado `80010000..8005cfff`; no se analizó un overlay.
- Observado: sesión MCP activa con 1324 funciones; proyecto y análisis se deben
  conservar, no clasificar `ghidra/` como caché por estar ignorado en Git.
- Contraste independiente: `.gitignore` excluye `ghidra/`; el inventario local
  `_work/cleanup-audit-20261113/files.json` mide 13,88 MB / 20 archivos allí.
  El hash del ejecutable coincide con la consulta de inicio anterior.
- Dictamen: inconcluso como prueba de utilidad para limpieza; confirma identidad
  y sesión, no demuestra que otros archivos sean prescindibles. No se modificó
  el programa, no se inició otra instancia ni se obtuvieron decompilados.
- Medición: duración MCP y preparación/revisión no medidas; ahorro no medido.
- Siguiente: conservar proyecto Ghidra. Candidatos y límites del inventario en
  `notes/project.md`; ninguna eliminación autorizada por esta comprobación.

### Seguimiento del mismo ensayo — 2026-11-13 — lista conservadora

- MCP `get_program_info()` volvió a confirmar `/SLPM_862.19`, PSX LE32,
  SHA-256 `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`,
  1324 funciones. Se reutiliza la lectura paginada anterior de segmentos: mismos
  insumos y objetivo, repetirla no aportaría evidencia de limpieza.
- Contraste: `conservative-list.json` no incluye el proyecto ni binarios; solo
  205 cachés Python y un temporal de audio, con hashes y exclusión de enlaces/Git.
- Dictamen sigue inconcluso sobre utilidad para decidir borrados; sin cambios de
  Ghidra, decompilados ni nueva instancia. Tiempo y ahorro no medidos.
- Siguiente: conservar Ghidra; esperar aprobación de eliminación de lista exacta.

## 20261113-ghidra-hud-uv - layout de primitivas, texturas y carga de packs

- MCP `get_program_info()`: `/SLPM_862.19`, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  Decompilados/desensamblados: `FUN_800220b8` (relocador), `FUN_800201b0`
  (primitivas type1/2 texturizadas), `FUN_80021ff0` (type4: solo SetPolyF3/F4,
  color 0x303030), `FUN_800315c8`/`FUN_80031268` (subida de texturas, entradas
  0x30), `FUN_800342dc` (máquina de carga de packs) y `FUN_8001f874` (lee
  entrada DF2_: offset `lw s0,0x8(a0)` en 0x8001f8a4, tamaño en 0x8001f8a8).
- Uso: tablas de conteo/stride/byte de textura (`tex_idx = byte & 0x1f`) para
  `_work/gaso/hud/bag2-font/audit_body_uv.py` (SHA `4ea9fe9b…`); informe
  `corrected/body-uv-audit.json` (SHA `f5df828c…`).
- Validación independiente: el mismo lector sobre modelos stock detecta
  `tex_idx 1` (Heat 231, Strike 551, accesorio Bi-O 20 vértices), luego no
  devuelve ceros triviales. 16 modelos Gas-O: 3075 vértices, todos `tex_idx 0`.
- Dictamen: útil. Demuestra la exclusión UV de body2 sin ejecutar el juego; no
  demuestra identidad del pack residente ni el render real.
- Medición: tiempo y ahorro no medidos.
- Siguiente: hook latch en 0x8001f8a4 para identidad residente del pack HUD.

## 20261113-ghidra-cam - proyección, OT y escala del escenario Gas-O; firma del latch

- MCP `get_program_info()`: `SLPM_862.19`, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`. Solo
  programa principal; el renderer de nodos vive en overlays (003.dbi), leídos con
  Capstone (`20261113-capstone-cam`).
- Consultas: `FUN_8002da74` (H por fotograma vía `FUN_80044504(DAT_8006d98c)`,
  `ClearOTagR(base-4,0x1001)`), `FUN_8002dc9c` (H por defecto 0x180),
  `FUN_80014318` (pista de cámara: H = bits 16..27 si no es cero),
  `FUN_8002d85c` (halfwords 0x1000/0x400/0x100), xrefs de `*(0x8005D410)` (solo
  `FUN_8001F874` y el cargador `FUN_8001F6FC`), `read_memory(0x8001F8A0,12)`.
- Resultados: H BAG2 = 384 = BAG1 (scus 0x800774E0, reset 0x180) y pistas Gas-O
  con H=0: el FOV no es la causa. OT del mismo tamaño en ambos. `0x8002d85c` es
  igual en BAG1 (0x800320c0): no es la diferencia de escala de mundo; la matriz
  1/4 frente a 3/8 **no se localizó en código**, se comprobó empíricamente
  (`_work/gaso/cam-ws/render_probe.py`: cam95 a escala 0.25 reproduce el vacío
  de `f855.png`). La palabra previa del latch es `0x3C028006`, no `0x3C020006`:
  error real corregido y fijado por test contra `assets/disc_files/SLPM_862.19`.
- Validación independiente: bytes iguales en `_work/mainexe/slpm.bin`; test
  `test_load_latch_site_matches_original_executable`; paquete `stage197`
  con `model_scale [3,2]` (SHA `b663417f…`) y `test_stage_port.py` 6/6 en WSL.
- Dictamen: útil (descartó FOV/OT, detectó un fingerprint erróneo). Sin prueba
  en juego; escala de mundo no localizada en código.
- Medición: tiempo y ahorro no medidos.
- Siguiente: validar cámara y HUD en partida grabada, con autorización.

## 20261114-ghidra-drift
- Purpose: explain lateral convergence of BAG1 dancers (owner question 2026-11-14).
- MCP: get_program_info (SLPM_862.19 sha ea5a1668…); decompile 0x8002ccc8, 0x8002c404, 0x80012c9c,
  0x8002d85c, 0x8002b5bc; get_xrefs_to 0x8002b5bc (FUN_8001e0f4 x4); read_memory 0x80051900/0x40,
  0x80051a70/0x30; disassemble FUN_8001e0f4.
- Evidence: re-anchor on clip change; root = base + clip tx x dancer scale >> 7; hard leash
  FUN_8002cd48; home X +-4*130 = +-520, radius 440 (x zoom >> 8); ctl 0x8005F820 + side*0x98
  (+0x28 home, +0x38 radius).
- Validation: BAG1 counterpart read independently with Capstone (capstone.md 20261114-capstone-drift).
- Outcome: useful; in-game values unverified. Time ~40 min, no rework.
- Next: owner decision on proportional BAG1 radius.

## 20261114-ghidra-psx-psyq-leash-release-review — 2026-11-14 UTC — radio BAG1 y liberación nativa
- Tipo: uso real, solo lectura; Ghidra12.1.4/PSX loader, JP main `SLPM_862.19`, base0x80010000.
- MCP exacto: `get_program_info()`; `decompile_function_by_address(address="0x8002cd48")`, `("0x8002B5BC")`, `("0x8002D85C")`; `read_memory(address="0x8002ad00", length=64)`.
- Fallo conservado: `decompile_function_by_address(address="0x8002ad00")` devolvió FUNCTION_NOT_FOUND; read_memory sí verificó el swap. Ningún cambio de análisis.
- Entrada main SHA-256 `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`; identidad MCP ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe.
- Resultado: consumidor XZ, inicialización raw/active y zoom nativos verificados. Contraste: bytes/fingerprints del test, código generado y ruta runtime de VBlank; no reproducción de interleaving en juego.
- Evidencia con hashes: `_work/goldfish/bag1-leash-verdict.json`; RED/GREEN y suite29/3 tests. Liberación overlay complementada con Capstone, no sustituye el uso obligatorio MCP.
- Dictamen: útil para semántica de main; lectura de overlay no realizada en MCP (programa abierto es main), no se afirma lo contrario.
- Medición: duración de consultas/preparación/revisión no medida; ahorro no medido.
- Siguiente: validar candidato solo con otra partida autorizada. `funcmatch.py` omitido: no se busca ahora equivalencia main BAG1/BAG2.

## 20261114-ghidra-release-validation — 2026-11-14 UTC — corrected leash live-read anchor
- Tipo: uso real de solo lectura; Ghidra12.1.4, PSX loader, JP main SLPM_862.19 (no overlay005).
- MCP exacto: `get_program_info()`; `read_memory(address="0x8002D810", length=20)`.
- Entrada/identidad SHA-256: ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe; PSX:LE:32:default.
- Resultado: hex `28006426100805263800668e52b3000cb8140726`; consumidor lee ctl+0x38 y llama 0x8002CD48, pasando actor+0x810 y actor+0x14B8.
- Contraste: el muestreador read-only de la nueva toma exige estos mismos 20 bytes en RAM antes de recoger raíz/base; runtime candidato3b43cff8. Enlace vivo y aceptación audiovisual pendientes al escribir esta entrada.
- Evidencia: `_work/gaso/drift/run_leash_release_capture.py` y `release-run-preflight.log`; no modificaciones de análisis ni de memoria del juego.
- Dictamen: útil como ancla independiente de direcciones JP; no prueba movimiento ni sincronización de captura.
- Medición: consultas/preparación/revisión no medidas; ahorro no medido.
- Siguiente: exigir grabación aceptada y contrastar posiciones, flags y liberación. Sin búsqueda de equivalencias main; funcmatch no pertinente.

## 20261114-ghidra-release-live-contrast — 2026-11-14 UTC — enlace vivo confirmado (complemento del anterior)
- Tipo: verificación de contraste, sin nueva consulta de análisis; Ghidra 12.1.4, JP main `SLPM_862.19`.
- Contraste: el muestreador de la toma aceptada exigió en RAM los mismos 20 bytes
  `28006426100805263800668e52b3000cb8140726` antes de cada bloque de muestras; 171 filas con
  `all_runtime_pinned`/`all_read_only` verdaderos y 0 lecturas con heartbeat cambiado.
- Resultado: las direcciones usadas (`ctl+0x38/0x3C`, `actor+0x810`, `actor+0x14B8`) corresponden a
  las confirmadas por MCP; la toma `bag1-release-autoplay` (runtime `3b43cff8…`) mostró radio 318
  y liberación `0x7FFFFFFF` sin reescritura.
- Límite: el contraste demuestra la dirección y el valor, no píxeles en pantalla ni sincronía exacta.
- Dictamen: entrada anterior corregida por complemento, no reescrita; Ghidra sigue siendo el ancla.
- Medición: no medida; ahorro no medido. Siguiente: ninguna consulta pendiente para este hito.

## 20261114-ghidra-end-center — 2026-11-14 UTC — costura nativa del centrado final
- Tipo: uso real acotado; Ghidra 12.1.4 por MCP, instancia existente preservada.
- Consultas: `get_program_info()` primero; `read_memory(address="0x8002d7f4", length=56)`.
- Entrada: main JP `SLPM_862.19`, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
- Resultado: lectura sin huecos confirma guardas actor[3]/ctl[0xC], sitio8002D818
  `8E660038` (lw a2,38(s3)), llamada8002D81C a8002CD48 y después8002C404.
  No se modificó análisis ni memoria del juego.
- Contraste independiente: fingerprints del ejecutable original en
  `tools/test/test_bag1_leash.py`; regeneración aislada solo añade el callback en las
  dos rutas de shard09. Evidencia `_work/gaso/drift/end-center/codegen/report.json`
  y build `_work/workflow/20261114T071651559442Z-bag1-end-center-reviewed/metrics.json`.
- Dictamen: útil para anclar la costura y conservar el orden nativo; no prueba el
  consumidor de pose, la cadencia ni el aspecto del candidato893833b1 dentro del juego.
- Medición: consultas, preparación y retrabajo no medidos; ahorro no medido.
- Siguiente: prueba grabada solo tras autorización. Se reutiliza la equivalencia
  BAG1/BAG2 ya contrastada, sin nueva búsqueda funcmatch; FFmpeg/recorder aplazados
  porque esta fase no ejecuta partida ni procesa nueva evidencia audiovisual.

## 20261114-ghidra-clock-diagnosis — 2026-11-14 UTC — alcance del recentrado
- Tipo: consulta real acotada, sin modificar análisis/proyecto.
- MCP: `get_program_info()` confirmó `SLPM_862.19`, PSX LE JP, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`;
  `read_memory(address="0x8002D818", length=16)` devolvió
  `38 00 66 8e 52 b3 00 0c b8 14 07 26 01 b1 00 0c`.
- Contraste independiente: fingerprints originales fijados por tests; traza de ambas
  tomas sitúa el hueco en fase1/5/6, no en fase1/4/clip68 donde el callback puede escribir.
- Dictamen: útil para verificar seam y alcance; no explica el stall ni valida gameplay.
  Medición/ahorro no medidos. Evidencia temporal en
  `_work/gaso/drift/end-center/capture-clock-replay.json`; siguiente: relojes del productor.

## 20261114-ghidra-clock-probe-host — 2026-11-14 UTC — alcance de la instrumentación
- Tipo: comprobación MCP real acotada, sin cambiar análisis ni proyecto.
- `get_program_info()` confirmó `SLPM_862.19`, JP/PSX LE, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  `read_memory(address="0x8002D818", length=16)` devolvió
  `38 00 66 8e 52 b3 00 0c b8 14 07 26 01 b1 00 0c`: costura de clamp/C404 sin cambios.
- Contraste: bytes originales y exclusión de fase del recentrado ya verificados; el nuevo
  diagnóstico está en callbacks host de audio/recorder, no modifica MIPS, regiones u overlays.
  Fixture host real/syntax-check reportados en `notes/gaso-import.md` y log del recorder.
- Dictamen: útil para confirmar identidad y límite de alcance; no diagnostica por sí solo
  la pausa. Sin equivalencia nueva que justifique repetir funcmatch, ni nueva grabación que
  justifique inspección FFmpeg. Tiempo/ahorro no medidos. Pendiente evidencia viva autorizada.

## 20261114-ghidra-dance-centering-crash — 2026-11-14 UTC — caída de servidor MCP en decompilación
- Tipo: fallo de herramienta MCP en ejecución; sin cambios al proyecto `.gpr`.
- Consulta: `decompile_function_by_address` sobre `0x8002CD48` y `0x8002C404` mientras `javaw` PID `63424` (`Ghidra: BAG2JP`) estaba abierto con `SLPM_862.19` (`ea5a1668…`).
- Fallo: `BrokenResourceError` / `Connection closed: MCP server process exited with code 1`; el catálogo de sesión retiró `ghidra` tras el fallo.
- Mitigación usada: desensamblado directo con Capstone 5.0.7 sobre `SLPM_862.19` y `005.dbi` (registrado en `notes/tool-evidence/capstone.md`) y contraste de RAM en `combined-ae-f2/bag2jp_watch.log`.
- Dictamen: bloqueado/caído en sesión actual para decompilación MCP; tiempo/ahorro no medidos. Siguiente: reiniciar puente/sesión antes de requerir nuevas consultas MCP Ghidra.

- Tipo: comprobación MCP real acotada, sin cambiar análisis ni proyecto.
- `get_program_info()` confirmó `SLPM_862.19`, JP/PSX LE, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  `read_memory(address="0x8002D818", length=16)` devolvió
  `38 00 66 8e 52 b3 00 0c b8 14 07 26 01 b1 00 0c`: costura de clamp/C404 sin cambios.
- Contraste: bytes originales y exclusión de fase del recentrado ya verificados; el nuevo
  diagnóstico está en callbacks host de audio/recorder, no modifica MIPS, regiones u overlays.
  Fixture host real/syntax-check reportados en `notes/gaso-import.md` y log del recorder.
- Dictamen: útil para confirmar identidad y límite de alcance; no diagnostica por sí solo
  la pausa. Sin equivalencia nueva que justifique repetir funcmatch, ni nueva grabación que
  justifique inspección FFmpeg. Tiempo/ahorro no medidos. Pendiente evidencia viva autorizada.

## 20261114-ghidra-block4-selector — 2026-11-14 UTC — retorno al selector Gas-O

- Tipo: consultas MCP de solo lectura con instancia GUI existente; sin cambios de análisis.
- Ghidra12.1.4; `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/gaso/probe_call.py`:
  `get_program_info {}`, `read_memory {address:0x8003190c,length:148}` y
  `decompile_function_by_address {address:0x8001f874}`. Cada conexión pide info primero.
- Main japonés SLPM_862.19, PSX LE32, SHA256
  ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe;
  sin overlay007 seleccionado en el proyecto. Salidas `block4-*-mcp.json` y
  `block4-program-info.json` en `_work/gaso/block2/`.
- Resultado: el loader usa tabla8005d410 y CdRead para cargar recursos. No prueba por
  sí mismo la invalidación del retrato. La lectura3190c era del contexto CAUGHT previo
  y no añadió información pertinente al preview: irrelevante para ese defecto.
- Contraste: regresión host ejecuta callbacks de producción (RED4/6→GREEN12/12);
  la recarga efectiva y el renderer quedan para la toma WGC autorizada.
- Dictamen: útil para confirmar binario/costura de carga; inconcluso para el retorno
  nativo aislado. Tiempo/ahorro no medidos. No funcmatch: no se buscan equivalentes BAG1.

## 20261114-ghidra-block4-capture-identity — 2026-11-14 UTC — ciclo captura/entrada

- Tipo: lectura MCP real con instancia GUI existente, Ghidra12.1.4; sin editar proyecto.
- Puente `D:/Dev/Tools/ghidra-mcp-python/python.exe _work/gaso/probe_call.py`:
  get_program_info primero; `read_memory {address:0x8002d4a0,length:48}` y
  `decompile_function_by_address {address:0x8002d85c}`. Main SLPM_862.19 JP/PSXLE32,
  SHA256 ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe.
- Evidencia `_work/gaso/block2/lifecycle-entry-seam-mcp.json` y
  `lifecycle-controller-init-mcp.json`: la inicialización escribe controller+18=-1,
  un valor reinicializado, no una identidad de carga. Lectura bounded del tramo
  de adopción de slot conserva instrucciones; no se crean funciones ni overlays.
- Contraste independiente: regresión host de callbacks reales demuestra aceptación
  indebida tras cambiar el atacante de la captura; nuevo guard revoca identidad/tablas.
  No se infiere generación de bytes iguales, reloj de frames ni ownership savestate.
- Dictamen: útil para descartar el contador de init como generación; evidencia viva
  de recuperación sigue pendiente. Tiempo/ahorro no medidos. No funcmatch/Capstone
  nuevo: no se buscan equivalentes ni hay bytes fuera del main que lo requieran.

### Seguimiento de la misma investigación: callers de init

- `get_program_info` primero en cada conexión del mismo puente; `get_xrefs_to`
 8002d85c→1caller8002ba18/FUN8002b5bc; 8002b5bc→4callers en8001e0f4
  (8001e424/430/43c/448). Salidas `lifecycle-{init,pair-init}-xrefs-mcp.json`.
- Corrección de alcance: xrefs del main no enumeran005 ni prueban un único evento
  de init en todo el juego; scan/capstone de005 confirma otros12JAL directos.
  Este nuevo dato evita fundamentar generación únicamente en fase3main.
- Costura existente8002ba18 se puede investigar sin nuevo layout de memoria;
  no está implementado un observador de generación. Sin cambios al proyecto,
  ahorro no medido; el ensayo previo se amplía, no se invalida su lectura de main.

## 20261114-ghidra-native-init-review — observador host, sin editar análisis

- Uso real: puente instalado `D:/Dev/Tools/ghidra-mcp-python/python.exe
  _work/gaso/probe_call.py`, Ghidra12.1.4 existente. Cada conexión pide
  `get_program_info` primero; consulta acotada `read_memory
  {"address":"0x8002ba08","length":32}`. Identidad completa guardada aparte
  con `get_program_info {}`. No reinicio, instalación ni creación de funciones.
- Programa main JP `SLPM_862.19`, PSX:LE:32, base80000000/entrada80035d98,
  SHA256 ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe.
  Resultado sin gaps: argumentos a0=s2/a1=s1/a2=sp+16 y word0c00b617 del JAL
  en8002ba18; overlay005 no se presenta como cargado en este programa main.
- Evidencia `_work/gaso/block2/lifecycle-native-init-review-{mcp,program}.json`.
  Contraste independiente: fixture host compara word con EXE JP original y
  sitio opt-in/AOT existente; revisión Goldfish del candidato separada.
- Dictamen: útil para confirmar la costura exacta de observación; no demuestra
  recuperación de ownership ni ejecución en partida. Ejecución/preparación y
  ahorro no medidos. Reusar bytes/xrefs históricos mientras no cambien entradas.

## 20261115-ghidra-slot1-native-empty — origen nativo de empty_raw

- Propósito: autenticar la tupla vacía de slot1 para recuperar ownership CAUGHT
  tras load sin journal ni MODMEM. Uso real: namespace MCP `tools.ghidra` en Code
  Mode, `get_program_info` primero (JP `SLPM_862.19`, SHA256 ea5a1668…1efe,
  1324 funciones). Decompilación de 800125fc/8001262c/800126a4/80031d3c/
  800319fc/800326d4/80032a40, xrefs de los tres helpers y disassembly acotada de
  80031d3c (60 instrucciones). Sin crear/renombrar funciones ni comentarios.
- Hallazgo: los constructores del actor fijan +0x10 = DFS de motions y llenan
  raw[] con FUN_800125fc (`[size][payload]...` hasta size0; raw[i]=&payload_i).
  raw[0]=M+4, raw[1]=M+8+size0; payload con primer word 0 da length0/meta0.
  FUN_800326d4 reubica/extiende y comparte tablas con el compañero, sin escribir
  +0x10 y conservando raw[0]; FUN_800319fc copia el +0x10 del principal;
  FUN_80032a40 usa otra estructura (+0xac). Evidencia transcrita
  `_work/gaso/block2/slot1-recovery-ghidra.json`.
- Validación independiente: harness host con DFS nativo, 25/25 mutantes muertos
  por aserción y dos revisores Goldfish que contrastaron la derivación.
- Dictamen: útil; permitió autenticar `empty_raw` por derivación nativa en vez de
  journal (sin cambio de MODMEM/cookie). No demuestra comportamiento en partida.
  Tiempo ~10 min de consultas; ahorro no medido. Respuestas MCP crudas no
  guardadas: se transcribieron las líneas relevantes.

## 20261115-ghidra-recovery-recording — preparación de toma guard1

- Pregunta: verificar sesión/programa relevantes antes del save/load grabado.
  MCP get_program_info: SLPM_862.19 JP, SHA256
  ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe.
  disassemble_function(address=0x80031d3c,offset=0,limit=24): constructor de
  actor existente; 24 instrucciones, sin modificación de proyecto/funciones.
- Contraste: evidencia de derivación DFS del ensayo anterior y host38/91 ya
  verificados, reutilizados sin repetir. Lectura de main.cpp del framework
  determina la vía F7 del host; no atribuir esa UI a la función PSX.
- Resultado: útil para verificar identidad/contexto; no nueva demostración de
  recuperación ni aceptación en partida. Tiempo de consultas no medido;
  ahorro no medido. Siguiente: toma con runtime94922aba y gates del grabador.

## 20261115-ghidra-process-audio-feasibility — verificación obligatoria acotada

- MCP get_program_info: SLPM_862.19 JP, SHA256
  ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe,
  1324funciones. disassemble_function(0x8002d06c,offset0,limit8) devuelve
  FUNCTION_NOT_FOUND: no crear/renombrar función para remediarlo.
- read_memory(0x8002d06c,length32) sí responde sin gaps; prólogo
  c0ffbd272400b3af219880003400b7af3c00bfaf3800beaf3000b6af2c00b5af.
  Corresponde al seam nativo observado para CAUGHT; proyecto/análisis intactos.
- Útil para identidad/bytes originales y cumplimiento de sesión; no nueva
  evidencia sobre audio Windows. Esa API se contrastó por SDK/docs oficiales
  y prueba host aislada, no se atribuye a Ghidra. Tiempo/ahorro no medidos.
