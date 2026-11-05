---
id: strike-shot-effect-plan
title: "Plan: portar el efecto de disparo nativo BAG1 de Strike"
tags: ["strike", "bag1", "plan"]
summary: "Recuperar el fogonazo/efecto de disparo de BAG1 sin romper pecho/emblema ni la lógica de ataque BAG2."
related: ["notes/strike-recovery.md", "notes/character-pipeline.md"]
created: "2026-11-04"
updated: "2026-11-04"
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

## Fase 4 (en curso): Implementación de la Opción A

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
- **Próximos pasos inmediatos (para continuar en la siguiente sesión):**
  1. Actualizar `bag2jp_strike_shot.h` con el offset de posición `+0x14B8` y la traslación de la matriz `0x8005D0F0`.
  2. Compilar con `tools/workflow/bag2_workflow.py build --tag strike-shot-coords` y desplegar en experimental.
  3. Ejecutar captura de ataque (`run_attack_capture.py BAG1`) y revisar la hoja de capturas para confirmar
     que el trazador sale de las pistolas de Strike y llega al torso de Heat.
  4. Verificar que la VRAM del pecho/emblema no sufre modificaciones.
  5. Partida completa con retorno al selector.

# Límites

Solo experimental. No se porta la lógica de ataque BAG1. No se reactiva la copia de
textura BAG2. La fase 1 necesita ataques: usar CPU agresiva (`BAG2JP_CPU_SKILL>=140`) o
la entrada de ataque del harness; en BAG1 nativo, una partida con ataques.
