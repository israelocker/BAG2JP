---
id: bag1-stage-song-heat
title: "Escenarios y canciones BAG1: Heat y Strike"
tags: ["bag1", "heat", "stage", "song"]
summary: "Receta compartida Heat/Strike, fuentes JP, audio y evidencia delimitada; campaña y escucha pendientes."
related: ["notes/bag1-character.md", "notes/character-pipeline.md", "notes/character-import-testing.md"]
created: "2026-10-30"
updated: "2026-11-06"
edited: "2026-11-06"
doc_kind: reference
---

# Escenario y canción se verifican por separado del personaje

## Ruta reutilizable y estado de evidencia (auditoría 2026-11-06)

1. Identificar disco/región y hashes. `iso_extract.py <disc.bin> list` entrega
   extents ISO en **bytes**; extraer a un directorio nuevo con `extract <out> <glob>`.
   Su lector entrega 2048 bytes útiles/sector: no sirve para conservar XA/STR raw
   completos. No ejecutar scripts de `_work` que escriban discos como probes.
2. Inventariar DFS y callbacks nativos/stock; contrastar palabras originales,
   llamadas, globales, tamaños y chart. JP y USA no son intercambiables.
   Los perfiles `tools/bag1import/profiles/stages/{heat,strike}.json` son contratos
   concretos, no heurísticas de relocación. El porter debe rechazar llamadas desconocidas.
3. Crear candidato en ruta nueva, desde la raíz del proyecto:

   ```powershell
   py -3.13 tools/bag1import/build_stage_package.py --root D:/Dev/Recomp/BAG2JP --profile strike --output <new-output>/strike_209.dfs
   ```

   `build_from_project` lee los inputs de `profile.package`; escribe DFS y JSON,
   no despliega. Strike: tres TIM nativos + dos comunes retargeteados + cuatro
   rellenos = nueve slots; modelo 44 huesos escala 3/2, intro JP + baile stock,
   lista vacía experimental. Banco0 SFX nativo se combina con bancos1..3 stock.
   El reporte conserva `experimental=true`; su texto fijo «stock sound bank» es
   obsoleto cuando `native_sfx_bank0=true`: comprobar bytes, no ese texto.
4. Revisar referencias externas/CLUT/UV, cámara, efectos, luces y lista vacía.
   **Requisito obligatorio:** identificar e importar las interacciones y eventos
   del escenario que avanzan con el puntaje (`level` vs `prev_level`); no basta
   con la geometría estática ni la pista de audio.
   `test_stage_port.py` comprueba estructura, banco0 y preservación del DBI Heat;
   la prueba aritmética de sprites no demuestra fidelidad GTE/cámara en juego.
5. Integrar candidato como fila `kind=3` conservando filas aceptadas:
   [DFS/payload/staging](character-alternate-entries.md). Mantener conjunto coherente
   payload/índice/manifest/exe y backups; no copiar el build tree entero.
6. Música: extraer el canal XA real, registrar hash/frecuencia/duración y tabla
   nativa; convertir a FLAC estéreo 44100 Hz para el decoder. La receta Strike
   exacta está abajo. No aplicar el corte/fade Heat de `song_ending.py` a Strike:
   ese adaptador procesa game/CD, requiere NumPy/ffmpeg y sobreescribe outputs.
7. Probar selección independiente del personaje, carga, canción completa,
   efectos/SFX y retorno, regresiones Heat/BAG2 y restauración de tarjetas/settings.
   Escucha humana separada. Endings/campaña: [su receta](endings-view.md).

**Qué está respaldado:** evidencia histórica conservada de carrusel15filas,
Strike209, canción completa+retorno, SFX y regresiones HeatB1/StrikeB2 listada
abajo. El propietario confirmó la rejilla/fondo negro. **No** nueva ejecución en
esta auditoría, aceptación auditiva subjetiva ni campaña completa demostrada.
Los bloques siguientes conservan revisiones fechadas; no son estado simultáneo.

Fuentes existentes:
- `tools/bag1import/port_bag1_stage.py`: motor con perfiles Heat/Strike y adaptador
  Heat conservado; no relocador validado con todos los escenarios.
- `mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_stage.c`: shim/XA y duración
  configurada por perfiles Heat/Strike. Sus constantes no se copian para otro escenario.
- `tools/bag1import/build_heat_stage_test.sh`, `song_ending.py`: adaptadores,
  no comandos de build por defecto del workflow Windows actual.

El [registro original](archive/bag1-stage-song-before-audit.md) conserva tablas,
offsets, causas y pruebas fechadas de chart, escala, callbacks y audio. Sirve
para investigar; confirmar región/palabras originales y source hashes antes de un parche.
No se repitieron estos tests en esta auditoría. La afirmación histórica «2P autoplay
verificado» no acredita por sí sola voces, canción nueva, ending ni online.

Requisitos de reutilización: inventario de callbacks/datos/chart, referencias
sin resolver explícitas, comprobación de duración y audio, efectos/cámara y
final+retorno con mods activos. No deducir canción de memoria ni del nombre
de la carpeta extraída; comparar evidencia del audio y tablas.

Las partidas Strike anteriores al port de escenario usaban **Heat BAG2** como
escenario/canción. No prueban Strike BAG1. Los candidatos visuales iniciales
conservaban audio/SFX BAG2; fueron sustituidos por las revisiones descritas abajo.

## Requisito obligatorio: eventos e interacciones del escenario según el puntaje (2026-11-06)

- **Regla general de importación de escenarios BAG1 a BAG2:**
  Al importar cualquier escenario de BAG1 a BAG2 no basta con portar la geometría 3D, texturas, cámaras y pista de audio. Los escenarios de BAG1 son interactivos y dinámicos: evolucionan con eventos visuales y ambientales que se disparan según el avance de la puntuación de los jugadores (por ejemplo, en el escenario de Heat, la rotura progresiva de paneles y ventanas desde el interior en llamas hacia la vista nocturna de la ciudad al alcanzar 15.000 y 45.000 puntos; en Strike, el avance progresivo de luces, elementos mecánicos y dinamismo del entorno conforme sube el puntaje).
- **Lógica nativa en BAG1:**
  En BAG1, la función de actualización del escenario (`update`, e.g. `0x801DDC60` en Strike JP, `FUN_801d...` en Heat) compara en cada ciclo el nivel de puntuación actual (`level`, en Strike JP `0x8006F638`, en Heat `0x80068714`) frente al nivel previo (`prev_level`, en Strike JP `0x8006EACC`, en Heat `0x800979D0`). Si `level > prev_level`, se activan los eventos de transformación del entorno correspondientes al nuevo nivel.
- **Adaptación requerida en BAG2JP:**
  El motor de BAG2 calcula el nivel de baile (`0x8005141C`) con sus propias tablas y umbrales. Para que el escenario importado reaccione, es imprescindible:
  1. Que `b1s_vblank` (`bag2jp_bag1_stage.c`) adapte la puntuación de BAG2 al formato de nivel esperado por el escenario BAG1 y lo escriba en el shim de comunicación (`B1S_SHIM + 8`).
  2. Que el guard del escenario en `b1s_vblank` no descarte el escenario (p. ej. `psx_mod_read_byte(stage) > 1` descarta otros escenarios que no sean 0 o 1).
  3. Que el DBI o trampolín del escenario invoque el `update` nativo propagando `level` (`SHIM + 8`) a `prev_level` (`SHIM + 9`).
- **Incidencia observada en Strike BAG1 (revisión 2026-11-06):**
  Durante la prueba en vivo de duelo ordenado (`_work/versus-runs/20261106T043419201749Z-ordered-heat-heat-strike-strike`), el propietario observó y reportó: *«el escenario de strike no esta avanzando, recuerda que mientras mas puntaje haces el escenario va teniendo eventos, lo mismo paso con la importación del escenario de heat, se habia importado bien, pero faltaba la interacción del escenario cuando iba subiendo su puntaje, ponlo en una nota que cuando importas los escenarios de bag1 a bag2 tambien tienes que importar esas interacciones del escenario con el puntaje»*.
  El escenario de Strike cargó su geometría y música, pero está estático frente a la puntuación. Esta interacción con el puntaje queda registrada como requisito mandatorio pendiente de implementación para Strike y para todo futuro escenario BAG1.

- **Incidencia resuelta: Pasillos laterales y celdas ausentes (2026-11-06):**
  - Causa: En el modelo original de BAG1 (`ST_STRI.DFS` archivo 5, 44 huesos), los huesos 0 a 39 utilizaban 10 mallas maestras (tipo 1) en Z=+29607 y 30 referencias relativas (tipo 2) a Z=-29589, -9857 y +9875 para instanciar los pasillos a lo largo de Z. BAG2 no soporta huesos tipo 2 en modelos de escenario, por lo que las 3 secciones laterales en Z no se renderizaban y las maestras quedaban desplazadas hacia adelante fuera de cámara.
  - Solución: Se implementó `flatten_type2=True` en `tools/bag1import/model_bag1_to_bag2.py` y se configuró en `tools/bag1import/profiles/stages/strike.json`. Esto expande cada nodo tipo 2 en una malla independiente tipo 1 con su propia copia de geometría.
  - Validación: Reempaquetado del DFS de Strike (334.816 bytes, 44 nodos tipo 1), actualización de payload `bag1_alt.bin`, compilación y prueba en vivo con captura de pantalla (`strike-stage-flattened-run-v6`). Los pasillos, las rejas de las celdas de la prisión, el suelo continuo y las luces del techo ahora se renderizan perfectamente en ambos lados flanqueando a los bailarines.

## Strike: audio profile candidate (2026-11-06)

### Prueba pendiente: estructuras laterales durante solos

- El propietario confirmó que el escenario funciona en la prueba en vivo con
  autoplay, pero observó desaparición/reaparición de estructuras laterales durante
  cámaras de solo; indica que también ocurría en BAG1. No demuestra descarga de texturas.
- Autorizó una prueba A/B temporal en experimental: identificar la estructura y
  la condición de descarte, evitar solo ese descarte conservando límites seguros,
  comparar el mismo solo con/sin cambio, artefactos y rendimiento. No mover geometría
   ni aumentar memoria para esta prueba. El candidato siguiente es experimental.
- MCP recuperado con el cliente local instalado, sin reiniciar Ghidra ni cambiar
  configuración: `20261106-ghidra-008` en `notes/tool-evidence/ghidra-psx-psyq.md`.
  `get_program_info` confirmó ejecutable JP y hash; juego preservado.
- La lectura nueva de `0x80022660` incluye `case 2`: el éxito del flattening no
  demuestra que BAG2 carezca globalmente de soporte tipo2, como se afirmó antes.
- Siguiente: trazar dibujado por fotograma, reproducir el solo y contrastar culling
  frente a clipping/orden/VRAM antes de editar. A/B todavía no ejecutada.
- Ensayo `20261106-ghidra-009`: excluidos render de personajes (`0x8002c404`),
  inicialización (`0x8003318c`), cámara, texto y entradas como condiciones del
  descarte buscado. Extracción Capstone complementaria en
   [su registro](tool-evidence/capstone.md); no identifica aún el render del escenario.

- Avance posterior `20261106-ghidra-010` / `20261106-capstone-002`: lectura MCP
  de `0x80030458` y contraste exacto de 2048 bytes con el ejecutable JP identifican
  el bucle real de visibilidad por grupo. El descarte por posición proyectada sigue
  a comprobaciones independientes de profundidad y flags GTE.
- Fixture reversible `bag2jp_stage_visibility_test.h`: sustituye únicamente
  `0x80030590: 0243001b` por `0800c175` (salto a aceptación `0x800305d4`),
  con seis palabras de guarda y restauración solo de la modificación propia.
  No evita los rechazos de profundidad `0x80030578` ni GTE `0x80030588`.
  Desactivado salvo variable `BAG2JP_TEST_STAGE_VISIBILITY=1`; archivo temporal
  `bag2jp_stage_visibility.mode` alterna 0/1 únicamente con Strike BAG1 cargado.
- Prueba host rojo→verde y regresión audio: dos tests pasan mediante
  `py -3.13 -m unittest tools.test.test_stage_visibility_fixture tools.test.test_bag1_stage_audio`.
  Build de dos jobs: `_work/workflow/20261106T091234997208Z-strike-visibility-fixture`;
  exe experimental SHA256 `55673109f093a71f37b94c55c37fcb98f10a606e25cd9d67655ca6bca0516254`.
  Payload y estable sin cambios; exe previo respaldado en
  `_work/stage_import/strike/visibility-build-backup/BAG2JP.exe`.
- Calibración visual del nuevo runtime revisada en
  `_work/versus-runs/20261106T091409672509Z-strike-visibility-calibration`;
  cinco imágenes vinculadas al catálogo. Restauración verificada de settings,
  controles, estado de mods y 21 saves. A/B mediante `_work/strike_visibility_ab.py`
  completada en `_work/versus-runs/20261106T091810099713Z-strike-visibility-ab`.
- Resultado A/B: el log confirma aplicación (`result=1`) y restauración (`result=2`),
  pero **comparación visual inválida**: Start no congeló Fever. Las fases avanzaron
  de1/5/6 a1/7/0 y1/7/3; `ab-compact.png` muestra cámaras/posturas diferentes.
  No acredita mejora, regresión ni causalidad del descarte. Duración total257,51s;
  ajustes/controles/mods y21 saves restaurados con hashes verificados; archivo
  temporal eliminado por el driver. Fixture permanece desactivado por defecto.
- Próximo paso: obtener captura comparable de la misma cámara/fotograma mediante
  un control de pausa o repetición verificado antes de repetir A/B. No repetir el
  intento con Start en Fever ni tratar éxito del harness como aceptación visual.
- Validación humana posterior: `_work/versus-runs/20261106T092907543033Z-strike-live-autoplay`,
  Player vs Player/autoplay ambos, Strike BAG1, descarte original activo (sin bypass).
  El propietario confirma que persisten los huecos visuales y aporta seis imágenes;
  no hay aceptación visual. Las imágenes no distinguen por sí solas descarte,
  clipping, orden de polígonos o texturas. Esta partida no evalúa el bypass.
  Cierre del harness460,102s; restauración verificada de controles/settings/mods y21 saves.

### Incidencia separada: pose durante la presentación inicial

- Auditoría posterior del pecho (solo lectura):
  `_work/stage_import/strike/current-chest-audit.json`, script
  `_work/audit_current_strike_chest.py`. Payload instalado/canónico idénticos,
  SHA256 `58f25584e6850dd37956802c0e5b2299d7aefcceac1a28750d4cc3aab08689e9`.
  Las dos llamadas de copia `DBI+12+0x2358/0x23d4` siguen anuladas en73/74/145/146.
  Modelos109/110/181/182 y TIM de los cuatro packs idénticos al backup del ensayo
  histórico del pecho (`chest_audit/candidate/runtime-before`); cambios en DBI A
  y bancos SEDT. No respalda pérdida del parche ni sustitución del modelo/textura.
- `_work/stage_import/strike/vram-rectangle-audit.json`: sin solapamientos directos
  entre rectángulos TIM estáticos del escenario209 y pack73. No demuestra ausencia
  de relocación/copia/animación de paletas durante ejecución. La hoja histórica
  `chest_audit/chest-before-after.png` muestra corrección del atlas/emblema, no una
  malla de armadura añadida. La discrepancia visual reportada sigue abierta.
- Iniciada captura `_work/strike_stage_chest_vram_probe.py` usando debug existente,
  cuatro dumps6000/7200/8400/9600 con confirmación en log de esta partida antes de
  copiarlos. Sin cambio de assets ni bypass; comparación de atlas/paletas pendiente.
- Resultado de esa captura: run `20261106T095426567529Z-strike-stage-chest-vram`,
  cuatro dumps confirmados, cierre171,975s/restauración21 saves y ajustes verificada.
  `chest-vram-comparison.json` y `chest-vram-phase-summary.json`: f6000 es anterior
  a carga de Strike (último trace ch0, fase377/380/0), no evidencia de corrupción.
  En f7200/8400/9600 ambos atlas tienen cero píxeles distintos; CLUTs exactas en
  7200/9600. En8400 difieren30 palabras de CLUT del TIM4; TIM5 exacto. No se observan
  las copias destructivas de360 palabras. Pendiente atribuir la diferencia de paleta,
  no asumir corrupción ni aceptación visual. Captura final oscura dice Dance Viewer:
  no tratar este cierre como aceptación de canción/retorno.
- El propietario propone Dance View para comparar pose por pose; se adopta como
  siguiente aislamiento de pecho/presentación. Boot del probe histórico falló por
  guard que exigía `strike_p1/p2=bag2` cuando ambos ya son bag1; preparación previa
  al try dejó ajustes temporales, restaurados manualmente desde
  `viewer-run/20261106T045814/baseline`, hashes originales verificados/sin juego abierto.
  Wrapper `_work/strike_viewer_current.py` acepta bag1 o bag2 sin modificar el script
  histórico; segundo boot iniciado. No afirmar visor abierto hasta resultado.
- Segundo boot confirmado: Dance View PID19820, evidencia
  `_work/character_import/strike/viewer-run/20261106T045944`, sesión en
  `_work/character_import/strike/viewer-session.json`. Selección Down/S/S llega
  a Strike BAG1; clip0 confirmado visualmente como NEUTRAL, cámara0/speed30.
  `clip-0-1793959289949833300/review-small.png` muestra el emblema S visible.
  No prueba que todas las poses/materiales estén correctos ni explica intermitencia.
  Mantener sesión abierta para revisión; ajustes temporales aún pendientes de
  restaurar mediante `py -3.13 _work/strike_viewer_current.py close` tras coordinar
  con el propietario. No restaurar bajo proceso activo ni confundir salida de boot
  con cierre del juego. No modificación de modelos/animaciones/runtime en este paso.
- Aclaración posterior del propietario (2026-11-06): la protección del pecho falla
  **sin ninguna pose seleccionada**, no durante la reproducción de NEUTRAL. Captura
  fresca `probe-1793959590516897500.png` en el mismo directorio; watch f024281:
  root19, mode4, viewerFFFF. Comparar FFFF frente a clip0 sin cambiar cámara/costume;
  el éxito visual de NEUTRAL no acepta el estado sin selección.
- Nueva incidencia autorizada: Dance View con Strike BAG1 carga el escenario BAG1
  pero el propietario escucha la canción Strike BAG2; debe usar también la canción
  BAG1. El log de la sesión solo contiene `activate` y ningún `song ...strike_game`.
  `b1m_filter` exige extensión BUST2_01, sector/canal del perfil y shim/modelo
  importado; todavía no se identifica cuál falla en el visor. No ampliar canales ni
  sustituir audio globalmente sin observar esas entradas. La sesión PID19820 sigue
  abierta; coordinar cierre antes de reconstruir/desplegar instrumentación.
- Continuación verificada: PID19820 cerrado con restauración de ajustes/saves.
  Diagnóstico opt-in `BAG2JP_TEST_VIEWER_AUDIO=1` (32 combinaciones como máximo)
  en `bag2jp_bag1_stage.c`: run `viewer-run/20261106T051542` muestra modelo ID1,
  shim correcto, XA37083/canal1 dentro de37082..64242, pero perfil nulo porque el
  root del visor es **0x19**, no **0x13**. Los watches imprimen hexadecimal; no
  confundir `19` con el root decimal19 del combate. Corrección mínima permite
  root0x19 SOLO con mode4 y conserva shim/modelo/ID/canal/extensión existentes.
- Regresión del audio: fallo de aserción PCM al reproducir root0x19/mode4 antes
  de corregir, luego dos tests audio/visibilidad verdes (3,855s). Primer intento
  de test diagnóstico falló por símbolo ausente; stub produjo después la aserción
  esperada, antes de implementación. Revisión contra backup de esta fase sin
  cambios ajenos. Consumidores compartidos: filtro, duración y fixture de
  visibilidad (este último sigue opt-in/off; no se acepta el bypass previo).
- Build `20261106T101904477460Z-strike-viewer-bag1-song` pasó en28,492s;
  exe experimental SHA256 `f59c6809b459f3601d26e3a4a938c0b557a7baca700380fa01cd94fca4d614b3`.
  Nueva sesión PID20508/run `viewer-run/20261106T052003`: log confirma perfil1,
  apertura `strike_game.flac` y duración136→129s. Aceptación auditiva humana
  pendiente; no afirmar canción completa/fin/retorno ni todos los modos aceptados.
- Pecho reproducido sin selección (`viewerFFFF`) en
  `viewer-run/20261106T051542/probe-1793960292235549000.png`; NEUTRAL en
  `viewer-run/20261106T052003/clip-0-1793960489006315100/01.png` sí muestra S.
  Comparación CPU-VRAM6000/7200 del primer run: ambos atlas y ambas CLUTs
  exactamente iguales a los TIM BAG1, cero copias destructivas360words
  (`chest-vram-comparison.json`). No prueba todos los frames ni determina causa
  geométrica; no reaplicar parche TIM histórico. Se conserva RAM6000 para trazar
  estado/bind transforms. Intento posterior `clip0` falló al salir el visor a
  root0x21; no se trató como captura NEUTRAL válida. Cierre/restauración verificados.
- La sesión de ese ensayo PID20508 quedó abierta para escucha y comparación, con ajustes
  temporales/copias de tarjetas. Cerrar mediante
  `py -3.13 _work/strike_viewer_audio_probe.py close` tras coordinar; no restaurar
  bajo proceso activo. Véase la continuación de referencia nativa abajo.
- Continuación 2026-11-06: PID20508 ya había salido al retomar. Ausencia de
  BAG2JP comprobada; `_work/restore_closed_strike_viewer.py` preservó logs finales
  y restauró ajustes y hashes de partidas originales. El RAM6000 es solo2MB;
  contiene player pointer `0x8025C3F8`, fuera del volcado. No permite diagnosticar
  sus transformaciones (`ram-inventory.json`, Ghidra014).
- Referencia BAG1, tras corrección del propietario: cargar explícitamente
  Options → Memory Card → Load Data → YES; captura `LOAD OK!`
  `native-combat-runs/20261106T053152/view-1793961416449012300.png`.
  Antes de cargar, Dance View estaba bloqueado: el intento anterior acabó en
  selección de1P y no constituye evidencia del visor. Después de cargar, abrir
  Dance View y seleccionar Strike/A. Sin seleccionar pose, **también falta la S**
  en el pecho (`view-1793961574554742900.png`, crop conservado); con NEUTRAL
  sí aparece (`view-1793961614670690400.png`). Comparación inspeccionada:
  `unselected-vs-neutral.png` en ese mismo directorio. Es evidencia del runtime
  BAG1 de referencia, no una nueva captura de hardware PS1 ni causa geométrica
  demostrada. No cambiar textura/modelo para corregir una supuesta regresión
  del port a partir de este caso.
- Decisión pendiente: conservar este estado nativo sin pose o autorizar una
  desviación visual deliberada para mostrar siempre la protección. Sin cambios
  de assets/código en esta continuación. Referencia PID41832 queda abierta para
  revisión; journal `native-combat-session.json`, cierre/restauración mediante
  `py -3.13 _work/character_import/strike/native_combat_probe.py close` cuando
  termine el propietario. Música del candidato BAG2 sigue pendiente de escucha;
  agujeros durante solos y pose inicial intermitente siguen independientes.
- Decisión del propietario: en BAG2 la protección debe verse también parado
  (sin pose, visor `FFFF`), sin forzar NEUTRAL ni cambiar bailes.
  Diagnóstico 2026-11-06 (sin cambios de assets/runtime aceptados):
  - Volcados 8 MB (opt-in `BAG2JP_RAM_DUMP_SIZE=8mb`, exe experimental
    `aee1a47c…`): `viewer-run/20261106T054637` (sin pose = WAIT slot71) y
    `20261106T055110` (NEUTRAL). Mismos nodos con matriz válida en ambos
    estados; se descarta la hipótesis de matrices nulas.
  - Los paquetes GT3 de la placa (tpage 0x1B, CLUT 0x3C) se generan en ambos
    estados con coordenadas de pantalla actualizadas: la parte inferior está en
    el nodo1 y la zona de la S en los nodos 9/10. Los emisores (`80027fc8`…,
    Capstone sobre RAM) ordenan cada triángulo en la OT por la suma de z de dos
    vértices: el orden es por polígono, sin z-buffer.
  - WAIT tiene un ciclo de respiración exacto de 88 frames: pelvis (b0) de -2,1°
    a -16,8° en x, pecho (b1) de -0,4° a +11,6°, cuello (b8) de -0,3° a +8,6°
    (`run_strike_wait_cycle.py`, run `20261106T061013`). La S aparece y
    desaparece según la fase del ciclo; la ventana exacta de fase no está
    resuelta.
  - Se comparó con el WAIT de un personaje BAG2 de serie (ch8, run
    `20261106T061818/stock-wait-2`, `_work/compare_wait_breathing.py`). La
    amplitud de pelvis, pecho y cuello es **igual** a la de Strike; solo cambia el ritmo:
    Strike tiene 45 frames con paso 2 y el de serie 55 frames con paso 3 (≈2× más lento). Esto
    contradice la hipótesis de que la respiración de BAG2 es más suave. Causa
    probable: la S de los nodos 9/10 queda ordenada detrás de la piel del torso
    en algunas fases.
  - Herramienta: `tools/bag1import/motion_codec.py` (formato leído de
    FUN_800126f8/800128b4/80012850, Ghidra015) hace un round-trip exacto de 104
    motions por volcado. Regresión: `tools/test/test_motion_codec.py`.
  - Pendiente de decisión del propietario: (a) sesgo de profundidad o adelantar
    los polígonos de la placa (causa raíz, sin tocar la animación) o (b) ralentizar
    o suavizar el WAIT de Strike (no corrige la oclusión).

- Ensayo humano con bypass confirmado:
  `_work/versus-runs/20261106T094126581420Z-strike-live-autoplay`,
  `visibility-activation.log` y `visibility-trial.txt`. El propietario informa
  que los huecos persisten durante cámaras de solo y también la pose inicial
  como caminando. Omitir el descarte lateral de pantalla no basta para corregir
  los huecos; no demuestra por sí solo cuál de clipping/orden/texturas los causa.
  No aceptar ni promover el bypass. Cierre323,359s, restauración verificada de
  controles/settings/mods y21 saves; control temporal eliminado por el driver.
- En ese mismo ensayo el propietario señala ausencia de la protección del pecho
  previamente esperada y aporta captura. Posible discrepancia de modelo/costume o
  paquete, sin causa demostrada. Antes de restaurar nada: contrastar versión y
  hashes realmente cargados con historial de la protección; preservar trabajo previo.
  No atribuirlo automáticamente al bypass ni reintroducir un parche histórico
  eliminado sin comprobar su propósito y la decisión del propietario.

- El propietario observa ocasionalmente una pose adelantada/no erguida en
  cualquiera de los dos lados. No atribuirla exclusivamente a Strike ni forzar
   postura de pie sin contrastar el papel nativo de la presentación.
- Reconfirmado por el propietario en la partida `20261106T092907543033Z-strike-live-autoplay`:
  unas presentaciones muestran a Strike erguido y otras con una pierna levantada,
  como caminando. Evidencia visual aportada por el propietario; incidencia abierta,
  no corregida ni aceptada. No atribuir intermitencia a reinicio sin medir frame/matrices.
- Evidencia existente, no nueva partida:
  `_work/versus-runs/20261106T081736509909Z-strike-live-autoplay/bag2jp_anim_trace.log`,
  líneas1299..1323. En f6599 P1 usa anim73/req104 y P2 anim71/req106;
  en f7037 P2 pasa a anim72/req103, vuelve a71 en f7362.
  Al entrar en fase1/3/3 (f7484) quedan73/71; ambos pasan a0 en f7490,
  reciben req0 en f7490/7491 y continúan con anim6/req1 en f7622/7623.
- Esto acredita transición de identificadores, **no** frame local, matrices,
  postura visual correcta ni descarte de un fallo intermitente de reinicio.
  Roles compartidos71=stand/source60 y72/73=appeal/source62; el perfil Strike
  no los sobrescribe. Igualar todos a stand ocultaría el papel de appeal.
- Próxima comprobación: correlacionar fotograma de presentación/transición con
  request, frame local y final de source62; comparar los dos lados y control BAG2.
  Sin cambio de animaciones ni aceptación nueva.

### Continuación de la evidencia de audio

- Implemented in `bag2jp_bag1_stage.c`: shared Heat/Strike music profiles, isolated
  XA channels, decoder switching, per-song duration override/restoration. Heat keeps
  its existing CD/game option; Strike uses the extracted game edit only.
- Native BAG2 evidence: main EXE `0x8001E3CC..1E3D8` copies stage id from
  `0x8005E666` to song byte `0x80089240`; match overlay `005.dbi`, base
  `0x8008F890`, calls `0x800358BC` at `0x800986EC` with that byte.
  Song start selects channel `index&7` and file `index>>3`; stage1 therefore uses
  `XA/BUST2_01.XA` channel1 and duration table `0x800555A8` u16 index1 (stock136s).
- JP BAG1 duration is **129s**, not the decoded file's132.053333s: native
  `0x80039A34..39A58` indexes the u32 table `0x800553F4`, entry1=129.
  Keep chart start920, frames6264, beats192; no extra fade or trim introduced.
- Source `_work/stage_import/strike/audio/dancexa1_s1.wav`: 37800Hz stereo,
  SHA256 `a05012d326579b76c53e1de96b88f2407cc4cd9ac3f2e3e2229674325903e42f`.
  `D:/ffmpeg/bin/ffmpeg.exe -hide_banner -loglevel error -n -i
  _work/stage_import/strike/audio/dancexa1_s1.wav -ar 44100 -ac 2 -c:a flac
  _work/stage_import/strike/audio/strike_game_44100.flac` produces the plugin's
  required44100Hz stereo. File14487342bytes, SHA256
  `880b02ef763284625fbfa91b7d9589f6bf2e07ea38cd0cfd535d549a47313d3d`.
  Staged as `1.0.0/bag1_music/strike_game.flac` in canonical/build/experimental
  packages; the earlier37800Hz FLAC is an unused intermediate, not deployed.
- Host regression `tools.test.test_bag1_stage_audio` failed before implementation
  and passes afterward: channel/slot isolation, Heat/Strike switching, seek, EOF,
  previous-filter chaining, stock duration restoration and external-write preservation.
- Build `20261105T235959660433Z-strike-song-profile` passed. Experimental exe
  `e29dce9774dddfd538af022dffd445b9292e621312a6cda0f924b5ae5201c7b7` deployed;
  old exe retained at `_work/stage_import/strike/audio/BAG2JP.before-song.exe`.
  Calibration `20261106T000120988911Z-strike-song-calib` reviewed,21saves verified.
  Estado de ese build: probe aún en curso entonces; resultado posterior en los
  runs 000303/002321 de abajo. No tratar este hash como ejecutable vigente.
- SFX y banco de sonido: el SEDT de Strike BAG1 tiene el banco 0 nativo (cues 4100–4102)
  fusionado con los bancos 1..3 de fever stock de BAG2 (cue 4000). Total 4 bancos, 103048 bytes.
  Empaquetado mediante `build_stage_package.py` con opción `native_sfx_bank0: true`.
  Test unitario `tools.test.test_stage_port` verifica la presencia exacta del banco 0 nativo.
- Selector de 15 filas: ampliado en `system/007.dbi` de 14 a 15 filas (Heat BAG2/1, Hiro, Kelly,
  Strike BAG2/1, Tsutomu, Capoeira, Bi-O, Shorty, Kitty-N, Gas-O, Comet, Robo-Z, Random).
  Aritmética MIPS de rand() modificada para división por 14 (`0x4924924A`, shift 2, resta de 14*q).
  Fila 5 muestra `< STRIKE BAG1 >` y miniatura `strike_bag1.png`. Fila 4 muestra `< STRIKE BAG2 >`.
  Tests `test_native_menu.py` y `test_stage_version.c` pasan al 100%.
  Run en vivo `20261106T004800028681Z-strike-15row-selector` recorrió el carrusel, seleccionó la
  fila 5 independientemente del personaje (Strike BAG2 elegido en character select), y verificó
  la carga de `entry 209 -> BAG1` y la música `strike_game.flac`. 21 tarjetas restauradas e intactas.

## Strike: mejoras aplazadas (decisión del propietario 2026-11-06)

Propietario: «Descartalo por ahora, que sea un punto de mejora para el futuro cuando
tengamos todos los personajes importados». No se trabaja en ellas hasta entonces:
- **S del pecho en WAIT/Dance View sin pose**: la S parpadea según la fase del ciclo de
  respiración (88 frames) por ordenación por polígono en la OT. BAG1 nativo se comporta
  igual y el WAIT de un personaje BAG2 de serie (ch8) tiene la misma amplitud. Opción
  recomendada al retomar: sesgo de profundidad o adelantar los polígonos de la placa
  (nodos 9/10). Diagnóstico completo arriba, en las secciones del pecho.
- **Texturas huecas del escenario de Strike durante solos**: ver «Prueba pendiente:
  estructuras laterales durante solos». El bypass de límites de pantalla no basta.

## Strike: candidato visual experimental (2026-11-05)

- El propietario autoriza avanzar hasta evidencia visual antes de consultarle.
  El plan sigue abierto; escucha humana y campaña real no están aceptadas.
- `build_stage_package.py --profile strike` genera209 desde datos JP: tres TIM nativos,
  atlas común reubicado, cuatro TIM de relleno, modelo44huesos escala3/2, intro JP
   y cámaras de baile BAG2. Lista de animaciones vacía experimental; banco SFX stock
   en esta revisión inicial (sustituido posteriormente).
- Tres pruebas WSL `tools.test.test_stage_port` verifican estructura, referencias de
  llamadas y Heat DBI idéntico al admitido. Payload `5acc109af8814ef86f710868bc9d1157c7164975f15af0c71f64c4350619465b`:
  19 entradas anteriores intactas, capacidad comprobada4270080≤27648000bytes.
  Fuentes y backups: `_work/stage_import/strike/candidate/`; detalle en el plan.
- Primer run `20261105T232648082595Z-strike-stage-candidate`:36s, `entry209 -> BAG1`,
  bailarines activos, suelo de rejilla, fondo negro; restauración21saves verificada.
- Corregido shim: ahora rellena niveles/flags para ids0/1, no otros; audio sigue
  limitado a Heat. Regresión C `py -3.13 -m unittest tools.test.test_bag1_stage_shim`
  falló antes y pasó después. Build `_work/workflow/20261105T233345251626Z-strike-stage-shim/`.
  Exe experimental `4624122f3435f5f3664050489f3d729957b100367391a8c2308f66d115f181ea`.
- Calibración revisada `20261105T233443293596Z-strike-stage-shim-calib`. Run posterior
  `20261105T233632011571Z-strike-stage-candidate`:12capturas de juego, separadas7s,
  muestran ataques, niebla y luces verde/rojo; entorno de rejilla sobre fondo negro.
  `stage-sheet.jpg` y logs conservados. **El wrapper agotó240s** después de capturar;
  no es una ejecución completa/aceptada. Ya no había proceso; `recover_timed_probe.py`
  restauró y verificó hashes de ajustes, controles y estado de mods. El hash previo
  de las21tarjetas quedó en memoria y no se pudo verificar tras la interrupción;
  la prueba solo configuró tarjetas copiadas. No declarar restauración total verificada.
- El propietario confirma «si corresponde» al revisar las capturas: el entorno mostrado,
  incluido el fondo negro, corresponde al escenario BAG1 esperado.
- Audio Strike completado: `strike_game.flac` (44.1 kHz, 129 s) y guard de root de juego
  `0x13` implementados y probados en vivo (`20261106T000303289538Z` y `20261106T002321415753Z`).
  Las 21 tarjetas originales verificadas intactas tras canción completa y retorno al selector.
- Selector de 15 filas completado: carrusel en `system/007.dbi` ampliado a 15 filas con
  módulo aleatorio `/14` por multiplicador recíproco `0x4924924A`, fila 5 para Strike BAG1
  (`< STRIKE BAG1 >`) y fila 4 para Strike BAG2. Verificado en vivo en `20261106T004800028681Z`.
- SFX de escenario integrados: Banco 0 nativo de `ST_STRI.DFS` (cues `0x4100-0x4102`)
  unido con bancos 1-3 de fever stock en `strike_209.dfs` (103.048 bytes). Verificado en vivo
  en `20261106T010056170156Z-strike-15row-selector`.
- Regresiones del carrusel de 15 filas verificadas en vivo: Heat BAG1 fila 1
  (`20261106T012500289564Z-heat-b1-regress`) y Strike BAG2 stock fila 4
  (`20261106T012746447672Z-strike-b2-regress`), ambas con 21 tarjetas intactas.
- Endings y campaña: `bag2jp_bag1_endings.c` actualizado para soportar modos 1 y 0 (campaña)
  además de modo 5 (Ending View); verificado con `test_bag1_endings.py`.
  Rutas de ending verificadas en vivo para Strike BAG1 A (`20261106T014236347408Z`),
  Strike BAG1 B (`20261106T014508143093Z`), Strike BAG2 stock (`20261106T014745480316Z`)
  y Heat BAG1 (`20261106T015016909315Z`), todas con 21 tarjetas verificadas.
- No se tocó la instalación estable ni se reactivó la iluminación de actor descartada.

## Strike: inventario histórico usado por el candidato (2026-11-05)

- Plan aprobado: `plans/strike-bag1-stage-song.md`; inventario histórico usado para
  el candidato experimental descrito arriba, no aceptación final.
- Preflight pasó: `_work/workflow/20261105T214104047068Z-strike-stage-inventory/`.
- `source_comparison.json` en `_work/stage_import/strike/`: extracción directa del disco
  JP `STAGE/ST_STRI.DFS` (LBA16850, 228288bytes). Su DBI **no coincide** con el anterior
   `STAGEE/ST_STRI.DFS`; las otras seis entradas sí. Base JP verificada `0x801DCDF8`;
  no reutilizar ciegamente las direcciones US ni asumir un desplazamiento uniforme.
- `inventory.json`: listados Capstone y candidatos de llamadas/referencias (incluyen
  datos embebidos; no son todavía límites de funciones ni reglas de relocación).
  Callbacks BAG2 id1 leídos del ejecutable: `0x801E33D0/33D8/3400/3420` en las tablas
  `0x80051B88/1BBC/1BF0`, `0x80054C10`, índice1. Decomp histórico disponible en
  `_work/stagedbi/bag2_209_decomp.txt`; wrappers33D8 y3400 llaman a db680 y dbb1c.
- Modelo:44huesos, conversión seca16196bytes, sin cola. Tres TIM **4bpp**; tamaños de
  bloques comprobados. No confundir el flag CLUT `8` con 8bpp. Primeros tres slots
  verificados más abajo; los seis restantes siguen pendientes.
- Reproducción: `py -3.13 -I _work/stage_import/strike/scripts/verify_stage_sources.py`;
  después `wsl.exe -d Ubuntu --exec python3 /mnt/d/Dev/Recomp/BAG2JP/_work/stage_import/strike/scripts/inventory_stage_code.py /mnt/d/Dev/Recomp/BAG2JP`.
- `jp_base_evidence.json`: destino leído de `0x80010D30` por el cargador `0x80037228`;
  `0x8001C024` copia payload+12 y borra BSS. Callbacks JP update `0x801DDC60` y setup
  `0x801DDED8`, tablas `0x80052AA8`/`0x80054CDC`, indexadas por byte0 del escenario.
- `call_matches.json`: nueve destinos externos; cinco cuerpos binariamente idénticos
  en BAG2: `4704C→442A4`, `470DC→44334`, `4707C→442D4`, `48D3C→49824`,
  `4C758→49F24` (todos con prefijo `0x800`). Los últimos son SetPolyFT4 y el stub BIOS
  rand. Las coincidencias enmascaradas confunden stubs/inicializadores: no aprobarlas solas.
   Contraste semántico posterior: MoveImage `49ADC→46C7C`, setup de luces del escenario
   `28284→23724` y update `277F8→22FF4` conservan su interfaz; no son cuerpos idénticos.
   No confundir estas luces del escenario con la iluminación de actor descartada.
- Reproducción de llamadas: `py -3.13 -I _work/stage_import/strike/scripts/match_stage_calls.py`.
- Sprite JP `0x80032BDC`: 13 argumentos. El drawer rotado BAG2 `0x8002F824` añade un
  argumento y **no sirve** como reemplazo directo. `0x8002EE10` conserva interfaz y setup
  de cámara, pero cambia la escala mediante `0x8006D98C`; solo coincide algebraicamente
  con JP si ese valor es384. No es una constante garantizada: `0x80014330` lo escribe
   desde los12bits bajos del halfword de un parámetro. Equivalencia visual aún abierta.
   `sprite_animation_checks.json`: modelo aritmético de576 combinaciones positivas
   (no ejecución MIPS). Con perspectiva384, cero diferencias; con256/512 aparecen
   476/501 diferencias. No prueba cámara/proyección ni todos los rangos/overflow.
    No aprobar el mapeo directo: evaluar un helper local que conserve la aritmética JP,
    sin modificar la perspectiva global del juego.
    Prototipo aislado posterior: `sprite_local_prototype.bin`,660bytes, copia del drawer
    BAG2 con nueve palabras originales verificadas antes de cambiar el denominador y
    los dos desplazamientos. Conserva cámara, cinco llamadas externas y tres saltos
    relativos internos; elimina la lectura de perspectiva global. No está desplegado
    ni tiene aún ubicación en el overlay. `sprite_local_prototype.json` registra hashes.
    `py -3.13 -I _work/stage_import/strike/scripts/prototype_local_sprite.py D:/Dev/Recomp/BAG2JP`
    compara los bloques aritméticos JP y adaptados mediante un intérprete limitado de
    sus instrucciones enteras:10600casos, cero diferencias (incluye negativos y
    overflow de32bits). No ejecuta GTE, cámara, asignación de primitivas ni el flujo
    completo; la equivalencia visual y la integración siguen pendientes.
- Texturas: tablas principales JP `0x80054CAC[1]→0x80053E0C` y BAG2
  `0x80054BDC[1]→0x800538EC` verificadas. **No usar `0x800538BC`** (hipótesis anterior).
  `texture_loading_audit.json` verifica tres descriptores JP (`strist1/2/3.tim`) y
  terminador, frente a nueve BAG2 y terminador; stride `0x30`. Ambos callers arrancan
  en DFS2; loaders `0x80034FD4`/`0x80031268` avanzan un archivo por descriptor.
  Por tanto, TIM JP2/3/4 corresponden a los primeros tres slots BAG2 `002/003/004`.
  Los overrides XY son−1: se conservan coordenadas de los TIM. El cargador escribe
  CLUT/tpage en descriptor+`0x14/0x16`, rectángulo imagen en+`0x28`.
  El MoveImage del DBI usa JP descriptor1+`0x28/0x2A`: destino equivalente BAG2
  `0x80053944/0x80053946`, no las referencias del DBI stock a otros descriptores.
   `texture_overwrites.json`: conservar los TIM stock005..010 cambia45palabras de las
   paletas JP (15 desde006 y30 desde007). Simulación de uploads por cabeceras TIM,
   sin runtime. Rellenar esos seis slots con copias del TIM JP4 mantiene los nueve
   archivos esperados por el cargador y cambia cero palabras nativas en la simulación;
   es candidato, no aceptación de materiales/modelo/animación. Reproducir con
   `py -3.13 -I _work/stage_import/strike/scripts/check_texture_overwrites.py D:/Dev/Recomp/BAG2JP`.
   No está terminada la construcción del archivo209.
- Referencias globales: `global_candidates.json` registra búsquedas regionales, no reglas
  automáticas de relocación. Tabla trigonométrica completa:8192bytes JP`0x8004E114`
  idénticos y únicos en US`0x80051B74` y BAG2`0x8004E488`; SHA256
  `e1a5c352df03529eeaf6bfcb3ccae70163a6303976191b27e503ee860298a006`.
  Por tanto JP`0x8004E914/0x8004EE14` corresponden a BAG2`0x8004EC88/0x8004F188`,
  conservando sus offsets, no ambos al inicio de la tabla. Reproducir con
  `py -3.13 -I _work/stage_import/strike/scripts/match_stage_globals.py D:/Dev/Recomp/BAG2JP`.
  Update JP`0x801DDC60` y US`0x801E25DC` aplican la misma selección de fase de tres
  estados a su acumulador (`JP0x8006F63C`, US`0x800774DC`); no etiquetar el primero
  como flags de beat. Los bytes comparados después (`JP0x8006F638/0x8006EACC`)
  corresponden al nivel actual/anterior US, no dos flags de beat.
  Luces: JP`0x8006EA80` contiene configs destino de72bytes, no matrices; se copia a
  `0x80075D30` al terminar la transición (`0x80027C00..`), como BAG2
  `0x8005F220→0x8005F308` (`0x80023314..`). Las matrices destino son JP`0x8006EAE0`.
  Además hay referencias indexadas omitidas por el escáner léxico: JPstage
  `0x801DDE08/0x801DDE14` escribe arrays `0x80075ED0/0x8006EBB8`; auditar también
  esas rutas, no declarar completo el inventario LUI por sus candidatos iniciales.
  Nueva dependencia del atlas común: el sprite JP lee CLUT desde descriptor
  `0x80054D9C+0x14` (`kyotu12.tim`, suma CLUT`0x2C0`) y tpage desde
  `0x80054D0C+0x16` (`kyotu00.tim`). No son los TIM propios de ST_STRI. Esos nombres
   no aparecen en el exe BAG2. Auditoría posterior `common_atlas_audit.json`: extraído
   `DFS1/G_COMMON.DFS` del disco JP. Caller `0x80036E78..88` pasa tabla `0x80054D0C`
   al cargador `0x8003532C` con cursor DFS1; cinco descriptores corresponden a entradas1..5.
   Comprobadas tres palabras originales del caller. `kyotu00.tim` es entrada1: imagen
   VRAM en palabras `(512,256,64,256)`; `kyotu12.tim` es entrada4, solo paletas.
   Su CLUT base `(992,64)` más `0x2C0` selecciona exactamente `(992,75,16,1)`,
   id `0x12FE`; SHA256 de esos32bytes
   `bac689549b18946f2622fb1c0c7f0ede945a527e36a1641d383fc3478dd4d2d2`.
   Ninguna imagen no vacía coincide por bytes con los671TIM extraídos de BAG2
   examinados; esto no cubre recursos comprimidos/no extraídos ni prueba ausencia
   de un equivalente visual. Se excluyen coincidencias triviales de imagen vacía.
   Falta decidir ubicación segura en VRAM BAG2 y enlazar atlas/paleta al helper;
   no copiar el atlas global sobre recursos activos sin comprobar ocupación.
   Reproducir: `py -3.13 -I _work/stage_import/strike/scripts/audit_common_atlas.py D:/Dev/Recomp/BAG2JP`.
   Referencias del caller: `common_loader_ref_80036e78.txt`, generado con WSL por
   `scripts/find_common_loader.py` bajo `_work/stage_import/strike/`.
- `review_stage_model_load_bag2.txt`: `0x80032A40` recibe el cursor devuelto por el
  cargador de texturas (11 con nueve TIM), copia modelo y cámara consecutivos y,
  **solo para ids1/2**, lee además el archivo siguiente de animaciones (`0x80032B00..3C`).
  Por eso209 usa slots011/012/013. Acortar la tabla a tres TIM desplazaría también esas
  lecturas; no basta sustituir tres imágenes. Se debe conservar coherencia entre tabla,
   archivos y animaciones; las animaciones stock de31huesos no están validadas con44huesos BAG1.
   Auditoría adicional:013.bin tiene dos registros de3616/1220bytes, cada uno precedido
   por su longitud, y terminador u32=0 (4848bytes exactos). No interpretar sus campos
   de cabecera como índices de hueso sin revisar el consumidor.
   `0x800125FC` construye la lista y devuelve el contador; `0x800329EC` y
   `0x800126A4` omiten sus bucles si ese contador es0. Un archivo de cuatro ceros
   representa una lista vacía en ese lector, pero **no acredita** que los demás
   consumidores ni el movimiento BAG1 funcionen con ella. Aún no sustituir013.bin.
   Evidencia: `review_stage_animation_{list,bind,init}_bag2.txt` y
   `sprite_animation_checks.json`; reproducción:
   `py -3.13 -I _work/stage_import/strike/scripts/check_sprite_and_animation.py D:/Dev/Recomp/BAG2JP`.
- Luces: destinos de matrices JP `0x8006EAE0` (0x60bytes)→BAG2 `0x8005F268`;
  countdown `0x8006EBD8`→`0x8005F2D8`; progreso `0x80075EE8`→`0x8005F3C0`;
   matrices actuales `0x80075E68`→`0x8005F350`. Restan otras globales del DBI.
- Corrección del supuesto «modo0xB»: en BAG2, el loader `0x80032A40` guarda su
  argumento stage-id en byte0 del objeto (`0x80032B44/4C`) y publica ese objeto en
  `0x80089200` (`0x80032EE4/EC`); caller `0x80033B1C/24` pasa el destino y el id.
  Por tanto, el guard del renderer compara **id de escenario11**, no un modo
  independiente. Strike usa id1: ese guard no debería excluir su escenario.
  Nueve palabras del ejecutable verificadas por `check_sprite_and_animation.py`;
  sigue pendiente probar los disparos en el escenario importado, no quitar la guarda.
- Reproducción adicional (WSL python3, rutas absolutas como arriba):
  `scripts/review_stage_equivalents.py` y `scripts/audit_texture_loading.py` bajo
  `_work/stage_import/strike/`; salidas `review_*.txt`, `texture_caller_*.txt`,
  `texture_loading_audit.json`, `perspective_ref_*.txt`. Evidencia estática, no aceptación visual.
- Siguiente de aquella fase (histórico): resolver escala/globales y consumo de
  miembros antes del candidato. La identificación anterior de 0xB como **stage-id11**
  invalida la antigua frase «modo sin identificar». El estado posterior está al
  principio; escucha humana, fidelidad restante y campaña real siguen separadas.
