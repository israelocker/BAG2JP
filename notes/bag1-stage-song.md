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

## Strike: audio profile candidate (2026-11-06)

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
