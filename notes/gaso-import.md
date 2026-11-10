---
id: gaso-import
title: "Gas-O: importación y aceptación"
tags: ["bag1", "gaso", "import", "evidence"]
summary: "Prioridad: paneles rojos sobre GAS corregidos y ACEPTADOS por el propietario el 2026-11-10 con el candidato v2; tanque rechazado por el propietario. Historial regional, SPU, audio y aceptación parcial conservados."
related: ["plans/gaso-import.md", "IMPORT_STANDARD.md", "notes/character-pipeline.md"]
created: "2026-11-06"
updated: "2026-11-10"
doc_kind: evidence
---

# Gas-O — ledger canónico

## Tareas Pendientes Prioritarias (Solicitadas por el Propietario)
- [x] **Escenario: paneles rojos no deben tapar el cartel blanco GAS**. V1 falló visualmente; v2 subdivide solo tres caras nativas y no muestra el solape en las capturas reales de la intro (frames 056-074). **Aceptado por el propietario el 2026-11-10.** Véase «Revisión visual de la intro v2» al final. No confundir pruebas host/build con aceptación.
- [x] **Escucha en combate de Chemical Love grabada**: Ejecución verificada en partida Versus real con captura de audio SPU/FLAC completa (`bag2jp_audio.wav`, 142.01s, 44.1kHz stereo) en `_work/versus-runs/20261108T225855012145Z-gaso-listen-gameplay/`.
- [ ] **Efectos visuales de humo de entrada de Gas-O**: expulsión de humo denso/fiel por los tubos de la mochila al inicio de sus combates.
- [ ] **Ataque Especial de Gas-O: corrección visual pendiente, NO aceptada por el propietario (2026-11-09)**:
  - Los siguientes puntos son antecedentes del candidato; no demuestran la aceptación visual actual. Véase el seguimiento de defectos al final de esta nota.
  - Extracción y renderizado de la malla 3D nativa original de BAG1 (`PLAYER2/P_GAS_A2.DFS` miembro 2 / `002.bin`: 41 vértices, 24 quads de cuerpo metálico, 8 triángulos de tapa biselada y 8 quads de cilindro de cristal translúcido).
  - Colores nativos de fábrica de PS1 aplicados: Metal `RGB(89, 89, 102)`, Cristal químico `RGB(125, 255, 106)`.
  - Sprites y volutas de humo químico con coordenadas UV auténticas de la tabla nativa `0x801DCE4C`.
  - Rival mantenido de pie y congelado (`anim 78`, sin knockdown) con buffer de comandos reseteado.
  - Verificado en combate real Versus con ráfaga de 140 fotogramas (`_work/versus-runs/20261109T070157624424Z-gas-o-attack-bag1-gasobag1`).
  - Comparativa directa con el metraje nativo generada en `_work/gaso_tank_authentic_comparison.png`.


## Alcance y aceptación

Plan aprobado: [gaso-import](../plans/gaso-import.md). Destino Bi-O, character9;
packs53/54/125/126, modelos89/90/161/162, fever17/35, escenario197.
El propietario exige variantes USA y JP de personaje, escenario y canción;
no confundir el personaje USA ya probado con la importación regional completa.
El propietario amplió esta continuación a Heat/Strike: completar también sus
variantes pendientes, sin esperar al cierre de Gas-O (2026-11-06).

Histórico del 2026-11-06, no reejecutado en esta continuación: fases0–5 USA,
P1/A, P1/B, P2/A, P2/B y canción completa con vuelta al selector. Rutas exactas
en `_work/current-state.json:gaso_task.evidence`; fuente de detalle: fases3–5
del plan. No demuestra escenario Gas-O ni variante JP aceptados.

## Despliegue regional experimental (2026-11-06)

### Escala y entrada: candidato host posterior

Se añadió Gas-O a `b1v_scale_q12`: **3132 para ambos trajes**, uniforme en
los tres ejes. Cálculo del candidato: round(3429 ×116/127), anclado a StrikeA
ya corregido y a los bytes de escala BAG1 Gas116/Strike127. No se escalaron
vértices ni clips. Para base98 da75 en lugar de98; es una propuesta de proporción,
**no una medición visual aceptada**. La lectura de la tabla BAG1 sigue siendo
evidencia cruda/histórica, no un nuevo análisis de su consumidor nativo.
MCP confirmó el consumidor BAG2: `8002B5BC` lee51904 por characterID, multiplica
por el factor común y llama `8002D85C`, que guarda base/escala en1514/14E4.

Regresión `tools.test.test_bag1_dancer_scale`: RED por98≠75 antes del cambio,
GREEN después; ejecuta el C real con RAM simulada, prueba GasP1/A yP2/B, tres
ejes, no acumulación, force-stock/BAG2 y Strike98→82 sin cambios. Junto con las
cinco pruebas visuales:6/6; `_work/gaso/scale-test-{red,green}.log`.
Baseline previo `versions-before-gaso-scale.c`. **Actualización posterior:** build
`20261106T212253733101Z-gaso-scale-candidate` pasó preflight y compilación (exit0).
Se desplegó solo el ejecutable; paquetes idénticos y cinco configuraciones intactas,
con hashes/backup en `_work/gaso/deployment-backup-scale/report.json`.
Staging de un solo fuente verificado contra baseline en `build-stage-backup-scale/`;
no se incorporó el drift ajeno de netsync. Primera comprobación de staging falló
por espacios en la cadena de validación, antes de copiar; corregida sin tocar C.
MCP confirmó principal JP/tabla de escala, log ghidra-027. Recalibración
`gaso-scale-probe` completada en89.472s; ocho destinos revisados por el agente
en `20261106T212406204315Z-gaso-scale-probe/probe-review-small.png`, sin afirmar
aceptación humana de fidelidad. Tres configuraciones y21saves restaurados.
Calibración aceptada para runtimeSHA
`27c73dd2c45d9e5f473944e8047e80a6af432180c5aa305eb7dea5b0fd89e9a9`.
Partida `20261106T212608163326Z-gaso-scale-p1a-full` completada en287.236s
(Gas-O A contra Strike B, StrikeBAG1); retornó al selector y restauró tres
configuraciones/21saves. Log de versiones confirma Gas98→75 y Strike98→82.
Revisión del agente de `motion-review-small.png` (gameplay, match8–13, retorno):
Gas-O menor que Strike, distintas poses durante la canción; no demuestra
fidelidad nativa ni todas las transiciones. La partida
`20261106T213125319853Z-gaso-scale-p2b-full` (Strike A contra Gas-O B) terminó
en284.549s con retorno, tres configuraciones/21saves restaurados. Log confirma
GasP2 98→75 yStrikeP1 98→82; el agente revisó gameplay ymatch8–13: distintas
poses y menor tamaño relativo, sin comparación nativa. En curso
`20261106T213638691729Z-gaso-scale-p1b-p2a-full`, Gas-O B contra Gas-O A,
**falló** tras194.725s: timeout esperando gameplay, pantalla VS en
`final-small.png`, estado root19/phase0/2/0; no canción ni retorno aceptados.
Restauró tres configuraciones/21saves. Log: ambos buffers expandidos en7738,
último cambio de animación8004 P1ch9/P2ch0; sin mensajes de escala. No prueba
que la escala causara el bloqueo ni que sea solo un fallo del harness.
Hipótesis a aislar: interacción del mismo personaje en ambos lados frente a
trajeB/P1 o carga de recursos. `20261106T214034604328Z-gaso-scale-p1b-isolated`
(Gas-O B contra Strike A), sin cambios de código, completó284.2s y retorno;
tres configuraciones/21saves restaurados. El agente revisó gameplay ymatch8–13:
poses distintas y tamaño menor que Strike, no comparación nativa. Descarta un
bloqueo general de P1/B frente a Strike, no identifica la causa del dobleGas.
`20261106T214542580162Z-gaso-scale-p2a-isolated` (Strike B contra Gas-O A)
completó288.626s y retorno, restaurando tres configuraciones/21saves. Log de
versiones: GasP2 98→75, StrikeP1 98→82. El agente revisó gameplay ymatch8–13:
distintas poses, escala reducida; no comparación contra BAG1 nativo.
Así quedan cubiertos P1/A, P1/B, P2/A yP2/B **contra Strike**, con canción y
retorno. No implica aceptación de todos los clips/transiciones ni solo/duet
fever; no se atribuye cobertura de esas capacidades solo por terminar partidas.
Gas-O contra Gas-O sigue siendo un fallo abierto y bloquea estabilidad general.

Observación acotada posterior: build `gaso-system-error-probe` pasó; se desplegó
solo el ejecutable (backup `deployment-backup-error-probe`, paquetes intactos),
SHA798e0d8a1e98763a2fafd669ab014e41d6e7f0245f4beba394917507d4b30086.
El observador de anim-trace arma únicamente con trace activo y tres palabras
originales verificadas; cambia addiu por ori equivalente para entrar al intérprete,
registra a0/a1/RA/SP de SystemError y restaura la palabra original sin modificar
registros ni suprimir el error. Test host RED por ausencia y GREEN del observador;
no prueba aún su ejecución real. MCP verificó palabras originales y registro VAB
(ghidra-032). Probe `20261106T223423673791Z-gaso-system-error-probe` terminó92.604s,
restauró tres configuraciones/21saves; ocho destinos revisados por el agente y
catálogo aceptado para este runtime, no aceptación humana de fidelidad.
Partida diagnóstica `gaso-system-error-capture` GasP1/B contra GasP2/A: resultado
en el párrafo siguiente. Auditoría independiente de la captura8MiB
anterior (`vab-allocations.json`) muestra cinco bancos activos; no demuestra por
sí sola agotamiento SPU ni motivo de fallo. Humo y estabilidad siguen pendientes.
Auditoría wire adicional `pending-vab-size.json`: el banco pendiente solicita110144
bytes y quedan91664 tras el extremo de los bancos activos; no evalúa reservas ni
fragmentación del asignador. Inspección de los13samples del VAB Gas-O: muestras12
y13 son idénticas,15120bytes cada una (dos programas de anunciador añadidos por
append_cue). Es una oportunidad de deduplicación exacta sin cambiar audio/cues,
todavía no implementada ni demostrada como corrección del bloqueo.

Captura `20261106T223630963763Z-gaso-system-error-capture` (GasP1/B contra
GasP2/A, StrikeBAG1) falló igual, pero el observador registró
`SystemError a0=0x56('V') a1=1 ra=8002E060`. MCP (ghidra-033) decompila el
llamador `FUN_8002de5c`: código1 = `SsVabOpenHead<0`; descarta los códigos0
(RAM), 2 (TransBody), 3 (tabla de sonidos) y 4. En `_SsVabOpenHeadWithMode` el
fallo cuadra con falta de SPU (`SpuMalloc==-1` o `addr+size>0x80000`); el lock
de transferencia no queda excluido por registro directo. Presupuesto SPU
(volcado8MiB): base4112+sistema60096+escenario StrikeBAG1225536+lado P1
(voz110112+4336+28384) termina en432624; quedan91664 y P2 pide110144.
Bi-O nativo: voz64032 (11 VAG, anunciador15120 una vez). Gas-O: 13 VAG,
110112; las VAG12/13 son copias idénticas del anunciador (cues0x1907/0x1908,
`append_cue`). Deduplicarlas deja94992: **insuficiente** por sí solo con este
escenario; no hay cola silenciosa recortable. Todos los fallos dobleGas usaron
StrikeBAG1; prueba discriminante `20261106T224516426260Z-gaso-double-heatstage`
(dobleGas en HeatBAG2 sin cambios) **falló igual** (SystemError 'V',1,
ra8002E060; configs y21saves restaurados): no es exclusivo de StrikeBAG1.
Volcado8MiB en HeatBAG2 (`20261106T224838746523Z-gaso-double-heatstage-8mb`,
mismo fallo; `bag2jp_ram_9000.bin` sha98C3EF56… copiado desde la instalación,
`vab-allocations.json`): slots0/1/2/4 iguales (60096, 225536, 110112, 28384);
el slot3 varía con el escenario (StrikeBAG1 4336, HeatBAG2 16448), así que la
etiqueta anterior «slot1 = escenario» era errónea. Extremo444720; quedan
**79568** y P2 pide110144. Con el mismo resto de bancos, Gas-O cabe dos veces
cuando su cuerpo de voz ≤ el de Bi-O (64032); hoy 110112, deduplicado94992.
Reducir los otros ~31KB exige recortar o remuestrear voces BAG1 (con pérdida).
**Aprobado por el propietario (2026-11-06): deduplicar + remuestrear**, sin
quitar voces. Implementado en `tools/bag1import/vab_budget.py` (compartido;
codificador VAG ADPCM local porque ninguna herramienta de `notes/assets.md` lo
cubre; 11 pruebas `tools/test/test_vab_budget.py`), límite en perfil
`gaso.json` `voice_bank.max_body_bytes`=64032. Corrección de tono según
ghidra-034 (centro/shift del tono). Resultado: cuerpo 63888/64032, las 11 voces
BAG1 remuestreadas −1104/128 semitonos (~0,61×), anunciador stock byte a byte.
Salida `_work/gaso/voice-budget/{usa,jp}`: solo cambia el miembro SEDT de
voz de los packs 53/54/125/126 (`diff-report.json`). Payload reproducido antes
byte a byte (5b618e…); nuevo payload `9f4294d5…` 9504768 bytes, 28 filas
verificadas y capacidad DUMMY (`_work/gaso/voice-budget/dummy-capacity.json`).
Build `gaso-voice-budget` correcto; desplegado (exe `6CE43381…`, payload,
manifest; respaldo `_work/gaso/voice-budget/deployment-backup/`). Selector
recalibrado (probe `gaso-voice-budget-probe`, 8 bordes revisados visualmente,
`accept_versus_calibration.py`). **Doble Gas-O B/A pasa** en StrikeBAG1
(`20261106T230811669356Z-gaso-voice-budget-double-strike`, 152s) y HeatBAG2
(`20261106T231105650680Z-gaso-voice-budget-double-heat`, 132s): sin
system-error, popups Gas-O/B y Gas-O/A, ambos en escenario; configs+21 saves
restaurados. Partida completa doble Gas-O B/A en StrikeBAG1 con `--finish`
(`20261106T232951078763Z-gaso-voice-budget-double-strike-finish`, 293s,
`complete_awaiting_visual_review`): fever dúo (fever2) en el trace, combo y
puntuaciones en juego, fin de canción y vuelta al selector revisados visualmente
(`agent-end-sheet.png`); sin system-error; configs+21 saves restaurados. WAV
antes/después para escucha: `_work/gaso/voice-budget/listening/`
(`_work/gaso/export_voice_listening.py`; duraciones iguales ±2ms). **Escucha
aprobada por el propietario (2026-11-06): voces y efectos se oyen bien.**
Regresión Gas-O individual (Gas-O BAG1/A vs Heat BAG2/A, HeatBAG2, `--finish`)
`20261106T233514461994Z-gaso-voice-budget-single-finish` completa, 287s, saves
restaurados.

**Anunciador con nombre de Gas-O (petición del propietario 2026-11-06).** Las
cues 0x1907/0x1908 del banco de voz eran las de Bi-O. Ghidra (ghidra-035):
`SsUtKeyOnV` solo lo llama FUN_8002e2d0; la tabla de sonido son 6×u16 (vab,
prog, cue, volumen, nota/fine), por lo que la tasa real es
44100·2^((60−centro)/12). BAG1 pack Gas-O miembro 7 (JP == USA byte a byte):
0x2091 vag01 "Gas-O!" 1,95s y 0x2090 vag02 "Gas-O" 1,41s; 0x20F0 vag03 dice
"versus" (no usado). Propietario eligió la versión japonesa. Mapeo en perfil
`gaso.json` `announcer.cue_map` {0x1907←0x2091, 0x1908←0x2090};
`preserve_announcer.rename_cue` reutiliza el registro stock de Bi-O. Bi-O sigue
con su banco nativo (sus cues no cambian). Cuerpo 63776/64032, voces BAG1
remuestreadas −1248/128 semitonos (antes −1104). Payload `78842df3…` (28 filas,
capacidad DUMMY `_work/gaso/announcer-names/dummy-capacity.json`), build
`20261107T000811610572Z`, desplegado en exp-8mb (exe `71CE8826…`, ruta real
`mods/bundled/...`; respaldo `_work/gaso/announcer-names/deployment-backup/`).
Probe `20261107T000948902901Z` revisado (8 bordes) y aceptado. Partida completa
doble Gas-O B/A en StrikeBAG1 `20261107T001149362684Z-gaso-announcer-names-double-strike-finish`
291s: fever en trace, popups Gas-O/B y A, gameplay, vuelta al selector
revisados; sin system-error; 21 saves restaurados. Pendiente: escucha en juego
del nombre por el propietario (WAV `_work/gaso/announcer-names/listening/`).
Pruebas host `tools/test/test_preserve_announcer.py` (5) + `test_vab_budget.py`
(11): 16 OK.

**Dobles de baile corregidos (2026-11-07, pendiente de revisión humana).** El
propietario vio pasos "de cabeza" que vuelven de golpe a pie. Causa: el
`b1_anim((7,v))` compartido de `tools/bag1import/anim_remap.py` usaba la petición
BAG1 `29+7-max(v,1)` (desplazada un nivel). Evidencia BAG1 (Capstone sobre
`_work/bag1/scus.bin`, capstone-005; Ghidra solo tiene cargado BAG2): 0x800243f4
decodifica la petición r>=29 como compás 7, nivel 35-r, así que el doble del
nivel v es la petición `35-v` (v 0..6); tabla alt 0x80055854 coherente. La
matriz de poses `_work/gaso/double_entry_matrix.py` coincide (Gas-O, Heat y
Strike). Remapeo regenerado: peor arista 171°→66° (Bi-O nativo 79°). Solo
cambian los 4 DFS de modelo (packs/voces idénticos); payload ff79c563…,
`_work/gaso/dance-doubles/`; exe C7A34421. Doble Gas-O B/A StrikeBAG1 con final
`20261107T002631063982Z-gaso-dance-doubles-double-strike-finish`: completo,
sin system-error, 21 guardados restaurados. **Afecta a Heat/Strike** en su
próxima reconstrucción (sus activos desplegados no cambian aún).

**Versión por defecto BAG2 (petición del propietario 2026-11-07).** Heat,
Strike y Gas-O abren el popup en su versión BAG2 (Gas-O → Bi-O): defaults
`bag2` en el manifiesto y `b1v_read_options` solo activa BAG1 con `bag1`
explícito. `mods/state.toml` de exp-8mb tenía heat/strike en `bag1`; cambiado
a `bag2` (respaldo `_work/gaso/version-defaults/deployment-backup/`). exe
8FE7BB2F. Run `20261107T003500323308Z-gaso-version-defaults-pick`: log
`open: … current 0` para Gas-O y Heat, popup muestra "GAME BAG 2", BAG1 sigue
seleccionable (confirm Gas-O BAG1).

**Corrección del anunciador (2026-11-07, sustituye el mapeo 0x1907/0x1908).**
El propietario seguía oyendo "Bi-O" en el VS y solo "Win" al ganar. ghidra-036:
la tabla de victoria 0x80051424 da a chr9 la cue 0x1909 (voz); el nombre del VS
son 0x3090 (P1 miembro 5, junto a 0x3130 "versus") y 0x3091 (P2 miembro 4).
0x1907/0x1908 son frases propias de Bi-O ("NOOOO"), no nombres: se quitan (una
cue ausente no suena: FUN_8002e2d0 devuelve -1). Perfil `announcer.voice_cues`
{0x1909←0x2090} y `vs_cues` {p1 0x3090←0x2090, p2 0x3091←0x2091}; nuevo
`preserve_announcer.replace_cue` conserva el registro stock y el "versus" exacto.
Cuerpos: voz 63792/64032 (remuestreo −848/128, mejor que −1248), VS P1
31600/36576 y P2 18368/27472 sin remuestrear. Transcripción de los bancos
reconstruidos: "Gas-O" en 0x1909/0x3090/0x3091. Payload `c6e4ae8f…` 9439232 B
(28 filas, cabe); **al cambiar la longitud cambia `expected_sha256`** (`443d687e…`
del `alt_report.json`); el primer probe falló con "stock overlay range checksum
failed" hasta corregirlo — `check_alt_payload.py` no lo comprueba. exe
`8DC32D7B`, respaldo `_work/gaso/announcer-fix/`. Probe
`20261107T005204027472Z` revisado y aceptado; doble Gas-O B/A StrikeBAG1 con
final `20261107T005347685398Z-gaso-announcer-fix-double-strike-finish` completo
298s, fever2, vuelta al selector, sin system-error, 21 saves restaurados. Host
tests 20 OK. Pendiente: escucha en juego por el propietario (VS y victoria).

**Ciclo combinado (2026-11-07): fix de dobles en Heat/Strike.** El propietario
pidió hacer los pasos pendientes en un solo ciclo. `_work/gaso/rebuild_heat_strike_doubles.py`
regenera los movimientos de Heat (95/96/167/168) y Strike (109/110/181/182) con el
mapeo antiguo, exige igualdad byte a byte con el miembro actual (16/16 iguales) y lo
sustituye por el corregido. Peor borde Heat 136.8°→55.1°; Strike sin cambio (52.7°).
Spec `_work/gaso/combined-cycle/spec.json`, payload `f2296c4c…` 9439232 B (28 filas,
cabe; `expected_sha256` sin cambio `443d687e…`). Scripts reutilizables nuevos:
`_work/gaso/stage_alt_payload.py <work>` (mods-src + árbol de build, actualiza ambos
hashes del manifest) y `_work/gaso/deploy_exp.py <work>` (exe/manifest/payload con
respaldo e informe). exe `8DC32D7B→FE791DD9`. Probe `20261107T103635164262Z`
revisado y aceptado; Heat BAG1/A vs Strike BAG1/A HeatBAG2 con final
`20261107T103823507356Z-combined-heat-strike-finish` completo 279s, fever en traza,
vuelta al selector, sin system-error; doble Gas-O B/A StrikeBAG1
`20261107T104322223495Z-combined-double-gaso` correcto. 21 saves restaurados en
todos. Ghidra no se usó en este paso (solo empaquetado; evidencia de la causa en
capstone-005). Pendiente: escucha/vista del propietario (nombres VS/victoria y bailes
Heat/Strike/Gas-O) y retrato HD Gas-O↔Bi-O (diseño por aprobar).

**Pitch de voces remuestreadas (2026-11-07).** El propietario aprobó el nombre en el VS
pero no oía el nombre de la victoria. Sonda de slots de cue (`--watch-cues`, límite del
watcher elevado a 32) mostró que 0x1909 sí se dispara (estado 4, 80 frames antes del Win)
y está en la tabla de sonido; el audio grabado no coincidía (NCC 0.09; control Bi-O
original 0.746). Volcado SPU (`BAG2JP_SPU_CUE_DUMP`, `--spu-cue-dump`) en
`20261107T114911955759Z-gaso-victory-spu`: muestras byte a byte correctas, pitch voz14
0x0465 en lugar de 0x0416. Ghidra ghidra-037: `SsPitchFromNote` suma `shift/128`, así que
el centro efectivo es `center − shift/128`; `vab_budget.resample_samples` aplicaba el
signo al revés y **todas** las voces remuestreadas sonaban +1.25 semitonos (también las
que el propietario escuchó). Corregido (test RED→GREEN, 21 OK). Rebuild
`_work/gaso/pitch-fix/` (prog11 centro 84 shift 48 = 83.625), payload `852ebd0c…`
(28 filas, cabe, `expected_sha256` sin cambio), exe `4790B275→F5F92BEB`. Probe
`20261107T115922321063Z` revisado/aceptado. Doble Gas-O B/A HeatBAG2 con final
`20261107T120108356029Z-gaso-pitch-fix-victory`: pitch voz14 0x0416, NCC 0.643 a 269.09 s,
21 saves restaurados. Escucha del propietario en `20261107T121359865999Z-gaso-owner-listen`
(doble Gas-O, autoplay): **aprobados** el nombre en el VS, las voces en canción con el tono
corregido y "Gas-O" antes de "Win" (2026-11-07).

**Retrato Ultra HD de Gas-O y Persistencia en Selector y Stage Select (2026-11-08).**
Se corrigió la conmutación dinámica del retrato Ultra HD de Gas-O (`029_Gas_O.png`, con máscara de gas, gafas moradas y tubos respiradores) frente a Bi-O (`020.png`, zombi con hacha en la cabeza). En `bag2jp_charsel_popup.c`:
- Se erradicó la corrupción de VRAM previa eliminando escrituras invasivas a descriptores de otros personajes (`0x80096438 + s*48 + 0x28`).
- Se implementó la subida limpia de la paleta modificada (entrada 235 con valor `0x7FFE` para Gas-O y `0x7FFF` para Bi-O) a través de `psx_mod_psyq_load_image(rx, ry, rw, rh, src_clut)` a las coordenadas del RECT VRAM de cada jugador (`0x80096458` para 1P, `0x80096488` para 2P, `0x800967E8` en Stage Select).
- Esto fuerza la invalidación de la caché de DuckStation/Recomp y activa la carga instantánea del hash `61E197B20D89CB1E` (Gas-O HD) con fondo verde tóxico (`0x0030E020`) y nombre "Gas-O".
- Verificado y registrado con capturas en partida real (`_work/gaso/evidence/portrait_check/crop1p_p2-popup.png`, `crop1p_stage-selected.png`, `crop2p_stage-selected.png`): ambos lados (1P y 2P) muestran al 100% el retrato HD nítido de Gas-O sin afectar a otros personajes ni a los rectángulos de la VRAM.

**Candidato fever solo (2026-11-07, aceptación pendiente).** El barrido del visor BAG2
registró 88 índices: 85 capturados y WIN4/FEVER4/FEVER5 vacíos. Los fever reproducidos
no coincidían con los dos originales BAG1: faltaba la entrada 17 en el payload y se
usaba la coreografía stock de Bi-O. `anim_remap_gaso.build_fever()` genera ahora
82/83/82, rebasa las voces a 0x6900 y conserva la cola vacía; el builder añade el
contenedor 17 conservando su miembro 1 stock. Pruebas host: 14 OK; los ocho
contenedores anteriores permanecen byte-exact. Candidatos USA/JP y comprobaciones en
`_work/gaso/fever-solo/`: payload 29 filas, 9.500.672 bytes frente a 27.648.000,
SHA-256 `54675d21e711d33d3a210206e512df931d570b3c2084a87306301873b626f57d`.
Build y despliegue solo experimental: exe `165a2dce…`. Entrada 35 duet sigue stock:
**no está corregida ni aceptada**. Confirmación nativa: [ghidra-038](tool-evidence/ghidra-psx-psyq.md).

Probe `20261107T133050002181Z-gaso-fever-solo-probe`: cierre/restauración verificados,
21 saves originales intactos; selector, ocho aristas y hoja revisados visualmente y
calibración aceptada para ese hash. Preflight `20261107T133430772393Z` pasó. La partida
completa `20261107T133531692083Z-gaso-fever-solo-full` (Gas-O BAG1 B/A, HeatBAG2,
audio y cues) terminó: salida de batalla a 157,5 s, retorno al selector a 163,2 s;
capturas de gameplay/final/selector revisadas en `finish-review-small.png`, ajustes y
21 saves restaurados. **No valida la solo:** la traza solo tiene fever0/2, solicitudes
de dueto 182/183/186 y ninguna 160–164. No se acepta por ello la entrada 17 ni el
dueto stock. Nueva prueba `gaso-fever-native-solo` en segundo plano mediante
`_work/gaso/fever-solo/run_solo_validation.py`: autoplay P2 desactivado exclusivamente
después del backup aislado, sin escrituras de puntuación, RNG ni progresión; capturas
adicionales si se observa fase7/fever1. Primer intento
`20261107T134334680723Z-gaso-fever-native-solo`: alcanzó fever1, anim102/req161,
pero abortó el capturador al reutilizar `solo-fever-016354.png`; el log registra cambios
de estado, no cada frame renderizado. Ajustes y 21 saves restaurados. Dos capturas
revisadas muestran el inicio, insuficiente para aceptar el movimiento completo.
Capturador corregido con contador de muestra en el nombre (regresión RED→GREEN en
`_work/gaso/fever-solo/test_solo_capture.py`). Repetición
`20261107T135026169853Z-gaso-fever-native-solo` completada sin error: fever1,
req162/anim103; log de versiones confirma `entry 17 -> BAG1 JP`. Salida de batalla
a 158,7 s y selector root13 a 166,7 s; ajustes y 21 saves restaurados/verificados.
Cinco capturas de solo y selector revisados en `solo-review-small.png`: personaje
visible y retorno correcto, pero muestreo insuficiente para certificar el movimiento
completo (no captura su vertical inicial). WAV estéreo 44.100 Hz, 301 s, conservado;
no se ha realizado aceptación subjetiva del audio. **Flujo solo comprobado, fidelidad
completa todavía pendiente:** siguiente comprobación con vídeo limpio continuo,
sin repetir calibración/build mientras no cambien sus entradas.
Las comparativas del visor
`20261107T082724-gaso-bag1` no bastan para aceptación: FEVER1 contiene escritorio al
inicio y no están sincronizadas. No se declara aún equivalencia visual ni de audio.

**Captura limpia y carga real (2026-11-07, equivalencia aún en revisión).** Visor aislado
`20261107T085957-gaso-bag1`, runtime sin cambios. `record_clean_fever.py` inicia
FFmpeg antes de seleccionar/reproducir y exige el foco confirmado por `focus.ps1`
(dos pruebas de rechazo/aceptación OK); `SetForegroundWindow` sin comprobar no lo
garantizaba y el primer intento aún capturó escritorio, conservado como inválido.
`selection-fever-82.mp4` muestra vertical/giro de cabeza y vuelta de pie, pero su
inicio incluye el movimiento anterior; `selection-fever-83.mp4` no permite confirmar
la vertical atribuida a FEVER2 en la referencia BAG1. Selección visible y comienzo
del movimiento no deben darse por sincronizados. Se conserva la incertidumbre:
ni una captura desfasada prueba un mapeo erróneo ni los datos correctos prueban la
reproducción completa. Fuentes 82/83: 437/450 frames según `animlib.frames`.
Comprobación independiente `loaded-fever-check.json` mediante VM_READ del proceso
propio: las animaciones completas del candidato 17 están en RAM (slots 0/1 en
offsets 1352428/1368924; slot 2 repite 0); las tres animaciones stock Bi-O no se
encuentran. Esto prueba carga, no el puntero activo ni fidelidad de reproducción.
Intervalo adicional `selection-fever-83-55s.mp4` completado (55 s, sin escritorio),
hoja reducida revisada: sigue sin verse claramente la vertical de la referencia
BAG1. La traza registra anim102 tras la última selección (f027090), correspondiente
al segundo clip; no se ha identificado por lectura el puntero de reproducción ni
sincronizado ambos vídeos. Antes de cambiar el mapeo hay que renovar/controlar la
referencia BAG1 FEVER2: su etiqueta seleccionada podría no certificar el clip que se
reproducía durante toda aquella captura. Es hipótesis, no error demostrado de la
referencia. FEVER1 sí muestra la vertical en la nueva captura, sin aceptar por ello
su ciclo completo. Visor cerrado mediante el helper: ajustes y saves originales
verificados. Audio, dueto y efectos de combate mantienen su aceptación pendiente.

**Resolución y verificación visual de fever solo (2026-11-07, fases 1, 2 y 5 de `plans/gaso-native-reference.md`).**
Referencia nativa BAG1 controlada (`runs/20261107T093427`, PID 52088) en Dance View Gas-O A:
selección directa de FEVER2 con una sola pulsación `Left` desde la lista en blanco (`---`),
sin reproducción previa. Grabación de 55 s (`controlled-fever2-from-blank.mp4`, 8.58 MB) con foco verificado.
Cierre verificado: 6 configuraciones y 21 saves originales intactos.
Hoja de contacto `controlled-fever2-55s-sheet.png` (8x7 a 1 fps) y comparativa lado a lado
`fever2-native-vs-bag2-controlled.png` (`compare_fever2_controlled.py`):
1. En BAG1 nativo, FEVER2 (anim 83) NO tiene vertical de cabeza ni breakdance invertido. Su ciclo
   de ~8 s consiste en pasos de pie, bombeos de brazos, bocanadas de humo (~3-4 s) y caída en freeze al
   suelo (mano derecha apoyada, torso inclinado, piernas extendidas horizontalmente) en los segundos
   7, 15, 23, 31, 39, 47, 55.
2. La vertical invertida con giro de cabeza (headspin) pertenece EXCLUSIVAMENTE a FEVER1 (anim 82). La
   aparición de un headspin al inicio de FEVER2 en el barrido inicial de 67 opciones se debió a que se
   grabó inmediatamente después de FEVER1 mientras el motor completaba la transición residual previa.
3. En BAG2, el candidato entrada 17 slot 1 (visor índice 83 / anim 83) en `selection-fever-83-55s.mp4`
   reproduce idéntico ciclo y el mismo freeze en el suelo (segundos 9, 25, 41, 57).
4. Queda resuelta la duda del propietario: las fevers solo de Gas-O (FEVER1=82, FEVER2=83) son fieles
   y exactas a BAG1 nativo. Los problemas percibidos se originaron en la ausencia previa de la entrada 17
   (que reproducía el fever stock de Bi-O retorciéndose de espaldas) y en el fallo previo de off-by-one en
   los doubles de baile (que filtraba la anim 82 en los bailes regulares).
Quedan pendientes: aceptación subjetiva de audio, fevers de dueto (entrada 35 stock), y las fases 3 y 4
de referencia de combate (humo y tanque).


**Referencia nativa Dance View BAG1 (2026-11-07, plan `plans/gaso-native-reference.md`
fase 1).** Runtime nativo aislado (`_work/gaso/native-reference/native_session.py`,
run `runs/20261107T072746`, tarjetas copiadas, Load Data → Dance View desbloqueado),
Gas-O A: 67 opciones catalogadas con 3 capturas cada una en
`_work/gaso/native-reference/danceview/gaso-a-catalog.json` (+ `labels.png`), vídeos
continuos FEVER1/FEVER2. **FEVER1 nativo de Gas-O empieza con break dance de cabeza y
vuelve a pararse girando** (ciclo ~16 s): la secuencia que el propietario notó en BAG2
es la original, pendiente de comparar clip a clip en BAG2 (fase 2). Cierre: configuración
y saves originales verificados. Nota técnica: gdigrab por título graba negro; usar la
región cliente del escritorio (`window_rect.ps1`).
Diagnóstico posterior: MCP ghidra-028 confirmó los límites de carga P2 en
800337B8/80033F14; no identifica aún la instrucción responsable. Se lanzó una
repetición instrumental `gaso-pair-loader-dump` con `--ram-dump-frame 9000`,
GasP1/B contra GasP2/A: falló en190.496s, restaurando tres configuraciones y21saves.
Dump2MiB conservado en `20261106T215340489151Z-gaso-pair-loader-dump/`, SHA256
`1b415ae413842c417af64b90560b11b694aea1eb5525c9afbd0dffc687773c2d`.
`audit_pair_loader_dump.py` confirma estado11, destinos separados80200000/80300000,
actorP1 publicado80256AB0 y actorP2 esperado80356A40 todavía no publicado;
las seis rutinas parcheadas init/event/post coinciden con el candidato en RAM.
Los actores están fuera del dump2MiB: no se infiere su contenido. Se amplió el
harness con `--ram-dump-size 2mb|8mb` (default2mb), manteniendo el filtrado de
flags heredados; RED por ausencia de tamaño explícito y GREEN50tests. Baselines
previos `versus-session-before-8mb.py`/`versus-tests-before-8mb.py`.
Captura8MiB terminada: `20261106T215858020561Z-gaso-pair-loader-8mb`, fallo de
carga189.226s, tres configuraciones/21saves restaurados. Dump SHA256
`63136ec917643e882a22acfbc457c57b376b91b3824f7ed8ad0d9371064fc21c`.
Auditoría adyacente: actorP1 válido con101clips; actorP2 esperado80356A40 tiene
cabecera/punteros cero y aún no está publicado. `p2-model-comparison.json`
confirma que los354880bytes del DFS P2 en80300000 son idénticos al candidato.
No se modificaron fuentes del juego ni escala.

MCP ghidra-029: el cargador llega al estado11; 80033F14 registra primero el
banco SEDT mediante8002E08C→8002DE5C, antes de inicializar al actor P2. No hay
PC/registros vivos en este dump: no demuestra bloqueo dentro de esas funciones.
El banco P2 apunta a80359FDC, offsets20/9268/119380,13entradas; contador global
60 y5bancos. Las comprobaciones visibles de capacidad de8002DE5C no muestran
un desbordamiento con esos valores; quedan por comprobar registro/transferencia
VAB y flujo vivo. `p2-sound-bank-comparison.json` confirma además que los119488bytes
del SEDT principal P2 coinciden íntegramente con el miembro3 del pack54; el segundo
SEDT del pack no se espera en ese mismo puntero. No se atribuye el fallo al audio
ni al parche DBI sin prueba.
Siguiente diagnóstico: localizar PC/pila de ejecución durante el bloqueo y
contrastar el banco P2 completo con su fuente; no repetir partidas exitosas ni
modificar escala o sonido como conjetura.
El humo sigue sin adaptación; completar la matriz técnica no lo subsana.

Intento de captura CPU terminado: wrapper `_work/gaso/capture_pair_cpu.py`, tag
`gaso-pair-live-cpu`, reutiliza la sesión aislada sin editar su implementación.
Ante el fallo consulta únicamente el listener TCP cuyo propietario es el PID
verificado del juego de prueba: tres muestras get_registers/read_ram(pila256).
No pausa ni escribe RAM; guarda `live-cpu-capture.json`, incluidos errores o
ausencia de listener. El PC puede corresponder a un punto seguro del scheduler,
no a la instrucción que originó el fallo. Comprobación de framing host pasada;
primer intento inline de esa comprobación falló por comillas, corregido sin
cambios de producto. Resultado `20261106T221745384011Z-gaso-pair-live-cpu`:
falló193.496s, tres configuraciones/21saves restaurados. El JSON no contiene
registros: `owned_listening_ports=[]`. Comprobación posterior del build verificado:
`build-win-codex/CMakeCache.txt` tiene **PSX_DEBUG_TOOLS:BOOL=OFF**, y main.cpp
compila debug_server_init solo sin PSX_NO_DEBUG_TOOLS. La disponibilidad del código
fuente no implicaba un servidor en el ejecutable: esta prueba no obtuvo PC/pila
y no se debe repetir sin cambiar el mecanismo de captura. Próximo paso: usar
instrumentación acotada de entradas/salidas de funciones del cargador mediante
la API de plugins disponible, o un build diagnóstico separado; mantener intacto
el candidato instalado hasta verificar el cambio diagnóstico.

Análisis sin otra partida: `scan_loader_stack_candidates.py` inspecciona los
últimos8KiB de la RAM8MiB conservada y cruza palabras con retornos JAL del main.
`loader-stack-candidates.json` encuentra807FFEA4→8002E060 (llamada80049F94),
807FFEF4→8002E100 (8002DE5C),807FFF08→80033F44 (8002E08C),
807FFF38→800348C4 (80033F14). MCP ghidra-031 confirma80049F94=SystemError.
Son candidatos compatibles con la ruta de error del registro VAB, **no unwind
validado**: no se conocen SP/PC vivos y pueden quedar retornos históricos.
Siguiente evidencia requerida: observar argumentos a0/a1 al entrar SystemError
y su RA, sin interceptar/suprimir el error ni cambiar capacidades de sonido.
Un primer comando inline de extracción falló por quoting de PowerShell;
se sustituyó por el script determinista, sin cambios del juego.

Humo: `_work/gaso/entrance-event-audit.json` confirma que el clip nativo62 y
el humo de entrada brotan durante los primeros 500 frames con partículas cian-blancas.
Tanque gigante translúcido de 8 segmentos implementado en `bag2jp_gaso_tank.h`
encerrando al rival con aturdimiento de pie sin derribo (animación 78).

Retrato HD y Color de Fondo Independiente por Jugador (2026-11-08, verificado con evidencia visual):
- Retrato HD de Gas-O activado mediante alternancia de la entrada 235 del CLUT en RAM a 0x7FFE
  (hash 61E197B20D89CB1E) y subida a VRAM con `psx_mod_psyq_load_image`.
- Color de fondo independiente por jugador implementado en `cs_char_name_hook` (0x80093474):
  se escribe en la pila de CPU ($sp + 0x28) el color correspondiente a cada jugador según su
  versión activa (Gas-O = verde tóxico 0x0030E020; Bi-O = azul/morado 0x00904840).
- Verificado empíricamente con captura real (`_work/gaso/evidence/indep_bg_check/full_selector.png`):
  cuando 1P selecciona Gas-O y 2P se posiciona sobre la casilla de Bi-O, 1P conserva íntegro
  su fondo verde tóxico y su retrato HD de Gas-O, mientras que 2P muestra su fondo azul original
  y el retrato de Bi-O, demostrando independencia total y cero interferencias entre jugadores.
los slots convertidos72/73 conservan eventos tipo1:2/5 en46, **1902 (0x76E)
en47**,1/4 en70; sonido tipo2 en47 correctamente rebased6144→26880.
El stub actual descarta esos eventos. En la DBI JP correctamente reubicada,
`801D59A8` maneja76E, activa92E0 e inicializa cuatro grupos de ocho partículas
mediante `801D7C04`. `801D60C4` actualiza/dibuja esos cuatro grupos con
`801D7E6C`: velocidades, desvanecimiento, crecimiento y16frames UV; llama al
renderer nativo800330DC. Es una ruta concreta compatible con el humo observado,
pero falta comparación visual nativa y traducción BAG2 del renderer/textura,
escala, coordenadas, pausa y ciclo de vida. No copiar direcciones/actor43BC de
BAG1 ni reactivar Bi-O; habilitar solo el disparador no dibujaría el efecto.
Decompiles/logs en `native-smoke-decompile/`, `native-smoke-lifecycle/`.

Siguiente unidad: compilar/desplegar el cambio mínimo de escala con backups y
probar visualmente ambos lados/trajes frente a Strike. Continuar la adaptación
del efecto nativo por separado, con regresión del evento47/ciclo de vida y
aceptación temporal en juego. La estabilidad general sigue pendiente.

### Estado actual: prueba del candidato con eventos neutralizados

**Resultado posterior y corrección del propietario:**
`_work/versus-runs/20261106T204943160205Z-gaso-event-full-review` terminó
`complete_awaiting_visual_review` en289.858s; volvió al selector y restauró
tres configuraciones y21saves. El agente revisó gameplay, seis capturas durante
la canción y returned-selector (`motion-review-small.png`): hay distintas poses,
pero no constituyen comparación de fidelidad contra BAG1 nativo.
El propietario rechaza la escala actual: Gas-O demasiado grande respecto a
Strike BAG1; además falta el humo de entrada. Estos dos requisitos quedan
abiertos; terminar la partida no acredita una versión estable.

El código actual aplica corrección Q12 solo a Strike (`b1v_scale_q12[1]`);
Gas-O no tiene ajuste específico y conserva la escala del slot Bi-O. Eso señala
el punto de ajuste, no demuestra todavía el factor correcto. Medir contra
escala/proporción BAG1 antes de elegir un porcentaje; ajustar uniformemente,
sin deformar el esqueleto. El callback de eventos Gas-O está neutralizado por
completo: puede explicar efectos ausentes, pero falta trazar el humo nativo.
No reactivar el manejador Bi-O para recuperarlo. Próximo objetivo: escala
relativa fiel y humo de entrada mediante eventos Gas-O compatibles; validar
ambos lados/trajes y repetir canción/fever/retorno después del cambio.

Investigación de escala posterior: dumps `_work/bag1/scus.bin` y
`_work/mainexe/slpm.bin` son imágenes crudas con base80010000, sin headerPS-X
de800bytes. Una primera lectura añadió ese header erróneamente y devolvió datos
ajenos; corregida sin modificar fuentes. Bytes de tablas históricas558FC/51904:
BAG1 Strike127/Gas116; BAG2 Strike98/Bi-O98. Aún falta confirmar consumo/región
y derivar el factor junto con las conversiones/modelos; no aplicar un porcentaje
solo por esos bytes. No se cambió la escala ni el humo durante esta consulta.

Consulta paralela del propietario, nombres para HD: imágenes del selector BAG2
verificadas en `assets/archive/system/015.bpe/content/041.png` (Tsutomu, Comet,
Bi-O, Strike, Shorty, Pander, Michael Doi, Capoeira), `042.png` (McLoad,
Sushi Boy, Heat, Kelly, Hiro, ChiChi & Sally), `043.png` (Hustle Kong,
ChiChi & Sally, Robo-Z Gold, Columbo). Tamaños192x256/192x256/192x201;
TIM originales con igual basename. Son atlas; conservar disposición y alfa.

El candidato `gaso-event-patch` está desplegado únicamente en experimental;
payload SHA256 `5b618e35205cf69332658bede4a3cab733973239b4567a1d36a8ab011d6c704b`.
El parche DBI sustituye init/postprocess y devuelve cero en el callback de
eventos Bi-O. Es un experimento: neutraliza también eventos cuya adaptación
Gas-O queda pendiente; no acredita fidelidad completa ni estabilidad.
La explicación anterior de «saltos sin reubicar» no basta como causa probada:
los destinos J/JAL dependen de su PC y los logs de eventos no son una traza
de instrucciones. El retorno PC cero anterior sigue siendo salida anómala,
no prueba de final normal de canción ni de ausencia de corrupción.

Calibración nueva `_work/versus-runs/20261106T204654564342Z-gaso-event-probe`:
ocho destinos revisados visualmente por el agente (no aceptación humana del
personaje), runtime `7c937eed1bf66fd95aa03b4f14440e8b855295923530f35f7dda3ad1b4b4ca41`.
Restauración de tres configuraciones y21saves verificada. Partida
`gaso-event-full-review` lanzada con Gas-O BAG1/A P1 y Strike BAG1/B P2,
StrikeBAG1, `--finish`; pendiente resultado, revisión temporal de capturas y
retorno al selector. No iniciar otra partida mientras siga activa.

Los párrafos siguientes describen el primer despliegue y fallos históricos;
no sustituyen este gate de aceptación pendiente.

Compilación `gaso-regional-stable` terminada correctamente (returncode0),
con dos jobs y pins existentes; el nombre del tag **no acredita estabilidad**.
Log: `_work/workflow/20261106T174606450658Z-gaso-regional-stable/build.log`.
Se desplegaron y verificaron por SHA25625archivos: ejecutable y paquetes
`bag2jp.feature.bag1-content`/`bag2jp.content.bag1-visuals` en
`D:/Games/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb`. No había juego abierto.
Backup de ejecutable/paquetes anteriores y reporte por archivo:
`_work/gaso/deployment-backup/`. Settings, keybinds, input, game_options y
mods/state se respaldaron y sus cinco hashes permanecen intactos; no se tocaron
memory cards ni la instalación estable `BAG2JP-win`.

Payload397174991e41b8f2959d937ede7dbfa98db8b4927a837e8fe454a567ef708583,
28filas con variantes JP presentes; capacidad DUMMY comprobada independientemente
en `_work/gaso/dummy-capacity.json`:9873408/27648000bytes. Nueve FLAC disponibles
para los tres perfiles y opciones regionales/CD. Strike/Gas CD siguen pendientes
de escucha, con los límites ya documentados abajo. Host visual5/5 y audio4/4
pasaron antes del build; no sustituyen prueba en juego.

**Límites del candidato:** stages200/209 reutilizan los mismos bytes portados
en ambas opciones (Heat desde DBI USA, Strike desde DBI JP); esto no demuestra
port JP/USA de sus DBI. Gas stage197 queda fuera del payload; eventos/id9 aún
pendientes. No presentar esas opciones como dos stages nativos ya completados.

**Siguiente gate, del propietario:** abrir el experimental y probar modelos
JP/International de Heat/Strike/Gas-O (ambos lados y trajes), selección de
canciones Japanese/International/CD, fever, canción completa y vuelta al selector.
El agente se detuvo antes de abrir el juego por petición expresa. No hay prueba
post-despliegue ni aceptación estable. Los apartados siguientes conservan las
evidencias históricas de preparación, no describen el estado actual del despliegue.

### Fallo visual observado: Gas-O no aceptado

El propietario señaló esqueleto/movimientos incorrectos. Revisión directa del
agente: `_work/versus-runs/20261106T175400496853Z-regional-gaso-strike-full/review-sheet.png`
muestra Gas-O invertido ya en el checkpoint gameplay inicial. Captura adicional
del PID experimental32840 en `_work/gaso/motion-review/motion-sheet.png` muestra
el cuerpo invertido/plegado junto al suelo; seis imágenes con pose idéntica no
constituyen evidencia temporal de una animación completa. Strike erguido.
No atribuir todavía la causa al esqueleto: falta aislar jerarquía/modelo frente
a clip/remapeo, región y fase. El builder usa `_work/gaso/test_001.bin` para
los cuatro modelos y convierte modelos A2/A4 también en P2; son seams que
investigar, no causas demostradas. La política sigue `proposed`.

La partida terminó técnicamente (`complete_awaiting_visual_review`,282.371s),
con restauración verificada y21saves intactos; **RECHAZADA visualmente**, no
aceptación de fidelidad. No confundir canción/retorno completados con animación
correcta. No se aplicó ninguna corrección especulativa. Siguiente paso: reproducir
clips/roles iniciales con capturas separadas y comparar modelo/animaciones con
fuente BAG1 nativa antes de modificar jerarquía o rotaciones.

Diagnóstico posterior: `_work/gaso/diagnose_model_motion.py` verifica directamente
entry89 JP del payload desplegado contra P_GAS_A2.DFS JP. Modelo41nodos coincide
con el convertidor; jerarquía intacta. Motions coincide con test_001.bin y con
regeneración actual. Slots0/67/68/71/72/73/94/98/99 conservan los bytes de canales
del clip BAG1 asignado (no prueba que la asignación semántica sea correcta).
Evidencia `_work/gaso/model-motion-diagnosis.json`. No descarta un error común
del convertidor ni diferencia entre intérpretes BAG1/BAG2.

Ghidra MCP confirmó tablas de Bi-O:80053600→801CEDBC,
80053568→80052824,80053698→801CF1B0. Los dos destinos801C están **sin inicializar**
en el principal abierto; no hay análisis válido de sus efectos todavía.
`skeleton-hooks-ghidra.json`, log ghidra-022. Captura runtime en curso mediante
versus_session, tag `gaso-skeleton-runtime`: terminó146.774s, restauración
verificada de ajustes y21saves, pero **no produjo dump**. Causa comprobada:
Session.start elimina todas las variables BAG2JP heredadas; frame superó8547.
No repetir ese comando confiando en el entorno.

Añadido `--ram-dump-frame` explícito al arnés, conservando el filtrado de otras
variables debug. Regresión contra Popen: RED None≠7500 antes, suite50tests GREEN
después (`PYTHONPATH=tools/test`, `py -3.13 -m unittest test_versus_navigation`).
Baseline previo `_work/gaso/versus_session-before-ram-dump.py` preserva cambios
anteriores. Captura `gaso-skeleton-ram-explicit` terminada147.097s: restauración
verificada y21saves intactos. Dump2MiB conservado en su carpeta de evidencia
`_work/versus-runs/20261106T180912132410Z-gaso-skeleton-ram-explicit/`, SHA256
`1c3e1a97867d57678088a533111e37e690c96d04f14c842e5ba64499bab092e7`.
Trace alrededor de7500: P1ch9 anim71/WAIT nativo60, fase1/2/3, fever0.

**Incompatibilidad concreta de bindings:** el builder conserva el DBI Bi-O sin
adaptación. Su inicializador801CEDBC escribe la tabla actor+7CC; comparado con
el inicializador nativo Gas-O JP (DBI miembro3, función file+50), difieren21de
las primeras30posiciones, incluyendo huesos4/5 sin canal y canales desplazados.
`binding-initializer-comparison.json` conserva hashes y valores; las posiciones
no escritas se representan comoFF (preinicialización BAG1 aún por contrastar).
MCP sobre el principal confirmó que80031D3C borra30bindings aFF y llama al
inicializador del personaje;8002BC38 entrega esa tabla a80012B9C para la pose.
La preservación de clips/modelo no evitaba esta incompatibilidad del consumidor.

Complemento Ghidra headless sobre copias, **no reemplazo del MCP**: proyecto
aislado `_work/gaso/gaso-runtime-hooks`, RAM cruda base80000000 PSX LE32 y DBI
nativo a base0 (direcciones de archivo, no runtime BAG1). GUI original intacta.
Decompilados `runtime-hook-decompile/{801cedbc,801cf1b0}.c`,
`native-hook-decompile/50.c`; comandos/logs ghidra-023. Callback801CF1B0 además
copia transformaciones de nodos19/22 a23/24/25/26/27 (strideB0): corregir solo
bindings no acredita compatibilidad de todo el DBI Bi-O.

Consumidor80012B9C confirmado por MCP (ghidra-024): recorre30huesos y usa
cada byte de la tabla para seleccionar el canal que genera su pose; FF/canal
ausente omite esa transformación. Evidencia `binding-consumer-ghidra.json`.
La comprobación directa del actor con `audit_live_binding.py` falló de forma
acotada: actor+7CC=8025720C queda fuera del dump2MiB. No acredita todavía la
tabla viva ni permite atribuir toda la inversión a esta incompatibilidad.

Comparación nativa ampliada:8packs USA/JP×trajeA/B×ladoA/B; dentro de cada
región el inicializador es idéntico. Entre regiones cambia el código, pero las
35asignaciones descompiladas coinciden (`native-binding-variants.json`). Corregida
la lectura del delay slot de retorno del extractor: las21diferencias principales
no cambian. No prueba todavía la preinicialización nativa.

Localizada además la base virtual nativa JP del archivoDBI:801D587C, corroborada
por dos tablas del ejecutable (init801D58CC y candidato postprocesado801D6204,
P2desplazado3AB8). `native-callback-layout.json` conserva palabras/hashes. Una
segunda importación headless aislada con esa base resolvió los saltos absolutos
que daban avisos con base0. El candidato postprocesado nativo contiene **siete**
bloques de copia de transformaciones, distintos de los **cinco** de Bi-O. Por
tanto no basta con cambiar la primera tabla y declarar el personaje corregido.
Queda verificar llamador/orden y traducir el layout nativo al de BAG2.
La envoltura JSON de la consulta anterior del consumidor fue reemplazada por un
nombre fijo del probe; su C/texto original sigue íntegro. Usar
`binding-0x80012b9c.c`; el probe ahora separa reportes por dirección (ghidra-025).

Siguiente: confirmar llamador/preinicialización nativa y traducir postprocesado; preparar
regresión y adaptación mínima compartida basada en datos, con guards del DBI,
después prueba controlada de pose/movimiento. No se corrigió ni redesplegó el
juego; esta incompatibilidad no demuestra por sí sola toda la causa visual.

### Pruebas posteriores al despliegue: navegación

El propietario autorizó al agente a ejecutar las pruebas. Probe
`_work/versus-runs/20261106T175201938738Z-regional-deployed-probe`:
89.155s, estado `calibrated_awaiting_visual_review`, restauración verificada
de tres archivos y21saves originales. Revisión visual del agente en
`probe-review-small.png`: Heat/Comet/Strike/Shorty/Bi-O coinciden con las ocho
aristas y P2 permanece en Comet. Catálogo aceptado con el helper y ligado al
SHA del ejecutable9ee82097e4a9c7c76f5a22d7f65427ff4d14479783bce53802b5b3f8b3501c6d;
es revisión del agente, no aceptación humana de fidelidad/estabilidad.
Se lanzó `regional-gaso-strike-full` (Gas-O BAG1 A vs Strike BAG1 B,
StrikeBAG1, --finish); resultado pendiente. No relanzar mientras siga activo.

## Phase 6 resume

- Preflight aprobado: `_work/workflow/20261106T152215858743Z-gaso-stage-resume/`.
  Sin staging/deploy ni ejecución nueva del juego en esta continuación.
- Ghidra MCP real, `get_program_info` primero, SLPM_862.19 JP principal:
  tablas confirman stage9→197, callbacks801E25C4/25CC/25F8/2618 y
  chart801E266C. Evidencias `_work/gaso/stage-ghidra-resume.json` y
  `stage-profile-audit.json`; log ghidra-019. No overlay cargado verificado.
- Candidato experimental regenerado con el builder compartido:
  `_work/stage_import/gaso/resume-audit/gaso_197.dfs`,545948bytes, SHA256
  `9cda85c90e63de117f8d20fffd2be35ab6600b836598a79845d268bf6885e188`.
  Cero llamadas sin mapear, modelo `{1:32,3:1}`. Esto **no** acredita la
  equivalencia semántica de los destinos de llamadas/globales.
- Cinco tests host verdes: `wsl.exe -d Ubuntu --exec python3 -m unittest
  tools.test.test_stage_port`. Heat conserva bytes admitidos; Strike conserva
  sus invariantes. Gas-O conserva texturas, banco nativo0 y cola stock posterior
  al chart. Regresión RED→GREEN: un callback desplazado4bytes dentro de la
  imagen se rechazó tras añadir validación contra las tablas del ejecutable.
- Fuente ST_GAS USA frente JP: solo cambia DBI, resto de miembros idénticos
  por hash (`stage-profile-audit.json`). El perfil actual mezcla DBI USA con
  ejecutable/chart JP: no publicarlo como variante regional íntegra sin auditar.
- jPSXdec decodificó DANCEXA2 canal1 de ambos discos: stereo37800Hz,
  5779872frames,152.9066667s; sectores2336bytes,2867sectores audio.
  ADPCM y PCM **difieren** entre USA/JP, por lo que no se deduplican.
  `_work/gaso/audio-region-audit.json` contiene hashes de fuentes y resultados;
  WAV en `_work/gaso/audio-{jp,usa}/DANCEXA2.XA[1].wav`.
  Tabla de duración BAG1 JP800553F4[9]=150s, SHA del ejecutable en reporte.
  Pendientes: confirmar ruta nativa id9→archivo/canal y escucha humana;
  duración decodificada no equivale a duración de batalla. No hay FLAC desplegado.

### Siguiente acción y gate

1. Decisión del propietario (2026-11-06): selector **BI-O / GAS-O**, nunca tres
   versiones regionales en ese selector. Crear **mod aparte** de variantes BAG1,
   siguiendo el flujo existente de mods, para elegir modelos Internacional/JP
   y asimismo escenarios. La propuesta de región ligada al selector queda
   rechazada. Granularidad aprobada: dos opciones globales independientes,
   modelos y escenarios; ambas inicialmente Japonés.
   Patrón existente: `mods-src/bag2jp.localization.regional/1.0.0/manifest.toml`
   (opciones `choice`, valores `international`/`japanese`, carga siguiente pantalla).
2. Auditar equivalencias de funciones/globales del perfil y song mapping nativo.
   Usar funcmatch para equivalentes del ejecutable principal y confirmar en
   Ghidra; no aplicar a overlays ni fiarse solo de coincidencias de bytes.
3. Completar integración en el motor compartido: el candidato musical ya cubre
   ambos archivos XA y stage9; el código de eventos del escenario sigue
   limitado a stage0/1. Auditar duración USA, escuchar edits CD y wiring del escenario
   antes de construir/desplegar; no basta añadir una fila musical de perfil.
4. Incorporar JP real, selector y eventos por score; preservar Heat/Strike,
   restauración de duración/configuración y guard B1ST. Validar en instalación
   experimental ambos lados/trajes, eventos, canción completa y retorno.

No fase6 aceptada, build runtime nuevo, snapshot ni checkpoint en esta continuación.
Los cambios previos del árbol y `active_task` de Strike se preservan.

### Heat/Strike incluidos: preparación musical regional

- Se extrajeron con jPSXdec los canales0/1 de DANCEXA1 JP y USA y se
  contrastaron subheaders2336bytes, ADPCM, PCM y muestras. Los dos temas
  difieren entre regiones; no deduplicarlos. Heat138.026667s ambas regiones;
  Strike JP132.053333s frente USA137.013333s. No confundir estos finales de
  archivo con las tablas de duración de batalla: falta auditar la tabla USA.
- `_work/gaso/shared-music-audit-v2.json` conserva fuentes, hashes y sondeo CD.
  El primer ensayo asignó incorrectamente Transform a Strike: cero ventanas
  fiables; queda retenido en `shared-music-audit.json`. Se corrigió a Power,
  pista12, con5ventanas PCM>=0.6 por región. Heat2Bad:9por región.
  Chemical Love tiene correlación de envolvente alta pero PCM<0.6: no declararlo
   desalineado ni aceptado por ese único umbral. Edits abajo; escucha pendiente.
- Se prepararon **seis FLAC experimentales** en
  `_work/gaso/regional-music-candidate/`: heat_2bad/strike/gaso ×
  japanese/international. `report.json` valida hashes, stereo44100Hz y duración
  preservada. Son XA remuestreado, **no calidad CD**; no desplegados.
- Heat ya dispone de CD adaptado, pero su adaptador histórico mezcla una cola
  XA; no extenderlo ciegamente a Strike/Gas-O. Fuente CD Strike real:
  `assets/music_cd/Bust a Move/12 Power.flac`; fuente Gas-O pista06.
- Wiring existente auditado: `psx_mod_option_value` permite consultar
  `bag2jp.localization.regional` / `regional` / `songs` explícitamente sin
   otro selector ni cambio del framework. El candidato musical que se describe
   abajo sustituye la opción antigua; todavía no se ha desplegado.
- Diseño aprobado para el mod visual: **dos opciones globales independientes**,
  modelos y escenarios, ambas Internacional/JP. El propietario corrigió el valor
  inicial a **Japonés para ambas** («Que Inicialmente sean su versión japonesa»).
  No se añade granularidad por elemento ni versiones regionales al selector de
  personajes. Canciones conservan su ajuste independiente en el mod existente.

Audio CD, aclaración posterior del propietario: usar el **mod de canciones
existente**, `Internacional / Japonés / Calidad CD`. No crear otro selector de
audio BAG1; el nuevo mod aparte es para modelos/escenarios. El antiguo ajuste
`bag1_song_audio=cd|game` no era la interfaz solicitada. Se retira del manifest
candidato; los ajustes personales guardados no se borran ni se reescriben.

### Candidato musical compartido: host, no desplegado

- `bag2jp_bag1_stage.c` consulta explícitamente `regional/regional/songs`
  del paquete `bag2jp.localization.regional` para Heat, Strike y Gas-O.
  Usa sufijos `japanese` / `international` / `cd`; opción ausente/inválida
  vuelve a Japanese, coherente con el default del mod existente. Esto no liga
  el audio a las opciones visuales. El valor antiguo BAG1 deja de gobernarlo.
- Filtro por perfil, extent BUST2_01/BUST2_02 y canal; conserva guard B1ST,
  gameplay/Dance View y filtro anterior. Añade stage9/canal1 y duración JP150s;
  restaura solo sus propias sobreescrituras. Recursos ausentes o formato no
  compatible no sustituyen PCM ni se disfrazan de calidad CD.
- RED observado: el test de nueve combinaciones falló en nombre de archivo con
  el código anterior. El test del manifest falló por el selector duplicado.
  GREEN: **4 tests host**, registro `_work/gaso/regional-audio-tests.log`,
  comando, hashes y tiempo en `regional-audio-tests.json`. Cubren nueve rutas,
  extent/canal equivocado, stock, Dance View, opciones ausentes/inválidas,
  archivos/extent ausentes, decoder inválido, seek/EOF y restauración.
- Cambio propio separado del trabajo anterior mediante copias de partida en
  `_work/gaso/regional-runtime-start/`; no se ha modificado el árbol de build
  ni la instalación. Falta compilar el plugin completo y aceptación en juego.
  El mod visual separado y los recursos JP de modelos/escenarios siguen
  pendientes; su diseño/default Japonés ya está aprobado, no volver a pedirlo.

### Mod visual regional: candidato host

Creado `mods-src/bag2jp.content.bag1-visuals/1.0.0/manifest.toml`: dos opciones
globales `models`/`stages`, ambas `japanese` por defecto; canciones y selector
BI-O/GAS-O no se modifican. `bag2jp_bag1_versions.c` consulta ese paquete
explícitamente y cambia offset **y tamaño exactos** de DF2 para la próxima carga.
Las cuatro combinaciones regionales son independientes; restaura entradas propias
y no pisa offsets ajenos. Una variante JP ausente no se sustituye por USA.

El generador compartido `make_alt_entries_exact.py` admite por fila
`regions: {international: ruta, japanese: ruta}` en lugar de `file`, registra
ambos hashes/tamaños y deduplica bytes idénticos. Las filas legacy conservan su
payload; `jp_size=0` significa **no disponible**, no equivalencia regional.
El índice actual se migró de esquema sin cambiar sus28filas, offsets ni tag;
todavía tiene **cero variantes JP**. No se regeneró ni desplegó el payload.

**Bloqueo de integración:** no compilar/desplegar este candidato como importación
utilizable hasta completar las filas JP reales y verificar conjuntamente la
selección BAG1, buffers y hooks de personaje. El fallback DF2 a stock ante un
hueco JP está probado aisladamente, pero no acredita coherencia con esos hooks.

Cinco pruebas host: `py -3.13 -m unittest -v tools.test.test_bag1_visual_regions`;
log/hashes/tiempo en `_work/gaso/visual-region-tests.{log,json}` mediante
`check_visual_regions.py`. Compila el vblank real y el tipo del índice real con
gcc/WSL; runtime/DF2 sintéticos, no juego. Prueba inicial: warning de stub sin usar
impidió compilar; corregido el harness, RED por seleccionar USA con JP pedido,
después GREEN. Incluye opciones inválidas/ausentes, JP faltante, límites de tabla,
stock/restauración, metadatos y empaquetado/deduplicación. No full-plugin build.
Baselines previos intactos en `_work/gaso/visual-runtime-start/` (tres archivos
ya modificados antes de esta tarea). Preflight pasó; Ghidra real confirmó el
principal JP y permitió lecturas acotadas de loader/tabla, log ghidra-020.

Siguiente unidad: generar recursos JP reales con motores compartidos y perfiles
Heat/Strike/Gas-O; no volver a pedir los defaults aprobados ni repetir las
pruebas sin cambios. CD/listening, semántica/eventos Gas-O y aceptación siguen
pendientes por separado.

### Inventario regional USA/JP (fuentes y miembros de salida)

Scripts deterministas `_work/gaso/inventory_regional_sources.py` →
`regional-source-inventory.json` y `map_output_members.py` →
`output-member-map.json`. Sin generar recursos, build ni despliegue.

| Personaje | Packs (miembros que difieren JP) | Modelos | Escenario |
|---|---|---|---|
| Heat | #1/#2 TIM etiqueta, #3 DBI, #6 TIM cuerpo (mismo tamaño, filas56–72 + CLUT) | idénticos | solo #0 DBI |
| Strike | #1/#2, #3 DBI, #5 TIM cuerpo (CLUT10→8 filas) | A2/B2 y A4/B4 distintos | solo #0 DBI |
| Gas-O | #1/#2, #3 DBI, #5 TIM cuerpo (mismo tamaño, filas0–16 + CLUT) | A2/B2 distintos, A4/B4 idénticos | solo #0 DBI |

Las diferencias de censura son reales en texturas de cuerpo y mallas: las
variantes JP deben **re-derivarse** con los mismos transformadores, no copiarse.
Mapa de salida (índice actual de28filas = `combined_spec.json` Gas-O):
TIM de cuerpo aparecen en salida como copia exacta (Strike) o retarget con
píxeles iguales (Heat/Gas-O); modelos y DBI de escenario están convertidos
(sin coincidencia directa). Etiquetas #1–#3 de pack no aparecen tal cual.
Limitación: el mapa asoció P1/P2 al traje A primero; confirmar lado B al derivar.

Plan de derivación JP (pendiente): por miembro de salida derivado de un miembro
fuente que difiere, aplicar la misma transformación con la fuente JP (copia
exacta o `tim_retarget` sobre la cabecera de salida); modelos Strike/Gas-O por
`model_bag1_to_bag2.convert`; DBI de escenario por el conversor de escenario.
Miembros idénticos y modelos Heat/Gas-O B4 se deduplican por hash. Generalizar
`build_gaso_assets.py` (rutas USA fijas) mediante el perfil `regions`, sin clonar.

**Gas-O JP generado (candidato host, 2026-11-06).** `build_gaso_assets.py
--region usa|jp [--out-dir]` lee extracción y carpetas de packs del perfil.
`_work/gaso/verify_gaso_regional_build.py` → `_work/gaso/regional-build/{usa,jp}`
y `report.json`: salida USA **idéntica byte a byte** a los 8 candidatos
existentes; JP difiere solo en body TIM2 (miembro 3 P1 / 2 P2, fuente #5) de los
4 packs y en el miembro 0 (modelo) de 89/90; 161/162 idénticos (A4 igual).
Portrait/DBI siguen siendo stock Bi-O, por eso las etiquetas JP no entran.
Límite heredado: 90/162 (P2) usan el modelo A2/A4, no B2/B4. Sin payload,
build ni juego. Pendiente: derivar Heat/Strike y DBI de escenario JP.

**Heat/Strike JP generados (candidato host, 2026-11-06).** Herramienta
compartida `tools/bag1import/build_regional_variants.py <perfil> <dir-nuevo>`
con perfil de recetas `profiles/regional_variants.json` (16 entradas; reglas
`copy`/`retarget`/`convert_model`). Exige que cada miembro fuente que difiere
entre regiones lo consuma una regla o esté ignorado (labels/DBI BAG1 del pack) y
que la receta International reproduzca **byte a byte** el candidato actual antes
de escribir JP. Salida `_work/gaso/heat-strike-regional/{international,japanese}`
+ `report.json`: las 16 reproducen USA. JP cambia: Heat packs miembro4 P1/3 P2
(body retarget); Heat modelos sin cambios (fuentes idénticas); Strike packs
miembro3 P1/2 P2, −64bytes (CLUT10→8 filas); Strike modelos miembro0 (−176/−104
bytes). Fever 22/40 se tratan como región-independientes (inferencia, no
mapeo de fuente probado). Sin payload, build ni juego. Pendiente: DBI de
escenario JP (200/209/197) y spec `regions` completa (filas sin cambio también
como `regions` con el mismo archivo, nunca `file`, o el default JP cae a stock).

### Edits CD Strike/Gas-O: candidatos generados

`_work/gaso/cd-edits-candidate/`: **strike_cd.flac129s** y **gaso_cd.flac150s**,
FLAC44100Hz estéreo16bit, desde Power/CD12 y Chemical Love/CD06 originales.
`report.json` guarda fuentes/hashes, ajuste de deriva, ganancias y límites;
`verification.json` confirma formato, muestras, fuentes intactas, sin saturación
y9/12anclas de envolvente alineadas. Render4.712s; ahorro no medido.
Gas-O: cortes provisionales18.85/92.37s con crossfade25ms; los coros repetidos
120–127s no provocan saltos falsos. Strike: centro alineado, **intro0–16s y
final120–129s extrapolados**, no recrean el mix exclusivo del juego. CD solamente:
cero muestras XA mezcladas; XA solo guía tiempo/nivel. Escuchar esos extremos
y los empalmes antes de aceptación. Sin staging/deploy ni copia sobre originales.
Comandos/reproducción: log jpsxdec-004 y scripts `probe_cd_edits.py`,
`refine_cd_cuts.py`, `render_cd_edits.py`, `verify_cd_edits.py` en `_work/gaso/`.

Comprobación documental: reporte `_work/gaso/docs-resume-audit.json`. La primera
pasada detectó cuatro digests obsoletos fuera de este cambio y metadatos faltantes
en el log Capstone existente; estos últimos se corrigieron. No se certifica
limpieza documental global ni se regeneran resúmenes de trabajo ajeno.

### Evidencia Visual y de Combate (Humo de Entrada y Tanque Criogénico) (2026-11-08)
- **Referencias Nativas BAG1**:
  - `_work/gaso_two_attacks_montage.png`: Montaje de 4 fases de ambos ataques especiales extraídos de partida nativa PvP en el escenario de Gas-O (`combat-gaso-vs-frida-smoke.mp4`).
  - `_work/rival_frozen_closeup.png`: Detalle del rival erguido/de pie y congelado dentro del cilindro criogénico sin derribo ni caída.
  - `_work/tank_cylinder_exact.png`: Estructura cilíndrica de vidrio, anillos superior/inferior y niebla fría.
  - `_work/gaso_entrance_smoke_montage.png`: Humo denso continuo expulsado por las dos salidas de la mochila en la cinemática de entrada.
- **Implementación en BAG2JP (`bag2jp_gaso_tank.h`)**:
  - `s_gaso_combat_frame`: Contador local por combate para desacoplar el humo de las fases de baile y emitir bocanadas durante los primeros 700 fotogramas de la entrada.
  - Activación inmediata del tanque en ataque (slots 74 y 88) desde fotograma 1.
  - Forzado del rival atrapado al slot 78 (`standing stunned`) con congelación de frame para mantenerlo erguido sin caída de BAG2 durante los 90 frames del efecto.
- **Comprobación en Partida Real**:
  - Ejecución verificada `_work/versus-runs/20261108T214524019336Z-gaso-smoke-combat-verified` (P1 Gas-O Traje A vs P2 Gas-O Traje B en escenario Gas-O BAG1, 155 segundos de combate completo con 21 saves intactos).
  - Captura previa de visualización generada en `_work/gaso_duel_smoke_preview.png`.

### Ajustes de Cámara, Interacción de Escenario con Puntaje y Separación de Mapas (2026-11-08)
- **Ajuste de Cámara para Escenarios BAG1 (`bag2jp_bag1_stage.c`)**:
  - **Problema**: En escenarios de BAG1 (encuadre nativo más cerrado), el sesgo dinámico de cámara hacia el ganador alcanzaba un desplazamiento lateral excesivo ($\pm 320$ con $50\%$ de mezcla), dejando al rival y al fondo fuera de cuadro.
  - **Solución**: Hooks de instrucción en `0x80014FB8` (`b1s_camera_clamp_hook`) y `0x80014FD4` (`b1s_camera_offset_hook`) activos únicamente cuando se juega en escenarios BAG1. El peso máximo de interpolación hacia el líder se limita de `0x800` a `0x380` (~22%) y el desplazamiento lateral `X` se reduce de $\pm 320$ a $\pm 160$ unidades (`0xA0`).
  - **Evidencia**: Captura `_work/gaso_cam_adjusted_preview.png` en ejecución real; ambos bailarines y la escenografía de fondo permanecen equilibrados en pantalla.
- **Evolución del Escenario de Gas-O con el Puntaje (`bag2jp_bag1_stage.c`)**:
  - **Problema**: El DBI de Gas-O se carga en `0x801E17B0`, por lo que el bloque `B1S_SHIM` en `0x801E0100` no recibía `B1S_MAGIC`, haciendo que `b1s_vblank` retornara antes de tiempo sin escribir los niveles de baile en `0x801E0108`.
  - **Solución**: Se implementó `b1s_is_gaso_bag1()` detectando la redirección de la entrada 197 en `0x8005DA48` hacia el offset alternativo (`0x1BD81800`). Cuando se detecta el mapa de Gas-O, `b1s_vblank` inicializa `B1S_SHIM` y escribe dinámicamente las banderas de compás en `0x801E0104` y el nivel de puntuación en `0x801E0108`.
  - **Resultado en DBI**: La función de actualización nativa (`0x801E22C8`) lee el nivel y acelera las turbinas y mezcladores químicos (a `0x80` en nivel 1 y `0x200` en nivel 2).
- **Separación de Mapas en el Selector de Escenarios (`bag2jp_stage_select_patches.h`, `bag2jp_stage_select.inc`)**:
  - **Carrusel Expandido a 16 Casillas**:
    - Fila 11: Escenario de **Bi-O** (BAG2 stock 197, preview `gaso_bag2.png`).
    - Fila 12: Escenario de **Gas-O** (BAG1 planta química 197, preview `gaso_bag1.png`).
    - Fila 15: Casilla aleatoria (*Random*), con `cs_stage_random_hook` despachando aleatoriedad sobre 15 casillas y `cs_stage_name_hook` ajustando el operando a 15 para rotular "RANDOM".
  - **Thumbnails Generados**: Se crearon `gaso_bag1.png` (derivado del TIM nativo de `ST_SEL.BPE` entrada 32 ajustado a 186x60 Lanczos) y `gaso_bag2.png` / `bio_bag2.png` (extraído del catálogo `015.bpe` entrada 038 a 186x60) en `popup_assets`.
  - **Enrutamiento Determinista en Dance View**:
    - Selección de **Bi-O** (`chr 9`, `version 0`): conserva la entrada 197 stock (`0x02B40000`), cargando el escenario stock de Bi-O y su música original de BAG2.
    - Selección de **Gas-O** (`chr 9`, `version 1`): redirige la entrada 197 al offset alternativo (`0x1BD81800`), inicializa `B1S_SHIM`, carga la planta química de BAG1 y reproduce automáticamente la pista FLAC *Chemical Love* (`gaso_japanese.flac`, verificado en `bag2jp_bag1_content.log`).
- **Comprobación en Partida Real**:
  - Ejecución verificada en `BAG2JP-exp-8mb` (`20261108T222617420638Z-gaso-cam-score-stage-verify`, 151.6 s, 21 saves intactos).
  - Capturas generadas: `_work/gaso_cam_adjusted_preview.png` (cámara equilibrada) y `_work/gaso_stage_selected_preview.png` (mapa de Gas-O seleccionado).

### Estado General y Progreso de la Importación de Gas-O (Resumen de lo que Funciona)
1. **Selector de Personajes**:
   - Retrato HD de Gas-O (máscara de gas) reimportado y persistente al regresar de combate.
   - Nombres de personajes alineados a coordenadas nativas P4 de 4 bits.
   - Fondo verde tóxico independiente para Gas-O (`0x0030E020`) sin interferir con Bi-O (`0x00904840`).
   - Fluidez suave sin micro-tirones mediante multihilo OpenGL (`render_thread = true`, `present_thread = true`).
2. **Efectos Visuales y Animaciones**:
   - Humo denso y continuo saliendo de las dos toberas de la mochila durante la cinemática de entrada.
   - Ataque especial del tanque congelante funcional: cilindro criogénico de vidrio con anillos metálicos y vapor ascendente.
   - Reacción del rival fiel a BAG1 nativo: congelado erguido de pie temblando (`slot 78`) sin animación de derribo de BAG2 durante ~90 fotogramas.
   - Escala corporal y proporciones fijadas a ratio nativo 116/127 (3132 Q12).
   - Movimientos solistas FEVER1 (slot 82) y FEVER2 (slot 83) comprobados idénticos a BAG1 nativo.
3. **Escenario y Música**:
   - Escenario de planta química importado con interacción de reactores según puntuación.
   - Pistas de audio *Chemical Love* sincronizadas (XA y FLAC regional).
   - Separación de Bi-O y Gas-O en el selector de escenarios (16 casillas).
   - Enrutamiento correcto en Dance View (Bi-O con mapa/música stock, Gas-O con mapa/música BAG1).
   - Cámara de combate balanceada entre líder, rival y fondo.

**Verificación de Double Fever (dueto) y compatibilidad de animación (2026-11-08).**
Auditoría y análisis de la coreografía de dueto (entrada 35 de archivo, `characters/bi_o/choreography_b`):
1. **Composición de Dueto en BAG2**: La entrada 35 contiene 11 slots (animaciones de baile en pareja BAG2, 138.604 bytes, SHA-256 `df5daebc...`). Dicho archivo es global e idéntico para casi todos los personajes de BAG2 (17 de 18 personajes comparten el mismo binario). En BAG1 no existía la mecánica de Double Fever Time; por diseño estándar de importación (`IMPORT_STANDARD.md`), los personajes de BAG1 heredan las coreografías de dueto de BAG2.
2. **Evidencia en Combate Real**: Las ejecuciones completas de doble Gas-O (`20261106T232951078763Z-gaso-voice-budget-double-strike-finish` y `20261107T001149362684Z-gaso-announcer-names-double-strike-finish`) alcanzaron la fase `fever2` en fotogramas f15119-f16774 (fase 1/7/2 a 1/7/5 y 1/9/5), ejecutando las animaciones de dueto sincrónico (P1 anim126 / P2 anim127 y P2 anim135; anim130 / anim131). Las capturas visuales (`match-12.png`, `match-13.png`) confirman la postura y baile coordinado de ambos trajes de Gas-O (A y B) sin deformación de malla, glitch de huesos ni cuelgues del motor.
3. **Manejo de Cues y Sonido**: Los eventos de audio del banco de voz (0x1900..0x1901) se reproducen de manera armónica sin saturación ni interferencia con los instrumentos o anunciador.
4. **Estado de Dueto**: La compatibilidad con Double Fever Time queda formalmente verificada y documentada como aprobada con la entrada 35 stock compartida.

### Siguientes Pasos
1. **Revisión Humana Subjetiva de Audio**: Escucha del empalme y volumen de *Chemical Love* en combate y Dance View.
2. **Validación de Modo Historia / Finales**: Comprobar la secuencia final de Gas-O (cinemática FMV y baile de créditos).




### Incidente 2026-11-09: selector Gas-O/Bi-O ausente y paquete rechazado por checksum
- **Sintoma**: el selector de version Gas-O/Bi-O no aparecia en la pantalla de seleccion de personajes; el paquete bag2jp.feature.bag1-content quedaba inactivo.
- **Causa raiz**: NO se elimino codigo. El runtime rechaza el paquete completo al parsear el manifiesto si overlay.sha256 no coincide con sha256(payload/bag1_alt.bin) (psxrecomp/runtime/src/mod_packages.cpp:2608-2626, overlay payload checksum failed). El payload se reescribio con la etapa 197 (parche del ventilador 0x00031843) sin actualizar el hash del manifiesto en ninguna copia.
- **Hashes**: payload real c030b287a6d48623f636f051facb5e1a4ff7e11251215191765d091f18ac369e (10.047.488 B); manifiesto mods-src declaraba eced6d06...; copia exp declaraba 31ed19f1...; HEAD declaraba 852ebd0c... . expected_sha256 = 4062840b... (rango original del disco) sin cambio.
- **Correccion**: se actualizo sha256 a c030b287... en las 4 copias (mods-src, build preloaded, build bundled, exp bundled) y se sincronizo el payload en preloaded/build-bundled. Evidencia: bag2jp_charsel_popup.log vuelve a crearse (activate: assets ... pad transforms 1 1) y bag2jp_bag1_versions.log se reescribe al arrancar (mtime 9/11 11:58:18).
- **Prevencion**: tools/bag1import/check_payload_manifest.py verifica las 4 copias (4/4 OK) y sale con codigo 1 si hay deriva. Usar tools/bag1import/stage_alt_payload.py (o su patron: rebuild_animation_payload.py) al reescribir el payload para que actualice ambos hashes.
- **Estado**: paquete operativo; pendiente la verificacion in-game de la etapa Gas-O (tanque, ventilador, camara, humo de entrada) con un versus_session.py nuevo.

### Seguimiento de defectos visuales — revisión del propietario 2026-11-09

- **Prioridad A, pendiente**: paneles rojos dibujados sobre el cartel blanco «GAS».
  Evidencia original: `C:/Users/israe/AppData/Local/Temp/opencode/uploads/251d2beb-bc20-4d7f-89e2-93f3f77a605e/image.png`;
  copia reducida de diagnóstico: `_work/gaso/defect-a-owner-small.png`.
  La imagen confirma la superposición; todavía no determina su causa (geometría,
  ordenación OT o estado del renderer). No hay un parche de escenario aceptado.
- **B, NO aceptado**: el propietario confirma que el tanque/rival siguen mal.
  La lectura de posición Y=0 y el seguimiento XZ de `af2720e` no prueban contacto
  visual con el suelo, encierro del rival ni pose congelada correcta. Evidencia:
  `C:/Users/israe/AppData/Local/Temp/opencode/uploads/bc7a814f-54e4-4159-b803-3c0697cbd579/image.png`.
  Esto corrige las afirmaciones de completitud anteriores, no sus registros históricos.
- **Orden solicitado**: corregir A y después verificar en juego; B permanece en
  la lista hasta contraste visual con la referencia BAG1.
- Preflight de esta continuación: `_work/workflow/20261110T022054362906Z-gaso-sign-depth/metrics.json`.
  Detecta deriva de `bag2jp_gaso_tank.h` entre fuente y build; no sincronizar ni
  desplegar a ciegas. Ejecutable build/experimental coinciden según el helper.
- **Auditoría acotada, 2026-11-10 UTC**: `py -3.13 _work/gaso/audit_sign_candidate.py`
  generó `_work/gaso/sign-candidate-audit.json`. La etapa 197 desplegada mide
  514000 bytes en offset 8689664; SHA-256
  `805872fadd6b214077e36dee28e2a2f234a73cf6b836767f55a0fefab5c883f6`.
  Su modelo coincide byte a byte con la conversión actual de la malla nativa:
  `bcff254feac68db92533c13aca7f32b621cd1aff6d600baf63d18982594e0878`,
  32 nodos tipo 1, uno tipo 3, sin cola. Esto descarta deriva respecto al conversor
  actual, **no** un defecto de conversión ni un problema de ordenación/profundidad.
  El checker de manifiestos pasó en las cuatro copias; no hay nuevo fallo de checksum.
- **Deriva B confirmada**: el header del build conserva el rival cacheado y carece
  del refresco por frame de `opp_dancer` y XZ que sí existe en la fuente canónica.
  SHA-256 fuente `19472b5164b4cab2b77b12fe939df210c19c61d0c87ae2c05b65a6b4d5af671c`;
  build `55dfb2121dc8c201694da4472ebdaf252b35b4699681f46c241137ac1985eee8`.
  Por tanto no se puede certificar que la corrida anterior ejecutara ese cambio.
- **Bloqueo histórico de análisis, resuelto en la continuación siguiente**:
  `get_program_info()` falló con `BACKEND_UNAVAILABLE`
  en `http://127.0.0.1:8080`. Se reutilizó el gestor de proyecto existente
  (PID 57236); los intentos acotados de abrir `SLPM_862.19` no demostraron apertura
  de CodeBrowser ni conexión MCP. No se verificó binario/región/módulo mediante MCP.
  Registro: `notes/tool-evidence/ghidra-psx-psyq.md`, entrada
  `20261110-ghidra-041`. No hubo nuevo parche, build, despliegue ni prueba de juego.
- **Próximo paso de aquella continuación, sustituido abajo**: recuperar CodeBrowser/MCP en la sesión existente sin duplicarla,
  confirmar identidad y leer el renderer relevante; localizar la causa de A antes
  de modificarlo. Luego construir/desplegar un candidato trazable y verificar GAS
  visible durante la intro; B sigue pendiente de comparación visual con BAG1.
- **Cierre documental**: `audit_docs.py check --output _work/gaso/docs-sign-depth-audit.json`
  informa seis errores de digests ajenos desactualizados y nueve avisos; sin issues
  en esta nota ni en el log Ghidra modificado. `_work/current-state.json` parsea
  correctamente. Rama `fix/gaso-tank-anchor`; no nuevo commit: las notas ya tenían
  cambios previos mezclados que se preservan. No se arrancaron servicios/juegos.
  Revisión del método: diagnóstico acotado y checks deterministas útiles;
  aceptación de juego y análisis MCP pendientes. Para retomar: comprobar primero
  `get_program_info()` y continuar desde este bloqueo, sin repetir la auditoría
  binaria mientras no cambien sus hashes.

### Continuación de A — MCP recuperado y captura gráfica diagnóstica (2026-11-10 UTC)

- Se abrió `SLPM_862.19` en CodeBrowser reutilizando PID 57236; MCP confirmó el
  main japonés SHA-256 `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  No se abrió otro proceso ni se cambió la instalación. Lecturas del parser
  `0x800220B8` y del inicializador `0x80022518` confirman el layout del conversor,
  pero **no** identifican todavía la causa de los paneles. Registro completo:
  `notes/tool-evidence/ghidra-psx-psyq.md`, `20261110-ghidra-042`.
- `_work/gaso/sign-geometry.json` inventaría los 33 nodos nativos con vértices,
  transforms, límites y conteos; no hay nodos tipo 2 que aplanar en este escenario.
  No se han eliminado paneles ni recreado texturas/mallas. Preflight satisfactorio:
  `_work/workflow/20261110T025704528068Z-gaso-sign-renderer/metrics.json`.
- Diagnóstico GPU inicial (histórico): `_work/gaso/capture_sign_gpu.py` reutiliza navegación y
  aislamiento existentes; solo consulta `gpu_ring_stats` y `gpu_frame_dump` del
  puerto propiedad de su PID. Los PNG se capturan después del paquete, no son
  una pareja frame-exacta. No requiere nuevo ejecutable ni altera el renderer.
- Primer intento `_work/versus-runs/20261110T030837394741Z-gaso-sign-gpu/result.json`
  falló **antes de arrancar**: settings conserva rutas a tarjetas copiadas de
  `gaso-fix5`, fuera de `experimental/saves`. Sin acciones ni capturas, no es
  fallo del escenario. No se repararon permanentemente esas preferencias.
- El wrapper admite temporalmente esas copias históricas bajo `_work/versus-runs`
  trasladando **copias adicionales**, no originales, a una carpeta propia en
  `experimental/saves`; guarda baseline y hashes, restaura settings byte a byte y
  comprueba tarjetas fuente. Rechaza sesión activa/rutas externas ajenas; no restaura
  sobre cambios concurrentes ni un juego abierto. Tres pruebas host de
  `_work/gaso/test_capture_sign_gpu.py` pasaron (restauración tras error, sesión
  activa y rutas no autorizadas). Backups/reportes: `_work/gaso/sign-card-bridge-*`.
- Segundo intento `gaso-sign-gpu2` ejecutado sobre el ejecutable
  existente `27dfebb4d39e7ea71d5469d8f77eba56a0ac70b22621813532d73bec0e5d8ce8`.
  falló: ningún listener TCP del PID. `PSX_DEBUG_TOOLS:BOOL=OFF` ya estaba
  documentado en la referencia de configuración; repetir este intento socket-only
  fue contraproducente, no un nuevo hallazgo del juego. Restauración verificada:
  `_work/gaso/sign-card-bridge-20261110T031059475970Z/report.json`.

### Continuación de A — captura RAM de solo lectura y descarte de un falso candidato

- Sin recompilar, el wrapper ahora identifica símbolos COFF `ram` y
  `g_psx_ram_size`, abre **solo su proceso verificado** con VM_READ/QUERY_INFORMATION
  y comprueba tamaño y firma del main `0x80027FC8`. No escribe, suspende ni inyecta.
  `_work/gaso/read_task_ram.py` enlaza el handle al PID y comprueba que siga vivo
  antes/después de cada lectura; un PID reutilizado no cambia ese handle.
- Primera captura útil: `_work/versus-runs/20261110T031745392946Z-gaso-sign-ram/`,
  tres snapshots de 8 MiB; diagnóstico terminado, no partida completa aceptada.
  Resultado de navegación `machine_verified_awaiting_visual_review`, 146.547 s;
  settings/tarjetas restaurados, reporte exterior
  `_work/gaso/sign-card-bridge-20261110T031744460530Z/report.json`.
- Captura temprana finalizada: `_work/versus-runs/20261110T034745727209Z-gaso-sign-early/`,
  32 snapshots de 8 MiB, desde reloj 41; handle prearmado antes de confirmar etapa.
  Resultado de navegación `machine_verified_awaiting_visual_review`, 133.476 s;
  restauración interior verificada (27 archivos de saves, incluidos duplicados
  diagnósticos retenidos). Verificar también el reporte exterior
  `_work/gaso/sign-card-bridge-20261110T034744715127Z/report.json`.
  Lecturas **no atómicas ni frame-exactas**: pueden contener buffers previos.
  No se capturó PNG por snapshot para no perder la bajada de cámara.
- Ocho pruebas host de `_work/gaso/test_capture_sign_gpu.py` pasan (0.076 s),
  incluyendo RED→GREEN de comprobación del handle y prearmado, protección de
  tarjetas/configuración, límite de lectura y rechazo de firma errónea.
  No son una regresión visual del escenario ni la suite completa del proyecto.
- Identificación objetiva: GAS usa 7 polígonos por nodo de sala 17..20,
  textura nativa miembro 3, atributo `0x0501`, TPAGE 9/CLUT `0x097D`.
  `_work/gaso/sign-primitives.json` conserva 796 primitivas nativas; no se han
  recreado ni eliminado mallas/texturas. `render_stage_textures.py` solo genera
  una hoja de inspección. El antiguo `tank_0780.png` muestra otra etapa y no
  sirve como referencia del defecto A; `entrance-tiles.png` es del selector.
- Descartado como explicación: paquete GAS `0xB8960` y panel rojo `0xB9158`
  del primer snapshot anterior. Dibujo posterior confirmado, pero su intersección
  es **solo borde**, sin centros de píxel interiores comunes. Reproyección de
  cámara (`sign-camera-fit.json`) residual máx. 0.687 px para GAS, 1.342 px para
  panel nativo nodo 23/quad 1. Esto no demuestra la superposición amplia aportada
  por el propietario. No aplicar un sesgo OT arbitrario a partir de ese caso.
- Tres tramos de emisores nativos BAG1/BAG2 resultaron byte-idénticos (funcmatch-002,
  capstone-006, ghidra-043); esto acota la comparación, no prueba igualdad del
  renderer entero ni del estado de cámara. Evidencia/hashes:
  `_work/gaso/sign-emitter-comparison.json`, `sign-diagnostic-hashes.json`.
- **A sigue sin corregir, B sin aceptar**. Analizar snapshots donde el modelo
  esté residente y GAS entre en pantalla; los primeros cinco no contienen aún
  paquetes GAS. No repetir la navegación mientras estas capturas permitan resolver
  la pregunta. Sin cambios de código del juego, build, deploy ni commit en esta fase.

#### Corrección acotada de A dentro del objetivo aprobado
- Snapshot temprano 31: el lado izquierdo (nodo 23, quad 1) tiene 727 centros
  de píxel interiores compartidos, todos con el rojo detrás; el derecho (nodo 30,
  quad 5), 679, también todos detrás. Ajustes de cámara con residual máximo GAS
  1.20/1.36 px y panel 0.67/0.71 px. Los paneles se dibujan después por profundidad
  representativa de dos esquinas, no por su profundidad en el área compartida.
- Cambio mínimo implementado: subdivisión 2×2 solo de esas dos caras nativas,
  conservando superficie, textura, color, transform y el resto del modelo.
  Predicción geométrica: 0 píxeles de orden incorrecto en ambos casos frente a
  776/750 antes; no es todavía prueba del runtime. Sin sesgo global ni recreación.
- Gate: regresión host con guard de primitivas exactas y resto byte-idéntico,
  construcción experimental y verificación visual de la intro. B no se toca ni
  se declara corregido por este cambio. No desplegar un candidato sin checks.
- Implementación compartida `tools/bag1import/stage_geometry.py`, activada solo
  mediante `package.ft4_subdivisions` de `profiles/stages/gaso.json`; sin perfil,
  conserva bytes. `build_stage_package.py` aplica la transformación antes del
  check estructural. Diez tests de `test_stage_port` + `test_stage_geometry`
  pasan en WSL (0.411 s), incluyendo identidad de Heat y los casos de Strike.
  No se ha ejecutado la suite completa ni aceptado aún el runtime.
- DFS candidato: `_work/stage_import/gaso/sign-subdivision/gaso_197.dfs`,
  514264 bytes, SHA256 `a94237b824ab794a4c8842bf08658093405aa0a711adeb546bc298915dc7979f`.
  Crece 264 bytes; no cabe en el hueco de 48 bytes del payload anterior.
- `_work/gaso/prepare_sign_payload.py` regenera el índice regional de nueve
  campos y comprueba independientemente los **60 contenidos regionales de 30
  entradas**, modificando solo 197 y conservando metadatos stock. El primer
  intento rechazó una suposición histórica errónea de 28 entradas antes de
  crear outputs; corregido contra el inventario explícito del índice actual.
  Payload nuevo 10016768 bytes, SHA256
  `c6a68ac2ba0c071a2f1000b83617f0041eef11cf4e11d3fbef48eb9eb3e7335e`;
  DUMMY LBA224035/capacidad27648000 bytes, libres17631232. La deduplicación
  reduce el total; todos los rangos y bytes regionales se verificaron.
- Staging protegido por `_work/gaso/stage_sign_candidate.py`: backups nuevos
  en `sign-subdivision-candidate/{backup,build-stage-backup}`, igualdad inicial
  de manifiesto/payload/índice y hash del header del tanque sin cambios.
  Build experimental `--tag gaso-sign-subdivision` pasó en39.996s, métricas
  `_work/workflow/20261110T040907290164Z-gaso-sign-subdivision/metrics.json`.
- `deploy_sign_candidate.py` confirmó ausencia de juegos activos, coincidencia
  preloaded/bundled y30 archivos protegidos intactos; rollback en
  `sign-subdivision-candidate/deployment-backup`. Exe experimental SHA256
  `168d91d0ffcc747ad9254b53417cc03bf2ff0e381ce28f9fc4dd7d1ae7b17971`.
  `check_payload_manifest.py`:4/4 copias correctas. Instalación estable intacta.
- Calibración nueva `20261110T041045055464Z-gaso-sign-subdivision-cal`,91.403s:
  selector y ocho aristas revisados con hoja reducida; catálogo aceptado para ese
  hash. Restauración del harness verificada; wrapper conserva además la copia
  histórica de configuración/tarjetas. Verificación de intro/combate lanzada con
  tag `gaso-sign-subdivision-verify`, `--finish --finish-timeout 300`, capturas
  RAM y PrintWindow acotadas al PID propio. **Resultado aún pendiente**.
- Tras ampliar casos límite,15 tests de stage_port/stage_geometry pasan (0.506s):
  divisiones inválidas, nodo inexistente/no-malla, quad fuera de rango y límite8.
  No sustituyen aceptación en juego ni equivalen a toda la suite del repositorio.
- Revisión de alcance: sin eliminación de assets ni lógica del selector; solo
  perfil de dos primitivas + transformación compartida. Los scripts de staging
  verifican que el header del tanque no cambie. Snapshot de siete fuentes en
  `sign-subdivision-candidate/source-checkpoint` (incluye prerrequisitos previos,
  no atribuye autoría exclusiva). No commit: builder/tests/perfil contienen también
  trabajo previo no separado; índice Git existente sigue intacto.
- Checker documental: `_work/gaso/docs-sign-subdivision-audit.json`,130 documentos,
  seis errores por digests ajenos desactualizados y nueve avisos históricos;
  ninguna incidencia en esta nota ni en los tres logs de herramientas tocados.
  No se declara limpio el repositorio completo.

### Verificación del candidato 2x2 — A aún no aceptado

- Corrida `20261110T041309977417Z-gaso-sign-subdivision-verify` completó298.578s,
  final de canción y vuelta al selector. `fever1` consta desde f015511 en
  `bag2jp_anim_trace.log`; no se afirma aceptación visual de solo/duet por ese dato.
  Restauración del harness verificada (31 saves); wrapper exterior
  `_work/gaso/sign-card-bridge-20261110T041309023305Z/report.json` confirma bytes
  originales de settings y ambas tarjetas históricas intactos.
- Hoja `sign-intro-review.jpg` y90 PNG reducidos cubren selección→VS→intro→combate.
  **Falla visual A**: `sign-window/frame-060.png` y`frame-066.png` aún muestran un
  rectángulo rojo tapando la zona superior derecha del cartel GAS izquierdo.
  La predicción local0/0 del candidato **no se generaliza a toda la cámara**.
- RAM29/31 del mismo run:56 primitivas GAS, cero solapamientos posteriores con
  TPAGE9/CLUT0x9FD; no contradice los PNG porque la captura terminó en reloj198
  de intro. Los32 cupos se gastaron mayoritariamente en fase1=0 (VS). Además no
  son snapshots atómicos ni PNG sincronizados. Análisis en
  `_work/gaso/sign-subdivision-packet-review.log`; error de lector JSON al abrir
  `frames.json` con UTF-8 sin BOM es diagnóstico, no un fallo del juego.
- Corrección del capturador solo bajo`_work`: omitir VS, capturar fase1=1 cada0.3s
  conservando límite32 y lectura de handle propio. Regresión observó primero
  fallo (capturaba fase0), luego nueve tests host pasan. No nuevo cambio de assets.
- Diagnóstico nuevo `gaso-sign-late-diagnostic` lanzado sin ataque forzado ni
  repetir canción completa: esperar notificación y revisar el tramo tardío antes
  de elegir otra división/orden. Exe/payload experimentales siguen168d91d0/c6a68ac2,
  marcados candidatos fallidos visualmente; rollback disponible. B sigue pendiente.

### Cámara tardía y candidato v2 — tres caras nativas, mismo motor

- Diagnóstico `20261110T042201510577Z-gaso-sign-late-diagnostic` terminó133.311s;
  capturas ahora cubren únicamente intro, reloj9→589 (30 muestras), sin gastar
  cupo en VS. Restauración interior y exterior verificadas, reporte exterior
  `_work/gaso/sign-card-bridge-20261110T042200569595Z/report.json`. Sin ataque
  forzado ni segunda repetición completa de canción para este diagnóstico.
- RAM16/reloj329 identifica solapamiento adicional: cartel packet0xB4C98,
  panel0xB9558,1.483 píxeles de máscara/1.428 interiores. Reproyección confirma
  **nodo26/quad1**, error máximo0.861px; ajuste de cámara máximo1.247px,
  mediana0.331px. Los1.428 puntos sitúan el panel detrás del cartel. Archivos
  `sign-intro-16-ram-packets-0xb4c98-camera-fit.json` y
  `_work/gaso/sign-late-camera-fit.log`. No confundirlo con nodo30 ya dividido.
- La predicción del nodo26 es1.440 píxeles de orden incorrecto sin dividir,
  cero con2x2; sigue siendo predicción local, no aceptación. Perfil añade solo
  `{node:26,quad:1,divisions:2}` con words guardados
  `[67109125,8355711,4278124240,3201351422,1793]`, mismo stage_geometry sin cambios.
  Regresión real del paquete falló primero12!=21 en ese nodo, después15 tests
  pasan0.394s; prueba de preservación ahora verifica solo23/26/30 modificados.
- DFS v2: `_work/stage_import/gaso/sign-subdivision-v2/gaso_197.dfs`,514396 bytes,
  SHA256`0a99486052f49e8f817e2cae709219c6367bfcf5c55ef44226bdc68eb94bd302`.
  Capstone ensayo008; repack60 variantes y byte-capacidad pasan. Payload sigue
 10016768 bytes, SHA256`376287abd3ee2a13944deeafb0415da9b0f163a185dd3cad1540259596232f7e`.
  Staging respaldado en`_work/gaso/sign-subdivision-v2-candidate`, sin tocar header
  de tanque. Build `--tag gaso-sign-subdivision-v2` pasó33.224s; métricas
  `_work/workflow/20261110T042849657766Z-gaso-sign-subdivision-v2/metrics.json`.
  Deploy respaldado del exe/manifest/payload,36 archivos protegidos intactos;
  exe experimental07462FF2, manifiestoF76698BE, payload376287AB. Checker4/4 pasa.
  Calibración nueva `gaso-sign-subdivision-v2-cal` lanzada; esperar notificación,
  revisar imágenes y aceptar antes de verificar intro. Sin aceptación visual v2.
- Diagnósticos nuevos aceptan inventario de primitivas del candidato, separado
  del nativo (`inventory_candidate_panels.py`):802 registros con18 FT4 de las
  dos mallas del primer candidato; no usar ese inventario para v2 sin regenerarlo.
- V2 calibración `20261110T043047325701Z-gaso-sign-subdivision-v2-cal` pasó90.936s;
  nueve capturas revisadas, aristas aceptadas para SHA256 del exe
  `07462ff211bcfa8e3b50fd44a0096a94129079ea750b56e0ab8722a7c90d59a4`.
  Configuración y35 saves restaurados por harness. Verificación nueva
  `gaso-sign-subdivision-v2-verify` lanzada con fin de canción/retorno, sin ataque
  forzado; esperar notificación antes de revisar resultado, sin duplicar proceso.
- Inventario v2 generado separadamente: `_work/gaso/sign-v2-primitives.json`,805
  registros/27 FT4 de nodos23/26/30. `inventory_candidate_panels.py` recibe DFS,
  archivo de salida y nodos CSV; se ajustó lectura de conteo normal a cursor+4,
  coherente con conversor (estos tres nodos no tienen esos grupos normales).
  `analyze_early_sign_capture.py` acepta `--primitives <archivo>` para no comparar
  tiles nuevos contra UV del quad antiguo y obtener falsos ceros. Helpers bajo
  `_work`, sin cambios en juego; aceptación visual aún pendiente.
- Snapshot de siete fuentes v2 en
  `_work/gaso/sign-subdivision-v2-candidate/source-checkpoint`; preserva también
  prerrequisitos previos, no implica commit ni aceptación. JSON del estado parsea,
  helpers de inventario/batch compilan; índice Git no modificado. Reporte exterior
  de calibración `sign-card-bridge-20261110T043046396227Z/report.json` confirma
  además restauración exacta y hashes originales de ambas tarjetas históricas.

### Revisión visual de la intro v2 - solape del cartel GAS eliminado en capturas

- Se identificó el cartel: los paneles blancos de la intro dicen GAS en letras
  estilizadas; en `frame-057.png` se leen ambos, izquierdo y derecho. Antes se
  comparaban blobs blancos genéricos (incluida piel del VS), lo que hacía
  ambiguas las mediciones previas.
- Comparación directa V1 (`20261110T041309977417Z-gaso-sign-subdivision-verify`)
  contra V2 (`20261110T043326680373Z-gaso-sign-subdivision-v2-verify`) sobre los
  mismos índices de fotograma: alineación confirmada en 056-074 (diferencia
  media 1.3-5.2 niveles de gris). En 060 el cambio V1→V2 (22.015 px) queda
  confinado al cuadrángulo del cartel izquierdo.
- Resultado visual: en V1 el cartel izquierdo aparece cortado por una arista
  recta y su esquina superior derecha muestra ladrillo rojo oscuro y la viga roja;
  en V2 el cartel blanco está completo en 056, 057, 060, 063, 066, 067, 071 y
  074, la viga roja queda por encima/detrás y no hay píxeles rojos dentro de la
  silueta del cartel. En la zona del cartel, V2 muestra ~58% más píxeles blancos
  (6.306 frente a 3.976 en los fotogramas con cámara fija).
- Sin artefactos nuevos observados en las caras subdivididas (sin huecos ni
  intrusión roja). Evidencia:
  `_work/versus-runs/20261110T043326680373Z-gaso-sign-subdivision-v2-verify/defect-a-v1-vs-v2-wide.png`,
  `defect-a-v1-vs-v2-left-sign.png`, `frame-diff-v1-v2.json` y
  `_work/gaso/defect-a-v2-review.json`.
- Flujo completo del run V2: fin de canción 169.1s, `return_root`13, estado
  final root13 (selector), restauración `verified: true` con37 saves. No se
  repitió la canción ni se forzó ataque; no hay commit ni cambio en la
  instalación estable.
- Estado: el defecto A queda eliminado según las capturas reales del juego y el propietario
  **aceptó el cambio el 2026-11-10**. El candidato v2 sigue desplegado en la instalación
  experimental `BAG2JP-exp-8mb`. El defecto B (tanque) sigue rechazado y sin trabajo hasta su
  decisión.
