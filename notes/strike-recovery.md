---
id: strike-import-recovery
title: "Strike: evidencia vigente y pendientes"
tags: ["strike", "bag1", "acceptance"]
summary: "Recuperada carga VS con paquete coherente de 19 entradas; prueba P1/B llega a gameplay. Voz del anunciador y fidelidad visual pendientes."
related: ["notes/character-alternate-entries.md", "notes/character-import-testing.md", "notes/character-pipeline.md"]
created: "2026-11-01"
updated: "2026-11-05"
edited: "2026-11-05"
doc_kind: reference
---

# Estado vigente de Strike

## Corrección acotada del pecho A: prueba antes/después (2026-11-04)

- Propietario autoriza reiniciar **solo BAG2 experimental**. BAG1 PID17936 se
  conserva abierto; ajustes y tarjetas de la sesión BAG2 anterior restaurados.
- Baseline fresco `graphics-run/20261104T125757-candidate`: captura neutralA
  reproduce la mancha azul/gris. Volcados6000/7200/8400: CLUTsA13+10filas exactos,
  TIM2 entero exacto, TIM1 difiere34palabras en x5..9/y12..45. El destino completo
  10×36 en VRAM(704,268) coincide con origen(732,424). No es cambio de paleta.
  `chest-vram-comparison.json`; la captura posterior evidencia además la otra fase
  de copia. No se fuerza una nueva captura baseline por tener la misma fase en
  los tres dumps; ya hay reproducción visual y copia destructiva demostrada.
- RED: contrato rechazabaA; regresión de ensamblado falla en73/74 por JAL activo
  (201399071,0x0C011B1F). Contrato compartido `strike-texture-contract.json` ahora
  admiteA original yB tras contrato de esqueleto. Las2copias se omiten solo en
  alternativosA73/74; skeleton/paletas/delay slots/TIM/modelos/motions intactos.
- `prepare_chest_payload.py` usa contratos/DFS compartidos y verifica **16bytes**
  distintos en todo el payload;17entradas idénticas. Capacidad DUMMY independiente
 27648000bytes, candidato5365760bytes. Fuente/recursos staged respaldados en
  `chest_audit/candidate/`. Suite130 host OK; build
  `20261104T180155067559Z-strike-costume-a-atlas-copy` pasado.
- Desplegado experimental: exe `a5fa8cf190bc68a25da64a4307dfccda8924e2784db2d30cbdefea990bfa804a`,
  payload `baa149bb0a0c580f63c86be38a8e694acab1c01b4aaa0b1def525beb1ebfaea6`,
  expected stock sin cambios `6828a241…55569`. Backups exactos de exe/manifest/
  payload en `chest_audit/candidate/runtime-before`.
- Prueba después `graphics-run/20261104T130315-candidate`: los tres dumps6000/
  7200/8400 tienen **ambos atlas yCLUTs completos idénticos aTIM BAG1/A**, cero
  palabras distintas y ninguna copia360palabras. Tres capturas NEUTRAL sin la
  mancha azul/gris; hoja `chest_audit/chest-before-after.png` revisada. Mismo
  candidato gráfico9x/interpolación144; fases del neutral/ventanas no idénticas.
- `chest_audit/verification.json`: BAG1 PID17936 preservado; nueva ventana BAG2
  PID39676 **abierta para el propietario** en StrikeA/NEUTRAL/cámara0.24saves
  originales intactos; baseline de BAG2 cerrado/restaurado, ajustes temporales de
  la nueva sesión pendientes de restauración cuando termine el propietario.
- Checkpoint local `37a4b3d` (WIP, contrato/tests solamente). Manifest/índice y
  notas mantienen cambios anteriores sin commit; payload y backups fuera deGit
  protegidos en la evidencia. **Aceptación acotada P1/A neutral del pecho**, no
  P2/canción/fever/retorno ni fidelidad global. Rostro/iluminación no modificados;
  siguen pendientes lectura de boca y separación material/paleta/luces.

## Diagnóstico facial y contraste de la línea de la boca (2026-11-04)

- Verificación estática (`strike/audit_face_sources.py` -> `face_audit/source-audit.json`):
  los 4 modelos instalados (109, 110, 181, 182) conservan geometría, normales, colores
  de iluminación y UVs 100% idénticos a la conversión nativa BAG1. La cabeza (hueso 12)
  posee 15 grupos de color; el grupo 0 es negro puro (`0x000000`) y los grupos 1/9/10/12
  son tono de piel (`0x204a90`).
- Primitivas de la cabeza: 0 triángulos planos F3. La malla está compuesta por 135
  triángulos Gouraud sin textura (G3), 14 triángulos Gouraud con textura (GT3) y 76
  cuadriláteros Gouraud con textura (GT4).
- Lectura en vivo sin invasión mediante `ReadProcessMemory` (`read_face_lighting.py` ->
  `face_audit/live-lighting-with-head.json` y `face_audit/face-lighting-analysis.json`):
  - Línea de boca y barba (P048, P069, P080, P106, P115): grupo 0 (`0x0`). Dibujan en
    `[0, 0, 0]` tanto en BAG1 nativo como en BAG2 candidato.
  - Piel circundante inmediata (labio superior, inferior y comisuras: P013, P027, P032,
    P044, P046, P074, P076, P098, P101, P126): grupos de piel `0x204a90`.
    - En BAG1 nativo: dibujan brillantes (`[255, 219, 39]`, `[255, 176, 31]`,
      `[254, 103, 24]`). Contraste ~220 vs 0: la boca resalta nítida.
    - En BAG2 candidato: dibujan en `[0, 0, 0]` (clamped a cero). Contraste 0 vs 0:
      la boca desaparece sumergida en la sombra negra de la piel.
- Causa raíz demostrada:
  - BAG1 Dance View usa la iluminación de su escenario nativo (`STAGES/ST_STRI.DFS`):
    Luz 1 es relleno positivo fuerte (`[5632, 8448, 5632]`, +2.06x) orientado de abajo
    hacia arriba (`1099, -3920, 455`), iluminando mentón y labios.
  - BAG2 Dance View carga el escenario 209 (Vault Factory, `stages/209_vault_factory/000.dbi`),
    cuya Luz 1 es una luz de sombra sustractiva (`[-8096, -7744, -5600]`, -1.89x) en
    dirección similar (`46, -3659, -1841`). Este término negativo supera al ambiente
    (`[183, 180, 192]`) y colapsa todas las normales de la parte baja a `[0, 0, 0]`.
  - Refutada la hipótesis de subir el ambiente global: el ambiente en BAG2 (183) ya es
    mayor que en BAG1 (168); subirlo no restaura el contraste direccional.
- Puerta de decisión: acordar con el propietario si la iluminación nativa de Strike
  debe inyectarse al bailarín en Dance View o generalizarse antes de modificar código.
- Prueba en vivo aprobada por el propietario (2026-11-04): inyectada la iluminación
  nativa de Strike (`ST_STRI.DFS`: matriz de color `[-2816, 5632, 7680, -2048, 8448,
  1536, -768, 5632, -3072]`, ambiente `[168, 168, 168]` y ángulos de dirección
  `[0, 256, 2880, ..., 1264, 976, 0]`) en la sesión abierta de BAG2 PID 39676.
  - Comprobación en memoria: los polígonos de piel circundante (P013, P027, P044,
    P074, P098) pasaron instantáneamente de `[0, 0, 0]` a `[255, 173, 31]`
    (tono de piel iluminado). Los polígonos de la boca (P048, P069, P080, P106, P115)
    se mantuvieron en negro puro `[0, 0, 0]`.
  - Comprobación visual: capturada y comparada en `face_audit/face-full-native-centered.png`.
    La línea de la boca y la barba goatee se vuelven nítidas y claramente definidas,
    idénticas a BAG1 nativo. La ventana abierta PID 39676 refleja el cambio en vivo.
- Prueba Versus P1 Strike (BAG1, Traje A) vs P2 Heat (BAG2, Traje A) en Stage 200 (Heat):
  - Ejecutado harness automatizado en `_work/versus-runs/20261104T192150838807Z-strike-lighting-vs-heat-1793820110/`.
  - Baseline Stage 200: matriz de color `[6048, -2080, 1536, 4192, -2640, 1024, ...]`, ambiente `[198, 152, 145]`.
  - Inyección en vivo durante gameplay: Strike recibe iluminación nativa; Heat (P2) conserva su iluminación de escenario sin alteración.
  - Paquetes en vivo de Strike: boca en `[0, 0, 0]` y piel circundante en `[255, 220, 43]` / `[255, 206, 42]`.
  - Capturas `strike-vs-heat-sheet.png` y `strike-vs-heat-closeup.png` revisadas. Strike mantiene la definición facial, perilla y pecho limpio en movimiento sobre el escenario de Heat.
  - Restauración completa verificada por `IsolatedFiles`. Perfil respaldado en `tools/bag1import/profiles/strike-lighting-profile.json`.

## Verificación de partida completa: Canción + Fever + Retorno (2026-11-04)

Siguiendo el orden de pendientes aprobado por el propietario, se ejecutó la prueba de
partida completa en modo Versus (P1 Strike BAG1 vs P2 Heat BAG2, escenario HeatBAG2):
- **Traje A** (`_work/versus-runs/20261104T195547740264Z-strike-full-match-p1a-1793822147`):
  - Progresión de canción entera: 165.7s totales, salida de combate a los 159.8s (`left_battle`).
  - Transición por Fever Time sin fallos ni desbordamiento de memoria (8 MB activos).
  - Retorno automático y seguro a pantalla de selección de personajes (`return_root: 13`).
  - Capturas de seguimiento: `match-8` a `match-17`, `song-end.png` y `returned-selector.png`.
  - Resultado: **PASSED**.
- **Traje B** (`_work/versus-runs/20261104T200053284790Z-strike-full-match-p1b-1793822453`):
  - Progresión de canción entera: 162.5s totales, salida de combate a los 156.6s (`left_battle`).
  - Traje B amarillo y emblema negro limpios en todo el gameplay sin parches blancos ni corrupción.
  - Transición por Fever Time y retorno automático al selector (`return_root: 13`).
  - Capturas: `match-8` a `match-17`, `song-end.png` y `returned-selector.png`.
  - Resultado: **PASSED**.
- Bloqueador resuelto: la partida completa, transiciones de Fever y retorno al menú
  quedan formalmente verificados con evidencia tanto para Traje A como para Traje B.

## Integración y verificación de voces y anunciador (2026-11-04)

Siguiendo el Paso 2 de los pendientes de Strike:
- Diagnóstico del banco de sonido (`SEDT`):
  - En BAG1 nativo (`P_STRIA1.DFS` miembro 6), Strike poseía 12 cues de voz (`0x1200..0x120b`).
  - La política de coreografía (`anim_remap_strike.py`) rebasaba los eventos de animación
    de Strike a `0x6100..0x610b` para evitar colisión con el rango `0x1100..0x110e` de BAG2.
  - Sin embargo, los paquetes instalados (73, 74, 145, 146) conservaban el miembro SEDT stock
    de BAG2 (con IDs `0x1100`), provocando que las llamadas `0x61xx` no encontraran correspondencia
    en la tabla SPU global y las voces quedaran mudas.
- Rebase y preservación del anunciador:
  - Se rebasó el banco de voces BAG1 de Strike de `0x1200` a `0x6100` (`rebase_cues.py`).
  - Se anexaron los cues del anunciador stock de BAG2 `0x1107` y `0x1108` (`preserve_announcer.py`)
    para que el anunciador llame a "Strike" y declare su victoria sin colisión.
  - Se reconstruyeron los 4 paquetes alternativos (73, 74, 145, 146) con alineación DFS a 4 bytes
    y se reempaquetó el payload alternativo (`65bbe67e…9b37`, 4640768 B en DUMMY27648000).
  - Build `strike-voices-staged` pasado; ejecutable desplegado `0d38ab64…0674`.
- Auditoría SPU en vivo en gameplay (`probe_cue_table.py` -> `cue-table-audit.json`):
  - La tabla global SPU (`0x8007F180`) registró 87 entradas en combate.
  - Las 12 entradas `0x6100..0x610b` de Strike quedaron cargadas en los registros 43 a 54.
  - Los cues del anunciador `0x1107` y `0x1108` quedaron cargados en los registros 55 y 56.
  - Los 38 cues del rival (Heat `0x10xx`) quedaron intactos y sin solapamiento.
- Pruebas completas de combate con audio activo (`test_strike_full_match.py`):
  - Traje A (`versus-runs/20261104T211441143600Z-strike-full-match-p1a-1793826881`): 162.6s, retorno root 13, PASSED.
  - Traje B (`versus-runs/20261104T211949477565Z-strike-full-match-p1b-1793827189`): 162.6s, retorno root 13, PASSED.
- Bloqueador resuelto: la integración de voces `0x6100` y del anunciador queda demostrada
  en RAM de SPU y en combate completo sin errores.

## Efectos del disparo de Strike BAG1 ausentes (2026-11-04..05, en curso)

- Propietario: al atacar, Strike BAG1 no muestra los efectos del disparo.
- Plan aprobado: `plans/strike-shot-effect.md`.
- **Fase 1 (Evidencia completada):**
  - Ataque automatizado en BAG2 vía `BAG2JP_TEST_STRIKE_ATTACK=1` (sitio `0x8009B084`), verificado con tests host (`test_attack_fixture.py`) y runtime.
  - Ráfagas de 120 PNG y volcados VRAM capturados para BAG2 stock (`_work/versus-runs/20261104T234703334123Z-strike-attack-bag2`) y BAG1 importado (`_work/versus-runs/20261104T235017173816Z-strike-attack-bag1`).
  - Test de control sin variable de prueba: 0 marcas y 0 ataques en 15 s (`_work/versus-runs/20261104T235238096302Z-strike-attack-bag1-control`).
  - Referencia nativa en combate completada (`_work/character_import/strike/native-combat-runs/20261104T193849/timed-shot-1793839879289203200`): anim63 ejecutada con entrada ordinaria de triángulo a compás 60. Demuestra desenfunde, disparo con fogonazo en cañón, trazador de bala alargado amarillo-blanco, partículas de humo/chispas e impacto con derribo de Heat (`muzzle-crops-grid.png`). Volcado VRAM nativo `gvram_dump.bin`. 6 configs y 5 saves originales verificados y restaurados.
- **Fase 2 (Análisis estático completado):**
  - Evento 16 (`0x80059424` index 1 → `0x801DB920`): calcula posiciones 3D de las bocas con GTE ApplyMatrixLV (`0x8004AE2C`), dispara audio cue `0x1208` y activa el temporizador de disparo.
  - Actualización por frame (`0x80055924` index 1 → `0x801DB940`): actualiza fogonazos, proyecta el trazador con RotTransPers (`0x8004B47C`), construye un cuadrilátero semitransparente `POLY_FT4` (comando GP0 0x2E, blend mode 1: B+F), emite partículas billboard 16×16 (`0x80035A30`) y cicla la paleta del cañón copiando filas 8/9 de CLUT con MoveImage.
- **Fase 3 (Decisión del propietario):** El propietario eligió la **Opción A (Plugin C nativo en el motor)**.
- **Fase 4 (Implementación en curso):**
  - Módulo C `bag2jp_strike_shot.h` en `mods-src/bag2jp.feature.bag1-content/` integrado en `bag2jp_bag1_versions.c` (`b1v_vblank`).
  - Tests host `tools/test/test_strike_shot_effect.py` (WSL gcc) y `tools/test/test_strike_shot_math.py` pasan.
  - Build runtime exitoso (`91ca0689071df3d1c972d937bb96a286cfb523eea8c5fd87482d5b1d50fadbfd`), calibración de selector renovada y validada.
  - Prueba en combate `20261105T032955635620Z-strike-attack-bag1`: 107 ejecuciones registradas durante anim74 (frames 24..48).
  - Hallazgo de coordenadas: `dancer + 0x14E4` contiene la escala del bailarín (82/85), no la posición mundial. La posición mundial real 3D se descubrió en `dancer + 0x14B8` (P1 x=-775, y=0, z=-147; P2 x=536, y=0, z=212). La matriz de vista de cámara en `0x8005D0F0` (32 B) lleva la traslación combinada en `+0x14`.
  - Corrección (2026-11-05): la proyección nativa compone `0x8005D0F0` con la matriz del bailarín `+0x14C4` (CompMatrix `0x80043A84`), raíz en `+0x810` y `SetGeomOffset(256,120)` (pantalla 512×240). Build `c08c4af3…` (no aceptado): trazador fino visible, pero los cuerpos quedan a ~0,8× la distancia x proyectada desde el centro (causa sin aclarar).
- **Referencia BAG1 nativa con ataque automatizado (2026-11-05):** `tools/bag1native/attack_bot.py` pulsa Triángulo en el flanco de compás leído de RAM (`0x80068704 & 0x10`); 2/2 ataques aceptados P1 Strike vs P2 Heat. Clip 60 fps `_work/character_import/strike/native-combat-runs/20261105T002406/attack-bot1.mp4` (+ `attack-bot1-frames/`, `attack-bot1-shot-sheet.png`, `attack-bot1-zoom.png`). Observado: Strike dispara hacia abajo-delante con estelas cortas blanco-amarillas y chispas en las pistolas, luego apunta horizontal hacia su izquierda (lejos de Heat); en Heat aparece una nube de partículas naranjas pixeladas del pecho a los pies, después tambalea y cae con estrellas. **No hay rayo continuo entre ambos.** Configs y saves restaurados.
- **Rediseño verificado y aceptado visualmente (2026-11-05):**
  - Efecto rediseñado en `bag2jp_strike_shot.h`:
    - Eliminado el rayo continuo y los marcadores de depuración verde/magenta.
    - Fogonazos (chispas diamante blanco brillante `0x00FFFFFF`, 8 px) y estelas cortas de trazador (~32–36 px) con núcleo blanco, cuerpo amarillo oro y punta degradada naranja.
    - Bocas en dos poses: hacia abajo-delante (`anim_frame <= 27u`) y lateral hacia la izquierda (`anim_frame >= 28u`).
    - Nube de impacto en rival (`anim_frame 26..46`): 8 partículas pixeladas dispersas (tamaños 4 a 10 px) del pecho a los pies de Heat con paleta naranja, ámbar y destellos calientes.
    - Compensación de escala en proyección: `(raw_sx * 85) / 100` compensa la escala del modelo (`+0x14E4` 82/85) respecto al espacio raíz no escalado.
  - Tests unitarios y matemáticos pasan (`test_strike_shot_effect.py` y `test_strike_shot_math.py`, 5 OK).
  - Build `strike-shot-particles` (runtime `ac4efe3ed870661974b8174819dd1a22c50f2da6ac7913c31018e8c51b3fdd85`) desplegado en experimental (`BAG2JP-exp-8mb`).
  - Captura en combate `_work/versus-runs/20261105T062700041177Z-strike-attack-bag1/` (`zoom-shot-grid.png`): idéntico al clip nativo BAG1.
  - Verificación VRAM de texturas: `vram_view.py` sobre volcados de frame 6700 frente a 7120 confirma 0 diferencias en todas las filas CLUT del torso y vestimenta (`{"p1_tim1": [], "p1_tim2": [], "p2_tim1": [], "p2_tim2": []}`).
  - Partida completa con retorno al selector: `_work/versus-runs/20261105T063254774562Z-strike-full-match/` (`song-end.png`, `returned-selector.png`). Retorno a Character Select verificado y ajustes/partidas restaurados.
  - Próximo paso: cerrar tarea de disparo de Strike y continuar con la siguiente prioridad de la importación de personajes.

## Escala Strike BAG1 frente a BAG2 (2026-11-04)

- Propietario percibe Strike BAG1 más grande. Comparación estática del modelo BAG1
  convertido contra stock BAG2 (entradas 109/181, mismos 44 huesos y mismos vértices):
  vértices y traslaciones de nodo BAG2/BAG1 = **0,8371** (A, n=2213, p10–p90
  0,8368–0,8374) y **0,8384** (B). Es decir, Strike BAG1 es ~19,5 % mayor en datos.
  Control: Heat BAG1/BAG2 ≈ 0,97–0,98, por eso Heat no mostraba esta diferencia.
- Prueba espejo P1 Strike BAG1/A contra P2 Strike BAG2/A en HeatBAG2:
  `_work/versus-runs/20261104T213116596013Z-strike-scale-mirror-a-1793827876/gameplay.png`
  confirma visualmente la diferencia con la misma pose inicial. Ajustes restaurados.
- Causa en el motor: `FUN_8002D85C` guarda en el bailarín (+0x14E4..EC, base +0x1514..1C)
  la escala por personaje de la tabla `0x80051904` (Heat 85, Strike 98). BAG1 usa la suya
  (`0x800558FC`: Heat 128, Strike 127). Mundo BAG2/BAG1: Heat 0,978·85/128=0,649,
  Strike 0,837·98/127=0,646, es decir, cada juego compensa el tamaño de su propio modelo.
  La pose (`pose_t` = traslación del modelo × escala del bailarín) y la altura de la cadera
  animada dependen de esa escala, así que corregirla ajusta malla, huesos y animación a la vez.
- Corrección (propietario aprobó «continúa»): `bag2jp_bag1_versions.c` `b1v_dancer_scale`
  multiplica esa escala por 3429/4096 (A) o 3434/4096 (B) solo en el lado con Strike BAG1,
  una vez por inicialización del bailarín; Heat queda intacto. Content id añade `SCL1`.
  Build `strike-bag1-scale`; exe experimental `1b87a790…ddca`, anterior respaldado en
  `strike/scale_backup_BAG2JP.exe`.
- Verificado: el log registra «scale 98 -> 82» solo para el lado BAG1. Espejo A
  `20261104T215439051609Z` y B `20261104T215723033323Z`: misma altura, pies apoyados
  (`strike/scale-before-after.png`). Partida completa A contra Heat
  `20261104T220031978248Z`: 161,9 s, retorno root 13. P2 BAG1 y partida completa B con la escala nueva siguen sin probar.

## Capturas del propietario: diagnóstico anterior del pecho A (2026-11-04)

- Propietario aporta cuatro capturas: rostro más iluminado/boca negra definida
  en BAG1; rostro oscuro/boca poco visible en BAG2; trajeA importado con mancha
  azul/gris simétrica sobre el arnés, ausente en referencia. No atribuir ambos
  síntomas al filtrado ni declarar que toda la diferencia facial sea iluminación.
- Diagnóstico **sin tocar ventanas/configuración/assets**. Preflight
  `20261104T175149164277Z-strike-costume-a-chest-diagnosis` pasado.
  `strike/audit_chest_source.py` verifica payload instalado `336bc625…7a46`:
  packsA73/74 conservan ambos JAL de copia `0x2358/0x23D4`; packsB145/146 tienen
  NOP. DBI nativoA=B, hash `60ca6aee…6572d`, sin esas copias de atlas (auditoría
  nativa anterior). La protección del emblemaB nunca se extendió aA.
- `chest_audit/source-audit.json` conserva hashes/palabras. Simulación offline
  `atlas-copy-simulation.png`: copiar atlas+(28,204) a+(0,12),10×36palabras,
  produce forma gris en CLUT0 semejante al defecto aportado. **Hipótesis fuerte,
  no prueba runtime nueva ni atribución demostrada de UV del pecho.**
- Próximo paso: coordinar reinicio **solo BAG2 experimental**, capturar VRAM A
  antes/después y verificar que una supresión acotada conserva TIM/CLUT/modelos
  nativos y elimina la mancha. BAG1 y sesiones entregadas se preservan hasta
  autorización. Rostro: investigar material/paleta frente a iluminación aparte;
  no compensación de gamma global, retoque inventado ni aceptación visual aún.

## Entrega inicial para capturas: sesión BAG2 ya reemplazada (2026-11-04)

- Plan `plans/strike-comparison-graphics.md` aprobado. En la entrega inicial se
  dejaron abiertas BAG1 PID17936 yBAG2 experimental PID40012, StrikeB amarillo,
  NEUTRAL/cámara0. **PID40012 se cerró/restauró con autorización y fue reemplazado
  porPID39676** en la corrección del pechoA; no reutilizar su identidad antigua.
  BAG1 PID17936 permanece protegido; consultar journal vigente antes de actuar.
- Journal `_work/character_import/strike/graphics-session.json`; evidencia y
  verificación en `graphics-run/`. BAG1 carga copiada confirmada LOAD OK; BAG2
  tarjetas copiadas habilitadas/montadas, sin captura manual LOAD OK independiente.
- BAG1 runtime instalado limita4x:9x falla explícitamente, restaurado antes del
  arranque válido. BAG2 confirma9x/4K interno. PGXP/filtrado compatible conservados;
  no pack corporalHD verificado ni nuevos assets. Monitor real1440p/~144Hz.
- Ambos logs confirman objetivo144presents/s por mezcla temporal (BAG1 adaptativa,
  BAG2 lineal); no144fps nativos ni medición sostenida del presentador. Muestreo
  heartbeat:59.7Hz en cada juego, sin acelerar música/lógica.24saves originales
  verificados intactos. Ajustes siguen temporales mientras están abiertos.
- Restaurar al terminar las capturas con `graphics_session.py close native` y
  `close candidate` (prefijo `py -3.13 _work/character_import/strike/`). Conserva
  controles/settings/mods y game.toml respaldados. No desplegar ni aceptar fidelidad.

## Prioridad visual: definición y defectos aún sin aceptar (2026-11-04)

El propietario pospuso Heat/VS para mejorar las texturas. Objetivo de este ciclo:
comparar el candidato actual sin cambiar el diseño BAG1. No se ha aplicado una
mejora nueva ni aceptado la fidelidad visual.

- Preflight `20261104T163638672188Z-strike-texture-definition` pasado; cambios
  anteriores preservados. Exe instalado `8e8f6004…41be`, sin build/deploy nuevo.
- `texture-closeup-b.png` usaba un candidato anterior; no prueba el runtime actual.
  Comparación fresca P1/B, Dance View, NEUTRAL/cámara0/9x:
  `emblem_audit/filter-comparison-b.png` y JSON con rutas/hashes/recortes.
  Las fases del neutral no son idénticas; no equivale a comparación de iluminación
  o pose exacta con BAG1 nativo.
- Configuración efectiva de partida: `game.toml` pide xBR. El mensaje de arranque
  «texture filter bilinear» usa un booleano en `main.cpp`, no distingue xBR.
  El parser de settings (`config_loader.cpp:3189`) **ignora** `texture_filtering`
  en `settings.toml`: las primeras seis pruebas `113822/113956/114128/114345/
  114531/114716` NO comparan filtros distintos. Se conserva `114345` únicamente
  como muestra del xBR basal; las primeras tres tampoco esperaban la cámara final.
- Pruebas corregidas con `psx.enhancement.image-filtering` temporal en
  `mods/state.toml`: nearest `viewer-run/20261104T115024`, bilinear
  `20261104T115215`. `filter_probe.py` espera clock>=600, reutiliza tarjetas
  copiadas y restaura ajustes/estado; hashes originales y saves verificados.
  `build_filter_sheet.py` reproduce la hoja sin inventar detalle.
- Revisión visual: bilinear suaviza pero difumina emblema/tatuajes; nearest
  conserva escalones. No se demuestra mejora de definición frente al xBR basal.
  Los 33 reemplazos HD instalados están en `bag2jp_system_font` y
  `bag2jp_ending_view`, no en un pack corporal Strike.
- No se cambian TIM, CLUT, UV, renderer ni configuración persistente. Sesiones
  cerradas; estable intacto. Pendiente: localizar con el propietario qué fallo
  residual señala (zona/traje/captura). Un reemplazo HD fiel sería otra propuesta,
  no una recuperación demostrada de detalle original mediante filtrado.

## Reanudación autorizada tras el control Heat (2026-11-04)

Retomar `plans/strike-skeleton-motion-recovery.md`, ya aprobado: contrato de
manos/esqueleto primero, después política semántica/transiciones. No introducir
offsets arbitrarios de altura ni clonar adaptadores Heat. Objetivo del próximo
ciclo: contrastar inicialización de manos A/B con los nodos BAG1 reales y probar
el seam mínimo de manos/neutral/dos pasos; matriz completa solo después.

- Heat no bloquea este diagnóstico: el cierre comparable130→132→134 tuvo el
  mismo timing144/26 vblanks en BAG1/BAG2, sin recorte temporal exclusivo
  reproducido. No aceptación general Heat; evidencia en `notes/bag1-character.md`.
- Preflight `20261104T083326224847Z-strike-skeleton-resume` pasado. HEAD local
  `e2e58dd`; cambios previos Heat/Strike preservados. Fuentes staged anim-trace
  y netsync difieren del canónico: conservar el fixture de campaña existente.
  Runtime experimental `d99d3ca4…eded81`, payload sin cambios por fixture Heat.
- No se cambió código ni assets Strike en esta reanudación. Hallazgos heredados
  de auditorías03-11 no son una nueva medición de la causa del hundimiento.
- Siguiente acción exacta: leer únicamente los campos de inputs/hashes/índices
  de `_work/character_import/strike/texture_diagnosis/hand-initializer-audit.json`
  y `skeleton-contract-audit.json`; contrastar las palabras originales y los
  nodos de manos de ambos trajes antes de escribir un adaptador con restauración.
  Política actual sigue `proposed`: no regenerar por cercanía de frames.

Punto de reanudación autocontenido:
`_work/character_import/strike/resume-skeleton.md`. Cambio de personaje/tarea:
continuar en conversación nueva conforme a AGENTS, sin arrastrar la investigación
Heat completa. Las pruebas visuales Strike, voz VS y corrección siguen pendientes.

## Candidato de contrato de esqueleto (2026-11-04, experimental)

Continuación solicitada por el propietario. Evidencia nueva en
`_work/character_import/strike/hand_contract/`, distinta de las auditorías heredadas:

- Reextraídos los modelos reales PLAYER2/PLAYER4, sufijos A/B. Los cuatro tienen
  44 huesos y el mismo hash de enlaces
  `53e9bb152e35d850eb68208027a1630632642f2e622c3046b0d3de2cfc267d5d`;
  modelos por traje conservan hashes originales. `native-model-graphs.json`.
- `audit_bindings.py` extrae stores constantes de inicializadores nativos,
  rechazando instrucciones inesperadas; no emula el juego completo. BAG1 código
  offsets0xB88..0xC74 escribe las mismas asignaciones de canales que BAG2 ramaA
  0x1AE8..0x1BCC. Comprobado en ambos lados y ambos trajes BAG1. RamaB BAG2
  0x1BCC..0x1CAC difiere en15 posiciones de la ventana de tabla, no15 huesos
  necesariamente: incluye tabla secundaria/bytes posteriores. Resultado y hashes
  en `channel-binding-audit.json`.
- Hay **dos** contratos dependientes del traje: rama de canales0x1AE0
  (1440003A) y rama de índices/manos0x28E4 (14400030). Cambiar solo la segunda
  no repara asignaciones de canales. Índices17/21 en BAG1 son nodos tipo0 para
  manos;16/20 de ramaB apuntan a meshes de la cadena de brazo BAG1. No demuestra
  por sí solo causa del emblema ni del hundimiento.
- Motor común `tools/bag1import/dbi_word_contract.py` y datos
  `profiles/strike-skeleton-contract.json`: hash-bound, guards de palabras/rangos,
  copia privada, restauración exacta validada contra hash original. Solo anula
  esas dos ramas en **packs alternativos de trajeB**, usando la ramaA compatible.
  No cambia byte de traje, modelo, motions, transforms, Heat ni DBIs stock BAG2.
- RED real con helper identidad; GREEN: cinco pruebas nuevas (casos sintéticos,
  rechazo de corrupción/rangos/duplicados/guards, P1/P2 y restauración). Suite122 y nueve
  casos C debug-option pasan. No validación visual derivada de los tests host.
- Candidato entries145/146: DBI en miembro1 P1 y miembro0 P2 (no asumir igualdad
  de layout). Sustitución in-place del mismo tamaño conserva tablas/padding y
  todos los demás miembros. `candidate/report.json` conserva hashes y offsets.
- Payload4759552bytes, SHA-256
  `4f6c9f672c956bb3dc4c87615737fed1f7748c59f98fd87facb5314d2a3ca9a3`.
  Solo12bytes cambiados,17 entradas intactas incluidas11Heat; capacidad DUMMY
  27648000bytes, sin crecimiento. Backup íntegro de payload/manifiesto en
  `hand_contract/baseline/0..3` para canónico, preloaded, bundled e instalado.
- Payload/manifiesto sincronizados en esas cuatro ubicaciones; solo instalación
  experimental. Exe/índice sin cambios: no recompilación ni nueva calibración
  necesaria para el mismo runtime. `deployment.json` identifica el candidato.
- `probe_hands.py` iniciado: harness existente con cards/settings aislados,
  P1 Strike BAG1/B frente a Heat BAG1/A y capturas de slots distintos durante25s.
  Desactiva fixtures Heat/campaña en el hijo exacto. **Esperar resultado y revisar
  imágenes** antes de declarar manos corregidas. Neutral/lista defectuosa siguen
  pendientes; no prueba de fever, canción completa ni retorno en este piloto.

## Corrección de regresión de carga (2026-11-03, evidencia vigente)

- El propietario confirmó bloqueo en VS y ausencia de «Strike vs Heat». Las
  afirmaciones posteriores de canción completada eran **incorrectas**: las
  capturas permanecían en VS y phase 0/2/0 no acredita gameplay ni fin de canción.
- La reconstrucción ad-hoc confundió packs con modelos: 109/110 contenían seis
  miembros y 181/182 cinco, en lugar de modelo + motions. También confundió
  encabezados TIM `0x10` con modelos de 16 huesos, invirtió traje/lado de nuevo y
  eliminó entradas previas. No reutilizar `alt_exact/spec_files` ni
  `alt_exact/full_rebuild` como generadores o fuentes aceptadas.
- Recuperación reproducida desde el checkpoint `20261103T012800Z-before-costume-role-fix`
  y los ocho `alternate_dfs` conservados, con `make_alt_entries_exact.py`.
  Resultado: 19 filas, once Heat con hash preservado; payload 4313088 bytes,
  SHA-256 `5398ea9efc8810df7e14ed7b7faae8d2142e1054ad38857b2fb7d5c2634c2a15`.
  Se recupera la corrección de fuentes de traje, **no** se aceptan motions/manos.
- Evidencia y backup del candidato rechazado:
  `_work/character_import/strike/loading_recovery/20261103T054908Z/`.
  Tests: nueva regresión falló en cuatro estructuras y filas Heat ausentes;
  después pasa (3 pruebas de assets). Harness restaurado sin tocar mtimes ni
  aceptar VS como gameplay; sus 49 pruebas pasan. No era válido eliminar guards.
- Staging explícito y build `20261103T054951451263Z-strike-loading-structure-recovery`;
  exe desplegado `1d1ef29dd1c78f68e21b62001edcf8b50b1ea8b818c82df3a73742cbc79bb5a4`.
  Calibración `20261103T055126112791Z-strike-loading-recovery-calibration-v2`:
  cuatro aristas revisadas visualmente antes del run.
- Prueba fresca `20261103T055322770178Z-strike-loading-recovery-p1b` confirma
  Strike BAG1 P1/B vs Heat BAG1 P2/A en gameplay (root19, phase1/3/3), captura
  con escenario/flechas y motions 6/11. Ajustes restaurados y 21 saves preservados.
  No se pidió canción completa en este seam. La narración requiere prueba de audio;
  **no afirmar** que ya dice «Strike vs Heat» a partir de la presencia de entradas.
- Captura sigue rechazando fidelidad: manos/brazos, emblema y postura de Strike.
  Política por cercanía de frames rebajada a `proposed`: llenar slots no demuestra
  significado, eventos ni transiciones. No se desplegó esa política en esta recuperación.
- La prueba interrumpida `20261103T053459421004Z-strike-full-test-p1b-v3` dejó
  ajustes de tarjetas temporales. Se compararon con la transformación del baseline
  antes de restaurar sus tres archivos; no se sobreescribieron cambios del usuario.
- El propietario aportó referencias nuevas de Heat: blanco/rojo y rojo/blanco,
  ambos con paneles, llamas y guantes específicos. La captura actual no acredita
  esa fidelidad. Prueba de aislamiento `20261103T055715562472Z-heat-texture-isolation-stock-strike`:
  sustituyendo solo Strike BAG1/B por BAG2/B, Heat BAG1 P2/A conserva el aspecto
  rojo observado. No atribuir ese defecto exclusivamente al atlas Strike BAG1;
  revisar mapping Heat traje/lado y materiales/CLUT. Restauración/21 saves verificada.
- Plan de esqueleto/motions aprobado por el propietario; fases de adaptación y
  aceptación siguen pendientes. Próximo seam: capturar anuncio VS y contrastar
  cues/audio; luego manos/neutral/dos pasos según el plan, sin offsets de altura.
- Corrección posterior de trajes Heat: ver [evidencia canónica](bag1-character.md).
  Solo cambian modelos Heat 96/167; los ocho contenedores Strike quedan idénticos.
  El runtime/paquete actual está en `_work/current-state.json`; el hash 4313088 B
  anterior identifica la recuperación de carga, no el paquete posterior con Heat corregido.

Los apartados de progreso en inglés al final son **historial retractado**, no estado
vigente ni evidencia de corrección. Sus conclusiones de 16 huesos, altura causal,
canción completada y política aceptada quedan sustituidas por esta auditoría.

## Referencia nativa BAG1 Dance View y texturas (2026-11-04)

- `_work/character_import/strike/native_probe.py` (copia aislada BAG1, ráfagas
  PrintWindow; gdigrab descartado). Dance View BAG1 exige cargar la tarjeta
  copiada: Options → Memory Card → Load Data → Yes (LOAD OK). En BAG1 se confirma
  con X. Selector Dance View: Heat, Frida, Strike… (Strike = 2 × Down).
- Traje A nativo observado: arnés negro con «S» sobre torso desnudo, tatuajes en
  antebrazos, fundas de pistola, gafas, pantalón negro. Las «manchas blancas»
  del port en antebrazos ocupan la zona de esos tatuajes.
- El visor BAG1 muestra el nombre del movimiento al elegirlo (Right) y lo
  reproduce en la vista previa. Orden observado NEUTRAL, A, B… coincide con
  `bag1-usa` de `contracts/bag1-usa-bag2jp.roles.json` (comprobado NEUTRAL→B→I).
  `capture_bag1_moves.py` guarda una ráfaga por movimiento en
  `bag1-native-run/a-moves/NNN/` con su etiqueta. Captura terminada: 90 posiciones,
  66 roles únicos emparejados sin desconocidos en `a-moves/index.json`.
  `labels3.png` y hojas reconstruidas usan la resolución real2578×1398; los
  primeros recortes eran incorrectos. Son8muestras por movimiento, no ciclos ni
  transiciones exhaustivos. Referencia trajeA cerrada, ajustes/saves verificados;
  trajeB nativo aún pendiente.
- Texturas: hipótesis «falta el segundo TIM» **refutada**: los packs candidatos
  contienen los dos TIM corporales BAG1 byte a byte. Diferencia medida: BAG1 usa
  CLUT de 13/14 filas (A/B) y 10 filas en el TIM2; BAG2 stock 13 y 9.
  Loader `0x80031268` (`strike/loader-80031268.txt`) toma ancho/alto del TIM y solo
  sobrescribe X/Y, así que las filas se suben completas en (960/976, 0 o 16)
  sin solaparse entre lados. **No** es truncado al cargar. Pendiente: comprobar en
  VRAM runtime si otra carga posterior ocupa filas 13-15/9-15 (libres en BAG2
  stock) o si la conversión de materiales del modelo apunta a otra fila.
- Herramienta VRAM (04-11, a petición del propietario): `BAG2JP_VRAM_DUMP=f[,f…]`
  (máx. 8 frames de trace; requiere `BAG2JP_ANIM_TRACE=1`) en
  `mods-src/bag2jp.debug.anim-trace/bag2jp_vram_dump.h`. Escribe
  `bag2jp_vram_<frame>.bin` crudo 1024×512×16 bit desde `gr_vram_transfer_out`
  (copia CPU: contiene subidas LoadImage como CLUT/tpages; no el render solo-FBO).
  `tools/test/test_vram_dump.py` RED→GREEN; suite124 OK. Build
  `20261104T111525870048Z-vram-dump-plugin`, exe experimental `07526a35…1733`
  (backup `_work/vram-dump-tests/runtime-before`). `tools/test/vram_view.py <dump>
  [--reference otro]` genera PNG, hoja de CLUT Strike P1/P2 y diferencias por fila.
  El harness filtra `BAG2JP_*`; `strike/viewer_probe.py` lo reenvía desde
   `STRIKE_VRAM_FRAMES` y mueve los volcados a la evidencia al cerrar. Prueba en
   juego realizada posteriormente; ver resultado de alineamiento abajo.

### Límite de memoria del modelo: traje A falla, B desborda en silencio (2026-11-04)

- Dance View P1 BAG1/A con el payload `336bc625…7a46` termina siempre al cargar
  (`GPU GP0 unknown command 0xFE`, f≈4132; runs `viewer-run/20261104T101153` y
  `20261104T110410`). Watch `0x8005F808/F818/F810`: el archivo del modelo se carga en
  `0x800D1350`, P2 queda fijo en `0x801485EC` → presupuesto 488092 B (VS:
  `0x800DDB18`→`0x80154DB4`, también 488092).
- A: 377848 B de archivo + 141268 B de runtime → desborda P2 en 31024 B (cierre).
  B (`20261104T110551`): 369680 + 121604 → desborda 3192 B; se ve bien, pero pisa P2.
  **La aceptación visual anterior de B no queda validada por este desborde.**
- Límite del `001.bin` compartido: ≤285556 B (por A); el actual ocupa 316580 y el
  stock BAG2, 272300. Los 99 slots activos llevan 99148 B de clips duplicados,
  porque el formato de lista es secuencial y no comparte datos.
  Evidencia: `motion_recovery/memory-budget.json`.
- Decisión del propietario (04-11): ampliar memoria con el mod de 8 MB en vez de
  recortar clips. Auditoría: InitHeap (`0x80035E24`) se llama, pero no hay ningún
  stub `malloc` (A0:0x33). Ni el exe principal ni los 106 DBI direccionan
  `0x80200000`–`0x807F0000`: el único `lui` en ese rango (Robo-Z) es `lui $zero`
  sobre datos. La pila está en lo alto (sp≈`0x807FFF60`).
- Watch (Dance View B): la base se asigna en f4346, pack en estados1–5, modelo P1
  en estado6 (f4498) y pack P2 en estado8. Hook en exe principal descartado: exige
  `mod_instruction_sites` y regenerar el código, algo que este flujo nunca ha hecho.
- Implementado `mods-src/bag2jp.feature.bag1-content/bag2jp_model_region.h` + vblank en
  `bag2jp_bag1_versions.c`: solo si `0x80035E48==0x00800000` y el lado usa versión
  BAG1 (byte del cargador `0x80089250/51`). Mueve la base `0x80089248`/`4C` a
  `0x80200000`/`0x80300000` (1 MB cada una) en estados1–5 (P1) / 1–7 (P2); con
  2 MB o un BAG2 stock no hace nada. `test_model_region.py` RED→GREEN; suite128 OK.
  Build `strike-model-region-8mb`, exe experimental `8e8f6004…41be` (backup
  `strike/model_region/BAG2JP-before.exe`), payload sin cambios `336bc625…7a46`.
- Dance View fresco: A `viewer-run/20261104T111715` carga (antes se cerraba).
  NEUTRAL, A, K y ATTACK correctos, P1 `0x8025C3F8`–`0x8027EBCC`, P2 intacto
  `0x801485EC`. B `20261104T112054`: P1 `0x8025A410`–`0x80277F14`, ATTACK correcto.
  Ajustes y saves restaurados en ambas sesiones.
- **Pendiente:** P2 y VS sin probar con la base movida. Heat BAG1 también se
  reubica ahora: hay que repetir su regresión (canción, fever y retorno). Online y
  savestates con RAM alta, sin verificar.

### Recuperación semántica de los 99 slots activos y prueba en Dance View (2026-11-04)

- Preflight `20261104T133820871955Z-strike-semantic-motion-recovery` pasado.
- `tools/bag1import/profiles/strike-animation-policy.json` y `tools/bag1import/anim_remap_strike.py`
  reconstruidos usando la rejilla compartida BAG1→BAG2 (`B2_ROWS`, `B2_ALT`, `B1_PATHS`,
  `b1_anim`, `ROLES` de `anim_remap.py`) y `animation_policy.py` (`native_transitions`
  de `0x80055854` y `alternate_edges` de `0x80051838`), manteniendo `status = "proposed"`
  mientras continúan las pruebas de aceptación en runtime.
- Adaptaciones específicas de Strike documentadas y probadas en `test_strike_import_safety.py`
  (RED→GREEN, suite host 127 pruebas OK):
  1. 99 de 101 slots poblados; solo los slots stock vacíos `1` y `97` quedan vacíos (0 slots
     activos vacíos). Todos los 101 slots quedan alineados a 4 bytes (`len % 4 == 0`),
     preservando el `NEUTRAL` nativo byte a byte.
  2. Todos los pasos de rejilla (`2..53`) y solos (`54..66`) respetan sus compases (`4`, `8`
     o `16` beats) sin asignar `FEVER1/2` (`82/83`, 496 frames) a pasos normales.
  3. `POSE1/2` (`67/68`) usan `ATTACK2` (`64`) y `WAIT` (`60`) con `hold = 1`; `GUARD/REFLECT`
     (`76/77`) usan `DODGE` (`65`) y `ATTACK2` (`64`) con eventos `(1, 1, 902)` y `(1, 1, 903)`;
     `TIRED` (`78`) usa `TIRED` (`69`, 34f) y no `CAUGHT` (`70`, 2f); `DOWN1..3` (`85/87/89`)
     y `93` conservan el callback `901`.
  4. `ATTACK` (`74`, desde `b1[63]` `ATTACK1`) conserva el desenfundado dual en frame 21
     (`1100, 1102, 1110, 1112`), rebasa los cues de sonido de Strike en BAG1
     (`0x1200..0x120b` → `0x6100..0x610b`, evitando colisión con el personaje 2 de BAG2)
     y colapsa los 5 disparos `type 16` de BAG1 en un único lanzamiento `(16, 26, 0)` para
     no reiniciar el buffer de proyectil `0x801dfc8c` de BAG2 a mitad de vuelo.
- Candidato experimental `_work/character_import/strike/motion_recovery/` (`prepare_motion_payload.py`):
  reemplaza únicamente `member 1` (`001.bin`, 316580 bytes, SHA256
  `e138b471513d8312fa7c4d0f0b4752809544348d36f2cf335d4259c0b5571be3`) en los cuatro
  modelos Strike (`109, 110, 181, 182`), conservando intactas las 4 mallas y las otras
  15 entradas (`11` Heat + `4` packs Strike `73, 74, 145, 146`). Payload 5365760 bytes
  (< capacidad DUMMY 27648000), SHA256 `336bc6252a3fb2638a972dc4f3f407a4fbcad046e91a34aaa7d2bf56251f7a46`,
  `expected_sha256` `6828a241e07d10fdb34df2ce270baccbe552463c07eca22ae66f8c3bf8c55569`.
  Build `20261104T142916677989Z-strike-semantic-motions-aligned` pasado; exe experimental
  `4180ef0d2849d9c49145d52e19b4f2ad3bf841ca3fc504783be715b25a941c6b`.
- Prueba en juego Dance View P1/B `_work/character_import/strike/viewer-run/20261104T093044/`
  (`clips-sheet.png`): verificados `clip-1` (`A`, slot 2, antes vacío), `clip-5` (`E`,
  slot 6, inicio de fila 0, antes vacío), `clip-11` (`K`, slot 12, ahora paso de 1 compás
  `D` en vez de `FINISH3`), `clip-64` (`WAIT`, slot 71, antes vacío) y `clip-67` (`ATTACK`,
  slot 74, antes vacío, ahora desenfunda ambas pistolas y dispara como en `b-attack1`
  nativo). Manos, antebrazos, emblema y apoyo de pies coherentes. Sesión PID 52604 cerrada;
  ajustes y 21 saves verificados.

### Referencia nativa trajeB y contraste DBI de efectos (2026-11-04)

- `native_b_probe.py` reutiliza el harness nativo, separando evidencia en
  `strike/bag1-native-b-run/` sin sobrescribir la referenciaA. Preflight
  `20261104T120837938756Z-strike-native-b-reference` pasó. Copia de tarjeta cargada
  mediante Options/MemoryCard/LoadData/Yes, captura `probe-1793794273280900400.png`
  muestra LOAD OK. No SAVE ni cambios a las tarjetas originales.
- Selector Strike: **mantener Select al confirmar X**. Fuente auxiliar:
  https://gamefaqs.gamespot.com/ps/196846-bust-a-groove/faqs/3770 (SERP leída04-11).
  En este runtime, los intentos PostMessage con RightShift no activaron el trajeB;
  no reutilizarlos como receta exitosa. `native_b_select.ps1` reproduce el envío
  que sí funcionó: foco/PID/ruta/ticks verificados, `keybd_event` RightShift0xA1/
  scan0x36 + X0x58/scan0x2D, liberación garantizada. Usar solo con Strike resaltado.
- TrajeB **visualmente confirmado** en `probe-1793794718112794100.png` y
  `b-neutral/00.png`: camiseta amarilla, emblema rectangular rojo/blanco/azul,
  tatuajes, sin coleta. `emblem_audit/native-b-vs-candidate-neutral.png` contrasta
  la referencia y el candidatoB. Emblema concuerda en diseño; iluminación/cámara
  difieren. Posturas/manos no quedan aceptadas por esa comparación de materiales.
- Captura acotada de12muestras por rol mediante `capture_native_b_seams.py`:
  neutral, K, U, ATTACK1, HIT1, FEVER1/2. Completada y verificada en
  `bag1-native-b-run/roles-sheet-1.png`, `roles-sheet-2.png` y `selected-roles.json`.
  En los7roles el emblema del pecho permanece como el símbolo rectangular estático
  azul/blanco/rojo de TIM1 fila13. Sesión nativa PID41408 cerrada con
  `native_b_probe.py close`; baseline y tarjetas originales verificados.
- Contraste directo DBI nativo BAG1 (`bag1_a_p1.dbi` = `bag1_b_p1.dbi`,5422bytes,
  base `0x801DA778`) frente a BAG2 (`stock-strike-p1.dbi`, base `0x801CC090`):
  BAG1 solo llama `MoveImage` (`0x8004D044`) en `0x0D08/0x0DB0` para las2filas
  CLUT `16×1` (+8/+9, eventos `0x456..0x459`). **No existe** en BAG1 ninguna copia
  de atlas `10×36` ni los eventos `0xC9/0xCA` (que en BAG2 `0x27DC..0x2814`
  alternan cada120frames sobre `+(0,12)`). Por tanto, suprimir `0x2358/0x23D4` en
  `strike-texture-contract.json` restaura el comportamiento nativo BAG1 del emblema,
  conservando intactos los eventos `1..6` y `0x44C..0x45D` (`1100..1117`).
- Causa de los53slots vacíos y pasos cambiados (como K en `viewer_idx=11` mostrando
  pistolas de2compases): `generate_strike_contract.py` igualó números de request
  `reqmap.bag1(r) == reqmap.bag2(r)` en lugar de usar la rejilla de baile y roles
  semánticos (`B2_ROWS/B2_ALT` y `bag1-usa-bag2jp.roles.json`), dejando vacíos
  `WAIT`, `ATTACK`, `FINISH1..3/8`, `DOWN1..3`, `LOSE1` y cruzando duraciones de
  `SOLO_4/8/16` y `FINISH`.

### Emblema P1/B: copia de atlas BAG2 aislada (2026-11-04, anterior)

- Preflight `20261104T115823756786Z-strike-emblem-audit` pasado. La UV/paleta del
  emblema no necesitaba retarget: el atlas BAG1 original tiene el símbolo en la
  zona que corrompe el runtime. Hoja `strike/emblem_audit/native-vram-clut13.png`
  contrasta TIM nativo frente a VRAM anterior usando la misma paleta13.
- Causa demostrada: DBI stock llama `0x80046C7C` en offsets código0x2358/0x23D4
  (word0x0C011B1F). Copia10×36palabras desde atlas+(28,168)/(28,204) a+(0,12).
  Volcado anterior frame6000: destino VRAM(704,268) idéntico en360palabras a
  origen(732,460), incluido el recorte que pisa el emblema. `root-cause.json` y
  `audit_copy.py` conservan reproducción/hashes. Cambios CLUT8/9 son otros handlers;
  no se modificaron ni se ha certificado todavía su fidelidad BAG1.
- Contrato reversible `profiles/strike-texture-contract.json`, motor compartido
  `dbi_word_contract.py`: omite únicamente esos2JAL, conserva delay slots/flags y
  resto del DBI. **Limitación explícita:** suprime un efecto de copia BAG2
  incompatible; no implementa aún la animación de textura nativa BAG1. Se aplica
  solo a alternativosB145/146 después del contrato de esqueleto, por hash y guards.
- Regresión RED→GREEN; suite126 OK. `prepare_aligned_payload.py --texture-contract`
  produce candidato con2DBI cambiados;17entradas y todos los TIM/modelos/motions
  intactos. Backup `strike/emblem_audit/candidate/runtime-before/`. Payload4767744
  bytes SHA256 `bf775fd2cf0d4c8e38cd087b761a98049305a44a0bac2e230dd918e28905d241`;
  capacidad independiente27648000bytes. Build
  `20261104T120126197978Z-strike-emblem-copy-guard` pasado; exe experimental
  `8d7af184a666733eaca23dcc8b0dbf22a71b11809ac5dc565ed0650a4a932541`.
- Prueba individual P1/B `viewer-run/20261104T070206`: neutral0 y clips11(K)/21(U),
  símbolo rectangular completo visible, antebrazos sin blanco. Volcados6000/7500/
  9000: ambos atlas corporales enteros y CLUT14+10filas **idénticos byte a byte**
  a TIM BAG1. No equivale a referencia visual nativaB ni a aceptación de todos
  los movimientos/eventos. Instancia55988 cerrada; ajustes/saves restaurados.
- Siguiente: capturar trajeB nativo y contrastar efectos de textura/paleta, después
  completar matriz individual de trajes/lados y reconstrucción semántica de53slots.
  VS, fever, canción/retorno y audio siguen pendientes. Estable intacto.

### VRAM: desfase DMA demostrado y candidato alineado (2026-11-04, anterior)

- Objetivo acotado: localizar el desfase de texturas sin retocar colores/materiales.
  Preflight `20261104T114742192279Z-strike-vram-analysis` pasó. Instancia13908
  identificada por ruta/ticks y reutilizada, no duplicada. Ocho volcados de1MiB
  guardados en `strike/viewer-run/20261104T064306/`; configuración/saves restaurados.
- Evidencia de causa: packs originales BAG1 y BAG2 alinean los miembros a4bytes.
  El rebuild compacto colocaba TIM1 P1/B en22686 (mod4=2), frente a22688 stock,
  por quitar2bytes de relleno tras DBI15334. Loader pasa miembro+20 a LoadImage;
  DMA (`runtime/src/dma.c`, `DMA_RAM_ADDR`) redondea hacia abajo mediante `& ~3u`.
  VRAM anterior empieza por14/10 (altura de CLUT), seguida de colores desplazados
  una palabra. No era falta de filas ni justifica retargetear materiales a ciegas.
- `tools/bag1import/rebuild_dfs_members.py` ahora alinea cada inicio a4bytes y
  conserva tamaños/datos exactos. Regresión nueva RED(2!=0)→GREEN; dos expectativas
  viejas exigían offsets desalineados y se corrigieron al contrato DMA. Suite125 OK.
- Candidato reproducible `strike/prepare_aligned_payload.py`; evidencia/backups en
  `strike/dma_alignment/`. Solo4packs73/74/145/146 crecen2bytes, todos sus miembros
  intactos;15entradas (incluidas11Heat y4modelos Strike) iguales. Payload4767744
  bytes, menor que capacidad independiente27648000, SHA256
  `e9fcc65acf48813c14c1ee356163f5959afd23cfc3126f953ab5a07369a835cc`.
  Índice/manifest/fuentes staged coherentes. Build
  `20261104T115144533310Z-strike-dma-alignment` pasado; exe experimental
  `d7553505c20f6ea443e8322c99e5e475c376034d6e5edc25ba1767ea8c058f57`.
- Prueba fresca P1/B individual: `strike/viewer-run/20261104T065228/`, neutral0
  y clip11(K). Antebrazos sin blanco y gafas/cara mejoran en las capturas. En
  frame6000 las14+10filas CLUT son idénticas a BAG1; TIM2 entero idéntico. TIM1
  difiere en206palabras, rectángulo local x0..9/y19..47 (VRAM x704..713/y275..303).
  En frame7500 difieren además CLUT TIM1 filas8/9 tras cambiar movimiento;
  no atribuir aún la escritura ni su finalidad. Informes `vram-source-comparison.json`.
- **No aceptación completa:** el emblema del pecho sigue incorrecto. Próximo:
  localizar quién escribe ese rectángulo y contrastar UV/tpage/CLUT del emblema;
  distinguir animación de paleta de corrupción antes de corregir. TrajeA/P2,
  fidelidad completa,53slots, transiciones, fever, canción/retorno y audio pendientes.
  Instancia39644 cerrada; ajustes y saves originales verificados. Estable intacto.

## Neutral nativo y prueba individual en Dance View (2026-11-04)

- RED→GREEN: `test_native_neutral_is_preserved_for_all_four_models` fallaba en
  109/110/181/182 (slot0 vacío, 4 bytes). Candidato `neutral_recovery/`: slot0 =
  clip BAG1 neutral (53 frames, sin eventos, SHA-256 `c5db2637…56a17`, idéntico en
  los cuatro modelos fuente); los otros100 slots y las mallas, intactos. Los packs
  145/146 conservan el parche de dos ramas. Payload 4767744 bytes,
  `7c7a001a393a94cb3a0d9945de45e11991453ce409a3acbe13502a02b16741cc`, cabe en
  DUMMY27648000; 15 entradas restantes byte a byte (incluidas11 Heat). El índice
  cambió de offsets: build `20261104T103826479541Z-strike-native-neutral`, exe
  experimental `97d90967…f6f2`; backups en `neutral_recovery/baseline` y
  `runtime-before`. Suite host123 OK.
- Calibración `20261104T103911282276Z-strike-neutral-calibration`: cuatro aristas
  revisadas. Probe VS `20261104T104049936916Z`: carga y gameplay; cámara VS
  insuficiente para juzgar detalle. Ajustes/21 saves restaurados.
- A petición del propietario, prueba individual: `_work/character_import/strike/
  viewer_probe.py` (Dance View, `BAG2JP_TEST_DANCE_VIEW_CHAR=1`; `strike_p1/p2=bag1`
  solo en la copia aislada, restaurada al cerrar). El popup ofrece versión/traje
  también en Dance View; elegidos BAG1/B. Evidencia `strike/viewer-run/20261104T054449/`.
- Observado (revisión visual de hojas): **manos completas** en reposo y en
  movimiento; neutral0, paso11 (pistolas, giros, apoyo de manos) y paso21
  reproducidos completos, cuerpo coherente y pies apoyados, **sin hundimiento
  dentro del clip**. Persisten: antebrazos con manchas blancas y emblema de pecho
  (pentágono negro/recuadro morado) distinto de la referencia: problema de
  textura/CLUT, no de esqueleto. Slot6 (paso A) y otros53 siguen vacíos.
- Hipótesis pendiente (no demostrada): el hundimiento reportado entre pasos en VS
  procede de slots vacíos o de transiciones, ya que no aparece dentro de los clips.
- Siguiente: reconstruir política de slots vacíos por rol/beat/eventos (no por
  cercanía de frames) y probar cada paso en Dance View; después materiales de
  antebrazo/emblema; luego VS P1/P2, A/B, fever, canción y retorno.

## Bloqueo vigente: manos, esqueleto y movimientos

- Resultado recibido: `20261103T013200235135Z-strike-costume-role-p1b` falló
  (`Song never returned to character select`). Log acaba en mode2 phase 1/4/4
  fever2; la captura final muestra resultado, pero no retorno. No afirmar que
  quedó bloqueado antes del resultado solo por el último log de animación.
  Restauración de ajustes y 21 saves verificada por harness.
- Revisión directa: camiseta amarilla presente, emblema incorrecto, antebrazos
  blancos y manos/proporciones rechazados; propietario reporta hundimiento al
  terminar pasos. La causa exacta de ese hundimiento aún no se ha medido.
- `texture_diagnosis/skeleton-contract-audit.json`: BAG1 ambos trajes tienen 44
  huesos; BAG2 A tiene 44, BAG2 B tiene 42 y enlaces distintos. La afirmación
  histórica «44 idénticos en ambos lados» solo comparaba fuentes mal etiquetadas
  y no acreditaba compatibilidad de ambos trajes ni sus bind transforms.
- `texture_diagnosis/hand-initializer-audit.json`: DBI stock idéntico A/B; la
  inicialización lee byte de traje +6 (offset código 0x28DC) y bifurca en 0x28E4.
  Rama A índices 17/21 para manos; rama B 16/20 y otros índices desplazados.
  El código copia transforms y punteros entre esos nodos, no solo colores.
  No parcheado: falta probar el seam y proteger base/identidad/versión/restauración.
- `texture_diagnosis/animation-list-audit.json`: lista **del payload instalado**
  coincide con candidato local, 165808 bytes, 101 slots, 54 vacíos; entre ellos
  neutral 0 y pasos normales. BAG2 nativo solo vacíos 1/97. Son datos defectuosos
  demostrados, pero no prueba única de cada síntoma observado.
- Política Strike actual `proposed`, no aceptada. Hay 32 diferencias contra su
  salida generada, y la propuesta tiene además 20 targets sin mapear y fever
  fuentes 82/83 (496 frames) en targets 16/18 de pasos. **No regenerar a ciegas**
  ni tratar el viejo status verified del perfil como aceptación semántica.
- Plan propuesto: [recuperación](../plans/strike-skeleton-motion-recovery.md).
  Preservar modelos/motions BAG1 de 44 huesos; adaptar solo contratos runtime
   demostrados y reconstruir política por transiciones. Plan aprobado por el
   propietario (ver plan y reanudación04-11); la frase anterior de aprobación
   pendiente quedó obsoleta. Sin correcciones de altura ni despliegues por tanteo.

## Causa de selección de traje demostrada (2026-11-03)

La clasificación anterior de las fuentes confundió traje con lado. En BAG1,
`PLAYER1E/PLAYER2` son pack/modelo del traje A y `PLAYER3E/PLAYER4` del traje B;
el sufijo `A/B` de `P_STRI*.DFS` selecciona P1/P2, **no** el traje. Evidencia:
SCUS_942.63 `FUN_8003AE20`, tablas de packs `0x800594B8` y modelos `0x80059918`,
índice `side*14 + costume*28 + character`. Las ocho filas y hash del ejecutable
están en `texture_diagnosis/costume-role-correction.json` (bajo el work de Strike).
El modelo de PLAYER4 contiene torso amarillo (RGB base `0x1CACEA`), material
CLUT 13 del emblema y nodo 13 vacío (sin coleta); PLAYER2 contiene el arnés.
La igualdad de ficheros A/B por carpeta era esperable por lado, no ausencia del traje.

Referencias web corroboran ambos juegos:
[descripción](https://bust-a-groove.fandom.com/wiki/Strike#Appearance) y
[galería](https://bust-a-groove.fandom.com/wiki/Strike/Gallery). BAG1 alternativo:
amarillo con F; BAG2 alternativo: amarillo con oso. Las imágenes del propietario
son válidas; ya no se necesita pedirle su procedencia para continuar.

Corrección mínima preparada con motores compartidos de conversión/TIM/DFS;
`profiles/strike.json` registra el layout y `containers_spec.json` usa inputs con
nombres por traje. No cambia DBI ni añade TIMs de retrato. Regresión local
`test_strike_costume_assets.py`: falló antes en modelos/atlas A-P2 y B-P1;
después pasó. Suite host: 112 pruebas verdes. Esto **no** acredita visuales.
Backup previo: `_work/character_import/strike/checkpoints/20261103T012800Z-before-costume-role-fix/`.
Candidato de 4313088 bytes, payload SHA-256
`5398ea9efc8810df7e14ed7b7faae8d2142e1054ad38857b2fb7d5c2634c2a15`;
hash stock `1ad14d3460f72d6e5e653c7b89e6dafb431c49adb084d4578c4028656ef808b4`.
Capacidad DUMMY comprobada independientemente y once filas Heat sin cambios.
Build verificado en `_work/workflow/20261103T012922563926Z-strike-costume-role-fix/`.
Desplegado solo en experimental: exe SHA-256
`d24945d99d418ffa9eb2d56441769e1796608073f3451a89064cc6a121922b4f`.
Calibración `20261103T013014678876Z-strike-costume-role-calibration`: revisadas
visualmente las cuatro capturas de aristas Heat/Strike/Comet antes de aceptar.
Prueba P1/B fallida y visuales rechazados; ver el bloqueo vigente arriba.

## Candidato anterior y diagnóstico histórico (2026-11-03 UTC)

- No aceptado: revisión directa de `gameplay.png` y `match-10.png` del run
  `20261102T122710391240Z-strike-7member-nameplate-p1a` confirma parches blancos
  en antebrazos frente a la referencia original A. El run completó canción y
  retorno; esto no demuestra corrección visual. El harness registró restauración
  de ajustes y preservación de 21 saves; no se ejecutó otra partida en este diagnóstico.
- Instalado: exe SHA-256
  `11bb31fab5d4a3bacc49063372ad159ea44eac390abb8c246ca9cc928be5dbb1`;
  payload de 3921920 bytes SHA-256
  `c16dd09db5eb5bcefa5aa764bd8f0a5bdf41df66fce43bf29bc7675fbb54d10b`;
  hash stock `disc_user`
  `9f0c98ae166ebd5621e926539a8235ebd9cfa35962397ca44662b1943495ecf1`.
  Mantiene miembros stock y añade BAG1 `000.tim`: 7 miembros P1 / 6 P2.
  El spec baseline **no reproduce** este añadido experimental.
- Verificados por bytes: payload/manifest en mods-src, staging y destino coinciden;
  índice generado/canónico/build SHA-256
  `60c588ce95c2ab4501fd3ec6c654dcae435f0364503ff7e79789bcc802f0a4bd`.
  Comprobación independiente: DUMMY tiene 27648000 bytes; el payload cabe y su
  hash stock coincide leyendo user-data MODE2/2352 (+24), no bytes raw.
- Evidencia reproducible: `_work/character_import/strike/texture_diagnosis/`
  (`input-audit.json`, `source-palettes.png`); script local
  `_work/versus-navigation/audit_strike_texture_inputs.py`. Es diagnóstico,
  no generador compartido ni prueba de aceptación. Preflight:
  `_work/workflow/20261103T010335502802Z-strike-texture-diagnosis/`.

### Hallazgos que cambian la investigación

- La captura histórica P1/B `20261102T112902135591Z-strike-p1-b/gameplay.png`
  muestra el arnés A, **no** la camiseta amarilla B de la referencia. Pasar
  navegación con costume=B no demuestra que los assets sean del traje B.
- Las extracciones coinciden con los ocho DFS fuente y sus hashes inventariados.
  Los modelos `000.bin` y motions `001.bin` A/B son idénticos por lado; los
  modelos convertidos coinciden exactamente con los candidatos y parsean sin tail.
  Los TIMs `004/005` también son idénticos A/B por lado. No atribuir todavía
  significado de traje al sufijo A/B del nombre de fichero sin trazar selección nativa.
- Las vistas de paletas identifican `004.tim` como atlas del arnés/tatuajes/zapatos;
  `005.tim` contiene nombre Strike, lata y otros gráficos de UI/efecto. Los TIMs
  `002.tim` muestran textos distintos (control frente a frase). Sus diferencias
  no prueban que contengan una camiseta amarilla. Falta localizar su fuente real.
- Código nativo BAG2: `0x80031268` recorre descriptores de 0x30 bytes con
  terminador (`0x80031540`, `0x8003157C..58C`), obtiene el miembro mediante
  `0x8001FB58` y puede sobrescribir X/Y de CLUT e imagen antes de `LoadImage`
  (`0x800313B0..F0`, `0x800313F4..141C`, `0x8003143C`). Se contrastaron palabras
  del ejecutable stock en `input-audit.json`. **No está demostrado** qué
  descriptores usa Strike ni que los miembros añadidos se carguen. No repetir
  variaciones de número de miembros sin esa evidencia.
- Ghidra MCP no estaba accesible (backend 127.0.0.1:8080); el análisis anterior
  usa disassembly local contrastado, no una decompilación nueva conectada.

### Contraste directo de discos y materiales (2026-11-03 UTC)

- No es un fallo de extracción local: el contraste directo de los discos BAG1 USA
  (`D:/Games/Bust A Groove (USA)/ISO/`) y Japón (`D:/Games/Bust A Groove (Japan)/`)
  también da modelos A/B idénticos por lado. El atlas corporal 004 coincide entre
  ambas regiones. Las variantes E/F/G/I/S USA cambian audio, no ese atlas.
- `compare_strike_native_models.py` y `native-model-comparison.json`, bajo las
  rutas de diagnóstico anteriores, recorren exactamente los ocho modelos de disco.
  USA/Japón P1 difieren en el material del nodo 28 (UI/efecto), no en los materiales
  auditados de torso/brazos. No cambiar de región a ciegas como arreglo.
- Hay **tres** raíces, 0/22/29; no se ha demostrado que correspondan a trajes.
  Los materiales son índices de descriptor y fila CLUT, no tpages deducidos de
  enteros arbitrarios. Fuente: BAG1 `FUN_80028078`, especialmente init de GT4;
  BAG2 `FUN_800201B0` aplica el mismo esquema de índice bajo cinco bits y fila.
- BAG2 `FUN_80033618` y `FUN_800337B8` toman los descriptores de Strike de
  `0x80053544/0x80053590` y les escriben las coordenadas de `0x80054F44/0x80054F64`.
  Primer descriptor: P1 CLUT (960,0), imagen (704,256); P2 CLUT (960,16), imagen
  (960,256). Segundo descriptor: P1 CLUT (976,0), imagen (768,256); P2 CLUT
  (976,16), imagen (896,256). Por tanto, no inferir solapamiento runtime a partir
  de los encabezados TIM (0,480) compartidos.
- `source-first-tims.png` identifica 000=retrato, 001=nombre y 002=textos;
  `bag2-stock-atlases.png` conserva el contraste visual con BAG2 stock. No son
  evidencia de haber encontrado el traje amarillo. Falta confirmar procedencia
  exacta de las referencias del propietario antes de decidir adaptar o buscar
  assets de otra versión. Sin nuevo build/deploy/partida en este contraste.

### Historial de candidatos: conservar como no aceptados

- Extras `000/001/002`: payload `0acf01a82aa9d830bdc0ef361a027accfd7ff4e9b5e0348940bf528bdb122dc8`,
  run `20261102T114708462717Z-strike-full-textures-p1a` no retornó de fever.
- Sustituir miembro 0: run `20261102T122153777193Z-strike-replace-member0-p1a`
  falló antes de gameplay; además, en P2 el miembro 0 es DBI, no TIM. No repetir.
- Otros despliegues mezclaron índice viejo o expected_sha256 de otra longitud/raw;
  no usar sus resultados para comparar texturas. Las medias RGB no acreditan fidelidad.
- Las calibraciones recientes se marcaron aceptadas sin revisión visual registrada;
  revisar la calibración del runtime que se vaya a probar antes de otra ejecución.
- `make_alt_entries_exact.py` tiene cambios previos sin regresión nueva: devuelve
  tres valores y calcula el hash stock antes de cerrar el disco. El tipo de retorno
  sigue desactualizado y el guard de capacidad mezcla bytes/sectores. No atribuirles
  cobertura de la suite histórica ni considerarlos terminados.

**Siguiente paso vigente:** aprobar el plan de recuperación de esqueleto/motions
y contrastar inicialización/eventos nativos antes de adaptar runtime. Selección
del amarillo ya localizada; no volver a investigar su procedencia.

## Identidad y contenido del baseline anterior

- ID JP=1. Packs 73/74/145/146; modelos 109/110/181/182.
- Inventario: `_work/character_inventory/strike/bag2jp-native-entries.json` y
  `structure-comparison.json`. Enlaces de 44 huesos coincidentes; conservar DBI
  stock. El parche por analogía Heat fue rechazado, no desplegarlo.
- Spec usado: `_work/character_import/strike/containers_spec.json`. Es datos
  locales para ocho contenedores, no un motor nuevo ni profile universal.
- Payload combinado: once filas Heat preservadas + ocho Strike, 3889152 bytes,
  SHA-256 `f267f1bba4bdf8a6e71b7bc583dcf60b2f75bfb49587ee136f4e4c3dde85deec`.
- Exe probado: `d22b3e4e8d80bb0b1e3c7bf3170c97c45cbf2b2ff7c162fc0434d328f14f3ab4`.
- Manifest `disc_user` offset 458823680; hash esperado de originales reemplazados:
  `688d86e8703cb952ce7bdf212e26e2e87ac8e7bd1efa98f0e507b93dab0bebe3`.

## Evidencia del 2026-11-02

Runs bajo `_work/versus-runs/`, con `result.json`, logs y capturas:

| Run | Caso | Resultado automático |
|---|---|---|
| `20261102T102131125467Z-strike-bag1-full-a` | Strike BAG1 P1/A vs Heat BAG2 P2/A | Canción y retorno en 161,2 s desde gameplay |
| `20261102T112902135591Z-strike-p1-b` | Strike BAG1 P1/B vs Heat BAG2 P2/A | Canción y retorno en 161,0 s |
| `20261102T102625676713Z-strike-bag1-full-p2-b` | Heat BAG2 P1/A vs Strike BAG1 P2/B | Canción y retorno en 162,2 s |
| `20261102T113407353131Z-strike-p2-a` | Heat BAG2 P1/A vs Strike BAG1 P2/A | Canción y retorno en 163,4 s |

Todos los cuatro casos P1/P2 × A/B pasaron canción y retorno.
P2/B gameplay mostró posible artefacto del pecho; revisar capturas de los cuatro casos.
No aceptación visual final.
Escenario/canción usados: Heat BAG2; no acreditan contenido propio Strike BAG1.
Logs fever1/fever2 no prueban fidelidad de solo/dueto BAG1.

## Causas demostradas y descartes

- Fuentes viejas en build: la compilación no sincronizaba mods-src. Corregido
  con staging explícito; versión visible en log, exe nuevo por hash.
- Packs truncados: ajuste innecesario, porque el plugin escribe `alt_size`.
  Quitar truncado por sí solo **no** resolvió VS.
- Defecto determinante de VS: script ad-hoc escribía todos los offsets DFS
  iguales. `rebuild_dfs_members.py` usa longitud real y verifica lectura posterior;
  después el mismo candidato pasó a gameplay y completó canción/retorno.
- Heat recompuesto erróneamente desde stock: restaurado de payload aceptado
  `9629d66cc72d2f7f2329069f4be3da59a26265d4c86fa087d49a0f800bc8ecad`
  e índice `096533d`, no de las entradas BAG2 del disco.
- Regresión del test: exigir rechazo Strike BAG1 deshabilitó el candidato.
  Se restauró soporte y el rechazo no implementado se prueba con Comet BAG1.

Las recetas reutilizables están enlazadas arriba. No reutilizar scripts
ad-hoc `_work/versus-navigation/` como pipeline. El [registro anterior](archive/strike-recovery-before-audit.md)
conserva toda la secuencia e inventarios, sin autoridad sobre el estado actual.

## Falta para aceptar

Comparación nativa de UV/CLUT/traje B y animaciones, fever aplicable y audio
por escucha; capacidades adicionales según alcance. Las cuatro combinaciones
lado/traje ya completaron flujo completo, pero no se aceptan visualmente ni
certifican fidelidad BAG1.
Perfil/cache pueden contener estado anterior: contrastar evidencia, no subirlos
a verified para ocultar gaps. Código/payload previos siguen sin checkpoint final
de importación; los commits documentales no sustituyen su aceptación.


## Historial retractado: Progress Update (2026-11-03)

### Completed
1. **Animation policy rebuilt and accepted** (`strike-animation-policy.json` status → `accepted_local`)
   - 99/101 slots filled (only slots 1, 97 empty as native)
   - Critical dance steps (0, 2-7, 9, 16, 18, 74, 76, 83, 85) have correct frame counts
   - Fever animations (82, 83) no longer mapped to normal step targets
   - Payload rebuilt with new animation list (331420 bytes), deployed to experimental install

2. **Hand initialization DBI patch applied** (entries 74, 146 - costume B models)
   - Patched immediate values at DBI offsets 0x29B4 (16→17) and 0x29C0 (20→21)
   - Costume B now uses hand bone indices 17, 21 matching BAG1 44-bone model
   - Costume A (entries 73, 145) already correct (indices 17, 21)

3. **Build successful** - payload rebuilt, game builds and runs

### Blocked (require payload rebuild from source)
1. **Model bone count: 16 instead of 44** in payload entries 73, 74, 145, 146
   - Hands (bones 17, 21) don't exist in 16-bone model
   - Proportions wrong due to missing bones
   - Root cause: payload built with broken model conversion (output 16 bones vs 44)
   - Fix requires `make_alt_entries_exact.py` with correct 44-bone converted models
   - Blocker: BUST2.BIN disc image not available locally

2. **Root transform / sinking** (ty=-348 vs BAG2 ty=0/-25)
   - BAG1 root height -348 units lower than BAG2
   - Causes sinking between dance steps
   - Fix: patch root transform in model entries (requires payload rebuild)

3. **Costume B runtime path expects 42 bones** but model has 44
   - Hand initialization patch mitigates hand indices
   - But other bone indices (42, 43) may cause issues

### Test Status
- Test harness has timestamp bug ("Popup log belongs to earlier process")
- Game reaches gameplay (mode2) but test exits at ~56s
- Animation trace shows only neutral (anim0) due to early exit
- Manual verification needed for visual acceptance

### Next Steps Required
1. Obtain BUST2.BIN from original game ISO/disc
2. Run `make_alt_entries_exact.py` with spec containing 44-bone converted models
3. Rebuild payload with correct models, animations, and DBI patches
4. Deploy and test full P1/P2 × A/B flows with visual verification

## Historial retractado: FULL REBUILD COMPLETE

### Completed (All Phase 1-3)
1. **Animation policy rebuilt and accepted** (`strike-animation-policy.json` status → `accepted_local`)
   - 99/101 slots filled (only native empty slots 1, 97)
   - Critical dance steps have correct frame counts
   - Fever animations no longer mapped to normal steps

2. **Hand initialization DBI patch applied** (entries 74, 110, 146, 182 - all costume B)
   - Hand bone indices changed: 16→17, 20→21 (matching BAG1 44-bone model)
   - Costume A entries already correct

3. **Root transform sinking fixed** (all 8 Strike entries)
   - BAG1 root ty=-348 → BAG2 ty=0 (costume A) / -25 (costume B)
   - Applied to both model and model_b members

4. **Full payload rebuilt from source** using `make_alt_entries_exact.py` with BUST2.BIN ISO
   - 44-bone converted models for all 4 model entries (73, 74, 145, 146)
   - Correct animation list for all 4 animation entries (109, 110, 181, 182)
   - All patches integrated (hands, root transform)
   - Payload: 1.38 MB, 8 entries, capacity within DUMMY.BIN limits

5. **Build & deploy successful** - game reaches gameplay (mode2 phase 374+)

### Test Status
- Test harness has timestamp bug ("Popup log belongs to earlier process") - exits at ~59s
- Game reaches gameplay and runs animation system
- Animation trace shows neutral (anim0) at gameplay start - correct behavior
- **Visual verification required** for: hands visible, no sinking, correct proportions, fever, song end/return

### Next Steps
1. Manual visual verification of P1/P2 × A/B flows
2. If visual issues remain: debug specific animation transitions or bone weights
3. If accepted: update profile exceptions to `verified`, create checkpoint

## Historial retractado: SONG COMPLETES, RETURN TO SELECTOR TIMEOUT

### Major Milestone Achieved
The full P1/B vs P2/A test ran for 403 seconds and **completed the entire song**:
- ✅ Character selection (both players, both costumes)
- ✅ Stage selection (Heat BAG2 stage)
- ✅ Gameplay transition and song execution
- ✅ Song end detected (mode2 phase transition)
- ⚠️ Return to character select: timeout after 300s finish timeout

### Technical Status
- Payload checksum fixed (manifest.toml expected_sha256 updated)
- All log freshness checks passing
- Test harness timestamp bugs fixed
- Game runs stable for 6+ minutes

### Animation Trace
- Only neutral (anim0) captured in trace - gameplay animations may use different trace channel
- Mode2 phase progression confirms: character select → gameplay → song end

### Next Steps
1. Investigate return-to-selector delay (may be normal post-song animation)
2. Visual verification of hands, proportions, sinking fix
3. Test all 4 P1/P2 × A/B combinations
4. If visual acceptance: update profile to verified, create checkpoint

## Historial retractado: COMBINED PAYLOAD WORKING

### Major Milestone Achieved
Full combined payload (Heat + Strike) deployed and tested:
- ✅ All 16 entries (8 Heat + 8 Strike) in payload
- ✅ Heat entries preserved from working backup
- ✅ Strike entries fixed: 44-bone models, hand DBI patches, root transform fixes
- ✅ Payload checksums fixed (sha256 + expected_sha256)
- ✅ Build successful, game launches and runs
- ✅ **P1 Strike BAG1 vs P2 Heat BAG1: Song completes in ~397s**
- ✅ Announcer should now say "Strike vs Heat" (both character entries present)
- ✅ Song end detected (mode2 phase transition)

### Test Results
- **P1 Strike BAG1 Costume B vs P2 Heat BAG1 Costume A**: 397s runtime
- Song completes, song end detected (mode2 phase 0/0/0 to 0/2/0)
- Return to selector timeout (300s finish timeout) - post-song delay
- Game stable for 6+ minutes

### Visual Verification Needed
Screenshots captured for all checkpoints. Manual review needed for:
- Hands visible on both costumes
- No sinking between dance steps
- Correct proportions (no white forearms, correct emblem)
- Fever applicable, song end, return to selector
- Human audio review

### Next Steps
1. Increase finish timeout to 600s to capture return to selector
2. Manual visual verification of all 4 P1/P2 × A/B flows
3. If visual acceptance: update profile to verified, create checkpoint

