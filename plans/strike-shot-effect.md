---
id: strike-shot-effect-plan
title: "Plan: portar el efecto de disparo nativo BAG1 de Strike"
tags: ["strike", "bag1", "plan"]
summary: "Recuperar el fogonazo/efecto de disparo de BAG1 sin romper pecho/emblema ni la lógica de ataque BAG2."
related: ["notes/strike-recovery.md", "notes/character-pipeline.md"]
created: "2026-11-04"
updated: "2026-11-05"
doc_kind: plan
status: "in_progress"
---

# Objetivo

El propietario eligió portar el efecto nativo de BAG1 (opción 2), en vez de reapuntar la
copia de textura de BAG2. Aceptación: en VS, Strike BAG1 (A/B, P1/P2) muestra el efecto
de disparo equivalente a BAG1 en cada disparo; pecho/emblema siguen intactos (VRAM igual al
TIM BAG1); el proyectil, impacto y reacción del rival (lógica BAG2) no cambian; canción,
fever y retorno pasan.

# Hechos ya demostrados

- BAG1: eventos de animación tipo 16 → `FUN_800390D0` → tabla `0x80059424` (DBI del
  personaje); tipo 1 → `FUN_80039080` → tabla `0x800593B4`. Strike BAG1 dispara 5 veces
  `(16,f,1)` en el ataque.
- Importado: usa el DBI de BAG2; un solo `(16,26,0)`; sin evento 202. En el DBI BAG2,
  201/202 son copias `MoveImage` anuladas por pecho/emblema.
- DBI BAG1 de Strike: 5422 B, base `0x801DA778`, 1352 instrucciones; llamadas externas a
  `0x8004AE2C, 0x8004B47C, 0x800500FC, 0x8001DED8, 0x8004BF7C, 0x8004D044, 0x8004AFFC,
  0x8004B08C, 0x8004A5BC, 0x800350E4, 0x80035A30` (GTE/GPU/sonido). Precedente de port de
  un DBI BAG1: `tools/bag1import/port_bag1_stage.py` (escenario Heat).

# Fases

1. **Evidencia (sin cambios).** Capturar el ataque en VS en BAG1 nativo, BAG2 stock y BAG1
   importado (fotogramas en cada disparo + volcado VRAM). Identificar qué es el efecto
   (sprite, polígonos, textura/CLUT y región del atlas BAG1) y si el proyectil BAG2 ya se ve.
2. **Análisis estático del DBI BAG1.** Aislar el manejador tipo 16 y su rutina de dibujo;
   separar la parte visual de la lógica de ataque BAG1 (que no se porta). Mapear campos del
   bailarín (`+0x43xx` BAG1 → `+0x15xx` BAG2), globales y funciones del ejecutable.
3. **Puerta de decisión (propietario).** Elegir implementación según la fase 2:
   a) reubicar solo la rutina visual del DBI BAG1 con la herramienta de port existente, o
   b) reimplementarla en un plugin C que dibuje lo mismo con la textura BAG1.
4. **Implementación** con contrato reversible por hash/guard, tests host (RED→GREEN),
   build, despliegue experimental.
5. **Aceptación:** VS P1/P2 × A/B con ataques forzados, comparación visual con BAG1 nativo,
   VRAM de pecho/emblema intacta, partida completa con retorno.

# Progreso

- 2026-11-04: plan aprobado («continúa»). Fase 1 bloqueada en provocar ataques:
  autoplay 2P + `BAG2JP_CPU_SKILL=150` no produce ningún ataque en 60 s
  (`_work/versus-runs/20261104T231339675256Z-strike-attack-probe-p1a-1793834019`, sin anim74).
  Corrección del diagnóstico: `local_60[p]` identifica ataques en curso y sus papeles,
  no disponibilidad. No modificarlo para provocar ataques.
- Enganche automatizado autorizado (opción 2), implementado en el plugin de diagnóstico:
  `BAG2JP_TEST_STRIKE_ATTACK=1`, sitio `0x8009B084`, palabra esperada `0xAC510020`.
  Solo P1 Strike en VS japonés/fase de baile activa; introduce orden CPU `0x6E` y
  temporización perfecta. No escribe proyectiles, puntuaciones ni estado ganador.
  `bag2jp_attack_fixture.h` y `test_attack_fixture.py`: prueba host falla sin implementación
  y pasa con ella; incluye rechazo de región/fase/personaje y anchos byte/halfword.
  Primer intento runtime rechazaba la palabra completa `0x8005E754=FF000000`; el campo
  real es byte, y `0x8005E748` es halfword. Corregidas las máscaras, no el estado nativo.
- Verificación runtime: `attack-width-run.log` en `_work/character_import/strike/`
  identifica el run. El trace registra «test fixture: P1 Strike attack input 0x6E» y
  después P1 `anim74 req110` en combate. Automatización de ataque demostrada; captura
  sincronizada de ráfagas/VRAM y referencia BAG1 todavía pendientes. No equivale a efecto
  de disparo restaurado. Build/despliegue solo experimental; ejecutable previo en
  `strike/attack-hook-backup/BAG2JP.exe`; fixture de campaña preexistente del build preservado.
- Capturas nuevas con el mismo ejecutable `9a9800be1f320140d1307b9d40cfe6605bcc0fdaaf1e43f8f1b23e4aac4c41ad`,
  sin rebuild ni cambio del efecto. Selector recalibrado y revisado visualmente para ese
  hash: `_work/versus-runs/20261104T234205776195Z-strike-attack-calibration`; aprobación
  vinculada a las cinco imágenes originales y al grafo. No se omitió la guarda de revisión.
  Runners exploratorios en `_work/character_import/strike/`: `run_attack_capture.py`,
  `capture_attack_burst.ps1`, `summarize_attack_capture.py`.
  - Stock BAG2: `_work/versus-runs/20261104T234703334123Z-strike-attack-bag2`.
    Ráfaga de120 PNG reducidos; ataque capturado f7021–7147,28 capturas durante él.
    VRAM f7060/7120 dentro del mismo ataque. La hoja muestra impacto y caída de Heat.
  - Importado BAG1 en BAG2: `_work/versus-runs/20261104T235017173816Z-strike-attack-bag1`.
    Ráfaga de120 PNG; ataque f6958–7083,26 capturas durante él, VRAM f7000/7060.
    La hoja también muestra impacto/caída posterior. No prueba equivalencia con BAG1 nativo.
  - En ambas ráfagas, máximo salto entre heartbeats de capturas consecutivas:6 frames.
    El heartbeat se actualiza cada6; PrintWindow no garantiza fotograma guest exacto.
    Los ocho volcados por run son VRAM CPU (texturas/CLUT), no framebuffer GL.
  - Control sin `BAG2JP_TEST_STRIKE_ATTACK`:
    `_work/versus-runs/20261104T235238096302Z-strike-attack-bag1-control`.
    Ventana de15s tras entrar al combate:0 marcas del enganche y0 transiciones P1 anim74.
    Es una prueba acotada de inactividad, no aceptación de juego natural completo.
  - `capture-result.json`, `attack-summary.json`, `burst/burst.json` y hojas en cada run
    conservan hashes, tiempos y límites. Las tres pruebas restauraron ajustes/controles/mods
    y verificaron las21 partidas guardadas. No se tocó la instalación estable.
  - Atlas BAG1 A de ambos TIM idénticos en las8 muestras del importado. **No** todas las
    paletas son idénticas: CLUT del miembro4 cambia30 palabras en f7060 y vuelve a ser
    exacta en f7120; causa pendiente. Evidencia: `attack-chest-vram.json` y
    `attack-palette-difference.json` del run importado. No confundir atlas intacto con
    contrato CLUT completamente aceptado durante todo el ataque.
  - Primer intento de ráfaga falló por compartir archivos abiertos por el CRT del juego:
    `_work/versus-runs/20261104T234416955784Z-strike-attack-bag2`. Conserva VRAM/traza
    útiles, pero no ráfaga. Regresión `test_shared_trace.ps1` reproduce el rechazo de
    `ReadAllText` y verifica lectura con `FileShare.ReadWrite`; repetición runtime correcta.
## Fase 1 completada: referencia nativa en combate verificada

- Sesión `_work/character_import/strike/native-combat-runs/20261104T193849`:
  - Identidad de RAM viva comprobada (`0x1000000`, imagen del ejecutable, ring progresivo y punteros de bailarines
    `0x80137EAC` P1 Strike, `0x801AA004` P2 Heat). Tests de guardas en `test_native_ram_guard.py` (4/4 pasan).
  - Entrada sincronizada por ventana nativa (`native_attack_window`: compás múltiple de 4, delta 0..2, >=5 compases
    restantes, munición >0). Triángulo ordinario inyectado a compás 60, delta 1, remaining 5.
  - Ataque anim63 ejecutado en combate nativo y capturado:
    `_work/character_import/strike/native-combat-runs/20261104T193849/timed-shot-1793839879289203200`.
    Fotogramas `[63:0..9]` a `[63:55..0:3]` demuestran desenfunde, disparo con fogonazo en la boca del cañón,
    proyectil/trazador alargado amarillo-blanco, partículas de humo/chispas e impacto con derribo de Heat
    (ver `muzzle-crops-grid.png` y `sheet.png`).
  - Volcado de VRAM nativa en combate `gvram_dump.bin` (símbolo `vram`/`g_vram` a RVA 139800384): confirma
    CLUTs de P1 cargadas a (960, 0) y (976, 0), y páginas de textura del escenario y personajes.
  - Cierre verificado: seis archivos de configuración restaurados y cinco archivos de guardado intactos.

## Fase 2 completada: análisis estático del DBI BAG1

- Evento tipo 16 (`0x80059424` tabla de 14 punteros, Strike index 1): llama a `0x801DB920`.
  - `0x801DB920` → `0x801DAA70` itera sobre las 2 pistolas ($s0=0, 1).
  - `0x801DA81C` toma el hueso de la mano ($a1=0x14), calcula la posición 3D de la boca del cañón con GTE
    ApplyMatrixLV (`0x8004AE2C`), inicializa los buffers de partículas y sonido de disparo (`0x800350E4`, cue `0x1208`).
- Bucle de dibujo por fotograma (`0x80055924` tabla de actualización por bailarín, Strike index 1): llama a `0x801DB940`.
  - `0x801DB3F8` / `0x801DB43C`: actualiza el fogonazo de cada pistola.
  - `0x801DAB28`:
    - Proyecta los extremos 3D del trazador de la bala con GTE RotTransPers (`0x8004B47C`).
    - Calcula el vector perpendicular, construye un polígono cuadrangular texturizado semitransparente
      `POLY_FT4` (comando GP0 0x2E, tamaño 0x28, semi-transparencia modo 0x20, tpage en `0x16($a0)`, CLUT en `0x0e($a0)`).
    - Lo inserta en la tabla de ordenamiento (Ordering Table).
    - Para las chispas/humo: genera posiciones con `rand()` (`0x801DB26C`) y llama a `0x80035A30`, que emite
      partículas billboard 16x16 semitransparentes en la OT.
    - Para la animación de color del cañón: copia una fila de CLUT 16x1 con `MoveImage` (`0x8004D044`):
      fila 8 en cañón 1, fila 9 en cañón 2. (Esto explica la variación temporal de paleta observada en f7060).

## Fase 3: Decisión tomada por el propietario

El propietario eligió la **Opción A (Plugin C nativo en el motor)**:
Reimplementar el trazador de bala (`POLY_FT4`), partículas y fogonazo en código C dentro de
`bag2jp.feature.bag1-content`, enganchado a Strike BAG1 en vblank/draw.

## Fase 4: aproximación histórica (sustituida, no referencia del port actual)

- Creado módulo `mods-src/bag2jp.feature.bag1-content/bag2jp_strike_shot.h` y su cableado en
  `bag2jp_bag1_versions.c` (`b1v_vblank`).
- Tests host completados y pasando:
  - `tools/test/test_strike_shot_effect.py`: mock de RAM/OT/Heap en WSL gcc. Valida no-emisión fuera de combate,
    activación en anim74 frames 24..48 de Strike BAG1, emisión de `POLY_G4` / `DR_TPAGE` / chispas,
    avance de heap y enlace en OT slot 2.
  - `tools/test/test_strike_shot_math.py`: proyección 3D y geometría del haz de bala.
- Build runtime exitoso: SHA256 `91ca0689071df3d1c972d937bb96a286cfb523eea8c5fd87482d5b1d50fadbfd`.
  Calibración de selector renovada y revisada visualmente: `20261105T030648596457Z-strike-shot-calibration`.
- Primera prueba en combate (`20261105T032955635620Z-strike-attack-bag1`):
  El log `bag2jp_bag1_versions.log` registró 107 ejecuciones en la ventana de ataque anim74 frames 24..48.
- **Diagnóstico y corrección de coordenadas:**
  - El primer intento leía `dancer + 0x14E4`, que en realidad almacena la escala del bailarín (82 Strike / 85 Heat),
    no su posición en el mundo 3D.
  - Mediante `dump_dancer_struct.py` en combate real se descubrió la posición mundial 3D en `dancer + 0x14B8`
    (P1 x=-775, y=0, z=-147; P2 x=536, y=0, z=212).
  - La matriz de vista en `0x8005D0F0` (32 B) lleva la traslación combinada en `+0x14`.
- **Próximos pasos históricos (obsoletos; no ejecutar):**
  1. Actualizar `bag2jp_strike_shot.h` con el offset de posición `+0x14B8` y la traslación de la matriz `0x8005D0F0`.
  2. Compilar con `tools/workflow/bag2_workflow.py build --tag strike-shot-coords` y desplegar en experimental.
  3. Ejecutar captura de ataque (`run_attack_capture.py BAG1`) y revisar la hoja de capturas para confirmar
     que el trazador sale de las pistolas de Strike y llega al torso de Heat.
  4. Verificar que la VRAM del pecho/emblema no sufre modificaciones.
  5. Partida completa con retorno al selector.

## Port nativo: candidato experimental del 2026-11-05

El propietario autorizó sustituir la aproximación al observar que faltaban partículas
(«Sí continua»). El runtime llama ahora a `bag2jp_strike_bag1_tick`, no al tick aproximado.
Los helpers de `bag2jp_strike_shot.h` siguen compartidos con Heat.

- `bag2jp_strike_bag1_fx.h`: 20 disparos y 40 partículas; cinco eventos (26/31/36/41/46),
  dos pistolas por evento, vida 20 ticks y tres partículas por disparo al expirar.
  Conserva el orden nativo dibujo→actualización y cuatro dibujos por partícula.
- `bag2jp_strike_bag1_draw.h`: POLY_FT4 y UV/CLUT nativos; huesos 1B/1A, matriz +2C.
  Correcciones demostradas por test y captura: descriptor `[side*19+character]` y
  composición cámara×bailarín antes de la matriz del escenario. El callback DBI recibe
  temporalmente esa cámara compuesta (`FUN_8002C404`); vblank no.
- Tests host: nueve casos pasan entre `test_strike_bag1_fx`, `test_heat_flame_effect`,
  `test_attack_fixture` y `test_heat_dbi_face_patch`; el nuevo renderer se prueba con UBSan.
- Build/candidato instalado: `99f3f3b20fc8446bacf332b6a23c6485e34c4a4e417eabcf8234e10a0b27773a`.
  Workflow `_work/workflow/20261105T161405458824Z-strike-native-actor-frame` conserva backup.
  Calibración aceptada: `20261105T161438885567Z-strike-native-actor-frame-calib`.
- Captura: `_work/versus-runs/20261105T161556823304Z-strike-attack-bag1-heatbag1/shot-sheet.jpg`.
  P1 Strike BAG1/A contra Heat BAG2/A en HeatBAG1: trazadores junto a las pistolas,
  rival derribado, puntuación 300→0. Ajustes restaurados y 21 guardados verificados.
  **No aceptado:** persisten fragmentos blancos BAG2 y las partículas BAG1 no se distinguen bien.
- Atlas de efecto `005.tim` y diez CLUTs exactos en muestras de la captura
  `20261105T155619530504Z-strike-attack-bag1-heatbag1` (`strike-effect-vram-audit.json`).
  Esto no sustituye el control de pecho/emblema ni una auditoría temporal del último candidato.

### Siguiente paso anterior (sustituido por la aceptación visual de abajo)

Separar únicamente emisores visuales del DBI BAG2 importado, con palabras originales,
hashes y tests, preservando estados, resultados y cues. No anular `FUN_801cc2a0` completo.
En `_work/strikedbi/bag2_strike_decomp.txt`, `FUN_801ccc20` emite el quad de disparo;
`FUN_801cd0a0` llama al billboard `0x8002f0a4` pero también avanza/desactiva partículas;
`FUN_801cc7b8` mezcla billboard, distorsión y temporización; `FUN_801cd7e4` dibuja la
distorsión mientras `FUN_801cdab0` actualiza sus puntos. Esta separación es análisis
estático, todavía no un parche aplicado ni prueba causal de todos los fragmentos blancos.

Después: comparar partículas con la referencia nativa, VRAM de pecho/emblema durante
ataque, matriz P1/P2×A/B, canción/fever/retorno. El modo especial de escenario 0xB no
está implementado en el renderer (se omite); no declarar soporte global. Revisar índices
de pistola de traje B frente al inicializador parcheado antes de probar ese caso.

### Revisión en vivo solicitada: Heat BAG1 vs Strike BAG1, Heat BAG1

- Fixture opcional `BAG2JP_TEST_HEAT_STRIKE_DUEL=1`: alterna comandos nativos de
  ataque P1/P2 en el límite CPU; no cambia efectos, daño ni resultados. Conserva
  las guardas de región, fase, personaje y estado por lado (stride `0x32`).
- Tres tests de `test_attack_fixture.py` verdes; mutación P1-only rechazada por
  la aserción de P2. Build `20261105T163147017023Z-live-bag1-duel` correcto.
- Runtime experimental `c054ea2c313010cc130df47372628d2ee77c0bc0ed8a8963da68ca3dda5404a2`;
  respaldo del anterior en ese workflow. Calibración revisada y aceptada:
  `20261105T163240216399Z-live-bag1-duel-calib`.
- `_work/character_import/heat/run_live_duel.py` conserva la ventana abierta hasta
  que el propietario la cierre; después restaura ajustes y comprueba guardados.
  Journal: `_work/character_import/heat/live-duel-session.json`. Revisión visual
  del propietario inicialmente pendiente; resultado actualizado abajo.
- Sesión viva `20261105T163443254952Z-live-heat-strike-bag1`, PID `42744`:
  popup confirma ambas versiones BAG1/A y escenario observado Heat BAG1. Traza
  f8107–8109 confirma anim74 en ambos lados. Las entradas se alternan, pero ambas
  animaciones pueden comenzar en el mismo compás: no se ha probado separación
  temporal de los ataques. Diez tests host pasan; ventana dejada al propietario.
- Resultado del propietario: «Okay, visualmente lo veo bien» tras la demostración.
  Aceptación visual del caso Heat BAG1/A vs Strike BAG1/A en Heat BAG1, con ambos
  ataques; no extiende aceptación a traje B, otros escenarios ni matriz completa.
  La eliminación de efectos BAG2 superpuestos deja de ser una corrección visual
  obligatoria por defecto: conservar el resultado aprobado y consultar antes de
  cambiarlo. Siguen pendientes las comprobaciones técnicas y de cobertura.

### Tanda de cobertura aprobada (2026-11-05)

El propietario solicita continuar con los pendientes y agrupar los casos en una
ejecución si es posible. Conservar los efectos aprobados; no confundir fixtures
de entrada con juego natural ni inyección temporal de luz con solución persistente.

| Paso | Caso / comprobación | Estado |
|---|---|---|
| 1 | P1 Strike BAG1/A vs Heat BAG1/A, Heat BAG1 | pendiente |
| 2 | P1 Heat BAG1/A vs P2 Strike BAG1/A, Heat BAG2 | pendiente |
| 3 | P1 Strike BAG1/B vs Heat BAG1/A, Heat BAG2 | pendiente |
| 4 | P1 Heat BAG1/A vs P2 Strike BAG1/B, Heat BAG1 | pendiente |
| 5 | Auditar luz facial, pistolas B y VRAM de ataque de esos casos | pendiente |
| 6 | Ending View Strike y escenario especial 0xB: recorrido separado | pendiente |

Pasos 1–4: una orden por lote, procesos secuenciales por las guardas diferentes
de los fixtures actuales. Cada caso exige picks observados, captura de ataque,
fases registradas, canción completa y retorno; una ausencia de Fever observado no
se transforma en aprobación por llegar al selector. Respaldo/restauración por caso.
Verificación prevista: `py -3.13 tools/test/strike_acceptance_batch.py --execute`;
regresión del organizador: `py -3.13 -m unittest tools.test.test_strike_acceptance_batch`.
Bloqueadores: 5 depende de 1–4; 6 requiere su propia navegación verificada, no
hereda aceptación de versus. No cambiar el ejecutable instalado mientras se mide.

Hallazgos durante la tanda (desplegados como candidato, no aceptados visualmente):
- Diagnóstico posterior: el candidato `6dc97e0d` **no prueba iluminación aplicada**.
  Su primer caso no registra el mensaje de aplicación. El shard generado 09 no
  despacha `psx_mod_function_entry` en `8002C404`: el generador exige la lista
  `mod_function_entry_funcs`, ausente de la configuración. Regresión de configuración
  rojo→verde; añadido el opt-in a `patches/BAG2JP-game.toml`. Tres tests de luz pasan,
   regeneración y build completados; falta observar el callback real antes de aceptar la cara.
  No editar C generado a mano. Generación aislada en `_work/strikedbi/lighting-codegen`;
  el emisor Windows existente sale 1 sin diagnóstico. Se compila un emisor nativo
  local con dependencias vendorizadas, sin cambiar pins ni instalar herramientas.
- DBI B de entradas 145/146 fuerza el inicializador A: la rama en offset 10480
  está anulada y asigna pistolas 1A/1B. El renderer restaba uno por traje; corregido
  y fijado con test RAM A/B y palabras del payload real (rojo→verde).
- `FUN_80022FF4` reconstruye luces y las copia a bailarines. Solución candidata:
  perfil nativo solo en estructuras de Strike BAG1, al entrar en `FUN_8002C404`,
  antes de dibujar. Sin tocar luces globales, escenario ni rival; omitir fades
  temporizados y fases ajenas a combate normal. Perfil contrastado con captura
  nativa de `face_audit/live-lighting-with-head.json`.
- Usar function-entry del plugin existente `bag2jp.bag1_versions`, guardado por
  palabras `27BDFF68/AFB20088/00809021` de SLPM JP. El jr final de luces no tiene
  instrumentación de instruction-hook en el C generado; no añadir un hook inerte
   ni modificar el framework: el opt-in del generador es necesario para el main compilado.
- Tras cerrar la tanda basal: build/calibración nuevos y repetir matriz en el
  candidato corregido; aceptación visual nueva de la luz sigue siendo necesaria.

Resultado basal: `20261105T164657339941Z-strike-acceptance-batch`, ejecutable
`c054ea2c…`, cuatro casos con ataques y retorno observado a raíz 13. Ajustes y
21 guardados restaurados por caso. Los 32 dumps conservan atlas 004/005 exactos
frente a sus variantes nativas admitidas (incluida la copia de pecho); no implica
aceptación visual de materiales. Fever observado únicamente en P1/A Heat BAG1.

Candidato instalado `6dc97e0dcce6e985354c4b8256fc48fa92030555893c7682297c4d727177af3c`:
build `20261105T170340171860Z-strike-lighting-render-proof`, respaldo de `c054ea2c…`
en ese workflow, calibración `20261105T170512060701Z-strike-lighting-b-guns-calib`
revisada y aceptada. Incluye corrección de pistolas B y luz actor-local; payload
sin cambios. Segunda tanda terminada: `20261105T170727021619Z-strike-acceptance-batch`,
cuatro casos con ataques, canción/retorno y restauración verificados; 32 dumps con
cero diferencias de atlas 004/005 frente a las variantes admitidas. Esto verifica
la ejecución y conservación de texturas, no acepta globalmente los materiales ni
la luz. Los sheets de ataque quedan disponibles por caso; P2/B revisado sin fallo
evidente de modelo, pero las capturas escasas no prueban cada fogonazo de pistola.
El organizador rechaza también un fallo en el cuarto
caso o una restauración no verificada (mutación del criterio anterior detectada).

Generación corregida: `_work/strikedbi/lighting-codegen/report.json` confirma que
solo cambia `SLPM_862.19_full_09.c`, añadiendo el despacho function-entry. Emisor
nativo compilado offline desde el framework fijado; respaldo del shard y `game.toml`
en `lighting-codegen/stage-backup`. Diecisiete tests host pasan. Build
`20261105T172504139699Z-strike-lighting-entry-enabled` correcto, aún sin desplegar
ni calibrar. No atribuir a este build las dos tandas anteriores. Ending View se
prueba separadamente con el instalado `6dc97e0d`; no prueba el ending de campaña.

# Límites

Solo experimental. No se porta la lógica de ataque BAG1. No se reactiva la copia de
textura BAG2. La fase 1 necesita ataques: usar CPU agresiva (`BAG2JP_CPU_SKILL>=140`) o
la entrada de ataque del harness; en BAG1 nativo, una partida con ataques.
