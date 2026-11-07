---
id: gaso-import
title: "Gas-O: importación y aceptación"
tags: ["bag1", "gaso", "import", "evidence"]
summary: "Personaje USA con evidencia histórica; doble Gas-O arreglado por presupuesto de voz SPU (pasa hasta gameplay en Strike/Heat); escucha, partida completa, entrada nativa y JP pendientes."
related: ["plans/gaso-import.md", "IMPORT_STANDARD.md", "notes/character-pipeline.md"]
created: "2026-11-06"
updated: "2026-11-06"
doc_kind: evidence
---

# Gas-O — ledger canónico

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
