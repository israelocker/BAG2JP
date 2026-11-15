---
id: gaso-import-digest
title: "Gas-O: Bloque 4, captura y ciclo de vida"
tags: ["digest", "gaso", "bag1", "evidence"]
summary: "Bloque4 bloqueado por readiness F7: load3 falló menú slot01 pese25ms;captura accepted solo diagnóstico,sin load/recuperación. EXE94922aba experimental/canónico0,cal2 aceptada,150saves/5configs protegidos. Próximo: señal de menú listo en host;no más tomas ciegas."
related: ["notes/gaso-import.md", "_work/current-state.json"]
created: "2026-11-14"
updated: "2026-11-15"
doc_kind: digest
source: "notes/gaso-import.md"
source_sha256: "d2650319d9c116808c84ed676bad9d355380000defee4def260d70cb514848b4"
---

# Gas-O: lectura vigente

Estado más reciente: sección «Bloque 4: guard1 desplegado; toma de recuperación».
Owner autorizó opción1 build/prueba. WIP13d52f9; fuentes canónicas guard0,
build guard1 con staging respaldado; EXE94922aba desplegado solo en experimental
(backup anterior e709c2f8, configs/paquetes conservados). Build39.198s PASS.
Cal1 rechazada jitter28.3ms; cal2 accepted=true,jitter12.9ms,audio0descartes,
catálogo revisado. Partida block4-recovery-load falló: F7 queda abierto, las teclas
del mismo lote no llegan al pause-loop; sin SAVED/.pst,150saves/configs restaurados.
Captura rechazada por shutdown inseguro, no validación de juego. Regresión3RED→7OK;
wrapper separa F7 y acción25ms (margen experimental). load2 sí guardó pero no llegó
a load por esperar stderr buffered. Ahora exige .pst no vacío+.thumb PSTH128x96
completa (nativa solo tras save exitoso),10hostOK; recorder para antes del juego.
load3 falló por menú slot01 sin guardar:25ms NO fiable. Captura accepted=true
solo diagnóstica (recorder cerró seguro), no load/recovered/fin/selector. No juego
activo;150saves/cinco configs protegidos,ningún .pst en saves originales. Próximo
interno: señal verificable de pause-loop listo y host tests; no más partidas
ciegas ni cambios framework/debug-tools sin evaluar alcance.
Señal candidata aún sin verificar: flag host estático s_wedge_classification_paused
(freeze_heartbeat.c176..180), activado justo antes del pause-loop(main.cpp8787).
Wrapper _work/gaso/block2/run_recorded_savestate.py
usa F7/Up/S (slot11 aislado), luego F7/L tras retirada; exige confirmación post-save,
recovered y restored. Sin debug server (OFF), sin cambios de gates/runtime.
No aceptación de recuperación todavía; no pedir conformidad sin evidencia.

Candidato host sobre 2ebb765. Ghidra: los constructores dejan actor+0x10 =
DFS de motions M y raw[i]=&payload_i (FUN_800125fc), luego raw[0]=M+4 y vacío
raw[1]=M+8+size0. `gaso_caught_native_empty` lo deriva con alineación/rangos y lo
usan publicación y recuperación (un word cero cualquiera ya no vale). En savestate,
solo con guard1, se reclama un lado si raw[1]==clip exacto del bank y VERIFY pasa;
si no, log «recovery refused». Solo lectura: restaura la retirada existente. Reset
no recupera. Sin journal ni cambio MODMEM. Runtime 38 OK, grupo 91 OK 46.1 s,
mutación 25/25 kills por aserción, Goldfish 2× SIN HALLAZGOS BLOQUEANTES. Suite 482
tests, mismos 29 FAIL/ERROR (no verde global). Límites: bank no listo/
otra base sin log, lecturas previas sin alinear. La sección superior actualiza
la autorización/build/toma; Bloque5 y conformidad selector aún pendientes.

Checkpoint anterior 2ebb765 (observador de reinicialización nativa), fuente44a91bf8: observa8002BA18/word0c00b617 con ABI
principal/actor/stack autenticado; invalida ambas capturas aunque direcciones y
bytes sean idénticos. Serial host64bit cambia en init/reset/load; no es generación
de contenido autenticada ni reloj de frames. No escribe RAM/CPU/tuplas/asignaciones,
no olvida binding publicado ni cambia hits/epoch visual desde init.35tests runtime
PASS12.137s; baseline35PASS14.069s+19/19assertion mutants68.210s. Primera matriz
12/13 dejaba pasar skip-site por comprobar también un opcode distinto: corregida.
Goldfish2revisores: fixture externo08 confirmado RED y separado de host; integración
AOT configurable descubre cualquier shard y comprueba orden dispatch/link/delay/CPS;
ausencia emisión skip explícito, presente incorrecta FAIL. Integración local ejecutada
sin skip,5snippets rechazados y19negativos de rango/ABI, binding preservado ambos lados.
Ambos revisores re-verificaron correcciones favorablemente. Home: compatible por
inspección+test separado, no ejecución integrada de dispatcher ni juego. Primera suite
475tests140.865s con1fallo/28errores mismos29nombres; final revisada479tests148.492s,
1fallo/28errores exactamente mismos29nombres de b38ca62, no verde global. Checkpoint
WIP host, sin cierre lifecycle/Bloque4 ni staging/build/deploy, instalado e709c2f8 intacto.
Siguiente: evidencia del origen nativo empty_raw/tablas para recuperación autenticada
tras load sin ampliar MODMEM ni deducir un puntero desde ceros/caché host pre-load.

Checkpoint anterior b38ca62: snapshot de8words de tablas de los dos actores; al take
valida membresía, personaje/lado y autoridad Gas-O BAG1 del atacante. Captura con drift
se consume sin take/lookup/hit ni redirección propia.
Log positivo slot1 reused tras VERIFY. Goldfish confirmó captura pendiente cuando
cambiaban listaYcontrolador y error del helper ante retiro seguido de stale; ambos
reproducidos RED134 y corregidos,2revisores favorables después.77tests PASS40.946s;
15variantes×2lados+reemplazo conjunto/retiro,5/5mutantes por assertions. Suite470tests,
1fallo/28errores, mismos29nombres; no verde global. Sin staging/deploy/juego.
Reset/load aún deja tupla publicada sin ownership host: lifecycle no terminado.
Framework memory.c exige tamaño/cookie MODMEM exactos: añadir journal guest cambiaría
compatibilidad con savestates previos; NO hacerlo sin decisión explícita. Investigar
recuperación autenticada compatible antes de elegir. Experimental sigue e709c2f8.
El observador antes propuesto está implementado solo en fuente/host, no desplegado;
no resuelve ownership serializado de tuplas. Guard1 continúa bloqueado.

Derivado de la sección «Bloque 3: escenario, HUD y audio re-hit de Heat» y «Bloque 2 sobre la base ±870»; verificar hash de la fuente
antes de reutilizar. La nota canónica conserva la cronología.

- **Bloque 4 (2026-11-14, autorizado):** conservar preview Gas-O al volver al selector,
  sin reabrir popup. Primer candidato `23bbdabd` mostró retrato Gas-O, pero nombre BI-O
  transitorio al retornar en captura aceptada: no cerrar con esa evidencia parcial.
  Candidato temprano global descartado SIN deploy tras Goldfish: variantes mixtas
  se sobrescribían. Capstone/fixture007 confirmaron que hook9347c era posterior a
  JAL93474->93504 (consumidor del nombre). Se mueve el MISMO hook antes del JAL.
  Fuente `9c7cec67…`, 15 tests PASS, revisión delta favorable tras corregir hallazgo.
  Build34.113s, EXE experimental `e709c2f8…`, backup y recursos conservados.
  `block4-consumer-cal` accepted=true y catálogo revisado; `block4-consumer-return`
  **accepted=true**,2033latidos/1stall99ms,12191pares audio/3descartes;150saves/configs
  restaurados. Retrato y nombre GAS-O ya en primer selector revisado (gf17532,
  t193.400), Heat intacto;37muestras consecutivas del reloj sin BI-O (WGC VFR puede
  repetir/saltar imágenes). Correcto hasta202s sin reabrir popup; conformidad pendiente.
  Suite final466tests,1fallo/28errores: mismos nombres, no verde global.
  Siguiente unidad autorizada: generación/ownership CAUGHT tras reset/load y logVERIFY,
  no repetir selector sin nuevos inputs. Fuente CAUGHT sigue guard0:
  reset/load deja una tupla publicada sin ownership host; resolver antes de productizar.
  Suite global457tests,1fallo/28errores en otras costuras; no es una suite verde.
- **Bloque 3 (2026-11-14, aceptado por el propietario):** el payload desplegado (`847058C4`, `stage197`
  `b663417f`) coincide con el canónico (`bag2jp_bag1_stage.c` `5F19F0ED`), sin rebuild.
  - Toma natural `block3-stage-c` (`ff800b28`, Gas-O BAG1 vs Heat BAG1 en `GasOBAG1`, 150
    saves/ajustes restaurados): WGC **`accepted: true`** (`2003` latidos, `0` stalls, jitter
    p99 `10.97 ms`, `59.941 fps`, `11977` pares audio `0` descartes, `owner.mp4` `d5eee345…`).
    `0` ataques; `level` `0->1` (`gf10298`), `1->2` (`gf12862`), fin `0x40` (`gf15750`);
    ventilador `0->128->512`; intro tubo->ventilador->sala->Ready; HUD `GAS-O` legible;
    pilares rojos, `1 Player Win`, solo fever y selector. Límites: VS Bi-O fuera de alcance,
    giro del ventilador medido en RAM, sin video BAG1 de referencia, audio subjetivo humano,
    ±2 fotogramas.
  - Audio re-hit de Heat (sin cambio de código): `clamp` (`mode1`) vs `r2` (`mode0`) es
    **bit-idéntico** (`max_abs_diff = 0` en 367,500 muestras `re_hit[-200..+300]`). La diferencia
    de `r3` a `+46.18` correlaciona `1.0000` con `slide_diag_1st - clamp_1st` (`mode1` vs `mode1`)
    y Ghidra/Capstone confirman que `mode1` (`0x801d66e4`) no llama a `0x8002e478`: es variante
    RNG nativa.
- **Vigente (base ±870 y Bloque 2 aceptados):** el propietario fijó la referencia inicial en GO + 2 s (cámara asentada
  T=[0,692,3028]). Medición `go-plus2-measure` aceptada; modelo GTE 0.75/OFX256 da ±870
  (zoom128: ±435). Solo cambia `B1HOME_WIDE`; radio 199, guardas y cámara nativa intactos.
- 23 tests PASS, 11/11 mutantes; dos Goldfish triados (`triage-go-plus2-anchor.md`).
  EXE `ff800b28…` desplegado EXE-only en experimental; calibración `go-plus2-cal` aceptada.
- `go-plus2-autoplay` **accepted=true** (1999 heartbeats, 1 stall, 11975 pares audio sin
  descartes; 150 saves/configs restaurados). GO+2 s: cuerpos ~215/~735 px frente a 235/727;
  la muestra RAM más cercana llega +0.88 s tarde (estimación visual, ±2 fotogramas).
- RAM: homes ±870, radio 199; final anim67/68 [-870,312,0]/[870,520,0]; INT_MAX, fever y
  selector observados. Hojas `go-plus2-match/` sin recortes visibles.
- **Conformidad del propietario** (2026-11-14) y commit local WIP 650d825. Snapshot tras el
  Bloque 2. Investigación del Bloque 2: tanque independiente de la separación; intercambio
  nativo de lados solo para los personajes 10/14; dueto sin evidencia. `BAG2JP_TEST_P1_DUET`
  ya llega al juego y `result.json` registra los fixtures armados. El fixture de dueto exige
  Heat contra Heat con trajes A/B, así que la toma B es Heat BAG1 A contra Heat BAG1 B.
  Tomas A `block2-attack-a` (tanque/CAUGHT/fever en solitario/selector) y B `block2-duet-b`
  (dueto con homes ±870 que se mantienen; bailarines cerca del centro) grabadas y aceptadas
  técnicamente. Siguiente: conformidad del propietario, commit local y snapshot. Histórico: READY ±1300 quedaba hacia el borde exterior a GO+2 s; ±700 hacia dentro.
  Lo siguiente es evidencia anterior:

- Owner pidió terminar más centrados, como al inicio. El radio 318 separaba pero dejaba
  P1 Z=-275 y P2 Z=272; anim45 desplaza y anim68 conserva el desfase.
- Candidato 893833b178d9bf96183bfc398a35eb1ac7d429ab2046ef2fcebea8ff9e1cda19:
  hook nativo8002D818, solo BAG1 principal en fase1/4, clip68 y blend completo; retorno
  de base X/Z hacia home con paso ceil(error/32), máximo8 por eje/actualización.
  Conserva Y, radio, cámara, ataques/parejas y fases liberadas por sus exclusiones.
- Radio esperado derivado de RAM restaurada (raw/zoom/home), no caché del proceso;
  puntero completo validado antes del helper de versión. Reset/load olvida deduplicación.
- 36 tests host PASS9.336s, 8 mutantes por aserción; build PASS35.514s. Regeneración
  aislada3.757s cambia solo shard09, dos callbacks. No demuestra presentación en juego.
- Dos Goldfish CON HALLAZGOS: puntero/caché de restore corregidos con RED→GREEN;
  fronteras del paso y ambas rutas AOT cubiertas. No es aprobación del owner.
- Owner «si autorizo»: EXE-only experimental893833b1 y partida sin ataques. Estable5612f03a
  intacto; respaldo3b43cff8. CLIP_PUBLISHED fuente0/build1 intencionado. Sin commit/snapshot.
- Calibración bag1-center-calibration aceptada y revisada; ocho transiciones/catálogo ligados
  al runtime. Partida bag1-center-autoplay completada304.363s; restaurados150saves/configs.
- Grabación de partida RECHAZADA:4213/10245pares audio fuera100ms y ventana17.92ms;
  heartbeat stall0.408s, offset wall/frame salta0.429s con contador audio/frame continuo.
  Causa del stall no establecida; no se validaron píxeles ni se alteraron puertas.
- Reintento autorizado bag1-center-autoplay-r2 completado304.098s y restaurados150saves/configs;
  grabación RECHAZADA:2719/10023pares fuera100ms, stall0.343s trasgf16014 y salto wall/frame0.336s.
  No validación visual, bypass ni nueva repetición automática. Causa sin establecer.
- Replay de las funciones reales reproduce los tres conteos (0/3553,4213/10245,2719/10023).
  Control sintético confirma que muestras continuas + salto wall rompe el ajuste afín.
  Ambos saltos están en fase1/5/6, recentrado inactivo; origen de la pausa aún desconocido.
- Instrumentación interna implementada: CSV productor frame/muestras/SDL performance counter
  cada6fotogramas de audio; recorder conserva brackets monotónico/civil y frame repetido/ausente.
  Son solo diagnósticos; comparar deltas/frecuencia, no épocas entre procesos. Formatos PCM/sync,
  heartbeat y puertas de aceptación sin cambios; fallos del CSV no abortan captura principal.
- 39 tests PASS10.159s;6mutantes por aserción y C completo Windows/SDL3 syntax-only PASS2.568s.
  Dos Goldfish CON HALLAZGOS: filtro mtime civil y errores de I/O diagnósticos corregidos con
  RED→GREEN. Evidencia `clock-probe-mutations.json` y `capture-clock-probe-verdict.json`.
  Concurrencia heredada de muestras, coste de flush y correspondencia viva siguen sin verificar.
- Siguiente: despliegue experimental `2135d5eb…` realizado; sondas en `clock-probe-autoplay`
  probaron pausa real del productor (393.01 ms en `gf 12006..12012` mientras `wall_minus_mono`
  varió ≤0.29 ms). Toma rechazada por audio y `invalid window Z order`. Ghidra MCP activo.
- Bloque 1 `wgc-center-autoplay` (`299.291 s`, 150 saves/configs restaurados) **ACEPTADO**
  bajo `wgc` (`manifest.json` `accepted: true`, `0` rechazos): `1675` heartbeats (`0` stalls,
  jitter `10.9 ms`, `59.942 fps`), `10011` pares audio (`0` descartes, `44057 Hz`, `15.47 ms`
  p99), `bag2jp_clock_probe.csv` max `112.127 ms`, `owner.mp4` `-15.3 LUFS` / `-1.1 dBTP`.
- RAM/visual (`wgc-center-sheet1.png`, `sheet2.png`): `scale 98 -> 75`, radio `318` todo el
  baile; en `phase 1/4` P1 converge de `[-438,85]` a `root [-521,460,1]` y P2 de `[491,226]` a
  `root [518,494,4]`; `0x7FFFFFFF` en `gf 15658`, solo fever P2 (`2 Player Win`) y retorno limpio
  al selector.
- Nuevo candidato `dance-centering` (`0665a9c3…` -> `5258009e…`):
  - Intento 1 (`0665a9c3…`): calibración `dance-center-cal` (`995443c5…`) aceptada, pero toma
    `dance-center-autoplay` RECHAZADA (`stall` productor `369.73 ms` en `gf 16026`, `1065/10009` pares
    fuera de `100 ms`), y `phase 1/4` quedó congelado por usar `anim 67` (`req 101`) en vez de `anim 68`.
  - Corrección `B1CENTER_IDLE_ALT = 67u` (`5258009e…`): 20 tests host PASS (`9.481 s`), 18/18 mutantes,
    Goldfish `SIN HALLAZGOS BLOQUEANTES` (`dance-centering-anim67-verdict.json`), build `33.903 s`.
  - Calibración `dance-center-cal2` (`560c72c5…`) y toma **`dance-center-autoplay2` ACEPTADAS** bajo WGC
    (`1696` heartbeats, `0` stalls, `10145` pares audio `0` descartes, `-15.2 LUFS`). Baile (`phase 1/3`,
    radio `199`): `P1 med|dx|=94.0, med|dz|=89.5`; `P2 med|dx|=63.0, med|dz|=66.0`; fin (`phase 1/4`)
    exacto en **`P1 [-520,473,0]` y `P2 [520,520,0]`**, liberación `0x7FFFFFFF`, solo fever P2 y selector.
  - Pendiente: conformidad visual del owner sobre `owner.mp4`/láminas, luego **Bloque 2** (ataques/CAUGHT/dueto/cierre).
- Históricos: bag1-release-autoplay aceptó captura, no este nuevo centrado; el owner
  pidió corregirlo. bag1-leash-autoplay fue rechazado por audio. Ataques/CAUGHT/pareja
  siguen sin validar para estos ajustes. Mantener camera_speed2.1 y hooks de cámara inactivos.
