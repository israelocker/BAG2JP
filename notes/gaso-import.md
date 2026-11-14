---
id: gaso-import
title: "Gas-O: importación y aceptación"
tags: ["bag1", "gaso", "import", "evidence"]
summary: "Bloque 3 aceptado. Preview de retorno Gas-O corregido en experimental e709c2f8: retrato/nombre desde primera presentación revisada, Heat conservado, grabación aceptada y150saves restaurados.15tests/Goldfish; suite global466tests con1fallo/28errores sin nuevos nombres. Lifecycle CAUGHT y guard1 canónico pendientes."
related: ["plans/gaso-import.md", "IMPORT_STANDARD.md", "notes/character-pipeline.md", "HANDOFF.md"]
created: "2026-11-06"
updated: "2026-11-14"
doc_kind: evidence
---

# Gas-O — ledger canónico

## Bloque 4 y retorno al selector (2026-11-14, autorizado/en curso)

- El propietario aprobó el Bloque 3 y su checkpoint local: «Okay aprobado, continua».
  Autorizó continuar el Bloque 4 propuesto, incluida su prueba grabada experimental.
- Requisito añadido: si se eligió Gas-O, al terminar y volver al selector debe
  aparecer su preview (retrato/nombre), no Bi-O; conservar el comportamiento de Heat.
  La imagen enviada documenta el síntoma; no hace falta abrir otra captura para entenderlo.
- Plan acotado: (1) regresión del retorno/preview y corrección mínima; (2) comprobar
  lookup por rival y lifecycle reset/savestate, log positivo de VERIFY; (3) Goldfish,
  build experimental y una toma WGC del flujo relevante; (4) presentar evidencia.
  El guard canónico permanece en 0 durante investigación; su activación pertenece
  al Bloque 4 aprobado, no a esta corrección aislada. No tocar la instalación estable.
- Aceptación selector: prueba host RED→GREEN de reentrada con recursos recargados,
  selección Gas-O/Bi-O por lado y cancelación, más retorno real grabado con Gas-O
  visible sin reabrir el popup. CAUGHT requiere sus pruebas de lifecycle separadas.
- Preflight `20261114T183850029279Z-gaso-block4-selector`: PASS; 48 fuentes iguales,
  única deriva conocida `bag2jp_gaso_caught.c` (guard canónico 0/build 1), recursos iguales.
- Goldfish del cierre documental del Bloque 3 omitido: solo notas; no aplica.
- Selector: `cs_feedback_hook` conservaba `s_cur_gaso` aunque los recursos invitados
  se recargaran; retrato y nombre además descartaban la versión retenida en
  IDLE sin confirmación y en SWALLOW. Helper compartido `cs_gaso_preview` consulta
  la versión provisional solo en OPEN/REPLAY y la retenida en el resto; vblank
  invalida exclusivamente la caché host fuera del overlay del selector.
- Host RED: 4/6 fallos por assertions con los callbacks antiguos; GREEN 6/6.
  Goldfish (2 revisores: `ses_e24a10fb7ffeEiHIQquvnIxeRM`,
  `ses_e24a10f92ffekfAVkwhMUmj6of`): **SIN HALLAZGOS BLOQUEANTES** en fuente
  SHA256 `28dcd9ed9467bbb33805930e453e85dbff3aaafee4ffd0437e0874adeb60a572`.
  Cobertura insuficiente confirmada y ampliada a 12 tests: lados mixtos, REPLAY,
  Heat, escenario y caché activa. Cancelación sintetiza SWALLOW, no pulsa el pad.
  12/12 PASS (2.266 s); 2/2 mutantes por aserción (lado equivocado/caché obsoleta).
  No se repitió review del mismo código de producción. Spec y evidencias en
  `_work/goldfish/spec-block4-selector-preview.md` y `_work/gaso/block2/block4-selector-*`.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Suite global: 457 tests, 1 fallo y 28 errores (131.505 s): **no verde**.
  Fallo `test_strike_costume_assets.test_package_keeps_models_separate_from_texture_packs`
  ("Existing Heat entries must all be preserved"); errores en visual_regions,
  caught_entry y payload/assets Heat/Strike. Nombres y trazas completos conservados
  en `block4-selector-full-suite.log`; no se alteraron estos módulos para ocultarlos.
- Build `gaso-selector-return`: PASS 38.628 s (2 jobs), advertencia heredada
  `-Wa,-mbig-obj` sin uso. Deploy EXE-only `23bbdabdc6fce9f23a6839088812bf74c018b3ea940ff92ce763e32cbabbd2d2`;
  respaldo `deployment-backup-selector-return`, 5 configuraciones protegidas,
  paquetes sin cambios. Calibración `block4-selector-cal` aceptada (552 latidos,
  1 stall, 3293 pares audio/0 descartes); 9 imágenes de selector/bordes revisadas,
  catálogo `b728d1a0…`. Toma `block4-selector-return` completada309.047s con
  150 saves/configuraciones restaurados; finalización de la grabación en curso.
  El log del popup registra una nueva publicación del retrato Gas-O al retorno,
  sin reabrir el popup; aún no equivale a aceptación visual.
- **Primera toma: captura aceptada, corrección funcional parcial.**
  `block4-selector-return` WGC accepted=true:2035latidos,4tardíos,1stall117ms,
  12163pares audio/8descartes,residuo17.12ms,ventana8.95ms. READY/baile/final,
  victoria Heat, dueto natural fever2 (sin fixtures) y retorno observados.
  En `block4-selector-return-overview.png`: retrato Gas-O al retornar, pero el
  primer nombre visible aún BI-O (gf17557); a196s ya GAS-O estable. **No cerrar**
  el requisito con esa toma. Es evidencia nueva, no motivo para repetir reviews
  del mismo candidato.
- Causa acotada del nombre inicial: el descriptor solo se actualizaba al alcanzar
  el callback animado de dibujo. Nueva regresión escenario12 comprueba el nombre
  inmediatamente tras actualizar retrato, antes de invocar ese callback: RED134.
  Helper `cs_set_gaso_name` comparte los cinco bytes de descriptor y prepara el
  nombre junto al primer retrato, solo en char select; el callback por lado sigue
  reaplicándolo para variantes mixtas. 13/13 PASS4.430s; mutante de llamada temprana
  omitida muere por aserción. Fuente `1f927ef2699d5e31e5bcc3366fc7bf7c92578a11ec9cea2890617759c6960b3a`.
  Build de ese candidato PASS34.753s, **no desplegado**: Goldfish delta confirmó
  que preparar un descriptor global en el bucle de ambos jugadores deja la variante
  del último lado. El segundo revisor lo clasificó como garantía no probada;
  regresión mixta reprodujo el fallo por aserción: hallazgo confirmado.
- Causa nativa verificada (Capstone sobre007 JP, SHA e4de48f6…):
  `80093474: JAL80093504` (`0c024d41`), delay NOP, **después** hook antiguo8009347c.
  `80093504` ya consume `80096dd8 + char*8`; el hook anterior llegaba tarde y podía
  usar el nombre del otro jugador durante una trama. Evidencia acotada
  `block4-name-consumer-mips.txt`; no se modificó el proyecto Ghidra.
- Sustitución: eliminada la escritura temprana global del bucle; el MISMO hook
  de nombre/tinte se mueve a80093474, antes de cada consumidor individual, con
  guard original0c024d41. No aumenta el número de hooks ni toca cámara/Heat.
  Regresión usa el sitio realmente registrado y ambos órdenes Gas-O/Bi-O antes
  de consumir el descriptor: RED134→GREEN15/15 (4.276s), incluido opcode nativo.
  Fuente `9c7cec678d3ca1122ebf3814744005238003a08bf6bfd7c90620ab4cb55cf635`.
  Build `gaso-selector-name-consumer` PASS34.113s; ambos revisores del delta
  favorables tras comprobar la sustitución (ver `block4-selector-verdict.json`).
  Límite del review: el harness no ejecuta el JAL nativo ni demuestra el tinte
  tras esa llamada. La nueva toma debe comprobarlo, no extrapolar los tests.
  Deploy EXE-only `e709c2f8…`, respaldo `deployment-backup-selector-name-consumer`;
  calibración `block4-consumer-cal` accepted=true (546latidos,0stalls,
  3247pares audio/0descartes),9imágenes revisadas y catálogo aceptado.
  Partida `block4-consumer-return` en curso; no aceptación anticipada.
- La toma final terminó309.897s, `restoration.verified=true` y150saves originales
  restaurados. Logs: nueva publicación Gas-O al retornar, sin volver a abrir popup;
  video `_work/recordings/block4-consumer-return/owner.mp4` **accepted=true**,
  sin rechazos:2033latidos/3tardíos,1stall99ms,jitter12.06ms,59.94084Hz;
  12191pares audio/3descartes,44057Hz,residuo16.39ms,ventana10.5ms.
- **Revisión final del selector: PASS técnico.**
  `_work/gaso/block2/block4-consumer-review.png`: final/victoria Heat, fever en
  solitario y retorno; primer selector visible en muestra193s (imagen gf17532,
  t193.400) ya muestra retrato GAS-O, nombre GAS-O y fondo verde; Heat conserva
  retrato/nombre. Sigue correcto a194/195/196/199/202s, sin reabrir popup.
  `bag2_record.py frames --tag block4-consumer-return --frame 17532 --span18 --step1`
  produce37muestras revisadas en `block4-consumer-first-name-frames.png`, todas
  GAS-O/Heat, sin BI-O. WGC es VFR y puede repetir/saltar fotogramas; no se afirman
  37imágenes distintas ni latencia calibrada (±2frames sigue estimación).
  El JAL tardío mutado vuelve a fallar por aserción (consumer-mutation.json).
- Suite final del código actual: **466tests,1fallo/28errores,153.189s**;
  mismos29nombres que la corrida previa, ningún nombre nuevo. No es verde global.
  `block4-consumer-final-full-suite.log` y `block4-full-suite-comparison.json`.
  Preview aprobado técnicamente solo para P1Gas-O BAG1 A frente a Heat BAG1 A;
  lados/variantes opuestos cubiertos en host, matriz real sigue en Bloque5.
  Conformidad del propietario sobre esta corrección todavía pendiente.
- **Siguiente unidad del Bloque4 (autorizada):** resolver generación y ownership
  CAUGHT tras reset/load, con prueba host RED→GREEN y evidencia nativa pertinente;
  añadir trazabilidad positiva VERIFY. Guard canónico0 hasta resolver esas puertas.
  No repetir calibraciones/tomas del selector mientras e709c2f8 y recursos no cambien.
  No nuevo snapshot pesado: checkpoint de candidato, no cierre total de Bloque4.
- Auditoría CAUGHT: el lookup ya verifica los clips auténticos de 0/1/9 por versión
  y falla cerrado para otros rivales (harness escenario 9). Reset/load invalida
  registros host pero deja una tupla publicada en guest RAM (comentario de fuente
  684..686): sigue siendo una limitación real, no lifecycle productizado.
  No se activa el guard canónico solo para dar por terminado el Bloque 4.
- Framework pin1a3fc0db303a, `mod_runtime.cpp:2769..2800`: tras restaurar guest RAM,
  reaplica main writes e invoca los callbacks savestate de plugins activos. No se
  serializa automáticamente el ownership CAUGHT. Esta lectura es análisis de fuente,
  no una prueba de carga real. Siguiente unidad: demostrar recuperación segura del
  binding/arena tras load y generación de tablas; no inventar continuidad del host.
- `bag2jp_bag1_load_latch.h` registra solo los packs HUD53/54/125/126 y se olvida
  tras savestate; no autentica generaciones de actor/tablas CAUGHT. No reutilizarlo
  como una prueba de generación completa. El callback session_reset del framework
  prohíbe explícitamente mutar guest RAM; no resolver el residuo escribiendo ahí.

## Bloque 3: escenario, HUD y audio re-hit de Heat (2026-11-14, aceptado por el propietario)

- **Sin recompilación ni recalibración en Bloque 3**: el payload desplegado en `BAG2JP-exp-8mb` (`847058C4`, con `stage197` `b663417f` en `0x849800`) coincide con su copia canónica y de build; el código del shim `bag2jp_bag1_stage.c` es `5F19F0ED` en ambas fuentes, compilado en el EXE `ff800b28`. Son entradas diferentes verificadas por separado, no igualdad de bytes entre payload y fuente C.
- **Toma grabada `block3-stage-c`** (`_work/versus-runs/20261114T172952125209Z-block3-stage-c`, autorización previa del propietario): juego natural en autoplay (Gas-O BAG1 A vs Heat BAG1 A en `GasOBAG1`, `debug_fixtures = {}`, 150 saves y ajustes restaurados).
  - Grabación WGC `_work/recordings/block3-stage-c/owner.mp4` (`d5eee3454fd7048f…`): `manifest.json` **`accepted: true`** (`2003` latidos, `1` tardío, `0` stalls, jitter p99 `10.97 ms`, `59.941 fps`; `11977` pares audio, `0` descartes, `44055 Hz`, residual p99 `17.29 ms`, ventana `9.52 ms`).
  - `bag2jp_watch.log` (`801E0104:4`, `801E0108:1`, `801E0109:1`, `801DECC0:2`, `801DECC2:2`) y `_work/gaso/block2/take-c-review.json`:
    - `0` ataques (`0` líneas `gaso_tank` / `request 202`).
    - Eventos de puntaje B1ST: `level` `0 -> 1` en `gf10298`, `1 -> 2` en `gf12862` (nunca retrocede), `previous level` sigue al fotograma siguiente, pulso de beat flags y fin de canción `0x40` en `gf15750`.
    - Ventilador (`801DECC2`): velocidad `0` en nivel 0 (fijo en la intro), rampa a `128` en nivel 1 y a `512` en nivel 2 sostenida hasta el final (giro verificado en RAM; velocidad de rotación no separable en capturas fijas).
    - Cámara intro (`take-c-sheet-intro.png`, 17.5–27 s): tubo -> paso por el ventilador -> sala -> plano frontal -> `Ready`.
    - Rótulo HUD `GAS-O` visible y legible; pilares rojos iluminados en niveles altos (`take-c-sheet-song.png`), `1 Player Win` (Gas-O), fever en solitario y retorno limpio al selector.
    - Límites declarados: pantalla VS sigue con arte de Bi-O (fuera de alcance), velocidad del ventilador juzgada solo por RAM, sin video de referencia BAG1 para cronometrar cámara/ventilador, audio subjetivo requiere escucha humana y latencia estimada ±2 fotogramas.
- **Resolución del audio re-hit de Heat (sin cambio de código)**:
  - La comparación continua de PCM de `gaso-clamp-last-heat-bag1` (`e165817c`, `mode1` re-hit `gf7437`) contra `gaso-rehit-mode0-heat-bag1-r2` (`18590587`, `mode0` re-hit `gf8047`) en `re_hit[-200..+300]` (`367,500` muestras) da **`max_abs_diff = 0`** (bit-idéntico).
  - La diferencia detectada antes en `gaso-rehit-mode0-heat-bag1-r3` (`18590587`, `mode0` re-hit `gf7430`) a `re_hit + 46.18` fotogramas correlaciona **`1.0000`** (`rms_diff = 40.03`, `max |d_re - d_1st| = 389.0`) con `(slide_diag_1st - clamp_1st)` (`20261113T085539682518Z-gaso-slide-diag-heat-bag1`, `23015cb8`, `mode1` vs `mode1` en `1st_hit + 46.18`). En `1st - 670..-590` también ocurre una variante análoga (`|clamp - r2| = 8776.9` vs `|r2 - r3| = 27.0`).
  - Ghidra MCP (`SLPM_862.19`: `FUN_800342dc`, `0x80025500`, xrefs de `0x8002e478`) y Capstone sobre el volcado RAM `wider-initial-camera-ram.bin` confirman que la tabla `0x8007f180` (66 cues) y el callback de Heat `0x801d66e4` (`0x8003190c`) para los códigos `mode1` `1/4/0x12d/0x3e9` solo actualizan estado/llama (`0x801d9a18+0xc`), nunca disparan cues SPU. La diferencia de `r3` es una variante de voz/SFX elegida por RNG nativo; `gaso_caught_can_continue` (`mode0`) es equivalente en audio a `mode1`.
- **Cierre:** el propietario aprobó `block3-stage-c` y continuar el Bloque4 («Okay aprobado, continua»). Estado y requisito adicional del selector en la sección vigente superior. La publicación canónica CAUGHT sigue pendiente del lifecycle, no de repetir la conformidad del Bloque3.

## Bloque 2 sobre la base ±870: investigación interna (2026-11-14, estado vigente)

- Encargo: «Si continúa» (empezar el Bloque 2 por la investigación). Objetivo: ataques,
  CAUGHT y fever de dueto correctos con homes ±870. Check: tomas grabadas y aceptadas, con
  revisión fotograma a fotograma. Las partidas requieren autorización del propietario.
- Ghidra MCP (`get_program_info` → `SLPM_862.19`, javaw 63424) + `read_memory` y Capstone
  local (sin crear funciones en el proyecto):
  - El clamp nativo `0x8002D81C → FUN_8002CD48` usa `ctl+0x28` como centro y `ctl+0x38`
    como radio, y solo actúa si `dancer+3` y `ctl+0xC` son distintos de cero.
  - `0x8002ABE4..0x8002AD44` intercambia home X/Y/Z (`+0x28..+0x34`), radio y `+0x40`
    entre los controles de ambos lados, **solo si el bailarín es el personaje 10 o 14**
    (`lbu 4(s1) == 0xA/0xE`) y su raíz X cruza la del rival. b1home ya excluye 10/14; el
    caso límite es un rival BAG2 10/14 frente a un BAG1, que heredaría ±870. Va a la matriz
    de pruebas, sin cambio de código.
- Tanque Gas-O (`bag2jp_gaso_tank.h:528-531, 618-621`): sigue la raíz del rival en cada
  fotograma, sin depender de la separación. Riesgo bajo; falta comprobarlo en juego.
- RAM de `go-plus2-autoplay`: en la fever en solitario el juego fija el home del ganador a 0
  (absoluto, gf16488). El perdedor conserva -870 (en nativo serían -520). **Dueto sin
  evidencia**: no se sabe si la coreografía usa homes absolutos o los ±870 heredados.
- Fixture de dueto: `BAG2JP_TEST_P1_DUET` (`at_duet_rng`, solo con traza y guardas nativas)
  no llegaba al juego, porque `versus_session.DEBUG_ENV_ALLOWLIST` no lo incluía. Añadido
  con TDD (`test_versus_session_env.py`: RED → GREEN; 5 tests con `test_score_fixture`).
  Runner `_work/gaso/block2/run_recorded_block2.py --fixture …` (lista blanca, 2 tests).
- Goldfish (2 revisores) y triaje en `_work/goldfish/triage-block2-duet-fixture-env.md`:
  - Hallazgo alto: las guardas del dueto exigen Heat en ambos lados con trajes A/B. Con Gas-O
    el fixture nunca se activaría. Heat BAG1 sigue siendo el personaje 0 (la versión es una
    bandera aparte), y la toma `20261104T054824756883Z-heat-p1-duet-rng-hook-bag1` (Heat
    BAG1 A/B) ya registró `duet RNG seed1` y `fever2` en juego.
  - El mismo fixture fuerza puntuaciones 500000/500100: no es juego natural.
  - Corregido: `versus_session.build_game_env`/`armed_debug_fixtures` (funciones puras) y
    `result.json` registra `debug_fixtures`; el runner acepta un único fixture y rechaza
    `--fixture=`. El test del runner recorre la ruta real `run_recorded_go_plus2` →
    `run_recorded_dance_center.main`; el mutante «fixture antes de la limpieza» muere.
    Tests: 8 (env + score fixture) y 2 (runner) OK.
- Goldfish ronda 2 (`spec-block2-env-builder.md`): aprobado con cambios. `debug_fixtures`
  se toma ahora del `env` real que recibe `Popen` (test con `Popen` simulado, RED → GREEN,
  9 tests OK); el test del runner restaura `sys.modules`/`sys.path`. El EXE desplegado
  `ff800b28` contiene ambos fixtures. El árbol de compilación define
  `GASO_CAUGHT_CLIP_PUBLISHED 1`: la toma A activa la publicación del clip en juego.
  Criterios de aceptación de A y B en el triaje.
- Tomas propuestas (EXE `ff800b28…` ya desplegado, sin rebuild, escenario GasOBAG1):
  A. Gas-O BAG1 A contra Heat BAG1 A, `--fixture BAG2JP_TEST_GASO_ATTACK`: tanque/CAUGHT y
     reacción con ±870, correa 199, cierre y selector.
  B. Heat BAG1 A contra Heat BAG1 B, `--fixture BAG2JP_TEST_P1_DUET`,
     `--watch-extra 80008548:4`: fever de dueto con ±870. Aceptación: `debug_fixtures`
     correcto, línea `duet RNG seed1`, `fever2`, grabación aceptada y revisión de posiciones.
- Tomas autorizadas («Okay continúa»), EXE `ff800b28`, 150 saves y ajustes restaurados en ambas:
  - **A** `block2-attack-a` (grabación aceptada, 1998 latidos, jitter p99 11.1 ms): fixture
    de ataque ×4; tanque sobre el rival en X 682/681 (home 870 ± 199) en gf7744 y gf7947;
    CAUGHT: publicado gf7744, entrada gf7746, la segunda entrada reutiliza el clip tras
    VERIFY (camino sin log, `gaso_caught.c:401-410`), restaurado gf8165; 0 pérdidas o
    rechazos. Cues 6906/690a despachados. Correa ±870/199 hasta la liberación nativa; fever
    en solitario de Heat (home 0) y selector. Muestras de pelvis fuera de 870±199: 12/123
    (referencia sin ataque 20/123). `_work/gaso/block2/take-a-review.json`, hojas `take-a-sheet-*.png`.
  - **B** `block2-duet-b` (grabación aceptada, 2020 latidos, 28 pares de audio descartados):
    `duet RNG seed1` y puntuaciones forzadas 500000/500100 (no es juego natural); `fever2`
    en f016519. `0x80008548` = `BF54BC7E` en f016519, exactamente 9 `rand` tras la semilla 1.
    En el dueto los homes siguen en ±870 (radio INT_MAX); la coreografía acerca a los dos
    bailarines (P1 -157..-493, P2 +391..+662) y en imagen bailan juntos cerca del centro.
    `take-b-review.json`, `take-b-sheet-duet.png`.
  - Sin verificar: separación de referencia del dueto nativo con ±520, audio subjetivo y
    latencia de pantalla (±2 fotogramas estimados).
- **Conformidad del propietario** con A y B tras ver ambos `owner.mp4` («okay esta bien»,
  2026-11-14). Incluye el commit local y el snapshot propuestos. No acepta el audio por
  separado ni convierte en aceptados los candidatos offline (ventilador, cámara, eventos).
- Commit local `d327e32`. Snapshot refrescado desde el árbol de compilación (opción del propietario):
  sha256 `0793e2aa…`, 320 MB, sin `.git` ni `build-win-codex`; anterior conservado como
  `previous-20261114T172611Z`. Incluye `CLIP_PUBLISHED 1` experimental y la música BAG1.
- Bloque 3, inicio: el payload desplegado (`847058C4`) es el canónico; ventilador y cámara
  siguen solo offline; el nombre GAS-O del HUD ya se ve en las tomas.

## Referencia GO + 2 s: candidato ±870 (2026-11-14, aceptado por el propietario)

- Corrección del propietario: «la camara que tienes que tomar para la posicion inicial
  correcta debe ser 2 segundos despues de que la palabra Go aparezca». Sustituye la referencia
  READY (±1300). Revisión visual de `initial-anchor-autoplay` (26c21150…): ±1300 sin recortes,
  pero a GO+2 s los cuerpos quedaban hacia el borde exterior de cada barra.
- Limpieza conservadora aprobada («okay ve por la conservadora»): auditoría
  `_work/gaso/drift/end-center/cleanup-2026-11-14.json`, 169.771 GB liberados;
  `gaso-combined-ae-f2` y todas las tomas del 2026-11-14 intactas.
- Medición `go-plus2-measure` aceptada (323 heartbeats, 0 stalls, 1909 pares audio sin
  descartes;150 saves/configs restaurados). "Go!" visual t=26.747 s; a GO+2 s la cámara ya está
  asentada (T=[0,692,3028], H=384). Con factor GTE 0.75 y OFX256, guías 235/727 sobre 960px
  dan -870.11/+874.90 a Y=460: candidato simétrico `B1HOME_WIDE=870` (zoom128: 435 exacto)
  proyecta 235.03/725.62. Modelo: `solve_go_plus2.py`, `go-plus2-measure/solution.json`.
- TDD: test RED (exit134) antes del cambio; 23 tests PASS 12.416 s; 11/11 mutantes por
  aserción detectados. Goldfish `ses_e257b132…` PASS condicional y `ses_e257b106…` con
  hallazgos no bloqueantes (muestra +0.69 s tras GO+2 s; ancla Y=0/Z=0 frente a raíz animada;
  zoom128 sin composición leash+home en host). Triaje: `_work/goldfish/triage-go-plus2-anchor.md`.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Build `go-plus2` PASS; EXE `ff800b2857a43c8924473c03dc0c7df04c2658aaa9c3188bc19061b0de8900df`
  desplegado EXE-only (respaldo `deployment-backup-go-plus2`, 5 protegidos, paquetes intactos).
  Calibración `go-plus2-cal` aceptada (546 heartbeats, 0 stalls, 3271 pares audio sin
  descartes), 11 imágenes revisadas, catálogo `d5340edb…` ligado.
- Partida `go-plus2-autoplay` (Gas-O BAG1 vs Heat BAG1, escenario Gas-O, sin ataques):
  **accepted=true**, 1999 heartbeats, 1 stall, 11975 pares audio sin descartes, residual p99
  17.2 ms; 150 saves/configs restaurados; `owner.mp4` SHA `eafd73e9…`.
  - GO+2 s (t=29.242 s, "Go!" en 27.242 s): cuerpos ~215 px (Gas-O) y ~735 px (Heat) frente
    a guías 235/727; `go-plus2-autoplay/go-plus-two-annotated.jpg`. La muestra RAM más
    cercana llega +0.88 s tarde; los homes son fijos, pero raíz/cuerpo exactos en ese
    fotograma quedan como estimación visual.
  - RAM 123 muestras de baile: homes ±870, radio 199; X P1 [-1084,-658], P2 [641,1091].
    Final anim67/68 converge a [-870,312,0]/[870,520,0]; liberación INT_MAX; fever f016348.
  - Hojas `go-plus2-match/` (baile, final, fever) sin recortes ni saltos visibles; vuelta al
    selector verificada. Cámara nativa gira durante el baile: no se fija al HUD.
- **Conformidad del propietario (2026-11-14):** «Si, está bien, procede», tras ver la imagen
  anotada GO+2 s. Commit local WIP del árbol completo autorizado (alcance elegido por el
  propietario; excluye `.agents/skills`, `tools/ffmpeg-skill` y logs sueltos). Snapshot
  aplazado hasta cerrar el Bloque 2. Siguiente: Bloque 2 (ataques/CAUGHT/dueto/cierre).

## Posiciones iniciales más separadas bajo cada barra (2026-11-14, histórico READY ±1300)

- Continuación autorizada: «Okay continúa con las correcciones». Medición desde antes de
  entrar al escenario, no desde el baile: `initial-alignment-measure3` aceptada (296 heartbeats,
  0 stalls,1771 pares audio,0 descartes;150 saves/configs restaurados). Las dos mediciones
  anteriores quedaron rechazadas tras errores del wrapper y se conservan como fallos.
  Regresión mock RED→GREEN corrigió `stop_recording()` sin argumentos y el conflicto de screenshot.
- Corrección del modelo anterior: faltaba el factor horizontal GTE16:9 de0.75. Ghidra MCP
  (`get_program_info` primero, mainJP) verifica offset256/120 mediante lectura8002DCFC/12B.
  En READY gf7314 de la toma aceptada, ambas anclas±700 proyectan dentro de sus barras;
  la cámara de introducción barre distintas posiciones. `initial-alignment-solution.json`
  calcula anclas -1305.08/+1305.07 para guías x235/727 sobre960px; candidato simétrico±1300
  proyecta235.95/726.04. Esto es proyección del **ancla**, no del cuerpo: las raíces animadas
  extrapoladas dan215.01/722.31. En GO la cámara cambia: no se promete alineación en todos
  los ángulos ni se bloquea al HUD.
- Nuevo candidato: solo `B1HOME_WIDE=1300` en `bag2jp_bag1_home.h`; mismas guardas nativas,
  radio199 derivado de referencia520 (zoom128: home650/referencia260/radio99), cámara intacta.
  Callback real observado RED antes del cambio;23 tests PASS13.494s y10/10 mutantes por
  aserción. Se conserva caché obsoleto INT_MAX en la regresión de restore hacia±1300.
  Goldfish `ses_e25996867ffeAombr17TQPTiO6` y `ses_e259950f8ffe0lYlPUPfV4jXC9`:
  hueco de restore corregido; alineación de cuerpo y recorte pendientes de partida real.
  Triaje/hashes: `_work/goldfish/initial-anchor-verdict.json`.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Build `20261114T141530983858Z-initial-anchor` PASS31.25s; solo header staged con respaldo
  `staging-backup-initial-anchor`, AOT sin cambios. EXE
  `26c211504ddaac90a0578dac7664117c682947723a5ab5dae10bef93bf7217fb` desplegado EXE-only;
  respaldo effb8edd en `deployment-backup-initial-anchor-deploy`,5 protegidos/paquetes intactos.
  Calibración `initial-anchor-cal` en curso. Wrapper completo empieza antes del escenario y
  termina al volver al selector; test mock de límites PASS. Falta grabación aceptada y revisión
  READY/GO, recorte durante baile, pose final, fever y selector. Sin Bloque2, commit ni snapshot.

- Antecedentes de ±700 y diagnóstico (no estado actual del candidato):
- Petición: «Okay veo ya desde el inicio estan muy juntos, osea su posicion inicial
  deberian estar mas separados basicamente deberian iniciar estando a la mitad de sus
  respectivas barras de puntaje, si me dejo entender? para que asi conserven esa posición
  inicial mas separadas, puedes revisar eso?» Sustituye pedir conformidad del centrado
  anterior. Tras la propuesta, el propietario autorizó implementar y obtener evidencia
  experimental grabada; esa autorización no incluye ataques/CAUGHT/dueto, commit ni snapshot.
- Objetivo/check: en la vista inicial, situar cada bailarín bajo el punto medio de su
  propia barra; después conservar esas nuevas referencias X/Z del escenario durante
  baile y pose final. No centrarlos en X=0 ni fijar su proyección al HUD cuando gire la cámara.
- Contraste fresco Ghidra MCP: `get_program_info()` identifica main JP `SLPM_862.19`
  (`ea5a1668…`, sin overlay identificado); `decompile_function_by_address` y
  `disassemble_function` de `0x8002B5BC` confirman tabla `0x80051918`, zoom stage+4 y
  llamada `0x8002BA18` (`0x0C00B617`) a `FUN_8002D85C` con vector inicial en `a2=sp+0x10`.
  `read_memory(0x80051918,12)` devuelve `82 82 82 82 82 56 82 82 82 82 82 82`;
  caso ordinario: ±130×4×zoom/256 = ±520 a zoom256, escenario5 ±344; escenario0xB,
  modo4, bailarines auxiliares y personajes especiales tienen rutas distintas.
- Verificación independiente: `py -3.13 _work/gaso/drift/end-center/audit_wider_home.py`
  contrasta tabla y palabra JAL con el EXE original y homes ±520 con el muestreo de
  `dance-center-autoplay2`; reporte/hash de entradas en `wider-home-audit.json`.
  Preflight `wider-home-review` pasó; esa primera revisión todavía no modificaba el runtime.
- Revisión visual de la grabación aceptada anterior (no una nueva validación): FFmpeg
  `probe.py` + `look.py` extraen t=0.100/1.546/139.117 s; la primera y la última muestran
  bailarines hacia el interior de sus barras. `wider-home-score-guides.png` señala los
  centros aproximados del interior de las barras (x235/727 sobre imagen960); no muestra
  una modificación del juego ni una solución 3D. Cámara y pose cambian entre fotogramas.
- Riesgo identificado: subir |home| sin otro ajuste amplía también el radio actual
  `round(|home|*300/784)`. Preservar la correa ceñida ya verificada (199 en este escenario)
  o recalcularla desde la escala nativa; no deshacer el recentrado al abrir la separación.
- Medición nueva autorizada: `wider-home-camera-baseline`, runtime5258009e sin modificar,
  run `20261114T125357316658Z-wider-home-camera-baseline`; ocho snapshots RAM8MB de solo lectura.
  Grabación **aceptada**:71 heartbeats,0 stalls,421 pares audio,0 descartes. Cámara estable:
  matriz8005D0F0, focal8006D98C=384, eye[13,1550,3041], target[-1,529,10].
  `solve_wider_home.py`/`wider-home-projection.json` calcula X=-687.10/+686.87 para las guías
  x235/727, usando alturas de referencia473/520 y offset geométrico supuesto256/120.
  Candidato simétrico **±700**, no alineación visual aceptada: proyecta x230.40/731.72.
- Implementación compartida experimental: `bag2jp_bag1_home.h` y callback antes del
  JAL8002BA18 verifican versión BAG1 principal, controlador/actor/stack, stage estándar,
  zoom y vector nativo. Solo cambian vector.X; el inicializador nativo conserva Y/Z/yaw.
  Stage5/B, modo4, chars10/14, auxiliares y BAG2 quedan fuera. Referencia del radio derivada
  de RAM mapea home±700 a referencia nativa±520 tanto en leash como en centro: sigue199,
  no268. No añade caché de home ni modifica cámara. Prueba RED anterior detectó268;
  suite leash11 PASS9.630s y callback home2 PASS en la comprobación posterior.
- Generación nativa aislada `generate_wider_home.py`: emisor42508148…,3.742s, cambia solo
  `SLPM_862.19_full_08.c`, añade una llamada8002BA18; no edición manual de código generado.
  El test de registro detectó primero la falta de opt-in; añadido a `patches/BAG2JP-game.toml`.
- Host final del cambio: home+leash13 PASS6.738s, cinco pruebas relacionadas y cinco AOT
  aprobadas en sus ejecuciones registradas; no una ejecución única de23. Baseline y nueve
  mutantes de home detectados por aserción. La primera mutación stageB sobrevivió por una
  tabla sintética incompleta; corregida la tabla realista, quedó detectada.
- Goldfish: `ses_e25d1bd64ffeMWGeFZrhwrDDw9` SIN HALLAZGOS BLOQUEANTES y
  `ses_e25d19d55ffeTvJxXHb4HvE8Tt` CON HALLAZGOS de cobertura. Triaje en
  `_work/goldfish/wider-home-verdict.json`: fixture18, centrado/restore real hacia700 y
  negativos independientes corregidos; protección AOT existente contrastada y reforzada.
  La alineación real del HUD sigue pendiente de grabación, no se deduce de tests host.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Build `20261114T131533246564Z-wider-home` PASS33.54s, tras staging con respaldo
  `staging-backup-wider-home`. EXE `effb8edd971992655aa06ce88d05b21e65dc83b73e742265f5ebc45597612216`.
  Despliegue EXE-only experimental verificado; respaldo5258009e en
  `_work/gaso/deployment-backup-wider-home-deploy`, cinco archivos protegidos y paquetes intactos.
- Calibración `20261114T131812464991Z-wider-home-cal`:150 saves/configs restaurados;
  grabación WGC **aceptada**,484 heartbeats,0 stalls,2883 pares audio,0 descartes.
  Selector y ocho transiciones revisados en `wider-home-cal-main.jpg`/`wider-home-cal-probes.jpg`;
  catálogo ligado a effb8edd, digest `e87fbe8a7348c38da2650d3ddbbdfda5778b6d831d56d4a27a4e69b993d70622`.
- Partida autorizada completada: `20261114T132537881098Z-wider-home-autoplay`, Gas-O BAG1
  contra Heat BAG1 en GasOBAG1, sin ataques,299.531s; restauración150 saves/configs verificada.
  `_work/recordings/wider-home-autoplay/manifest.json`: **accepted=true**, rejections vacías,
  WGC y182 comprobaciones de ventana aprobadas;1714 heartbeats,1 tardío,59.942fps,
  jitter p9911.27ms. **Una pausa de63ms tras gf7992**, no cero pausas; las puertas originales
  aceptaron la toma. Productor7992→7998=211.2175ms entre muestras nominales de100ms.
  Audio exacto del juego:44057Hz,10279 pares,0 descartes,residual p9916.01ms,ventana6.97ms;
  owner.mp4 medido -15.3LUFS/-2.2dBTP/LRA7.1LU, sin modificar audio ni retimar video.
- RAM y revisión propia:123 muestras de baile mantienen homes[-700,+700],radio199;
  medianas |dx|91/73 y |z|68/63. En fase1/4 se ejercitan **anim67 P1 y anim68 P2**;
  gf15306 raíces[-694,411,-78]/[748,512,73] convergen a gf15486/15546
  **[-700,312,0]/[700,520,0]**. El diferente Y es de la pose, no un nuevo puesto Z.
  Liberación nativa INT_MAX en fase1/5, fever posterior y regreso al selector comprobados.
  Reporte `wider-home-run-analysis.json`;13 fotogramas consecutivos por intervalo inicial,
  transición final y fase liberada en `wider-home-visual-frames.json` y hojas correspondientes.
- **Resultado visual parcial, no aceptación final del requisito:** el inicio gf7123..7135
  muestra más separación; Gas-O queda cerca de su guía, pero Heat todavía hacia el interior
  de la mitad de su barra. La solución proyectiva anterior era una aproximación con offset
  supuesto y cámara de otra toma: el snapshot nuevo mide eye[-14,1167,3209],target[-1,487,12],
  distinto del baseline. No usar el cálculo ±687 ni los homes±700 como prueba de alineación
  exacta en píxeles. La corrección funcional de anclas/radio/final sí quedó observada.
  `wider-home-owner-sheet.jpg` muestra las guías aproximadas, final, fever y selector;
  conservar candidato experimental y declarar pendiente afinar la alineación inicial.
  Video `_work/recordings/wider-home-autoplay/owner.mp4`, logs y RAM en el run anterior.
  Precisión±2 fotogramas estimada; calidad subjetiva del audio reservada al humano.
  Sin Bloque2, commit ni snapshot. Siguiente: mostrar evidencia y recoger conformidad sobre
  esta separación aproximada; si se exige coincidencia con ambas mitades, afinar proyección
  contra la cámara real antes de otro candidato, sin introducir bloqueo al HUD.
- Herramientas: Ghidra MCP recuperado por puente instalado, sin duplicar GUI ni instalar;
  FFmpeg y script determinista usados sobre evidencia existente. Sin funcmatch/Capstone:
  no se buscaban equivalentes BAG1 y Ghidra respondió. Sin modelos locales: análisis corto
  de código nativo y proyección, no trabajo mecánico masivo. Recorder usado para medición
  autorizada; dos revisores Goldfish convocados para este cambio de fuente. Tiempo/ahorro no medidos.

## Centrado X/Z de la pose final BAG1 (2026-11-14, antecedente verificado)

- Requisito del propietario tras ver la toma anterior: «al final si estan separados pero
  deberian estar mas centrados, uno se ve mas adelante que el otro, centralos mas como
  cuando iniciaron». La toma anterior está aceptada técnicamente, **no** como resultado visual.
- Causa contrastada: `anim45` lleva a ambos a extremos Z opuestos y `anim68` conserva
  el desplazamiento dentro del círculo. En gf15504: raíces `[-380,473,-275]` y
  `[649,520,272]`, puestos iniciales X=−520/+520, Z=0. Un radio menor no aporta retorno
  interior; el muelle BAG1 original tampoco actúa dentro del radio.
- Corrección acotada experimental: `bag2jp_bag1_center.h`, llamada desde
  `bag2jp_bag1_versions.c` en el sitio nativo `0x8002D818` (`0x8E660038`), después
  del reanclaje/blend y antes del recorte y consumidor de pose. Solo principales BAG1,
  fase `1/4`, clip68 con blend completo, actor/clamp activos, modo1/2 y sin pausa.
  Retorno de **base X/Z**, `ceil(|error|/32)` con máximo8 unidades/eje y una vez por
  actor/VBlank. No escribe raíz, Y, registros, radio ni cámara; excluye otros clips/fases
  y radio ilimitado. El baile anterior y las rutas nativas de victoria/derrota quedan fuera.
- El radio válido se deriva de RAM restaurada: tabla raw × zoom y proporción del puesto;
  no depende del caché host del leash. Esto permite retomar un estado318 después de haber
  cacheado la liberación INT_MAX. El leash previo no cambia. Reset/load compuesto conserva
  `b1load_forget` y limpia el nuevo latch; se usa una sola inscripción de la API real.
- Host: regresión RED→GREEN con las posiciones medidas, convergencia sintética en≤160
  actualizaciones, exclusiones, punteros extremos, pausa, restauración318→INT_MAX→318,
  pasos firmados en límites32, no modificación de Y/radio/CPU. Última suite relacionada:
  **36 tests PASS, 9.336 s**; **8 mutantes detectados por aserción**. Evidencia en
  `_work/gaso/drift/end-center/mutations.json`; no prueba la presentación real del juego.
- AOT: regeneración aislada3.757s, solo cambia `SLPM_862.19_full_09.c` en sus dos
  ocurrencias del sitio; test exige ambas. Config canónica añade solo `0x8002D818`.
  Hooks de cámara `0x80014FB8/0x80014FD4` siguen fuera; mantener `camera_speed=2.1`.
- Goldfish: dos revisores nuevos (`ses_e271d8a15ffeeo0UH9Gxg8XPpV`,
  `ses_e271d6ae7ffeBo00UO3xgl062D`), ambos **CON HALLAZGOS**. Confirmados y corregidos
  con regresiones: lectura de actor+4 antes de validar el bloque completo, caché del leash
  obsoleto tras load, cobertura exacta de pasos y de ambas ocurrencias AOT. Corregido además
  un fallo de compilación propio: API `savestate_load_plugin` inexistente; el callback
  compuesto usa `psx_mod_register_savestate_plugin`. No se presenta la auto-verificación
  posterior como otro Goldfish. Spec y triaje: `_work/goldfish/spec-bag1-end-center.md`
  y `_work/goldfish/bag1-end-center-verdict.json`.
  **Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.**
- Primer build falló por esa API en30.039s; log en
  `_work/workflow/20261114T070755808015Z-bag1-end-center/build.log`. Fuentes corregidas
  copiadas con hash previo y respaldo nuevo en `end-center/review-fixes-build-backup`;
   build `bag1-end-center-reviewed` **PASS, 35.514 s**, dos jobs. EXE candidato SHA-256
   `893833b178d9bf96183bfc398a35eb1ac7d429ab2046ef2fcebea8ff9e1cda19`.
   Métricas: `_work/workflow/20261114T071651559442Z-bag1-end-center-reviewed/metrics.json`;
   hashes de candidato/instalaciones: `_work/gaso/drift/end-center/build-hashes.json`.
    Es prueba de compilación/enlace, no de aceptación en partida.
- El propietario respondió «si autorizo» al despliegue solo experimental y una partida
  grabada sin ataques. EXE-only desplegado con hash893833b1 y respaldo del anterior3b43cff8
  en `_work/gaso/deployment-backup-bag1-end-center/report.json`; cinco configuraciones
  protegidas y paquetes sin cambios. No autoriza ataques, commit ni snapshot.
  Calibración `bag1-center-calibration` completada y grabación aceptada: 597 heartbeats,
  jitter p99 11.6 ms, audio residual p99 15.25 ms. Revisados video y diez capturas;
  catálogo de ocho transiciones aceptado para este runtime. Restaurados 150 saves.
- Herramientas: MCP confirmó JP `SLPM_862.19` y bytes del seam; se reutilizan el análisis
  y la toma previa, no nuevas búsquedas masivas. Grabador y FFmpeg se usaron para la
  calibración autorizada; la partida `bag1-center-autoplay` terminó una sola vez.
  `funcmatch` no aporta a un equivalente ya confirmado. Ahorro no medido.
- Partida completada en304.363s: `_work/versus-runs/20261114T072915522621Z-bag1-center-autoplay`;
  restauración de configuraciones y150saves verificada. Finalización única del grabador
  **RECHAZADA**, exit1/`accepted=false`:4213/10245pares de audio fuera de100ms y una
  ventana17.92ms fuera del ajuste. No usar sus píxeles para validar gameplay ni el recentrado.
- Diagnóstico acotado: heartbeat registra stall0.408s trasgf16008; contraste independiente
  encuentra salto de offset de reloj real0.429s y contador audio/fotograma continuo.
  Causa de la pausa de planificación no establecida. Evidencia:
  `_work/gaso/drift/end-center/rejected-capture-diagnostic.json` y manifiesto original;
  no se reparó, recortó ni relajó la puerta para aceptar esta toma.
- Owner respondió «Si autorizo continua»: autoriza repetir con el mismo candidato,
  sin ataques. `bag1-center-autoplay-r2` lanzada una sola vez con wrapper revisado;
  reutiliza calibración/catálogo, EXE y puertas sin cambios. Completada304.098s en
  `_work/versus-runs/20261114T075559301619Z-bag1-center-autoplay-r2`; configuraciones y
  150saves restaurados/verificados. Finalización única **RECHAZADA**, exit1/accepted=false:
  2719/10023pares de audio fuera100ms;1677heartbeats,6tardíos,59.945fps,jitterp9915.43ms,
  stall0.343s trasgf16014. No se inspeccionaron sus píxeles para validar el centrado.
- Contraste del reintento: offset wall/frame salta0.336s alrededor del stall, sin saltos
  de muestras>2205 entre fotogramas consecutivos. Es recurrencia del síntoma, no causa
  demostrada. `_work/gaso/drift/end-center/retry-rejected-diagnostic.json` conserva
  contraste, restauración y hashes de ambas instalaciones; estable5612f03a sin cambios.
  No se modificaron puertas ni se reparó/recortó/re-finalizó la toma para aceptarla.
- Diagnóstico interno posterior: `py -3.13 _work/gaso/drift/end-center/replay_capture_clock.py`
  reproduce con `HeartbeatClock`/`audio_placement` de producción exactamente0/3553,
  4213/10245 y2719/10023 pares descartados para calibración, primera toma y reintento.
  El control sintético sin discontinuidad pasa; saltos wall de0.343/0.408s con muestras
  continuas son rechazados por la misma puerta, sin cambiarla ni re-finalizar originales.
  Evidencia: `_work/gaso/drift/end-center/capture-clock-replay.json`.
- Mecanismo confirmado del rechazo: el video usa tiempo real y el dump cuenta muestras
  por fotograma emulado; un solo ajuste afín no representa la discontinuidad entre ambos.
  Esto no demuestra corrupción del audio ni identifica el origen de la pausa.
  Los dos saltos caen en fase1/5/6 (clips100/96 y95/99), fuera del recentrado fase1/4/clip68.
  En r2 otra lectura del proceso observógf16014 a wall1794643228.7343493 dentro del hueco.
  No basta para distinguir una pausa real del productor de un salto compartido de reloj:
  el heartbeat y el sync carecen de marca monotónica emitida por el productor.
- El diagnóstico anterior solo cambió `_work/` y documentación: Goldfish omitido para
  esa fase. El owner respondió «Okay, continua» a la instrumentación interna; resultado:
  `bag2jp_anim_trace.c` añade `bag2jp_clock_probe.csv` cada6fotogramas de audio con
  `frame,samples,producer_ticks,producer_hz` (SDL3 performance counter, lectura antes de I/O).
  El recorder añade `clock_observations.csv`: frame incluso repetido/ausente y brackets
  monotónicos/civiles antes/después de leer heartbeat. Comparar deltas/frecuencia dentro
  de cada reloj; no asumir épocas iguales entre procesos.
- Compatibilidad: WAV, sync de dos columnas, heartbeat y puertas de aceptación sin cambios.
  Los CSV nuevos son diagnósticos, no inputs de `HeartbeatClock`/`audio_placement` ni prueba
  automática de pertenencia a sesión. Ausencia, fallo de apertura/escritura/cierre o copia
  del diagnóstico avisa y no aborta la captura principal. Se conserva el probe ambiguo;
  identidad inicial/final queda registrada, sin descartar por mtime civil si el reloj retrocede.
- Verificación host: 39tests PASS10.159s (`test_audio_clock_probe`, `test_bag2_record`,
  `test_anim_trace_samples`, `test_recording_window`); fixture C usa callbacks reales,
  reloj controlado y salto343ms. Se fijan formatos antiguos y fallos opcionales. Dos baselines
  y6mutantes por aserción pasan en `clock-probe-mutations.json` bajo
  `_work/gaso/drift/end-center/`; fuentes copiadas, originales nunca mutadas.
  `check_clock_probe_compile.py` valida el C completo con comando real Windows/SDL3:
  syntax-only PASS2.568s; reporte `clock-probe-compile/report.json`. No prueba enlace ni ejecución viva.
- Goldfish: dos revisores nuevos (`ses_e26d9a8a4ffeU1j3FIn73PieGG`,
  `ses_e26d9a89cffeOueTP3G9cIY9FP`), ambos **CON HALLAZGOS**. Confirmados y corregidos
  con RED→GREEN: mtime dependiente del reloj investigado y escritura diagnóstica que podía
  abortar la captura. Añadidos frame ausente y errores header/flush/cierre. Límites no verificados:
  coherencia concurrente del contador de muestras heredado, coste de flush y correspondencia viva.
  Dictamen/inputs en `_work/goldfish/capture-clock-probe-verdict.json`.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Staging con respaldo y compile/link de la instrumentación: `PASS`, 33.144s, enlace
  `BAG2JP.exe` `2135d5eb6ef70755c2272c32057ad2c58bf3e2cf47c5aca45db142f8be59a780` en árbol de compilación; respaldo previo en
  `_work/gaso/drift/end-center/staging-backup/20261114T084258Z/bag2jp_anim_trace.c`.
- Despliegue EXE-only y corrida diagnóstica autorizados («Continua»): `deploy_verified_exe.py --tag clock-probe --preserve-canonical-feature-manifest` desplegó `2135d5eb…` en `BAG2JP-exp-8mb` (respaldo `_work/gaso/deployment-backup-clock-probe/report.json`; estable `5612f03a…` intacto). Calibración `clock-probe-calibration` (`106.143 s`, 150 saves restaurados): catálogo visualmente revisado y ligado (`reviewed_catalog_sha256: 790f91c6…`), pero video rechazado por `heartbeat jitter p99 22.7 ms > 1 frame` (audio 0 descartes). Partida `clock-probe-autoplay` (`295.946 s`, 150 saves restaurados): **RECHAZADA** por `1874/7595` pares >100 ms, ventana 1 s de `119 ms` y `capture: invalid window Z order` a los ~127.5 s (`stalls: [{after_frame: 12006, seconds: 0.292}]`).
- Causa del fallo de audio probada (`analyze_clock_probe_autoplay.py` → `_work/gaso/drift/end-center/clock-probe-autoplay-analysis.json`): `clock_observations.csv` mantuvo `wall_minus_mono_rel_ms` en `[-0.0015, +0.2891] ms` (sin salto del reloj civil), mientras `bag2jp_clock_probe.csv` registró una pausa real del productor/emulación de **393.01 ms** entre `gf 12006` y `gf 12012` (`ds = 4409` muestras ≈ 100 ms), en `mode2 phase 1/3/3 fever0` (antes de fever y del recentrado `phase 1/4 clip 68`). El origen interno de esa pausa puntual en el emulador sigue abierto; Ghidra MCP re-establecido (`javaw` PID 63424, `SLPM_862.19` SHA `ea5a1668…`).
- Integración WGC (`gfxcapture`) para grabar con ventanas encima (autorizada por owner): FFmpeg 8.1 (`n8.1.3-35-gf1acb0a266-20261113`) instalado en `D:\Dev\Tools\ffmpeg-wgc\ffmpeg-n8.1-latest-win64-gpl-8.1\bin\ffmpeg.exe` (`D:\ffmpeg\bin\ffmpeg.exe` intacto). `tools/test/bag2_record.py` (`--capture-backend {auto,wgc,gdigrab}`, default `auto`) y `tools/test/recording_window.py` (`require_uncovered=False`) capturan por `HWND` ignorando ventanas superpuestas y movimiento `(x, y)` sin fijar topmost ni foco, manteniendo guarda de PID, token `SetPropW`, visibilidad, no minimización y tamaño cliente (`rect[2:]`); `parse_ffmpeg_start` acepta `gdigrab` y `lavfi` con `-use_wallclock_as_timestamps 1` (`start >= 1.0e9`).
- Verificación WGC: **45 tests host PASS en 7.162 s** (`test_recording_window`, `test_bag2_record`, `test_audio_clock_probe`, `test_anim_trace_samples`); E2E vivo con ventana Win32 `320x240` totalmente tapada (`_work/gaso/drift/end-center/wgc-e2e-smoke/`): `review_mid_wm_timer.png` mostró `gf 253 == E2E 253` y la corrida con audio obtuvo `accepted: true`, `capture_backend: "wgc"`, `jitter_p99_ms: 4.5`, `stalls: 0`, `audio dropped: 0`. Goldfish (`_work/goldfish/wgc-capture-integration-verdict.json`): dos revisores **SIN HALLAZGOS BLOQUEANTES** (`ses_e265f0a9effewK76LIUQpl6gqe`, `ses_e265f0a9cffepl5GdjBuDpqwK7`); 3 ajustes menores aplicados y re-probados.
- Partida real del **Bloque 1** autorizada («Si procede»): `wgc-center-autoplay`
  (`_work/versus-runs/20261114T104433736313Z-wgc-center-autoplay`, `299.291 s`,
  `150` saves y configs restaurados/verificados) con backend `wgc` sobre `BAG2JP.exe` `2135d5eb…`:
  - Grabación `_work/recordings/wgc-center-autoplay/manifest.json` **ACEPTADA** (exit `0`,
    `accepted: true`, `0` rechazos): `1675` heartbeats (`0` perdidos), `jitter p99: 10.9 ms`,
    `59.942 fps`, `0` stalls, `10011` pares de audio (`0` descartes, `44057 Hz`,
    residual p99 `15.47 ms`, ventana `6.34 ms`), `window_guard` (`checks: 175`,
    `require_uncovered: false`, `passed: true`), `producer_clock_copied: true`
    (`bag2jp_clock_probe.csv` p50 `100.124 ms`, p99 `104.795 ms`, max `112.127 ms`, sin pausas;
    `wall_minus_mono` en `[-0.0011, +0.2705] ms`), loudness `owner.mp4` `-15.3 LUFS` / `-1.1 dBTP`.
  - Muestreo RAM/watch y hojas visuales (`_work/gaso/drift/end-center/wgc-center-sheet1.png`,
    `wgc-center-sheet2.png`): `scale 98 -> 75`, radio `318` durante todo el baile (`gf 6582..15594`);
    en `phase 1/4` (`gf 15402..15654`) P1 converge suavemente de `[-438, 85]` a `root [-521, 460, 1]`
    y P2 de `[491, 226]` a `root [518, 494, 4]` sin saltos; en `gf 15658` (`phase 1/5/6`) ambos
    liberan a `0x7FFFFFFF`, se completa el solo fever P2 (`2 Player Win`) y regresa limpio al
    selector (`returned-selector.png`).
  - Pendiente: conformidad visual del propietario sobre `owner.mp4`/hojas de contacto, y **Bloque 2**
    (ataques/`CAUGHT`/`fever-duet-sync` con autorización explícita) más **cierre final**
    (commit/snapshot). Sin commit ni snapshot todavía; estable `5612f03a…` intacto.
- Nuevo requisito del propietario tras revisar `gf 15583` de `owner.mp4` (2026-11-14):
  «Puedes hacer que se centren aun mas? quiza que mientras esten bailando se sigan centrando o algo
  pero que no se alejen tanto del centro» — aclarando explícitamente que «centro» significa
  «la posicion inicial a la cual comenzaron, no al centro o en medio de la pantalla».
  Diagnóstico de `wgc-center-autoplay/leash-actor-samples.jsonl`: en `phase 1/3` (`124` muestras),
  el radio `318` permitía deriva libre en `P1 X=[-838,-181], Z=[-323,331]` y
  `P2 X=[175,858], Z=[-340,343]` porque `FUN_8002CD48` no actúa dentro de `dist <= radius`.
- Candidato `dance-centering` (`BAG2JP.exe` `0665a9c333cea85b5dda205426ca602049b969435ab15a9bdc45a3a8da1aecc9`,
  enlazado en build tree, **sin desplegar**):
  1) `bag2jp_bag1_leash.h`: aprieta `B1LEASH_BAG1_RADIUS` de `480` a `300` sobre `784` (`199` para
     `|home|=520`, `132` en escenario 5, `99` en zoom `128`).
  2) `bag2jp_bag1_center.h`: mantiene pose final `phase 1/4` (`anim 68`, paso `ceil(|err|/32)`, máx `8`)
     y añade centrado continuo durante baile normal `phase 1/3` (`deadzone=16`, `divisor=48`,
     `max_step=3` hacia `(home_x, 0)`), restringido a `b1center_radius_ready` (excluye `0x7FFFFFFF`/fever),
     `ctl+4 == 0x1000`, `anim <= 72` y `!b1center_attack_busy()` (lecturas alineadas de `0x8005E748/54/78/84`).
     En `20261113T190419608874Z-gaso-combined-ae-f2` (`f=6658..15000`), `0x8005E748/54` fueron `(0,0)` en
     baile normal y no-cero en ataques/cooldown; `0x8002D7A0..0x8002D8D4` y `005.dbi 0x8009A548/560/5A0`
     verificados con Capstone (tras caída de Ghidra MCP en `decompile_function_by_address`).
- Verificación host y compilación:
  - `py -3.13 -m unittest -v tools.test.test_bag1_leash tools.test.test_bag1_dancer_scale tools.test.test_mod_instruction_sites tools.test.test_ap2_no_attack tools.test.test_gaso_hud_runtime tools.test.test_bag1_stage_shim`:
    **20 PASS en 11.853 s** (RED→GREEN; incluye exclusiones de bytes vecinos de ataque, `slot 2`, `mode 1`,
    `anim 0/72/73`, `b1v_restore` -> `b1leash_forget()` y bytes reales en `SLPM_862.19`/`005.dbi`).
  - `py -3.13 _work/gaso/drift/end-center/check_dance_center_mutations.py`: baseline PASS + **17/17 mutantes
    por aserción KILLED_ASSERTION** (`dance-mutations.json`).
  - Dos revisores Goldfish en frío (`ses_e2630ff74ffeExl05RwlKv9o87` CON HALLAZGOS no bloqueantes,
    `ses_e2630fc9dffee4DDy4W5fk3JW8` SIN HALLAZGOS BLOQUEANTES; `_work/goldfish/dance-centering-verdict.json`).
    Aplicadas las 4 mejoras menores (quitar `b1center_axis` sin uso, añadir `b1leash_forget()` en
    `b1v_restore()`, cubrir bytes vecinos/slot 2/bordes y fijar direcciones/offsets en `SLPM_862.19`/`005.dbi`).
    Límite declarado: modelo host simplifica `FUN_8002C404`; falta validar suavidad visual, ataques/hitstun,
    fever, savestates y retorno en partida real.
    Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
  - Staging con respaldo (`_work/gaso/drift/end-center/staging-backup-dance/`) y `bag2_workflow.py build --tag dance-centering`:
    PASS en `35.69 s` (`[5/5] Linking CXX executable BAG2JP.exe`, cero advertencias en los archivos modificados).
- Siguiente: pedir autorización del propietario para desplegar `0665a9c3…` en experimental `BAG2JP-exp-8mb`
  (manteniendo estable `5612f03a…` intacto) y ejecutar **una** partida autoplay grabada con WGC sin ataques
  (con calibración vinculada al nuevo hash) para validar el centrado durante el baile y al final antes de Bloque 2.
- Validación en juego autorizada (`dance-centering` `0665a9c3…` -> `5258009e…`, 2026-11-14):
  - El propietario autorizó («Si procede») el despliegue experimental y la partida grabada con WGC sin ataques.
  - Intento 1 (`0665a9c3…`): calibración `dance-center-cal` (`995443c5…`) ACEPTADA, pero la toma
    `dance-center-autoplay` (`20261114T114849058627Z-dance-center-autoplay`) fue **RECHAZADA**
    (`accepted: false`, `1` stall de `0.27 s` tras `gf 16026` por pausa real del productor de `369.73 ms`
    en `bag2jp_clock_probe.csv`, `1065/10009` pares fuera de `100 ms`). Diagnóstico RAM reveló además
    que `phase 1/4` usó `anim 67` (`req 101`, no `anim 68`) y quedó congelado en `[-473,-180]` / `[572,194]`.
    Auditoría de 13 partidas previas en `_work/versus-runs/` confirmó que `phase 1/4` alterna entre `anim 67` y `anim 68`.
  - Corrección `anim 67` (`B1CENTER_IDLE_ALT = 67u` en `bag2jp_bag1_center.h`): 20 tests host PASS (`9.481 s`),
    **18/18** mutantes por aserción (`dance-mutations.json`), Goldfish en frío (`ses_e2610cb5fffeRUfZ4qT8Bng226`
    `SIN HALLAZGOS BLOQUEANTES`, `_work/goldfish/dance-centering-anim67-verdict.json`) y build
    `dance-centering-anim67` PASS (`33.903 s`, `BAG2JP.exe` `5258009e95c805c4cd57151417e0ea695b2e5edf1518a3d827fee58eeca7d9c1`).
  - Despliegue EXE-only verificado a `BAG2JP-exp-8mb` (`dance-centering-anim67-deploy.json`, respaldo en
    `_work/gaso/deployment-backup-dance-centering-anim67-deploy`, `5` archivos protegidos y paquetes intactos,
    estable `5612f03a…` intacto). Calibración `dance-center-cal2` **ACEPTADA** (`493` heartbeats, `0` stalls,
    `2929` pares audio) y catálogo vinculado (`560c72c55b0723684b5d113e72399c83123bd017fbcd9ba41bf6dc7de6fb40f6`).
  - Toma final `dance-center-autoplay2` (`_work/versus-runs/20261114T120907225878Z-dance-center-autoplay2`,
    `295.973 s`, `150` saves/configs restaurados): grabación `_work/recordings/dance-center-autoplay2/manifest.json`
    **ACEPTADA** (`accepted: true`, `0` rechazos, `capture_backend: "wgc"`, `window_guard` `180` checks `passed: true`,
    `1696` heartbeats, `1` perdido, `jitter p99: 10.61 ms`, `59.942 fps`, `0` stalls, `10145` pares audio,
    `0` descartes, `44057 Hz`, `residual_p99_ms: 15.66`, `window_max_ms: 6.96`, `bag2jp_clock_probe.csv`
    `max 205.134 ms`, `owner.mp4` `-15.2 LUFS` / `-2.0 dBTP`).
  - Muestras RAM (`leash-actor-samples.jsonl`) e inspección visual (`dance-center-autoplay2-tiles.jpg`,
    `dance-center-autoplay2-sheet.jpg`):
    - En baile (`phase 1/3`, `124` muestras, radio `199`): P1 `med|dx|=94.0, med|dz|=89.5` (antes `128 / 214`);
      P2 `med|dx|=63.0, med|dz|=66.0` (antes `130 / 177`). Ambos permanecen centrados en su columna propia.
    - En pose final (`phase 1/4`): P1 converge de `[-502,466,-99]` (`gf 15240`) a **`[-520, 473, 0]`**
      y P2 de `[520,513,91]` a **`[520, 520, 0]`** exactos en `gf 15360..15420`; en `gf 15480+` liberan a
      `0x7FFFFFFF`, completan solo fever P2 y vuelven limpios al selector (`returned-selector.png`).
  - Pendiente: conformidad visual del propietario sobre `owner.mp4` y hojas de contacto, luego **Bloque 2**
    (ataques/`CAUGHT`/`fever-duet-sync` con autorización explícita) y cierre final (commit/snapshot). Sin commit ni snapshot.

## Radio proporcional BAG1: nueva validación autorizada (2026-11-14, histórico previo al recentrado)

- El owner respondió «continua» a la pregunta explícita sobre desplegar el candidato corregido
  y repetir una partida autoplay grabada sin ataques. Autoriza esta nueva prueba, no commit.
- Despliegue EXE-only verificado `3b43cff82d073ce2c7a29ecc377520c886e3d5d84ad258e2967bfc7427d9c89f`;
  respaldo `exp-backup/BAG2JP.exe.16768892`, informe `_work/gaso/drift/leash-release-deploy.json`.
  Estable y tres configuraciones protegidas sin cambios. Preflight `bag1-leash-release-run` pasó.
- Calibración `_work/versus-runs/20261114T060342369277Z-bag1-release-calibration`: menú, selector
  y ocho transiciones revisados en las dos hojas `release-calibration-*.jpg`; aceptación vinculada
  al hash del nuevo runtime. Restaurados 150 saves y controles/settings/estado, verificados.
- Toma `bag1-release-autoplay` completada: run
  `_work/versus-runs/20261114T060817268486Z-bag1-release-autoplay`,
  `complete_awaiting_visual_review`, 301.407 s; restauración verificada de 150 saves y de
  keybinds/settings/estado con los hashes previos. Vigilancias de control/radio y muestreador
  de RAM de solo lectura `_work/gaso/drift/run_leash_release_capture.py`: el enlace vivo exigió
  los mismos 20 bytes confirmados por Ghidra y el runtime `3b43cff8…`; es muestreo no atómico,
  no frame-exacto.
- Grabación `_work/recordings/bag1-release-autoplay` **ACEPTADA** (`accepted=true`, 0 rechazos):
  1930 heartbeats (1 perdido), jitter p99 12.8 ms, 59.939 fps, 0 stalls, audio residual p99
  15.74 ms y ventana máxima 9.51 ms.
- Vigilancias: ambos radios 440 en gf6581 y 318 en gf6582; en gf15681 el nativo libera a
  `0x7FFFFFFF` y **no** se vuelve a sobrescribir. El log del plugin solo registra el ajuste de
  los bailarines 0 y 2 (BAG1) con scale 98→75.
- Muestreo de actor: 171 filas con personajes 9/0, 141 finitas con radio 318 y 22 ilimitadas
  tras la liberación; hueco de raíz P2−P1 entre 402 y 1542 en 8 ventanas, ninguna negativa;
  0 lecturas con heartbeat cambiado y 8 filas post-partida sin raíz.
- Revisión visual propia: intro gf6560 (`GAS-O` vs `HEAT`), muestras de 16 a 182 s con
  separación sostenida y HUD `GAS-O`, fin de canción con `PLAYER 2 WIN`, poses finales y
  regreso a Character Select (186/189/191/193 s). Comparado con la hoja base
  `_work/gaso/drift/baseline-spacing-small.jpg` y la nueva `release-spacing-sheet.jpg`.
- Sin ataques: `request_counts` no incluye 202 y la traza no tiene líneas attack/fixture;
  `GASO_CAUGHT_CLIP_PUBLISHED` y los hooks de cámara quedan como estaban.
- Límites declarados: el muestreo no es atómico ni frame-exacto, el hueco es espacio de mundo
  (no píxeles en pantalla), ±2 fotogramas por latencia sin calibrar, y la calidad subjetiva del
  audio requiere escucha humana.
- Observado fuera de alcance: el banner de intro muestra «BI-O Vs Heat» (arte/nombre stock del
  slot importado 9); no es una regresión de este cambio y no se toca aquí.
- Estado posterior: el owner pidió más centrado X/Z (sección vigente), no dio conformidad visual. Sin commit, sin snapshot y con la instalación
  estable intacta. El artefacto de verificación antiguo `verify_leash_closeout.py` no se reutiliza
  porque fija el despliegue previo `16768892…`.

## Radio proporcional BAG1: correcciones host y partida pendiente (2026-11-14, anterior al nuevo despliegue)

- El propietario autorizó la recomendación («okay continua con lo recomendado»): radio proporcional
  BAG1, pruebas host, build/despliegue en `BAG2JP-exp-8mb` y una partida grabada sin ataques.
  No autorizó commit; instalación estable intacta. Mantener `camera_speed=2.1` y los hooks de
  cámara `0x80014FB8/0x80014FD4` desactivados.
- Implementado en `bag2jp_bag1_leash.h` y `bag2jp_bag1_versions.c`: solo bailarines elegibles BAG1,
  control por slot `0x8005F820 + slot*0x4C`, identidad del actor verificada, radio redondeado
  `abs(home_x)*480/784`, sin ampliar radios y sin reescritura estable. El candidato corregido
  conserva la liberación nativa y espera al radio inicializado, como se detalla abajo.
- Build `bag1-leash` correcto; exe desplegado
  `167688927edddccc45749b46c9259b94e4601e092756307d9d7aa36d4c4594e5`.
  Copia anterior `3191236A…` en `_work/gaso/drift/exp-backup/`. Calibración revisada y aceptada:
  `_work/versus-runs/20261114T052208305761Z-bag1-leash-calibration`.
- Partida `_work/versus-runs/20261114T052416752358Z-bag1-leash-autoplay`: Gas-O BAG1 A contra
  Heat BAG1 A, GasOBAG1; arnés alcanzó fin/regreso (`complete_awaiting_visual_review`, 300.244 s).
  Restauración verificada de controles, settings, estado y 150 saves. Las cuatro vigilancias
  adicionales son puesto X/radio, **no raíz/base**.
- **Captura RECHAZADA**, `_work/recordings/bag1-leash-autoplay/manifest.json`, `accepted=false`:
  `audio: a 1 s window is 17 ms off the fitted placement (> 1 frame; pause or drift)`.
  Máximo 17.04 ms, 12 pares descartados, pausa host 0.125 s; guardia de ventana correcta.
  `finalize` terminó con código 1; no se repite ni se relajan puertas. Los fotogramas extraídos
  son diagnósticos, no evidencia de aceptación visual o de sincronía.
- RAM, `_work/gaso/drift/leash-watch-summary.json`: ambos radios 440 en gf6563 y 318 en gf6564;
  en gf15639 pasan a `0x7fffffff` y el plugin los vuelve a 318 en gf15640. P2 cambia puesto X
  de 520 a 0 en gf16001. Dos pares de escrituras registrados (inicio/final), no lucha continua.
  **Defecto confirmado y corregido en fuente/build, no en la instalación**: el plugin anulaba
  una liberación intencionada. El overlay JP `005.dbi` genera `INT_MAX` en `0x8009CAC4/C8`
  y lo escribe en los cuatro radios con `0x8009CB0C/10`, dos lados separados por `0x98`,
  antes de avanzar la fase `0x8005D3DC` de 4 a 5. Requiere subfase >=6 y excluye escenarios
  0/3/5/11. El clamp nativo `FUN_8002CD48` usa ese radio si actor+3 y ctl+0xC están activos;
  no se midieron esas banderas ni el movimiento raíz durante la liberación. No afirmar una
  regresión visual de fever a partir de esta captura rechazada.
- Goldfish: primer intento sin veredicto por límite del proveedor (`REVISIÓN NO UTILIZABLE`).
  Dos revisores en frío completaron `_work/goldfish/spec-bag1-leash.md`:
  `ses_e2775fb72ffeguzmEO52kApfA3` y `ses_e2775d158ffeNrOOAq8ONFbwW7`, **CON HALLAZGOS**.
  Estado revisado del header: `dc28f1fc3bb862ba7b196fd4d79b154d91d4e387644b1dd8ff0c3522565fd86d`.
  Triaje: liberación confirmada; riesgo de interrupción durante inicialización confirmado por
  ruta de ciclos/VBlank y reproducido en host, no en partida; swaps de radios en
  `0x8002AD1C..2C` confirmados, efecto en ataques/pareja sin verificar. Refactor de escala sin
  regresión encontrada; tabla `0x80051924` alimenta Y, no Z. Evidencia/triaje:
  `_work/goldfish/bag1-leash-verdict.json`. Auto-revisión declarada de las correcciones;
  no se atribuye un nuevo veredicto limpio ni se relanza la revisión completa por inercia.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Correcciones mínimas (`bag2jp_bag1_leash.h`, SHA-256
  `f5bc3466ba538e27c0abbeb655b08150574748a5ad2be03f396a39a8948c5f6f`): conservar exactamente
  `0x7fffffff`; para valores finitos exigir `radius == raw_radius*stage_zoom>>8` antes de
  ajustar. Raw en ctl+0x3C, zoom signed16 en `*(0x80089200)+4`; rechazar puntero/zoom inválidos
  y overrides finitos desconocidos sin cachearlos. El código generado/runtime puede entregar
  VBlank tras los stores `0x8002D920/28` y antes del multiplicador `0x8002BA20..38`:
  el caso host home260/raw440/zoom128 antes producía 79 por doble escalado; ahora espera220
  y ajusta a159. No hay reproducción de esa alineación temporal en una partida real.
- Verificación: RED de liberación e inicialización falló por sus aserciones, después GREEN;
  suite relacionada **29 tests OK**, **8/8 mutantes detectados**. Tras corregir solo el fixture
  para que la liberación conserve raw440, **3/3 tests focalizados OK**, 4.756 s, exit0.
  Logs `_work/gaso/drift/leash-release-red.log`, `leash-release-green.log`, `leash-init-red.log`,
  `leash-init-green.log`, `leash-release-final-suite.log`, `leash-release-mutants.log`,
  `leash-release-final-fixture.log`.
- Build `bag1-leash-release-guard` correcto (33.171 s, dos jobs), header staging idéntico;
  candidato `3b43cff82d073ce2c7a29ecc377520c886e3d5d84ad258e2967bfc7427d9c89f`,
  **sin desplegar ni ejecutar**. Métricas:
  `_work/workflow/20261114T054600995931Z-bag1-leash-release-guard/metrics.json`.
  Exp mantiene `16768892…`, la versión con los dos defectos; no confundirla con el candidato.
- Siguiente paso: pedir autorización para desplegar el candidato corregido y realizar otra
  partida autoplay grabada sin ataques, con calibración revisada y vigilancias de raíz/base,
  puesto/radio y activación del clamp. Solo aceptar captura con `accepted=true`; revisar
  separación durante baile, liberación/fever, intro/HUD, fin y selector antes de pedir conformidad.
  Ataques, CAUGHT y pareja siguen sin probar. No commit ni snapshot de hito aceptado.
  Fuente `CLIP_PUBLISHED=0`, build `1`, intencionado.
- Herramientas consideradas no ejecutadas: `funcmatch.py` no corresponde a buscar un escritor
  de overlay, ni se necesita otra equivalencia de main; no nueva captura/`bag2_shots` sin partida
  autorizada. Modelos locales no aportaban a este razonamiento acotado; extracción/watch/hashes
  deterministas. No se usa FFmpeg para reparar o eludir la puerta de audio rechazada.

## Toma 4 aceptada y diagnóstico inicial de deriva (2026-11-14, anterior al ajuste)

- Toma `gaso-latch-site-autoplay4` (exe 3191236A…, payload 847058C4…), autorizada ("si autorizo,
  sigue con lo que recomiendas"); `manifest.json` `"accepted": true` (1916 latidos, 0 pares de audio
  descartados, residuo p99 17.97 ms). Las tomas 1-3 fueron rechazadas por pausas de 0.3 s del host:
  el juego del propietario "Watcher of Realms" estaba en primer plano (diagnóstico
  `_work/gaso/slide/zorder_log.py`); al cerrarlo la toma pasó. Nunca se forzó un filtro.
- Etiqueta HUD **PASA**: "GAS-O" con la fuente nativa BAG2, alineada a la derecha como "HEAT"
  (`_work/gaso/cam-ws/hudlabel4-30s.png`, `hudlabel4-zoom.png`).
- Sin ataques **PASA**: `bag2jp_bag1_versions.log` 21 líneas, 0 `gaso_tank`, 0 `request 202`. El
  contador `bag2jp.autoplay.attack_blocked` no es visible (sin herramientas de depuración).
- Intro **PASA con reserva**: cámara dentro del tubo, baja por el ventilador a la sala
  (`intro4-sheet.jpg`); el primer instante (~8.8 s) muestra una zona negra arriba a la izquierda y un
  panel gris. Arte VS "Bi-O VS Heat": fuera de alcance. Fin de canción y regreso al selector
  alcanzados (STOP del vigilante), no inspeccionados fotograma a fotograma.
- **Pregunta del propietario**: los bailarines BAG1 se desplazan durante el baile y acaban hombro con
  hombro. Confirmado en video (`_work/gaso/drift/drift-sheet.jpg`: separados en 0:16, juntos en 3:02).
- Mecánica BAG2 (Ghidra MCP SLPM_862.19): `FUN_8002ccc8` re-ancla la base (+0x14b8/+0x14c0) al cambiar
  de clip; la raíz es base + traslación del clip × escala del bailarín >> 7 (`FUN_80012c9c`, escala
  en +0x14e4). `FUN_8002cd48` es una correa dura: si la raíz se aleja más que el radio del puesto, la
  recorta al borde. `FUN_8002b5bc` (llamado por `FUN_8001e0f4`): puesto X = ∓4·tabla
  0x80051918[escenario] (130) = ±520, radio = tabla 0x80051a70[escenario] (440); ambos × zoom >> 8.
  Control por lado: 0x8005F820 + lado×0x98 (puesto +0x28, radio +0x38).
- Mecánica BAG1 (Capstone `_work/bag1/scus.bin`): también re-ancla (0x80031574) y aplica correa
  (0x8003161c), pero es un muelle que resta 1/32 del desplazamiento total por fotograma; puesto
  ±0x310 (784), radio 0x1e0 (480).
- Proporción: separación mínima posible BAG1 = 1568 − 960 = 608 unidades (escala Gas-O 116); BAG2 =
  1040 − 880 = 160 (escala 75). Relativo al tamaño del bailarín, BAG2 permite acercarse unas 2.5
  veces más. La deriva neta de los clips no distingue BAG1 de BAG2 (`_work/gaso/drift/root_drift.json`:
  mediana neta stock Heat 873, BAG1 Heat 818). **Hipótesis**: es la geometría de la correa BAG2 con
  la deriva de las coreografías BAG1, no un error de conversión. No verificado: valores de raíz/base
  en partida y si los bailarines stock BAG2 convergen igual (no hay toma stock).
- Propuesta entonces pendiente (posteriormente autorizada, véase sección vigente): para lados con versión BAG1, fijar el radio a
  la proporción BAG1 (|puesto X| × 480/784 ≈ 318) escribiendo +0x38 del control desde el plugin
  (escritura de datos, sin hook nuevo en el exe principal). Validar con una partida grabada con
  vigilancia de raíz/puesto/radio.

## Partida grabada scale32+HUD y opt-in nativo del latch (2026-11-13, estado vigente)

- Autorización del propietario ("si autorizo"): staging, build, despliegue en
  `BAG2JP-exp-8mb` y una partida autoplay grabada sin ataques. Sin permiso de commit.
- Staging `_work/gaso/combined-scale32-hud/` (payload `847058c4…`, solo cambian las
  entradas 53/54/125/126 HUD y 197 miembros 11/12). El primer build falló por un
  defecto real: `bag2jp_bag1_versions.c` no incluía `cpu_state.h` (el harness host
  define su propio `CPUState`); corregido (versions.c `620E3D47D7F5`).
- Partida `gaso-scale32-hud-autoplay` (exe `c391f357…`; Gas-O BAG1 A vs Heat BAG1 A,
  escenario GasOBAG1, p1_2p y p2_2p). Grabación `_work/recordings/gaso-scale32-hud-autoplay/`
  con `manifest.json` `"accepted": true` (solo puertas de captura/sincronía, ±2 fotogramas
  sin calibrar). Evidencia del arnés `_work/versus-runs/20261114T040531514961Z-gaso-scale32-hud-autoplay`;
  restauración verificada.
  - **Sin ataques: PASA.** 0 cues `gaso_tank`, 0 `request 202` (cam95: 24 cues, 2 peticiones).
    El contador `bag2jp.autoplay.attack_blocked` no aparece en ningún log (build sin
    herramientas de depuración): se observa el resultado, no el disparo del hook.
  - **Cámara del intro: PASA visualmente, con reserva.** `_work/gaso/cam-ws/new-intro-sheet.jpg`
    y `new-intro-zoom.jpg`: desde ~8.5 s la cámara mira dentro del tubo rojo/blanco hacia
    el ventilador, lo atraviesa y entra en la sala (~11 s); sin el vacío exterior de cam95.
    Reserva: cuñas oscuras pequeñas los primeros ~0.4 s; sin vídeo de referencia BAG1.
  - **Etiqueta HUD: FALLA.** `_work/gaso/cam-ws/hudlabel-30s.png`: P2 muestra `HEAT`,
    P1 no muestra etiqueta (se dibuja el rectángulo stock, vacío en el body2 corregido).
  - Pantalla VS muestra arte de Bi-O: fuera del alcance de este cambio.
- **Causa del fallo HUD:** el latch `0x8001F8A4` está en el exe principal (código AOT) y
  el runtime solo llama plugins de instrucción nativos para sitios en
  `[recompiler] mod_instruction_sites` (`mod_plugins.h:60-69`). No estaba listado: el C
  generado no tenía ninguna llamada `psx_mod_instruction`, el latch nunca se activaba y el
  hook HUD declinaba. Los tests host llaman a los hooks directamente y no lo podían ver.
- **Corrección:** `mod_instruction_sites = ["0x8001F8A4"]` en `patches/BAG2JP-game.toml`
  (`95EEC934439D`) y en `game.toml` del árbol de build. Generación aislada
  `_work/gaso/latch-codegen/generate_latch_site.py` (emisor `42508148…`): solo cambia
  `SLPM_862.19_full_04.c`, y solo por el bloque estándar del sitio (llamada + dirección vía
  `psx_mod_memory_address`, identidad sin plugin de memoria según `test_mod_runtime.cpp:829`).
  `stage_latch_site.py` exige exactamente ese diff y guarda copias en `stage-backup/`.
- Nueva regresión `tools/test/test_mod_instruction_sites.py` (`2006B5E4334A`): todo sitio
  de instrucción del exe principal registrado en `mods-src` debe estar listado (y llamado en
  el C generado del árbol de build). Dos mutantes eliminados (sin línea de config; C generado
  anterior). Suite de 6 módulos: 26 OK.
- **Hallazgo previo, no tocado:** los hooks de cámara BAG1 `0x80014FB8`/`0x80014FD4`
  (`bag2jp_bag1_stage.c:369-370`, sección 2026-11-08) tampoco están listados, así que en
  código nativo no se ejecutan. Activarlos cambiaría la cámara de todas las etapas BAG1:
  decisión del propietario. La sonda `0x80049F94` de anim-trace reescribe su palabra de
  código (RAM sucia) y es intencionada. Ambas figuran como excepciones en el test.
- Build `gaso-latch-site` OK; desplegado solo el exe `3191236ACFD8B95C73D58B7572458A870E2FFCB34ECE8B3DEC3D15165E4F545F`
  (copia del anterior en `_work/gaso/combined-scale32-hud/exp-backup/BAG2JP.exe.c391f357`).
  **Etiqueta HUD sin validar en partida:** requiere una nueva partida grabada autorizada.
- **Goldfish 2026-11-13 (opt-in nativo del latch)**, 1 revisor (`ses_e27b6da5affeJh2481bRiH49fo`,
  spec `_work/goldfish/spec-gaso-latch-site.md`). Hashes revisados: `patches/BAG2JP-game.toml`
  95EEC934439D, `test_mod_instruction_sites.py` 2006B5E4334A, `generate_latch_site.py`
  E7FC3B57A6B5, `stage_latch_site.py` B704D8122DF1, `full_04.c` a04ca5912dc7. Veredicto:
  **SIN HALLAZGOS BLOQUEANTES**. Confirmado: el diff generado es solo el bloque de
  `0x8001F8A4`; no es delay slot; `psx_mod_memory_address` es identidad sin memory plugin
  (`mod_runtime.cpp:3834-3850`); el rango de texto es `0x80010000+0x4D000`.
  Hallazgos no bloqueantes, sin aplicar:
  1. El `game.toml` del árbol de build difiere del canónico en `present_thread` y en
     `buffer_ms` (45 frente a 90). Es una divergencia previa a este cambio, pero el exe
     desplegado usa la configuración de runtime del árbol de build. Antes de cualquier
     checkpoint, separar en `patches/BAG2JP-game.toml` esta línea de los demás cambios previos.
  2. Si falta el árbol de build, el test omite la comprobación del C generado.
  3. El regex de `#define` toma el primer literal hex, así que una expresión se resolvería mal.
  4. Solo cubre `*.c` y `*.h` (no `.inc`/`.cpp` ni registros indirectos); hoy no falta ningún sitio.
  5. El emisor no es el del árbol de build; lo mitiga la comprobación de diff exacto.

  La justificación de `0x80049F94` no la pudo verificar el revisor con los archivos permitidos.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.

## HUD BAG2 y revisión cam95 (2026-11-13, estado vigente)

- Petición: usar para `GAS-O` sobre la barra la misma fuente que los personajes
  BAG2. Candidato **offline**, no desplegado ni integrado en payload/build.
- Composición literal de glifos HUD nativos, sin comprimir ni remapear sus índices
   compartidos: G de Hustle Kong, A de Heat, S de Strike, guion/O de Bi-O.
   S corregida: `[56,80,70,87]` (14 píxeles) más una columna transparente; el primer
   candidato copiaba en x70 tres píxeles del contorno de la T vecina.
  Perfil `tools/bag1import/profiles/gaso.json`: 69x7 en `[0,0,69,7]`, dentro
  del antiguo arte de nombre BAG1 USA/JP. Conserva las paletas corporales y todos
  los píxeles externos al destino respecto a la textura BAG1 retargeteada.
  **Estar dentro del antiguo nombre no demuestra exclusión de UV corporales**;
  esa auditoría sigue pendiente y bloquea la integración.
- `tim_retarget.paste_native_glyphs` y `build_gaso_assets.build_hud_texture`
  comparten la composición. `bag2jp_bag1_hud.h` ajusta solo el sprite Gas-O del
  lado actual, con tres palabras guardadas de overlay005, versión/entrada activa,
  descriptor, registro de textura y límites RAM. Mantiene CLUT/tpage/Y/colores,
  anclaje derecho y descriptores globales Bi-O sin modificar. No acredita todavía
  identidad del pack residente ni ejecución real del dispatcher.
- Evidencia vigente: `_work/gaso/hud/bag2-font/corrected/{usa,jp}/`, `audit.json` y
   `_work/goldfish/spec-gaso-hud-native-font.md`. Suite
   `py -3.13 -m unittest tools.test.test_tim_label tools.test.test_gaso_hud tools.test.test_gaso_hud_runtime`:
   18 tests OK (5.032s). Harness C con overlay005 original y CPU/RAM sintéticas:
   cuatro lado/traje positivos, lados mixtos y guardas negativas; no es una partida.
   18 contenedores comparados al candidato anterior: ocho packs cambian solo body2,
   los otros diez no cambian. Cinco mutantes aislados del callback eliminados;
   originales conservados. El audit exige ahora los nueve nombres exactos por región;
   sondas independientes rechazan salidas faltantes, adicionales o renombradas.
   También eliminado en memoria el mutante sin validación estricta del tipo de
   espaciado: `[False]`/`[0.0]` producen exactamente dos fallos de aserción. Sin
   modificar fuentes para las mutaciones. Son seis mutantes en dos ensayos distintos.
- Frente a `final-build`, body2 restaura además 261 píxeles USA/277 JP por textura
   en la antigua ranura errónea. «Fuera del rótulo intacto» se refiere a la fuente
   BAG1 retargeteada limpia, no a aquel candidato con la ranura corporal alterada.
- Goldfish inicial: ambos **CON HALLAZGOS** (S contaminada/inventario incompleto).
   Corregidos y revisados en frío por dos agentes nuevos, con alcance solo de esas
   correcciones: `ses_e296fade9ffebYDKWXqDiQDtEo` y `ses_e296f833effe2OOABfSOSFpBjU`,
   ambos **SIN HALLAZGOS BLOQUEANTES**. El segundo sugirió los casos False/0.0:
   añadidos y probados con mutación estrecha, sin cambiar la implementación revisada.
   Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Auditoría UV NO terminada: `corrected/model-inventory.json` verifica el layout
   completo de 16 miembros de modelos (USA/JP, trajes/lados y accesorios), pero
   los cuerpos contienen 14 nodos type4. Falta resolver las primitivas texturizadas,
   el uso de esos nodos y la selección de textura del renderer. No se certifica
   seguridad por estar dentro del antiguo nombre. Integración bloqueada también por
   identidad del pack residente y aceptación real pendientes.
- **Actualización 2026-11-13: exclusión UV de body2 DEMOSTRADA offline.**
   `audit_body_uv.py` (layout Ghidra `FUN_800220b8`/`FUN_800201b0`/`FUN_80021ff0`;
   type4 solo dibuja F3/F4 sin textura) recorre los 16 modelos: cuerpos m0 con
   3075 vértices texturizados, todos `tex_idx 0` (body1); accesorios m2 sin
   primitivas texturizadas; 0 referencias a body2. Control negativo: el mismo
   lector ve `tex_idx 1` en Heat/Strike/accesorio Bi-O stock. Informe
   `corrected/body-uv-audit.json`. Sigue pendiente la identidad del pack residente
   (body2 de Bi-O y Gas-O tienen geometría TIM idéntica) y la validación en juego.
- **Ataques en autoplay 2P: causa localizada** (Capstone sobre `005.dbi`): los
   hooks AP2 fuerzan el bloque CPU por compás y este elige ataque 0x6e con stock
   en 0x8009afd8..0x8009b078.
- **Actualización 2026-11-13 (tarde): arreglos implementados, solo probados en host.**
   - Identidad del pack residente: `bag2jp_bag1_load_latch.h` (97AD496C9A3B) engancha
     0x8001F8A4 (`lw s0,0x8(a0)` en `FUN_8001F874`, único lector de la tabla DF2_
     junto al cargador `FUN_8001F6FC`, según xrefs Ghidra) y registra si el offset
     leído de las entradas 53/54/125/126 es el alt. El HUD usa ese latch, no la tabla
     RAM actual. Se borra en reset de sesión y tras cargar savestate (callback solo
     de restauración, `mod_plugins.h:44-47`): tras cargar un estado se ve el rótulo
     stock hasta que el pack se relea. **Bug real hallado por test nuevo:** la palabra
     previa era 0x3C020006 en vez de 0x3C028006; el latch no habría disparado nunca.
     Test contra los bytes del EXE original y Ghidra `read_memory` 0x8001F8A0.
     12/12 mutantes del latch eliminados.
   - Autoplay 2P sin ataques: `bag2jp_ap2_no_attack.h` (B534206A781D) en 0x8009AFE0
     fuerza `$v0=0` (stock 0x1b no se modifica) si `ap2_on()` y el lado está en
     autoplay; `$s3`/`$s5` comprobados como 0x8005E728+p*0x32 y 0x8005CF08+p*0x24
     (0x8009AD24..AD40). Límites: omitir dos `rand()` desplaza la secuencia RNG; con
     un solo lado en autoplay ese lado aún puede contraatacar (ruta 0x8009AF00→B074).
     La prueba pedida usa ambos lados (máscara 3). Comentario falso de
     `bag2jp_mods.c` corregido.
   - Suite `py -3.13 -m unittest tools.test.test_ap2_no_attack tools.test.test_gaso_hud_runtime tools.test.test_bag1_stage_shim tools.test.test_tim_label tools.test.test_gaso_hud`: 21 OK.
- **Cámara del intro: causa raíz = escala de mundo del escenario.** Ni FOV (H=384
   en BAG1 y BAG2, Ghidra/Capstone) ni OT (mismo tamaño 0x1000, mismo -0x60) ni
   geometría ausente (el domo cubre 360°). BAG2 dibuja el modelo de escenario a 1/4
   de las unidades de cámara y BAG1 a 3/8 (nota archivada
   `archive/bag1-stage-song-before-audit.md:46-49`; Heat usó (3,2); ratio de bailarín
   75/116≈2/3). Con `model_scale: null`, la cámara BAG1 queda encima y fuera del domo
   encogido. `_work/gaso/cam-ws/render_probe.py` reproduce el fotograma grabado
   (f855) con escala 0.25 y la cámara cam95. Con modelo ×1.5 y claves nativas, las
   claves 1..80 quedan dentro del tubo y la sala (`sc_sheet.png`), profundidad máx.
   ~10000 < límite OT 17280. El render offline es simplificado: no sustituye la
   prueba en juego.
   - Perfil `profiles/stages/gaso.json` (F7D90DB832B5): `model_scale [3,2]`,
     `camera_scale` eliminado, `camera_speed 2.1` conservado. Test
     `test_gaso_stage_world_scaled_for_native_camera` (rojo antes, 6/6 OK en WSL).
     Paquete `stage197` sha256 `b663417f…b2` (514396 B), igual al candidato offline.
     Sin staging ni despliegue. `strike.json` también tiene `model_scale: null`: posible
     mismo defecto, no investigado.
- Goldfish 2026-11-13 (latch + AP2), spec `_work/goldfish/spec-gaso-latch-ap2.md`:
   `ses_e28dae82dffeGA1QIDfzwCL51k` y `ses_e28dadb44ffeiK0hFxDCUalBU1`, ambos
   **SIN HALLAZGOS BLOQUEANTES**. Aplicados: literales en el harness AP2, comentario
   AP2 (RNG, contraataque con un lado, origen de `$s3`/`$s5`), semántica savestate,
   duplicados de offsets alt en test. Ninguno detectó la palabra previa errónea del
   latch (el harness copiaba la macro); la encontró el test contra el EXE. No
   cambiado: los hooks AP2 previos usan `$s4 & 1` sin guardia p>1 (consistencia,
   preexistente). Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Revisión del delta (fingerprint del latch, tests nuevos, perfil de escala, test
   de escenario), spec `_work/goldfish/spec-gaso-delta-scale.md`: **Goldfish
   omitido**, el subagente `ses_e28c65ee4ffevFPJkuDZuNqg9g` falló por límite del
   proveedor. Sustituido por **auto-revisión declarada** (no es Goldfish): el test
   de escenario lee el DFS binario (escala 6144, traslación ×1.5, claves de cámara
   nativas, pistas 1+ idénticas a stock); los nodos tipo 3 siguen crudos; suelo
   141×1.5×1/4≈52.75 frente a 141×3/8≈52.88 en BAG1; traslaciones s32 sin desborde;
   nada depende de `camera_scale 0.95`; el test de firma falla si falta el EXE.
   Veredicto: SIN HALLAZGOS BLOQUEANTES. Repetir Goldfish real cuando haya cupo.
   Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- `corrected/native-index-preview.png` inspeccionada: GAS-O sin comprimir, columna
   de espaciado limpia. Escala de grises diagnóstica de índices, NO colores de la
   CLUT efectiva en juego. Fuentes del hook SHA256
   `a2beb511bc1ed58b60b976355c9bc1442e704e4a4a684ac7bb8703a7ac57fbd6`.
- Checks de cierre: estado JSON e informe coherentes; payload fuente `8a6749d0…`
   y exe experimental `e68ba69e…` conservan hashes de cámara95, sin staging HUD.
   `git diff --check` sobre los archivos seleccionados **no pasa**: reporta 4760
   líneas históricas de esta nota y 1830 del log Ghidra por whitespace/CRLF del
   árbol ya modificado. No se normaliza ni limpia trabajo anterior. Los bloques
   nuevos se comprobaron sin espacios finales literales; no equivale a diff limpio.
- **Corrección de la afirmación anterior sobre cámara95:** la finalización de
  `gaso-cam95-autoplay` terminó con `manifest.json accepted=true`, pero eso solo
  acepta la captura. Revisados 71 fotogramas consecutivos (8.287–9.453s;
  `intro-frame-sheet.jpg` en esa grabación): desde 8.536s y hasta aproximadamente
  8.8s persisten silueta exterior del domo/ventilador y vacío negro. **FALLA** el
  criterio visual inicial; la proyección offline no lo certificaba.
- **FALLA también «sin ataques»:** `events.csv` registra dos activaciones del
  tanque, cues6906 en gf7592 y gf9436 (~25.59s y56.36s), con restauraciones
  posteriores. La ausencia de fixtures no garantizó ausencia de ataques; causa
  aislada después (ver «Ataques en autoplay 2P» arriba). No se lanza otra partida ni se afirma aceptación del flujo.
- Captura revisada: exe `e68ba69e132cbec5e0a8271072c1788fe97d9b99cbdd415785d8e088a15b6a64`,
  `review.mkv` SHA `8988a7013d2d8e6a044e0bc1ddd43ac6358913a993aedaf5336fcca3f0961d5f`;
  59.94fps, audio exacto FLAC estéreo, 191.834s. Latencia de pantalla sin calibrar:
  ±2 fotogramas solo estimados; juicio auditivo subjetivo y resto del flujo no
  certificados en esta revisión.
- Siguiente: completar auditoría UV e identidad residente del HUD; después preparar integración
  reproducible y solicitar la autorización necesaria para validación en juego.
  Investigar cámara/ataques internamente, conservando `camera_speed=2.1` y el
  estado experimental anterior. Sin commit ni modificación del estable.

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
- Checkpoint Git local `ae6a004` en `fix/gaso-tank-anchor` con 8 archivos
  (motor `stage_geometry.py`, perfil `gaso.json`, tests, integración y esta
  nota). Se añadió `model_bag1_to_bag2.py` por ser dependencia directa del
  motor. Los 15 tests pasan con
  `wsl -d Ubuntu --exec python3 -m unittest tools.test.test_stage_port tools.test.test_stage_geometry`.
  Snapshot del árbol sucio previo en `_work/goldfish/pre-commit-dirty.patch`;
  quedan 80 entradas sucias ajenas sin commitear. Sin push y sin cambios en
  `BAG2JP-win`.
- Estado: el defecto A queda eliminado según las capturas reales del juego y el propietario
  **aceptó el cambio el 2026-11-10**. El candidato v2 sigue desplegado en la instalación
  experimental `BAG2JP-exp-8mb`. El defecto B (tanque) sigue rechazado y sin trabajo hasta su
  decisión.

### Revisión Goldfish del checkpoint (registro durable)

- 2026-11-10. Estado revisado: commit `ae6a004` en `fix/gaso-tank-anchor`.
  Tres revisores en frío sobre `_work/goldfish/spec-checkpoint-v2.md`; veredicto
  `CON HALLAZGOS`. Aplicados y comprobados seis: runner real de tests
  (`wsl -d Ubuntu --exec python3 -m unittest tools.test.test_stage_port
  tools.test.test_stage_geometry`, `load_tests` en `test_stage_port.py:17` que
  pytest ignora), dependencia `model_bag1_to_bag2` incluida en el alcance,
  snapshot previo del árbol sucio, pathspecs explícitos en vez de `git add -A`,
  evidencia corregida (`owner_acceptance`, `review_limits`, recuento de frames) y
  tests tautológicos declarados como deuda. Refutado: nada. No verificable:
  contenido de `BAG2JP-win` (fuera del repositorio).
- Este registro es el previsto por `notes/goldfish-review.md`; `_work/` queda solo
  como evidencia cruda. Veredicto de revisor: no es aprobación del propietario ni
  permiso de despliegue.

### Tanque B — coordenadas corregidas, candidato experimental (2026-11-10 UTC)

- El propietario pidió continuar el ataque especial. Se reabre B; A sigue
  aceptado y sus recursos no cambian. Objetivo acotado: corregir altura, caída y
  composición del tanque antes de evaluar encierro/pose/liberación en juego.
- Causa contrastada: el C restaba altura y caída a Y local, aunque la cámara
  ya invierte Y, y omitía la matriz del rival. Ghidra MCP confirmó el patrón
  nativo de composición (`20261110-ghidra-044`); la RAM histórica inicializada
  aporta contraste, no aceptación de comportamiento.
- Cambio: `bag2jp_gaso_tank.h` suma altura/caída, compone cámara con matriz del
  rival y cancela punteros cuyo registro completo sale de RAM 8 MiB. Mantiene
  seguimiento XZ previo del source; se reconoce expresamente su inclusión al
  staging porque faltaba en el build anterior. Sin cambios a humo, duración,
  congelación slot 78 ni cartel GAS. No se clona el motor de otro personaje.
- TDD del C real: `tools/test/gaso_tank_harness.c` y `test_gaso_tank.py`, guest RAM
  aislada y paquetes GPU emitidos. RED de inversión/matriz/cancelación y RED de
  límite RAM conservados; GREEN final: 7 tests (tanque + escala), 3,979 s.
  `_work/gaso/tank-anchor-{red,bound-red,final-host}.log`. El harness cubre caída,
  suelo desde ataque real, matriz no identidad, puntero nulo/fuera de rango y
  cancelación persistente. No simula el motor completo ni valida la pose.
- Suite completa: 217 tests, **1 fallo y 31 errores**, 20,399 s; no verde.
  `_work/gaso/tank-anchor-host-suite.log` y `tank-anchor-host-failures.txt`
  enumeran audio/shim/vblank y contratos/assets Heat/Strike. No se ha probado
  independientemente que sean preexistentes; no se modifican fuera de alcance.
- Goldfish: **2 revisores independientes**, spec
  `_work/goldfish/spec-gaso-tank-space.md`. Primera pasada `CON HALLAZGOS`:
  límite superior RAM insuficiente (alto), falta de spawn/suelo y cancelación
  persistente (medios). Confirmados y corregidos con tests; ninguno refutado.
  Relectura acotada por ambos: **SIN HALLAZGOS BLOQUEANTES** en ese alcance.
  No verificaron hashes por su cuenta ni aceptación visual/suite completa.
  Hash del header revisado:
  `7bd077089dd21a0af334aa2a0ec5b8bb457b1464a29c39ff468df3ac1347ac0f`.
  Sigue siendo un único efecto pese al tamaño del header; sin refactor ajeno.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.

- Build de dos jobs: PASS, 41,867 s; warning clang `-mbig-obj` sin uso.
  `_work/workflow/20261110T102150722350Z-gaso-tank-space/metrics.json`.
  Desplegado **solo EXE experimental**, SHA-256
  `3145ba5bc943751ea3337868743d5a5e24b184087467239ebeeba4c7dd10d39f`.
  Payload `376287ab...`, DFS aceptado `0a994860...`, settings y saves sin cambios
  tras despliegue. Backup/rollback:
  `_work/gaso/tank-space-candidate/deployment-backup`; build backup separado.
  `BAG2JP-win` estable no tocado. El candidato no está aceptado.
- Prueba gráfica fresca P1 GAS-O BAG1 A contra Heat BAG2 A, escenario GAS-O:
  `_work/versus-runs/20261110T102756932598Z-gaso-tank-space-bag1/`.
  Fixture explícito de ataque/defensa, no juego natural; 120 capturas PrintWindow
  con heartbeat antes/después, no exactas por frame. Ráfaga compacta inspeccionada
  en `tank-space-burst-compact.png`: caída desde arriba y volumen vertical, pero
  cristal verde oculta al rival; **encierro/pose no verificables visualmente**.
  No se declara B aceptado. Traza: rival anim 78 en f7255/f7307, transición
  a anim 89 req202 en f7308 y vuelta a 78 en f7309; no demuestra inmovilidad
  continua ni se atribuye todavía una causa. `attack-window-trace.txt`.
- Navegación del nuevo runtime: 9 imágenes inspeccionadas y catálogo ligado a
  sus hashes, `_work/versus-runs/20261110T102335812425Z-gaso-tank-space-probe`.
  Ambas sesiones cerradas por el harness; restauración de controles/settings y
  saves verificada. El bridge restauró también las tarjetas externas históricas;
  `post-test-protected-check.json` confirmó los **42 originales** del backup,
  incluido settings `b41a5fc8...`. Se conservan copias nuevas de tarjetas de test.
  El hash `runner_sha256` de `capture-result.json` identifica el runner Strike
  reutilizado; el hash del adaptador efectivo está en el check posterior:
  `b4a430b42a517129d6c69d21ccde203dc3da975baf055ba40df8ea193018863c`.
- Documentación: checker completo 131 docs, 6 errores/9 avisos en el repositorio;
  comprobación focal de esta nota y log Ghidra sin incidencias en
  `_work/gaso/tank-space-docs-targeted.json`. `git diff --check` focal limpio.
- Siguiente acción exacta: inspeccionar emisores de cristal/cuerpo del header
  (opcode G4, estado de mezcla/orden OT) contra los helpers compartidos y los
  paquetes nativos; usar la ráfaga y traza anteriores sin repetir captura.
  Formular una hipótesis de opacidad y un RED del C real antes de otro cambio.
  Después verificar por qué f7308 sale de anim 78 durante el tanque y cubrir
  P1/P2 × A/B, fin de canción, fever aplicable y selector. No inferir aceptación
  de B a partir de tests/build/revisores. Sin snapshot de milestone: candidato WIP.

### Ataque del tanque — requisito de fidelidad completa (2026-11-10 UTC)

- Petición: «la reconstrucción 100% fiel el efecto, sonido, tamaño, todo».
  El candidato `d9ce984` es parcial y no queda aceptado por esta petición.
- Objetivo: geometría/proporciones/transforms, materiales/partículas, estados,
  tiempos, reacción y sonido originales sincronizados. Corregir opacidad ya no
  basta. Números históricos llamados «exactos» requieren código/datos/traza nativos.
- `plans/gaso-attack-effect.md` conserva historial y propone F1–F8, audio, comparación
  por guest frame y compatibilidad con los 19 rivales. Al proponerla esperaba aprobación;
  sin nueva implementación, build, despliegue ni captura de esta revisión.
- Preflight PASS: `_work/workflow/20261110T104154528615Z-gaso-native-fidelity-plan/metrics.json`;
  HEAD `d9ce984`, índice vacío, 82 cambios previos preservados, 31 fuentes coincidentes,
  sin drift de recursos, EXE build/desplegado iguales. No es aceptación del ataque.
- Ghidra MCP confirmó main JP `SLPM_862.19` y reproducción de cues `0x8002e2d0`
  (trial `20261110-ghidra-045`). Es una dependencia BAG2, no la identificación del
  sonido/controlador BAG1 del tanque. Escucha histórica general no valida este ataque.
- Siguiente acción histórica al proponerla: aprobar revisión F1–F8; luego F1, inventario de identidad/región,
  hashes y carencias sin repetir capturas válidas. Cartel GAS aceptado, estable,
  preferencias y tarjetas preservados. Esta unidad es exclusivamente documental:
  Goldfish no requerido aquí, sí para el siguiente cambio que lo active.

#### Aprobación y comienzo F1 (2026-11-10 UTC)

El propietario aprobó explícitamente la revisión F1–F8 mediante **«Aprobar plan»**.
Ejecutar el contrato completo sin pedir otra aprobación del mismo plan; esto no
acepta el efecto ni convierte `d9ce984` en una reproducción fiel.

Auditoría inicial de solo lectura: `_work/gaso/full-fidelity-source-audit/report.json`
(0.747 s), ocho contenedores GAS-O USA y ocho JP, miembros con hashes, identidad
del ejecutable/disco de referencia. `character_workflow.py validate-profile`
valida 84 animaciones, pero mantiene dos excepciones pendientes (accesorio y región):
`generation_ready=false`.

El vídeo original de 45 s contiene **solo H.264, sin pista de audio**, y no vincula
cada imagen a un frame invitado. Su runtime actual coincide con el registrado,
pero `session.json` conserva `closed=false`: no demuestra una sesión activa ni
restauración. El `boot_exe` relativo de `game.toml` tampoco existe actualmente.
Revisar carga real, estado y procedencia antes de nuevas capturas; no usar este
vídeo para afirmar equivalencia sonora o tiempos exactos.

#### F1 cerrado como inventario; F2/F3 en investigación (2026-11-10 UTC)

No hay cambio de runtime ni aceptación nueva. El inventario identifica fuentes y
carencias; **no** demuestra fidelidad del port. Reportes de solo lectura:
`_work/gaso/full-fidelity-source-audit/{report,accessory,audio,audio-deployed}.json`.

- BAG1 JP main `SLPS_012.32`: SHA-256
  `9676a28c589e20829e5b43874c8534e49393337f4f5238610598b14257a778ff`;
  overlay GAS-O P1 JP `native-gas-jp.dbi`:
  `05220579f3f84427f7e9744136561a3cc9cb437f3699765f01d06aaaf0f17eb4`.
  Base de **archivo**, incluyendo cabecera de 12 bytes, `0x801d587c`, contrastada
  con tablas de callbacks del main (`native-callback-layout.json`). No aplicar
  esta base/direcciones al overlay USA ni tratar un candidato JP como USA.
- Los 41 vértices copiados al header coinciden exactamente con el miembro original
  de 1460 bytes, SHA `106a0fc2dd49ada4998d8ebe7be99f939c7336a4f797a720a292575173374c2e`.
  Pero hay 44 registros de primitivas frente a 40 caras emitidas actualmente;
  cuatro registros adicionales siguen sin interpretar. La transformación estática
  original es identidad. Los porcentajes 35 % XZ / 22 % Y no proceden de ella.
- El controlador JP `0x801d5bb0` inicializa altura en suelo del rival +4096 y
  velocidad cero. `0x801d67a0` actualiza velocidad con `32*delta`, resta de Y
  `delta*(velocidad_actualizada + (32*delta >> 1))` y limita al suelo del rival
  (`+0x43cc`). Al aterrizar escribe `0x7fffffff` en el estado del rival; aún falta
  demostrar el significado completo de ese campo. No equivale por evidencia a
  forzar animación BAG2 78/frame0. Los tiempos fijos 12/65/15 siguen siendo WIP.
- `0x801d6908` sigue XZ del rival mientras cae y los conserva después. Construye
  escala desde dimensiones del rival `+0x43b8/+0x43c0`, con `12*dimensión+230`
  normalmente y `+600` en dos casos de IDs; Y viene de una tabla por personaje
  multiplicada por cuatro. El main JP `0x80013ed4` compone la matriz/modelo con
  esa escala R12 y la cámara. Identificar las unidades, tabla y equivalencias de
  estructuras BAG2 antes de cambiar el tamaño; no sustituirlo por otro porcentaje.
- `0x801d666c` mantiene efectos de aterrizaje y partículas; a partir de contador
  >32 llama a la segunda fase. `0x801d6480` decide salida por flags/temporizador
  del rival y restaura su estado guardado, no por un fade global de 15 frames.
  `0x801d60c4` además retrasa el controlador por parámetro del evento y una señal
  global. Pendiente trazar ese evento, reloj, render/materiales y ramas de defensa.

**Audio: diferencia demostrada en lo desplegado, no solo ausencia de escucha.**
El overlay llama a `0x1806` en `0x801d6480` y a `0x180a` en `0x801d7218`; este
último puede repetirse por temporizador/azar, no es un único sonido al inicio.
SEDT miembro6 es idéntico USA/JP. Los dos cues originales usan muestras de 7568
y 672 bytes, SHA `7399441cdd4269c9dc41b358f1369d44f23e867857b351b6e3481fe1078c12c8`
y `07a87f233c77a7e3ba131c3f32d40c351d7273b466d16db68379617536495a02`.
Los candidatos históricos conservan esas muestras, **pero el payload experimental
actual no**: cues rebased `0x6906/0x690a`, muestras de 5184/480 bytes y center/shift
93/48 y 101/48 frente a 86/0 y 94/0. Se aplicó el resampling del presupuesto de voz.
No confundir esos candidatos antiguos con lo desplegado. Recuperar audio exacto
sin perjudicar otras voces requiere resolver el presupuesto y routing en F5.

La extracción desplegada verifica manifiesto, índice y LBAs reales de BUST2/DUMMY:
offset de manifiesto es absoluto de disco; offsets del índice son relativos al
archivo BUST2. Una resta directa fue rechazada por el guard de rango y se corrigió
el análisis, sin tocar el payload. Main JP `0x80032064` confirma volumen/pitch
por registro y multiplicador global; falta PCM aislado/onset y escucha del ataque.

Ghidra: trial `20261110-ghidra-046` documenta consultas MCP y análisis headless
complementario, incluyendo una importación main con offset erróneo descartada.
Usar solo `native-tank-main-corrected-decompile/` y posteriores con bytes
contrastados, no `native-tank-main-decompile/`. La sesión MCP sigue siendo main
BAG2 JP; no se ha confirmado el overlay BAG1 mediante ese canal ni cambiado su GUI.

Siguiente unidad: terminar F2 con emisor nativo y evento/tabla de dimensiones;
F3 conserva la carencia de PCM/frame invitado. No implementar F4 con esas incógnitas
ni declarar sonido/tamaño originales por tener el mismo archivo de vértices.

#### F2 — primitivas y disparador contrastados (2026-11-10 UTC)

El emisor JP `0x8002ab3c` y sus consumidores distinguen **44 primitivas** del
miembro2: 8 G3 (`0x8002becc`, stride de paquete 0x1c), 24 G4 (`0x8002c430`,
0x24), 2 F3 (`0x8002cf6c`, 0x14), 2 F4 (`0x8002d020`, 0x18) y 8 G4 con
prefijo de ocho bytes (`0x8002d3e0`, 0x2c). Los ocho triángulos de la tapa son
Gouraud, no los F3 de la reconstrucción; faltan las cuatro primitivas F3/F4.
El cilindro usa los ocho últimos registros, cuyo cuarto word es 1. El seguimiento
del inicializador `0x80025528` ya confirma su significado: pasa `word-1` a
`0x800489a4`, construye draw-mode con `0x80048eac(…,1,1,tpage)`, inicializa G4
0x38 y habilita semitransparencia con `0x80048c88` (opcode final0x3a).
Los 24 G4 metálicos quedan en0x38 opaco y la tapa G3 en0x30; no se activa en ellos
la mezcla. Para el cilindro se selecciona ABR0 (promedio), con prefijo draw-mode
encadenado antes del polígono mediante `0x80048bd4`. En la rama PSX estándar,
el comando es0xe1000600; la otra rama de GPU se conserva en el decompile, no se
supone activa. La reconstrucción actual usa G4 semitransparente para metal y
cristal sin ese prefijo individual. La iluminación de `0x8002bbe8` usa normales/GTE y
depth cue, y la inserción OT usa profundidad; no equivale a RGB constante y OT fijo.
Evidencia: `native-tank-render-dispatch-decompile/`, `native-tank-primitives-decompile/`
y `full-fidelity-source-audit/accessory.json` bajo `_work/gaso/`.

El slot original **63 sí contiene el disparador del tanque**: evento `(16,20,1)`;
el 64 no tiene evento16. También contiene `(1,11,0x76d)` y cues1803/1805.
`attack-events.json` conserva todos los eventos extraídos con `animlib.info`.
El main JP `0x8002efc8` cruza el frame del evento16 y llama a `0x80035d80` con
actor, valor del evento y contador `param_1[7]`. Este wrapper selecciona la tabla
`0x8005510c + side*0x38 + character*4`; GAS-O P1 apunta a `0x801d5bb0`.
Ese controlador habilita el tanque con valor1 y calcula retraso desde el tercer
parámetro menos16. Por tanto no hay evidencia para reemplazar ATTACK1 por ATTACK2;
sí hay una diferencia explícita al normalizar valor1 a0 en `anim_remap_gaso.py`.
Resolver la adaptación del dispatcher BAG2, no restaurar ese valor a ciegas.

La tabla Y JP en `0x801d8280` contiene, para IDs BAG1 0..13:
`410,530,390,390,420,350,460,440,470,380,390,390,150,320` (se multiplica por4).
`scale-y-table.json` registra dirección/base y offset. No asigna valores inventados
a los personajes exclusivos de BAG2. Faltan unidades de dimensiones, consumidor del
estado rival y binding de partículas. F2 sigue
parcial; la aceptación visual/audio y F4 siguen pendientes. No se cambió el runtime.

#### F2 — Ghidra reconectado y reacción nativa identificada (2026-11-11 UTC)

- MCP recuperado sin instalación ni cambio de configuración: se abrió una sola
  instancia de Ghidra12.1.4 y el proyecto existente. `get_program_info` confirma
  `SLPM_862.19`, main JP, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  Consultas relevantes MCP: constructor de pose `0x8002bc38` (la consulta a
  `0x8002bd70` cae dentro), wrapper `0x8002c060`, setup `0x8002b5bc` e inicializador
  `0x8002d85c`. Recuperación, intentos fallidos y análisis complementario registrados
  en `20261111-ghidra-047`. La instancia queda abierta para reutilizarla.
- Preflight PASS en0.721s: `_work/workflow/20261111T024051754674Z-gaso-ghidra-reconnect/metrics.json`.
  Fuentes/recursos y EXE build/desplegado coinciden; no se hizo build, deploy ni captura.
- **Corrección de interpretación:** `0x800756bc + side*0x88` es el campo `+0x34`
  del controlador nativo que se pasa a `0x8002ed08`. Ese consumidor compara distancia
  XZ con un umbral antes de corregir la posición. Escribir `0x7fffffff` al aterrizar
  desactiva esa corrección ordinaria; **no prueba por sí mismo una animación congelada**.
  El avance del clip se calcula por otros campos en `0x8002efc8`.
- `0x8001e030` y `0x8001f6a0` consumen flag0x80 y contador signed16 de
  `0x80087992 + side*0x14`. Restan uno en su actualización de estado/ritmo habilitada
  por global0x8006ec30&2, no `delta` en cada frame gráfico; al agotarse ponen cero y
  limpian flag0x80. Esto explica la condición de salida del tanque `0x801d6480`.
  No asignar una duración fija en frames a ese contador sin contrastar sus llamadas.
- **Reacción GAS-O explícita:** `0x8001fc84`, al procesar flag0x10, selecciona
  request `0x7b` (123) si el atacante registrado es9, en lugar de la tabla general
  de golpes. Pasa ese request al controlador `0x8002d734`; este lee byte en
  `0x80051614 + 123 = 0x8005168f`, cuyo valor original JP verificado es **70**.
  Es la ruta nativa CAUGHT, distinta de forzar TIRED/slot78 BAG2. La otra ruta
  `0x80020478` tiene sus propios guards: no se presume idéntica en todos los modos.
  Evidencia: `native-tank-hit-request-routing-decompile/` y
  `full-fidelity-source-audit/reconnected-hit-routing.json` bajo `_work/gaso/`.
- MCP `0x8002d85c` confirma dimensiones BAG2 en actor `+0x1534/+0x1538/+0x153c`,
  derivadas de cabecera del modelo `+0x18/+0x1c/+0x20` por escalaR12, con división
  signed truncada hacia cero. Esto identifica el destino, pero falta verificar
  las unidades/origen de dimensiones BAG1 antes de reutilizar la fórmula del tanque.
- Las lecturas previas `native-tank-particle-binding-decompile/` identifican emisor
  y parámetros nativos; `textures-deployed.json` prueba píxeles y paletas originales
  en A/P1 USA/JP, no su direccionamiento VRAM vivo ni las otras variantes.
  `0x80022430` contiene estados de fin/victoria/fever: el antiguo rótulo «tank main»
  no demuestra su función y no se usa para concluir la reacción del rival.

Siguiente unidad F2: trazar el clip70 y sus transiciones/temporización, contrastar
el equivalente BAG2 y completar dimensiones/binding de partículas. Conservar la
ruta de evasión y restauración; no reemplazarla por escrituras continuas a slot78.
F3 sigue pendiente de PCM/onset y presupuesto sin remuestrear los efectos.
Solo investigación/documentación: F4 y aceptación de fidelidad siguen pendientes.
Comprobación documental focal de nota/plan/log: sin incidencias en
`_work/gaso/reconnect-docs-check.json`; estado JSON válido. Goldfish no requerido
en esta unidad exclusivamente documental; no se cambió herramienta productiva,
runtime, payload ni manifiesto. No se repite la suite host de entradas intactas ni
se presenta su resultado histórico como una prueba nueva del tanque.

#### F2 — CAUGHT y corrección de unidades de escala (2026-11-11 UTC)

Unidad del plan F1–F8 aprobado; **sin cambio de runtime**. Evidencia vinculada:
`_work/gaso/full-fidelity-source-audit/caught-motion.json`, `caught-contract.json`
y trial `20261111-ghidra-048`.

- Se auditaron clips66..70 de14 modelos BAG1 JP A/P1, sin errores del decoder y
  con round-trip de valores. CAUGHT70 tiene dos frames, sin eventos, metadata
  `[0,4,0,0,0,0]`;13 son estáticos, pero Strike rota el hueso5 en sus tres ejes.
  **No forzar frame0 universalmente**. TIRED69 tiene34 frames con movimiento.
  El round-trip del mismo codec no sustituye aceptación en juego ni cubre B/P2.
- `0x8002efc8` hace loop con metadata+5 cero y clamp en otro caso; CAUGHT hace
  loop. `0x8002ec60` ajusta el ancla al cerrar el loop, no decide liberar al rival.
  Mientras sigue flag0x80 se actualiza el clip existente; salida por estado/ritmo
  y siguiente request, no por terminar esos dos frames.
- BAG2 `0x8002a090` despacha request123 a78 mediante tabla `0x8005181c`, también
  confirmado por MCP. `0x8002d06c` comparte loop/clamp, pero el perfil asigna78 a
  fuente69/TIRED, no70. No sobrescribir slot78 globalmente: tiene otros usos.
  Falta seleccionar CAUGHT por rival con guardas/restauración, incluidos personajes
  BAG2 sin clip BAG1 correspondiente. La equivalencia sigue sin aceptar.
- **Corrección de unidades:** BAG1 JP `0x8002f7c0` escribe el argumento de escala
  R12 masked16 en43a8/43ac/43b0 y43b8/43bc/43c0. Las dimensiones escaladas de la
  malla son **43d8/43dc/43e0**, desde actor2c/30/34 por escala/4096 truncada hacia
  cero; ID3 añade escala al alto. Las descripciones anteriores de43b8 como
  «dimensiones» quedan corregidas por este inicializador, no por una conjetura.
- MCP BAG2 `0x8002d85c` confirma escala en14e4/14e8/14ec y1514/1518/151c, y
  dimensiones reales en1534/1538/153c. **No usar estas dimensiones en la fórmula
  del tanque `12*43b8+ajuste`**: mezclaría longitudes con escala. Los bloques14f4
  y1504 tampoco son ternas XYZ de escala demostradas. Falta contrastar escrituras
  posteriores y qué terna BAG2 corresponde a43b8 durante el ataque.
- `0x8002e72c` pasa escala base43a8 al modelo; `0x8001397c` multiplica en R12.
  Se descartó la hipótesis de que8002e64c refrescara43b8: solo envuelve8002e224,
  constructor/interpolador de poses. Estas consultas no resuelven la escala activa.

MCP sigue operativo con main BAG2 JP `SLPM_862.19`/SHAea5a1668. Los controladores
sin definición de función en GUI se analizaron adicionalmente en el proyecto
headless aislado, tras contrastar bytes; no se afirma MCP del overlay BAG1.
Siguiente F2: consultar escrituras por offsets43b8 y consumidor/terna BAG2;
cerrar selección CAUGHT y binding de partículas. No repetir búsqueda de escala
por el render de poses ni auditar otra vez clips intactos. F3 conserva PCM/onset
y audio sin remuestrear pendiente; F4 y aceptación siguen pendientes. Cartel GAS,
estable, tarjetas y preferencias intactos. Goldfish no requerido: solo RE/docs,
sin cambio productivo de herramientas, runtime, payload o manifiesto.

#### F2 — escala de referencia y escala de dibujo BAG2 (2026-11-11 UTC)

Continuación del plan aprobado, sin cambios de runtime. `scale-write-sites.json`
y `scale-reference-sites.json` en `_work/gaso/full-fidelity-source-audit/` conservan
el barrido determinista del main original JP y del main BAG2. Solo busca offsets
literales: **no prueba ausencia de escrituras por alias, memcpy o módulos**.

- Main BAG1: las únicas escrituras literales SW/SH a43b8/43bc/43c0 encontradas
  pertenecen al inicializador8002f7c0 ya contrastado; otras escrituras copian43a8
  a un actor secundario en8002d734. No hay evidencia nueva para llamar «dimensiones»
  a esas ternas ni para sustituirlas por bbox.
- BAG2:8003318c copia1514/1518/151c a14e4/14e8/14ec tanto en el actor principal
  como en el secundario. Esto identifica **escala de referencia guardada** frente
  a **escala de trabajo/dibujo**; el inicializador8002d85c establece ambas iguales.
  No se ha probado en este análisis la frecuencia con que se llama8003318c ni que
  ningún módulo pueda cambiar la referencia. No confundir el barrido con una traza.
- MCP confirma identidad del main y los32 bytes de8003318c, pero su decompilado
  devuelve FUNCTION_NOT_FOUND porque no hay función definida en esa dirección en
  la GUI. El análisis complementario aislado `bag2-tank-scale-writes-decompile/`
  (7.091s, exit0) aporta el consumidor; no se alteró el proyecto GUI.
- La coincidencia literal1514 en80040e14 es de ISO9660/directorios, **no de escala**:
  MCP del contenedor80040d9c la descarta. No aceptar todo offset coincidente como
  referencia a actor. Trial049 registra también esta consulta irrelevante.

La correspondencia estática permite diferenciar referencia y dibujo, pero aún no
certifica igualdad dinámica del tanque: falta contrastar alias/módulos pertinentes
y el argumento R12 de inicialización de ambos juegos. Siguiente unidad: comprobar
el camino de carga/inicialización y los escritores por puntero a las ternas, no
repetir el barrido directo ni los constructores de poses descartados. Selección
CAUGHT por rival y partículas/audio siguen abiertos; F4 no iniciado. Verificación
de esta unidad documental no implica aceptación en juego ni suite host nueva.

#### F2 — argumento de carga R12 y ajuste del importador (2026-11-11 UTC)

El camino de inicialización queda identificado estáticamente, sin cambiar runtime:
`full-fidelity-source-audit/scale-load-arguments.json` y
`native-tank-scale-load-decompile/8002de94.c` bajo `_work/gaso/`.

- BAG1 JP: `8002de94` llama a `8002f7c0` con el byte de tabla `800516d8+ID`
  dividido por1 normalmente. En la rama especial del cargador puede dividirlo
  por8; no se identifica esa rama como combate normal por conjetura. Tabla IDs0..13:
  `128,127,132,128,131,122,131,121,144,116,124,128,34,88`.
  El rival Gas-O normal recibe116; con ese valor la fórmula XZ del tanque por defecto da
  `12*116+230=1622` R12, no35% elegido manualmente. Las excepciones de IDs y escala
  Y originales siguen aplicándose; este ejemplo no sustituye la fórmula completa.
- BAG2: MCP de `8002b9f4` resuelve el cargador `8002b5bc`. La llamada a8002d85c
  recibe `(character_byte * signed_stage_factor)/256`, truncado hacia cero y
  enmascarado a16bits. La tabla de personaje empieza en80051904; MCP48bytes y
  payload original coinciden. Gas-O/Bi-O ID9 tiene byte98, pero **98 no es por sí
  solo la escala final**. Hay ramas para secundarios y escenario especial;
  no asumir factor256 ni extrapolar el caso normal a ellas.
- Un escritor relevante no pertenece al MIPS: `b1v_dancer_scale()` en
  `mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_versions.c` modifica referencia
  1514/18/1c y trabajo14e4/e8/ec, con `(base*q+2048)>>12`. Gas-O usaq3132 y Strike
  3429/3434; selección/versión y caché de puntero/valor guardan la aplicación.
  El reporte liga el source actual por SHA; no se ha editado ni demostrado aquí
  su orden exacto respecto del frame del tanque. Una lectura solo del main omitiría
  este ajuste. Los bbox1534/38/3c siguen sin ser escala.
- Barrido acotado de GAS-O JP y Bi-O P1/P2: las dos coincidencias del P1 Bi-O son
  words de punteros801d14ec/801d151c interpretables como instrucciones, **no
  escritores probados**. No contar datos como código ni afirmar ausencia de alias
  o memcpy. El barrido no cubre todos los overlays ni es una traza de ejecución.

Siguiente comprobación: contrastar en frames inicializados el factor de escenario,
las ternas antes/después del ajuste host y el reloj/evento del tanque, reutilizando
RAM válida si contiene esos campos; capturar solo lo que falte y preservando las
sesiones/configuración. No volver a buscar el argumento inicial ya identificado.
Esto permitirá fijar el contrato de escala original frente al espacio BAG2 antes
de F4. CAUGHT por rival, partículas y audio exacto siguen pendientes. Trial050
registra consultas/inputs/límites; unidad documental, sin aceptación en juego.

**Contraste reutilizado, sin otra captura:** el dump inicializado histórico
`20261110T034745727209Z-gaso-sign-early/sign-intro-31-ram.bin` coincide con SHA
`e272fae7241f8e9e5261ad9cbe335376dee959aef53d9616a775714d4f645a9f`.
Su metadata identifica runtime27dfebb4, no el3145ba5b actual, y no es atómico.
Factor de escenario en800af538+4 =256; Gas-O actor80256944 tiene75 en las dos
ternas; Heat actor801a8104 tiene85. El log de esa misma ejecución registra
`scale98 ->75` para Gas-O. Es coherente con `(98*3132+2048)>>12=75`, pero no es
una medición antes/después del mismo frame ni demuestra todos los escenarios.
El reporte anterior incluye estos campos y sus límites. Próximo contrato por
resolver: correspondencia del espacio de escala del efecto con el bailarín
importado, conservando proporciones/trayectoria originales; no introducir116,
75 o1622 directamente en otro espacio sin validar el consumidor.

#### F2 — convención de escala tanque/bailarín (2026-11-11 UTC)

Unidad estática, sin cambios de runtime ni captura. Reutiliza decompilados ya
guardados en `_work/gaso/`: `native-tank-lifecycle-decompile/801d6908.c`,
`native-tank-main-corrected-decompile/80013ed4.c` (no el import rechazado
`native-tank-main-decompile/`), `native-caught-scale-matrix-decompile/8001397c.c`
y `native-caught-scale-consumer-decompile/8002e72c.c`.

- Tanque BAG1: `801d6908` dibuja con rotación de `801d588c`, traslación X/Z del
  rival (+0x36f4/+0x36fc) e Y de caída por slot; escala X/Z =
  `12*rival_R12+230` (+600 en escenario 0xb o rival ID13), Y =
  `801d8280[ID rival]<<2`. `80013ed4` aplica `escala*node>>12` a la matriz y a la
  traslación de nodos: **R12, 4096 = 1,0**.
- Bailarín BAG1: `8002e72c` pasa actor+0x43a8 a `8001397c`; la matriz usa
  `S*node>>12`, pero las traslaciones de huesos usan `*S>>7`: **S/128 = 1,0**.
- BAG2: barrido de grupos `sra ...,7` empareja nativo
  {800133f4,8001397c,8004d5a0} con BAG2 {80012c9c,80013144,8004d83c}. MCP de
  `80013144` muestra la misma fórmula (hijos en +0x94/+0x98 en vez de +0xe4/+0xe8).
  **BAG2 y BAG1 comparten la convención S/128 del bailarín**, así que 75 (BAG2)
  y 116 (BAG1) son directamente comparables como tamaño de mundo.
- Falso positivo descartado: el literal 0x14e4 en `80023c38` (función 80023be4)
  es la rutina de memory card con global `800514e4`, no la escala del actor.
- Intento inválido descartado: leer node+8 del RAM histórico en actor+0x14 dio
  punteros; actor+0x14 no es la estructura de nodo en BAG2. El valor unidad de
  node+8 para el modelo del tanque **sigue sin verificar**.

**Hipótesis de contrato (no validada):** en BAG1 el tanque XZ mide
`(12*S+230)/4096` frente al rival `S/128` (≈0,375×rival + 230/4096). Conservar
la proporción en BAG2 daría `12*S_bag2 + 230*r` en XZ e Y = `tabla*4*r`, con
`r = escala BAG2 / escala nativa` del rival (Gas-O 75/116≈0,647; Strike 82/127≈0,646;
Heat 85/128≈0,664, modelo BAG2 ~2 % distinto). La altura de caída (suelo+4096,
gravedad 32*delta, tope +0x43cc) necesita el mismo factor. Antes de F4 falta:
(1) unidad de node+8 en el modelo del tanque; (2) si el tope +0x43cc depende de
escala; (3) rivales solo-BAG2 sin entrada en la tabla Y: **sin resolver, requiere
decisión del dueño** si no aparece equivalente. Las constantes 35/100, 22/100,
`1200*rem²` y el slot78/frame0 forzado del WIP siguen siendo inventadas y se
sustituirán en F4. Trial051 registra consultas y límites.

#### F2 — unidad node+8 y espacio tanque/bailarín (2026-11-11 UTC)

Unidad estática, sin cambios de runtime. Resuelve el punto (1) anterior.

- Formato común: cada hueso del archivo termina en 10 words `xf`. MCP de BAG2
  `80022518` (único llamador de `800220b8`) copia esas 10 words **sin cambios** al
  nodo: node+8/+c/+10 = `xf[2:5]` (escala por nodo). Hijos en +0x94/+0x98.
- Archivos: tanque `002.bin` (SHA106a0fc2…) un hueso, `xf=[0,0,4096,4096,4096,0,…]`;
  bailarín Gas-O `000.bin` (SHAe4197c9c…) 31 de 41 huesos con escala4096 y el resto
  con ajustes locales. Ambos usan unidad R12 (4096=1,0) por nodo. Dentro del juego
  original tanque y bailarín pasan por el mismo parser, así que la relación entre
  ambos no depende de cómo trate ese parser `xf`. Las direcciones del docstring
  (`0x80029624`) son de otra build: en el main JP cae a mitad de función (inútil).
- Consecuencia: el vértice del bailarín se escala por `S/4096` (8001397c/80013144),
  el del tanque por `(12*S_rival+230)/4096` en XZ y `tablaY[ID]*4/4096` en Y
  (801d6908/80013ed4). Las traslaciones `*S>>7` del esqueleto no pueden ser las
  del archivo (piernas de 13045 frente a rodilla12229: mismas unidades en archivo),
  así que deben venir en otra unidad de animación; **inferido, no trazado**.
- Comprobación de coherencia, no aceptación: altura en reposo de Gas-O
  (`_work/gaso/rest_pose_extents.py`, sin rotaciones) 47826 unidades de archivo →
  1354 mundo con S116; tanque sobre Gas-O mide 4480*1520/4096=1662 y radio428:
  ≈1,23 veces la altura del rival y lo rodea. En BAG2 el root del rival (+0x810,
  pelvis≈488) concuerda con unidades `archivo*S/4096`.
- Fórmula BAG2 propuesta para F4 (pendiente de validar en juego): factor de vértice
  `T_nativo(rival)*r/4096`, `r=S_BAG2_rival/S_nativo_rival`; misma `r` para altura de
  caída4096, gravedad32 y tope, conservando así los frames de la caída.

| Rival | XZ nativo | Y nativo | r | XZ BAG2 | Y BAG2 | WIP actual |
|---|---|---|---|---|---|---|
| Heat (0) | 1766 | 1640 | 85/128 | 0,286 | 0,266 | 0,35 / 0,22 |
| Strike (1) | 1754 | 2120 | 82/127 | 0,276 | 0,334 | igual |
| Gas-O (9) | 1622 | 1520 | 75/116 | 0,256 | 0,240 | igual |

El WIP es ≈22 % más ancho y ≈17 % más bajo que esta fórmula para Heat. Límites: el
modelo BAG2 de Heat difiere ≈2 % del de BAG1, y `r` por escala no capta esa
diferencia; los rivales solo-BAG2 siguen sin entrada en la tabla Y (**decisión del
dueño**). Sigue abierto: si el tope `+0x43cc` depende de escala, CAUGHT por rival,
partículas y audio F3. Trial052 registra consultas, fallos y límites.


#### F2 — altura del tanque frente al rival y rivales solo-BAG2 (2026-11-11 UTC)

Ejecuta lo acordado con el dueño («okay continua con lo recomendado»), sin cambios
de runtime. Fuente: extracción USA completa `_work/bag1_disc_full/`; la tabla de
nombres de modelo de `scus.bin` (0x80059918) da el orden de IDs 0..13 y la tabla de
escala USA 0x800558fc coincide con JP 800516d8. Se extrajo el miembro 0 de los 14
`PLAYER2/P_xxxA2.DFS` (`_work/gaso/native-models/`); el de Gas-O es idéntico byte a
byte a `character_inventory/gaso/000.bin`. Los 14 modelos se recorren completos.
Informe con SHA por DFS/modelo: `full-fidelity-source-audit/tank-height-ratio.json`.

Medida en pose de reposo (solo traslaciones, `rest_pose_extents.py`): altura del
rival `sizeY*S/4096`, altura del tanque `tablaY*4*4480/4096`. Cociente tanque/rival:
Heat 1.228, Strike 1.157, Frida 1.169, Hamm 1.536, Kelly 1.215, Shorty 1.119,
Pinky 1.171, Kitty 1.146, Hiro 1.142, Gas-O 1.227, Capoeira 1.364, Robo 1.21,
ID12 1.819, ID13 1.567.

- **No es constante.** Las ocho entradas Y distintas (IDs 0, 1, 4–9) dan 1.119–1.228,
  mediana 1.164; los doce humanoides, mediana 1.19 (1.119–1.536). El valor 390 de los
  IDs 2, 3, 10 y 11 parece compartido y explica la dispersión (Hamm es bajo de
  verdad: su modelo mide 1111).
- XZ no necesita tabla: usa la escala del rival para todos (ID13 y escenario 0xb
  usan +600; corregido en el informe, radio 437).
- Las palabras xf[0] no nulas (0x08000000/0x10000000 en huesos simétricos) parecen
  rotaciones de 180°/360° y no alteran la altura medida; no se ha trazado su consumidor.

Para rivales que no existen en BAG1 quedan dos candidatos, ambos **aproximación**
y no fidelidad original: (a) `Y = 1.164 × altura de reposo BAG2 del rival`;
(b) valor compartido `390*4*r`. **Elección pendiente del dueño.** Siguiente: medir
las alturas de reposo de los modelos solo-BAG2, el tope `+0x43cc`, CAUGHT por rival,
partículas y audio F3. Trial053 registra la unidad; sin aceptación en juego.

#### F2 — alturas de reposo BAG2 y regla unificada de altura (2026-11-11 UTC)

Continuación de la unidad anterior, sin cambios de runtime. Script
`_work/gaso/bag2_rest_heights.py`; informe con SHA de cada modelo:
`full-fidelity-source-audit/bag2-rest-heights.json`. Se midieron los modelos stock
`assets/archive/characters/<nombre>/model_a_p1/000.bin` de los slots 0..17 (tabla
de modelos 0x80055258 del main BAG2). Los 18 se recorren completos (0 bytes
sobrantes). Ningún modelo nativo ni BAG2 usa nodos tipo 2, así que las alturas
nativas de la unidad anterior no cambian. Ambos juegos tienen 14-17 nodos tipo 4 con
la misma estructura; se ignoran por igual en los dos lados. Altura BAG2 =
`sizeY*tablaBAG2/4096` con factor de escenario 256, sin ajuste host.

| Slot BAG2 | Altura BAG2 | Cociente nativo | Tanque = cociente x altura | Entrada nativa x r |
|---|---|---|---|---|
| 0 heat | 1029 | 1.228 | 1263 | 1191 (1.16x) |
| 1 strike | 1296 | 1.157 | 1499 | 1789 (1.38x) |
| 2 comet | 1114 | solo BAG2 | 1296 (mediana) | sin entrada |
| 3 tsutomu | 703 | solo BAG2 | 819 (mediana) | sin entrada |
| 4 kelly | 996 | 1.215 | 1211 | 1192 (1.20x) |
| 5 shorty | 910 | 1.119 | 1018 | 891 (0.98x) |
| 6 pander | 1080 | solo BAG2 | 1257 (mediana) | sin entrada |
| 7 kitty_n | 1225 | 1.146 | 1403 | 1432 (1.17x) |
| 8 hiro | 1155 | 1.142 | 1318 | 1314 (1.14x) |
| 9 bi_o | 1178 | solo BAG2 | 1372 (mediana) | sin entrada |
| 10 capoeira | 747 | 1.363 | 1018 | 1018 (1.36x) |
| 11 robo_z_gold | 1077 | 1.210 | 1304 | 1133 (1.05x) |
| 12 columbo | 276 | 1.819 | 502 | 502 (1.82x) |
| 13 sushi_boy | 867 | solo BAG2 | 1010 (mediana) | sin entrada |
| 14 chichi_sally | 770 | solo BAG2 | 897 (mediana) | sin entrada |
| 15 michael_doi | 1088 | solo BAG2 | 1267 (mediana) | sin entrada |
| 16 mcload | 651 | solo BAG2 | 758 (mediana) | sin entrada |
| 17 hustle_kong | 894 | solo BAG2 | 1040 (mediana) | sin entrada |

Conclusiones:

- La opción (b) `390*4*r` **no está definida** para rivales solo-BAG2: no tienen
  escala nativa con la que calcular r. Habría que inventar r, así que se descarta
  como regla general.
- Para personajes que vuelven en BAG2 con **modelo BAG2 stock**, aplicar su entrada
  nativa x r no conserva la proporción original: Shorty quedaría 0.98x (el tanque no
  le cubre la cabeza) y Strike 1.38x, porque esos modelos BAG2 no son el BAG1 escalado.
- Regla propuesta unificada: `Y_tanque = cociente_nativo[personaje] x altura de reposo
  renderizada del modelo rival real`, con cociente 1.164 (mediana de entradas
  distintas) solo para quien no existe en BAG1. Para un modelo nativo importado
  (Gas-O, Heat/Strike BAG1) es **algebraicamente idéntica** a `tablaY*4*r`, así que
  no altera la fidelidad ya establecida. Para modelos stock y solo-BAG2 es una
  aproximación que conserva la proporción tanque/cuerpo, marcada como tal.
- Límites: pose de reposo, solo traslaciones (sin rotaciones ni escala por nodo),
  sin nodos tipo 4, factor 256, sin ajuste host ni medida en juego. El slot 18
  (Heat p2) no se midió. **Elección del dueño pendiente** entre esta regla y otra.
  Siguiente: tope `+0x43cc` y caída con r, CAUGHT por rival, partículas y audio F3.
  Trial054 registra la unidad.

#### F2 — decisión de altura y contrato de caída (2026-11-11 UTC)

**Decisión del dueño (2026-11-11):** «continua con lo recomendado» aprueba la regla
unificada de altura de la sección anterior: `Y_tanque = cociente_nativo[ID] x altura
de reposo renderizada del rival real`, con mediana 1.164 solo para rivales que no
existen en BAG1 (aproximación marcada). Para modelos nativos importados equivale a
`tablaY*4*r`. Queda descartada la opción `390*4*r`. La aceptación en juego sigue pendiente.

Contrato de caída, estático, sin cambios de runtime. Informe:
`full-fidelity-source-audit/fall-contract.json` (script `_work/gaso/fall_contract.py`,
payloads nativo ec7f4b0e... y BAG2 143b4bf8... verificados por SHA).

- `+0x43cc` **no es escala**: `8002f7c0` copia ahí la Y de aparición del actor
  (43c8/43cc/43d0 = posición inicial). El tope de `801d67a0` es el suelo del rival.
- `801d5bb0`: el tanque nace en `suelo_rival+0x1000` con velocidad 0. `801d67a0`:
  `v += 32*dt; y -= dt*(v+16*dt)`; al cruzar el suelo fija Y, escribe 0x7fffffff
  (solo desactiva el recentrado XZ) y lanza el aterrizaje. **Caída y gravedad no
  dependen del rival**; solo el suelo. Aterriza en 16 frames con dt=1 y con dt=2.
- Conversión a BAG2: las dos constantes son unidades de mundo, así que se escalan
  por la relación de mundo, no por r del rival. Separación normal de bailarines:
  nativo `8002de94` ±0x310=784; BAG2 `8002b5bc` `espaciado[escenario]*4*factor/256`
  = 520 con espaciado 130 y factor 256. Relación 0.663, coherente con r de Heat
  85/128=0.664 y de Gas-O 75/116=0.647. Candidato F4: caída 4096x0.663 ≈ 2717,
  gravedad 32x0.663 ≈ 21.2 (ambas x factor/256), suelo = Y de aparición del rival.
  La duración de 16 frames se conserva.
- Contraste con el WIP `bag2jp_gaso_tank.h`: baja 1200 unidades en 12 frames
  (`GASO_TANK_FALL_DUR`, `y_drop` cuadrático inventado), es decir, menos de la mitad
  de altura y 4 frames menos. Se sustituirá en F4.
- `801d5bb0` crea **dos tanques** cuando el rival es ID10 (Capoeira, pareja) o ID5
  con el indicador de compañero; uno en los demás casos. Los parámetros de humo
  dependen de la escala del rival (`43bc*2`, `43bc*4+100`, contador 0x1f). Equivalencia
  BAG2 para parejas (IDs 10/14) pendiente con CAUGHT por rival.
- Límites: relación de mundo medida solo en escenario normal (espaciado 130);
  escenario 5 (espaciado 86) y especial 0xb sin cubrir. Valor real de dt
  (`80075f00`) no medido. Encuadre de cámara no comparado. Sin aceptación en juego.
  Siguiente: CAUGHT por rival (incluidos solo-BAG2 y parejas), guardas/restauración,
   partículas; luego F3. Trial055 registra la unidad.

#### F2 — selector de impacto BAG2 y enlace CAUGHT pendiente (2026-11-11 UTC)

Contrato estático acotado, **sin cambios de runtime**. Evidencia consolidada:
`_work/gaso/full-fidelity-source-audit/hit-selector-contract.json` y
`_work/gaso/hit-selector-verified.asm`; trials ghidra056 y capstone009.

- El selector relevante no está en el main: está en `system/005.dbi` JP,
  payload tras12bytes, base8008f890. Los barridos negativos del main no demostraban
  ausencia de emisor. No reutilizar la base USA8008f6c0 ni tratar el DBI de disco
  como memoria del combate cargada en el MCP.
- `8009b594..8009b5b4` toma el ID del actor seleccionado por S2 y lee el primer
  byte de `80051458+ID*2`; lo guarda en la petición pendiente `+0x18` del bloque
  `8005cf08+lado_receptor*0x24`. El segundo byte no nulo llama a80019d70 en esta
  rama. S2 puede invertirse respecto al receptor: no confundir emisor con víctima
  ni dar por resuelto el reflejo a partir de una sola rama.
- La entrada9 de Bi-O es `[202,1]`, confirmada contra el main y por MCP36bytes.
  Esta ruta usa reacción genérica202, no la excepción nativa de GAS-O9 que en
  `8001fc84` selecciona123→CAUGHT70. **No es prueba de todos los caminos de impacto.**
- Consumidor `8009d0a8..8009d0dc`: si la petición signed16 es no negativa, llama
  a8002a090 con modo1, factor4096 y tiempo de `+0x1c`; luego consume `+0x18=-1`
  y guarda la anterior en `+0x1a`. La petición no es una orden que deba reescribirse
  cada frame. No confundir estos offsets con el contador nativo de liberación.
- BAG2 también emite123 en8009b2cc y8009b444 bajo otras condiciones. Es incorrecto
  afirmar que123 solo puede significar «atrapado por GAS-O» o que no existe en BAG2.
  El rol de todas esas condiciones no queda identificado aquí; **no cambiar global78**.
- Las políticas actuales Heat/Strike/Gas-O sobreescriben el legado78←70 por78←69
  TIRED. El mapa de roles no-danza efectivo no conserva otro destino para fuente70.
  Esto es una comprobación de fuentes/políticas, no una nueva auditoría del payload
  desplegado. No se ha probado que un clip stock BAG2 equivalga a CAUGHT.

Consecuencia para F4: enlazar CAUGHT por rival y solo en el contexto del ataque
importado, conservando las reacciones stock fuera de él. No basta cambiar el número
de petición ni congelar frame0. Los originales70 de los personajes BAG1 siguen
disponibles en las fuentes; Strike conserva su movimiento de dos frames.
Pendiente inmediato: establecer un enlace de clip independiente y reversible para
los imports presentes y su pareja, y una adaptación explícita para esqueletos
solo-BAG2; verificar capacidad/tablas, guardas de versión/emisor/víctima/reflejo,
propagación a compañero y restauración por fin/cambio de actor/escena. Después,
partículas y F3 PCM/onset1806/180a, sin reabrir búsquedas del selector ya resueltas.
F2 permanece incompleto y no hay aceptación de fidelidad ni despliegue nuevo.

#### F2 — tablas de clips y enlace CAUGHT reversible (2026-11-11 UTC)

Unidad estática, sin cambiar runtime. `clip-table-contract.json` bajo
`_work/gaso/full-fidelity-source-audit/` contrasta el main y el dump histórico
`sign-intro-31-ram.bin` de la ejecución20261110T034745727209Z. No es una captura
atómica ni del runtime actual. Trial057 registra las consultas y los límites.

- Actor BAG2: `+820` número N de clips; `+824` tabla de punteros a motions;
  `+828` longitudes u16; `+82c` punteros a metadata. `80031d3c` y `800319fc`
  reservan4N bytes, luego2N, alinean a4 y reservan4N. `800125fc` cuenta motions
  hasta el terminador; `8001262c` toma frames de motion+4; `800126a4` resuelve
  metadata mediante motion+offset y el desplazamiento guardado allí.
- En el dump, Gas-O80256944 y Heat801a8104 tienenN101. Las101 entradas de cada
  actor concuerdan en frames y metadata con sus motions. El final de las tablas
  coincide exactamente con actor+14, inicio de otra reserva: **no hay capacidad
  adicional demostrada para escribir la entrada101 en las tablas originales**.
  Gas-O78 tiene34frames y Heat78 tiene44; no son los dos frames CAUGHT originales.
- `800326d4` reconstruye/amplía tablas y puede copiar los mismos punteros y N al
  compañero de8005f80c[lado*2]. El constructor31d3c crea compañeros para10/14;
  5/6 también tienen rutas de compañero con identidad diferente. No asumir que
  toda tabla es privada, ni que ID o lado por sí solos identifican al compañero.
- El controlador8002d06c consulta metadata/eventos y longitud del clip anterior
  **antes** de aplicar una nueva orden. Después mantiene reloj/interpolación;
  metadata+5=0 hace loop mediante módulo, que exige longitud no nula. Modo1
  reinicia al entrar; no justifica escribir frame0 en cada actualización.
- El consumidor de pose8002bc38 usa motions+824, slots actual154c/anterior1550,
  frame1554/siguiente1558 y caches1494/1498. El decoder800128b4 reinicializa si
  cambia el puntero motion en su estado+830;8002ccc8 también lee+824 para root.
  Cambiar solo el puntero metadata o el slot no constituye un enlace completo.

**Diseño candidato, aún no implementado ni aceptado:** copiar las tres tablas a
una reserva privada del actor conN+1 entradas, conservar lasN originales y añadir
CAUGHT enN, sin tocar78 ni los mapas globales. ConN101 las tablas nuevas requieren
1020bytes, más motion/metadata y estado de control; no es una reserva ya autorizada
o verificada en RAM. El clip debe tener dos frames válidos, loop/eventos originales
y conversión de esqueleto/escala comprobada. No reutilizar un hueco por conjetura.

La transacción futura debe ejecutarse fuera de lecturas concurrentes del juego,
guardar identidad/generación del actor, N y los tres punteros, y comprobar que no
los reemplazó otro cargador. Cada compañero real requiere su enlace y su clip,
aunque antes compartiese tablas. Liberar por fin/cambio de actor/escena sin escribir
en memoria reciclada; antes de quitarN, ningún slot actual/anterior ni decoder/cache
puede seguir referenciando la entrada o motion añadidos. No restaurar ciegamente
un frame/slot viejo sobre una nueva reacción legítima. Estos son requisitos de
seguridad, **no una implementación demostrada**.

Siguiente unidad: preparar y auditar los CAUGHT70 originales para Heat/Strike/Gas-O
por traje/lado con el conversor existente, y verificar el punto de entrada/salida
del controlador y callbacks por personaje para un slot añadido. Parejas, reflejos
y retarget solo-BAG2 siguen abiertos; no afirmar CAUGHT stock equivalente. Reutilizar
este contrato y el selector056, sin repetir sus búsquedas. Después partículas/F3.

#### F2 — inventario de huecos existentes para CAUGHT (2026-11-11 UTC)

El propietario preguntó si había espacios libres para añadir CAUGHT a todos los
personajes y aprobó auditar primero los huecos existentes. Esto **sustituye el
siguiente paso de conversión inmediata** del apartado anterior. Reserva sin sitio
para crecer no equivale a lista sin entradas vacías.

`reusable-slots.json` y `reusable-slot-candidates.json`, bajo
`_work/gaso/full-fidelity-source-audit/`, ligan por SHA72 listas stock
(18 personajes × A/B × P1/P2) y24 listas importadas (Heat/Strike/Gas-O ×4 × USA/JP).
Las importadas se extrajeron del payload experimental376287ab con el índice source
actual ligado por SHA y layout comprobado; no es una lectura de todos los actores
actuales en RAM ni prueba de identidad del índice compilado.

| Listas stock, idéntico resultado en sus cuatro variantes | Slots de cuatro bytes cero |
|---|---|
| Heat, Strike, Bi-O, Columbo, Comet, Hustle Kong, Kelly, Kitty-N, Michael Doi, Robo-Z Gold, Shorty, Sushi Boy, Tsutomu | 1,97 |
| Hiro | 1 |
| Pander | 97 |
| McLoad | 1,68,96,97 |
| Capoeira | 1,97,117 |
| Chichi/Sally | 1,95,96,97,116,117 |

Todas las24 listas importadas tienen huecos1/97 y101 entradas. Stock tiene101
excepto Capoeira/Chichi-Sally, con118. **No existe un slot vacío común a las72
listas stock**: Pander tiene56frames en1 e Hiro218frames en97.

Un hueco no demuestra un rol muerto: el dispatcher8002a090 selecciona1 para
Pander(ID6) si la tabla pide0 y su slot actual es0; request143 corresponde a97
(WIN4). Otros huecos nominalmente alcanzables:68 por requests84/102,95 por141 y96
por142.116/117 requieren revisar remaps/compañeros, no basta la tabla nominal.
Los duplicados completos también se inventariaron, pero no se consideran libres.

Recomendación pendiente de prueba: priorizar **slot1 para Heat/Strike/Gas-O** en
vez de ampliarN o alterar78. Para el resto, escoger por perfil; Pander necesitaría
otro candidato (97 solo tras resolver WIN4). No se ha probado todavía la ausencia
de lectores directos, callbacks o transiciones que seleccionen esos huecos fuera
del dispatcher. No instalar CAUGHT en ninguno por este inventario solo.
Siguiente: acotar las rutas a1 de los tres imports y el enlace/retirada reversible;
después cubrir Pander/pares y retarget solo-BAG2. Se mantienen el loop nativo de
dosframes, la prohibición de forzarframe0 y las guardas/restauración de trial057.
Trial058 conserva consultas, errores y límites. Sin cambios de runtime ni aceptación.

#### F2 — rutas del slot1 y reserva acotada al combate (2026-11-11 UTC)

Continuación de la auditoría aprobada, **sin instalar CAUGHT**. Los reportes nuevos
`slot1-routes.json` y `slot1-callbacks.json` en
`_work/gaso/full-fidelity-source-audit/` conservan hashes y contextos de instrucciones.
Se reutiliza el inventario058; no se volvieron a extraer sus listas de animaciones.

- Main y seis DBI de `assets/archive/system`: siete llamadas literales a8002d06c
  en main, todas dentro del dispatcher8002a090 ya analizado. Las tres escrituras
  literales a154c/1550 son del controlador y del inicializador8002d85c (este pone0).
  El módulo005 llama al dispatcher, no directamente al controlador. Sin embargo,
  **004 tiene dos llamadas directas** (offsets de fichero4b24/4c34, argumento de
  slot cargado de pila). No se deduce que sus valores excluyan1 ni se inventa su base.
- Los72 DBI stock de personajes y24 DBI de packs importados USA/JP no contienen
  llamadas/saltos literales a8002a090/8002d06c, punteros literales a ellos ni stores
  con offset154c/1550. Esto descarta esas formas concretas en esos bytes, **no**
  aliases, offsets calculados o llamadas indirectas. Los imports se leen del payload
  376287ab mediante el mismo índice source ligado por SHA: no es prueba de RAM actual.
- Relectura de8002a090: el cambio nominal0→1 está guardado por ID6/Pander;
  propagación a compañeros por IDs5/6/10/14 no pertenece a Heat0/Strike1/Gas-O9.
  No convertir esta observación en soporte de parejas. La tabla de retorno de timer
  800518ec empieza86,88,90,93,93,0,0,0 (MCP y raw coinciden); esos ocho bytes no
  contienen1, pero no se demostró aquí todo rango posible de indexación.
- MCP8002cf44 confirma que el vencimiento del reloj lee metadata/duración del
  slot actual para calcular velocidad y siguiente segmento; no selecciona un clip
  nuevo. El callback3190c reutilizado llama indirectamente al handler del personaje.
  MCP319ac no está analizado (`FUNCTION_NOT_FOUND`): no afirmar agotadas esas rutas.

**Candidato de integración, todavía no implementado:** usar1 únicamente durante
combate005 para un rival importado Heat/Strike/Gas-O con identidad de actor, versión,
tablas, entrada vacía y clip CAUGHT real verificados. No reservar1 globalmente, no
alterar78 ni reutilizar97/WIN4. Primero preparar raw motion, longitud y metadata
coherentes; entrar por el controlador para reiniciar una vez y dejar el loop nativo,
no escribir frame0 cada tick ni destruir metadata vieja antes de que se consuma.

La retirada debe respetar una reacción legítima nueva: liberar el control al próximo
pedido válido, sin restaurar encima el slot previo por fuerza. Conservar el contenido
prestado mientras current154c, previous1550, decoder830 o caches todavía lo puedan
referenciar; verificar cualquier tabla compartida. Cambio de actor/escena/versión
invalida la identidad y prohíbe escribir sobre el nuevo actor. Estos son requisitos
para regresión, **no garantías existentes** ni autorización de desplegar el candidato.

Siguiente unidad: auditar CAUGHT70 de Heat/Strike/Gas-O por traje/lado/región y su
conversión en el modelo importado, con loop y metadata completos; reutilizar las rutas
anteriores y probar entrada/cesión/restauración en el seam host antes de tocar runtime.
004 y llamadas indirectas siguen sin certificar un slot libre global. Pander/pares y
retarget solo-BAG2 siguen abiertos; después partículas/F3. Trial059 registra límites.

#### F2 — CAUGHT original por variante y modelo importado (2026-11-11 UTC)

`_work/gaso/full-fidelity-source-audit/caught-variants.json` liga las24 combinaciones
Heat/Strike/Gas-O × trajeA/B × ladoP1/P2 × USA/JP con sus DFS originales, modelo y
lista del payload desplegado376287ab. Se reutilizó el inventario058 y su índice
source por SHA; **no se alteró el paquete ni se leyó RAM de actores actuales**.

| Rival importado | CAUGHT70 bytes | Tracks / frames | Movimiento entre frames | Aumento de lista al sustituir vacío1 |
|---|---:|---|---|---:|
| Heat | 348 | 19 / 2 | ninguno | 344bytes |
| Strike | 352 | 19 / 2 | hueso5 | 348bytes |
| Gas-O | 348 | 19 / 2 | ninguno | 344bytes |

Cada personaje tiene un único hash de CAUGHT entre sus ocho variantes. Metadata
original `000004000000000000000000`, sin eventos, byte5=0: el controlador puede
recorrer el loop de dosframes; una pose estática no justifica forzarframe0.
El stream se decodifica con índices válidos para el modelo, sus19tracks y valores
completos sobreviven al round-trip del codec y se comprueba el offset de metadata
por lectura independiente de words. Round-trip no equivale a reproducción en juego.

Los24 modelos conservan grafo de huesos y transformaciones originales, y el prefijo
parseado es idéntico a convertir el modelo de su DFS correspondiente. Strike/Gas-O
coinciden además en todos los bytes del miembro. **Heat no**: conserva5112bytes
anexos en trajeA y4520 enB después del modelo parseado; su función no se deduce aquí.
La primera auditoría falló al asumir fin de miembro=fin de modelo. La comprobación
posterior identifica el prefijo convertido exacto y liga el anexo por hash; no se
elimina ni se declara irrelevante. No copiar el miembro completo de otro personaje.

Serialización solo en memoria: sustituir el vacío1 de4bytes por CAUGHT original,
conservar101slots y reparsar produce **los otros100clips idénticos byte a byte**,
incluido78/TIRED. Los344/348bytes son crecimiento de esa lista, no presupuesto
completo de DFS/payload/RAM. No se generó ni instaló contenido nuevo en este ensayo.

Queda lista la evidencia del clip para estos tres imports, **no** la aceptación del
enlace ni el retarget de rivales stock/solo-BAG2. Siguiente: pruebas del seam host
de préstamo1, entrada una vez, loop, cesión ante reacción legítima y retirada solo
cuando current/previous/decoder/caches no lo referencien; identidad de actor/tablas
y escena como en trial059. No repetir esta extracción mientras hashes no cambien.
Después integrar únicamente el candidato acotado que pase esas pruebas, manteniendo
abiertos parejas, partículas y F3; ninguna prueba host sustituye el flujo en juego.
Trial060 conserva el fallo inicial, consultas y límites. Sin cambios de runtime.

#### F4 parcial — política host de préstamo CAUGHT, sin integrar (2026-11-11 UTC)

Primer componente C experimental en `bag2jp_caught_loan.h`, con harness real
`tools/test/caught_loan_harness.c` y runner `tools/test/test_caught_loan.py`.
**Solo decide acciones; no lee/escribe RAM, publica tablas, invoca el controlador,
reproduce el loop ni está incluido en el runtime.** F2/F3 y el port F4 siguen abiertos.
El adaptador futuro debe comprobar hechos reales, aplicar la acción atómicamente
y solo entonces adoptar `next`; ante fallo conserva el estado anterior.

- `ENTER` una vez por hit creciente no nulo: módulo005, imports Heat0/Strike1/Gas-O9
  versión1, identidad completa de carga/actor/tablas, clip verificado, tablas
  exclusivas, slot1 vacío, ninguna referencia y punto seguro declarado por adaptador.
- `YIELD` ante otra reacción legítima, fin del impacto o cambio de hit; no selecciona
  una animación previa obsoleta. `RESTORE` significa retirar contenido prestado,
  solo tras cesión, punto seguro y cero referencias current/previous/decoder/pose;
  bits de referencia desconocidos también bloquean. No sobrescribe78 ni fuerza frame0.
- Pérdida de identidad, alias o binding produce `ABANDON`: reserva huérfana retenida,
  sin restaurar/liberar/reutilizar. Un descriptor queda ligado a su primera identidad
  incluso en IDLE; no se resetea para borrar el historial. Quiescencia y disposición
  de descriptores descargados siguen siendo obligaciones del adaptador, no funciones
  implementadas aquí. No se certifica slot1 como libre globalmente.

Verificación del componente: RED inicial8métodos/25fallos de aserción con stub NONE;
GREEN inicial8; regresión de replay RED1; estado final **12métodos nuevos y19pruebas
enfocadas PASS**, compilando este header con WSL gcc C11, Wall/Wextra/Werror.
Mutaciones finales **24/24 detectadas**, sobre copias temporales sin tocar el header.
El primer ensayo ampliado detectó23/24: usar el mismo hit en B ocultaba la guarda
de identidad tras la de replay. Se reforzó B con hit posterior y se conservó ese
resultado fallido, no se borró ni se contó como PASS.

**Suite completa no verde:**231tests,1failure y31errors; los32nombres coinciden con
la primera suite de esta sesión. Hay errores de enlace/compilación en audio, shim
y regiones, además de comprobaciones de assets; el fallo único es
`StrikeCostumeAssetsTests.test_package_keeps_models_separate_from_texture_packs`.
Nombres y trazas completos: `_work/gaso/caught-loan-verified-full.log` y
`_work/gaso/caught-loan-host-policy.json`. No se alteraron esas costuras ajenas para
ocultarlos. Tampoco las7pruebas del tanque WIP demuestran fidelidad de su geometría.

**Goldfish, 2026-11-11 UTC:**2revisores en frío, spec
`_work/goldfish/spec-caught-loan-policy.md`, solo los3archivos anteriores;
base9d9de35, header revisado SHA
`883a434c3d99cf0f66571fc782efd8d77504bd40b703ba764b005d60b8d9db5c`
(reconstruido invirtiendo la corrección; no se guardó snapshot inicial de tests).
Veredicto **CON HALLAZGOS**: ambos confirmaron pérdida del historial A→B→A al
reasignar owner en IDLE. Reproducido por aserción fallida y corregido ligando el
descriptor a su primera identidad; además se ampliaron referencias de entrada,
pérdida en RETIRING, nuevos/decrecientes hits e inmutabilidad de ambos inputs en
las cuatro acciones. Sin hallazgos refutados; adaptador/RAM/teardown no verificados.
Re-verificación final19PASS y24mutaciones; no se lanzó una segunda revisión.
Header tras triaje SHAaebf5bc479f9d95c01cacf77dab229ca16d73b58317e44662dd5942594f6ecfb.
Evidencia: `_work/goldfish/caught-loan-policy-verdict.json` y reporte host anterior.
Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.

Siguiente: adaptador mínimo que pruebe punto seguro y publicación/entrada/cesión/
retirada con memoria/controlador reales; primero regresiones host de la transacción,
sin confundir flags sintéticos con prueba de exclusividad o referencias. Reutilizar
clips24variantes y auditorías previas. Rutas004/indirectas, parejas, rivales stock/
solo-BAG2, partículas y audio exacto pendientes. Sin build del juego ni despliegue.

#### F4 parcial — transacción RAM CAUGHT en host, controlador pendiente (2026-11-11 UTC)

Continuación aprobada, sin integración en el runtime. Nuevo componente C
`mods-src/bag2jp.feature.bag1-content/bag2jp_caught_binding.h`: `b1cb_publish()` y
`b1cb_restore()` validan un buffer RAM y publican/retiran la tupla del slot1
raw4bytes/length2bytes/metadata4bytes. Todos los rechazos preceden a la escritura;
solo esos10bytes pueden cambiar. No escriben slot/frame/pedido, ni llaman al
controlador, ni adoptan `b1c_decide.next`. Restaurar conserva una reacción legítima
nueva. Repetir mientras la tupla está instalada se rechaza; después de retirarla
el primitivo puede republicar: el historial por impacto pertenece a la política
ligada a identidad, que no se debe resetear para evitar sus guardas.

- Comprueba límites/alineación, tamaños en64bits, actor/ID/lado/count/tablas,
  tupla vacía de origen o tupla prestada exacta,2frames/cabecera metadata CAUGHT
  y solapamientos completos/parciales/cruzados de tablas de los cuatro
  actores cargados. La exclusividad es **conservadora**: también rechaza tablas
  compartidas entre dos actores adicionales, aunque no sean el destinatario;
  puede rechazar parejas ajenas. No prueba ausencia de alias en otros subsistemas.
- `paused` y `quiescent` siguen siendo precondiciones del futuro llamador, no
  hechos probados por booleanos. Autenticidad de clip/esqueleto, versión/generación/
  epoch, parada exclusiva y límite real decoder/pose/controlador siguen pendientes.
  Leer830/1494/1498 y excluir current154c/previous1550 añade guardas, no demuestra
  quiescencia. La atomicidad solo se afirma frente al guest detenido, sin callbacks
  ni observadores concurrentes. No libera clips ni descriptores huérfanos.

Pruebas reales C con RAM de bytes, no copia Python del componente:
RED4métodos/11aserciones fallidas con stub de rechazo; GREEN inicial16PASS.
Final25PASS en22.215s (6métodos nuevos y los19 previos);16/16mutaciones detectadas
en15.698s;51casos ASAN/UBSAN sin diagnósticos en10.088s. La primera ronda de16
mutaciones dejó sobrevivir la guarda RAW porque otra condición enmascaraba el
fixture; corregido el fixture válido y conservado el resultado fallido. Suite
completa237tests en42.624s: **1fallo31errores**, mismos32nombres que la primera
suite de esta unidad. No green global ni aceptación del efecto. Logs/reportes en
`_work/gaso/caught-binding-host.json` y `caught-loan-binding-*.log`.

Ejecutado además el header sobre COPIAS del dump histórico sign-intro-31, SHA
e272fae7241f8e9e5261ad9cbe335376dee959aef53d9616a775714d4f645a9f, runtime27dfebb4,
no atómico/no actual: actores Gas-O80256944 y Heat801a8104, ambosN101; clips
originales70 de348bytes. Reserva de clip SINTÉTICA en la copia, no asignación libre
probada en vivo. Publicación dentro de10bytes y retirada exacta byte a byte;
fuente/dump intactos. `caught-binding-verified-ram-probe.json`,0.335639s excluye
compilación/preparación; no es reproducción de la animación ni traza del MIPS.

**Goldfish — 2026-11-11 UTC:** spec `_work/goldfish/spec-caught-binding.md`, base
bcd59c3, dos revisores frescos, header revisado SHA
e6b16c5358bff2d0ad18c12f8ce1dea9aef53a8bb4b7faf68634bd213939d84c
con snapshot; snapshot inicial de tests no retenido. **CON HALLAZGOS**: alias entre
actores adicionales reproducido RED y cerrado conservadoramente; fixtures de alias
de retirada, destinos RAW/LENGTH/META, pérdida RAW/length y count extremo aislados.
Precisado el alcance del retry. Al corregir alias se detectó además en revisión
propia un desbordamiento del inventario con cuatro actores ajenos y owner ausente:
reproducido ASAN RED, acotado y re-verificado51casos limpios. No se ocultó esa
regresión ni se lanzó segunda revisión. Sin hallazgos refutados; integración real
fuera de alcance. Header final SHA5406260b11454c0d2679b1f6556349d00e045bea4b051eed87adf29985c873ce.
Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.

Siguiente: demostrar punto de entrada/retirada real y componer política+transacción
sin adoptar estado si falla la publicación. La lectura MCP8002d4a0 incluye
SW8002d4b8 al slot, después de procesar el clip antiguo: **no prueba un hook seguro**
ni permite ignorar temporales/callbacks del controlador. Probar ejecución efectiva
del controlador antes de integrar; no otro inventario de clips/huecos. Parejas,
retarget stock/solo-BAG2, partículas y F3 siguen abiertos. Sin build del juego,
payload modificado, despliegue ni partida nuevos. Trial062 registra límites.

#### F4 parcial — adaptador compuesto CAUGHT, controlador ejecutado (2026-11-11 UTC)

Continuación aprobada, sin integración en el runtime. Nuevo componente C
`mods-src/bag2jp.feature.bag1-content/bag2jp_caught_adapter.h`: `b1ca_apply()`
compone la política ligada a identidad (`b1c_decide`) con la transacción de RAM
pausada (`b1cb_publish`/`b1cb_restore`) de forma que RAM cambia ANTES de adoptar
estado. Devuelve 1 si la observación se manejó y quedó coherente, 0 si la
transición decidida no pudo completarse (nada cambió salvo la parte infalible de
una transacción exitosa, así que el llamador reintenta en el siguiente punto
seguro con el MISMO adaptador), y `committed` solo es 1 cuando el descriptor del
préstamo o la tupla RAM cambiaron de verdad: `B1C_NONE` se maneja pero nunca se
commitea.

- ENTER publica los diez bytes del slot1 antes de adoptar; `binding_valid` impide
  una segunda publicación por impacto y `b1cb_publish` sigue rechazando un slot que
  ya no contiene la tupla vacía original. La petición de entrada es una sola por
  impacto: el adaptador no reintenta `request_entry` (edge-triggered, sin acuse);
  si la entrega falla, ese impacto pierde CAUGHT en silencio y la recuperación es
  ceder y restaurar.
- YIELD adopta RETIRING sin tocar RAM ni la petición entrante. RESTORE exige
  binding propio, VM pausada y quiescente y la tupla aún nuestra; el fallo conserva
  RETIRING para el siguiente punto seguro. RETIRING sin binding se adopta de vuelta
  a IDLE en vez de bloquear para siempre. Invariante declarada y aseverada tras
  cada escenario: `phase == B1C_IDLE` implica `!binding_valid`.
- ABANDON es terminal para el descriptor. Ahora re-deriva la propiedad contra RAM
  (`b1ca_owns_tuple`, independiente de current/previous porque un CAUGHT en
  reproducción hace legítimamente current al slot1): si el slot ya no es nuestro lo
  da por libre; si la tupla sigue exacta y solo llega `binding_intact = 0`, DEFIERE
  para que una muestra transitoria no destruya el impacto; si puede, libera el slot
  mediante `b1cb_restore` y solo entonces baja `binding_valid`. Un restore
  rechazado dentro de un guest detenido deja la tupla instalada y debe el teardown
  al llamador (fuera de alcance). Sin parada y quiescencia no se huérfana.
- `b1ca_matches_identity` compara los siete campos que un binding puede portar
  (actor/raw/length/metadata/count/character/side). Generación, epoch, content tag
  y version siguen siendo del llamador: el seam no prueba autenticidad de carga.

Contrato del controlador probado ejecutando `FUN_8002d06c` original sobre el
intérprete de producción (probe13, `_work/gaso/controller-probe-probe13.txt`): el
tick de entrada avanza el frame, dispara los eventos del clip VIEJO (sink
`0x800319ac`) y solo después escribe `+0x154c` y decodifica en ese mismo tick; por
eso slot1 debe estar publicado antes de que llegue el pedido. Una petición nueva
legítima se adopta de inmediato (slot 89 limpia current/previous), CAUGHT no se
restaura, la entrada deja `frame = 0` y `+0x1554`/`+0x1558` no se escriben. El
evento es dependiente de ventana `(prev_frame, new_frame]` y el `next` transitorio
depende de la longitud del clip viejo (44 frames -> 1, 1 frame -> 0).

Pruebas C reales con RAM de 2 MB, no copia Python del componente: RED 45 casos, 38
fallan con stub de rechazo puro y los 7 de rechazo puro pasan; GREEN 13 métodos /
13 PASS en 9.904 s; 42/42 mutaciones muertas en 31.546 s sobre los tres headers
(incluye guardián de slot ocupado, orden binding/publicación, `committed`,
identidad, replay, poses A/B y exclusividad); 45 casos ASAN/UBSAN sin diagnósticos
en 8.31 s. Suite completa 250 tests en 40.176 s: 1 fallo y 31 errores, mismos 32
nombres preexistentes que la base de 237, ninguno en `test_caught_*` (+13 tests,
+8 métodos nuevos del componente). Se excluye y documenta un mutante equivalente:
el guard `binding_valid` de ENTER es inalcanzable por la API porque la política
pura nunca decide ENTER estando HELD; se conserva como defensa en profundidad. El
harness empieza con `#undef NDEBUG` para que una compilación de release no lo
convierta en verde vacío.

**Goldfish - 2026-11-11 UTC:** dos revisores frescos (cobertura de tests y máquina
de estados), spec `_work/goldfish/spec-caught-adapter.md`, base c688767, solo los
cinco ficheros del alcance. Ambos **CON HALLAZGOS**. El revisor de estado confirmó
que ninguna ruta adopta estado sin cambiar RAM ni cambia RAM sin adoptar, y que
todo lo falible precede a `b1cb_commit`. Triaje: identidad sin ejercitar,
`references` siempre 0, `incoming_reaction` siempre 0, contenido de
`adapter.binding` nunca inspeccionado, doble ENTER por el motivo equivocado,
`committed = 1` en `B1C_NONE`, poses, exclusividad, reintento con adaptador nuevo,
replay del mismo `attack_id` y flags siempre favorables quedan cubiertos por
escenarios nuevos y el mutante que cada uno mata; ABANDON deja de ser irreversible
con una sola muestra; RETIRING sin binding ya no se bloquea. Se aceptan y
documentan como limitaciones: `request_entry` sin acuse, identidad sin
generación/epoch/tag/version, y dos hallazgos abiertos sobre
`bag2jp_caught_binding.h` (el comentario de exclusividad sobredeclara comparación
por valor y `b1cb_actor_matches` usa offsets literales) que no se tocan aquí para
no invalidar el hash verificado de esa unidad. No se lanzó una segunda revisión.
Los hashes revisados (adaptador `e7be285e...`, harness `d8654f4d...`) no conservan
snapshot; los finales están en `_work/gaso/caught-adapter-host.json` y el veredicto
en `_work/goldfish/caught-adapter-verdict.json`. Veredicto de revisor: no es
aprobación del propietario ni permiso de despliegue.

Siguiente: integrar el adaptador en el hook real (publicar antes de la petición,
consumir la cesión y retirar tras el yield) y probarlo con los 24 clips nativos;
después retarget de parejas y rivales solo-BAG2, partículas nativas de impacto y
aterrizaje, y F3 de audio exacto sin remuestreo (`0x1806`/`0x180a`,
`0x6906`/`0x690a`, presupuesto 64032). Sin build del juego, payload modificado,
despliegue ni partida nuevos. Trial 063 registra límites.

#### F4 parcial — seam real del controlador: la entrega por `+0x18` no alcanza slot1 (2026-11-11 UTC)

Decisión del propietario: «Hook en controlador (Recomendado)». Sin cambios de
runtime, build ni despliegue en esta unidad. Detalle y comandos:
`_work/gaso/caught-seam-findings-20261111.md`.

- Runtime: no hay puntero a la RAM invitada; solo `psx_mod_read/write_*`. Los
  headers del adaptador (`uint8_t *ram`) necesitan una capa de acceso para el
  runtime, que invalida los hashes verificados y obliga a repetir RED/GREEN/
  mutaciones/sanitizer. Durante un vblank el invitado está parado (`paused`), pero
  el vblank llega en límites de dispatch, también anidados: `quiescent` no está
  probado en `b1v_vblank`.
- Cadena de llamadas: los siete `jal 8002d06c` están dentro de `FUN_8002a090`;
  este solo se llama desde `005.dbi` (`8009d088/d0c0/d100/e0f0`). El consumidor de la
  petición pendiente es `8009d0a8 lh a2,0x18(s5)` (palabra `86a60018`) en
  `FUN_80099e90`, al que se llega por puntero. El cierre estático de callees de
  `8002a090`/`8002d06c` tiene 18 saltos indirectos sin resolver, así que no prueba
  la no reentrada; un barrido de la pila viva buscando las direcciones de retorno
  de `8002a090` sí sería una prueba conservadora.
- **Bloqueo del contrato `request_entry`:** en modo 1, `FUN_8002a090` traduce la
  petición a slot con las tablas `8005180c` (+10 sustituciones `80051838`),
  `8005182e`, `8005181c` y `800518e4`. Leídas por MCP, ninguna da 1 en ningún rango.
  Solo Pander (ID6) llega a slot1. Escribir en `+0x18` no puede entrar en slot1
  para los IDs 0/1/9.
- Seam realizable: function-entry en `0x8002d06c` (`mod_function_entry_funcs`).
  Precedente: `0x8002C404`, que funcionó y se retiró el 05-11 solo por razones
  visuales. El callback corre antes de que el cuerpo lea `cpu->gpr`. Para el rival,
  con modo 1 y el slot traducido de la petición nativa del impacto (Gas-O: entrada
  `[202,1]`): publicar slot1 y cambiar `a2=1`, sin escribir en `+0x18`.
  `func_8002D06C` existe en el shard 09; hay scripts de codegen aislados en
  `_work/strikedbi/{generate,stage}_lighting_entry.py`.
- Abierto antes de implementar: el contrato nuevo del adaptador (redirección en
  lugar de `request_entry`) con sus regresiones host; la residencia en RAM invitada
  del clip CAUGHT auténtico por rival; la salida o temporizador de la ruta 202
  frente al contador nativo de liberación `0x80087992+side*0x14`; y las llamadas a
  compañeros (líneas 437/456) frente a la llamada principal (412).

Siguiente: con el propietario, aprobar la redirección en la entrada del
controlador y su contrato. Después: capa de acceso RAM con la verificación host
completa, codegen aislado del hook, build y partida.

**Aprobado por el propietario (2026-11-11):** redireccion en la entrada del controlador («Aprobar redirección (Recomendado)»): resolver primero con evidencia residencia del clip, salida/temporizador y parejas; luego contrato nuevo con verificación host completa, codegen aislado, build, despliegue exp y partida.

### 2026-11-11 — clean-trace-review-20261111: recuperación y candidato diagnóstico

- Recuperada la ejecución interrumpida `20261111T161441118945Z-gaso-tank-test`: no tenía resultado ni restauración y usó el ejecutable antiguo. No es prueba limpia del ataque. Restauración exacta de los tres ajustes anteriores al cambio manual de tarjetas: `_work/gaso/clean-trace-recovery/report.json`; 41 saves sin cambios durante la recuperación, sin afirmar igualdad antes del intento antiguo.
- Traza BAG2: song-frame `0x800892EC`, pending por lado `0x8005CF20/44`; no se atribuye semántica del beat/bar BAG1 a ese contador. Formato antiguo de eventos preservado; muestras separadas sin duplicar resultados cuando solo cambia reloj/pending. El muestreo vblank puede perder peticiones transitorias. Retiradas las escrituras de slot78, frame0 por tick y halfword adicional del tanque; adaptador CAUGHT real todavía no integrado.
- Goldfish: dos revisores fríos, ambos con hallazgos. Corregidos guard de log nulo/traza apagada, duplicación de eventos, cobertura real del callback Gas-O/pending de ambos lados y comentario de congelación falso. RED y GREEN registrados; 33 pruebas específicas pasan. Suite completa: 259 pruebas, 1 failure + 31 errors, exactamente los mismos 32 nombres previos; no se declara suite verde. Evidencia: `_work/gaso/caught-loan-trace-review-{red,green,full}.json`, `_work/gaso/caught-adapter-full-compare-trace-review-full.json`, `_work/goldfish/clean-trace-verdict.json`.
- Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Build aprobado para diagnóstico: `_work/workflow/20261111T163252104139Z-gaso-clean-trace-final/metrics.json`, 34.033 s, dos jobs. Fuentes staged con respaldo y hashes: `_work/gaso/clean-trace-stage-backup/`. Despliegue EXE-only experimental verificado: SHA `6a5435966cd672f8cc5fc824b67bf37be35c2bd21442051c14fec6dcb25658d1`; `_work/gaso/clean-trace-deployment/report.json`, 89 archivos protegidos sin cambios, paquetes/cartel aceptados preservados. No aceptación visual ni fidelidad completa por compilar/desplegar.
- Siguiente: terminar calibración del nuevo runtime, inspeccionar sus cinco imágenes, ejecutar Gas-O BAG1/A vs Heat BAG2/A con fixture artificial `BAG2JP_TEST_GASO_ATTACK=1` y retorno al selector. El fixture envía entrada de ataque y desactiva esquiva/contraataque de P2; no fuerza reacción ni animación. Resolver petición 123/202 y duración observada antes de implementar CAUGHT/residencia/salida/parejas.

Calibración nueva `20261111T163349911319Z-gaso-clean-trace-calibration`: cinco imágenes inspeccionadas (P1 Heat → Comet → Heat → Strike → Heat; P2 Comet inmóvil), catálogo vinculado al runtime/hash/imágenes. Probe restauró tres ajustes y 43 saves; bridge restaura después las rutas externas originales. Partida `gaso-clean-tank-attack` lanzada en background con `--finish-timeout 420`; resultado aún pendiente.

### clean-trace-result-20261111 — diagnóstico, no aceptación del tanque

- Partida limpia `_work/versus-runs/20261111T163601126807Z-gaso-clean-tank-attack/`: runtime `6a5435966cd672f8cc5fc824b67bf37be35c2bd21442051c14fec6dcb25658d1`, Gas-O BAG1/A → Heat BAG2/A, escenario GasOBAG1. Fixture **artificial**: 70 entradas de ataque y una anulación de defensa registradas; sin escrituras de animación rival. Canción/flujo abandonó combate a 164.3 s y volvió al selector (`root13`), finish 170.1 s; ejecución completa 294.305 s. Lámina reducida e imágenes de retorno inspeccionadas. Capturas dispersas NO muestran un tanque activo ni prueban fidelidad del impacto; audio no capturado, fever no aceptado.
- `trace-analysis.json` conserva SHA de la traza, líneas/eventos/samples y episodios. P1 `110→74`: f7005/song695 y f7211/song901. P2 **`202→89`**: f7109/song799 (línea8358) y f7313/song1003 (línea8569). P1 **`123→78`**: desde f7415/song1105, línea8675; 98 filas conservan ese valor, NO equivalen a 98 llamadas. En este ensayo la petición123 corresponde al cansancio del atacante, no a la víctima del tanque. Esto resuelve el routing observado para Gas-O→Heat, no prueba rivales/parejas no ensayados ni todos los transitorios.
- P2 permanece en slot89 desde f7109 hasta f7529/song1219: **420 frames muestreados, con dos peticiones202**, NO duración de un único golpe. Desde la segunda petición observada hasta slot90:216 frames. Slot90 dura92 frames muestreados, vuelve a slot6 en f7621/song1311. No sustituir estos spans por un temporizador fijo ni equiparar song-frame BAG2 con el flag beat/bar BAG1. El seam previsto `a1==1 && a2==89` sigue necesitando comprobar contexto/compañeros antes de usarlo.
- Restauración verificada: Session protegió45 saves y tres ajustes; ambos bridges de probe/partida tienen `restored:true` y SHA de sus tarjetas históricas intacto. Comparación posterior independiente: **89 archivos protegidos previos al despliegue iguales**, incluidos ajustes, saves y paquetes/cartel GAS; settings original `b41a5fc8…` con sus rutas externas restauradas, ningún proceso BAG2JP activo. Instalación estable sin cambios.
- Verificación de código reutilizada sin cambios de entrada:33 tests específicos pasan; suite259 con los mismos32 fallos preexistentes (lista completa en `_work/gaso/caught-adapter-full-compare-trace-review-full.json`), no suite verde. Goldfish: dos revisores pidieron cambios, cuatro hallazgos confirmados corregidos y regresiones verificadas; `_work/goldfish/clean-trace-verdict.json`. **Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.** El despliegue diagnóstico estaba aprobado por separado; CAUGHT real aún NO integrado ni aceptado.
- Próximo paso acotado: NO repetir esta partida. Contrastar el temporizador original BAG1 (contador3/flag0x02) con la salida nativa BAG2 y el segundo impacto observado, sin inventar duración. Comprobar reserva8MB y exclusión de compañeros para el préstamo reversible de slot1 en005, IDs0/1/9, usando Ghidra MCP relevante antes de implementar la redirección YA aprobada. Fuente puntual: `_work/gaso/caught-seam-findings-20261111.md` y `_work/gaso/native-tank-rival-hit-timer-decompile/`; conservar salida90 y el contrato nativo. Fidelidad F2/F3 sigue abierta (partículas/audio/escala/caída/altura nativas); no usar HOLD65 ni otras constantes WIP como contrato.

## native-timing-contract-20261111 — F2 estático; tanque original aún NO integrado

Reanudación autorizada «okay, continua». No se repitió la partida limpia ni se modificó código de producción, runtime, paquetes o ajustes. Evidencia agrupada/hashes: `_work/gaso/native-timing-contract.json`.

- **BAG1 JP, reloj:** `8001f32c` genera flag02 cuando índice de secuencia %4==0, han transcurrido >4 frames desde el paso previo y umbral<=índice; umbral+=4. Son cuatro pasos de tabla con fase retardada, NO un número fijo de frames ni un compás musical ya demostrado.
- **BAG1 JP, captura:** ataque exitoso en `8001fc84` inicializa3. `8001ef9c` transfiere contador y char atacante al rival con flag10 en pulso02; cachea P2 para ataques simultáneos. Dispatcher llama transferencia antes de `8001f6a0` de ambos lados. El rival puede decrementar en ese mismo pulso; flags01/fase/esquiva condicionan el camino. No traducirlo a tres intervalos futuros completos.
- **BAG1 JP, salida visual:** `801d6480` estado2 espera contador rival<1, borra activo y restaura estado previo de uno/dos actores. Estado1 dispara1806 y comprueba flag80. `801d60c4` activa estado0 con pulso02 tras el retardo del evento. Sustituye como contrato los HOLD65/FADE15 del candidato aproximado, que siguen sin corregir en runtime.
- **BAG2 JP, acierto:** decompilación nueva/aislada de005 `80099e90`, líneas649–664/759–765/979–981: usa tabla80051458 por char atacante, escribe req202 para Gas-O y unidades3; duración=`T[barStart+4*units+3]-T[barStart+3]`, T=8005e2f0/barStart=8005e684. MIPS independiente: `8009b5b4 sh req,+18(s5)`, `b5f0 addiu v0,zero,3`, `c144 sw duración,+1c(s5)`. El main202→89 guarda índice2, resta dos veces longitud de salida90 y luego pasa a90. Ambas arquitecturas usan tablas/grupos de cuatro, pero el desfase y la equivalencia temporal nativa NO están probados; NO aceptar automáticamente el temporizador BAG2 como duración fiel.
- **Residencia:** `psx_mod_alloc_guest_memory` reserva Expansion1 (`9f000000+offset`), no mainRAM80400000. El binding actual exige span main80000000..80800000; adoptar Expansion1 requiere revisar decoder/accessors y cambiar contrato. Modelo8MB usa80200000/80300000,1MiB por lado; comentario/rangos de heap no prueban reserva80400000. Sigue candidato NO reservado; ninguna alternativa elegida aún.
- **Herramientas:** Ghidra MCP main y bytes contrastados; headless nativo/005 con contraste MIPS. Historial nuevo en `notes/tool-evidence/ghidra-psx-psyq.md`, `capstone.md`, `funcmatch.md`. Funcmatch JP→US devolvió0 con prefijo truncado200words: inconcluso, NO prueba ausencia. Scan de clears02 en main/005 no localizó equivalente y no se repite como prueba negativa.

**Siguiente acción exacta:** leer este apartado y `_work/gaso/native-timing-contract.json`; con Ghidra MCP primero, resolver alineación del índice/flag02 BAG1 con tabla BAG2 usando la generación de secuencia del escenario BAG1 y sus datos originales, no estimando con420/216 frames de la partida con dos impactos. Después demostrar residencia/exclusión de compañeros para préstamo slot1 de005 IDs0/1/9 antes de la redirección8002d06c YA aprobada. No implementar duración aproximada ni proclamar importación completa; F2/F3/port visual/audio/aceptación siguen pendientes.

## sequence-residency-contract-20261111 — datos nativos, fase y reserva; sin nuevo port desplegado

Evidencia/hashes: `_work/gaso/sequence-residency-contract.json`; datos completos en `sequence-chart-audit.json` y `sequence-phase-comparison.json` del mismo directorio. No se modificaron producción, paquetes, ajustes ni el ejecutable experimental; el tanque instalado sigue siendo el candidato aproximado.

- **Proveniencia real de la secuencia:** perfil `tools/bag1import/profiles/stages/gaso.json`, chart table JP8004d980 apunta a8004d804: inicio612/frames8204/pasos320. `port_bag1_stage.bag1_chart` añade32 pasos previos y convierte a inicio-208/frames9024/pasos352/intro32. Ambas variantes del entry197 del payload aceptado contienen exactamente esa salida. Payload fuente=instalado376287ab…; stage0a994860…/DBI174a8066…. No se ha regenerado ni cambiado.
- **Fase y diferencia concreta:** MIPS nativo230f4..2312c y nuevo Ghidra005800997ec generan `start+(frames*i+beats//2)//beats`. Alineación `j=i+32`: 265/321 entradas iguales y56 con destino un frame más tarde. BAG1 flag02 usa tabla[4k-1]+5; BAG2 impacto normal usa tabla[barStart+3]+5 con barStart=4k+28; apuntan a entradas correspondientes, pero la cuantización difiere. Comparación aritmética estática, NO replay de ambos juegos. No prueba duración idéntica ni justifica HOLD65, FADE15 o420/216 frames.
- **Corrección de seguridad:**80400000 NO es una reserva. El paquete expanded-ram declara explícitamente InitHeap de unos8MiB y stack alto. Que ningún modelo se vea allí no prueba propiedad. No escribir clips en esa dirección arbitraria.
- **Alternativa ya instalada, aún sin integrar:** SDK `psx_mod_alloc_guest_memory` reserva Expansion1(9f000000+), arena separada que las cargas guest normales pueden leer. Ghidra MCP main:8002ccc8→80012a94→800128b4→800126f8 conserva el puntero del clip/raw table+824; no se observó máscara a2MB/mainRAM en esos caminos de root motion/init/deltas. Prueba existente del framework `test_mod_memory_snapshot.c` compilada/ejecutada con sus flags CMake: ambas fases0,6.435s; verifica asignación, identidad/restauración de snapshots y rollback de arena. NO ejecuta el decoder CAUGHT del juego ni acredita ya la integración.
- **Contrato que debe cambiar antes del hook:** binding/adapter actual usa un solo buffer main80000000..80800000 y rechaza9f… correctamente. Siguiente seam: región de clip asignada y explícita, manteniendo guards de actores/tablas en mainRAM; no relajar rangos indiscriminadamente ni tocar heap global. Probar límites/alias/metadata/restauración y lectura real del decoder antes de publicar slot1. Exclusión de compañeros/retirada de préstamo sigue pendiente. La redirección8002d06c YA está aprobada; no pedirla de nuevo.

**Siguiente acción exacta:** leer este apartado y `_work/gaso/sequence-residency-contract.json`, verificar Ghidra MCP/estado Git; diseñar y probar RED→GREEN el acceso a clip en arena asignada, sustituyendo el supuesto80400000. Antes de integrar demostrar decoder real y quiescencia/exclusión de compañeros. Mantener la secuencia/paquete aceptado intactos; la desviación de un frame queda abierta para la fidelidad, no corregir música/escenario incidentalmente. No repetir la partida limpia ni estos headless/pruebas con inputs idénticos. Después portar estados/caída/escala/partículas/sonido originales; no anunciar tanque importado ni100%.


### owned-clip-host-contract-20261111
CAUGHT: añadido acceso explícito a una asignación inmutable Expansion1 `9f000000..9f100000`, sin ampliar límites main-RAM de actores/tablas. APIs legacy conservadas; adapter/runtime aún NO conectados. El llamador debe demostrar procedencia, vida útil, pausa/quiescencia y retiro real; los límites del búfer no lo prueban.
RED inicial: falta de API al compilar (no RED de comportamiento). GREEN final: 27 métodos reales C/WSL, `caught-loan-owned-clip-review-green.json`; mutaciones aisladas: baseline pasa y siete regresiones detectadas (incluye lectura fuera de clip detenida con página protegida). Suite completa: 267 métodos, 1 fallo/31 errores, mismos 32 nombres previos en `caught-adapter-full-compare-owned-clip-full.json`; NO suite verde.
Goldfish: dos revisores nuevos; hallazgos de cobertura confirmados y corregidos: longitud completa al restaurar + republicación, límites del aperture con metadata válida, alineación/fin relativo/tail protegido y layout alternativo. Evidencia `_work/goldfish/owned-clip-verdict.json`. Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
MCP confirmó decoder `800126f8`, `800128b4`, `80012a94` con punteros relativos sin máscara de RAM. Prueba del decoder original con bus/interpreter real: primer intento no compiló (extracción incluyó texto de comentario/prototipos ausentes); segundo no enlazó por mocks duplicados del bus real; tercero enlazó pero tuvo SIGSEGV. Intentos conservados; GDB no instalado, declaraciones implícitas verificadas sin error; cuarto no enlazó libm; quinto ASAN localizó un símbolo DATA autogenerado erróneamente como función antes de entrar al decoder. Sexto detuvo esa autogeneración; séptimo detuvo un observador parity no implementado. Se definieron DATA con tipos reales y tres observadores como en tests del framework. Octavo pasó; noveno añadió controles pero confundió el campo flags+4 con conteo+6 y falló; MCP126f8 confirmó el offset y décimo pasó con flags/conteo/frame y poses no vacías bajo ASAN. Los diez intentos conservan trial/log y fuentes previas; no se modificó el framework. Original MIPS `800126f8/80012850/800128b4` ejecutado con dirty_ram_interp/memory.c reales: CAUGHT70 Heat348B/Strike352B/Gas-O348B, secuencia 0/1/0/1, poses iguales desde main-RAM y asignación Expansion1, arena sin cambios. `_work/gaso/owned-decoder-probe10/trial.json` y `owned-decoder-result.txt`. Seam aislado con servicios opcionales desactivados; no es controlador vivo, rendering ni prueba de retiro. Sin build/deploy/juego/payload modificado. Próximo: plumbear adapter de región y demostrar retiro/exclusión de compañeros antes del hook aprobado. `80400000` sigue NO reservado.


### adapter-region-negatives-20261111
CAUGHT: añadido `B1CaughtClipRegion` en `bag2jp_caught_adapter.h` (NULL=legacy sin cambios) y helpers `b1ca_publish`/`b1ca_restore` que despachan a `b1cb_publish_in`/`b1cb_restore_in` cuando region!=NULL. Las 3 llamadas en `b1ca_apply` (ENTER publish, RESTORE restore, ABANDON restore) usan los helpers. `b1ca_owns_tuple` sigue solo-RAM-principal (retorna -1 seguro para owned). Nuevos negativos con region!=NULL: escenario 8 restore_not_quiescent_owned, escenario 9 restore_different_region_owned, escenario 10 tables_inside_owned_region; adapter escenario 14 owned_region_negatives (kind 0 quiescent=false, kind 1 región distinta, kind 2 YIELD+retiring y restore OK mismo region). GREEN: 26 tests enfocados, suite completa 272 tests con los mismos 32 fallos baseline previos y sin regresiones. Legacy inalterado. Goldfish: dos revisores (ses_e342ba3a7ffeimqSssl5Yrlq3s safety, ses_e342ba3a6ffeYCPlxtYcPmY0Po tests); hallazgos A1/A2/A3 (alias rango, no_references, identidad de región) confirmados y corregidos con negativos. Evidencia `_work/goldfish/owned-clip-adapter-region-verdict.json`. Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue. Build/deploy/juego/payload sin cambios; tanque instalado aún aproximado, fidelidad NO aceptada; 80400000 NO reservado.


### retire-and-partner-exclusion-20261111
CAUGHT: añadidos escenarios 15-16 en `caught_adapter_harness.c` y 2 tests en `test_caught_adapter.py` para demostrar retiro y exclusión de compañeros con región owned antes del hook `0x8002d06c` (ya aprobado). Escenario 15 (`retire_failure_owned`, kinds 0-3): RESTORE se rechaza cuando no hay quiescencia, VM no parada, slot1 aún `current` o slot1 aún `previous`; el binding se mantiene intacto y RAM no cambia; tras corregir el defecto, el mismo adapter retira y vuelve a IDLE. Escenario 16 (`partner_exclusion_owned`, kinds 0-1): compañero cuyas tablas aliasan el área owned bloquea ENTER (identidad no coincide); compañero con tablas propias y disjoint permite el borrow. GREEN: 34 tests totales (adapter 18 + owned_clip 10 + binding 6), suite completa sin regresiones (mismos 32 fallos baseline previos). Log `_work/gaso/caught-loan-adapter-retire-partner-full.log`. Build/deploy/juego/payload sin cambios; tanque instalado aún aproximado, fidelidad NO aceptada; 80400000 NO reservado. Próximo: verificación residencia 8MB, luego aceptación en juego.


### retire-partner-owned-mutations-20261111
CAUGHT: extendido el coverage del retiro con región owned tras revisión Goldfish de pruebas. Escenario 17 (`retire_owned_region_defect`, kinds 4-8): identidad de región cambiada, región data NULL, tablas del actor fuera de rango (0x9f100000), clip instalado debajo de la base de la región y clip que desborda la región — todos rechazan RESTORE con VM pausada y quiescente; el mismo adapter se recupera y retira tras deshacer el defecto. Escenario 16 kinds 2-3: compañero con tablas disjoint permite borrow completo ENTER→YIELD→RESTORE; tras retiro completo el mismo owner re-borrow con nuevo hit en el mismo adapter. GREEN: 35 tests enfocados (adapter 18 + owned_clip 10 + binding 6), 0 fallos. Suite completo (discover): 275 tests, 1 fallo + 31 errores = los mismos 32 baseline previos, sin regresiones (`caught-adapter-full-compare-adapter-retire-partner-full.json`, names=32 idénticos). Goldfish pruebas: mutaciones owned añadidas son válidas; sin defecto de código en adaptador (F1/F2 resueltos en fuente). Evidencia `_work/goldfish/owned-clip-adapter-retire-partner-verdict.json`. Build/deploy/juego/payload sin cambios; tanque instalado aún aproximado, fidelidad NO aceptada; 80400000 NO reservado. Próximo: verificación residencia 8MB, luego aceptación en juego.


### owned-clip-8mb-residence-source-20261111
CAUGHT: residencia de la arena owned con RAM 8MB verificada por lectura de fuente del build tree (`BAG2JP-codex-build/BAG2JP/psxrecomp`), NO por ejecución en juego.
- `mod_runtime.cpp:3552` `psx_mod_alloc_guest_memory(size, align)`: devuelve 0 dentro de host-output scope; si no, delega en `memory.c:113` `psx_mod_memory_alloc`: arena bump de `PSX_MOD_MEMORY_SIZE`=1MiB en `PSX_MOD_MEMORY_BASE`=`0x1F000000` (`mod_memory.h:23-24`), alineación potencia de 2 ≤4096, sin liberación, memset a 0, devuelve `0x9F000000+start`.
- `psx_memory.h:60` `psx_ram_map_read`: solo pliega con `g_psx_ram_mask` direcciones físicas `< 0x00800000`; `0x1F000000+` pasa sin cambios. Con 8MB activo la ventana main es `0..7FFFFF`; no hay solapamiento con Expansion1 ni con la apertura GPU-DMA (`0x00800000`).
- Lecturas guest: fast path `psx_cyc.h:287` solo para `phys < 0x00800000`; el resto va a `*_slow`/`psx_read_word_raw` (`memory.c:1746`), que sirve `mod_memory` antes del open bus (`1752`). Equivalente en half/byte (`2173`, `2299`) y escrituras (`2111`, `2245`, `2613`). Fuera de lo asignado, Expansion1 sigue siendo open bus (`FFFFFFFF`).
- Snapshot/save state: `psx_mod_memory_snapshot_*` incluye la arena; `psx_mod_memory_layout_cookie` depende de `mod_memory_used`, así que la asignación debe hacerse una sola vez, con tamaño fijo y en init del plugin; asignar a mitad de partida cambiaría el cookie (riesgo de compatibilidad de saves de estado).
- Ningún mod de `mods-src` llama hoy a `psx_mod_alloc_guest_memory` (grep), así que la arena de 1MiB está libre para este clip.
Límites: no prueba que el plugin sea "trusted" ni que el decoder CAUGHT lea la arena en juego; probe10 lo demostró solo en el intérprete host. Build/deploy/juego/payload sin cambios; fidelidad NO aceptada; 80400000 NO reservado. Próximo: integrar el hook `0x8002d06c` (aprobado) con asignación única en init, build+deploy EXE a `BAG2JP-exp-8mb` y aceptación en juego.

### caught-entry-recovery-20261111 — candidato inseguro aislado, no integración

Este bloque sustituye la instrucción anterior de pasar directamente al build.
La redirección sigue aprobada, pero el candidato posterior a aquella nota no
implementaba sus precondiciones. Se conservó íntegro antes de corregirlo en
`_work/gaso/caught-entry-recovery-backup/`: cuatro archivos con hashes verificados.

- Defectos constatados: callback `int` frente a ABI `void`; comparación de petición
  `202` donde llega slot traducido `89`; clip host cero marcado listo sin copiar
  bytes auténticos al invitado; buffer RAM parcial con límites insuficientes;
  publicación sin préstamo persistente ni restauración; reactivación incoherente.
  **El candidato no llegó a compilarse como runtime ni a desplegarse.**
- Corrección acotada: `bag2jp_gaso_caught.c` registra ahora un callback `void`
  deliberadamente inerte, sin acceso RAM, asignaciones ni cambios de registros.
  Feature `bag1-gaso-caught` desactivada por defecto y descrita como seam inactivo.
  Incluso habilitarla no publica slot1. Esto no implementa la reacción CAUGHT.
- RED: `_work/gaso/caught-loan-entry-recovery-red.log` demuestra ABI incompatible
  y default incorrecto (4.982 s). GREEN: `entry-recovery-focused` verifica 38 tests
  en 23.812 s: callback real + adaptador/binding/región owned. Compilación WSL GCC
  `-std=c11 -Wall -Wextra -Werror` con headers reales del framework; dependencia
  externa del build tree, no test autónomo en otro checkout.
- El harness comprueba la CPU completa y cero accesos/asignaciones en 120 entradas
  por matriz y tres repeticiones adicionales. No hay callbacks de reset/activación
  registrados: esas repeticiones **no prueban** lifecycle real ni savestates.
- Suite completa: 278 tests, 1 fallo y 31 errores; los mismos 32 nombres de la
  baseline, comprobados en `caught-adapter-full-compare-entry-recovery-full.json`.
  No es una suite verde. Logs completos en `_work/gaso/caught-loan-entry-recovery-*`.
  El primer combinado usó por error `test_owned_clip` (módulo inexistente);
  se corrigió a `test_caught_owned_clip`. El primer comparador eligió un log
  enfocado sin fallos; se rechazó y se reutilizó el comparador canónico correcto.
- Staging: las dos copias `.c` del build tree se sustituyeron solo tras comprobar
  su hash anterior `31fdefde…`; ambas coinciden ahora con la canónica
  `17ceb85d5691195b3aa4cd064a55362ebf42fd99cc870ec4d7bfb10267f5c6a6`.
  Evidencia/hashes completos: `_work/gaso/caught-entry-recovery-report.json`.
  No se reejecutó codegen ni se cambió el hook generado ya verificado.
- Manifiestos del build **no sincronizados en este paso**: el paquete preloaded
  conserva payload aceptado `376287ab…`, sin nueva feature; la copia histórica en
  `src/mods-src/...` tiene pins antiguos `c030b287…`/`4062840b…`. No sobrescribir
  esta divergencia sin respaldo y verificación de qué copia consume el build.
- Ghidra MCP confirmó main JP y bytes de entrada frente al raw; el decompile de
  esa dirección no existe en la sesión GUI. Ensayo y límite registrados en
  `notes/tool-evidence/ghidra-psx-psyq.md`, `caught-entry-recovery-mcp-20261111`.
- Goldfish: dos revisores nuevos, `SIN HALLAZGOS BLOQUEANTES` para **cuarentena**,
  no para redirección. Hashes en el reporte anterior; resúmenes y triaje en
  `_work/goldfish/gaso-caught-entry-recovery-verdict.json`. Confirmaron los límites
  de lifecycle y respaldo; el respaldo/staging se verificó después independientemente.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.

Sin build de runtime, despliegue, nueva partida ni aceptación de fidelidad.
Payload/escenario aceptados, instalación estable, configuración y saves intactos.
**Siguiente:** conservar esta cuarentena mientras se implementa y prueba el
contrato de redirección `modo=1/slot89 → slot1` sobre el adaptador persistente:
identidad principal/atacante/versión, bytes auténticos por rival en guest,
acceso RAM 8MB acotado y exclusión de compañeros, retiro quiescente y
reset/savestate. Resolver equivalencia temporal nativa sin inventar duración;
solo después staging reproducible de fuentes/manifiestos, build, deploy
experimental y aceptación en juego. `80400000` sigue sin reserva.

### caught-entry-contract-20261111 — composición host verificada, runtime aún inerte

Objetivo acotado aprobado: publicar slot1 antes de redirigir el argumento
`modo1/slot89→1`, usando el adaptador persistente, sin escribir `+0x18` ni
reiniciar frames. **No es integración ni aceptación del tanque dentro del juego.**

- Nuevo `bag2jp_caught_entry.h`: compone la política/binding existentes, solo
  desde IDLE sin binding. Valida actor principal de su lado y Gas-O principal
  contrario con lecturas acotadas. Rechaza compañeros, slots/peticiones/versiones
  incompatibles y hechos insuficientes. Procedencia request202, versiones,
  generación, autenticidad/residencia y propiedad de pausa siguen siendo hechos
  que deberá demostrar el llamador del runtime, no datos inferidos del slot89.
- Solo después de publicar correctamente los diez bytes de la tupla, cambia
  `entry.slot=1`; conserva el mismo adaptador para replay/reintento/retirada.
  Header experimental **no incluido** por el callback runtime. Clip/backing y
  buffers deben seguir vivos y sin alias hasta retirar el préstamo.
- RED real con stub que rechazaba todo: 4 tests, 13 subcasos esperados fallaron
  en `redirect()`; sin errores de compilación. Primer GREEN enfocado: 42 tests,
  33.145 s, WSL GCC `-std=c11 -Wall -Wextra -Werror`. Logs
  `_work/gaso/caught-loan-entry-contract-{red,green}.log`.
- La versión final tiene cinco tests nuevos / 60 ejecuciones C sintéticas:
  tres rivales, ambos lados, actores por encima de 4 MiB, diez bytes escritos
  como máximo y comparación del resto de los 8 MiB; entradas negativas sin
  efectos; préstamo persistente, entrega repetida, retirada y nuevo attack_id.
  No se ejecuta el controlador MIPS ni se usan clips auténticos en este fixture.
- Suite final `entry-contract-review-final`: 283 tests, 1 fallo y 31 errores,
  79.131 s. Los cinco tests nuevos pasan. Comparador confirma los mismos 32
  nombres de fallo/error de baseline; **la suite completa no está verde**.
  Reporte `_work/gaso/caught-adapter-full-compare-entry-contract-review-final.json`.
  La primera suite, anterior al hallazgo de revisión, tuvo 282 tests y los
  mismos 32 nombres; se conserva, no sustituye la re-verificación final.
- Preflight pasó en 0.336 s; identidad/entrada Ghidra MCP contrastadas con raw,
  sin inferir semántica nueva: ensayo `caught-entry-contract-mcp-20261111` en
  `notes/tool-evidence/ghidra-psx-psyq.md`. Hashes, comandos/evidencia y límites
  en `_work/gaso/caught-entry-contract-report.json`.
- Goldfish: dos revisores nuevos, uno `SIN HALLAZGOS BLOQUEANTES`, otro
  `CON HALLAZGOS` por cobertura negativa de retirada insuficiente. Confirmado
  leyendo guards y escenario; corregido con seis casos: pausa falsa y referencias
  reales current/previous/decoder/poseA/poseB pese a `view.references=0`.
  Verifican descriptor, RAM, argumento y backing intactos al rechazar, y reintento
  correcto al liberar la referencia. Re-verificados en la suite final, sin cambiar
  producción tras revisión. Registro `_work/goldfish/caught-entry-contract-verdict.json`.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Hash producción revisada `851b00b38dd6e18a51d6606f6ae954e12751667a3c664fe00b31dc3168f5902f`;
  hashes finales de harness/test y previos a revisión en el reporte. Sigue intacto
  el callback inerte `17ceb85d…` y la feature default off. No se hizo staging al
  build, codegen, build runtime, deploy ni partida. Payloads, saves, ajustes e
  instalaciones no se tocaron. Dependencias adapter/binding conservan cambios
  anteriores aún pendientes; no confundir checkpoint WIP con checkout autocontenido.
- Checkpoint local `2726fe4` (`WIP: verify stopped-RAM CAUGHT entry composition`):
  solo los tres archivos nuevos de esta unidad. Los cambios previos de headers,
  notas y otros temas se conservaron fuera del commit. Sin push ni snapshot de
  milestone: es trabajo intermedio experimental, no resultado aceptado.

**Siguiente:** reutilizar este contrato y sus tests; no repetir cuarentena ni
inventarios. Cargar los clips auténticos por rival desde la evidencia ya existente
y demostrar copia/residencia guest por asignación única; construir observaciones
del runtime (main/companion, atacante/versión/procedencia/generación), cerrar
ABANDON owned y retiro/reset/savestate real, y resolver equivalencia temporal.
Después wiring del callback y tests de integración, manifiestos reproducibles
con respaldo, Goldfish del cambio runtime, build/deploy experimental y aceptación
de CAUGHT/retorno a selección. Fidelidad original del tanque/audio/tamaño/caída
sigue pendiente. No habilitar un fixture sintético ni reservar `80400000`.

### caught-clip-bank-20261111 — bytes auténticos y residencia host, sin wiring runtime

- Unidad acotada: banco compartido `bag2jp_caught_bank.{h,c}` y datos generados
  desde los DFS originales fijados por `tools/bag1import/contracts/caught-bank.json`.
  Miembro 1, slot 70; Heat 348 B, Strike 352 B, Gas-O 348 B; offsets 0/348/700,
  total 1048 B. Hashes de fuentes/clips coinciden con la auditoría existente;
  reproducción exacta de bytes, incluidos los dos ceros nativos de padding.
  Solo versión BAG1 e IDs 0/1/9, no soporte para esqueletos BAG2-only.
- `build_caught_bank.py --check` confirma `.inc` determinista con SHA
  `238afcd54625091017bb47e2f9913d68c5bba803fa8aa3b8fb1999d1e86bee79`.
  Intentos iniciales de generación fallaron por miembro 0 y por asumir ausencia
  de padding; contrastados con extractor previo y offsets originales, corregidos
  sin transformar los clips. No son evidencia RED de comportamiento.
- Una tentativa de asignación fija/alineada por descriptor cero inicializado;
  fallo inicial terminal. Verifica todo el banco guest antes de exponer un clip;
  prepare repetido/lookup nunca reasignan ni reparan/escriben memoria. Corrupción
  rechaza salida sin modificarla; snapshot coincidente puede recuperar validez.
  Pausa, procedencia, scope API y vida del descriptor/backing son precondiciones
  del llamador; no resetear/copiar el descriptor para conseguir otra asignación.
- Harness usa allocator, backing y snapshot **reales** de `memory.c`; sustituye
  solo APIs de título. No prueba bus CPU completo, mod-manager ni savestate/reset
  completo. 14 escenarios C y dos tests de fuente. Error de compilación inicial
  por warnings existentes del framework conservado en `clip-bank-red`; se acotó
  su supresión al include existente, manteniendo `-Werror` en todo código nuevo.
  Luego stub RED: 5 tests, 14 fallos esperados; GREEN inicial: 5 pasan, 7.854 s.
- Suite final `clip-bank-review-final`: 290 tests, siete nuevos pasan; 1 fallo y
  31 errores, 72.126 s. Comparador confirma los mismos 32 nombres previos:
  `_work/gaso/caught-adapter-full-compare-clip-bank-review-final.json`.
  **Suite completa no verde**. Reporte con hashes/comandos/límites:
  `_work/gaso/caught-clip-bank-report.json`. Primera suite de 290 preservada.
- Goldfish: dos revisores nuevos `SIN HALLAZGOS BLOQUEANTES`. Observación menor
  confirmada: el negativo de hash invocaba helper y no flujo completo. Cambiado
  a `extract_clips` con fuente alterada/contrato temporal; bypass del hash solo
  en memoria dispara el fallo esperado. Producción sin cambios tras revisión;
  suite final re-verifica el test. Respuestas y triage:
  `_work/goldfish/caught-clip-bank-verdict.json`.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Preflight pasó en 0.307 s. MCP confirmó main JP y entrada decoder `800128b4`,
  32 bytes iguales a raw; ensayo `caught-clip-bank-mcp-20261111` en log Ghidra.
  No implica semántica o timing nuevos. Callback inerte SHA `17ceb85d…` y feature
  default off intactos; banco no staged/enlazado. Sin build, deploy, partida,
  payloads, saves o ajustes modificados. Fidelidad CAUGHT/tanque no aceptada.

- Checkpoint local `bf01979` (`WIP: verify authentic CAUGHT clip bank residency`):
  solo siete archivos nuevos de esta unidad; cambios previos y notas conservados
  fuera del commit. Sin push ni snapshot de milestone; es protección intermedia,
  no permiso de despliegue ni aceptación.

**Siguiente:** reutilizar banco y composición host. Construir observaciones reales
con identidad main/companion, atacante/versión/procedencia de request y generación;
cerrar ABANDON owned y ciclo de retiro/reset/savestate, y equivalencia temporal.
Solo después wiring/tests de integración, manifiestos con respaldo, Goldfish
runtime, build/deploy experimental y aceptación en juego. No repetir extracción,
inventario o cuarentena mientras hashes no cambien; `80400000` no está reservado.

### caught-dispatch-context-20261111 — ABI y procedencia parcial, sin wiring runtime

- Investigación acotada del dispatcher original `8002a090` y del consumidor de
  `system/005.dbi`. **Corrección importante para el futuro wiring:** `a0` de
  `8002d06c` es un controlador; el actor está en `word[a0]`. El `actor` de la
  composición host anterior es una identidad ya resuelta, no ese registro CPU.
  Controlador main `8005f820 + side*98h`, companion a `+4ch`; lista main en
  `8005f808 + side*8`. No se ha cambiado el callback con esta información.
- Probe scratch ejecuta bytes originales mediante `dirty_ram_interp.c` real,
  con RAM sintética y callees observados. Dispatcher `8002a090..8002b5bc`:
  60 casos (IDs 0/1/9/5/6, ambos lados, requests 200..204 y salida por timer).
  Captura 84 llamadas a `8002d06c`: 60 main con RA `8002ae68`, 12 companion con
  RA `8002afe4`, 12 con RA `8002b06c`. IDs 10/14 y otras rutas no ejercitados.
- Traducción observada: requests 200/201/202/203/204 a slots 85/87/89/91/71;
  al expirar timer con current 89 se solicita salida 90. Duración sintética 216,
  length[90]=36: timer inicial 144, salida con timer cero. **No demuestra**
  equivalencia temporal BAG1, reproducción del clip ni comportamiento en partida.
- Segundo span, separado para no anidar el intérprete: consumidor original
  `8009d06c..8009d0c8`, ambos lados. Diez casos 200..204 llaman al dispatcher con
  main controller, modo 1, request original, `a3=4096` y quinto argumento 216;
  dos negativos sin pending no lo llaman. Registros de setup del loop los aporta
  el fixture; el loop entero no se ejecuta. Pending global sigue disponible al
  retorno `8009d0c8`: `half[8005cf08 + side*24h +18h]`. Su limpieza nativa está
  después de la llamada (`8009d0d4`), según contraste estático. No escribir ese
  campo para forzar CAUGHT; no es el `+18h` del actor/controlador.
- En la entrada al controller, el dispatcher conserva su RA exterior en
  `word[sp+d4h]`. La combinación RA main `8002ae68`, RA exterior `8009d0c8`,
  controlador/lista main y pending 202 permite plantear un filtro conservador.
  Es **hipótesis de integración**, no prueba de que el atacante sea Gas-O ni de
  exclusión de reflejos. La RA exterior fue suministrada en el fixture dispatcher;
  el span consumidor confirmó por separado el callsite, no ejecución anidada.
  `bag2jp_bag1_get_version` solo no basta: no comprueba active/force-stock;
  contrastar también disponibilidad efectiva (`bag2jp_bag1_has_version`).
- Evidencia: `_work/gaso/caught-dispatch-context-report.json`, con hashes de main,
  overlay, intérprete y fixture. `probe3` pasó 72 spans y 94 llamadas observadas
  en 3.557 s; transcript y fuente conservados en `dispatch-context-probe3/`.
  `probe1` abortó por expectativa errónea RA companion `AFD8`; el JAL original en
  `AFDC` prueba `AFE4`. Corregida la expectativa, `probe2` pasó 60 spans/84 llamadas
  en 3.384 s. Fallo, fuente fallida y transcript inicial conservados; no fue un
  bug runtime ni evidencia RED de una implementación. Derivador inicial guardado
  y protegido contra sobrescribir el fixture final; comando en project-config.
- Preflight pasó en 0.330 s, métricas en
  `_work/workflow/20261111T222223696011Z-gaso-caught-live-contract/metrics.json`.
  MCP confirmó main JP y tres lecturas coincidentes con raw; ensayo
  `caught-dispatch-context-mcp-20261111` en el log Ghidra. No nuevos cambios de
  producción: no se repitió la suite host (290 tests/32 nombres previos es evidencia
  **histórica**), ni Goldfish: solo scratch, nota, log y estado; no se tocó archivo
  de código/configuración sujeto a esa revisión. No hay veredicto nuevo de código.
- Callback inerte SHA `17ceb85d…`, feature default off y banco sin wiring intactos.
  Sin build, staging, deploy, partida, payload, saves ni ajustes modificados.
  CAUGHT y fidelidad del tanque siguen pendientes de aceptación.

**Siguiente:** usar el ABI confirmado para construir un lector de observaciones
con tests positivos/negativos del main controller, RA/pila/pending, módulo y límites
RAM. Resolver procedencia efectiva de Gas-O/versión y reflejos sin darla por probada
por request 202; conservar generación/identidad. Cerrar ABANDON owned y retiro,
reset/savestate y equivalencia temporal antes de wiring/activación; luego tests de
integración, manifiestos con respaldo, Goldfish, build/deploy experimental y partida.
Reutilizar estos spans y banco auténtico mientras hashes no cambien.

### caught-context-reader-20261111 — lector host, no autorización del impacto

- Nuevos `bag2jp_caught_context.{h,c}`: lector **solo host**, no incluido por el
  callback ni enlazado al runtime. Recibe RAM coherente detenida y cinco registros
  abstractos (controller, mode, slot, sp, ra); resuelve `actor=word[controller]`,
  main/lista/lados y oponente. La salida es contexto, no `B1CaughtAttackFacts`.
  Éxito con oponente Heat también es deliberado: request 202 no identifica Gas-O.
- Filtro conservador: controller main fijo por lado, modo 1/slot 89, RA principal
  `8002ae68`, RA exterior `word[sp+d4h]=8009d0c8`, pending global 202, base de
  overlay `word[80010ce0]=8008f890` y cinco palabras originales en los dos
  callsites. Las huellas son **parciales**, no autenticación del módulo completo
  ni prueba de generación/procedencia. La pila completa `d8h` y ambos actores
  `155ch` deben caber en el buffer, con tope 8MiB; suma de pila sin wrap.
- Rechazo sin modificar salida; ninguna escritura en RAM/CPU. Precondiciones:
  snapshot detenido/coherente, longitud real correcta y salida sin alias con
  entradas. No son garantías de pausa real, versión efectiva, reflejos ni vida de
  la carga; tampoco valida tablas, clips o exclusividad del préstamo.
- Fixture C carga código de main/005 con hashes originales fijados en el runner;
  actores, pila, pending y puntero de módulo son sintéticos. 81 escenarios:
  16 válidos (ambos lados, actores bajos/por encima de 2MiB, dos personajes por
  rol), 14 negativos de argumentos/RA/pila, 44 de identidad/pending/huellas y
  siete null/límites. La ampliación de revisión añade 30 casos, total **111**:
  pending `01cah` en ambos lados y 28 límites aislados de actor/oponente/pila.
  Compara toda la RAM, registros de entrada y salida en rechazo.
- RED: stub compilable, cuatro tests/16 fallos esperados en positivos, 18.491 s;
  `_work/gaso/caught-loan-context-reader-red.{json,log}`. GREEN específico: 19
  tests incluyendo entry/banco/callback inerte, 27.058 s, `context-reader-green`.
  No se confunden estos tests sintéticos con entrada CAUGHT en partida.
- Goldfish: dos revisores frescos pidieron cambios de cobertura, sin identificar
  defecto funcional bajo las precondiciones. Se confirmaron y corrigieron: el
  actor inválido antes discrepaba también de la lista, faltaban límites inclusivos
  y pending con byte bajo 202. Ahora controlador/lista concuerdan al probar actor
  inválido, hay éxito al último bloque completo y rechazo truncado, con pila baja
  válida para aislar los actores; la pila también se prueba en su extremo exacto.
  Cinco métodos del lector pasan después de la ampliación (20.256 s).
  Dos mutantes temporales (sin rango de actor / pending leído a un byte) producen
  seis fallos de aserción exigidos en ambos lados. No se modificó lógica productiva
  tras revisión, solo claridad del contrato y pruebas. Veredicto/triage:
  `_work/goldfish/caught-context-reader-verdict.json`; mutantes:
  `_work/gaso/caught-context-reader-mutations.json`.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Suite final del lector: 295 tests, un fallo y 31 errores (90.605 s), mismos
  32 nombres del baseline; **suite no verde**. Los cinco métodos nuevos pasan.
  Logs `caught-loan-context-reader-review-full.{json,log}` y comparación
  `_work/gaso/caught-adapter-full-compare-context-reader-review-full.json`.
- Preflight pasó en 0.344 s: métricas
  `_work/workflow/20261111T225531101561Z-gaso-caught-context-reader/metrics.json`.
  MCP y contraste raw en ensayo `caught-context-reader-mcp-20261111` del log
  Ghidra; reporte `_work/gaso/caught-context-reader-report.json`.
- Checkpoint local WIP `28aaeee`: solo los cuatro archivos nuevos del lector y
  pruebas. No incluye ni revierte cambios previos; no push ni snapshot de hito
  aceptado. El checkpoint no autoriza despliegue ni acredita funcionalidad CAUGHT.
- Callback inerte SHA `17ceb85d…` y feature default off verificados sin cambios.
  No wiring, staging, build, deploy, payload, partida, saves ni ajustes alterados.
  CAUGHT y fidelidad del tanque siguen sin aceptación.

**Siguiente:** reutilizar este lector y los spans anteriores, no reconstruirlos.
Trazar los productores de request 202 en el overlay original para distinguir
impacto directo Gas-O de reflejos y otros atacantes, comprobar versión efectiva
(`has_version` más selección real, no solo `get_version`) y vincular identidad de
carga/generación. Luego cerrar ABANDON owned y retiro/reset/savestate/timing antes
de conectar callback/banco/composición y probar el juego experimental.

### caught-hit-provenance-20261111 — origen y reflejo, sin captura runtime

**Objetivo:** contrastar el productor original de request 202; esta petición y un
oponente Gas-O no bastan para atribuirle el ataque. Investigación, no wiring.

- Fuentes originales fijadas: main raw SHA `143b4bf8…` y overlay JP `005.dbi`
  SHA `bc5f3045…`, los mismos del ensayo de contexto. Probe scratch
  `_work/gaso/probe_hit_provenance.c`, intérprete productivo y hashes completos
  en `_work/gaso/caught-hit-provenance-report.json`. No se reemplazaron bytes.
- Inicialización original `8009abf4..8009acd0`: el flag local del receptor es
  1 cuando la trayectoria procede del otro lado y el contador es impar, o 2
  cuando procede del propio lado con contador par. El selector `8009b3a8..b7f0`
  usa `s2 = s4 ^ 1` para flag 1 y `s2 = s4` para flag 2; `s4` es receptor.
  No se deduce origen del rival que esté seleccionado en pantalla.
- Defensa original `8009b454..b508`, ejecutada aparte en ambos lados: cambia
  activo 1→2 y contador 1→2; pending del defensor es 172. Al ejecutar después
  la inicialización, el receptor siguiente es el atacante original con flag 2.
  La inicialización de ataque con activo/contador 1 en `8009b8fc/b908` se
  contrastó estáticamente, no se ejecutó ese camino completo de inicio.
- Al acertar, `8009b588` guarda el carácter de origen en estado del receptor
  `8005e728 + side*32h + 2fh`; `8009b5b4` publica la petición de su tabla.
  El selector borra activo del origen (`8009b52c`) y contador (`8009b7c8`)
  antes del consumidor. Por tanto no se puede reconstruir la dirección con
  una lectura tardía de esos dos campos.
- Resultado final: **124 casos de selector, dos comparaciones espejo y dos
  defensas**, sin fallo de aserción. Ambas posiciones; receptores Heat/Strike/
  Gas-O; oponentes representados por IDs 0/1/9/8/10, sin validar sus assets;
  contadores 1/3 directos y 2/4 de retorno. Ocho casos dejan `202` con Gas-O
  enfrente pero origen Heat o Strike. No deben activar CAUGHT de Gas-O.
- Gas-O contra Gas-O: los campos de identidad coinciden entre directo y
  retorno. La comparación del fixture solo excluye 256 B de stack local del
  productor y 8 B de puntuaciones; el retorno transfiere 200 puntos más.
  **No son estados completos idénticos ni prueba de imposibilidad universal**;
  sí refutan atribuir origen solo con carácter/pending y campos borrados.
- Primer ensayo `probe1`: 120 casos pasaron en 3.734 s. `probe2` falló por una
  expectativa excesiva de igualdad de toda RAM; `probe3` conservó ese fallo y
  diagnosticó diferencias únicamente en puntuaciones fuera del stack. Se
  corrigió la expectativa, no el juego: `probe4` pasó (3.918 s). Final `probe5`
  pasó en 4.000 s con las defensas añadidas. Fuentes, logs de trial y transcritos
  fallidos/pasados retenidos por directorio; no constituyen RED→GREEN productivo.
- Límites: juicios/aciertos sintéticos; sonido observado sin ejecutarlo y RNG
  fijo en cero; no combate, animador/decoder ni versión efectiva/generación de
  carga. Los spans separados no equivalen a ejecutar una partida completa.
- MCP Ghidra main JP y tabla de 36 B contrastados con raw: ensayo
  `caught-hit-provenance-mcp-20261111` del log de herramienta. Preflight pasó
  en 0.319 s, métricas
  `_work/workflow/20261111T231944374679Z-gaso-caught-hit-provenance/metrics.json`.
  Goldfish omitido justificadamente: solo scratch/evidencia, notas/estado y
  referencia de comandos; ningún archivo productivo de sus rutas disparadoras.
  Suite de 295 tests/32 fallos-errores anteriores es histórica, no repetida.
- Callback SHA `17ceb85d…` inerte y feature default off verificados sin cambios.
  No staging, build, deploy, payload, partida, saves, settings ni aceptación.

**Siguiente:** reutilizar estos spans y resolver una captura acotada del origen
antes de su borrado. Candidato: instrucción original `8009b5b4 = a6a20018`,
con origen `s2`, receptor `s4` y bloque pending `s5`; observarla no debe escribir
pending ni forzar poses. El registro tendría que validar actores, versión
efectiva, módulo/generación, consumo único y retiro/reset/savestate antes de
autorizar `89→1`. No está implementado. El guard host antiguo «oponente Gas-O»
de `b1ce_main_rivals` tampoco cubre el retorno genuino de un ataque Gas-O al
propio Gas-O: adaptar el contrato solo con origen acreditado, sin congelar
reflejos de ataques ajenos. No excluir permanentemente el caso espejo ni
inferir autorización de los snapshots. Después cerrar ABANDON owned y timing,
integración, Goldfish y aceptación experimental ya aprobados.

### handoff-20261112 — entrada limpia y hallazgo P0 del binario desplegado

Punto de entrada para una sesión nueva: `HANDOFF.md` (raíz). Resume objetivo,
estado por capas, contrato nativo confirmado, medidas de partida, comandos,
pendientes y prohibiciones. Esta sección conserva el hecho nuevo que motiva el
P0; el resto del ledger sigue siendo histórico y no se reescribe.

- **Implementado hasta 2026-11-11 (WIP, sin aceptación):** `bag2jp_caught_source.{h,c}`
  (captura/consumo host verificado con probe3: 124 llamadas, 100 aceptadas),
  `bag2jp_caught_context.{h,c}` (lector de 111 escenarios, no enlazado),
  `bag2jp_caught_entry.h` (composición host, no incluida por el runtime),
  `bag2jp_gaso_caught.c` (callback de entrada `0x8002d06c` + plugin de
  instrucción `0x8009b5b4`), y ampliación de `bag2jp_caught_adapter.h` con
  `b1ca_reset/save_state/load_state/state_size` (128 B).
- **Hallazgo P0 (2026-11-12, lectura de fuente + cadenas del ejecutable):** el
  binario desplegado en `BAG2JP-exp-8mb` (SHA `BDAF4B82…`, 25 442 304 B) contiene
  `bag2jp.gaso_caught` y `bag2jp.gaso_caught_capture`. El registro de plugins no
  consulta la feature ni el manifest, y `captured[]` nunca se limpia: en cuanto
  una publicación de la petición 202 pasa las validaciones (Heat, Strike o Gas-O,
  tabla `0x80051458`), el callback escribe `gpr[6]=1` en **todas** las entradas
  posteriores a `0x8002d06c`. No hay clip auténtico publicado, así que no puede
  afirmarse que sea inocuo. El estado «inerte/default-off» solo vale con
  `captured[]` vacío, que es lo único que cubren los 3 tests de
  `test_gaso_caught_runtime`.
- **Divergencia de staging constatada:** el build compiló
  `BAG2JP-codex-build/BAG2JP/src/bag2jp_gaso_caught.c` (SHA `B605A188…`, captura
  con literales); la copia canónica `mods-src/...` (SHA `A1CFEBEA…`, 8629 B) ya
  tiene las constantes con nombre y no estaba staged (preflight la listó en
  `sources.different`). La copia `src/mods-src/...` es el stub inerte obsoleto de
  1085 B (`17CEB85D…`) y no se compila. El manifest desplegado es el aceptado
  (`F76698BE…`, sin la feature), no el canónico (`6EAB9377…`, con
  `bag1-gaso-caught` `default_enabled=false`).
- **Tests y baseline:** `test_caught_adapter` 25/25, `test_caught_source` +
  `test_caught_context` 10/10, `test_gaso_caught_runtime` 3/3,
  `test_caught_integration` 4/4 (48 escenarios). Suite completa 306 tests,
  1 fallo + 32 errores: los mismos nombres de baseline previos, no una suite
  verde.
- **Siguiente:** neutralizar el P0 (no escribir `a2` salvo captura autenticada
  como Gas-O y consumida una vez, o desplegar el stub inerte), re-staging
  canónico, `preflight`/`build`/deploy con hash y solo después partida de
  diagnóstico. No se jugó con este binario: no hay aceptación nueva.

### caught-p0-inert-20261112 — P0 neutralizado, despliegue con hash

Evidencia fresca de esta sesión; lo anterior de este ledger es histórico.

- **Ghidra MCP:** `get_program_info` = `SLPM_862.19` (sha256 `ea5a1668…`, 1324
  funciones). `read_memory 0x8002d06c` = prólogo `addiu sp,sp,-0x40`; sin función
  definida en Ghidra y 0 xrefs (entrada indirecta).
- **Corrección de la premisa P0:** el runtime fijado (`1a3fc0db303a`) solo activa
  hooks de función/instrucción de ids en `plan.plugins`
  (`mod_packages.cpp:4150-4183`, `mod_runtime.cpp:368-394`); el plan incluye un
  plugin solo si su feature del manifest está habilitada. El manifest desplegado
  `F76698BE…` no declara `bag1-gaso-caught`, así que `BDAF4B82…` era inerte en la
  práctica. Además el canónico solo declara `bag2jp.gaso_caught` (no
  `bag2jp.gaso_caught_capture`) y `0x8009b5b4` no está en ningún
  `[recompiler] mod_instruction_sites`: la captura no puede dispararse aunque se
  active. El defecto de código era real y latente.
- **Cambio (`mods-src/bag2jp.feature.bag1-content/bag2jp_gaso_caught.c`, SHA
  `9989264B…`):** `GASO_CAUGHT_CLIP_PUBLISHED 0` (sin escritura de `a2` en
  runtime); cada publicación invalida primero el registro del receptor; solo se
  guarda origen Gas-O (char 9) BAG1 (`has_version`/`get_version` del lado),
  directo (no reflejado); la entrada exige modo 1, slot 89 y actor principal del
  receptor y consume el registro haya o no cambio de `a2`.
- **Tests host:** `test_gaso_caught_runtime` compila el harness con publicación
  0 y 1. RED contra la copia obsoleta del build tree (`B605A188…`): 5 fallos
  (Heat/Strike redirigen). GREEN canónico 6/6; conjunto caught 52 OK. Suite
  completa 309 tests, 1 fallo + 32 errores = mismos nombres de baseline (incluye
  el error preexistente de compilación de `test_caught_entry` por
  `bag2jp_caught_adapter.h` modificado); no es suite verde.
- **Goldfish (2026-11-12, hash revisado `9989264B…`, 2 revisores fríos):**
  veredicto CON HALLAZGOS, ninguno bloqueante para P0 inerte.
  Aplicados: filas Heat/Strike con `versions[GASO][lado]=1` para ejercitar el
  control de carácter; sonda no consumidora `recorded()` que distingue captura
  guardada/rechazada también con publicación 0; 6 variantes de rechazo que deben
  invalidar el registro. Mutantes `no_char_check` (4 fallos) y `late_supersede`
  (2 fallos) detectados. Refutado: `bag2jp_caught_source.h:4` (consumo en
  desajuste) no aplica, el runtime no usa `b1cs_take`. Límites (P3): registro
  obsoleto tras fin de ronda/reset/savestate (sin plugin de reset,
  `generation=1` fijo); `get_version` informa selección, no contenido cargado
  (`versions.c:174-177`). Veredicto de revisor: no es aprobación del propietario
  ni permiso de despliegue.
- **Build y despliegue:** re-stage solo de `bag2jp_gaso_caught.c` (copia previa en
  `_work/gaso/p0-backup/bag2jp_gaso_caught.B605A188.c`); `bag2jp_bag1_versions.c`
  queda con drift deliberado. `preflight`/`build --tag gaso-caught-p0-inert` OK
  (`_work/workflow/20261112T024923593725Z-gaso-caught-p0-inert/`). Exe
  `68E3AB2E…` (25 442 304 B) desplegado en `BAG2JP-exp-8mb`, hash igual; copia
  previa `BAG2JP.exe.bak-BDAF4B82-pre-p0`. Manifest desplegado sin cambios
  (`F76698BE…`). `BAG2JP-win` intacto. **No se jugó:** sin evidencia en juego ni
  aceptación.
- **Siguiente:** partida de diagnóstico opcional; P1 banco de clips; activar solo
  tras declarar los ids de ambos plugins en el manifest, `0x8009b5b4` en
  `mod_instruction_sites` y P3 resuelto.

### caught-p1-bank-20261112 - banco de clips enlazado (solo host)

Evidencia fresca de esta sesión; no se usó Ghidra (cambio solo host/runtime de
mods, sin parche MIPS).

- **Cambio:** `bag2jp_gaso_caught.c` (SHA `2020CF47…`) registra
  `psx_mod_register_activation_plugin("bag2jp.gaso_caught", …)`; la activación
  llama `b1cc_prepare()` sobre un `B1CaughtBank` estático de vida de proceso y
  solo cuenta `gaso_caught.bank_ready`/`bank_unavailable`. Una asignación de
  1048 B en Expansion 1, copia verificada por relectura, sin reintento ni
  reparación. Entrada/captura sin cambios (`GASO_CAUGHT_CLIP_PUBLISHED 0`); nada
  consulta el banco todavía. Comentarios de cabecera de `bag2jp_caught_bank.{h,c}`
  actualizados.
- **Hechos del runtime (`1a3fc0db303a`):** la activación corre solo para
  features habilitadas (`mod_runtime.cpp:3161`), antes de `memory_init`, que no
  limpia la arena de mods (`memory.c:1207-1237`); la arena es un bump allocator
  de vida de proceso incluido en el snapshot; el cookie de layout depende de
  `mod_memory_used` (`memory.c:64,88`).
- **Tests host:** RED contra la fuente P0: 6 fallos (escenarios 1/4/5 sin
  activación). GREEN `test_gaso_caught_runtime` 9/9 (escenarios 0–6 × publicación
  0/1): copia única auténtica tras 3 reactivaciones con arena previa de `0x34` B;
  fallo de asignación terminal sin escrituras; corrupción informada y no
  reparada; banco preparado y hooks sin escrituras ni asignaciones. Con
  `test_caught_bank`: 16/16 (los fallos de copia los cubre solo esta suite
  compañera). Conjunto caught 54 OK. Suite completa 311 tests, 1 fallo + 32
  errores con el mismo conjunto de nombres que P0 (`_work/p1-full-suite.log`);
  no es suite verde. `build_caught_bank.py --check`: 1048 B, `238afcd5…`.
- **Goldfish (2026-11-12, 2 revisores fríos, runtime y tests):** CON HALLAZGOS,
  ninguno bloqueante. Aplicados: staging de los archivos del banco y línea CMake
  (sin ellos el enlace fallaba); comentarios obsoletos del banco; escenario 6
  (hooks de solo lectura con banco preparado); arena previa no vacía; código
  muerto de reset en el harness. Mutantes `p1_entry_writes_bank` (detectado
  solo por el escenario 6) y `p1_bank_fixed_base` (escenarios 1/5/6) detectados.
  Documentados: activar la feature cambia el cookie de savestate (savestates con
  feature apagada se rechazan encendida y viceversa); un primer fallo de copia
  deja el banco no disponible todo el proceso aunque un savestate restaure los
  bytes; lockstep `g_ls_mode==2` en la relectura es solo diagnóstico. Veredicto
  de revisor: no es aprobación del propietario ni permiso de despliegue.
- **Build y despliegue:** copiados al `src/` del build tree `bag2jp_gaso_caught.c`,
  `bag2jp_caught_bank.c` (`6C3225FF…`), `.h` (`FD9D107E…`) y `_data.inc`
  (`238AFCD5…`), hash iguales; `CMakeLists.txt` del build tree L78 añade
  `src/bag2jp_caught_bank.c` (copias previas en `_work/gaso/p1-backup/`). El
  repo canónico no versiona ese cableado CMake: hueco previo, no resuelto aquí.
  `preflight`/`build --tag gaso-caught-p1-bank` OK
  (`_work/workflow/20261112T032006955485Z-gaso-caught-p1-bank/`). Exe
  `01C9BD93…` (25 444 352 B) desplegado en `BAG2JP-exp-8mb`, hash igual; copia
  previa `BAG2JP.exe.bak-68E3AB2E-pre-p1`. Manifest desplegado sin cambios
  (`F76698BE…`, sin la feature): la activación no corre en la instalación.
  `BAG2JP-win` intacto. **No se jugó.**
- **Pendiente P1 en juego (requiere activar la feature):** decoder lee las poses
  correctas y arena intacta tras reset/savestate.
- **Siguiente:** P2 (autorización/consumo y `b1cc_lookup` por rival en la
  entrada); requisitos de activación de la sección anterior siguen vigentes.

### caught-observe-20261112 - captura y consumo observados, clip sin publicar

- **Checkpoint local:** `ab5480e` (WIP): runtime, harness, driver y bloque CAUGHT
  del manifest. Los cambios previos de hashes del payload quedan fuera del commit.
  No implica aceptación de fidelidad ni publicación del clip.
- **Alcance autorizado:** activar `bag1-gaso-caught` solo en exp-8mb para
  diagnóstico. `GASO_CAUGHT_CLIP_PUBLISHED=0`: no publicar slot 1, no cambiar
  `a2`, no escribir pending `+0x18` ni `0x80400000`, ni regenerar payload.
- **Cambio:** manifest default-off con ambos ids `bag2jp.gaso_caught` y
  `bag2jp.gaso_caught_capture`; activación local explícita en `mods/state.toml`.
  Contadores host y trazas `b1v_log` para banco, captura/rechazo y consumo.
  Punteros actor/pila limitados a RAM viva mediante `memory_get_ram_bytes()`
  (2/8 MiB); pila también admite scratchpad. El primer filtro fijo de 2 MiB
  rechazó dos impactos en la partida `20261112T035643119438Z-gaso-caught-observe-diag`.
  La corrección conserva el rechazo de spans fuera de límite y registra `sp`.
- **Evidencia fresca:** build/preflight pasados en
  `_work/workflow/20261112T041805621128Z-gaso-caught-observe-stack/` (build 33.661 s).
  Exe build/deploy SHA `97DE924AB300572373834E7CC66B93B46DE425CB797E585E9AF36E93420652B4`;
  backup experimental `BAG2JP.exe.bak-AE55F0C2-pre-stack`. `versions.c` no se
  restageó: drift deliberado de otra tarea. Instalación estable sin cambios.
- **Partida fresca:** `_work/versus-runs/20261112T042121831233Z-gaso-caught-observe-diag2/`,
  Gas-O BAG1 A P1 vs Heat BAG2 A P2, GasOBAG1, fixture de ataque explícita (no
  juego natural). Banco listo `9f000000`; dos publicaciones
  `request 202 s2=0 -> s4=1 sp=807fff28 stored`, cada una seguida de
  `entry taken by side 2 actor 801a8104, a2 unchanged`. Fin de canción y retorno
  observados (finish 170.0 s, salida de batalla 163.8 s). Revisión visual acotada
  en `visual-review.json` y `diagnostic-compact.png`: selección, combate y retorno;
  las capturas finales ya muestran selector, no poses CAUGHT. Runner conserva
  `complete_awaiting_visual_review`; decisión separada, sin atribuirle otra aceptación.
- **Calibración:** `20261112T041920241316Z-gaso-stack-calibration`, ocho aristas
  revisadas y aceptadas para el hash nuevo. Se usó el bridge reversible
  `_work/gaso/run_clean_trace_session.py`; runner directo rechazaba las rutas
  históricas de memcards. Restauración final verificada: settings `B41A5FC8`,
  keybinds `EAAF722E`, state `2DDB7306`; tarjetas originales preservadas.
- **Tests:** regresión RED contra fuente previa en build tree en ambas variantes
  de publicación; GREEN runtime+banco 19/19. Escenario 8 cubre pila alta en 8 MiB,
  último span válido, desborde de un byte, límite 8 MiB y rechazo en retail.
  `_work/gaso/observe-stack-{red,green,full-suite}.log`: suite completa 315 tests,
  1 fallo + 32 errores, mismos nombres que `_work/p1-full-suite.log`; no es verde
  (preservación de entradas Heat, KeyErrors de assets y compilación caught_entry
  afectados por trabajo previo). No se corrigieron fallos ajenos a este alcance.
- **Goldfish:** observe `ses_e322d4667ffeT7Kh20eTnVgsmG` y logging
  `ses_e3220e4a9ffeT5sklla5EUdNu7`: CON HALLAZGOS, ninguno bloqueante. Aplicados
  rangos de lectura, test de ids, no-evento en dirección ajena, atributo printf,
  motivos de rechazo comprobados, registros crudos y texto condicionado al macro.
  Corrección de geometría: spec `_work/goldfish/spec-gaso-caught-stack.md`, revisores
  `ses_e3206b48fffeQKnq5MvQR1GMRI` y `ses_e3206b488ffeC0HMY0XkxIrn2W`, ambos
  SIN HALLAZGOS BLOQUEANTES; enlace real y diagnóstico corroboran su conclusión.
  Límites no bloqueantes: fixture scratchpad no cubre bordes, helper solo recibe
  spans constantes 6/50 B; no generalizar su aritmética sin nueva prueba.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- **Corrección a notas históricas:** se confirmó el hook de productor vía
  intérprete dirty-RAM sin `mod_instruction_sites`; esa lista es requisito para
  emisiones nativas AOT, no para esta ejecución. Build con debug tools OFF:
  el canal verificado es `bag2jp_bag1_versions.log`, no TCP `mod_counters`.
  Ghidra MCP identificó main JP `ea5a1668…` y leyó entrada `8002d06c`; registro en
  `notes/tool-evidence/ghidra-psx-psyq.md`. No se reanalizó overlay ni MIPS.
- **No aceptado aún:** decoder/binding de clip, reset/savestate, equivalencia
  temporal, fever y fidelidad visual/audio. `captured[]` y contadores son host-only,
  no se guardan/restauran: tras load pueden describir otra línea temporal.
  Activar cambia el cookie por +1048 B de arena; estados off/on incompatibles.
  Fallo inicial de copia sigue terminal. Sin prueba fresca de savestates.
- **Siguiente:** P2 `b1cc_lookup` por rival, binding y procedencia/generación;
  conectar lifecycle P3 antes de publicar. No repetir esta captura sin cambiar
  inputs/código/hipótesis. Checkpoint experimental no equivale a aceptación CAUGHT.
### caught-p2-research-20261112 - selección por receptor, sin publicación

- Investigación posterior a `ab5480e`; el ejecutable experimental sigue siendo
  `97DE924A`, sin cambios de runtime ni nuevas partidas. Preflight pasó
  (0,82 s), reporte `_work/gaso/p2-preflight.json`.
- `bag2jp_caught_bank.c:36-45` exige versión BAG1 y solo encuentra personajes
  0/1/9. `test_caught_bank.py` ya prueba los bytes originales (348/352/348), la
  selección y el rechazo de BAG2/sin descriptor sin cambiar salida ni guest.
  Es evidencia existente reutilizada, no una ejecución nueva. La versión del
  atacante no debe usarse para seleccionar el clip del receptor: Heat BAG2 del
  diagnóstico anterior debe quedar no soportado, no recibir un clip Heat BAG1.
- Runtime actual: `generation=1/tick=0` sigue siendo provisional; captura y
  consumo observe-only no autentican lifetime, identidad de tablas ni decoder.
  Los helpers host de binding/adapter y sus cambios previos no equivalen a
  integración runtime; no se tocaron ni se corrigieron fallos ajenos.
- Contrato leído del framework: `mod_plugins.h:36-47` distingue limpieza host de
  sesión y callback posterior a carga. `mod_runtime.cpp:2769-2800` recorre plugins
  del plan tras restaurar; no guarda automáticamente sus estructuras host.
  No se ha demostrado un evento de generación por carga de actor ni quiescencia.
- Desglose propuesto al final de `plans/gaso-attack-effect.md`: aprobar solamente
  P2a (lookup diagnóstico por personaje/versión del receptor, RED→GREEN, sin
  publicación); después investigar identidad/generación y lifecycle P2b/P3.
  F8 contra 19 rivales no se reduce a los tres perfiles del banco.
- Ghidra MCP reutilizado para identidad y lectura acotada de entrada del
  controlador; registro `caught-p2-research-mcp-20261112` en su log. No se repitió
  el probe de partida ni se invocaron herramientas irrelevantes.
- Goldfish no requerido en esta entrega: solo plan, nota, registro de herramienta
  y estado; ningún cambio a código, manifest, payload o rutas protegidas.
- Siguiente: obtener aprobación de P2a. Hasta entonces conservar
  `GASO_CAUGHT_CLIP_PUBLISHED=0`, no cambiar `a2` ni tablas, sin build/despliegue.

### caught-p2a-lookup-20261112 - consulta diagnóstica por receptor, sin publicar

- Aprobación del propietario («Continua») al desglose P2a; alcance solo
  diagnóstico. `GASO_CAUGHT_CLIP_PUBLISHED=0` sin cambios, sin publicar slot 1,
  sin escribir pending `+0x18` ni tablas. P2b/P3 siguen sin contrato demostrado.
- Implementación en `bag2jp_gaso_caught.c`: tras consumir el registro, consulta
  `b1cc_lookup(&bank, personaje_capturado, versión_del_lado_receptor, &clip)`.
  La versión se lee en la entrada con `bag2jp_bag1_has_version`/`get_version`
  (guarda `personaje < 18`), nunca la elección BAG1 del atacante. Contadores
  `gaso_caught.lookup_ready|lookup_rejected` y una sola línea de log con
  personaje, versión, resultado, clip y bytes. Descriptor local a cero: un
  rechazo registra `clip=00000000 bytes=0` aunque la API no limpie salidas
  previas. Comentario de `bag2jp_caught_bank.h` corregido (ya no dice que nadie
  lo consulta).
- Host RED→GREEN: `_work/gaso/p2a-red.log` falla por el lookup ausente en ambas
  variantes; `_work/gaso/p2a-green.log` y `p2a-green2.log` dejan 20/20 en
  `test_gaso_caught_runtime` + `test_caught_bank`. Escenario 9 usa el banco real,
  ambos lados, perfiles Heat/Strike/Gas-O BAG1, cambio de versión del receptor
  entre captura y entrada en ambos sentidos, y rechazos por personaje no
  admitido, capacidad ausente y banco corrupto sin asignaciones ni escrituras
  guest nuevas. Suite completa `_work/gaso/p2a-full-suite.log`: 316 tests,
  1 fallo/32 errores, nombres idénticos al baseline `observe-stack-full-suite.log`.
- Goldfish (dos revisores fríos, spec `_work/goldfish/spec-gaso-caught-p2a.md`):
  ambos `SIN HALLAZGOS BLOQUEANTES`. Sugerencias menores aplicadas: comentario
  del header y comprobación de cambio de versión entre captura y entrada. No es
  aprobación del propietario ni permiso de despliegue.
- Ghidra MCP `caught-p2a-mcp-20261112`: identidad `SLPM_862.19` JP y lectura de
  `0x8002d06c` igual al registro previo; sin escrituras. Prueba redundante exigida
  por el flujo, no lifetime ni selección.
- Build `_work/workflow/20261112T050545068145Z-gaso-caught-lookup-observe/`
  (preflight/build pasados). Exe `A9296DDBF5A9DE268C297D52F19E7654D95F73C71DD6FED42D9FB58B203D4F57`
  desplegado solo en exp-8mb; backup `BAG2JP.exe.bak-97DE924A-pre-lookup`.
- Calibración `_work/versus-runs/20261112T050755645568Z-gaso-p2a-calibration`:
  ocho aristas y selector revisados y aceptados para el hash nuevo.
- Partida positiva `20261112T051100576135Z-gaso-p2a-lookup-heat-bag1`
  (Gas-O BAG1 P1 vs Heat BAG1 P2): banco `9f000000`; dos
  `request 202 s2=0 -> s4=1 stored` y dos tomas con
  `a2 unchanged; lookup char=0 version=1 ready clip=9f000000 bytes=348`. Una
  tercera petición reflejada rechazada. Fin 150,5 s, salida 144,3 s, retorno
  root 13. Secuencia visual revisada (versus, selección, combate, fin, selector).
- Partida negativa `20261112T051605884720Z-gaso-p2a-lookup-heat-bag2`
  (Gas-O BAG1 P1 vs Heat BAG2 P2): dos tomas con
  `a2 unchanged; lookup char=0 version=0 rejected clip=00000000 bytes=0`; el
  atacante BAG1 no autoriza un receptor BAG2. Fin 170,0 s, salida 161,0 s,
  retorno root 13; secuencia visual revisada.
- Restauración viva comprobada tras ambas partidas: `settings.toml` `B41A5FC8`,
  `keybinds.ini` `EAAF722E`, `mods/state.toml` `2DDB7306`; sin proceso BAG2JP.
- Límites: el `lookup ready` acredita disponibilidad e integridad del banco, no
  generación ni identidad de tablas del actor; `captured[].clock` sigue
  provisional. Sin publicar el clip, sin aceptación de la animación CAUGHT ni de
  los 19 rivales (F8). Siguiente: investigar P2b (identidad/generación de carga)
  antes de cualquier escritura; no repetir estas partidas sin cambios.


### caught-p2b-generation-20261112 - generación por carga, sin escritura

- P2b se ejecutó como investigación estática (owner: «continua con lo que
  recomiendas»). `GASO_CAUGHT_CLIP_PUBLISHED` permanece en 0; no hubo build,
  despliegue ni partida. Solo lecturas Ghidra MCP y documentación.
- Programa verificado: `SLPM_862.19`, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`,
  base `0x80000000`, entrada `0x80035d98` (JP, PSX LE32). Registro de la
  prueba en `notes/tool-evidence/ghidra-psx-psyq.md` (`caught-p2b-generation-20261112`).
- `0x8009b5b4` (productor `sh v0,0x18(s5)`) y `0x8002d06c` (entrada del
  controlador) no están definidos como funciones en el ejecutable principal
  (FUNCTION_NOT_FOUND). El productor pertenece al overlay 005 (más allá del fin
  de texto `0x8005D000`); Ghidra principal no puede decompilarlo. El anclaje
  P2b se hace sobre las estructuras de controlador/actor.
- `0x8005f808` es un puntero al actor del lado 0; `0x8005f80c/10/14` los
  demás lados; `0x8005f818/1c` sus acompañantes (`+0x1728`). 26 referencias a
  `0x8005f808`, incluyendo `FUN_8001e0f4` (READ en `0x8001e420`) y
  `FUN_80034210` (WRITE en `0x80034230`). `0x8005f820` (controlador lado 0)
  solo aparece como PARAM en `0x8001e418` de `FUN_8001e0f4`.
- Máquina de fases `DAT_8005d3dc` (0/1/2/3), conducida por `FUN_8001e0f4`:
  - fase 0 → 1: prepara selección, asigna `DAT_80089248=&0x800ddb18`,
    `DAT_8008924c=&0x80154db4`, `DAT_8008923c=&0x8009ef40`,
    `DAT_80089240=personaje`; llama `FUN_800342dc(0)`; pasa a 2.
  - fase 2: espera a que `FUN_800342dc(1)` devuelva 0; entonces pasa a 3.
  - fase 3: reinicializa las cuatro parejas controlador/actor
    (`FUN_8002b5bc(&0x8005f820, DAT_8005f808)` y análogos), llama
    `FUN_800997ec(*DAT_80089200)`, `FUN_800995e0()`, `FUN_8009769c()`,
    pone `DAT_8005d3d8=1`, `DAT_8005d3e0=0`, `DAT_8005d298=0`,
    `DAT_8005d3dc=0`, `DAT_8005d29c=0`.
  - `FUN_8001e744` (inicio de combate) resetea `DAT_8005d3dc=0` y otros
    globales; el arranque (`main` en `0x8001e938`) deja `DAT_8005d3dc=0`
    (limpieza de bss). Es decir, el ciclo 0→1→2→3→0 ocurre por entrada de
    combate, no solo al arrancar.
- `FUN_8002b5bc(controlador, actor)`:
  - si `actor == NULL` o `actor+4 == -1`, pone `*controlador = 0` y sale
    (lado inactivo);
  - en caso contrario calcula posición/escala y llama `FUN_8002d85c`.
- `FUN_8002d85c` reinicializa el controlador en cada pareja: `*controlador =
  actor`; `+4=0x1000`, `+6=0x400`, `+8=0x100`, `+0x14=0x8000000`,
  **`+0x18=-1`**, `+3=1`, `+0xd=0`, `+0x10=0`; copia coordenadas y escala
  desde `DAT_80051a70[personaje]`; escribe campos del actor
  (`+0x810/+0x814/+0x818`, `+0x1524/+0x1528/+0x152c`, `+0x14b8/+0x14bc/
  +0x14c0`, `+0x14e4/+0x14e8/+0x14ec`, `+0x1514/+0x1518/+0x151c`,
  `+0x14f4..+0x1510`, `+0x1548=0`, `+0x154c=0`, `+0x1554=0`) y calcula
  `+0x1534/+0x1538/+0x153c`.
- `FUN_80034210()` (estado 0xb del cargador, lado ausente): asigna
  `DAT_8005f808 = DAT_80089248` (búfer fijo `&0x800ddb18`), pone
  `actor+4=0xff`, `DAT_8005f818 = base+0x1728`; la otra rama usa
  `0x80154db4/+0x1728`. Limpia `DAT_8005f808[7]`, `DAT_8005f810[7]` y los
  acompañantes `+7`. Los búferes de actor son RAM estática fija, no asignada
  dinámicamente.
- `FUN_800342dc(int)` es el cargador/estado gráfico (casos 0..0xe de
  `0x80089215`); en el caso 0xb llama `FUN_80034210` si falta un lado y luego
  `FUN_80033c10`, avanzando a 0xc/0xd/0xe. Devuelve 0 cuando ambos lados
  faltan o `DAT_80089234>3`.

Conclusiones P2b (sin escrituras ni publicación):

1. No existe contador explícito de generación en el ejecutable principal. El
   ciclo de fases `DAT_8005d3dc` (0→1→2→3→0) es el evento de recarga por
   combate: la fase 3 es el único punto donde se reinicializan las parejas
   controlador/actor y se pone `+0x18=-1`.
2. La identidad del actor (`DAT_8005f808/0c/10/14`) no sirve como generación:
   los búferes son fijos (`0x800ddb18` y `0x80154db4`, más acompañantes
   `+0x1728`), por lo que la igualdad de punteros se repite entre combates.
3. El personaje de cada lado se fija en fase 1 (`DAT_80089240`,
   `DAT_8005e666`) y se mantiene hasta el siguiente ciclo; `actor+4` guarda el
   personaje o `0xff` (lado ausente). Una captura previa queda obsoleta cuando
   la fase 3 vuelve a ejecutarse o cuando `+0x18` se reinicia a `-1`.
4. La regla de invalidación para `captured[]` debe basarse en el ciclo de fases
   (reinicio de `+0x18` a `-1` / fase 3), no en la identidad del puntero ni en
   `generation=1/tick=0`, que siguen siendo provisionales.
5. Esto no autoriza publicar: sigue faltando probar serialización, quiescencia,
   reset de sesión y decoder (P3), y el guard de publicación/restore.
6. Siguiente recomendado: P3 (ciclo de vida: `session_reset`, savestate/restore,
   invalidación), manteniendo `GASO_CAUGHT_CLIP_PUBLISHED=0` y sin tocar
   `a2` ni tablas guest.

Evidencia host previa reutilizada: P2a (20/20 host, suite sin nombres nuevos,
dos Goldfish sin hallazgos bloqueantes, Heat BAG1 `ready` / Heat BAG2
`rejected` en juego) y P0/P1. No se repitieron pruebas host ni partidas.

### caught-p3-lifecycle-20261112 - ciclo de vida, sin publicacion

- P3 completado como investigacion de implementacion (no hay partida, sin escribir
  guest, sin publicar). Se anadieron los callbacks de ciclo de vida del plugin
  `bag2jp.gaso_caught` en `mods-src/bag2jp.feature.bag1-content/bag2jp_gaso_caught.c`:
  - `gaso_caught_session_reset()`: se ejecuta antes de cada activacion de plan
    (emulacion detenida, contexto host-only, nunca muta estado guest). Pone
    `captured[].available = 0` en ambos lados para invalidad cualquier registro
    obsoleto de la partida anterior.
  - `gaso_caught_savestate()`: se ejecuta despues de la restauracion de estado
    guest y antes de que el PC se reanude (rebindear hooks, no avanzar juego).
    Igualmente pone `captured[].available = 0` para que una captura previa a la
    carga no sobreviva al load: los buffers de actor son RAM fija y
    `controller+0x18` se resetea a -1 en el setup de fase 3, asi que una captura
    previa ya no coincide con ningun actor vivo.
  - Ambos se registran en `PSX_MOD_CONSTRUCTOR` junto al plugin de activacion,
    `function_entry` e `instruction` ya existentes. No hay escrituras guest, no
    hay asignaciones, no hay publicacion. `GASO_CAUGHT_CLIP_PUBLISHED` sigue en 0.
- Prueba host: escenario 10 de `gaso_caught_runtime_harness.c` verifica que
  session_reset y savestate invalidan `captured[]` sin escrituras guest ni
  asignaciones, y que `enter()` no consume tras invalidar. 21/21 pruebas host OK
  (incluyendo P2a).
- Contrato P3 documentado: los registros de captura sobreviven solo dentro de
  un ciclo de partida (fase 3 de `DAT_8005d3dc` reinicializa parejas y pone
  `+0x18=-1`). Siguiente: estudio de publica/restore quiescente con guard y
  aprobacion del propietario, manteniendo CLIP_PUBLISHED=0.

### caught-retire-contract-20261112 - publicación/retiro por contrato (host), sin partida

- Corrige abb8320: el restore por temporizador escribía sin comprobar que el clip
  hubiera salido de slot1, y el redirect a2=1 ocurría aunque la publicación no se
  hubiera hecho (slot1 vacío, longitud 0 usada como divisor).
- Ghidra MCP (`SLPM_862.19`, sha256 `ea5a1668…851efe`; reabierto en esta sesión).
  `0x8002d06c` no es función definida: bytes con `read_memory`, iguales a
  `_work/mainexe/slpm.bin`, desensamblados con capstone en
  `_work/gaso/fun_8002d06c.asm` (sha256 `b4dddc256d22bcf7…`, script `dis_8002d06c.py`):
  - `0x8002d4b8 sw t0,0x154c(s0)` (bytes `4c 15 08 ae`): current = a2 dentro de la
    misma llamada de entrada.
  - `0x8002d6cc sw v0,0x1550(s0)` (bytes `50 15 02 ae`): previous = current al salir.
  - `divu` por `length[current]` en cada tick (`0x8002d644`, `0x8002d684`) y al
    abandonar el slot (`0x8002d494`).
  - Conclusión: restaurar solo es seguro con current≠1 y previous≠1; «estuvo en
    slot1» se observa en la llamada siguiente.
- Código (`bag2jp_gaso_caught.c`, sha256 `a9a0100ffffe4192…`, fuente sigue en `CLIP_PUBLISHED 0`):
  - la toma ejecuta `b1cb_publish_in` del contrato validado sobre una copia host
    dispersa (lista de actores, actores listados, sus 3 tablas ≤ 0x1000 entradas,
    palabra vacía) y replica sus 3 escrituras (palabra raw, media longitud, meta);
  - a2=1 solo si slot1 tiene este clip para este actor; una segunda toma con el
    clip aún publicado lo reutiliza y reinicia la espera;
  - cada llamada de entrada revisa primero el retiro: marca «entered» si
    current/previous==1; restaura por `b1cb_restore_in` cuando ya entró y ambos
    salieron, o tras 60 llamadas si nunca entró; un restore rechazado (p. ej.
    decoder `+0x830` dentro del clip) se registra una vez y se reintenta cada 8 llamadas;
  - logs: `slot1 published … a2 -> 1`, `slot1 publish refused … (contract|unreadable)`,
    `slot1 entered`, `slot1 restore refused … retrying`,
    `slot1 restored … (clip left slot1|clip never started)`.
  - Límite conocido: reset/savestate olvidan una tupla publicada sin restaurarla;
    una publicación posterior sobre esas tablas falla cerrada (probado en host).
- Pruebas host: `py -3.13 -m unittest tools.test.test_gaso_caught_runtime
  tools.test.test_caught_bank` → 23 OK (harness `8189998e3dcb1550…`, test
  `25e998dbb661571e…`), builds 0 y 1. El harness simula tablas por actor, solo
  admite escrituras en la entrada slot1 de una tabla listada y comprueba la tupla.
  Escenario 12 reescrito: entrada/salida en dos pasos, restore rechazado por
  decoder con reintento acotado, nunca iniciado (59/60), reutilización, otro clip
  y 3 publicaciones rechazadas.
- Mutaciones (`_work/gaso/mutate_caught.py`): 7/7 detectadas (ignorar previous,
  redirect sin publicación, sin freno de reintento, 59 llamadas, reutilización sin
  reiniciar espera, reutilizar otro clip, restaurar sin haber entrado).
- Suite CAUGHT completa (13 módulos, 106 pruebas): todo OK salvo `setUpClass` de
  `test_caught_entry`, preexistente y ajeno: `caught_entry_harness.c` (2726fe4)
  necesita el `bag2jp_caught_adapter.h` sin commitear, cuyas funciones nuevas
  `b1ca_reset`/`b1ca_load_state` no usa (`-Werror=unused-function`); con el header
  de HEAD tampoco compila (falta `region`). El plugin Gas-O no incluye ese header.
- Sin validar: comportamiento en juego (pendiente partida grabada con build
  `CLIP_PUBLISHED=1` solo en el árbol de build).
- **Revisión Goldfish** (spec `_work/goldfish/spec-gaso-caught-retire.md`, estado
  revisado: plugin `a9a0100f…`, harness `8189998e…`; 2 revisores en frío):
  ambos **CON HALLAZGOS**. Triaje:
  - Confirmado y bloqueante (A-P1 = B-B1): la reutilización de un clip publicado
    ponía a2=1 sin releer la RAM; si el juego reescribe/mueve las tablas sin reset,
    redirigía a un slot1 con longitud 0 (división en `0x8002d494`). Reproducido en
    host (RED: harness línea 980, «lost» no detectado). Corregido:
    - el retiro comprueba primero, con 12 lecturas, identidad (char/side),
      COUNT/RAW/LENGTH/META y la tupla `(clip, 2, info)`; si cambió, registra
      `slot1 lost side=N … (rewritten by the game)`, olvida y no escribe;
    - la reutilización exige además el contrato en modo verify (`b1cb_plan` +
      `b1cb_tuple`, sin escrituras); si falla, `slot1 reuse refused … (contract)`.
  - Confirmado (A-P4/B-S1): copia byte a byte y reintento sin tope. Corregido:
    copia por palabras alineadas (≈¼ de lecturas trazadas) y abandono sin escribir
    tras `GASO_CAUGHT_RESTORE_TRIES 32` rechazos (`slot1 restore abandoned`);
    la tupla abandonada apunta al banco nunca liberado con longitud 2.
  - Confirmado (A-P5/B-N1): `word[a0]` sin `guest_range_ok`. Corregido.
  - Confirmado (A-P2, A-P6/B): el harness no mutaba RAM con el clip publicado y
    no comprobaba el lado. Añadidos casos: reescritura antes/después de entrar,
    antes de la toma, solo longitud, solo meta, tablas movidas, palabra vacía
    alterada (verify), abandono tras 32×8 llamadas; `enter()` exige
    `slot1_holds_clip` y slot1 vacío en el otro lado.
  - Refutado (A-P3/B-N2, stride de la lista de actores): volcado real
    `_work/versus-runs/20261110T043326680373Z-gaso-sign-subdivision-v2-verify/sign-intro-24-ram.bin`
    (`_work/gaso/actor_list_probe.py`): `8005f808`=Gas-O (char 9, side 0, n=101),
    `8005f810`=Heat (char 0, side 1, n=101), `8005f80c`/`8005f814`=0; coincide con
    el harness y el contrato.
  - S2 (otros lectores de las tablas): capstone sobre `_work/mainexe/slpm.bin`
    (`143b4bf866bf6e47…`, `_work/gaso/scan_slot_users.py`, salida
    `slot_users.txt`) da 130 accesos a `0x820/824/828/82c/154c/1550`, agrupados
    con Ghidra (`get_function_by_address`). Fuera del controlador todos indexan
    las tablas por `current`; el único lector extra de `previous`
    (`FUN_8002bc38`, `0x8002bc74`) solo lo compara con `current`
    (`bne a2,v0`). Refutado para lecturas directas. Límite abierto: punteros del
    clip guardados fuera de `0x830/0x1494/0x1498`, y tablas copiadas al
    acompañante por `800326d4` (`8005f818/1c` no están en la lista de 4 que
    verifica la exclusividad; en el volcado citado el acompañante tiene n=0).
  - S3 (savestate de otro proceso con otro banco): no verificable en host;
    límite declarado.
  - Equivalente: el mutante «reutilizar otro clip» sobrevive tras el cambio, porque
    la consulta va por (personaje, versión) y la comprobación de identidad olvida
    una publicación cuyo personaje cambió; se retiró con su razón en el runner.
- Tras las correcciones: plugin `53a09f47badf99be…`, harness `76d45c68a12beebc…`;
  `test_gaso_caught_runtime` + `test_caught_bank` → 23 OK (builds 0 y 1);
  mutaciones 11/11 detectadas (`mutate_caught.py` `8cf30907…`: ignorar previous,
  redirect sin publicación, sin freno, 59 llamadas, reutilización sin reiniciar
  espera, restaurar sin entrar, reutilizar sin verify, sin detección de pérdida,
  pérdida sin meta, sin tope de reintentos, verify que escribe).
- Build experimental (`CLIP_PUBLISHED 1` solo en `BAG2JP-codex-build/src`;
  `bag2jp_bag1_versions.c` canónico no copiado a propósito): `bag2_workflow.py
  build --tag gaso-caught-retire2`, exe `EA0C7F16AF3D16A42437B10F6D559FDEF92988EC0DAB6979D3BDF0449F99F86D`,
  desplegado solo en exp-8mb (backup `BAG2JP.exe.bak-A9296DDB-pre-retire`;
  ajustes en `_work/gaso/exp-backup-pre-retire/`). Calibración
  `20261112T155020408170Z-gaso-retire2-calibration` con
  `_work/gaso/run_clean_trace_session.py` (puente reversible de tarjetas; la
  llamada directa a `versus_session.py` falla porque `settings.toml` apunta a
  tarjetas de `gaso-fix5`): ocho aristas revisadas y aceptadas;
  `settings.toml` restaurado a `B41A5FC8`.

### caught-active-reuse-20261112 - segundo golpe activo, candidato sin aceptación

- Ensayo `20261112T155241389733Z-gaso-retire-heat-bag1`, exe `EA0C7F16…`:
  terminó y volvió a root13 (170,4 s de seguimiento; 312,774 s totales), pero
  **NO es validación aceptada**: `_work/recordings/gaso-retire-heat-bag1/manifest.json`
  tiene `accepted:false`. Conservados vídeo, audio, eventos y logs originales.
- Dos problemas observados, no ocultados:
  1. Reutilización activa: publicación a t132,810/gf8086, entrada gf8088 anim1;
     segundo golpe t136,212/gf8290 rechazado por VERIFY; gf8292 anim89 y
     restore t136,241. Trace y eventos en `_work/gaso/retire-event-review.json`.
     La verificación llamaba al plan de **retiro**, que exige current/previous≠1
     y ausencia de referencias: rechazaba precisamente un clip propio aún activo.
  2. Grabación rechazada: 3079 latidos, 4 tardíos, jitter p99 11,43 ms;
     pausa real 244 ms después de gf18018, 567/18469 pares de audio fuera del
     ajuste, ventana máxima 34,44 ms. `_work/gaso/retire-audio-diagnostic.json`
     localiza otra ventana a gf1621–1680 (navegación) con 34,443 ms. Recortar el
     final por sí solo NO basta (diagnóstico: ventana 37,1 ms). Sin modificar
     puertas ni excluir pares a mano; el vídeo queda rechazado.
- Corrección acotada (fuente sigue `CLIP_PUBLISHED=0`): `b1cb_inspect` valida
  identidad, límites, índices, clip y exclusividad sin exigir retiro;
  `b1cb_plan` lo envuelve y conserva current/previous≠1 y `b1cb_no_references`.
  Publish/restore siguen usando plan. Solo VERIFY usa inspect + tuple y no
  escribe guest. Plugin `08db37e56877aed8…`, binding `1ad022af059b4ba8…`.
- RED real: nuevo escenario con current=previous=1 y decoder dentro del clip
  falla en `publish && enter` (harness línea1084), log `reuse-active-red.log`.
  GREEN: 77 pruebas (runtime/binding/bank/adapter/loan/owned_clip), exit0,
  `reuse-active-green.log`. Tras mejora de cobertura, binding 6/6 exit0
  (`reuse-binding-review.log`). Mutaciones 12/12 detectadas con fallos de
  ejecución, no errores de compilación (`reuse-mutations.log`, logs individuales
  `mutation_*.log`). El runner anterior contaba un error de compilación como
  kill al quitar la única llamada de slot1_intact; corregido manteniendo la
  referencia en `0 && ...`, y ahora exige fallo de escenario.
- Goldfish nuevo para el delta (`spec-gaso-active-reuse.md`, 2 revisores):
  A **SIN HALLAZGOS BLOQUEANTES**, B **CON HALLAZGOS** (solo cobertura menor).
  Ambos confirman guardas de escritura intactas. Hallazgo confirmado/aplicado:
  probar rechazo de publicación por decoder/pose con **tupla todavía vacía**,
  para que una tupla ya publicada no oculte la falta de guarda. Harness binding
  `93e7e1734eb2143a…`; runtime `c9ecd822c7eca7b9…`.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Build `gaso-active-reuse` pasó preflight/build; exe
  `11102F81E6B5B732696A0246986727808C4B449AF8B1B655D72B6189425BF1D8`,
  solo exp-8mb; backup previo `BAG2JP.exe.bak-EA0C7F16-retire2`. Guarda 1 solo
  en árbol de build; ningún cambio en estable. Calibración
  `20261112T161103659501Z-gaso-active-reuse-calibration`: selector y ocho aristas
  inspeccionados en `reuse-cal-grid.png` y aceptados para ese hash.
- Nueva prueba en curso: `_work/gaso/run_recorded_retire.py` (wrapper del harness
  y puente reversible, no cambio de motor ni de grabador). Arranca grabación al
  gameplay y la detiene tras el primer selector comprobado por RAM, incluyendo
  0,5 s de imagen de retorno antes de STOP. Captura íntegra de ese intervalo,
  no montaje de audio. No pretende validar la navegación que queda fuera del
  intervalo. Hash wrapper `ece11fdaf1d08199…`; sintaxis y 3 tests host de límites
  comprobados (selector detiene, otro estado continúa, captura terminada no se
  sobrescribe), `reuse-capture-boundary-tests.log`, exit0. Ejecución viva
  pendiente. Tag `gaso-active-reuse-heat-bag1`, log `_work/gaso/reuse-run.log`.
- Siguiente: exigir manifest accepted=true; comprobar segundo golpe en anim1,
  retiro posterior, fin y selector; revisar fotogramas y audio. No pedir
  conformidad ni commit (paso7) antes de tener esa evidencia. Límites anteriores
  de compañeros, generación, savestate entre procesos y latencia siguen abiertos.
- Resultado del nuevo ensayo `20261112T161312762561Z-gaso-active-reuse-heat-bag1`:
  harness exit0, 301,425s; seguimiento171,1s, fin observado160,5s, retorno root13.
  Ajustes verificados tras el puente: settings `B41A5FC8A597`, keybinds
  `EAAF722E480D`, state `EE35AB929773`; 67 saves originales comprobados por el
  harness. El wrapper detuvo la captura en `returned-selector`, no `song-end`.
- El trace sí corrige el fallo: primer golpe gf7385 y segundo gf7589 con Heat
  en anim1; ningún `reuse refused`. Retiro t9,966/gf7804–7805, posterior anim90;
  petición reflejada rechazada t132,918/gf15175. Datos en
  `_work/gaso/gaso-active-reuse-heat-bag1-event-review.json`. Esto es evidencia
  de logs, NO aceptación visual ni fidelidad de audio.
- `finalize` exit0, manifest `accepted:true` **solo de sincronización**:
  1716 latidos, 5 tardíos, jitter12,45ms, 0 pausas; audio44058Hz,
  10267 pares/0 descartes, ventana8,24ms. Pero la inspección de contenido
  (`look.py`, tiempos0,5/1,9/2,94/3,4/6,35/10,1/167/170s) muestra **otro juego
  tapando BAG2JP en todos esos fotogramas**. La captura no sirve como evidencia
  de BAG2JP aunque sus puertas temporales hayan pasado. No se cambia el
  manifiesto técnico ni se atribuyen al juego imágenes de otra aplicación.
  Dictamen separado: `_work/gaso/reuse-visual-review.json`,
  `gameplay_evidence_accepted:false`. No se revisan más imágenes de esa sesión
  ajena ni se entregan como vídeo del ataque.
- **Bloqueo actual (paso5, antes de conformidad/commit):** hace falta ventana
  BAG2JP visible, completa y sin cubrir durante combate→selector. No cerrar,
  mover ni interferir con la sesión ajena para forzar una grabación. Alternativa
  futura: captura directa del render, solo si se demuestra imagen no negra y
  sincronización; PrintWindow de screenshots no demuestra vídeo válido.
  No relanzar otra partida a ciegas con la misma oclusión. Sin commit; candidato
  experimental `11102F81…` permanece instalado, fuente canónica guardada en0.
- Owner autoriza corregir el bloqueo: foco y Always on Top **solo al grabar**,
  para «todas las ventanas que necesites grabar». Helper genérico
  `tools/test/recording_window.py` integrado en `bag2_record.py`, sin imponer
  ese estado a ventanas no seleccionadas ni cambiar la instalación de juego.
  Pruebas/restricciones/fallos del ensayo y vídeo de ventana propia en
  `notes/tool-evidence/bag2-record.md`, entrada foreground/topmost temporal.
  Goldfish en curso (`_work/goldfish/spec-recording-window-focus.md`);
  no relanzar runtime/build/calibración sin cambios. Tras validar el grabador,
  reanudar partida con exe11102F81 y entregar únicamente vídeo revisado del juego.
- Corrección del grabador verificada en host:31 pruebas/7mutantes; Goldfish
  2×CON HALLAZGOS con correcciones aplicadas y verificadas (cookies de ventana,
  popups, cancelaciones/cierre y estado atómico antes de finalize). Detalle y
  hashes en el log del grabador. Windows puede negar foreground: se aborta sin
  grabar otra aplicación, sin forzar teclas ni cambiar opciones globales.
- Nueva partida en curso con la protección, tag `gaso-pinned-reuse-heat-bag1`,
  log `_work/gaso/pinned-reuse-run.log`; se reutilizan exe11102F81 y calibración.
  Siguiente: finalize solo tras cierre/restauración; verificar guard passed=true,
  manifest accepted=true **y** píxeles de BAG2JP; después revisar ataques/fin/retorno.
- `gaso-pinned-reuse-heat-bag1` falló al empezar a grabar por foco de teclado
  denegado; ajustes/saves restaurados, sin nueva aceptación. El criterio final
  es el de PowerToys solicitado: pedir foco una vez, mantener topmost descubierto,
  no requerir monopolizar el teclado. Prueba Win32 v6 grabó la ventana correcta
  sin foco de teclado y restauró estados;31tests/7mutantes siguen verdes.
  Helper/grabador finales `42e6c1d…`/`7c783595…`.
- Integración actual: `gaso-topmost-reuse-heat-bag1`, log
  `_work/gaso/topmost-reuse-run.log`. No repetir capturas anteriores ni calificarlas
  de aceptadas. Seguir hasta evidencia real visible/sincronizada y solo entonces
  consultar conformidad/commit; exe11102F81 y fuente guard0 sin cambio.
- Chequeo temprano de la captura actual a1s (`topmost-early-check.png`): sí se
  ve BAG2JP, Gas-O/Heat y escenario correcto; sin oclusión en ese fotograma.
  No equivale aún a validar la partida ni la sincronización/restauración final.
- **Cierre del paso 5 (evidencia grabada) de `gaso-topmost-reuse-heat-bag1`**:
  manifiesto `accepted=true`, 1481 latidos (4 perdidos), jitter p99 13,2 ms,
  59,939 fps, audio 44056 Hz/8881 pares/0 perdidos/ventana 9,59 ms, 20 eventos;
  `window_guard` `passed=true` con 157 comprobaciones y `focus_acquired=false`,
  `recording_state=closed`; ajustes B41A5FC8A597/EAAF722E480D/EE35AB929773 y
  71 saves originales restaurados (verificado por el harness). Evidencia:
  `_work/recordings/gaso-topmost-reuse-heat-bag1/` (`owner.mp4`, `raw.mkv`,
  `review.mkv`, `events.json`, `stills/`) y run
  `_work/versus-runs/20261112T172921464652Z-gaso-topmost-reuse-heat-bag1`.
- **Revisión visual propia (fotograma a fotograma)**: láminas en
  `_work/gaso/sheets/` (`first-catch.png`, `second-catch.png`, `retire.png`
  y recortes `key-catches.png`/`key-rival.png`; generadas con
  `_work/gaso/make_sheets.py`). Confirmado: (1) es BAG2JP, Gas-O vs Heat en
  GasOBAG1, sin aplicación ajena; (2) en el primer golpe (≈3,02 s) el rival tras
  el pilar verde recibe impacto y su medidor junto a «HEAT» pasa de 300 a 180;
  (3) en torno al retiro (gf7714–7715, ≈9,76–10,16 s) se ve a Gas-O **agarrar y
  lanzar al rival**, que cae al suelo, es decir el clip CAUGHT en acción, y el
  actor vuelve a su animación propia después; (4) el HM pasa a anim90 y la
  partida vuelve al selector (root13). No verificado por mí: el significado
  exacto del valor del medidor y el «eye-flash» de reacción (no identificado con
  certeza en las láminas); ambos quedan como observación, no como aceptación.
- Estado: **pendiente solo la conformidad del propietario y el commit del paso 7**.
  Fuente canónica sigue en `GASO_CAUGHT_CLIP_PUBLISHED 0`; exp-8mb conserva el
  ejecutable `11102F81…BF1D8`. Nada commiteado.

### caught-bag1-reference-20261112 - referencia BAG1 nativa con autoplay

Petición del owner: «los timings varian»; grabar en BAG1 Gas-O vs Heat en el
escenario GAS-O con el mismo ataque y comparar fotograma a fotograma.

- Herramienta: `_work/gaso/native-reference/bag1_reference_session.py`
  (`boot`/`keys`/`shot`/`ram`/`record`/`close`/`finalize`). Aislamiento de
  `native_session.py` (6 ficheros respaldados, tarjetas copiadas, saves
  verificados al cerrar). Audio exacto con el driver SDL `disk` (S16LE 44100,
  colocado por ajuste tamaño/tiempo + `asetrate` a la tasa medida), sin mezcla
  temporal (`smooth-presentation` off), ventana 1280×960, captura ddagrab con
  sellos de pared, RAM BAG1 en el mismo reloj. `finalize` solo tras `close`
  (el driver bloquea el raw).
- Autoplay BAG1 (modo 2P, sin parchear el exe): de `bag1_decomp.txt`,
  `FUN_80021c6c` busca en el compás la última pulsación y `FUN_8002a048` elige
  grupo por el botón final (`DAT_8006914c>>4`); la tabla normal común
  `@80055f00` tiene comandos de un solo botón: × → paso 3 (nivel 0, válido
  siempre), △ → 0x6e ataque, □ → 0xaa esquiva, ○ → paso 1. Corrección: en los
  bytes de comando 0x10/0x20/0x40/0x80 son ↑→↓← y 1/2/4/8 son △○×□ (el
  docstring de `dump_bag1_commands.py` los tenía al revés). El bot pulsa en cada
  frontera de compás × para P1 (X) y P2 (N), y △ (A) para Gas-O en los compases de
  ataque. Las tablas solo no se cubren (no hace falta para esta ventana).
- Toma: `runs/20261112T163101-bag1-reference/gaso-vs-heat-autoplay/`
  (`owner.mp4`, `raw.mkv`, `ram.csv`, `events.json`, `manifest.json`,
  `check/`). Guarda de ventana `passed` (200 comprobaciones); RAM: los dos
  jugadores con paso válido (bit 0x4) en todos los compases; ataques en los
  tiempos 20 y 28 (`p1_attacks` 2→1→0); golpe a Heat en el tiempo 24
  (`p2_flags` 0x10→0x92→0x80), segundo aviso en el 32, libre en el 40 (36,87 s),
  vuelve a puntuar en el 44. **`accepted=false`**: 56,1 fps (umbral propio 59,5);
  ddagrab no pasa de ~58 fps ni sobre el escritorio (a 144 Hz da ~97 fps con
  huecos de hasta 35 ms). Los tiempos de abajo usan sellos de pared: precisión
  estimada ±2 fotogramas.
- Medición: `tank_timing.py` (fracción de píxeles verdes por fotograma);
  bordes idénticos en `raw.mkv` y `owner.mp4` de ambos juegos. Origen T0 =
  primer fotograma con tanque.

  | Evento (desde T0) | BAG1 nativo | BAG2 (`gaso-topmost-reuse-heat-bag1`) |
  |---|---|---|
  | Tanque 1 visible | 0 (29,983 s) | 0 (2,367 s) |
  | Tanque 1 desaparece | +2,35 s (~5,5 tiempos) | +0,90 s |
  | Entre tanques | Heat fuera, **misma pose de atrapado**, 1,10 s | Heat fuera **con estrellas de aturdimiento**, 2,12 s |
  | Tanque 2 visible | +3,45 s | +3,02 s |
  | Tanque 2 desaparece | +7,03 s (dura 3,58 s) | +4,33 s (dura 1,32 s) |
  | Tras el tanque 2 | de pie ~0,2 s y baila en el compás siguiente (+8,6 s); sin caída | estrellas hasta ~+5,5 s, caída al suelo ~+6,5–7,1 s, de pie ~+7,5 s (retiro slot1 +7,58 s) |

  Tempo comparable (BAG1 0,428 s/tiempo; tanques a 3,4–3,5 s en ambos). La
  duración total del castigo es parecida (~7,0–7,6 s), pero en BAG2 el tanque
  dura 2,6× menos, aparece un estado de aturdimiento con estrellas que en BAG1
  no se ve y hay una caída al suelo final que BAG1 no muestra en esta toma.
  Láminas: `check/attack-sheet.png`, `bag1-between-tanks.png`,
  `bag1-release.png`, `bag2-attack-sheet.png`, `compare-sheet.png`; vídeo
  lado a lado `check/compare-bag1-left-bag2-right.mp4` (izq. BAG1 con su audio,
  der. BAG2; T0 a los 2 s).
- No verificado: la causa en BAG2 de la vida corta del tanque y de las
  estrellas/caída (falta contrastar con Ghidra el temporizador del tanque y el
  estado del receptor); la pulsación BAG1 cae una frontera de compás antes del
  golpe (ataque en el tiempo 20 → golpe en el 24), no medida aún en BAG2.
- Siguiente: decidir con el owner si se corrige la duración del tanque y la
  reacción del rival antes del commit del paso 7.

### caught-tank-timing-candidate-20261112 - candidato host, no aceptado

- El owner eligió corregir antes del commit («Continua»). La siguiente
  validación grabada está dentro del ciclo solicitado; el commit sigue sin permiso.
- Cambio experimental en `bag2jp_gaso_caught.c`/`bag2jp_gaso_tank.h`: contador
  por receptor al consumir la entrada directa de Gas-O BAG1; el visual detecta
  cambios, sostiene el tanque en slots 89/1 y corta tras abandonar la reacción.
  Se eliminó la vida fija HOLD65. No se escriben pending+0x18 ni 0x80400000.
  Las constantes nuevas (descenso6, salida9, borrado por anim-frame38) son
  aproximaciones de la toma, NO contrato nativo demostrado ni fidelidad aceptada.
  El borrado al siguiente ataque aún debe contrastarse con código nativo.
- Evidencia host previa: 26 tests OK (`test_gaso_caught_runtime`16 y
  `test_gaso_tank`10, 7,426 s). Cuatro mutantes finales detectados; el primer
  intento de no-clear falló compilando por variable sin uso y NO cuenta como
  detección funcional; su variante posterior falló la aserción del escenario7.
- Build `20261112T222731773660Z-gaso-tank-bag1-timing/metrics.json`:
  `status=passed`, fase build41,09s. Comprobado al retomar; no demuestra partida
  ni despliegue. Staging solo `src/bag2jp_gaso_caught.c` y `src/bag2jp_gaso_tank.h`;
  backup `_work/gaso/build-src-backup-pre-tank-timing/`. Canónico guard0;
  guard1 solo en build/src. `bag2jp_bag1_versions.c` no se copió a propósito.
- Goldfish: dos primeros intentos `ses_e2e1fdeafffeC4lGSrOjRRO4On` y
  `ses_e2e1fd3c9ffeRUXsp6pSU5OZGy` fallaron por cuota sin emitir hallazgos:
  REVISIÓN NO UTILIZABLE. Spec `_work/goldfish/spec-gaso-tank-timing.md`.
  Se solicitaron dos revisores en frío nuevos al retomar; veredicto pendiente.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Herramientas consideradas: Ghidra MCP verificado (log propio); shell/JSON
  para evidencia objetiva; subagentes para Goldfish exigido. FFmpeg/grabador
  se reservan para la validación real, no se repite vídeo con runtime anterior.
  Funcmatch no corresponde: aún no se busca equivalencia main BAG1→BAG2;
  el origen del timer pendiente está en overlay005. Sin tarea mecánica masiva
  adicional que justifique un modelo GPU local durante esta revisión acotada.
- Pendiente: triar Goldfish, corregir/reverificar hallazgos antes de desplegar;
  identificar estrellas y salida90 (aún intactas), contrastar tiempos nativos,
  grabar nueva prueba con audio y manifest aceptado. Sin commit ni aceptación.

#### Goldfish y regresiones al retomar

- Revisores nuevos `ses_e2e158122ffexvgA8TIKPBQ57T` y
  `ses_e2e15676fffeNAguDiUb4yuAzn`: ambos CON HALLAZGOS. Estado revisado:
  candidato de build anterior; los cambios siguientes NO están en ese exe.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Confirmados y corregidos: `released` no se reiniciaba al volver al trap;
  filtros de personaje/versión conservaban el tanque; sustitución de rival
  válido heredaba el visual. Cuatro regresiones nuevas fallaron con aserciones
  antes del fix (`_work/gaso/tank-goldfish-red.log`); después 30 tests OK.
- Confirmado y corregido: slot1 ajeno prolongaba el tanque. Regresión RED
  `_work/gaso/tank-slot1-red.log`; consulta de solo lectura
  `bag2jp_gaso_caught_owns_slot1(side,actor)` exige guard1, publicación,
  identidad de actor y tuple original intacta. Test runtime comprueba propietario,
  lado/actor inválidos y ausencia de escrituras. GREEN final
  `_work/gaso/tank-goldfish-green2.log`: 31 tests OK/10,398s (16 runtime/15 tanque).
- Confirmados aún ABIERTOS: heurística `anim_frame < elapsed` no prueba inicio
  posterior; retornos por heap/OT/cámara congelan reloj; coherencia savestate
  dentro de root19; pérdida de hit con puntero temporalmente inválido. Descartar
  el hit con identidad inválida es conservador, pero no prueba fidelidad temporal.
  El hilo único evita carrera concurrente; orden real hook/tick NO verificado.
  Faltan P2, máximo, intercalado y savestate. Ningún hallazgo refutado.
- SHA256 post-fix tanque `AA3475B55A651D9084DEBF7C5DDAACFB38A3CF78A48B2762BCF2D0713955FE74`;
  caught `9B5B8D64D1D5F62955C079C4203C985408276091EBC9868ABAEDDE3A7D9E20D6`.
  Whitespace: diff--check ordinario detecta CRLF previos en líneas del candidato;
  `git -c core.whitespace=cr-at-eol diff --check -- <rutas del cambio>` pasa.
  No se normalizaron archivos completos ni se cambió config Git.
- No nuevo staging/build/deploy tras estos fixes. El build verde de41,09s está
  obsoleto respecto a la fuente actual. No suite global nueva ni prueba en juego;
  estos 31 casos verifican solo las costuras host. Guard canónico sigue0.
- Próximo acotado: reemplazar la heurística de ataque por una transición demostrada
  y resolver reset/savestate antes de reconstruir; mantener abiertas procedencia
  de tiempos, estrellas y salida90. No repetir Goldfish del mismo checkpoint.

#### caught-tank-state-20261112 - transición observada y descarte al cargar

- Objetivo acotado: eliminar `anim_frame < elapsed` y descartar estado host
  obsoleto tras reset/savestate; aceptación de esta costura mediante regresiones
  del header/callback reales. No equivale a aceptación del ataque.
- Preflight `20261112T231544516747Z-gaso-tank-state` pasó. Git previo conservado
  en `_work/gaso/tank-state-start-status.txt`; sin staging a build ni despliegue.
- Nuevo visual: adopta la familia74/88 presente al golpe y solo arma borrado
  cuando después observa no-ataque->ataque. Un frame pausado o un bucle de la
  misma animación no se convierte en otro ataque al envejecer el tanque.
  Límite explícito: no detecta reinicio74->74 sin una muestra no-ataque intermedia.
  El umbral38 sigue siendo aproximación experimental, no contrato BAG1 demostrado.
- `gaso_caught_forget()` incrementa epoch host en reset y savestate; el visual
  lo adopta descartando tanque y golpes contados anteriores aun con root19.
  No reconstruye un tanque activo del savestate: falla cerrado. Conserva el
  límite previo del tuple publicado en RAM al cargar; no lo repara ni escribe.
- Observación de golpes/transiciones y mantenimiento se ejecutan antes de las
  puertas gráficas heap/OT/cámara. Fallar dibujo no pausa liberación ni límite.
- RED `_work/gaso/tank-state-red.log`: 19 casos, cuatro fallos de aserción nuevos
  (epoch, ataque pausado, transición sin dibujo, límite sin dibujo). GREEN
  `_work/gaso/tank-state-green2.log`: 35 tests OK/11,001s (19 tanque/16 callback,
  callbacks compilados guard0 y1). El escenario8 antiguo simulaba «ataque
  anterior» solo con elapsed5; se corrigió para generar un golpe real durante
  anim74/frame100, acorde con su requisito. Primer GREEN falló solo ese fixture;
  se conserva `_work/gaso/tank-state-green1.log`, no se declara éxito de ese run.
- Ghidra MCP verificado, consulta decompile8002d06c falló FUNCTION_NOT_FOUND;
  read_memory8002d4a0/48 sí pasó. Alcance/límites en log ghidra-psx-psyq.
  No se repitió FFmpeg/grabador porque este tramo es host y el runtime no cambió.
  Funcmatch no pertinente a un cambio de estado host sin búsqueda de equivalentes.
- Suite global y Goldfish estrecho de esta corrección nueva en curso; no repite
  la revisión completa del candidato. Spec `_work/goldfish/spec-gaso-tank-state.md`.
  Fuentes canónicas guard0; build anterior obsoleto; sin commit.

##### Triaje y verificación del estado

- Goldfish estrecho: `ses_e2ded1025ffe2iyj2HVsVxV3w4` y
  `ses_e2ded1018ffeQw2Cl9xfiQE2pw`, ambos CON HALLAZGOS. Verifican por lectura
  la transición y el mantenimiento antes del render; no ejecutaron pruebas.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Hallazgo confirmado/corregido: callback->golpe nuevo->primer tick perdía el
  golpe. RED `_work/gaso/tank-epoch-window-red.log`. El callback guarda ahora
  `epoch_hits[]`; el visual toma ESA frontera, no el contador posterior al tick.
  El reset ordinario fuera de combate adopta golpes actuales sin silenciar el
  primer golpe futuro. Test añadido de salida real root13 y reentrada root19.
- Segundo hallazgo confirmado/corregido: el caso sin render no probaba cuándo
  se observaba el flanco. Ahora exige `clear_on_attack` durante frame37 sin
  render y la desactivación en frame38 AÚN sin render; luego restaura dibujo.
- GREEN final `_work/gaso/tank-state-green3.log`: 37 tests OK/11,067s
  (21 tanque,16 callback; callback guard0/1). Mutaciones reales sobre copias
  `_work/gaso/tank-epoch-mutations/`: sin incremento epoch y sin snapshot del
  callback mueren por aserción, no por compilación (3,159s/3,172s).
  Script reproducible `_work/gaso/check_tank_epoch_mutations.py` conserva copias,
  logs y resultados; no modifica fuente ni entorno global.
- Primera suite completa `_work/gaso/tank-state-full-suite.log`: 363 tests,
  1 fallo y32 errores/108,716s. Comparación literal de33 nombres con baseline
  `_work/gaso/p2a-full-suite.log` sin añadidos ni retirados; reporte
  `_work/gaso/tank-state-suite-comparison.json`. No es suite verde.
  Se inició antes del último fix de epoch: NO prueba por sí sola el estado final.
  Nombres completos en logs, grupos: stage_audio, stage_shim, visual_regions,
  caught_entry, heat_announcer/costume/dbi_face_patch, strike_bag1_fx/costume/
  texture_contract; fallo `test_package_keeps_models_separate_from_texture_packs`.
- Repetición completa sobre fuentes finales en
  `_work/gaso/tank-state-final-full-suite.log`, en curso al escribir este bloque.
  Hashes finales `_work/gaso/tank-state-final-source-hashes.json`. Whitespace
  con `core.whitespace=cr-at-eol` pasa; sin cambios de configuración Git.
- Límites aún abiertos: orden hook/tick real, impactos con puntero temporalmente
  inválido, reinicios sin observar no-ataque, P2 y fidelidad6/9/38. No se reconstruye
  visual de un estado cargado. Estrellas/salida90 siguen intactas; son el siguiente
  tramo de investigación nativa. No reabrir un gate de autorización ya concedido
  para investigar: commit sí necesita permiso; guard1/despliegue y partida no se
  hicieron en este tramo. No repetir revisión completa sin cambio/evidencia nuevos.
- Cierre de la repetición: **365 tests,1 fallo/32 errores,106,422s**. Los33
  nombres coinciden exactamente con baseline p2a; sin nombres añadidos/retirados
  en `_work/gaso/tank-state-final-suite-comparison.json` (incluye lista completa).
  No se afirma que el repositorio esté verde ni se arreglaron fallos ajenos.
  Checker documental de ambas notas: issues vacíos en
  `_work/gaso/tank-state-docs-check.json`. El próximo tramo es localizar en
  overlay005 los productores de estrellas y salida, no otra ronda de tests
  idénticos. Mantener salida90 hasta contrastar el contrato y la decisión previa.

#### caught-secondary-effect-20261112 - origen estático, sin parche

- Objetivo de este tramo: localizar productor de partículas y salida90 sin
  tocar comportamiento. Preflight gaso-stars-research pasó; estado Git previo
  `_work/gaso/stars-research-start-status.txt`. Sin nuevo build/deploy/partida.
- **Dos canales diferentes:** tabla main80051458 tiene fila Gas-O `[202,1]`.
  Primera columna entrega request202 -> motion89; segunda columna1 se carga
  en0058009b5d0 y llama `80019d70(rival,1)` en8009b5e4. Redirigir el motion a
  CAUGHT NO elimina este canal. Tabla compartida: Heat/Strike también `[202,1]`;
  deshabilitarla globalmente dañaría golpes ajenos/stock/reflejos.
- Selector secundario en **actor+1724**. 19d70 lo guarda y selector1 llama
  **8001a8fc**: inicializa8 registros de48B desde actor+15a0, fases angulares
  separadas0x200. **80019e34** comprueba selector y despacha selector1 a
  **8001ab8c**, independiente del slot de animación actual. Este último rota/
  expande partículas, usa sprites de atlas y desvanece tras edad80 con paso4;
  alterna grupos de partículas y parámetros de sprite. Es el candidato concreto
  del efecto observado; **no se ha demostrado aún la identidad gráfica exacta
  del bitmap de las estrellas** ni el orden live respecto al hook CAUGHT.
- **Caída90:** no la crea ese efecto secundario. Reutilizado decompile verificado
  de dispatcher8002a090: request202 guarda índice2, tiempo=max(1,duraciónPendiente
  -2*len(salida90)); modo0 descuenta delta8006d994, y al expirar usa tabla
  800518ec[2]=90 (excepto ramas especiales45/46,84/85). 0058009c144 escribe
  pendiente+1c a partir de tabla temporal. Es salida nativa BAG2, todavía intacta.
  No confundir marcador3 de005 con duración idéntica a BAG1.
- Evidencia nueva `_work/gaso/stars-research-report.json`: hashes main/005,
  cuatro regiones MCP=raw, palabras callsite, hashes de4 decompiles y tiempos.
  MCP obligatorio sí usado; dos consultas sin función/una función ajena están
  registradas junto con éxitos en ghidra-psx-psyq. Capstone: scan8 candidatos,
  independiente pero no exhaustivo; no sustituye Ghidra ni evidencia visual.
- Riesgo para el siguiente hook:8009b5e8 (delay-slot JAL) es `move a1,s0`;
  cambiar a1 antes del JAL sería sobrescrito. Además la publicación slot1 puede
  ser rechazada DESPUÉS de ese punto; no suprimir ahí sin probar propiedad y
  fallback. No se ha elegido ni aplicado una escritura nueva de actor.
- Herramientas pertinentes: Ghidra MCP+headless aislado, Capstone/hash para
  contraste; se reutilizó decompile005 y timing previo sin reejecutarlos.
  FFmpeg/grabador se reservan para prueba real; no hubo nueva toma que analizar.
  Funcmatch no aplica a este routing ya localizado, sin búsqueda de equivalente.
  Goldfish omitido justificadamente: solo notas y evidencia en _work, ninguna
  ruta ejecutable tools/mods/patches modificada EN ESTE tramo. Fuente previa
  host-verificada sigue guard0; build antiguo obsoleto. No commit.
- Próximo: confirmar sprite/efecto visible con asset o evidencia runtime ya
  existente, y diseñar supresión solo para receptor con CAUGHT publicado propio
  (fallar cerrado si no lo está), manteniendo Heat/Strike/stock/reflejos. Antes
  de quitar salida90, contrastar la decisión previa de conservarla; no convertir
  una investigación en permiso para cambiar silenciosamente ese contrato.

#### caught-secondary-suppression-20261112 - candidato host guard0

- Objetivo: identificar el sprite y suprimir el canal secundario solo después
  de publicar/verificar CAUGHT propio. Preflight gaso-secondary-suppress pasó;
  Git previo en `_work/gaso/secondary-suppress-start-status.txt`.
- Asset encontrado: `assets/archive/system/010/001.tim`, miembro1 deDFS010,
  SHA2560039c3d39da4e86452b63028d70e575a38514f8a07d2026ca23318881821431f;
  SHA1 coincide con _container y PNG con _png_sha1. TIM4bpp, imagen512,256 de
  256x256 (UVbase0,0). UV72,56/16x16 del renderer impar contiene **estrella**;
  cicloCLUT8..11 produce naranja/rojo. Extracción directa desde TIM, no solo
  el PNG histórico: `_work/gaso/secondary-star-palettes.png` y
  `secondary-star-identity.json` (hashes,100 píxeles no cero).
- Búsqueda de atlas: contacto reducido de100 PNGs del sistema; system000 era
  fuente/paleta, irrelevante. Pillow avisó de transparencia de paleta durante
  esa hoja exploratoria; la evidencia final usa bytes TIM/CLUT originales.
  Lectura de assets/archive/system/_container.json falló porque no existe;
  se usó el manifiesto correcto system/010/_container.json. No se alteró asset.
- Límite: correspondencia estática sprite/UV/paleta, **no nueva captura de juego**
  ni demostración del descriptor54c50 cargado. MCP solo ve su inicialización.
- Cambio en `bag2jp_gaso_caught.c`: tras publish/VERIFY y redirecta2=1,
  `gaso_caught_suppress_secondary(side,actor)` exige owns_slot1 vivo, rango
  completo hasta+1726 y selector1; escribe solo halfword0 en actor+1724.
  Guard0 permanece canónico. Rechazo de lookup/binding/VERIFY conserva efecto.
  No hooks nuevos, llamada guest, tabla global, pending+18 ni timer/salida90.
- **Consecuencia audiovisual conocida:** selector1 agrupa8 partículas Y la
  petición del sonido genérico0x0e desde1ab8c. Desactivarlo elimina ese canal
  entero; NO es una corrección exclusivamente visual. Fidelidad del audio y
  que el controlador posterior conserve selector0 están pendientes de partida.
- RED `_work/gaso/secondary-suppress-red.log`: el caso positivo guard1 falla
  por no suprimir; negativos/guard0 conservan comportamiento. Primer GREEN
  falló el whitelist antiguo de solo tuple; se extendió a una excepción exacta
  (main actor,+1724,width2,value0,previo1,guard1), no a escrituras arbitrarias.
  GREEN `_work/gaso/secondary-suppress-green2.log`: **39 tests OK/11,273s**
  (18 runtime/21 tanque). Casos positivos ambos lados, re-hit activo, vecino
  superior y atacante intactos, otros selectores0/2/21 conservados. Negativos:
  receptorBAG2, binding inválido, Heat/Strike/Gas-O BAG2 y reflejo.
- Goldfish estrecho `_work/goldfish/spec-secondary-suppress.md`, revisión nueva
  de este helper/callsite/tests, no del candidato completo. Primer revisor
  ses_e2db2dc0cffdwxzW6BeIflKmLd: SIN HALLAZGOS BLOQUEANTES; señaló límites
  de cobertura (rango al límite RAM, VERIFY rechazado con selector1, reproducción
  real del controlador). Segundo revisor y suite global en curso.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Herramientas: MCP/lecturas relevantes contrastadas; PIL/struct para recorte
  reproducible sin manipular ventanas con TIMedit. Capstone/headless previos
  reutilizados; no otra extracción idéntica. FFmpeg/grabador no corresponden
  aún: no hubo nueva partida/captura. Sin trabajo masivo que justifique GPUlocal.
  Sin staging/build/deploy/commit; no presentar esta supresión como aceptada.

##### Triaje final de la supresión

- Segundo Goldfish ses_e2db2dbffffeZVY0tjBI6rwSzF: CON HALLAZGOS de cobertura,
  no bug funcional confirmado. Se aplicaron ambos: caso15 recoloca el receptor
  en el último actor alineado cuyo campo cabe y en el siguiente word fuera de
  RAM; caso14 incluye pérdida de tuple tras publicación y otro golpe con selector1.
  Esa ruta conserva feedback nativo. El segundo revisor tampoco ejecutó pruebas.
  No se repitió la revisión del mismo checkpoint tras corregir cobertura.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- GREEN final `_work/gaso/secondary-suppress-final-targeted.log`: **40 tests
  OK/12,598s** (19 runtime en guard0/1,21 tanque). Hashes de fuentes/tests finales
  en secondary-suppress-final-hashes.json. SelectorfueraRAM no se lee/escribe;
  canario de alias en80000000 queda intacto. No se relajó el guard de producción.
- `_work/gaso/check_secondary_mutations.py`:3 mutantes sobre copias detectados
  por aserción real (no compilación): sin clear5,456s, selectores ajenos2,898s,
  sin rango de campo3,130s. Resultados/logs en secondary-suppress-mutations/;
  no se modificó código canónico para ejecutarlos.
- Suite completa secondary-suppress-full-suite.log:367 tests,1 fallo/32errores,
  105,634s. Mismos33 nombres que baseline p2a, sin añadidos/retirados; listado en
  secondary-suppress-suite-comparison.json. Corresponde a la misma implementación
  antes de añadir cobertura límite/pérdida de tuple y comentario de cabecera;
  esos cambios finales se verificaron con los40 casos. No suite global verde.
- Próximo ciclo: preparar staging/build experimental de estas fuentes con
  backup y guard1 solo en build/src; conservar divergencia intencional de
  bag1_versions y no tocar estable. Después grabar validación de tanque/estrellas
  y audio, comparar con BAG1, preservando salida90 hasta resolver decisión previa.
  La supresión completa del canal incluye0x0e: declarar esa diferencia al evaluar
  audio; no afirmar que un PASS host prueba la escucha ni la reproducción real.

#### caught-clear-frame23-20261113 - corte del tanque al siguiente ataque

- `GASO_TANK_CLEAR_FRAME` 38→23: inferencia de una toma a 0,428 s/beat (~16
  frames `+0x1554` por beat); BAG1 corta 0,61 s ≈ 1,43 beats tras iniciar el
  ataque. Supone que el corte BAG1 sigue el beat. 40 tests host OK
  (`_work/gaso/clear-frame23-targeted.log`); Goldfish
  ses_e2d7dd90affemn6N7733AOEA75 SIN HALLAZGOS BLOQUEANTES, notas aplicadas.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Build `gaso-clear-frame23b` (exe `7340f010…`), toma aceptada
  `gaso-clear-frame23-heat-bag1`. Desde el inicio del tanque, BAG1/BAG2:
  tanque1 2,35/2,32 s; hueco 1,10/1,11 s; tanque2 +3,45/+3,43; fin tanque2
  +7,03/+7,18. Tras el tanque2 BAG2 aún difiere: salida90 (Heat cae y se
  levanta en +8,3; BAG1 baila en +7,1). Decisión del propietario pendiente.

#### caught-tank-liquid-20261113 - interior translúcido con burbujas

Petición del propietario: el interior se veía verde, opaco, "como un escáner
láser"; en BAG1 es líquido translúcido con burbujas.

- Evidencia nativa reutilizada (decompiles JP ya contrastados,
  `native-tank-primitives-decompile/`): los cinco emisores hacen NCLIP y
  descartan caras traseras; cilindro G4 0x3A con E1000600 (ABR0), metal G4 0x38
  y tapa G3 0x30 opacos. Causas del aspecto anterior: dos capas de cristal (cara
  delantera y trasera), modo E1 aplicado a primitivas equivocadas (la OT antepone
  paquetes: la GPU dibuja en orden inverso), metal semitransparente, 8 cuadrados
  `strike_emit_spark` y humos que saltaban de segmento cada frame.
- Cambio en `bag2jp_gaso_tank.h` (solo render): culling por signo de
  `det(tank_rot)` (todas las caras están enrolladas hacia dentro; vale con
  cámara encima y rival reflejado); una capa de cristal ABR0; metal/tapa
  opacos; orden GPU: E1 promedio, cristal, E1 aditivo, burbujas, brillos, metal,
  E1 promedio restaurado. Burbujas: 1-2, anillo de 16 segmentos aditivo con
  centro transparente y brillo, al 83-90 % de la columna, radio 110 por
  profundidad (redondas desde cualquier ángulo). Color del cristal despejado de
  la mezcla 50 % de BAG1 (blancos teñidos 153,185,150 y mediana 47,90,44 en
  31,0 s): `0x204422` ×1,1..×2,25 con degradado lateral. La iluminación GTE
  nativa no se reproduce: es aproximación.
- Tests: escenarios 21 (OT en orden GPU, modos, colores, conteos exactos),
  22 (rival reflejado) y 23 (cámara encima: 0 cristal, 8 tapa). 43 tests OK
  (`_work/gaso/liquid-targeted.log`); 9/9 mutantes detectados
  (`_work/gaso/liquid-mutants-r4.log`).
- Goldfish `_work/goldfish/spec-gaso-liquid.md`, 2 revisores
  (ses_e2d5d31c7ffeFr9ucWJM2db1si, ses_e2d5d2510ffeGO1RZVVFnYM2SY): CON
  HALLAZGOS. Aplicados: signo de culling invertido con cámara sobre el tanque
  (→ determinante), estado aditivo heredado (→ E1 final), burbujas sobre el metal
  (→ metal al final), radio de burbuja que se anulaba con el rival girado,
  comentario 66-79 %, huecos de test (reflejo, culling de metal/tapa, color del
  brillo). Refutado: hash distinto al del spec (solo se restauraron fines de
  línea; contenido idéntico). Tras el triaje cambiaron además el estilo de
  burbuja y el color; verificados con tests, mutantes y partida, no con una
  segunda ronda Goldfish. Riesgo residual en `strike_project` compartido
  (int16 sin clamp cerca del plano cercano), fuera de alcance.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Partida: build `gaso-liquid6`, exe `2d471918…` en exp-8mb (copia
  `BAG2JP.exe.bak-7340F010-pre-liquid`), calibración
  `20261113T025831301330Z-gaso-liquid6-calibration` revisada y aceptada. Toma
  **aceptada** `gaso-liquid6-heat-bag1`: 1704 latidos, 0 parones, 0 pares de
  audio descartados, jitter p99 12,8 ms. Tomas intermedias: liquid2/3
  aceptadas (aspecto superado), liquid4/5 rechazadas por audio/jitter
  (5b aceptada, color aún saturado). Mediana dentro del tanque ahora
  (54,91,56) frente a BAG1 (47,90,44); antes (31,109,50). Corte del tanque1
  revisado fotograma a fotograma: limpio, sin restos. Hojas en
  `_work/gaso/liquid-review/liquid6-*.png`.
- Diferencias que quedan: borde de burbuja algo más cian que en BAG1; sin puff
  lateral de humo ocasional de BAG1; un fotograma de la caída deja ver la base
  verde. Juicio visual final del propietario pendiente; sin commit.

##### Ajuste de proporciones/bordes y diagnóstico de aspecto (2026-11-13)

- A petición del propietario, candidato con escala XZ24%/Y26% (radio259,
  altura1164, antes378/985); burbuja radio68, borde `0x3c3430`, interior
  transparente hasta80% del radio (antes110/`0x704c28`/65%). Se busca más
  margen sobre cabeza/pies y menos anchura relativa, no se ha implementado la
  fórmula nativa por personaje. Comparación visual en
  `_work/gaso/liquid-review/phone-3-proportions.jpg` y `phone-4-bubbles.jpg`.
- Host:44 tests dirigidos pasaron; `liquid-mutants-r5.log` registra10/10
  mutantes detectados y restauración del header. Al elevar la cámara de21/22
  a4000, todas las tapas quedaron visibles: el mutante sin culling de tapa
  sobrevivió inicialmente. Se añadió escenario24 (cámara bajo el suelo a-2000,
  cero tapas) y volvió a detectarse. Ese log registra códigos de retorno,
  no conserva stderr de cada mutante; no confundirlo con prueba visual.
- Build `gaso-liquid7` pasó33,489s. Exe experimental
  `ca4a31c69dea1359b525a04bd40d70381bb8335897af53f607f514173915cfb6`;
  backup `BAG2JP.exe.bak-2D471918-pre-liquid7`. Copia activa del header:
  build/src/bag2jp_gaso_tank.h; no se toca la copia histórica bajo src/mods-src.
  Calibración `20261113T033425778903Z-gaso-liquid7-calibration` revisada/aceptada.
- Tomas preservadas: liquid7 RECHAZADA (1 parón,419 pares de audio descartados,
  ventana98ms); liquid7b RECHAZADA (cierre inseguro: invalid window Z order y
  FFmpeg sin salida limpia); liquid7c **captura ACEPTADA**,1707 latidos,0
  descartados,0 parones, jitter p99 12,1ms, residual de audio p99 15,94ms.
  Los errores PowerShell al resumir ErrorRecord en7b no prueban fallo del juego;
  el motivo de rechazo se tomó del manifest. No se borró ninguna toma.
- Revisión visual previa: primera caída y corte en hojas `l7-onset-sheet.png`,
  `l7-onset-zoom.png`, `l7-clear-sheet.png`; cristal presente en la ampliación,
  corte limpio. La nueva altura/anchura se aproxima más a la referencia, pero
  las burbujas siguen ovaladas y su borde aún es más definido que en BAG1.
  **No hay conformidad del propietario ni aceptación global de fidelidad.**
- Continuación interna: Ghidra MCP confirmó main JP `SLPM_862.19`, SHAea5a1668;
  `8002dc9c` fija GeomOffset256,120 y H384. La lectura de consumidores de
  cámara no identifica aún un contrato público para consultar el aspecto efectivo.
  El log de la partida dice `mod selected fixed display aspect 16:9` y
  `GTE X-squash + stretched present`; settings.toml4:3 no es fuente suficiente.
- Diagnóstico de host **aislado**, no parche de producción:
  `py -3.13 _work/gaso/check_bubble_aspect.py`, informe
  `_work/gaso/bubble-aspect-host.json`. Con header SHA58fcae3d… sin modificar,
  anillo real18×22 unidades. Bajo la hipótesis de scanout512×240 a16:9,
  ancho/alto presentado0,682. Prototipo con radio horizontal compensado por el
  aspecto explícito:26×22→0,985 a16:9 y34×22→0,966 a4:3. Comprueba aritmética,
  no detecta el aspecto en ejecución, no demuestra scanout de liquid7c ni
  suavidad nativa. No se aplicó una constante6/5 fija a producción.
- Herramientas consideradas: Ghidra y scripts deterministas usados; grabación/
  FFmpeg nuevos omitidos en esta continuación por reutilizar la toma aceptada y
  no estar implementada la siguiente corrección. Funcmatch no aplica (no se
  buscan equivalentes entre ejecutables), modelos locales no aportan a esta
  cuenta pequeña; Goldfish sí aplica a los cambios de header/tests.
- Siguiente: integrar una corrección de aspecto con contrato verificable (sin
  asumir16:9 de settings), probar radio y grosor/color del borde con valores
  independientes, mantener fuente guard0 y salida90. Una nueva prueba en juego
  requiere autorización del propietario según AGENTS; no hay nuevo commit.

- Goldfish del ajuste: spec `_work/goldfish/spec-gaso-liquid7-scale.md`, dos
  revisores `ses_e2cdf75f6ffebXgVLCEIhrtrnk` y
  `ses_e2cdf75f2ffeoFhw6T882rOxcN`, ambos **CON HALLAZGOS**, header revisado
  SHA58fcae3d4aae78255b9ed46f15254878545936f8bd995a8765db339ecf37e00c.
  Confirmado/corregido: prueba de radio/grosor/color dependía de producción o
  no existía; nuevo `check_bubble_rim_geometry()` fija centro248,647, radios
  exteriores9,11/interiores7,8 y color literal0x3c3430, incluido el segundo
  extremo del segmento. Nombre del test ya no afirma redondez. Orden de
  contorno antes de brillo protegido con `glint_seen`. No se ha corregido el
  comentario excesivo de redondez del header ni su aspecto real; se mantiene
  como límite explícito junto con cobertura adicional de crecimiento/vista rasante.
  Las cámaras21/22 y24 son complementarias, no se confirmó ocultación de fallo.
  Re-verificación:44 tests/exit0/11,514s (`liquid7-rim-targeted.log`), tres
  mutantes de radio/grosor/color compilados correctamente y detenidos por
  aserciones en copias aisladas (`bubble-rim-mutations.json`); fuente canónica
  sin modificar. Triaje `_work/goldfish/gaso-liquid7-scale-verdict.json`.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.

##### Integración de aspecto dinámico (2026-11-13, candidato solo host)

- Objetivo: compensar píxeles no cuadrados sin asumir16:9; sin tocar tanque,
  color/grosor, clips/duración, pins ni settings. No nueva partida/despliegue.
- Descartados márgenes existentes: view_x_margin solo funciona en native-wide2,
  no en squash/stretch1 de liquid7c; x_margin además incluye guards de culling.
- Nueva API de solo lectura `psx_mod_display_pixel_aspect`→
  `gpu_display_pixel_aspect`: ratio físico reducido ancho/alto a partir del
  display vivo, clasificador4:3 y aspecto configurado; native-wide añade columnas.
  Falla cerrado con salidas0 para display ausente/desactivado/depth24, viewport
  local configurado, null/alias y valores inválidos/no representables.
- `patches/psxrecomp-display-pixel-aspect.patch`: gpu.h,mod_plugins.h,gpu.c,
  mod_runtime.cpp, previamente limpios. No incluye main/renderer ajenos. Replay
  desde pin1a3fc0db303adcef9b6999747f90c30fb25da50f coincide normalizado con
  los4 archivos (`framework-aspect-patch-check.json`); reverse-check pasa.
  Primer ensayo dentro de `_work` fue no-op de git apply detectado por bytes;
  ensayo válido fuera del repo en Temp/opencode, no solo por exit0.
- Nuevo `bag2jp_gaso_bubble.h`: ry=floor(r*H/z), rx=floor(ry*den/num), límites
  2..96 antes de narrowing/multiplicación extrema; consulta por dibujo, sin cache.
  Sin macro API, omite burbujas solamente. Comentario ya no promete redondez.
  Header principal cambia6 líneas CRLF por LF, sin normalización global.
- RED API6 aserciones y RED integración7 en3 tests registrados en
  `display-pixel-aspect-red.log`/`bubble-aspect-integration-red.log`.
  Primer GREEN dejó1 fallo de fixture dinámico: la subida cambia centro647→646
  al segundo tick. Expectativa fijada, radios sin relajar; log fallido preservado.
- GREEN49 tests/exit0/16,684s (`bubble-aspect-integration-green2.log`), API17
  escenarios,4:3/16:9/21:9/native-wide, cambio entre ticks, fallback y límites.
  Cuerpos reales de query/API con inputs simulados; **no renderer enlazado ni
  clasificador real en partida**. gpu.c y mod_runtime.cpp completos pasan
  sintaxis gcc/g++ WSL (aspect-gpu-syntax.log/aspect-mod-runtime-syntax.log).
  Mutantes3 plugin+3 API por aserciones, sin errores de compilación contados
  (`bubble-aspect-mutations.json`), más3 radio/grosor/color revalidados
  (`bubble-rim-mutations.json`, reporte actualizado al candidato).
- Goldfish: spec `_work/goldfish/spec-gaso-bubble-aspect.md`,2 revisores en frío
  ses_e2cc8c443ffe3taK7q38QPsUy8 y ses_e2cc8c43fffepP2qMhfT5xinej, veredicto
  **CON HALLAZGOS**. Confirmado/corregido: aspecto configurado inválido era
  aceptado con clasificación4:3; nueva prueba17 falla antes de mover validación
  de positividad fuera de la rama. RED `display-pixel-aspect-native43-invalid-red.log`.
  Final49 tests/exit0/15,521s con18 casos API (`bubble-aspect-integration-final-host.log`).
  Parche final SHA0a25564a1bbb4e8c293ff76a97332098a41a5bdb5661febd58c24ef2e7e337da
  reproducido de nuevo contra el pin; el cambio no altera el target de las
  mutaciones anteriores, que se conservan como evidencia de esa revisión.
- Hallazgo de enlace/staging confirmado y comprobado en costura real: copia de
  ambos headers a build/src con backup `_work/gaso/build-stage-aspect-backup`,
  equality de bytes y hashes protegidos de bag1_versions/caught sin cambiar;
  CAUGHT0 canónico/1 solo build. Build `gaso-bubble-aspect-host-link` PASÓ,
  134,975s/dos jobs, métricas `20261113T044756561876Z-gaso-bubble-aspect-host-link`.
  Exe candidato **solo build**
  `752e21f0d5479217943212e075859bc0c7428d7a31bc9e659962fbdc06bb8246`.
  llvm-nm del objeto bag1_versions tiene `U psx_mod_display_pixel_aspect`;
  el exe define ésta y gpu_display_pixel_aspect (aspect-plugin-references.log,
  aspect-linked-symbols.log). Por tanto el plugin nuevo no quedó en fallback
  compilado sin API. No es prueba de ABI binaria con runtimes viejos: reconstruir
  runtime/plugin juntos; fallback macro solo es compatibilidad de fuente.
- Límites Goldfish: clasificador puede cambiar antes de presentar; aún no prueba
  píxeles finales ni suavidad. Dependencias native-wide preexistentes hacen
  aritmética int para aspectos extremos; alcanzabilidad de configuración inválida
  no demostrada. No se amplía alcance a hardening general ni se promete seguridad
  integral para cualquier positivo. Triaje `gaso-bubble-aspect-verdict.json`.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- No despliegue ni nueva partida; exp-8mb conserva SHAca4a31c6 y stable intacto
  por alcance (sin escrituras). Próximo: **autorización para desplegar el candidato
  en experimental y validar en juego grabado con audio exacto**, con recalibración
  por exe nuevo, comparación BAG1/4:3/16:9 y revisión frame a frame antes de pedir
  conformidad. Salida90 y commit siguen pendientes de permiso explícito.

- Autorización2026-11-13: propietario respondió «continua» a la pregunta explícita
  de desplegar este candidato solo en exp-8mb y validar grabado. Se interpreta
  como permiso para ese despliegue/prueba, **no** commit ni aceptación visual.

##### Validación grabada del aspecto dinámico (2026-11-13)

- Despliegue autorizado completado: exp-8mb ejecuta752e21f0…; backup del exe
  ca4a31c6 y5 archivos protegidos en `_work/gaso/deployment-backup-bubble-aspect`.
  Primer intento se bloqueó por manifest distinto: build f76698be… omite la
  feature CAUGHT; instalado586c8019… coincide exactamente con el canónico. Se
  preservó instalado, sin copiar paquetes. Nuevo helper de `_work` requiere
  hashes de exe/metrics, no sesiones activas, backup nuevo, copia temporal y
  replace final; excepción de manifest exige igualdad canónica.3 pruebas sandbox
  pasan (`aspect-deploy-helper-tests.log`). No se generaliza como tooling aceptado.
- Fallo de ejecución: tras bloqueo, la consola siguió y calibró exe viejo
  (`20261113T064802635528Z-gaso-bubble-aspect-calibration`). **No aceptada/reutilizada**.
  Se añadió fail-fast a invocación. Calibración nueva correcta
  `20261113T065139538691Z-gaso-bubble-aspect-calibration-new`, revisión visual de
  2P/selector aceptada. El catálogo se reutilizó en4:3: mismo exe/controles y
  menú nativo4:3 idéntico; no se reutilizó calibración del exe anterior.
- Toma **ACEPTADA** `gaso-bubble-aspect-heat-bag1`:1705 latidos,1 perdido tarde,
  1 parón68ms trasgf12012 (fuera de ambos ataques inspeccionados), audio0 pares
  descartados/residual p9916,31ms/ventana6,72ms; manifiesto accepted=true.
  Review SHA24efff99c7914d8fd239c80f126d2f2b0ff54173b6a33aaa0234b07a6609ec25.
  No se presenta como captura sin parones ni como conformidad humana.
- Revisión: spawn loggf7190/t2,813, descenso visible~2,862; corte1 loggf7329/
  t5,129, desaparición visible~5,195; salida2 corte visible10,033. Hojas
  onset/clear/release2-consecutive.jpg en `_work/gaso/aspect-review`, revisadas
  fotograma a fotograma. Ambos cortes limpios; caída final slot90 se conserva.
  La latencia visual es~3-4 fotogramas frente a etiquetas en esas fronteras:
  ±2 era estimación no calibrada, no una garantía que estas tomas demuestren.
- Comparación a edad de tanque~1,016s: BAG1 t31,0, liquid7c t3,9 y nuevo t3,83
  (spawns7c2,884/nuevo2,813 según events.json, no resta wall-start de events.csv).
  Burbujas visualmente más redondas y mismas proporciones altas del tanque;
  bordes **aún más definidos que BAG1**, sin promesa de coincidencia exacta.
  phone-proportions.jpg/phone-bubbles.jpg mostradas por read para el móvil.
  Primera hoja recortó mal porque stills son1280×720, no1920×1080; corregida
  con escala medida antes de concluir. Release2 se ordenó numéricamente al
  cruzar9→10s (orden léxico era incorrecto); ampliado crop para seguir cámara.
- Flujo completo16:9: salida de combate160,4s, retorno root13 en170,2s;
  selector visible en170s (`end-flow.jpg`), Gas-O/Heat BAG1 A. No validación
  separada de fever solo/duet; audio subjetivo pendiente de escucha humana.
- Ensayo complementario4:3: wrapper `_work/gaso/run_recorded_native43.py`
  añade override widescreen=false solo dentro de IsolatedFiles, exige backup y
  settings4:3, restaura después. native43/native43b **RECHAZADAS** por audio:
  2557 pares/ventana102,66ms/parón322ms;1129 pares/parones337+43ms. No más
  reintentos ni modificación de gates. Causa concreta de pausas no identificada;
  disco libre435,8GB. **4:3 sigue sin validación de captura aceptada**.
- 5 archivos protegidos (settings,keybinds,input,game_options,state) coinciden
  con sus hashes previos al despliegue; restablecimiento de tarjetas originales
  verificado por harness en todas las sesiones (125/127/129 saves según run).
  Stable no se tocó. Fuentes canónicas guard0, sin commit ni nueva aceptación.
- Evidencia consolidada `_work/gaso/aspect-runtime-review.json`; vídeo exacto:
  `_work/recordings/gaso-bubble-aspect-heat-bag1/owner.mp4`. Herramientas:
  Ghidra MCP identidad/8002c404, grabador+FFmpeg look/frames+Pillow usados;
  funcmatch no aplica (no matching MIPS), modelos locales omitidos en extracción
  determinista pequeña. Goldfish de producción reutilizado (sin cambio en
  runtime/plugin); auxiliares nuevos solo `_work` exentos por lista cerrada.
- Próximo: conformidad del propietario **solo sobre este aspecto16:9** con
  diferencia de borde declarada.4:3, slot90 y commit continúan pendientes; no
  interpretar una respuesta sobre aspecto como autorización de commit.

##### Líquido aditivo más traslúcido (2026-11-13, candidato solo host+build)

- Petición del propietario tras ver phone-bubbles/proportions: líquido verde «un
  poco más traslúcido», como BAG1. Simulación `_work/gaso/aspect-review/
  phone-translucency-sim.jpg` mostrada y aprobada con «Okay continúa» (permiso
  para cambio y pruebas host; **no** despliegue, partida ni commit).
- Medición (`translucency-sim.json`): dispersión p90-p10 R por tercio BAG1
  118/90/71 frente a BAG2 actual 55/59/48. ABR0 fija peso de fondo0,5; la PS1 no
  ofrece valor entre0,5 y1,0. Invertido ABR0 sobre new-frame.png (error medio
  0,384) y simulado tinte aditivo: 108/119/81, medianas por tercio conservadas.
- Cambio `bag2jp_gaso_tank.h`: vidrio 0x3A bajo ABR1 con `GASO_GLASS_RGB`
  0x051206 y el mismo sombreado lateral; orden GPU E1 aditivo, tinte, anillos,
  destellos, metal, E1 0x600 (siempre, ya no condicionado a burbujas). Se aparta
  a propósito del modo promedio nativo de BAG1 (comentado en el código).
- Pruebas: harness exige ningún 0x3A en ABR0, tinte en límites literales, E1
  completo 0x620/0x600 y degradado izquierda>derecha. RED10 fallos
  (`liquid-additive-red.log`); GREEN49 tests (`liquid-additive-green2.log`).
  Mutantes7/7 muertos (`liquid-additive-mutations.json`).
- Goldfish: `_work/goldfish/spec-gaso-liquid-additive.md`, 2 revisores, **CON
  HALLAZGOS** sin defectos bloqueantes; triados en
  `_work/goldfish/gaso-liquid-additive-verdict.json` (pruebas de degradado/E1,
  datos de evidencia, comentario x1.125). Solapes de burbujas y saturación del
  destello quedan para la revisión grabada.
- Build `gaso-liquid-additive` pasó en 34,7s, exe
  7dfebd76338bdd3be14d2367ea48cba4550733d309fc6f4f323e16f61fbf5ac7. Header
  staged con backup `_work/gaso/build-stage-liquid-backup`; build guard1.
  exp-8mb sigue en752e21f0. **No desplegado.**
- Autorización «Si, continúa» (2026-11-13) para desplegar 7dfebd76 en exp-8mb y
  grabar. Desplegado con `deploy_verified_exe.py` (backup
  `_work/gaso/deployment-backup-liquid-additive`, manifest canónico preservado).
  Calibración `20261113T075551784541Z-gaso-liquid-additive-calibration` aceptada.
- Tomas `gaso-liquid-additive{,-b}-heat-bag1` **RECHAZADAS** por audio (989 y
  1169 pares); parones del juego de 301ms en gf7992 y 253ms en gf16026. El flujo
  terminó (selector a los 170s) y la restauración se verificó; los 5 archivos
  protegidos están intactos. Los fotogramas siguen continuos en el trace: la
  emulación se congela en tiempo real. No es atribuible al cambio: hay parones
  ≥200ms en ~7968-7998 y ~12006-12012 desde liquid4/5/7 y native43, con exes
  distintos. Hipótesis sin probar: `b1m_filter` (`bag2jp_bag1_stage.c:204-222`)
  lee el FLAC de BAG1 con fread/drflac_seek en el callback XA; un seek por
  desajuste del cursor podría bloquear. Fotograma orientativo de la toma b
  (`phone-liquid-additive.jpg`, t3,899): visualmente cerca de BAG1. **No es
  validación.**
- Diagnóstico del parón (owner «Okay continúa», opción 1): `b1m_filter` registra,
  solo con `BAG2JP_TEST_B1M_TIMING=1`, los seeks y las lecturas FLAC ≥5ms con hora
  UTC. Pruebas `test_bag1_stage_audio` 5/5; el arnés no definía
  `b1s_is_gaso_bag1` (fallo previo en el árbol de trabajo): se añadió un stub y
  el caso «stage 9 stock → sin sustitución». Mutantes 3/3. Goldfish
  `spec-b1m-timing-diagnostic.md`: CON HALLAZGOS no bloqueantes; se añadió el
  flag `open=` y la cobertura del stub. Pendiente separar en el commit los demás
  cambios sin confirmar de stage.c. Build `b1m-timing-diagnostic-2`, exe 23015cb8
  (incluye el líquido), desplegado con backup `deployment-backup-b1m-timing`.
  Calibración `20261113T082744116114Z` aceptada.
- Toma `gaso-b1m-timing-heat-bag1` **ACEPTADA**: 1706 latidos, 5 tardíos, 1
  parón de 132ms en gf12012, 10 pares descartados (dentro del gate). **Pero el
  diagnóstico no se activó**: `versus_session.py:144-147` filtra las variables
  `BAG2JP_*` salvo una lista fija. Sin líneas de tiempos; la hipótesis FLAC
  sigue sin probar.
- Revisión de la toma aceptada (líquido aditivo): spawn gf7148/t2,828, tanque
  visible ~2,905 (cae) y completo ~2,951. Corte 1 en log t5,146, visible 5,203,
  limpio. Corte 2 tras restore t9,848, visible ~10,054, limpio. Selector a los
  170s. Hojas `b1m-onset/clear/release2.jpg` y comparación
  `phone-liquid-accepted.jpg` (t3,844, edad ~1,016s): el rival se ve con
  contraste completo bajo un tinte verde, cerca de BAG1. Las burbujas mantienen
  el borde más nítido que BAG1. Los 5 archivos protegidos están intactos.
- Herramientas: Ghidra MCP ya verificado esta sesión (SLPM_862.19); no se
  consultó de nuevo porque el cambio es solo el modo de mezcla del plugin, sin
  código MIPS. funcmatch/modelos locales no aplican; Pillow/numpy para medir.
- Próximo: conformidad del propietario sobre el líquido (16:9). Para el parón:
  añadir `BAG2JP_TEST_B1M_TIMING` a la allowlist de `versus_session.py`
  (tools/**, con Goldfish) y repetir la toma con la variable. 4:3, slot90 y
  commit siguen pendientes.

##### Deslizamiento del rival atrapado (2026-11-13, solo investigación)

- Owner: Heat atrapado se desliza a la izquierda; debería quedarse quieto.
- Evidencia de vídeo (toma aceptada `gaso-b1m-timing-heat-bag1`,
  `_work/gaso/slide/slide-grid.jpg`, `after-grid.jpg`): el tanque con Heat se
  acerca a Gas-O de forma continua desde 3,5s; a los 10,5s Heat cae junto a
  Gas-O y a los 12s ya está de nuevo en su sitio. Spawn X 513 → 311 entre
  capturas. Referencia BAG1 (`bag1/bag1-grid.jpg`, 29,5-34,5s): el rival
  queda en una pose fija y no se mueve.
- Descartado: el clip CAUGHT publicado no lleva traslación. Los 3 clips del
  banco (`b1cc_data`, 2 fotogramas) tienen raíz constante
  (`motion_codec.decode`).
- Trace: Heat vuelve a bailar dentro del tanque (P2 anim 49 → 2 → 7), y Gas-O
  sigue en anim 78. Ghidra: `FUN_8002ccc8` re-ancla la base `+0x14b8/+0x14c0` a
  `root(+0x810) - traslación/2` en cada cambio de animación. Capstone: la
  función 0x8002a090..0x8002b5bc (sin definir en Ghidra) recoloca a la pareja
  en los estados 10/14. Ahí la base del otro bailarín se interpola
  (`0x800436e4`, peso `+0x1546`) hacia la del atacante más `±0x154 ×
  escala`, y su `+0x810` se copia relativo al atacante.
- Hipótesis, sin prueba en tiempo de ejecución: la lógica de pareja/pasos de
  BAG2 sigue moviendo al rival mientras está atrapado. Falta un registro por
  fotograma de base, raíz, estado `+4` y anim de ambos bailarines durante la
  captura; eso exige una partida autorizada.
- Arreglo propuesto, no implementado: mientras el tanque retiene al rival,
  fijar la base al valor del spawn y, opcionalmente, mantener la pose CAUGHT
  como BAG1. Primero pruebas de host.

###### Corrección del diagnóstico y candidato de anclaje (2026-11-13)

- Autorización: «okay cotninua» y posteriores «Continua» para el diagnóstico
  grabado y el arreglo propuesto. No autoriza commit ni implica conformidad.
- **Corrige la explicación anterior:** el reloj nativo `800892EC` no es el
  contador global `fNNNNNN` del watch/recorder. Al alinearlos correctamente,
  Heat permanece en anim1 durante la captura, no vuelve a bailar. `actor+4`
  es ID de personaje (Heat=0), **no estado de animación**. La hipótesis de
  recolocación de pareja no quedó acreditada. Los clips tienen raíz constante,
  pero no nula: Heat (20,1443,-17), según el decoder.
- Diagnóstico `20261113T085539682518Z-gaso-slide-diag-heat-bag1`: la toma fue
  **RECHAZADA** por jitter/audio; sus datos RAM son diagnósticos, no validación
  audiovisual. Tabla corregida `_work/gaso/slide/heat-table-f.txt`: raíz X
  513→99 entre f7593 y f8008. Cada reinicio de la pose de dos fotogramas
  vuelve a iniciar la mezcla (peso 0x500) y desplaza la base aproximadamente
  cuatro unidades. Ghidra MCP `FUN_8002ccc8` confirma el reanclaje desde raíz
  mezclada menos traslación decodificada. La pose constante no evita ese bucle.
- Harness: `versus_session.py --watch-extra ADDR:SIZE,...` permite columnas
  diagnósticas, valida RAM/alineación/solapamientos y rechaza >32 watches antes
  de crear el run. La allowlist incluye `BAG2JP_TEST_B1M_TIMING`. 54 pruebas
  host y 8 mutantes válidos en `watch-extra-green2.log`/`mutations2.json`.
  El primer intento de mutantes estaba contaminado por un error del test de
  sys.argv: no cuenta. Goldfish anterior CON HALLAZGOS; duplicados/límite
  temprano corregidos. Los cambios ajenos contra HEAD quedan fuera de alcance.
  Tras la corrección, la falta de líneas de tiempos no demuestra por sí sola
  que el diagnóstico siga inerte: también puede no haber seeks/lecturas lentas.
- Candidato: `gaso_caught_hold` fija base X/Z mientras la anim1 pertenece a
  nuestra publicación. Independiente de la vida del tanque, no modifica altura
  ni slot90; libera el ancla al perder ownership/slot o reset/epoch. Guard0
  canónico permanece intacto. RED 1/29 en `hold-red.log`; GREEN ampliado
  56/56 en `hold-review-green.log`; siete mutantes históricos y otros tres
  de los huecos del review detectados por assertions (`hold-review-mutations.json`).
- Goldfish: primer revisor agotó cuota sin resultado (no cuenta); dos revisores
  nuevos CON HALLAZGOS, sin defecto bloqueante confirmado. Se añadieron pruebas
  para ambos lados, reemplazo con ownership válido, epoch con ancla activa y
  republicación. Persistido en `_work/goldfish/gaso-caught-hold-verdict.json`.
  **Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.**
- Build `gaso-caught-hold`: exe
  `5ab1082ed4cf79298dfa881b74e8e4ba65a4776efd629b2c8179402abe89412c`,
  staged con backup `build-stage-hold-backup`, desplegado solo a exp-8mb;
  backup `deployment-backup-gaso-caught-hold` conserva 23015cb8. Manifiesto
  canónico preservado, paquetes sin cambios. Calibración revisada/aceptada
  `20261113T091527203162Z-gaso-hold-calibration`.
- Toma **ACEPTADA** `gaso-caught-hold-heat-bag1`, run
  `20261113T091728443684Z`: 1706 latidos, 3 tardíos, p99 14ms, un parón de
  42ms en f12006, cero pares de audio descartados. 419 fotogramas en anim1:
  raíz X 513→503 inicialmente; después oscila 503/505, Z=97 constante.
  **Elimina la deriva acumulativa, no toda oscilación.** No declarar inmovilidad
  exacta ni aceptación definitiva. P1/P2 verificados por punteros en el watch.
- Revisión propia: caída 2,898–2,982s; corte primero 5,249s; segunda caída
  6,298–6,366s; caída final desde ~9,905s, tanque desaparece ~10,020s sin
  residuos. Hojas `hold-frames-{7244,7383,7448,7664,7678}.jpg`, de un fotograma
  por muestra; vista general `hold-contact.jpg`. Selector a 170s. Restauración
  verificada de ajustes y 145 saves originales; cinco hashes protegidos iguales.
- Vídeo corto: `_work/gaso/slide/gaso-hold-attacks.mp4` (1,5–12,5s del owner).
  Completo: `_work/recordings/gaso-caught-hold-heat-bag1/owner.mp4`.
  Latencia pantalla/log sin calibrar (±2 fotogramas solo estimación); juicio
  subjetivo de audio pendiente de humano. No nueva prueba 4:3 ni fever.
- Siguiente: eliminar la mezcla/reanclaje residual de la pose en el seam nativo
  sin fijar huesos/raíz después del render; primero regresión host. Candidato
  desplegado queda experimental. Conformidad del líquido, slot90 y commit
  pendientes. No snapshot nuevo: no se cerró un hito de aceptación.
- Herramientas: Ghidra MCP obligatorio usado y verificado en SLPM_862.19
  ea5a1668; recorder/FFmpeg y harness local usados. funcmatch no aplica (no se
  buscan equivalentes BAG1); modelos locales no aportan al razonamiento de
  orden/blending y no se cargan durante la prueba GPU. bag2_run/report/shots no
  se repiten: wrapper seguro existente y frames del recorder cubren este seam.

###### Pose con clamp nativo: sin oscilación periódica (2026-11-13)

- Autorizado por «Okay continúa». Metadata+5=1 conserva el último fotograma;
  +5=0 envuelve y causa reanclaje periódico. MCP confirmó SLPM_862.19 ea5a1668
  y32 bytes en8002d06c; decompile directo FUNCTION_NOT_FOUND. Se reutilizó el
  headless existente, contrastado con bytes/SHA143b4bf8, sin modificar Ghidra.
- Ensayo `_work/gaso/slide/run_clamped_controller.py`, WSL, trials
  `clamp-native-1`/`clamp-native-rehit`: MIPS original con intérprete real,
  callees raíz/render observados, NO ejecutados.200ticks: original101
  reanclajes/peso1280; clamp1 reanclaje inicial/peso4096/frame1. Re-hit añade1
  reanclaje explícito; otros200ticks sin bucle. Pedido de salida90 funciona.
- Generador mantiene extracción/hashes originales; modifica una copia solo en
  metadata+5 (tres bytes en banco; mismas poses/tamaños/offsets/eventos). Binding
  exige1 y rechaza banco looping, sin ampliar autorización de escritura/retiro.
  Fixtures actualizados. Se retiraron únicamente pin/estado/caller/constantes
  privados añadidos por esta tarea; candidato anterior respaldado. Dos tests
  ahora exigen que el visual no sobrescriba coordenadas, incluso ante reemplazo,
  ambos lados, epoch y republicación. No se borró trabajo previo ajeno.
- RED banco3fallos/perfil (`clamp-red.log`), RED no-pin2fallos
  (`clamp-no-pin-red.log`); GREEN **122 tests dirigidos**, no suite global,
  `clamp-host-green.log` (bank/binding/owned/adapter/loan/runtime/tank/bubble/
  aspect/audio/codec). Generador `--check` pasa.
- Goldfish2 revisores CON HALLAZGOS sin bloqueante confirmado. Faltaba re-hit y
  render real: se añadieron al ensayo/toma; re-hit resultó un límite real.
  `_work/goldfish/gaso-clamp-last-verdict.json`.
  **Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.**
- Build `gaso-clamp-last` pasa32,34s, exe
  `e165817cf49e83a246b8157cba299e2382307f206ea39057175e19933b350c49`.
  Warning de flag `-Wa,-mbig-obj` no usado, no atribuido al arreglo. Staging
  binding/banco/tank en `build-stage-clamp-backup`. Deploy exe-only exp-8mb,
  manifiesto preservado, backup5ab1082e `deployment-backup-gaso-clamp-last`.
  Calibración `20261113T094443009320Z-gaso-clamp-calibration` revisada/aceptada.
- Toma **ACEPTADA** `gaso-clamp-last-heat-bag1`, run
  `20261113T094636858580Z`:1706latidos/1tardío/p99 13,4ms/0parones/0pares audio
  descartados.420filas anim1 f7233..7652. Tras mezcla inicial, f7255..7436 raíz
  exactamente(511,100), base(505,106), peso4096/frame1; después del segundo golpe,
  f7459..7652 raíz(507,103), base(501,109), peso4096/frame1. **Sin oscilación ni
  deriva entre golpes; re-hit recoloca(-4,+3).** Rangos con transiciones:
  X505..513/Z97..103. Inmovilidad exacta de toda la secuencia NO aceptada.
- El primer helper lanzó assertion al exigir peso4096 durante la nueva entrada
  del re-hit: no fue rechazo del grabador. Se separaron episodios y se muestran
  rangos completos/estables en `gaso-clamp-last-heat-bag1-summary.json`, sin
  ocultar el cambio entre golpes ni modificar gates.
- Revisión de17frames por hoja: caída~2,820..2,888s, corte~5,152s, segunda caída
  ~6,227..6,288s; salida90~9,840s, tanque fuera~10,006s. Hojas
  `clamp-frames-{7232,7372,7436,7653,7668}.jpg`/`clamp-contact.jpg`. Selector170s;
  ajustes/149saves restaurados,5hashes protegidos iguales, staged3archivos igual
  al canónico. Guard0 sigue intacto. Audio subjetivo/4:3/fever sin nueva aceptación;
  latencia ±2frames solo estimación. Vídeo `_work/gaso/slide/gaso-clamp-attacks.mp4`
  (1,5..12,5s); completo `_work/recordings/gaso-clamp-last-heat-bag1/owner.mp4`.
- Siguiente: investigar reentrada explícita sobre CAUGHT ya activo sin tocar
  timers. Caller8002a090 renueva duración en controlador+44 antes del entry;
  modo1 reinicia pose/reanclaje aunque sea el mismo clip. Evaluar preservación
  solo tras VERIFY de publicación viva, con regresión de duración/velocidad/
  salida90; **no cambiar de modo sin esa prueba**. Investigación interna
  autorizada; no commit, aceptación definitiva ni snapshot nuevo.

###### Reentrada compatible: candidato host, sin aceptación (2026-11-13)

- Objetivo: evitar el reanclaje del segundo golpe sin tocar timers. Ghidra
  (SLPM_862.19 ea5a1668): el modo1 de8002d06c fija frame0, reinicia mezcla,
  copia param5 en +1c/+20, limpia +0a/+0b, copia el frame en +24 y llama a
  entry8003190c solo si byte+0d==0; el modo0 avanza sin reanclar. El caller
  8002a090 renueva +44 y pasa -0x8000000.
- Cambio acotado en `gaso_caught_can_continue`: solo tras VERIFY de una
  publicación viva, misma identidad/clip, slot1 actual y anterior, frame1,
  mezcla4096, cap a3=4096, velocidad fija idéntica en stack/controlador,
  rate=-speed, tick=-1, +0a=+0b=0 y +24=0 (lo que modo1 escribe). Entonces a1 1→0; a2 sigue
  redirigiendo a slot1. Entrada inicial, ambos lados y todo rechazo conservan
  modo1. Span del controlador 0x24→0x28. Guard0 canónico intacto; no hay
  escrituras a actor, controlador ni pending+18.
- Diferencia conocida, no ocultada: modo0 no reinicia +10 (acumulador
  sub-frame), ni +20 (contador que desciende en cada llamada), ni ejecuta
  los callbacks de entrada 8003190c (incluido el cue nativo de Gas-O 0x782).
  El
  ensayo MIPS original (`probe_continue_controller.c`) demuestra 10 avances
  compatibles: sin reanclaje extra, frame1/mezcla4096, rate y velocidad
  intactos, +20 descontando, +44 conservado y salida90 explícita; los callees
  de render/raíz solo se observan, no se ejecutan.
- Evidencia host: **125 tests dirigidos** verdes (`rehit-host-green5.log`);
  13/13 mutantes muertos por aserción (`rehit-mutations.json`), incluidos los
  tres guardas nuevos. Escenario17 aísla identidad, lookup BAG1 y VERIFY;
  escenario18 repite el avance en el lado espejo. Los 2 revisores Goldfish
  previos dieron hallazgos P2 (callbacks/timers y cobertura) ya atendidos aquí;
  revisión delta en curso.
- Build `gaso-rehit-preserve` (exe `c330ef1b…`, 31,4s) se hizo **antes** de los
  tres guardas nuevos: quedó obsoleto y no se desplegó. exp-8mb sigue con
  `e165817c` (sin candidato). Antes de cualquier toma hay que reconstruir.
- Revisión Goldfish delta (2026-11-13): el revisor detectó que modo1
  escribe +24=0, no 1; la guarda se corrigió a +24=0 (GASO_CAUGHT_ENTRY_FRAME_COPY).
  También exigió declarar +10 y el cue 0x782, ya incorporados arriba.
  El span 0x28 no introduce lectura insegura. Escenario17 aísla identidad,
  lookup BAG1 y el contrato de RAM; su mutante compuesto (ignore_reuse_contract)
  mata la prueba. 14/14 mutantes muertos.
- Límite: el escritor de 0x810 no está identificado: en el main exe solo hay
  dos stores (bloque de char 0x0a en8002b320 y spawn en8002d934), ninguno
  aplicable, y tampoco aparece en el overlay de Heat ni en el payload. La toma
  mostró -2 en X al entrar y -2 durante la mezcla, con ancla -4/+3. Modo0 evita
  el reanclaje, pero un salto residual de 2 unidades solo se mide en juego.
- Siguiente: desplegar solo con autorización del propietario y grabar el
  segundo golpe con watch de controlador +0a/+0b/+20/+24 y de 0x810/0x14b8;
  sin esa grabación no hay conformidad ni commit.

###### Reentrada modo0 en juego: sin salto, pero cambia el audio (2026-11-13)

- Autorizado por «continúa» tras pedir build/despliegue/toma. Build
  `gaso-rehit-mode0` 35,9s, exe `18590587d44e20eee729d9bd8b15ed54eda8ec6bd9d65d7320ce79cb8035e85f`
  (staging: solo override CLIP_PUBLISHED=1; deriva previa de `bag1_versions.c`
  ya existía en el build del clamp y no se tocó). Deploy exe-only en exp-8mb;
  backup `e165817c` en `_work/gaso/deployment-backup-gaso-rehit-mode0/`.
- `settings.toml` de exp-8mb apuntaba a tarjetas de `gaso-fix5` (escrito 1s
  tras cerrar el juego de la toma del clamp, después de la restauración
  verificada). Se restauró el baseline `2ac29271…` de esa toma; copia del
  estado anterior `settings.toml.stale-b41a5fc8`. Tras las tres corridas sigue
  `2ac29271…`; 149 saves verificados.
- Calibración `20261113T130247604851Z-gaso-rehit-calibration`: 9 capturas de
  aristas revisadas (`rehit-calibration-sheet.jpg`) y aceptada.
- Corrida 1 sin `BAG2JP_TEST_GASO_ATTACK=1`: no hubo ataque; grabación
  RECHAZADA (el juego cerró antes del STOP). Corrida r2 con fixture: RAM válida
  pero grabación RECHAZADA (orden Z durante menús). r3: grabador iniciado 15s
  tras `stage-selected.png` y STOP al capturar `returned-selector.png`
  (`_work/gaso/slide/stop_on_selector.ps1`): **ACEPTADA**, 1595 latidos,
  0 parones, 0 pares de audio descartados, p99 12,4ms.
- RAM r2 y r3 idénticas (`rehit-watch-r3.txt`): primer golpe f7226 (modo1
  nativo, mezcla 1280→4096); re-hit f7430: +44 13→216 y +20 sigue
  descontando (f7ffff36→f7ffff34) = **modo0 activo**. f7248..7644: raíz
  (511,100), base (505,106), mezcla 4096, frame1, +08 word 0x100 (+0a/+0b=0),
  +24=0, rate/speed/tick intactos. Salida90 natural f7645 al agotarse +44.
- Vídeo: re-hit 12,04..12,30s sin cambio de pose/posición mientras cae el
  tanque (`r3-heat-7430.jpg`); salida 15,62..15,89s normal (`r3-heat-7645.jpg`).
  Canción terminada (144,7s) y vuelta al selector observadas.
- **Hallazgo de audio** (`compare_rehit_audio.py`, `rehit-audio-*.txt/json`):
  dumps alineados por frame contra la toma del clamp (re-hit en modo1). Primer
  golpe (modo1 en ambas): diferencia <= -32 dB en toda la ventana. Re-hit: igual
  hasta +36 frames, luego contenido distinto de +42 a ~+130 frames (0,7-2,2s),
  sin desfase temporal (lag 0) y con modo1 hasta ~18 dB más fuerte: **modo0
  omite un sonido nativo del re-hit**, coherente con los callbacks 8003190c
  omitidos. Identidad exacta del sonido sin verificar; juicio subjetivo pendiente
  del propietario: `_work/gaso/slide/rehit-ab-native-vs-mode0.mp4` (4s modo1,
  luego 4s modo0). Corte de ataques `gaso-rehit-mode0-attacks.mp4`; completo
  `_work/recordings/gaso-rehit-mode0-heat-bag1-r3/owner.mp4`.
- Nuevo en r3: dos `request 202 s2=1 -> s4=1 rejected: reflected` (f8966,
  f13170), rechazo por diseño de la captura; esa lógica no cambió.
- Límites: ±2 frames estimado; no se midió 4:3; escritor de 0x810 sigue sin
  identificar (en r3 no se movió). Sin commit ni conformidad.
- Siguiente: decisión del propietario entre (a) aceptar modo0 sin ese sonido,
  (b) volver a modo1 y aceptar el salto, o (c) investigar qué sonido emite
  8003190c en la reentrada para conservarlo sin reanclaje.

## Plan A-E aprobado y nombre HUD candidato (2026-11-13)

El propietario aprobó A sonido, B nombre del marcador, C ventilador, D cámaras,
E eventos por puntaje. Precisó D dos veces: **importar el movimiento de cámaras
del escenario de Gas-O de BAG1 únicamente, manteniendo la distancia de BAG2**;
no basta suavizar la intro actual y no se cambian los demás escenarios.
La investigación sigue sin otra autorización; despliegue/partida grabada y commit
mantienen sus permisos separados. No sigue abierto el antiguo gate de elegir A/B/C
del sonido: se aprobó investigarlo y corregirlo.

- **A, WIP previo, no cerrado:** se añadió cola/reproducción de cues rebased
  6906/690a. Host54 y build872e6753 pasaron; no desplegado ni Goldfish del audio.
  El reemplazo del pulso nativo por cambio de beat y su temporización aún requieren
  contraste: no se declaran fidelidad ni sonido correcto. Sigue el resampling de
  muestras documentado en la auditoría del audio. Re-hit sin resolver.
- **Corrección de lectura:** 8003190c es un dispatcher de eventos del actor,
  no el reproductor de sonido. En 8002d06c los códigos 779/782 se envían solo
  si el actor receptor es char9. Heat (char0) recibe1/4/12d/3e9 en esa entrada.
  Por tanto, las menciones anteriores a «cue782 perdido en Heat» no prueban la
  identidad del sonido que falta. No reproducir782 como si fuera un cue de audio.
- **B, causa comprobada:** el primer intento draw_gaso_label solo pasó
  py_compile; al ejecutarlo falló NameError(parse). También infería el recuadro
  desde todos los píxeles blancos y escribía en ambas texturas: no era seguro.
  Sustituido por transferencia 4bpp compartida, sin fuente inventada/PIL/numpy en
  producción. El arte nativo sí existe en member5: USA100x17, JP116x17,
  idéntico entre ambos trajes/lados dentro de cada región.
- HUD nativo: overlay005 SHA bc5f3045084e4b3e19009910441627977863c8b5791b5cdb716a766e68b28fb2,
  payload base8008f890 tras quitar12bytes. FUN80093de0 consume descriptor de
  6bytes: u/v/width/height y u16 índice de textura. Para char9 ambos trajes,
  8009e6d6/8009e742 = `20 70 2d 07 01 00`: recuadro[32,112,77,119), body2.
  Perfil gaso.json guarda los rectángulos; body1 no se modifica. Se reduce el
  arte regional por vecino más cercano centrado y se remapean sus índices a la
  fila gris stock preservando cero transparente/negro no cero.
- Pruebas: RED de funciones ausentes; GREEN12 en0,217s
  (`_work/gaso/hud/label-final-green.log`), 8 combinaciones USA/JP×A/B×P1/P2,
  formatos/truncamientos/nibbles/transparencia y píxeles exteriores intactos.
  Cinco mutantes terminan por aserción (`label-mutations.json`), no por error de
  importación. Builder real:18 contenedores, solo cambia member3(P1)/2(P2) de
  los packs, resto byte-idéntico frente al mismo builder sin la copia del nombre.
  Rebuild tras corregir formatos produce los mismos18 bytes de candidatos:
  `_work/gaso/hud/final-build/report.json`; hashes finales de fuentes/tests en
  `final-source-hashes.json`. Preview `label-preview.png`: stock/USA/JP.
- **Goldfish B:** 2 revisores, CON HALLAZGOS. Longitud declarada del bloque
  podía superar el archivo aunque el slice tuviera suficientes píxeles:
  confirmado, regresión RED2 fallos y corregido (12tests finales verdes).
  Segundo hallazgo, no verificable aquí: HUD selecciona CLUT compartida, no la
  CLUT corporal. La correspondencia RGB/orden de esa CLUT con la referencia
  usada por el remapeo queda pendiente; el preview NO la demuestra. No cerrar
  colores ni legibilidad hasta comprobar la CLUT efectiva/partida grabada.
  Registro `_work/goldfish/gaso-hud-label-verdict.json`; hash final del copiador
  db5a7a02f89f48703aff4888f5df27758451ed1d93fd0d3f551f8d6908d06a7d.
  **Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.**
- Herramientas: MCP main confirmado y consumidor overlay complementado en
  headless, trial HUD en ghidra-psx-psyq.md; decodificación MIPS Capstone y
  omisión motivada TIMedit en sus logs. No nuevo juego/video ni copia a paquetes
  instalados. exp sigue18590587; candidato de audio build872e6753 separado.
- **Siguiente unidad C:** revisar el parche801E2448 y update801E22C8 del
  perfil de escenario gaso.json contra BAG1 nativo antes de ajustar velocidad.
  D/E siguen pendientes; A/B quedan candidatos sin aceptación. No commit/snapshot.

## C: ventilador, divisor y lectura del nivel corregidos offline (2026-11-13)

- Objetivo/check: recuperar el cálculo original del giro y su dependencia del
  nivel de puntaje, sin tocar cámaras/geometría/otros eventos. Se conserva todo
  como candidato offline; no hay permiso implícito de despliegue/partida/commit.
- BAG1 USA ST_GAS member0 SHA
  0d3a49731d5d44f62e108ce925aa37fafc044896a3e7ce5ab80f1efdc430a320:
  update801E22C8 multiplica speed801E5562 por delta800774E8 y divide entre16
  (SRA v1,v1,4 en801E2448, word00031903), con redondeo signed hacia cero,
  acumulación u16 en801E5560 y propagación de la matriz a nodos12..15.
  Los topes son80 para nivel1 y200 para nivel2; la rampa incrementa por update.
  JP STAGE/ST_GAS member0 SHA
  fdb6129c1aeba87c94116c6c27c1f2c94cfd6e55bed989b3604e8f5930222356
  usa SRA a0,v1,4 en offset de archivoCB8. No se le asignó la VA de USA.
- El perfil portado alteraba la división a2 (00031843), conservando el mapeo
  de delta a8006D994: en velocidades asentadas el avance de la fórmula es8x.
  **No es una medición de RPM ni de cadencia efectiva.** Se sustituye ese
  override por guard/no-op00031903→00031903 para rechazar drift de entrada.
- RED inicial: dos fallos de4tests (`_work/gaso/hud/fan-red.log`); primer
  candidato d5a9f702 conservaba solo la división nativa,20tests verdes,
  dos bytes distintos. **Ese candidato queda incompleto, no usar para deploy.**
- Goldfish2 revisores, CON HALLAZGOS: reveló un fallo previo que los tests
  de constantes no cubrían. Al entrar por nivel1, el LUI801E23E0 quedaba8007;
  el LB común, ya reubicado a offset0108, leía80070108 en vez del shim801E0108.
  Ruta tomada tenía otro LUI correcto en el delay slot801E23C0. Confirmado en
  decompile/MIPS generado; no es un efecto del divisor ni una hipótesis visual.
- Corrección acotada en el perfil: patch guardado801E23E0,
  3C028007→3C02801E. Excepción concreta de reubicación en este perfil, sin
  cambiar el motor compartido para todos los personajes. Si se corrige el
  tracking de flujo general, este guard obliga a revisar/eliminar el adaptador.
  No se afirmó que se hubiera auditado toda la reubicación del escenario.
- Nuevo RED para las dos rutas: un fallo (`level-path-red.log`); GREEN final
  **21tests** de stage_port/stage_geometry/gaso_stage_fan, sin cambio de criterios
  de aceptación. Guard de divisor y de LUI probado con fuente alterada.
  `test_gaso_stage_fan.py` ejecuta el generador real, no otro motor de giro.
- Prueba independiente con intérprete PSXRecomp instalado:
  `wsl.exe -d Ubuntu --exec python3 /mnt/d/Dev/Recomp/BAG2JP/_work/gaso/stage-fan/run_interpreter_probe.py`.
  Ejecuta instrucciones originales y portadas del tramo de update, sin render
  ni llamadas externas:144casos por variante (niveles0/1/2,8 velocidades,
  deltas-1..4 y wrap u16). RAM80070108 envenenada con2 para exponer el fallo.
  Nativo coincide con fórmula/topes; port anterior NO; candidato final coincide.
  3,122s compilación/ejecución, hashes/código en `stage-fan/interpreter/report.json`.
  No demuestra FPS reales ni ejecución completa del escenario.
- Candidato final `stage-fan/candidate-v2/stage197.dfs` SHA
  00d613392023b33655dfce425cfda0f6a7cbd536e17a74bbadd6776a7f7d02e6,
  514396bytes. Contra el generador previo a C (baseline0a994860) solo cambian
  **3bytes en2 instrucciones del member0**. Los otros12miembros y demás bytes
  del DBI son idénticos: conserva cartel GAS/cámaras/geometría/audio.
  No se repaquetó payload ni se tocó manifiesto o instalación; exp sigue18590587.
- Goldfish registro `_work/goldfish/gaso-stage-fan-verdict.json`. La objeción
  de comparar solo un slice se contrasta además con el contenedor entero y el
  intérprete; la cadencia/RPM queda no verificable sin prueba real.
  **Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.**
- Herramientas: Ghidra MCP main JP + headless de ambos updates, Capstone y
  producción-interpreter; logs por herramienta. Unicorn no está instalado en
  Python Windows (ModuleNotFoundError); no se instaló, se reutilizó el intérprete
  disponible. No se ejecutó funcmatch: aquí se compara overlay, no equivalentes
  de funciones main BAG1→BAG2. Tiempo/manual/ahorro global desconocidos.
- Siguiente **D**: inventariar movimiento de cámaras específico de Gas-O BAG1
  (intro y baile, dónde están sus tablas/control) y definir la adaptación que
  conserve la distancia BAG2, no copiar acercamientos nativos ni tocar otros
  escenarios. El punto E debe incluir la lectura correcta del shim por todas
  las rutas: el hallazgo C no certifica el resto de eventos. A/B siguen WIP.

## D: cámara del escenario Gas-O BAG1 con distancia BAG2 (2026-11-13, candidato offline)

- Objetivo/check: importar el movimiento de cámara de Gas-O BAG1 (intro member6,
  150 claves) en stock track 0, escalando posiciones (no ángulos) a distancia
  BAG2. No se cambian los demás escenarios. Se conserva como candidato offline;
  no hay permiso implícito de despliegue/partida/commit.
- Inventario (inventario-v2.json):
  - GASO USA member6: 1 track, 150 claves, radio 8479→4864 (BAG1, más cercano).
  - GASO JP member6: idéntico a USA (mismo SHA 99b04764…).
  - Common banks G_COMM_E/G_COMMON: 21 tracks cada uno (baile compartido).
  - Stock 012.bin: track 0 intro (165 claves, radio 16429→3869, BAG2 distance);
    tracks 1-27 baile (radio ~1000-3500, BAG2 distance).
- build_stage_package.py: tras construir/remuestrear la cámara (cam_speed=2.1,
  150→165 claves), escala componentes X/Y/Z de cada clave por camera_scale.
  Ángulos (índices 3-5) sin cambios. camera_scale=1.0 = sin escalado (identidad).
- gaso.json: `"camera_scale": 1.94` (16429/8479 ≈ 1.94, iguala distancia de inicio
  del intro BAG2). Sólo afecta a gaso; ningún otro stage profile usa != 1.0.
- Prueba `test_gaso_camera_positions_scaled_to_bag2_distance` en
  tools/test/test_stage_port.py: remuestrea la nativa igual que el constructor,
  compara posiciones escaladas (3 componentes) y ángulos idénticos. 22 tests
  verdes (stage_port + stage_geometry + gaso_stage_fan).
- Sólo cambian los bytes de position del intro camera track; el resto del DBI
  (baile, geometría, texturas, audio, modelo) es byte-idéntico al build previo a D.
- No se repaquetó payload ni se tocó manifiesto o instalación; exp sigue 18590587.
- Cadencia/visual no verificables sin prueba real en juego. Necesita permiso del
  owner para deploy y grabación.
- Goldfish spec: _work/goldfish/spec-gaso-stage-camera.md. Revisión en frío
  pendiente (no es aprobación ni permiso de despliegue).
- Siguiente **E**: verificar eventos de puntaje en stage 9 (B1ST shim 0x801E0100)
  con grabación aceptada; auditar rutas de lectura del shim. A/B/C siguen WIP.

## E: eventos de puntaje en stage 9 / B1ST shim (2026-11-13, candidato offline)

- Objetivo/check: verificar que el shim B1ST en 0x801E0100 se ejecute correctamente
  en stage 9 (Gas-O BAG1), escribiendo beat flags, score level, previous level, y
  reseteando el ventilador del escenario en nuevo partido. No se cambian los demás
  escenarios. Se conserva como candidato offline; no hay permiso implícito de
  despliegue/partida/commit.
- bag2jp_bag1_stage.c: b1s_vblank acepta stage_id == 9 (línea 55) junto con 0 y 1.
  Stage 9 requiere adicionalmente b1s_is_gaso_bag1() (entrada 197 -> ALT) y magic
  B1ST presente en 0x801E0100 (prueba de residencia).
- En nuevo partido: score level (shim+8) y previous level (shim+9) se resetean a 0;
  stage fan angle/speed (0x801DECC0/0x801DECC2) se resetean a 0 (solo stage 9).
- En cambio de beat: beat flags bit 0 y bit 4 escritos en shim+4; score level
  calculado desde best score vs umbrales de dance de BAG2.
- Stage 9 sin Gas-O BAG1 seleccionado: vblank no hace nada (flags/level se quedan en 0).
- port_bag1_stage.py: escribe magic 'B1ST' en SHIM - B2_BASE (offset 0x51F0 en DBI).
- gaso.json globals: 0x80068704 (beat flags, 4B) -> 0x801E0104; 0x80068714 (score
  level, 1B) -> 0x801E0108; 0x800979D0 (previous level, 1B) -> 0x801E0109.
- Pruebas: test_bag1_stage_shim.py cubre stage 9 (con Gas-O BAG1 y sin él);
  test_stage_port.py verifica magic B1ST en el build de gaso. 23 tests verdes
  (stage_port + stage_geometry + gaso_stage_fan + bag1_stage_shim).
- No se repaquetó payload ni se tocó manifiesto o instalación; exp sigue 18590587.
- No hay aceptación en juego: requiere permiso del owner para deploy y grabación.
- Goldfish spec: _work/goldfish/spec-gaso-stage-score-events.md. Revisión en frío
  pendiente (no es aprobación ni permiso de despliegue).
- Siguiente **F**: recorded take con permiso explícito del owner (BAG2JP_TEST_GASO_ATTACK='1'
  + stop_on_selector.ps1). A/B/C/D/E siguen como candidatos offline sin aceptar.

## Reanudación 2026-11-13 (tarde): deriva de fuentes y estado real de exp

- Preflight `gaso-resume-20261113`: deriva mods-src vs `BAG2JP-codex-build/BAG2JP/src`
  en 3 archivos. Diffs en `_work/workflow/drift-20261113/`.
  - `bag2jp_gaso_caught.c`: build=1, mods-src=0 en `GASO_CAUGHT_CLIP_PUBLISHED`.
    Intencional y ya registrado (`retire_evidence.source_clip_published=false`,
    `experimental_clip_published=true`). No se toca.
  - `bag2jp_bag1_versions.c`: mods-src añade guardas `!b1v_active || b1v_force_stock`
    en `bag2jp_bag1_get_version` (registrado en `completed_this_session`). Aún no
    está en el build; entra en el próximo candidato combinado.
  - `bag2jp_bag1_alt_index.h`: **inconsistente**. mods-src (SHA 5EE8FE4F, tag
    `0x9418D707`, 10:48) colapsa `jp_off/jp_size` a `alt_off/alt_size` y reubica
    offsets; no coincide con ninguna salida de payload en `_work`. El build usa
    C3EBF689 (tag `0x376287AB`) = `_work/gaso/sign-subdivision-v2-candidate/payload-out`,
    que coincide con el DUMMY desplegado. No se propaga el de mods-src: compilarlo
    contra el DUMMY actual leería offsets erróneos y perdería las variantes JP.
    Pendiente: identificar su origen o restaurarlo desde el payload-out (decisión
    del owner antes de sobrescribir).
- **Estado real de exp-8mb distinto del anotado arriba**: el exe instalado es
  `872e6753...` (build `gaso-tank-sound` 08:57, compilado con CLIP_PUBLISHED=1),
  no `18590587`. Pasos `gaso-deploy-f` (10:43-10:44) y la grabación
  `_work/recordings/gaso-attack-take` (exe 872e6753, `accepted: true`, 0 eventos,
  gf 5862-13050) existen sin registro en esta nota ni permiso F localizado en
  `current-state.json`. Hubo otra partida hasta 11:45 (logs de exp). Sin revisar
  aún; no cuenta como aceptación.


- Goldfish D (cámara a distancia BAG2), 2026-11-13, 2 revisores fríos sobre
  `_work/goldfish/spec-gaso-stage-camera.md`: **CON HALLAZGOS**.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
  - Confirmado y corregido: las llaves son s16 ojo xyz + objetivo xyz (no ángulos);
    el código escalaba el ojo respecto al origen (radio k0 24438 en vez de ~16430).
    `build_stage_package.py` (38D63F21C47D) ahora escala la distancia ojo-objetivo,
    conserva el objetivo, valida llaves de 12 bytes y desborde s16; `new_track_len`
    fuera del bucle. Prueba reescrita sin reimplementar la fórmula
    (`test_stage_port.py` BB6857E91DC2): radio k0 = stock (±1 %), objetivo nativo,
    ratio 1.94 y dirección en k0/klast, pistas de baile stock idénticas, Heat/Strike
    sin `camera_scale`. Verde 23/23; roja con la fórmula antigua (ratio 1.487).
  - Pendiente del owner: `camera_speed=2.1` agota las 150 llaves nativas hacia el
    fotograma 71 de 165; el resto de la intro (~57 %) queda fija en la última llave.
  - Sin verificar offline: encuadre/FOV, recorte cercano/lejano, transición a pista 1.
    Falta la evidencia `_work/gaso/stage-camera/shared-green.log` citada en la spec.
  - Alcance: el diff de `gaso.json` (F0A47B2272AB) incluye también parches del
    ventilador (C) y `strike.json` cambios fuera de D.
- Goldfish E (eventos de puntaje), 2026-11-13, 2 revisores fríos sobre
  `_work/goldfish/spec-gaso-stage-score-events.md`: **CON HALLAZGOS** (sin bugs).
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
  - Corregido: `b1s_is_gaso_bag1` aceptaba cualquier offset ≠ stock/0; ahora usa
    `bag2jp_bag1_entry_is_alt(197)` (nuevo en `bag2jp_bag1_versions.c` 6267D0BB3673),
    que compara con `alt_off`/`jp_off` exactos del índice. Comentario de cabecera de
    `bag2jp_bag1_stage.c` (5F19F0EDA312) actualizado a stage 9.
  - Pruebas no vacías (`test_bag1_stage_shim.py` 8BEE2721B4CA, usa la búsqueda e índice
    reales): ventilador precargado ≠0 y puesto a 0 en stage 9; stages 0/1/2 no tocan el
    ventilador; bit 0x40 fin de canción; reinicio tras salir de root 0x13; stage 9 con
    offset stock, otro offset, 0 o sin 'B1ST' deja centinelas intactos. Roja con la
    detección antigua y sin el reinicio del ventilador. `gcc -fsyntax-only -Wall` limpio.
  - Riesgos para la toma F: un fotograma con root ≠ 0x13 a mitad de partida reinicia
    nivel y ventilador; los hooks de cámara (`b1s_*` camera) ahora también actúan en
    stage 9; las globales beat flags/prev level no las lee el código nativo de Gas-O
    (inofensivas). Orden setup/vblank/primer beat y revancha: solo en juego.
  - El índice `bag2jp_bag1_alt_index.h` de mods-src sigue inconsistente (ver arriba): la
    detección exacta depende de que el índice compilado corresponda al DUMMY desplegado.

### Origen de `alt_index.h` 0x9418D707 y uso del exe 872e6753 (2026-11-13)

- Autor: sesión OpenCode `ses_e326378fbffeMXgcnTfyc4Dfkb` ("Ejecutar P0 CAUGHT runtime
  con Ghidra"), tras la autorización del propietario a las 10:43:04 ("si autorizo,
  continua") de desplegar en exp-8mb y grabar F. Evidencia: copia de solo lectura de la
  base de OpenCode y `_work/workflow/drift-20261113/ses_e326378f-cmds-*.txt`.
- 10:44 build `gaso-deploy-f` -> exe 872e6753 (árbol de build en ese momento:
  `CLIP_PUBLISHED=1`, cue de tanque A WIP 0x6906/0x690a, guardas existentes); copiado a
  exp-8mb sin copia de seguridad del exe anterior (18590587).
- 10:45 `build_stage_package.py --profile gaso` ->
  `_work/gaso/stage-fan/candidate-v2-with-camera/stage197.dfs` e7a47c4c (ventilador C +
  cámara D con la fórmula antigua, escalada respecto al origen: el error que luego
  encontró Goldfish).
- 10:48 un script `py -3.13 -c` reconstruyó el payload de forma contigua (offsets
  reubicados, `jp_off/jp_size` colapsados a `alt_off/alt_size`) y reescribió a mano el
  header de **mods-src**: 0x9418D707 son los 8 primeros hex del SHA de ese payload
  contiguo (9418d707cc55...), visto en el manifest de exp a las 11:05. No fue
  `make_alt_entries_exact.py` (no hay `alt_report.json`). Ese payload ya no existe.
- 10:49-11:12 el juego salía al arrancar con payloads contiguos (9418d707, luego
  806ccdd0, 6338560 bytes): el exe compilado conserva los offsets antiguos.
- 11:14 `_work/gaso/stage-camera/patch_payload_inplace.py`: parche in situ de la entrada
  197 sobre 376287ab. Verificado hoy: payload de exp 6ff5aa89, mismo tamaño (10016768),
  896 bytes distintos, todos dentro del hueco de la entrada 197 (0x849800-0x8C715C);
  contenido = e7a47c4c. El manifest de exp quedó obsoleto (`sha256`/`expected_sha256` =
  c67e575d, de un parche sobre la base equivocada); el juego arrancó igualmente.
- Grabaciones: 11:15-11:24 aceptada pero en RETRY/QUIT todo el rato (la sesión lo
  admitió); 11:34-11:36 `_work/recordings/gaso-attack-take` aceptada, gf 5862-13050,
  0 eventos; sin revisión fotograma a fotograma ni conformidad del propietario.
- Estado: el header de mods-src no corresponde a ningún payload existente; payload y
  manifest de mods-src siguen en 376287ab. Recomendación: restaurar el header de mods-src
  desde `_work/gaso/sign-subdivision-v2-candidate/payload-out` (C3EBF689, 0x376287AB) y
  regenerar con `make_alt_entries_exact.py` en el build combinado A-E. Exp contiene la
  cámara D defectuosa (corregida en fuente, sin desplegar). `camera_speed` 2.1 se deja
  como está por decisión del propietario (2026-11-13).

### Build combinado A-E regenerado con el estándar (2026-11-13)

Orden del propietario: rehacer bien lo que hizo la otra sesión con el procedimiento
estándar. Directorio `_work/gaso/combined-ae/`.
- `stage197.dfs` 28bff4ac (ventilador C + cámara D corregida) con
  `build_stage_package.py --profile gaso`; `compose_spec.py` -> `spec.json` (30 filas,
  base 376287ab); `make_alt_entries_exact.py` -> payload c2129468 (10016768 bytes,
  4891 sectores), header 3f091c60 (tag 0xC2129468), `expected_sha256` 9a16bfba.
- `verify_payload.py` ok: base_rel 0x1B538000, cabe en DUMMY, layout idéntico al header
  base C3EBF689 (jp no colapsado), 2030 bytes distintos solo en 53/54/125/126 (nombre HUD
  B, un miembro) y 197 (miembro 0: 2 instrucciones del ventilador; miembro 12: cámara).
- Staging con respaldos en `backup/00-07`: header, payload y manifest de mods-src
  (solo línea `sha256`); en el build tree header, `bag2jp_bag1_stage.c`,
  `bag2jp_bag1_versions.c` y manifest preloaded (= mods-src c0f567ba).
- Build `gaso-combined-ae`: exe 3519b5ad; `check_payload_manifest.py` 3/3 copias OK.
- Host: 23 tests OK.

Goldfish 2026-11-13, payload combinado A-E, estado: payload c2129468, header 3f091c60,
manifest c0f567ba, exe 3519b5ad; 2 revisores; veredicto CON HALLAZGOS (sin bloqueantes).
Spec `_work/goldfish/spec-gaso-combined-ae-payload.md`.
- Confirmado (H1): el manifest del build tree ganó además el bloque `bag1-gaso-caught`
  y 2 plugins (`default_enabled = false`); es el mismo contenido que mods-src y exp ya
  tenían, pero no estaba en el spec. La descripción dice "observe-only, no clip
  publication" y el build tree compila con `GASO_CAUGHT_CLIP_PUBLISHED=1`: exp activa la
  feature, así que este exe publica el clip igual que 872e6753 (experimental, toma F
  autorizada). Pendiente: corregir la descripción cuando se decida publicar.
- Refutado como riesgo (H2): estados intermedios del manifest (786e49d8, ef1d63d7) sin
  respaldo; el resultado final se comparó contra los originales respaldados
  (586c8019/f76698be) y solo difiere en lo descrito.
- Refutado: un revisor atribuyó `sra 1->4` a la cámara D; es el ventilador C (divisor
  nativo /16). La cámara está solo en el miembro 12.
- Menor: `compose_spec.py` dice "C+D+E" (E vive en el exe y la firma B1ST ya estaba en
  la base); copia vieja sin uso en `src/mods-src/` del build tree.
- Pendiente en vivo: carga del payload, ventilador por nivel, cámara, nombre HUD
  (intl/JP), savestates antiguos con offsets iguales y contenido distinto.
Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
### Toma F grabada sobre build combinado A-E (`gaso-combined-ae-f2`, 2026-11-13)

- Despliegue experimental en `D:/Games/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb`
  (respaldo previo en `_work/gaso/combined-ae/exp-backup/`: exe `872E6753`,
  `settings.toml` `2AC29271`, `keybinds.ini` `EAAF722E`, `mods/state.toml` `EE35AB92`,
  `manifest.toml` `CE5ACB6F`, `bag1_alt.bin` `6FF5AA89`): exe `3519b5ad`,
  `manifest.toml` `c0f567ba`, `bag1_alt.bin` `c2129468`;
  `check_payload_manifest.py` en exp 1/1 OK.
- Calibración previa aceptada: `_work/versus-runs/20261113T182646483322Z-gaso-combined-ae-probe`
  (94.9 s, `restoration.verified: true`, 8 bordes verificados visualmente en
  `_work/gaso/combined-ae/probe-sheet.jpg`).
- Toma 1 (`gaso-combined-ae-f`, `_work/versus-runs/20261113T185258565946Z-gaso-combined-ae-f`,
  303.655 s, `restoration.verified: true`): `bag2_record.py finalize` RECHAZADA
  (`accepted: false`, salida 1) por 1 stall de 0.202 s tras `gf=16008` que desplazó
  1206/11543 pares de audio (`residual_p99_ms=158.85`, `window_max_ms=158.68`).
  Conservada como diagnóstico; no se usa como evidencia aceptada.
- Toma 2 (`gaso-combined-ae-f2`, `_work/versus-runs/20261113T190419608874Z-gaso-combined-ae-f2`,
  302.383 s, `restoration.verified: true`, 150 saves originales):
  `py -3.13 tools/test/bag2_record.py finalize --tag gaso-combined-ae-f2` -> **ACCEPTED**
  (salida 0, `manifest.json` `accepted: true`):
  - `owner.mp4` (`_work/recordings/gaso-combined-ae-f2/owner.mp4`, SHA-256 `165f2984...`),
    `review.mkv` (`ce98190e...`), `raw.mkv` (`7fddb116...`), 41 eventos.
  - Reloj: 1923 latidos (`gf=6150..17682`), 5 tardíos, jitter p99 14.72 ms, 59.944 fps,
    1 stall menor de 0.125 s tras `gf=16014` durante Fever 1; `window_guard.passed: true`
    (202 checks).
  - Audio (`bag2jp_audio.wav`, `-15.2 LUFS`, `-0.58 dBTP`): `offset_s=-102.595789`,
    `rate_hz=44056`, 11515 pares, 8 descartados, `residual_p99_ms=17.07 ms`,
    `window_max_ms=12.6 ms`.
- Revisión por ítem sobre la grabación aceptada (hojas en `_work/gaso/combined-ae/f2-sheets/`):
  - A (audio tanque/re-hit): `gaso_tank` disparó `cue 6906` (`gf=7474`, `7681`; `vt=22.094s`,
    `25.534s`) y `cue 690a` (`gf=7491..7857`, 14 líneas en `versions.log`), y
    `bag2_report.py` registró `0x6906x2` y `0x690ax3` en `cues phase 0`; los picos RMS
    del WAV suben a 8654 (`vt=22.5s`, pico 31733) y 9634 (`vt=26.0s`, pico 31722)
    inmediatamente tras ambos `0x6906`. Falta escucha humana subjetiva y el sonido
    faltante del re-hit de Heat sigue sin identificarse.
  - B (HUD `GAS-O`): visible y legible en P1 (`tank1.jpg`, `tank2.jpg`, `lvl2.jpg`)
    con tinte verde-amarillo; correspondencia exacta de CLUT y pantalla VS (que sigue
    mostrando `Bi-O vs Heat` en `gf=6652`) pendientes.
  - C (ventilador): `bag2jp_watch.log` verifica aceleración de `801DECC2`: `0 -> 0x80`
    (`gf=11188..11442`) y `0x80 -> 0x200` (`gf=13856..14622`) con avance suave del
    ángulo `801DECC0`, y giro visible en `intro.jpg`.
  - D (cámara intro stage Gas-O BAG1): `intro.jpg` (`gf=6850..7000`, `vt=9.165..14.177s`)
    muestra el descenso limpio desde el domo superior pasando por ventilador y paneles
    hasta encuadrar a Gas-O y Heat sin clipping; mantiene el tramo final quieto por
    `camera_speed=2.1` (dejado así por decisión del owner).
  - E (eventos de puntaje B1ST): `B1ST` (`0x54533142`) activo desde `gf=6452` (`root=13`);
    nivel `0->1` en `gf=11187` (`sc=0x2DD2`) y `1->2` en `gf=13855` (`sc=0x6612`),
    flags `['0', '1', '11', '40', '41']`; `lvl2.jpg` confirma letreros `GAS` iluminados
    y paneles alternos en nivel 2.
  - F (ataque CAUGHT y flujo completo): 2 capturas con tanque translúcido verde, líquido
    ascendente y burbujas sobre Heat (`gf=7453..7593` y `gf=7657..7875`, `slot1`
    publicado/restaurado `clip=9f000000`, `bytes=348`), ataque de Heat (`gf=15148..15278`),
    rechazo por reflejo (`gf=15349`), Fever 1 (`gf=15659..17142`) y retorno limpio al
    selector de personaje (`songend.jpg`, `vt=3:06s`, `return_root=13`).
- Estado de aceptación: grabación técnica aceptada (`manifest.json`), pendiente de
  conformidad visual/auditiva del propietario. Commit no autorizado. `CLIP_PUBLISHED=1`
  permanece solo en build tree experimental (`mods-src/bag2jp_gaso_caught.c` sigue en 0).
