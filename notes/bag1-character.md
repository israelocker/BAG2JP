---
id: bag1-character-heat
title: "Heat: adaptadores y evidencia histórica"
tags: ["bag1", "heat", "reference"]
summary: "Heat: corrección de modelos por traje verificada en ambos lados; adaptadores y gaps históricos de animaciones/audio siguen separados."
related: ["notes/character-pipeline.md", "notes/character-alternate-entries.md", "notes/strike-recovery.md"]
created: "2026-10-29"
updated: "2026-11-05"
edited: "2026-11-05"
doc_kind: reference
---

# Heat no es la plantilla de todos los personajes

## Ataque BAG1: efecto de llamas portado (2026-11-05, experimental, pendiente de revisión del propietario)

- **Causa.** El efecto de fuego del DBI de Heat en BAG2 muestreaba la página de VRAM x768 y256, que ahora contiene las texturas BAG1 de Heat (tira de llamas de `005.tim`). Por eso aparecían el anillo blanco y el arco pixelado. Además, la animación facial del DBI (6 llamadas a MoveImage) sobrescribía esa tira. El impacto no fallaba: la CPU P2 esquivó (req170) y luego se protegió (req171).
- **Cambios.**
  - `tools/bag1import/patch_heat_dbi.py`:
    - el parche 3 anula las 6 llamadas MoveImage faciales;
    - el parche 4 anula solo el renderizador `FUN_801ce628`. La lógica de impacto, las reacciones y los cues siguen activos.
  - `patch_heat_face_payload.py` aplica los dos parches a las entradas 59/60/131/132 sin cambiar el tamaño. Ahora conserva el relleno final.
  - `alternate_payload.py` `repack` mantiene compartidas las entradas que lo estaban.
  - Payload: 4640768 B, sha `7fd23c00…`, fijado en `manifest.toml`.
- **Efecto.** `mods-src/bag2jp.feature.bag1-content/bag2jp_heat_flame.h` reimplementa el efecto nativo de BAG1 (`FUN_801daa10`/`dad98`/`db64c`/`dbc34`), es decir llama, anillo y 24 partículas, con POLY_FT4 y la tpage/CLUT del descriptor BAG2. Valores en runtime: tpage `003c`, clut `003d`, el anillo usa `+0x40`.
  - Coordenadas locales del bailarín (+0x810/+0x818), con la cámara compuesta con la matriz del atacante o del objetivo, como hace el DBI de BAG2.
  - `life` = ticks restantes del reproductor de movimiento (`0x8005F820 + side*0x98 + 0x20`).
  - Las escalas de tamaño y posición están ajustadas al clip nativo; no son derivadas.
  - Los frames UV 9-11 usan la fila superior, porque BAG2 sube la etiqueta "HEAT" encima de ellos.
- **Fixture de prueba** (solo con `BAG2JP_TEST_HEAT_ATTACK=1`): fuerza el ataque de P1 y borra el esquive o la guardia de P2. No es juego natural.
- **Evidencia.**
  - Captura `_work/versus-runs/20261105T143352068565Z-heat-attack-bag1` (exe `a7f056a4`). La secuencia es la misma que en el clip nativo:
    - llama corporal durante el agachado;
    - destello que sube;
    - columna que cae sobre el rival;
    - explosión y llamas en el suelo;
    - Strike derribado con estrellas, puntuación 300→0.
  - VRAM: los texels del anillo son idénticos a `005.tim`. La página difiere en 210 halfwords, que son la etiqueta HEAT de BAG2.
  - Partida completa sin fixture: `_work/versus-runs/20261105T143617747233Z-heat-flame-full`, termina la canción y vuelve al selector. En esa partida no hubo ataque natural.
  - Tests de host: `test_heat_flame_effect`, `test_heat_dbi_face_patch`, `test_attack_fixture` (6 OK).
- **Gaps.**
  - El anillo de la explosión se ve naranja y en bloques, frente al destello blanco nativo. Su textura y CLUT coinciden con BAG1, así que la diferencia probable es el tamaño o la mezcla; no está verificado.
  - Falta la comparación visual del propietario.
  - Antes de este trabajo ya fallaba `test_heat_costume_assets.py`.

## Pose final del Double Fever: ganador frente a perdedor (2026-11-04)

- Propietario observa que Heat (ganador) se inclina hacia el perdedor. Fuente en línea
  (TV Tropes): el dúo termina con el **perdedor** inclinándose ante el vencedor; la pose del
  ganador no está documentada en línea. Referencias del propietario: el perdedor acaba
  encogido/cabeza baja; el ganador, de pie con brazo en alto o rodilla en tierra y brazos
  extendidos hacia el perdedor.
- Fixture `heat-p1-duet-rng-hook-bag2` (BAG2 sin modificar) y `-bag1`: puntuaciones
  artificiales P1 500000 / P2 500100. Fotograma final idéntico en ambos: P1 (traje A,
  blanco) rodilla en tierra con brazos extendidos; P2 (traje B, rojo, más puntos) inclinado
  hacia P1. P1 reproduce anim132→134, P2 anim131. Hoja:
  `_work/character_import/heat/fever_exit/final-pose-bag2-top-bag1-bottom.png`.
- Conclusión acotada: la importación BAG1 reproduce exactamente el final de BAG2 original.
- Puntero ganador nativo (`winner_probe.py`, lectura `ReadProcessMemory`, BAG2 sin
  modificar, `_work/versus-runs/20261104T221554675244Z-heat-duet-winner-bag2`,
  fixture reproducido): `0x80089254` = 0 hasta fase 1/6/2 y luego = bailarín P2
  (`0x801A7E44`), coherente con la puntuación mayor. Por tanto, en BAG2 original el
  **ganador P2 se inclina hacia el perdedor**, y el perdedor P1 acaba con una rodilla en
  tierra y los brazos extendidos hacia él; ambos quedan inclinados uno hacia el otro.
  Propietario objeta que el ganador no debería inclinarse. Lo probado es paridad con BAG2
  sin modificar **bajo el fixture artificial** (puntuaciones y semilla RNG forzadas, salida
  P1 132→134); no que sea el final de una partida natural.
- **Resuelto con partida natural** (`natural_duet_probe.py`, BAG2 sin modificar, autoplay
  2P sin fallos ni ataques, sin fixture). Criterio nativo (`jp005` 0x80098c5c): Double
  Fever si ambos superan el umbral y |diferencia| < 1000. Intentos 1–4: Fever simple;
  intento 5 (`_work/versus-runs/20261104T224422766963Z-heat-natural-duet-5`): P1 28930,
  P2 29630, ganador P2. Perdedor P1: anim132→134, rodilla en tierra con brazos hacia el
  ganador; ganador P2: **anim129, de pie con el brazo en alto** (pose de victoria).
  Hoja `_work/character_import/heat/fever_exit/natural-duet-final-sheet.png`.
- Conclusión: el final natural es correcto y coincide con las referencias del propietario.
  El «ganador inclinado» (anim131) solo aparece con la semilla RNG forzada del fixture;
  es un artefacto de la prueba, no del juego ni de la importación. No usar ese fixture como
  referencia visual de pose final. Sin cambios de código. No probado: Double Fever natural
  con Heat BAG1 (depende del azar de puntuaciones).
- **Seguimiento abierto (propietario, 2026-11-04):** seguir observando los Double Fever en
  cualquier partida natural, sobre todo con personajes BAG1 (Heat, Strike) y cruces
  BAG1/BAG2: pose final de ganador/perdedor, cortes, orientación entre ambos, transición a
  resultado. Registrar personajes, versiones, trajes, lado ganador, puntuaciones y anims
  (`natural_duet_probe.py` guarda puntero ganador y capturas del cierre).

## Auditoría de cierre fever en curso (2026-11-03)

### Corrección de alcance: Double Fever no existía en BAG1

Validación web solicitada por el propietario antes de continuar (2026-11-03):
el **Double Fever Time/dueto es una incorporación de BAG2**, no una coreografía
original BAG1 pendiente de importar. BAG1 tiene fever individual con variantes;
FEVER1/FEVER2 no significan individual/doble. Debió aclararse antes de programar
pruebas de dueto como parte de la fidelidad BAG1.

Fuentes leídas, no solo snippets:
- [GameFAQs, PSO_Femme, reseña del 08-07-2002](https://gamefaqs.gamespot.com/ps/196847-bust-a-groove-2/reviews/36715):
  afirma explícitamente «A Double Fever time is a Bust A groove 2 exclusive».
- [TV Tropes, Finishing Move](https://tvtropes.org/pmwiki/pmwiki.php/VideoGame/BustAGroove):
  describe el fever individual y sitúa el dueto «In the sequel».
- [GameFAQs, kidmigaru, Command Patterns FAQ](https://gamefaqs.gamespot.com/ps/196847-bust-a-groove-2/faqs/8706):
  documenta el dual fever de BAG2 con ambos jugadores en nivel5 y dentro de1000
  puntos; respalda la distinción y concuerda con el gate JP inspeccionado.

Consecuencia: el dueto instalado es **compatibilidad/adaptación BAG2 sobre modelos
BAG1**, no fidelidad a una secuencia BAG1 inexistente. Conservarlo sin cambios por
ahora; no inventar/importar un dueto nativo BAG1 ni desactivarlo sin aprobación.
El propietario autorizó continuar investigando el dueto como adaptación. La
fidelidad del fever individual y su pose final es un objetivo válido separado.

### Fixture de comparación P1 (experimental, 2026-11-03)

Para comparar exactamente fever2 y salida P1 132→134, el hook opt-in
`BAG2JP_TEST_P1_DUET=1` aporta puntuaciones artificiales 500100/500000. Requiere
trace activo, identidad JP, root19/mode2/phase1/3/3, Heat A/B y palabra original
0x284203E8 en 0x80098C44. Solo escribe los dos scores; no modifica MIPS,
ganador, flags fever ni motions. Esto no es evidencia de puntuación natural.

- Experimento TCP `score_fixture.py` abortó antes de navegar: build con
  `PSX_DEBUG_TOOLS:BOOL=OFF`, listener ajeno/ausente rechazado. Run
  `20261103T120651822314Z-heat-p1-duet-fixture-bag2`, ajustes/21 saves restaurados.
  Conservar como experimento fallido; usar `hook_fixture.py`, no habilitar debug global.
- `test_score_fixture.py`: RED observado por ausencia de writes; GREEN con
  header real y 13 casos de guards/límites. Suite host: 115 pruebas y nueve casos
  C debug-option pasados. Fuente canónica y staged comparten hook/header; staged
  conserva su fixture previo de campaña, no se sobrescribió con el canónico.
- Build `20261103T121518803359Z-heat-duet-score-fixture`: correcto en 31,741 s.
  Desplegado solo exe experimental, SHA-256
  `5acdea13d7626030ad876b3e7fde6ef7180a12a0cab37fd9cf5793842de5bb6a`.
  Baseline anterior en `fever_exit/runtime-before-score-fixture/BAG2JP.exe`;
  reporte `fever_exit/score-fixture-deployment.json`. Payload sin cambios.
- Calibración `20261103T121744892418Z-heat-score-fixture-calibration`: cuatro
  PNGs revisados (Heat↔Comet horizontal, Heat↔Strike vertical), catálogo con hashes
  de imágenes/runtime y sello de revisión. Ajustes/21 saves restaurados.
  Control BAG2 con hook terminado, rechazado como caso no equivalente (abajo).
  Comparación BAG1 pendiente. Runner exige
  `fixture-validation.json` = `matched_fixture`: hook ejercitado, captura fever2,
  P1 request186→132 y followup134. Revisar PNGs/timing además del resultado host.
  No hay corrección de animaciones ni causa visual demostrada.

#### Resultado del primer fixture: dos supuestos refutados

Run `20261103T121927251964Z-heat-p1-duet-hook-bag2`: canción/retorno completos,
ajustes/21 saves restaurados, 290,559 s total. Hook ejercitado y fever2 capturado,
pero `fixture-validation.json` = `unmatched_fixture`: request180/181→126/127,
después P2 request186→135 directo. No ejecutar BAG1 como si fuese control del
camino132→134. Los 176 PNG revisados en `duet-exit-sheet.png` muestran salida
y pose final hasta fade; 21 frames negros/fade no son captura totalmente fallida.

Código nativo ya extraído permite explicar el desajuste sin más partidas:
- JP005 0x80098920..0x8009894C: scoreP1>scoreP2 fija 0x8005E699=1.
  0x8009CE74..0x8009CEC4: valor1 manda request186 al slot P2 (+0x3C),
  valor2 al P1 (+0x18). La idea «P1 por delante para cierre P1» era incorrecta.
  Screenshot `match-13.png` muestra 500100/500000, conforme al fixture.
- 0x8009CDB8 llama RNG nativo0x80049F24; 0x8009CE04..0x8009CE34 toma
  variante módulo3 y emite pares requests180/181,182/183,184/185 (Heat).
  Scores no controlan esa variante.
- Main 0x8002A65C..0x8002A6B8: predecesores126/127/131 van directo134+lado;
  predecesor130 permite132 y followup134. No son recorridos equivalentes.

### Ampliación RNG autorizada (2026-11-04, pendiente de runtime)

El propietario autorizó continuar tras proponer control de selección aleatoria
sin modificar motions ni flags winner/fever. Objetivo/check: obtener en ambos
modelos requests184/185→130/131, luego P1 request186→132→134; validar el recorrido
y revisar su cierre visual, canción y retorno. No aceptar por tests host solamente.

- Scores del fixture invertidos a P1=500000/P2=500100, conforme a la selección
  nativa de lado ya medida. RED del guard de writes observado antes del cambio.
- `SLPM_862.19`0x80049F24..2C es veneer BIOS A0/0x2F (`rand`), palabras
  240A00A0/01400008/2409002F. OpenBIOS original0xBFC060E4..0xBFC0610C usa seed
  RAM0x00008548: `seed=seed*0x41C64E6D+0x3039`, devuelve `(seed>>16)&0x7FFF`.
  Input1 devuelve16838; módulo3=2 selecciona requests184/185 para Heat.
- Hook de instrucción en JP0050x8009CDB8, palabra original0C0127C9, aporta
  únicamente seed1 **antes** de esa llamada; no salta RNG ni escribe su resultado,
  requests, flags o código. Guards: trace+env exactamente1, JP, Heat A/B,
  root19/mode2/phase1/7/1/fever2, veneer, instrucciones de despacho y cuerpo
  completo del RNG BIOS. Si no coinciden, no escribe. Código nativo005 contrastado
  con `assets/archive/system/005.dbi`, hash bc5f3045…b28fb2 (completo en
  `native-dispatch-contract.json`). Sin cambios de framework/config/pins.
- Header real: 13 casos score y 30 casos RNG (28 guards alterados, desactivado,
  válido); RED por helper RNG ausente y GREEN posterior. Suite117 y nueve casos
  C debug-option pasados. Runner añade guard de seed ejercitada y variante184/185;
  prueba mock acepta camino completo y rechaza seed/variante/cierre/followup ausente.
- Primer build `20261104T053939251970Z-heat-duet-rng-fixture` falló al compilar
  por firma incompleta del callback (faltaba argumento dirección). Corregida;
  regresión adicional compila el adapter real con firma de dos argumentos y
  comprueba dirección, trace, log y env. Build `heat-duet-rng-callback-signature`
  correcto: `20261104T054051997302Z-heat-duet-rng-callback-signature`, 24,392 s.
  Exe experimental desplegado, SHA-256
  `d99d3ca4aee3adacf0bced4c6588a7c691ac15e170fcfd308da9a56214eded81`;
  backup anterior `fever_exit/runtime-before-rng-fixture/BAG2JP.exe`, reporte
  `fever_exit/rng-fixture-deployment.json`. Recalibración iniciada; pendiente juego.
  Staged conserva fixture previo de campaña. Siguiente: desplegar experimental,
  recalibrar por nuevo hash y ejecutar control BAG2; BAG1 solo si el caso coincide.

### Control BAG2 comparable obtenido (2026-11-04)

- Calibración `20261104T054135891679Z-heat-rng-fixture-calibration`: cuatro
  aristas revisadas visualmente y ligadas a hashes; ajustes/21 saves restaurados.
- Run `20261104T054314117168Z-heat-p1-duet-rng-hook-bag2`: `matched_fixture`,
  seis guards del runner cumplidos, incluidos seed aplicada y requests184/185.
  Canción/retorno completos; ajustes/21 saves restaurados; 290,606 s total.
- Trace: 130/131 desde f15210, P1 132 desde f16045 (request186 en16046),
  134 desde16189; sale a phase1/9/5 en16215. Tramo132 total144 vblanks;
  desde inicio phase1/7/5 (16049), quedan140 en132 y26 en134 antes de salir.
  No confundir esos140 con duración total de132 ni inferir defecto solo por30
  frames de fichero134 frente a26 vblanks observados.
- 176 PNG revisados en `duet-exit-sheet.png`, incluyendo `114.png` del tramo134;
  21 frames fade/negros posteriores. Se ve el cierre conjunto hacia pose baja,
  con cámara acercándose a P2. Esto fija control nativo, no acepta adaptación BAG1.
- Run BAG1 equivalente terminado; resultado comparado abajo. No repetir control
  BAG2 mientras inputs y runtime sigan iguales.

### Resultado BAG1/BAG2: mismo cierre temporal en el caso comparado

- BAG1 `20261104T054824756883Z-heat-p1-duet-rng-hook-bag1`: `matched_fixture`,
  canción/retorno completos, ajustes y21 saves restaurados; 280,262 s total.
  176 PNG revisados,20 negros/fade posteriores. P1 130 req184/P2 131 req185
  desde14744; P1 132 desde15580, request186 en15581; 134 desde15724; salida
  phase1/9/5 en15750. Son **144 vblanks en132 y26 en134**, iguales a BAG2.
- [Comparación visual alineada](../_work/character_import/heat/fever_exit/matched-exit-comparison.png)
  y `matched-exit-comparison.json` conservan tiempos, paths y hashes de traces/PNGs.
  Siete offsets relativos al inicio132; muestras más cercanas del heartbeat, no
  igualdad exacta de frames de motion. Se observa el descenso de P1 y cierre
  conjunto hacia pose baja/con brazos extendidos en ambos; no un gesto que BAG1
  pierda antes que BAG2 en este recorrido. Cámara/efectos difieren y parte de P1
  queda fuera de plano en las últimas muestras: no afirmar identidad visual total.
- **Conclusión acotada:** no se reprodujo un recorte temporal exclusivo de la
  adaptación BAG1. El tramo134 corto observado también ocurre con Heat BAG2.
  No hay fundamento en esta prueba para alargar clips, añadir hold ni cambiar
  pose. No demuestra fidelidad completa BAG1 ni acepta otras variantes/rosters.
- Checkpoint local `e2e58dd`: solo fuente/header del fixture y regresiones host;
  experimental/diagnóstico, no corrección ni aceptación general de animaciones.
  Las demás modificaciones Heat/Strike se conservaron sin incluirlas. Runtime
  experimental permanece con fixture opt-in; estable intacto. No snapshot de
  release: este hito valida diagnóstico, no una importación aceptada.

Siguiente: revisión del propietario de la comparación. Si el corte denunciado
corresponde a otro gesto/variante, identificar su frame/request antes de nuevas
partidas o cambios. Mantener pendiente Strike y la voz VS; no declarar resueltos
los gaps globales de transiciones/dueto por este único caso.

Prioridad del propietario: comprobar por separado fever individual/doble y la pose
final en Dance View; canción completada no acredita ese cierre. Evidencia nueva:
`_work/character_import/heat/fever_exit/` (preflight
`20261103T062038363798Z-heat-fever-exit-audit`). Esa primera auditoría no cambió
assets ni runtime; el hook experimental posterior se describe arriba.

- Auditoría byte a byte de entradas instaladas 22/40: individual 101/102 = clips
  BAG1 82/83, 449/494 frames y 32 beats; 103 repite 82; 104/105 vacíos también en
  stock. Doble 126..136 conserva prefijos de movimiento BAG2; cierres 132/133 =
  72 frames, 134/135 = 30 y 136 = 120. Archivo no truncado no prueba reproducción
  completa ni compatibilidad visual con el modelo BAG1.
- `viewer-run/fever-82` y `fever-83`: índices RAM 82/83 y etiquetas FEVER1/2
  revisados, 22 capturas por clip, unos 32 s cada uno, con ciclos completos y
  contact sheets. Esos nombres son **dos variantes individuales**, no una prueba
  del dueto. La tabla nativa Dance View ofrece requests 160..164, no 180..186.
  No declarar doble probado en Dance View con FEVER2.
- Trace de partida previa reutilizado: P1 130→132→134; P2 permanece en 131 hasta
  reset. Aún no se demuestra que eso sea defecto: contrastar despacho nativo,
  tiempos efectivos y salida de ambos bailarines antes de cambiar clips.
- Contraste posterior del código original JP: `system/005.dbi`, base 0x8008F890,
  en `jp005-assembly.txt`, bloque 0x8009CE74..0x8009CEC4, manda request186 solo al
  lado seleccionado por 0x8005E699. Por ello P2 sin cierre propio no demuestra
  una regresión. Main 0x8002A638..0x8002A6B8 convierte 186 según lado/predecesor:
  puede seleccionar 134/135 directamente o reproducir 132/133 y encolar 134/135
  tras `frames(132/133)*2`. No tratar 132 y 134 como aliases intercambiables.
  Ensamblado de main en `main-motion-assembly.txt`; no se parcheó código.
- Comparación control BAG2/BAG1 en mismo stage Heat BAG2 iniciada con harness
  existente y captura PrintWindow de 22 s al observar fever2 phase1/7/2. Esperar
  resultado y revisar PNG/timeline antes de aceptar o lanzar otro run. Helpers
  de diagnóstico limitados a `fever_exit/compare_duet.py` y `capture_fever.ps1`.
- Control BAG2 terminado: run `20261103T112812038408Z-heat-duet-exit-bag2`,
  canción/retorno y ajustes/21 saves restaurados (304,17 s total del harness).
  176 PNG en 22,085 s; revisión de contact sheet con tramo de dueto, cierre y
  selector visible. Request186 se dirige a P2 y selecciona **135 directamente**
  (predecesor131), sin tramo132; por ello no es todavía control del camino
  P1 132→134 visto en la partida BAG1 anterior. Timeline abarca f16044..17358.
  Detector RGB distingue 21 frames negros/fade tras la salida, no un fallo
  total de captura. `capture-review.json` es diagnóstico, no aceptación automática.
  Comparación BAG1 lanzada después de cerrar/restaurar ese control; revisar su
  resultado antes de programar repeticiones.
- Run BAG1 `20261103T113412522530Z-heat-duet-exit-bag1` completó canción/retorno,
  restauró ajustes/21 saves (288,41 s total), pero **seleccionó fever1 individual**,
  request161→slot102 en P1, no dueto. No tiene `duet-exit-capture/`: el disparador
  inicial solo reconocía phase1/7/2 de dueto. No es comparación equivalente ni
  evidencia visual nueva del cierre. Helper ajustado para phase1/7/2 o /3 y
  registrar `capture-kind.json`; comprobados con mocks casos solo, dueto, fase
  ajena, sin fever y un único disparo por proceso. Nuevo run BAG1 en curso;
  no inferir selección de dueto por el tag del run.
- Nuevo BAG1 `20261103T114108401125Z-heat-duet-exit-bag1`: individual en P2,
  request162→slot103 (repite BAG1 82/FEVER1). `capture-kind.json` confirma tipo1;
  176 PNG revisados, timeline f15528..16842, 21 frames fade tras salida. El cuerpo
  llega a la pose reclinada en el suelo y la conserva durante phase1/7/5
  f16169..16335 (166 vblanks, unos 2,77 s). No se observó corte a mitad de esa
  variante; coincide en movimiento final con el vídeo BAG1 nativo FEVER1 visible.
  `solo-observed-exit.json` verifica prefijo de movimiento idéntico a fuente82
  (449 frames, SHA-256 de prefijo
  `44a8c1b5bfc52682d7a714b05e201ed0eb1489fa421aced3c1544cd229685cd4`).
  Esto no acepta la variante82/83 completa en todo flujo ni el dueto. Canción y
  retorno completos, ajustes y 21 saves restaurados; 295,928 s total del harness.
  No quedaron procesos de esta prueba ni se cambiaron motions.
- Selección de tipo contrastada en JP005 original: bloque 0x80098B10..0x80098C54
  aplica umbral a los scores; el dueto requiere además diferencia absoluta
  `abs(scoreP1-scoreP2) < 1000` (0x80098C44, palabra 0x284203E8). Por ello el mismo
  roster/stage no garantiza mismo tipo de fever. No repetir partidas indefinidamente
  ni modificar ese gate de juego para presentar una prueba forzada como natural.
  **Siguiente:** preparar un caso comparable del camino P1 132→134 antes de otra
  captura de dueto (o aislar esos clips con un fixture explícitamente etiquetado).
  La diferencia de cierre denunciada por el propietario sigue sin causa demostrada;
  no aplicar un hold, sustituir pose ni alargar clips por aproximación.
- Se cerró la sesión experimental y se verificó restauración de ajustes y 21
  saves. La navegación inicial entró en Ending View por usar índice 4 (base cero);
  evidencia excluida. Dance View correcto es índice 3; piloto corregido.
- Copia BAG1 nativa en `D:/Dev/Scratch/bag1-native-reference`: sesión aislada con
  LOAD OK desde tarjeta copiada y vídeo `native-run/fever1.mp4` de 22 s. Su captura
  existente de cuatro segundos por acción no bastaba para revisar todo el cierre.

### Mejora visual de la referencia solicitada por el propietario

Solo `D:/Dev/Scratch/bag1-native-reference/game.toml`: `[video] supersampling = 4`
y `texture_filtering = "bilinear"`; 4:3 conservado, sin reemplazar modelos,
texturas ni motions. PGXP ya estaba activado. Backup exacto
`fever_exit/native-visual-enhancement/game.before.toml` (SHA-256
`d03fb430f9ba91f259bed88e5aca40e742c5a158383e9f540f2595e7587de23c`).
El log `native-run-hq/stdout.log` confirma `GL GPU pipeline ready (internal scale
4x...)` y filtro bilineal; la línea previa `supersampling 1x` se emite antes de
crear el contexto, no debe usarse como escala GL efectiva. Revisión visual de
Heat completada en `native-run-hq2/probe-1793703977955730300.png` (neutral),
`probe-1793704009985990500.png` (FEVER2) y
`probe-1793704072183954200.png` (FEVER1): contornos limpios y texturas filtradas.
Comparación del cierre sigue en curso. No se tocó BAG1
original ni BAG2 estable. Smooth Presentation ya estaba activo: no se modificó
y no debe confundirse con nuevos frames de animación.

La primera sesión HQ terminó por `sdl_window_close`; se restauró su baseline
antes de la segunda, sin cerrar sesiones ajenas. Segunda sesión HQ cerrada de
forma controlada; settings, bindings, estado de mods y tres archivos de saves
originales verificados. La mejora de `game.toml` queda persistente.

**Captura inválida excluida:** vídeos `native-run-hq2/fever1.mp4` y `fever2.mp4`
de 22 s terminaron con imagen negra en captura gdigrab por ventana. Se detectó al
revisar sus contact sheets; no acreditan animación ni cierre. Las capturas PNG
con PrintWindow sí son visibles y prueban la mejora visual. Antes de volver a
grabar usar un piloto PrintWindow y comprobar píxeles; no repetir gdigrab sin
corregir el método. El vídeo anterior `native-run/fever1.mp4` sí es visible y
muestra giro en suelo y reinicio del clip también en BAG1 nativo; no demuestra
que la salida a pose final en partida sea correcta.

## Modelos/trajes: corrección verificada el 2026-11-03

El propietario aportó dos referencias de Heat BAG1: blanco/rojo y rojo/blanco.
El paquete anterior mezclaba modelos por lado, mientras los atlas seguían el traje:
`model_a_p2` usaba PLAYER4 y `model_b_p1` usaba PLAYER2. Eso cambiaba materiales,
paneles y colores. No era un simple recoloreado del TIM ni se resolvía por hash de
backup. El caso con Strike BAG2 conservaba el defecto.

Contrato nativo BAG1: carpeta PLAYER2=modelo A, PLAYER4=modelo B, sufijo A/B=P1/P2;
packs/atlas proceden de PLAYER1E y PLAYER3E respectivamente. La selección nativa
comparte el índice `side*14 + costume*28 + character` (SCUS_942.63 FUN_8003AE20).
El script legacy `build_heat_test.sh` también corregido en sus rutas de modelo;
no se ejecutó su antiguo rebuild destructivo. Se reutilizaron conversor, escritor
DFS y `alternate_payload.repack` existentes.

- Cambio limitado: miembros modelo 0 de entradas Heat 96 y 167. Motions, DBI,
  atlas y bancos de audio idénticos; las otras 17 entradas (incluidas ocho Strike)
  mantienen bytes. Conservado padding cero del miembro anterior.
- Evidencia/backup/report:
  `_work/character_import/heat/texture_diagnosis/20261103T060552Z-costume-model-fix/`.
  `body-source-palettes.png` muestra CLUTs fuente, no render runtime.
- Regresión `test_heat_costume_assets.py`: RED en A/P2 y B/P1, GREEN tras corrección.
  Suite host completa: 114 pruebas, más nueve casos C debug-option; log en evidencia.
- Build `20261103T060623074355Z-heat-costume-model-routing`. Payload 4759552 bytes,
  SHA-256 `a5996333f8de393ba3154297eb9650d9e0c50f949ea994d60b5346582cdf0776`;
  exe `b0f186feae9895efd1b714cd74cfad63e4e4ab3b4d52619d4b6c850986098e80`.
  Solo instalación experimental; backups coherentes antes de desplegar.
- Calibración `20261103T060712533062Z-heat-costume-routing-calibration`, cuatro
  aristas revisadas visualmente. Run `20261103T060900069128Z-heat-costume-routing-both-outfits`:
  Heat BAG1 P1/B y P2/A muestran rojo/blanco y blanco/rojo con paneles/llamas.
- Run inverso `20261103T061127414073Z-heat-costume-routing-reverse-full`:
  P1/A blanco/rojo y P2/B rojo/blanco revisados en captura; canción y retorno al
  selector en 162,9 s desde gameplay, salida de battle a 156,7 s. Trace incluye fever2;
  eso no acepta por sí solo fidelidad de coreografía/dueto. Ajustes y 21 saves
  preservados en ambos runs.

Aceptación de este seam: asignación visual por traje y lado recuperada según las
referencias. No declara todo Heat aceptado ni acredita la voz «Strike vs Heat»;
esa comprobación de audio sigue pendiente en el task Strike.

Código existente contrastado por ruta y función:
- `tools/bag1import/model_bag1_to_bag2.py`: adaptación del layout de modelo.
- `tools/bag1import/anim_remap.py`: política/dispatch Heat; no solver genérico.
- `tools/bag1import/patch_heat_dbi.py`: adaptación específica de huesos/accesorio.
- `tools/bag1import/audit_animation_roles.py`: auditor Heat, no aceptación universal.
- `tools/bag1import/preserve_announcer.py` y `restore_heat_winner.py`: adaptación
  de audio/nombre con límites propios. No sustituir bancos por número sin loader.

Para nuevas importaciones usar [pipeline](character-pipeline.md) y
[entradas alternativas](character-alternate-entries.md). No copiar el parche de
cabeza a Strike: el inventario Strike demuestra enlaces coincidentes y conserva DBI stock.

## Evidencia, no una nueva aceptación

Los resultados Heat anteriores (pasos, defensa, fever, voces, popups y cache)
están preservados en [registro histórico](archive/bag1-character-before-audit.md).
Consultar la sección concreta y verificar sus inputs/runtime/hashes antes de reutilizar.
No se reejecutaron esas capturas durante esta auditoría documental.

Las partidas nuevas Strike vs Heat en [Strike](strike-recovery.md) acreditan su
flujo indicado; no certifican automáticamente todo el movimiento/audio Heat.
El estado global Heat conserva gaps de transiciones/dueto; no etiquetar el conjunto
como «completo» porque una versión resumida antigua lo hacía.
