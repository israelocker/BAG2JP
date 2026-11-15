---
id: tool-evidence-bag2-record
title: "Evidencias: bag2_record.py (grabación de validaciones en juego)"
tags: ["tools", "evidence", "ffmpeg", "video", "audio", "testing"]
summary: "Historial del grabador de video + audio exacto del juego alineado a fotogramas; obligatorio en toda validación en juego."
related: ["AGENTS.md", "notes/assets.md", "tools/test/bag2_record.py", "notes/tool-evidence/ffmpeg-skill.md"]
created: "2026-11-12"
updated: "2026-11-14"
doc_kind: evidence
---

# bag2_record.py - historial

## 2026-11-14 - Bloque 3: toma natural block3-stage-c

- Propósito: verificar en juego el escenario GasOBAG1 (ventilador, cámara intro, eventos de puntaje B1ST y rótulo HUD GAS-O) sobre la base ±870 (`ff800b28`, `bag1_alt.bin` `847058C4`).
- `run_recorded_block2.py` (sin `--fixture`, autoplay natural) + `finalize --tag block3-stage-c`: `accepted: true` bajo `wgc`, `2003` heartbeats (`1` dropped_late, `0` stalls, jitter p99 `10.97 ms`, `59.941 fps`), `11977` pares audio (`0` descartes, `44055 Hz`, residual p99 `17.29 ms`, ventana `9.52 ms`). `owner.mp4` SHA-256 `d5eee3454fd7048f…`. 150 saves y ajustes restaurados.
- Revisión: hojas `take-c-sheet-intro.png` y `take-c-sheet-song.png` + `bag2jp_watch.log` en `_work/gaso/block2/take-c-review.json`. Límites: latencia de pantalla ±2 fotogramas estimada; audio subjetivo requiere escucha humana; velocidad del ventilador juzgada solo por RAM. Resultado: útil; tiempo no medido.

## 2026-11-14 - Bloque 2: tomas block2-attack-a y block2-duet-b

- Propósito: ataque Gas-O (tanque/CAUGHT) y fever de dueto sobre la base ±870, runtime ff800b28.
- `run_recorded_block2.py --fixture …` + `finalize --tag block2-attack-a`: accepted=true,
  1998 heartbeats (1 perdido), 1 stall, jitter p99 11.1 ms, 59.938 fps; 11959 pares audio,
  1 descarte, residual p99 16.47 ms, ventana 8.11 ms.
- `finalize --tag block2-duet-b`: accepted=true, 2020 heartbeats, 1 stall, jitter p99 9.7 ms,
  59.940 fps; 12103 pares audio, 28 descartes, residual p99 16.07 ms, ventana 7.06 ms.
- Revisión: hojas ffmpeg (`_work/gaso/block2/take-*-sheet-*.png`) ubicadas por `events.json`
  y `frames`. 150 saves/configs restaurados en ambas. Resultado: útil; tiempo no medido.

## 2026-11-14 - go-plus2: medición, calibración y partida aceptadas técnicamente

- Propósito: referencia GO+2 s del propietario y validación del candidato ±870.
- `finalize --tag go-plus2-measure` (runtime 26c21150…): accepted=true, 323 heartbeats,
  0 stalls, jitter p99 10.7 ms, 59.948 fps; 1909 pares audio, 0 descartes. Sampler RAM 25 s.
- Runtime ff800b2857a43c8924473c03dc0c7df04c2658aaa9c3188bc19061b0de8900df:
  `finalize --tag go-plus2-cal`: accepted=true, 546 heartbeats (8 tardíos), 0 stalls, jitter
  p99 10.5 ms; 3271 pares audio, 0 descartes. 11 imágenes revisadas; catálogo d5340edb….
- `finalize --tag go-plus2-autoplay`: accepted=true, 1999 heartbeats (2 tardíos), 1 stall,
  jitter p99 10.7 ms, 59.940 fps; 11975 pares audio, 0 descartes, residual p99 17.2 ms,
  ventana 9.32 ms. owner.mp4 SHA eafd73e9ffb916180be1cf9ce9f5f376a77e4eb39ed93ef21a92a35267eb4cb4.
  150 saves/configs restaurados por el harness.
- Limitación: el sampler RAM no alcanzó GO+2 s exacto (+0.69 s y +0.88 s); la alineación
  en ese fotograma es estimación visual. Resultado: útil. Ahorro de tiempo no medido.
  Scripts en `_work/gaso/drift/end-center/` (`run_recorded_go_plus2.py`, `solve_go_plus2.py`,
  `review_go_plus2_match.py`).

## 2026-11-14 — initial-anchor: límite inicial, fallos conservados y calibración

- Runtimeeffb8edd: initial-alignment-measure y measure2 rechazadas por cierre/identidad de
  ventana tras errores del wrapper: screenshot gameplay duplicado y acceso self.args inexistente.
  La segunda conserva342 heartbeats,0 stalls,2047 pares audio/0 descartes; no es aceptación.
  Corrección scratch con test mock RED→GREEN: screenshot capture-start separado,
  `stop_recording()` sin argumentos antes del cierre; puertas del grabador intactas.
- `finalize --tag initial-alignment-measure3`:exit0,accepted=true,296 heartbeats,0 tardíos,
  0 stalls,jitter p9910.2ms,59.929fps;1771 pares audio/0 descartes,44041Hz,
  residual p9913.67ms,ventana4.99ms.150 saves/configs restaurados.
- Candidato26c211504ddaac90a0578dac7664117c682947723a5ab5dae10bef93bf7217fb:
  `finalize --tag initial-anchor-cal`:exit0,accepted=true,501 heartbeats,6 tardíos,
  0 stalls,jitter p9911.6ms,59.941fps;2975 pares audio/0 descartes,44056Hz,
  residual p9915.3ms,ventana2.49ms.150 saves/configs restaurados.
  Once imágenes revisadas y ocho bordes verificados; digest catálogo
  b5a9d3bdbf24eb2a9ef410d4bb17df7d46c062774edcd27ec08ef34d564e3153.
- Wrapper completo inicia antes del escenario y para al volver al selector, no en gameplay;
  test mock del límite PASS. Partida initial-anchor-autoplay en curso; no aceptación anticipada.
  Scripts/comandos en `_work/gaso/drift/end-center/`; ahorro no medido.

## 2026-11-14 — wider-home: medición, calibración y partida aceptadas técnicamente

- Baseline runtime5258009e, tag wider-home-camera-baseline:71 heartbeats,0 stalls,
  421 pares audio,0 descartes; ocho snapshots RAM de solo lectura junto a captura.
- Candidato effb8edd971992655aa06ce88d05b21e65dc83b73e742265f5ebc45597612216,
  wrapper `_work/gaso/drift/end-center/run_recorded_wider_home.py`, sin fixtures de ataque.
  `bag2_record.py finalize --tag wider-home-cal`:exit0,accepted=true,484 heartbeats,
  8 tardíos,jitter p9913.6ms,59.942fps,0 stalls;2883 pares audio,0 descartes,44056Hz,
  residual p9914.62ms,ventana1.87ms. No cambios en puertas ni video original.
- Selector y ocho bordes revisados en hojas compactas; catálogo digest e87fbe8a…,
  `wider-home-cal-accept.json`. Restauración150 saves/configs verificada por harness.
- `bag2_record.py finalize --tag wider-home-autoplay`:exit0,59.04s;accepted=true sin
  alterar puertas,1714 heartbeats,1 tardío,jitter p9911.27ms,59.942fps;una pausa63ms trasgf7992.
  Audio44057Hz,10279 pares,0 descartes,residual p9916.01ms,ventana6.97ms;WGC182 checks PASS.
  Runtimeeffb8edd…,owner.mp4 SHA79fc77962d192796f5cc106393f75ce9b1f0feda1746c03ebcb74cf8a0d84bfc.
  Run20261114T132537881098Z-wider-home-autoplay:150 saves/configs restaurados.
- Análisis determinista `inspect_wider_home_run.py`: primer intento falló por esperar
  columna dt_qpc_ms inexistente; corregido para CSV frame/samples/producer_ticks/producer_hz.
  La pausa del productor7992→7998 mide211.2175ms; no confundir ese intervalo de seis VBlanks
  con duración exacta del stall del heartbeat. Anclas±700/radio199/final/fever/selector observados.
  Alineación inicial con ambas barras solo parcial según revisión FFmpeg; aceptación técnica
  del recorder no equivale a conformidad visual. Precisión±2 frames estimada, audio subjetivo
  humano; ahorro no medido. Siguiente:presentar candidato y límite visual al propietario.

## 2026-11-14 — WGC dance-center-autoplay2 (aceptada) y rechazo previo dance-center-autoplay

- Intento 1 (`dance-center-autoplay`, exe `0665a9c3…`): finalizado y **RECHAZADO** (`accepted: false`, `1` stall de `0.27 s` tras `gf 16026`, `1065/10009` pares audio fuera de `100 ms`; `bag2jp_clock_probe.csv` registró pausa real del productor de `369.73 ms` en `f16026->f16032`). Conservado sin recortar.
- Intento 2 (`dance-center-autoplay2`, exe `5258009e…`): grabado bajo backend `wgc` (`require_uncovered: false`, `window_guard` `180` comprobaciones `passed: true`) y **ACEPTADO** (`manifest.json` `accepted: true`, `0` rechazos): `1696` heartbeats (`1` perdido, `jitter p99: 10.61 ms`, `59.942 fps`, `0` stalls), `10145` pares audio (`0` descartes, `44057 Hz`, `residual_p99_ms: 15.66`, `window_max_ms: 6.96`), `producer_clock_copied: true` (`bag2jp_clock_probe.csv` `max 205.134 ms`).
- Inspección FFmpeg (`.agents/skills/ffmpeg-skill` `look.py --tiles 4x3` y `loudness.py --measure-only` sobre `owner.mp4` `-15.2 LUFS` / `-2.0 dBTP`) + lámina `dance-center-autoplay2-sheet.jpg` confirmaron baile centrado y pose final simétrica en `(±520, 0)`. Límites: precisión ±2 fotogramas estimada; calidad subjetiva del audio queda al juicio humano.

## 2026-11-13 — gaso-cam95-autoplay: captura válida, criterios funcionales fallidos

- Finalización en segundo plano completada una vez; no se sondeó ni se relanzó.
  Exe `e68ba69e132cbec5e0a8271072c1788fe97d9b99cbdd415785d8e088a15b6a64`;
  `manifest.json accepted=true`, `_work/recordings/gaso-cam95-autoplay`.
- Captura 191.834s, 1914 latidos, 2 tardíos, jitter p99 13.3ms, 59.940fps y un stall;
  audio 11477 pares/0 descartes, rate44055Hz, offset−101.064115s, residual p99 17.84ms,
  window_max8.83ms. Restauración de settings/cards verificada en el run original.
- `frames --tag gaso-cam95-autoplay --frame 6590 --span 35 --step 1` y revisión
  FFmpeg: 71 frames. Cámara inicial FALLA (8.536–8.8s); no es aceptación visual.
- `events.csv` contradice «sin ataques»: tanque/cue6906 gf7592 y gf9436 (~25.59/56.36s),
  ambas restauraciones posteriores. No tener fixture no demuestra ausencia de ataques.
- Resultado: grabador útil como evidencia temporal, no certificador de gameplay. No
  se solicitó conformidad ni se lanzó otro juego; causa de ambos defectos pendiente.
  Precisión ±2 frames estimada, audio subjetivo no evaluado. Tiempo/ahorro desconocidos.

Skill: `bag2-game-recording` (`D:/Dev/Tools/agent-data/shared/agents/skills/bag2-game-recording/SKILL.md`).

## 20261112-bag2-record-001 — 2026-11-12 — crear y probar el grabador

- Tipo: uso real (creación con autorización del owner).
- Diseño: video = FFmpeg gdigrab de la región cliente de la ventana (H.264 qp 0); el primer fotograma lleva la hora de reloj (`start:` del banner, comprobado: 1794469436.698643 entre 436.574 y 437.760). Audio = volcado propio del juego (`BAG2JP_AUDIO_DUMP=1`, mezcla final 44.1 kHz + `bag2jp_audio_sync.log` fotograma→muestra), no micrófono ni loopback (dshow solo ofrece cámaras). Un sondeo cada 4 ms sella con hora de reloj cada actualización de `bag2jp_frame.txt` (cada 6 fotogramas) y cada línea nueva de `bag2jp_bag1_versions.log`; un ajuste robusto da el reloj fotograma↔segundo.
- Entradas: `tools/test/bag2_record.py` SHA-256 `6b07bc408e551200bd726236671eaade3befb15426e211439314b17cb49768a1` en el ensayo; exe exp-8mb `a9296ddbf5a9de268c297d52f19e7654d95f73c71dd6fed42d9fb58b203d4f57` (P2a, sin cambios).
- Pruebas de host: `py -3.13 -m unittest tools.test.test_bag2_record` → 8 OK, incluido un finalize sintético con un pitido en el fotograma 1120 que debe sonar a 2.002 s en `owner.mp4` y `review.mkv`. Mutación (filtro de audio anulado) → falla con 3.003 ≠ 2.002: la prueba detecta desalineación.
- Ensayo 1 (`rec-smoke-1`, 15 s): funcionó, pero residuo máximo 78 ms. Causa: `tasklist` cada segundo bloqueaba el sondeo hasta 708 ms (saltos de 30–42 fotogramas). Corregido con un handle de proceso no bloqueante y una pasada de descarte de valores atípicos.
- Ensayo 2 (`rec-smoke-2`, 20 s): 200 latidos (= 20 s × 10), residuo máximo 9.0 ms (< 1 fotograma), 59.940 fps, desfase de audio −249.0 s (el juego llevaba ~4 min abierto). La etiqueta `gf 15534` a t=10.000 s coincide con el ajuste (15534.71). Hoja de contacto: imagen real, no negra.
- Límites observados: `bag2_run.ps1 -Audio` agotó 170 s sin volver (el juego quedó en una pantalla de visor con ROUTE/SPEED/CAMERA, no en partida); el ensayo no tuvo eventos del plugin ni un sonido de referencia, así que la alineación audio↔imagen en juego real queda **pendiente** de la primera partida con evento audible. Precisión de etiqueta ±2 fotogramas; la ventana debe estar visible y sin tapar.
- Dictamen: útil para grabar y localizar fotogramas; alineación de audio validada solo en host (sintético).
- Medición: record 20 s + finalize ≈ 30 s de pared; ahorro no medido.
- Siguiente paso: usarlo en la prueba Gas-O CAUGHT y comprobar la alineación con un sonido identificable (cue del ataque) contra su fotograma en el trace.

## 20261112-bag2-record-002 — 2026-11-12 — corrección tras revisión Goldfish y deriva del audio

- Tipo: corrección de bag2-record-001 (no reescribe su conclusión; la matiza).
- Revisión Goldfish (`_work/goldfish/spec-bag2-record.md`, dos revisores en frío): ambos «ok con correcciones». Hallazgos confirmados, ninguno refutado:
  - un ajuste de una sola recta con descarte de atípicos ocultaba pausas en los extremos (reproducido: error de 120 fotogramas con residuo de 2 ms);
  - el desfase de audio no medía la dispersión y podía salir de otra sesión;
  - el audio se copiaba en finalize, no al parar;
  - la cabecera WAV atrasada y `-shortest` recortaban hasta 1 s de video;
  - ffmpeg podía quedar huérfano;
  - faltaban `argtypes`, no se comprobaba la ruta del exe y había `Tail` en modo texto;
  - la documentación afirmaba de más («logs sellados», «±2 frames», «DPI handled»).
- Correcciones:
  - reloj por tramos (`HeartbeatClock`) con descarte de sellos tardíos y lista de pausas;
  - pares de audio limitados al rango grabado;
  - audio copiado al parar;
  - `-ignore_length 1`;
  - relleno finito `apad=whole_dur` + `atrim`, porque `apad` + `-shortest` no terminaba nunca dentro de `filter_complex`;
  - límite `-t`, `try/finally` y BrokenPipe;
  - `argtypes`, ruta del exe con `QueryFullProcessImageNameW` y comprobación de monitor principal;
  - `Tail` binario y latido con mtime;
  - etiquetas `gf` mediante subtítulos ASS (`labels.ass`);
  - `manifest.json` con `accepted`/`rejections`; finalize sale con 5 si se rechaza.
- Hallazgo en vivo (`rec-smoke-3`, 20 s, exe `a9296ddb…3d4f57`): la primera versión corregida rechazó la grabación porque el 2.9 % de los pares se desviaba más de un fotograma, sin ninguna pausa. Causa medida:
  - el volcado escribe trozos desiguales por vblank (693/777/936/534/1230/240), lo que da ±20 ms por par;
  - promedia exactamente 735 muestras por fotograma emulado, es decir unos 44056 Hz frente al reloj de pared a 59.94 fps, una deriva del 0.1 %: 17.5 ms en 20 s y unos 180 ms en 3 min.
- Corrección de la deriva:
  - recta (muestra → segundo de video) con un descarte de líneas rotas (> 100 ms);
  - tasa efectiva redondeada a entero, porque `asetrate` solo acepta enteros;
  - desfase por mediana a esa tasa;
  - el audio se reproduce con `asetrate=<tasa>,aresample=44100`, lo que desplaza el tono un 0.1 % (unos 2 cents).
  - Puertas:
    - tasa a menos de 1 % de 44100;
    - pares descartados ≤ 0.5 %;
    - mediana de residuo por ventana de 1 s ≤ 1 fotograma.
- Pruebas de host (`py -3.13 -m unittest tools.test.test_bag2_record`, test SHA-256 `4412cd12edeb3732e5a98a0b34fde2832ffb40adb7bbe5e6368c1c5df8e1a39c`, script `f07455fcb8076b6ef38d9f48c0dd6c0b11726c8daeb3e9890b86db2fc26a9d0d`): 12 OK. Cubren:
  - sello tardío, pausa cerca del final, latido viejo y audio de otra sesión;
  - volcado en trozos reales;
  - desfase positivo y negativo, y video completo pese a la cabecera atrasada;
  - toma de 20 s con deriva del 0.65 %: pitidos a 1.001 s y 19.019 s, medidos a 1.000998 s y 19.01907 s.
  - Mutaciones detectadas: desfase anulado (falla por 1.0 s) y tasa forzada a 44100 (falla por 129 ms).
- Re-finalize en vivo de `rec-smoke-3`: ACEPTADA.
  - Reloj: 200 latidos, 0 descartados, jitter p99 11.8 ms, 59.940 fps, 0 pausas.
  - Audio: tasa 44057 Hz, 1189 pares, 0 descartados, residuo p99 por par 16.1 ms, ventana máx. 1.4 ms.
  - `owner.mp4` SHA-256 `a931291a69bdc89cc7167a249bd49cbd9545782e4db75f8e7fa115347cdfd186`.
- Documentación corregida: `AGENTS.md` y el SKILL ahora dicen qué se sella realmente, exigen `accepted`, presentan ±2 fotogramas como estimación sin calibrar y limitan lo probado al monitor principal al 125 %.
- Sigue sin validar: la latencia de pantalla (imagen frente a etiqueta) y la alineación con un sonido real del juego, porque el ensayo no tuvo ningún evento audible.
- Dictamen: útil, con puertas que rechazan los fallos que antes pasaban sin aviso.
- Medición: no medido.
- Siguiente paso: calibrar la latencia en la partida Gas-O CAUGHT usando el cue del ataque y su fotograma en el trace.

## 2026-11-12 - CAUGHT retire: grabación completa rechazada

- Comandos: `py -3.13 tools/test/bag2_record.py record --tag gaso-retire-heat-bag1`
  y `finalize --tag gaso-retire-heat-bag1`; exe `EA0C7F16…99F86D`, exp-8mb,
  ventana1920x1080. Audio propio del juego, nunca micrófono/loopback.
- Resultado **rechazado**, manifest accepted=false: pausa244ms tras gf18018,
  567/18469 pares fuera del ajuste, ventana34,44ms. 3079 latidos/4 descartados,
  jitter11,43ms. Archivos originales conservados en `_work/recordings/gaso-retire-heat-bag1/`.
- Contraste: `_work/gaso/review_retire_audio.py` localiza el desfase final y
  ventana de navegación gf1621–1680; terminar antes de la pausa no basta.
  No relajadas las puertas ni cambiado el grabador. Tiempo finalize y ahorro
  no medidos. Uso útil para detectar evidencia no válida, no aceptación del ataque.
- Siguiente: captura explícita combate→primer selector, tag
  `gaso-active-reuse-heat-bag1`, usando `_work/gaso/run_recorded_retire.py`;
  resultado pendiente, no asumir que otra delimitación pasará los controles.

## 2026-11-12 - active-reuse: temporización pasa, contenido inválido por oclusión

- `record/finalize --tag gaso-active-reuse-heat-bag1`, exe `11102F81…25BF1D8`,
  wrapper `_work/gaso/run_recorded_retire.py`; captura gameplay→returned-selector.
  Finalize exit0/manifest accepted=true: 1716 latidos/5 tardíos, jitter12,45ms,
  sin pausas; audio44058Hz,10267 pares/0 descartes, ventana8,24ms.
- **No aceptación de juego:** inspección FFmpeg de ocho tiempos de vídeo muestra
  otra aplicación cubriendo BAG2JP. El grabador valida límites del monitor al
  empezar, no detecta oclusión durante el ensayo; sus puertas temporales no
  certifican contenido visual. Dictamen `_work/gaso/reuse-visual-review.json`.
- Contraste: trace dos golpes en anim1 y retorno13, pero eso no convierte el
  vídeo ajeno en evidencia de BAG2JP. Conservar captura y no entregar como prueba.
  Duración de ensayo301,425s; finalize/manual/ahorro no medidos.
- Siguiente bloqueado: repetir con BAG2JP descubierto sin interferir con la otra
  sesión, o demostrar una captura directa independiente antes de usarla.

## 2026-11-12 - foreground/topmost temporal autorizado para cualquier captura

- Owner: «A todas las ventanas que necesites grabar». Implementación compartida
  `tools/test/recording_window.py`, `RecordingWindow(hwnd,pid)`; no depende de
  título ni ejecutable. `bag2_record.py` lo usa alrededor de FFmpeg, no de toda
  la partida/navegación. No cambia PowerToys ni opciones globales ni simula teclas.
- Guarda identidad/estados originales (incluidos popups propios existentes),
  pide SetWindowPos TOPMOST y SetForegroundWindow. Si Windows deniega activación,
  aborta; no usa AttachThreadInput ni altera foreground lock. Comprueba cada1s
  identidad/foco/topmost/geometría/solapamiento conservador en Z-order; ante
  pérdida detiene captura, restaura y finalize la rechaza aunque pase audio.
  Al terminar restaura foco previo solo si el usuario no eligió otra ventana.
- Fuentes oficiales consultadas con Context7 Win32 API:
  https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowpos
  y `nf-winuser-setforegroundwindow`; las restricciones de Windows son reales,
  Always on Top no equivale a permiso ilimitado para robar foco.
- RED: stub sin efectos,8 tests/7 fallos de aserción (`window-focus-red.log`).
  Primera pasada verde24 tests (`window-focus-green.log`,4,564s); después se
  endureció la restauración, verificación final pendiente de revisión Goldfish.
- Prueba Win32 real sin juego: `_work/gaso/probe_recording_window.py`, dos ventanas
  Tk propias (verde objetivo/roja competidora). Intento1 falló antes de FFmpeg
  por hash de ejecutable ausente en carpeta de ensayo; intento2 por alias Store
  `sys.executable` no legible. En ambos salió del contexto y cerró solo ventanas
  propias. No borradas evidencias `window-focus-native/` y `-v2/`.
- Intento3 usó GetModuleFileNameW para identificar el ejecutable Python real:
  `_work/gaso/window-focus-native-v3/report.json`:5 checks,guard passed=true,
  topmost y foreground restaurados. Capturó3,184s/H.264/640x420/60fps;
  `visible.png` a1s inspeccionado: ventana verde correcta, no otro juego.
  Capture exit5 esperado (no heartbeat/audio de juego en este ensayo de ventana);
  NO es aceptación de BAG2JP ni un manifest temporal verde inventado.
- Medición: duración de vídeo3,184s; tiempo manual/retrabajo/ahorro no medidos.
  Siguiente: Goldfish del helper/integración, regresión final, luego repetir solo
  la partida pendiente con el mismo exe y calibración sin reconstruir runtime.
- Goldfish de ese checkpoint: **2 revisores, ambos CON HALLAZGOS**
  (`spec-recording-window-focus.md`), confirmados y corregidos:
  - Identidad HWND/PID insuficiente si se recicla HWND dentro del mismo proceso:
    cookie privada UUID con SetPropW/GetPropW, retirada al salir. Una ventana
    recreada no hereda esa cookie. Si UIPI impide marcar el foreground previo,
    no se restaura su foco con una identidad que no se puede demostrar.
  - Popups: restauración en orden propietario→descendiente; se restauran popups
    supervivientes por su identidad propia aunque el objetivo desaparezca.
  - Ventana final sin vigilancia/cancelación: comprobación al final y durante
    cierre de FFmpeg cada100ms; proceso desaparecido/Ctrl+C son captura inválida;
    se mata/espera al hijo antes de liberar el guard incluso con segundo Ctrl+C.
  - Carrera con finalize: session atómica y estados recording/restoring/closed;
    guard pending/passed=false hasta restauración terminada. Finalize rechaza
    estado pendiente y FFmpeg no cerrado limpiamente; ausencia de guard solo
    permanece compatible con grabaciones históricas, no con sesiones nuevas.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Verificación final: `py -3.13 -m unittest tools.test.test_recording_window
  tools.test.test_bag2_record`31 tests/exit0/4,579s (`window-focus-final-verified.log`).
  Pruebas del bucle real con FFmpeg simulado, no solo un mock del bucle entero:
  muerte del proceso, interrupción y cancelación durante shutdown dejan error,
  estado restoring y no pueden aceptarse antes de terminar el guard.
- `_work/gaso/mutate_window_focus.py`:7/7 kills por fallos de aserción (copias
  aisladas, originales nunca sustituidos): sin pin, cookie ignorada,
  popup no restaurado al morir padre, cierre sin vigilancia, hijo abandonado,
  cancelación no invalidada, finalize ignorando guard. Logs `window-mutation-*`.
- Native v4/v5 tras el endurecimiento: Windows negó el foreground. v5 lo dejó
  documentado en `window-focus-native-v5/report.json`: capture_started=false,
  topmost_restored=true, window_cookie_removed=true. Ese rechazo es correcto;
  no se simulan teclas ni se cambia el bloqueo de foco para forzarlo. No afirmar
  éxito visual de esas tomas inexistentes; v3 anterior sigue siendo prueba de
  las llamadas Win32 básicas, no del hash final completo.
- Hashes finales: helper `e3014fbc7950964d…`, grabador `4568d18757d09cec…`,
  test helper `006bc045ce118333…`, test grabador `f31c7b85e17baea8…`.
  Caso de uso común para cualquier grabador: `with RecordingWindow(hwnd,pid)
  as window:` iniciar captura; `window.check()` durante captura/cierre;
  terminar y esperar FFmpeg antes de salir del contexto. No pin de todo el
  escritorio ni de toda una partida. El grabador BAG2 conserva búsqueda por
  ruta del ejecutable solicitado (`--game-dir` configurable, experimental
  predeterminado), no por títulos.
- Prueba de integración en curso: `gaso-pinned-reuse-heat-bag1`, mismo exe11102F81
  y calibración ya revisada; sin rebuild ni copia de runtime. No modelos GPU
  simultáneos. Herramientas locales usadas donde aportan prueba (Win32/FFmpeg),
  no modelos locales para decidir identidades/restauración de ventanas.
- Integración `20261112T172244916529Z-gaso-pinned-reuse-heat-bag1`: falló al
  arrancar la captura por «lost foreground», sin crear vídeo; no aceptada.
  Salió sin dejar proceso BAG2JP, ajustes B41A5FC8/EAAF722E/EE35AB92 restaurados,
  69 saves originales verificados por el harness. No era fallo del ataque.
- Refinamiento acorde a **Always on Top de PowerToys**: foco de teclado no es
  visibilidad. Windows puede negarlo mientras permite una ventana topmost
  descubierta. Se pide foco una sola vez y se registra `focus_acquired`; no se
  exige apropiarse continuamente del teclado. Identidad-cookie, topmost,
  geometría fija y ausencia de solapamientos siguen siendo obligatorios; no se
  tolera grabar una ventana cubierta. Esto sustituye la condición de foco estricto
  de los ensayos anteriores, sin bypass de bloqueo ni teclas simuladas.
- Prueba final Win32 `window-focus-native-v6/report.json`: focus_acquired=false,
 10 checks,guard passed=true,topmost_restored=true,previous_foreground_restored=true.
  Captura3,184s; `visible.png` a1s inspeccionado y muestra la ventana verde correcta.
  Código5 interno sigue siendo esperado por ausencia de reloj/audio de juego en
  este ensayo de herramienta. La aplicación ajena conserva el foco de teclado.
- Fuente final helper `42e6c1d9979731bc…`, grabador `7c783595b1fafbd8…`;
  test helper `d75816b501d09f68…`, test grabador `f31c7b85e17baea8…`.
  Tests31/31 exit0/4,630s (`window-topmost-verified.log`), mutaciones7/7 exit0
  (`window-topmost-mutations.log`). Triaje durable Goldfish en
  `_work/goldfish/recording-window-focus-verdict.json` (no nueva aceptación del owner).
  Ensayo real nuevo en curso: `gaso-topmost-reuse-heat-bag1`, mismo runtime/calibración.
- **Ensayo real `gaso-topmost-reuse-heat-bag1` completado y ACEPTADO**:
  `py -3.13 tools/test/bag2_record.py finalize --tag gaso-topmost-reuse-heat-bag1`
  → `ACCEPTED`, exit0 (`_work/gaso/topmost-finalize.log`). `window_guard`
  (`session.json`) `passed=true, checks=157, focus_acquired=false, pending=false,
  error=null, restore_error=null`, `recording_state=closed`,
  `capture_error` ausente. Es decir, el guard genérico funcionó de extremo a
  extremo **en una partida real**: mantuvo la ventana seleccionada al frente sin
  foco de teclado, no detectó oclusión/movimiento y restauró el estado.
- Owner solicitó (2026-11-12) que la protección sirva para «todas las ventanas
  que necesites grabar»; el helper es HWND/PID explícito y el grabador BAG2 lo
  usa alrededor de FFmpeg. Confirmado que no tocó ventanas no seleccionadas y que
  dejó `BAG2JP_processes=0` al terminar.
- Medición de esta sesión de grabación: `elapsed_seconds` del run 278,778 s
  (incluye navegación, calibración de menús y captura de la partida). Ahorro/tiempo
  manual no medido; no se afirma ninguna cifra no instrumentada.

## 2026-11-13 - caught-tank-liquid: tomas del interior translúcido

- Propósito: validar en partida el nuevo render del tanque (cristal, burbujas, color).
- Comandos: `_work/gaso/run_clean_trace_session.py --action probe --temporary-controls --tag gaso-liquid{2..6}-calibration`,
  `accept_versus_calibration.py`, `_work/gaso/run_recorded_retire.py --tag gaso-liquid{2,3,4,5,5b,6}-heat-bag1 ... --stage GasOBAG1`,
  `tools/test/bag2_record.py finalize --tag <tag>`.
- Resultados: liquid2, liquid3, liquid5b y liquid6 ACCEPTED; liquid4 REJECTED (jitter p99 29,6 ms, audio 43485 Hz,
  9099 pares fuera); liquid5 REJECTED (1 parón, 2158 pares >100 ms). Repetir la misma build (5b) bastó; causa
  probable carga externa, no medida. Toma final `gaso-liquid6-heat-bag1`: 1704 latidos, 0 parones, 0 pares
  descartados, jitter p99 12,8 ms, residual p99 16,9 ms.
- Validación independiente: revisión de fotogramas (ffmpeg-skill) y mediana de color frente a BAG1.
- Resultado: útil; el guard de rechazo evitó usar dos tomas defectuosas. Cada ciclo build+calibración+toma
  ~8-10 min medidos por los logs (calibración ~90 s, toma ~297 s). Ahorro no medido.

## 2026-11-13 - liquid7/7b/7c: tanque más alto y burbujas tenues

- Propósito: comparar escala24/26 y anillos68/0x3c3430/80% con BAG1.
  Runtime exp-8mb SHAca4a31c69dea1359b525a04bd40d70381bb8335897af53f607f514173915cfb6;
  región JP. Helper existente `run_recorded_retire.py` y `bag2_record.py` sin cambios.
- Comando: `py -3.13 _work/gaso/run_recorded_retire.py --action run --tag
  gaso-liquid7{,b,c}-heat-bag1 --audio-dump --temporary-controls --p1-character
  Gas-O --p1-version BAG1 --p1-costume A --p2-character Heat --p2-version BAG1
  --p2-costume A --stage GasOBAG1 --finish`; después `bag2_record.py finalize
  --tag <tag>`. Calibración previa20261113T033425778903Z revisada y aceptada.
- Resultados preservados:7 REJECTED (audio419 pares, ventana98ms,1 parón);
  7b REJECTED (invalid window Z order al cerrar y FFmpeg sin cierre limpio);
  7c ACCEPTED1707 latidos/0 descartados/0 parones, jitter p9912,1ms,
  audio residual p9915,94ms/ventana7,88ms. PowerShell falló al resumir7b con
  Substring sobre ErrorRecord; se leyó el manifest, no se reinterpretó como éxito.
- Contraste: revisión visual de onset/cut mediante hojas FFmpeg: proporciones
  más próximas, corte limpio, burbujas aún ovaladas y borde más definido que
  BAG1. La aceptación del manifest certifica captura, no fidelidad ni owner.
- Resultado: útil para rechazar dos capturas y conservar una válida. Primera
  ejecución297,087s; tiempo total/retrabajo/ahorro no medidos. En la continuación
  de diagnóstico no se ejecutó partida nueva; próxima corrección primero host.

## 2026-11-13 - bubble-aspect: toma16:9 aceptada,4:3 rechazada

- Propósito: verificar burbujas y proporciones tras compensación dinámica,
  autorización del owner «continua» a pregunta explícita. JP/exp-8mb752e21f0…,
  vídeo/audio exactos del mismo proceso. Comando ya verificado:
  `py -3.13 _work/gaso/run_recorded_retire.py --action run --tag
  gaso-bubble-aspect-heat-bag1 --audio-dump --temporary-controls --p1-character
  Gas-O --p1-version BAG1 --p1-costume A --p2-character Heat --p2-version BAG1
  --p2-costume A --stage GasOBAG1 --finish`; luego finalize --tag. Guard0 fuente.
- 16:9 ACCEPTED1705latidos/1late/1stall68ms trasgf12012, audio0 descartados,
  residual16,31ms/ventana6,72ms. SHA review24efff99…/owner837e4190… en manifest.
  No falsear como captura sin pausas. Fuera de ataques, el parón no invalidó gates.
- Nativo4:3 wrapper `run_recorded_native43.py`, mismos args y tags
  gaso-bubble-aspect-native43{,b}-heat-bag1; deshabilita temporalmente feature
  widescreen dentro de IsolatedFiles, sin tocar permanentemente settings/cards.
  REJECTED:2557 pares/ventana102,66ms/parón322ms;1129 pares/parones337+43ms.
  Gates respetados, ambas tomas preservadas; causa de pausas desconocida.
- Revisión independiente: FFmpeg/frames, dos cortes limpios, selector en170s.
  Borde aún más nítido que BAG1; no hay aceptación4:3 ni conformidad humana.
  5 archivos protegidos iguales a predeploy y hashes de saves originales
  verificados por harness en3runs. Calibración nueva065139538691Z aceptada;
  064802635528Z fue del exe viejo tras deploy bloqueado, no aceptada/reutilizada.
- Resultado: útil, aceptación parcial16:9. Detalles/tiempos de ejecución en
  versus-runs/*gaso-bubble-aspect*/result.json; manual/ahorro no medidos.
  Próximo: conformidad visual16:9;4:3 requiere investigar captura, no relajar gates.

## 2026-11-13 - liquid-additive: dos tomas rechazadas por parón preexistente

- Propósito: validar el líquido aditivo (exe 7dfebd76) en exp-8mb con permiso
  del owner. Mismo comando `run_recorded_retire.py` (Gas-O/Heat BAG1 A,
  GasOBAG1, --finish), tags gaso-liquid-additive{,-b}-heat-bag1, y luego finalize.
- Resultado: REJECTED las dos. 989/1169 pares descartados; parones de 301ms
  (gf7992) y 253ms (gf16026). Gates sin relajar.
- Investigación: el heartbeat muestra un hueco en tiempo real con los fotogramas
  del trace continuos. Las capturas del arnés no coinciden con los parones.
  Manifests desde liquid4: parones ≥200ms en ~7968-7998 y ~12006-12012 con
  varios exes. Causa no confirmada; la hipótesis es el seek FLAC de b1m_filter.
- Resultado útil: descarta el cambio como causa y acota los puntos del parón.
  Tiempo y ahorro no medidos. Siguiente: diagnóstico del parón o una toma nueva,
  según decida el owner.

## 2026-11-13 rival hold: diagnóstico rechazado y candidato aceptado

- Exe23015cb8: `run_recorded_retire.py ... --tag gaso-slide-diag-heat-bag1
  --watch-extra <14 campos> --finish --audio-dump ...`, finalize5, RECHAZADO:
  jitter p99 24,4ms y ventana audio64ms. No cuenta como validación; watch RAM
  acota deriva f7593..8008. Error inicial de alineación songclock/global f
  corregido en `heat-table-f.txt`. No se relajan gates.
- Exe5ab1082e: misma ruta segura taggaso-caught-hold-heat-bag1, 16 extras/32
  watches, finalize0/manifest accepted=true. 1706 latidos,3 tardíos,p99 14ms,
  1 stall42ms, cero pares audio descartados. Eventos/fotogramas revisados: spawn
  f7244/7448, corte f7383 y salida f7664/7678. Selector170s/restauración145 saves.
- Resultado útil parcial: deriva acumulativa eliminada, raíz estabilizada en
  X503/505 tras entrada513. No inmovilidad exacta ni aprobación del owner.
  Evidencia `_work/gaso/slide/hold-runtime-summary.json` y cinco hojas de frames.
  Tiempo/ahorro no medidos; latencia visual aún sin calibrar.

## 2026-11-13 clamp sin pin: episodios de captura

- Wrapper seguro taggaso-clamp-last-heat-bag1,16extras/32watches,exe e165817c.
  Finalize0/accepted=true:1706latidos/1tardío/p99 13,4ms/0stalls/0pares audio
  descartados. Sin cambios a gates. Watch: raíz511/100 y luego507/103 tras
  re-hit; no oscilación periódica, sí salto entre golpes. Primer helper confundió
  entrada explícita y bucle; reporte separa episodios y conserva rangos completos.
- Cinco secuencias17frames revisadas, slot90/tanque fuera~10,006s/selector170s.
  Ajustes/149saves restaurados,5hashes iguales. Evidencia en `_work/gaso/slide/`
  y `_work/recordings/gaso-clamp-last-heat-bag1`. Útil parcial, no inmovilidad
  exacta ni conformidad. Tiempo/ahorro desconocidos, latencia sin calibrar.

## 2026-11-13 re-hit modo0 (tres corridas)

- `bag2_record.py record` lanzado al inicio de la corrida: (1) RECHAZADA, el
  harness cerró el juego antes del STOP (`capture window identity changed`);
  (2) RECHAZADA a ~94s por orden Z durante la navegación de menús.
- Corrección: `_work/gaso/slide/stop_on_selector.ps1` inicia el grabador 15s
  tras `stage-selected.png` y crea STOP al aparecer `returned-selector.png`.
  (3) `gaso-rehit-mode0-heat-bag1-r3` ACEPTADA: 1595 latidos, 0 parones, 0 pares
  descartados, p99 12,4ms. `frames --frame 7430/7645` útiles para la revisión.
- Resultado: útil; el procedimiento con watcher es reutilizable. Tiempo de
  las dos tomas fallidas ~10 min de partida perdidos. Próximo: considerar
  integrar el arranque/STOP en versus_session si se repite.
## 2026-11-13 - Toma combinada A-E/F (`gaso-combined-ae-f` y `f2`)

- Propósito: validar en juego el build combinado A-E (`exe 3519b5ad`, payload `c2129468`)
  con `GASO_CAUGHT_CLIP_PUBLISHED=1` experimental.
- Comandos: `_work/gaso/slide/stop_on_selector.ps1 -Tag <tag> -StartDelaySeconds 2 -TimeoutSeconds 600`
  + `versus_session.py --action run --tag <tag> --p1-character Gas-O --p1-version BAG1 --p1-costume A
  --p2-character Heat --p2-version BAG1 --p2-costume A --stage GasOBAG1 --temporary-controls
  --audio-dump --finish --finish-timeout 420 --watch-extra ...` con `BAG2JP_TEST_GASO_ATTACK='1'`,
  seguido de `py -3.13 tools/test/bag2_record.py finalize --tag <tag>` y `frames --tag <tag>`.
- Corrida 1 (`gaso-combined-ae-f`, 303.655 s): RECHAZADA por `finalize` (salida 1) debido a
  1 stall de 0.202 s en `gf=16008` que desplazó los pares posteriores (`residual_p99_ms=158.85`,
  `window_max_ms=158.68`, `rate_hz=44040`). Se conservó solo para diagnóstico.
- Corrida 2 (`gaso-combined-ae-f2`, 302.383 s, `restoration.verified: true`, 150 saves):
  **ACCEPTED** (salida 0): 1923 latidos (`gf=6150..17682`, 5 tardíos, jitter p99 14.72 ms,
  59.944 fps, 1 stall menor de 0.125 s tras `gf=16014`), `window_guard.passed: true` (202 checks),
  audio 44056 Hz / 11515 pares / 8 descartados / `residual_p99_ms=17.07 ms` / `window_max_ms=12.6 ms`.
- Contraste independiente: `bag2_report.py` (`cues phase 0: 0x6906x2 0x690ax3`, Fever 1, atexit),
  `bag2jp_watch.log` (B1ST, niveles 0->1->2, ventilador 0->0x80->0x200) y hojas `frames`.
- Resultado: útil; la puerta rechazó una corrida con deriva de 200 ms y aceptó la repetición
  sincronizada. Latencia de pantalla (±2 fotogramas estimados) sin calibrar y calidad subjetiva
  de audio pendiente del propietario. Tiempo manual/ahorro no medidos.

## 2026-11-13 - Toma scale32+HUD (`gaso-scale32-hud-autoplay`)

- Propósito: validar escala de mundo del escenario (stage197 `b663417f`), etiqueta GAS-O y
  partida autoplay sin ataques (exe `c391f357`, payload `847058c4`), sin fixture de ataque.
- Comandos: calibración `versus_session.py --action probe --temporary-controls --tag
  gaso-scale32-hud-calibration` + `accept_versus_calibration.py --run ...`; watcher
  `stop_on_selector.ps1 -Tag gaso-scale32-hud-autoplay -StartDelaySeconds 2 -TimeoutSeconds 1200`;
  `versus_session.py --action run ... --stage GasOBAG1 --temporary-controls --audio-dump --finish
  --finish-timeout 420`; `bag2_record.py finalize --tag gaso-scale32-hud-autoplay`.
- Resultado de captura: **ACCEPTED** (salida 0), 1954 latidos `gf=6366..18084`, 4 tardíos,
  jitter p99 14.84 ms, stalls 0.135 s tras gf11166 y 0.073 s tras gf15006; restauración
  verificada (150 saves).
- Revisión: sin ataques PASA (0 cues tanque, 0 `request 202`); intro PASA visualmente con
  reserva; etiqueta HUD FALLA (P1 sin etiqueta). La grabación permitió localizar un fallo
  que los tests host no veían (sitio de instrucción del exe principal no optado).
- Resultado: útil. Una primera ejecución falló antes de jugar por calibración caducada
  (catálogo ligado al hash del exe): hubo que recalibrar. Tiempo manual no medido.

## 2026-11-14 - Toma 4 aceptada (`gaso-latch-site-autoplay4`)
- Tomas 1-3 rechazadas (colocación de audio por pausas de host de 0.3 s y `invalid window Z order`);
  causa: el juego del propietario "Watcher of Realms" en primer plano (diagnóstico
  `_work/gaso/slide/zorder_log.py`). Tras cerrarlo, toma 4 aceptada: 1916 latidos, 0 pares
  descartados, residuo p99 17.97 ms.
- Revisión: etiqueta GAS-O PASA, sin ataques PASA, intro PASA con reserva; deriva lateral de
  bailarines BAG1 observada (`_work/gaso/drift/drift-sheet.jpg`).
- Resultado: útil; lección: revisar aplicaciones en primer plano antes de grabar.

## 20261114-bag2-record-leash-release-review — 2026-11-14 UTC — radio BAG1 y liberación nativa
- Tipo: uso real de captura previa/finalización; no nueva partida. Python3.13, herramienta canónica `tools/test/bag2_record.py`.
- Comando: `py -3.13 tools/test/bag2_record.py finalize --tag bag1-leash-autoplay`, exit1. Watcher terminó exit0; run300.244s, restauración verificada150 saves/configs.
- Entrada exe `167688927edddccc45749b46c9259b94e4601e092756307d9d7aa36d4c4594e5`; salida `_work/recordings/bag1-leash-autoplay/manifest.json` SHA-256 `9fbbd50ab5912e588de2871a45901c60da266ff31f5daad1a4019d8626246bce`.
- Resultado RECHAZADO: audio ventana1s desviada17.04ms (>1frame), 12pares descartados; pausa0.125s. Guardia de ventana válida, pero accepted=false prevalece. Sin bypass ni segunda finalización.
- Contraste: `_work/gaso/drift/leash-watch-summary.json` `25fef92d1a22c83441cdefe5386ed63cdb8226d9e6fa544790d54d06f440b49f` demuestra valores de RAM, NO raíz/posición visual. Manifest conserva hashes de raw/review/owner/events.
- Dictamen: útil para rechazar evidencia no admisible, no validación del ajuste. No nueva captura/`bag2_shots`: falta autorización para otra partida.
- Medición: run300.244s; finalización/preparación/revisión no medidas; ahorro no medido.
- Siguiente: nueva toma autorizada con candidato corregido; conservar rechazo y no pedir conformidad visual sin evidencia válida.

## 20261114-bag2-record-release-accepted — 2026-11-14 UTC — toma bag1-release-autoplay aceptada
- Tipo: uso real de captura y finalización; Python3.13, herramienta canónica `tools/test/bag2_record.py`, skill `bag2-game-recording`.
- Comandos: watcher `_work/gaso/slide/stop_on_selector.ps1 -Tag bag1-release-autoplay -StartDelaySeconds 2`;
  `finalize --tag bag1-release-autoplay` exit0; `frames --tag bag1-release-autoplay --frame 15681 --span 12 --step 2`
  y `--frame 6560 --span 10 --step 2`.
- Entrada: runtime `3b43cff82d073ce2c7a29ecc377520c886e3d5d84ad258e2967bfc7427d9c89f`; run
  `_work/versus-runs/20261114T060817268486Z-bag1-release-autoplay` (301.407 s, restauración 150 saves verificada).
- Salida: `_work/recordings/bag1-release-autoplay/manifest.json` SHA-256 `dbe17f12…`, `raw.mkv` SHA-256 `94204911…`.
- Resultado ACEPTADO: `accepted=true`, 0 rechazos, 1930 heartbeats (1 perdido), jitter p99 12.8 ms,
  59.939 fps, 0 stalls, audio residual p99 15.74 ms y ventana máxima 9.51 ms.
- Contraste: 24 PNG extraídos alrededor de gf15681 (liberación nativa) y gf6560 (intro) revisados
  visualmente; eventos `events.json` mapean gf6580 a 8.446 s. La aceptación del grabador no otorga
  aceptación visual por sí sola; la revisión de separación/liberación/fin/selector fue propia.
- Dictamen: útil y suficiente como puerta de evidencia; sin bypass, sin repetición para eludir gates.
- Medición: partida 301.407 s; finalización y extracción no medidas; ahorro no medido.
- Límites: ±2 fotogramas por latencia de pantalla sin calibrar; audio subjetivo requiere escucha humana.
- Siguiente: pedir solo conformidad del owner; no nueva toma sin autorización y no commit.

## 20261114-bag2-record-center-calibration — 2026-11-14 UTC — calibración del recentrado
- Tipo: uso real autorizado; Python3.13 y `tools/test/bag2_record.py`.
- Comandos: wrapper `_work/gaso/drift/end-center/run_recorded_candidate.py --action probe --tag bag1-center-calibration --temporary-controls --audio-dump`; `finalize --tag bag1-center-calibration`, exit0.
- Entrada: runtime `893833b178d9bf96183bfc398a35eb1ac7d429ab2046ef2fcebea8ff9e1cda19`, JP;
  run `_work/versus-runs/20261114T072555505757Z-bag1-center-calibration`.
- Resultado: manifest `accepted=true`, 597 heartbeats, nueve tardíos/perdidos, un stall60ms,
  jitter p99 11.6ms, 59.936fps, audio residual p99 15.25ms/ventana máxima2.34ms.
- Evidencia: `_work/recordings/bag1-center-calibration/manifest.json`; hashes de salidas en manifiesto.
- Contraste: video y diez capturas revisados; ocho transiciones del catálogo correctas y aceptadas;
  restauración de 150 saves verificada. No prueba recentrado en partida.
- Dictamen: útil para la puerta de calibración; sin bypass. Ejecución110.902s;
  finalización/revisión y ahorro no medidos. Precisión visual ±2frames estimada; audio subjetivo humano.
- Siguiente: esperar finalización de la única partida autorizada `bag1-center-autoplay`.

## 20261114-bag2-record-center-rejected — 2026-11-14 UTC — partida y audio discontinuo en reloj real
- Tipo: uso real autorizado; mismo runtime893833b1 JP; wrapper `run_recorded_candidate.py`
  `--action run --tag bag1-center-autoplay --temporary-controls --audio-dump` Gas-O/Heat BAG1A,
  GasOBAG1, `--finish --finish-timeout 420`, watches de homes/radios/controladores.
- Partida304.363s completada, configuraciones y150saves restaurados/verificados; run
  `_work/versus-runs/20261114T072915522621Z-bag1-center-autoplay`.
- Comando `py -3.13 tools/test/bag2_record.py finalize --tag bag1-center-autoplay` ejecutado una vez:
  exit1, `accepted=false`,4213/10245pares fuera100ms, ventana17.92ms;1710heartbeats,
  jitterp9915.42ms/59.943fps y stall0.408s trasgf16008. Ventana guardpassed/FFmpegexit0
  no compensan el rechazo de audio.
- Evidencia: manifiesto `_work/recordings/bag1-center-autoplay/manifest.json`, syncSHA
  `ab6ca73c0f12543fafc4c8c29661b8c77df5a0d2ed2f97a34fb43040cca7fadd`, rawSHA
  `6dee18d2b53c72113ac49570449409b34bd07a9e6d5db1ac551d80a355d9ac2a`.
- Contraste independiente: contador audio/frame continuo, offset wall/frame salta0.429s;
  reporte `_work/gaso/drift/end-center/rejected-capture-diagnostic.json`.
- Dictamen: útil como puerta de rechazo; causa del stall no establecida. No validación
  visual ni bypass/recorte/re-finalización. Diagnóstico/finalización/ahorro no medidos.
- Siguiente: pedir permiso de nueva toma; no repetir sin autorización, no commit/snapshot.

## 20261114-bag2-record-center-retry-rejected — 2026-11-14 UTC — repetición autorizada
- Tipo: uso real autorizado por «Si autorizo continua»; mismo runtime JP
  `893833b178d9bf96183bfc398a35eb1ac7d429ab2046ef2fcebea8ff9e1cda19`, sin ataques.
- Comando: `py -3.13 _work/gaso/drift/end-center/run_recorded_candidate.py --action run --tag bag1-center-autoplay-r2 --temporary-controls --audio-dump --p1-character Gas-O --p1-version BAG1 --p1-costume A --p2-character Heat --p2-version BAG1 --p2-costume A --stage GasOBAG1 --finish --finish-timeout 420 --watch-extra 8005F848:4,8005F858:4,8005F8E0:4,8005F8F0:4,8005F820:4,8005F8B8:4,8005F82C:4,8005F8C4:4`.
- Resultado: partida304.098s, restauración de150saves/configuraciones verificada; run
  `_work/versus-runs/20261114T075559301619Z-bag1-center-autoplay-r2`.
- `py -3.13 tools/test/bag2_record.py finalize --tag bag1-center-autoplay-r2` una vez:
  exit1/accepted=false;2719/10023pares audio fuera100ms, residualp9917.09ms,
  ventana7.74ms;1677heartbeats/6tardíos,59.945fps,jitterp9915.43ms,stall0.343s trasgf16014.
- Evidencia: `_work/recordings/bag1-center-autoplay-r2/manifest.json`, syncSHA
  `522a8179281bfc65f0e446bd260e8ec3925a248150470695fe7c86693b1db107`, rawSHA
  `72842f5e5abb5d06e7b668a3b33619fe9935f8f043406ba810e0d4f383a27884`.
- Contraste independiente: medianas wall/frame antes/después del stall difieren0.336s;
  sin saltos de muestras>2205 en frames consecutivos; hashes estable/experimental y
  restauración en `_work/gaso/drift/end-center/retry-rejected-diagnostic.json`.
- Dictamen: útil como puerta de rechazo; causa concreta sin establecer. Sin inspección
  visual para aceptación, bypass, reparación, recorte ni nueva finalización/partida.
  No se repitió FFmpeg visual sobre evidencia no aceptada. Finalización/revisión/ahorro no medidos.
- Siguiente: diagnosticar discontinuidad con ambas tomas antes de otra prueba autorizada.

## 20261114-bag2-record-clock-replay — 2026-11-14 UTC — detector y relojes
- Tipo: diagnóstico interno de solo lectura; no nueva captura ni finalización.
- Comando: `py -3.13 _work/gaso/drift/end-center/replay_capture_clock.py`.
  Usa `HeartbeatClock`, `parse_sync_log`, `audio_placement` y `MAX_AUDIO_DROPPED`
  del recorder actual; entradas calibración y ambas tomas JP893833b1 ya registradas arriba.
- Resultado: conteos exactos0/3553,4213/10245 y2719/10023; control sintético sin salto pasa,
  con0.343/0.408s de salto wall y muestras continuas falla la puerta original.
  Se conservan hashes sync, latidos, fases nativas y lecturas independientes en
  `_work/gaso/drift/end-center/capture-clock-replay.json`.
- Contraste: el productor `bag2jp_anim_trace.c` registra frame/muestras sin walltime;
  `HeartbeatClock` conserva el salto wall y el ajuste de audio es único/afín.
  r2 incluye otra lectura de proceso con el mismogf16014 dentro del hueco. Los saltos
  ocurren después de fase4, fuera de la elegibilidad del recentrado. No hay timestamp
  monotónico del productor que discrimine pausa real frente a salto del reloj compartido.
- Intento inicial: faltaba archivo de muestras en calibración; diagnóstico falló antes
  de producir reporte. Se hizo opcional solo ese input ajeno al detector; replay final pasa.
- Dictamen: útil para confirmar mecanismo de rechazo, inconcluso sobre origen del stall.
  No corrupción PCM demostrada, aceptación visual, reparación, bypass ni partida nueva.
  Tiempo de ejecución/retrabajo/ahorro no medido. Siguiente: contrato monotónico host.

## 20261114-bag2-record-clock-probe-host — 2026-11-14 UTC — diagnóstico monotónico adicional
- Tipo: implementación y ensayo host; no grabación, despliegue ni nueva finalización.
- Entradas: recorder SHA-256 `7df2fcf10bb50650ca222aac327180915bed8963f7829dcc7543ea45fbcf57a5`;
  productor C `7d336bb51dfe402719ec5f205b8408964a6e3ec8156a95277c017eb1bea98c34`.
  Contrato SDL3 `SDL_GetPerformanceCounter/Frequency`: deltas/frecuencia, épocas opacas.
  Docs oficiales consultadas por Context7: `https://wiki.libsdl.org/SDL3/SDL_GetPerformanceCounter`
  y `https://wiki.libsdl.org/SDL3/SDL_GetPerformanceFrequency`.
- Comando host: `py -3.13 -m unittest -v tools.test.test_audio_clock_probe tools.test.test_bag2_record tools.test.test_anim_trace_samples tools.test.test_recording_window`:
  39 tests PASS10.159s. Fixture real de callbacks C conserva PCM/sync de dos columnas y
  emite pares frame/muestras/counter/frequency; fixture del loop real conserva heartbeat
  y registra brackets monotónico/civil, incluyendo frame repetido y ausente.
- RED→GREEN: al inicio faltaban ambos CSV; luego la revisión confirmó que el filtro por
  mtime civil descartaba evidencia tras retroceso y que un fallo del CSV abortaba la captura.
  Pruebas reprodujeron ambos antes de corregir. Ahora open/header/write/flush/close/copy
  diagnósticos son opcionales con advertencia; el archivo ambiguo se retiene con identidad
  inicial/final, no se declara pertenencia a sesión por copiarlo. Fallos iniciales de mocks
  de reloj/logging se aislaron en el fixture; no se relajaron aserciones de compatibilidad.
- `py -3.13 _work/gaso/drift/end-center/check_clock_probe_mutations.py`: dos baselines PASS,
  seis mutantes KILLED_ASSERTION. Fuentes copiadas; reporte `clock-probe-mutations.json`
  conserva hashes, comandos, salidas y tiempos. No cuentan fallos de compilación como kill.
- `py -3.13 _work/gaso/drift/end-center/check_clock_probe_compile.py`: C completo con comando
  real Windows/SDL3 derivado de Ninja, syntax-only PASS2.568s; sin enlace ni staging.
- Dos revisores Goldfish CON HALLAZGOS; triaje y correcciones probadas en
  `_work/goldfish/capture-clock-probe-verdict.json` y nota canónica `notes/gaso-import.md`.
  Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Dictamen: útil para verificar contrato diagnóstico/compatibilidad y fallos host. No prueba
  coherencia concurrente del contador heredado, coste de flush, efecto vivo ni origen del stall.
  Las tomas rechazadas siguen rechazadas; puertas sin cambios. Preparación/retrabajo/ahorro
  no medidos. Siguiente: compile/link con staging respaldado; juego requiere autorización.

## 20261114-bag2-record-clock-probe-build — 2026-11-14 UTC — staging y enlace de instrumentación
- Tipo: staging con respaldo y compile/link en árbol de compilación; sin despliegue, sin partida, sin commit, sin snapshot.
- Entradas: productor C `7d336bb51dfe402719ec5f205b8408964a6e3ec8156a95277c017eb1bea98c34`; recorder host (sin compilación) `7df2fcf10bb50650ca222aac327180915bed8963f7829dcc7543ea45fbcf57a5`.
- Comando: `py -3.13 tools/workflow/bag2_workflow.py build --tag clock-probe-staging` (preflight + build, dos jobs implícitos).
- Respaldo previo: `_work/gaso/drift/end-center/staging-backup/20261114T084258Z/bag2jp_anim_trace.c` (sha previo `caf3e7fff5dfc01dce68b9aaf9ffb936220569700176c9a96996ce4404976a91`).
- Staging: `mods-src/bag2jp.debug.anim-trace/bag2jp_anim_trace.c` → build `src/bag2jp_anim_trace.c`, `match: true` (sha `7d336bb5…`). Informe `staging-report.json`.
- Resultado: preflight passed (sources matching 47; `sources.different` solo `bag2jp_gaso_caught.c`, ajeno); build `returncode 0`, `[5/5] Linking CXX executable BAG2JP.exe`, 33.144s; solo advertencia `-Wa,-mbig-obj` no usada. Log: `_work/workflow/20261114T084307508491Z-clock-probe-staging/build.log`.
- Dictamen: fuente vinculada en build tree (`linked=true`), no desplegado (`deployed=false`), no probado en juego (`live_validated=false`). Puertas de aceptación sin cambios; grabaciones previas siguen rechazadas. Despliegue y partida diagnóstica requieren autorización del owner.

## 20261114-bag2-record-clock-probe-autoplay — 2026-11-14 UTC — sonda viva en juego (gdigrab)
- Tipo: prueba grabada autorizada en experimental `2135d5eb6ef70755c2272c32057ad2c58bf3e2cf47c5aca45db142f8be59a780` (`_work/versus-runs/20261114T100637319588Z-clock-probe-autoplay`, 295.946 s); 150 saves/configs restaurados.
- Resultado: **RECHAZADA** (`accepted: false`): `1874/7595` pares de audio > 100 ms, ventana 1 s `119 ms`, y `capture: invalid window Z order` a ~127.5 s (`stalls: [{after_frame: 12006, wall: 1794650999.355674, seconds: 0.292}]`).
- Discriminación (`_work/gaso/drift/end-center/clock-probe-autoplay-analysis.json`): `clock_observations.csv` mostró `wall_minus_mono_rel_ms` dentro de `[-0.0015, +0.2891] ms` (sin salto del reloj civil), mientras `bag2jp_clock_probe.csv` midió una pausa real del productor de `393.01 ms` entre `gf 12006` y `12012` (`4409` muestras ≈ 100 ms) en `mode2 phase 1/3/3 fever0`. Queda descartado un salto del reloj del sistema y un efecto del recentrado/fever en ese hueco.

## 20261114-bag2-record-wgc-integration — 2026-11-14 UTC — integración WGC (gfxcapture) y Bloque 1 en juego
- Tipo: integración de backend `wgc` (`D:\Dev\Tools\ffmpeg-wgc\ffmpeg-n8.1-latest-win64-gpl-8.1\bin\ffmpeg.exe`), pruebas host, E2E sintético ocluso y partida grabada en juego (`wgc-center-autoplay`).
- Cambios: `tools/test/bag2_record.py` (`3f3f9ebc…`), `tools/test/recording_window.py` (`27fe3c09…`), `tools/test/test_bag2_record.py` (`7a991287…`), `tools/test/test_recording_window.py` (`3324eede…`). Puertas de alineación y `gdigrab` sin cambios.
- Host y Goldfish: `py -3.13 -m unittest -v tools.test.test_recording_window tools.test.test_bag2_record tools.test.test_audio_clock_probe tools.test.test_anim_trace_samples` → 45 tests PASS `7.162 s`; E2E sintético ocluso `accepted: true` (`_work/gaso/drift/end-center/wgc-e2e-smoke/`); dos revisores Goldfish `SIN HALLAZGOS BLOQUEANTES` (`_work/goldfish/wgc-capture-integration-verdict.json`). Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
- Partida real Bloque 1 (`_work/versus-runs/20261114T104433736313Z-wgc-center-autoplay`, 299.291 s, 150 saves/configs restaurados): `finalize --tag wgc-center-autoplay` **ACEPTADA** (exit 0, `accepted: true`, 0 rechazos): `1675` heartbeats (`0` perdidos), `jitter p99: 10.9 ms`, `59.942 fps`, `0` stalls, `10011` pares de audio (`0` descartes, `44057 Hz`, residual p99 `15.47 ms`, ventana `6.34 ms`), `window_guard` (`checks: 175`, `require_uncovered: false`, `passed: true`), `bag2jp_clock_probe.csv` max `112.127 ms` (sin pausas), `loudness.py` `-15.3 LUFS` / `-1.1 dBTP`.
- Dictamen: WGC + relojes verificados en juego real sobre `BAG2JP.exe`; centrado final, radio `318`, liberación `0x7FFFFFFF`, solo fever P2 y vuelta al selector revisados. Tiempo/ahorro no medidos. Siguiente: conformidad visual del owner y Bloque 2 (ataques/`CAUGHT`/dueto) con autorización.

## 20261114-bag2-record-clock-probe-live — 2026-11-14 UTC — captura real en exp y causa del stall
- Tipo: despliegue EXE-only autorizado («Continua») en `BAG2JP-exp-8mb`, calibración y una partida grabada sin ataques (`bag2_record.py` con `gdigrab`), más re-establecimiento de Ghidra MCP.
- Despliegue: `deploy_verified_exe.py --tag clock-probe --preserve-canonical-feature-manifest`: `893833b1…` → `2135d5eb6ef70755c2272c32057ad2c58bf3e2cf47c5aca45db142f8be59a780`, respaldo en `_work/gaso/deployment-backup-clock-probe/report.json`; estable `5612f03a…` intacto.
- Calibración `clock-probe-calibration` (`20261114T095200987521Z-clock-probe-calibration`, 106.143 s): 150 saves/configs restaurados; catálogo visualmente revisado y ligado (`reviewed_catalog_sha256: 790f91c6…`). El video de calibración fue **RECHAZADO** por `heartbeat jitter p99 22.7 ms > 1 frame` (audio pasó con 0 descartes).
- Partida `clock-probe-autoplay` (`20261114T100637319588Z-clock-probe-autoplay`, 295.946 s): 150 saves/configs restaurados; grabación **RECHAZADA** por `1874/7595` pares de audio >100 ms, ventana 1 s de `119 ms` y `capture: invalid window Z order` a los ~127.5 s (`stalls: [{after_frame: 12006, seconds: 0.292}]`).
- Análisis (`analyze_clock_probe_autoplay.py` → `_work/gaso/drift/end-center/clock-probe-autoplay-analysis.json`): `wall_minus_mono_rel_ms` en `clock_observations.csv` se mantuvo en `[-0.0015, +0.2891] ms` (24 686 muestras, sin salto del reloj civil), mientras `bag2jp_clock_probe.csv` midió una pausa real del productor/emulación de **393.01 ms** entre `gf 12006` y `gf 12012` (`ds = 4409` muestras ≈ 100 ms), en `mode2 phase 1/3/3 fever0` (antes de fever y del recentrado `phase 1/4 clip 68`). Causa raíz del fallo de audio probada: pausa real del productor, no salto del reloj del sistema.

## 20261114-bag2-record-wgc-integration — 2026-11-14 UTC — captura WGC tolerante a ventanas encima
- Tipo: descarga e integración de FFmpeg 8.1 (`n8.1.3-35-gf1acb0a266-20261113`) con filtro `gfxcapture` (`Windows.Graphics.Capture`) en `tools/test/bag2_record.py` y `tools/test/recording_window.py`; pruebas host + E2E con ventana ocluida + 2 revisiones Goldfish.
- Binario WGC instalado en `D:\Dev\Tools\ffmpeg-wgc\ffmpeg-n8.1-latest-win64-gpl-8.1\bin\ffmpeg.exe` (`D:\ffmpeg\bin\ffmpeg.exe` intacto). `--capture-backend {auto,wgc,gdigrab}` (default `auto` prefiere `wgc`, variable `BAG2JP_FFMPEG_WGC`).
- Comando WGC: `-use_wallclock_as_timestamps 1 -f lavfi -i gfxcapture=hwnd=<hwnd>:max_framerate=<fps>:capture_cursor=0 -vf hwdownload,format=bgra,crop=trunc(iw/2)*2:trunc(ih/2)*2:0:0 ...`; `parse_ffmpeg_start` acepta `gdigrab` y `lavfi` con reloj real (`>= 1.0e9`). `RecordingWindow(..., require_uncovered=False)` no fija topmost ni foco ni rechaza solapamiento o movimiento `(x, y)`, pero mantiene token `SetPropW`, dueño PID, visible, no minimizado y sin redimensionamiento.
- Pruebas host (`py -3.13 -m unittest -v tools.test.test_recording_window tools.test.test_bag2_record tools.test.test_audio_clock_probe tools.test.test_anim_trace_samples`): **45 PASS en 7.162 s** (incluidos casos RED→GREEN).
- Prueba E2E viva con ventana Win32 `320x240` totalmente tapada por `OCCLUDING_WINDOW` roja topmost (`_work/gaso/drift/end-center/wgc-e2e-smoke/`): `review_mid_wm_timer.png` mostró **`gf 253` == `E2E 253`** sin oclusión ni bordes; corrida con audio (`manifest-smoke.json`): `accepted: true`, `capture_backend: "wgc"`, `jitter_p99_ms: 4.5`, `59.923 fps`, `stalls: 0`, `audio dropped: 0`.
- Goldfish (`_work/goldfish/wgc-capture-integration-verdict.json`): dos revisores (`ses_e265f0a9effewK76LIUQpl6gqe`, `ses_e265f0a9cffepl5GdjBuDpqwK7`) **SIN HALLAZGOS BLOQUEANTES**; 3 ajustes menores aplicados y re-probados. Límite pendiente: prueba real con `BAG2JP.exe` SDL3/D3D11 bajo WGC (y la pausa periódica de ~293 ms del emulador sigue sin resolverse).

## 20261114-bag2-record-block4-selector — 2026-11-14 UTC — preview tras retorno

- Uso real autorizado; WGC y audio PCM exacto. Wrapper existente
  `run_recorded_block2.py --action probe --temporary-controls --audio-dump`
  con tags `block4-selector-cal` (23bbdabd) y `block4-consumer-cal` (e709c2f8).
  `bag2_record.py finalize --tag <tag>` una vez por captura; ambas accepted=true.
  Primera:552latidos/1stall,3293pares audio/0descartes,15.31msresiduo,2.08msventana;
  segunda:546latidos/0stalls,3247pares/0descartes,14.96msresiduo,2.53msventana.
  Nueve imágenes/bordes de cada catálogo revisadas y aceptadas por separado.
- `run_recorded_selector_return.py --action run --tag block4-selector-return
  --temporary-controls --audio-dump --p1-character gaso --p1-version BAG1
  --p2-character heat --p2-version BAG1 --stage GasOBAG1 --finish`:
  pin23bbdabd, sin fixtures,309.047s,150saves/configs restaurados. La cola de3s
  conserva retorno sin entrada de pad. Finalize accepted=true:2035latidos/4tardíos,
  1stall117ms,12163pares/8descartes,17.12msresiduo,8.95msventana.
- Dictamen: útil, **captura aceptada pero corrección funcional parcial**. FFmpeg
  detectó retrato Gas-O con nombre BI-O transitorio al retornar (gf17557), corregido
  más tarde. No ocultar esa evidencia ni tratar grabación aceptada como aprobación.
- Nuevo runtime e709c2f8 mueve hook antes del consumidor de nombre; la nueva toma
  `block4-consumer-return`:309.897s,150saves/configs restaurados; finalize una vez,
  accepted=true,sin rechazos,2033latidos/3tardíos,1stall99ms,12.06msjitter,
  59.94084Hz,12191pares audio/3descartes,16.39msresiduo,10.5msventana.
- Revisión FFmpeg: retrato y nombre GAS-O en primer selector muestreado gf17532,
  t193.400, Heat correcto y sin reabrir popup, hasta202s. `frames --frame17532
  --span18 --step1` y hoja `block4-consumer-first-name-frames.png`:37muestras sin BI-O;
  VFR puede repetir/saltar fotogramas, ±2frames estimado. Útil para el requisito;
  no valida matriz de rivales ni lifecycle CAUGHT.
- Versiones de grabador/backend conservadas de la instalación verificada. Tiempo
  de pared de cada run en result.json; ahorro y retrabajo manual no medidos.

## 20261115-bag2-record-recovery — calibración guard1 y toma save/load

- Runtime94922aba, PSXRecomp experimental JP; guard1 solo en build, canónico0.
  Grabador/backend WGC y gates sin cambios. Wrapper block2 probe con
  `--temporary-controls --audio-dump --tag block4-recovery-cal{,2}`.
- Primera calibración REJECTED:551latidos,8tardíos,jitter28.3ms>1frame,
  sin stalls, audio3301pares/0descartes/ventana1.53ms. Conservada íntegra;
  recovery-cal-clock-diagnosis.json muestra jitter también en productor.
  No atribuir causa únicamente al observador ni declarar corrección.
- Segunda calibración accepted=true:545latidos,7tardíos,jitter12.9ms,
  sin stalls,3259pares audio/0descartes/ventana1.69ms. Catálogo revisado con
  imágenes reducidas recovery-cal2-{sheet,probes}.png y helper canónico
  accept_versus_calibration.py; movimientos correctos en los ocho arcos.
  Restauración verificada en ambas:150saves y tres archivos de configuración.
- Partida block4-recovery-load iniciada con run_recorded_savestate.py
  (Gas-O/Heat BAG1 A,GasOBAG1,fixture GASO_ATTACK,fin420s). Vigila log y
  encola F7/Up/S para slot11, F7/L tras retiro; exige SAVED+fichero aislado,
  recuperación y nuevo retiro. PostMessage no es confirmación. Pendiente
  resultado/finalize/revisión; no aceptación del comportamiento todavía.
- Tiempo cal1 108.690s,cal2 103.559s según result.json; preparación/revisión
  y ahorro no medidos. Ver ledger Gas-O para resultado vivo actualizado.

### Resultado load1 y repetición load2

- load1 falló144.485s con heartbeat obsoleto: F7 pausado, trial saving, sin
  SAVED/.pst. Finalize REJECTED por shutdown inseguro/identidad de ventana al
  cerrar proceso antes del grabador; no es evidencia aceptada de recuperación.
  Reloj330latidos/0tardíos/jitter9ms/sin stalls;audio1975pares/0descartes,
  ventana4.67ms. Settings y150saves restaurados verificados por harness.
- Diagnóstico de fuente+imagen t38s: Up/S en lote inicial se descartan en
  drain_host_events, menú sigue slot01. Wrapper separa lotes con25ms y exige
  las mismas confirmaciones;3regresiones RED→GREEN(total7tests). load2 en curso,
  sin cambio EXE ni umbrales. Esperar resultado antes de aceptar comportamiento.

### load2: guardado sí realizado, acuse buffered; load3 en curso

- load2 falló146.364s por guardado no reconocido antes del retiro. Sí existe
  cards/openbios/state_80035D98_slot11.pst1958997B y .thumb49164B; stderr al
  cerrar confirma SAVED11@8008E8B4. No hubo petición load. Captura REJECTED
  por cierre/identidad de ventana; reloj456latidos/1tardío/jitter13.2ms,
  audio2731pares/0descartes/ventana5.54ms.150saves/configs restaurados.
- Fuente nativa: thumbnail PSTH128x96 se escribe solo tras boot_state_save
  exitoso. Wrapper reconoce .pst no vacío+.thumb completa con cabecera válida
  en cards inicialmente vacías, en vez de esperar stderr;10host tests OK
  después de1RED. Recorder se para antes del juego también en error.
- load3 iniciada, mismos runtime/gates/pareja/fixture. Pendiente resultado;
  no aceptación ni nueva repetición sin diagnóstico.

### load3: captura aceptada, protocolo de menú no fiable (bloqueo)

- Run147.625s falla con heartbeat obsoleto, sin SAVED/.pst. t38s muestra menú
  F7/slot01;25ms no garantiza cambio de event-drain a pause-loop. Sin load,
  recovered, nueva retirada ni fin/selector: NO aceptación del comportamiento.
- Finalize accepted=true:337latidos/1tardío,jitter11.3ms,sin stalls,
  1993pares audio/0descartes,ventana5.54ms; shutdown seguro al parar recorder
  primero. Es una captura diagnóstica aceptada, no recuperación aceptada.
-150saves/configs restaurados. Chequeo independiente final: cinco configs
  de deployment-backup iguales, sin .pst en saves originales, canónico guard0
  y EXE94922aba experimental sin cambios; no instancia activa.
- No más repetición ciega. Siguiente interno: señal verificable de menú listo,
  host regression y evaluación de alcance si exige framework. Sin ahorro medido.

## 20261115-bag2-record-native-menu-ready — ensayo de señal observable

- Owner aclaró que no quería otro sistema de guardado; se conserva el F7 nativo
  y confirmó continuar. Sin modificaciones del runtime, formatos ni grabador.
  EXE94922aba y calibracióncal2 se reutilizan sin cambios.
- Utilidades existentes: llvm-nm --defined-only del toolchain WSL registrado y
  inspect_host_symbols.read_symbols. COFF RVA+ImageBase coincide con nm para
  open141516238,slot1416566b0,paused15bdffcb0. Detalle en menu-readiness-symbols.txt
  y menu-readiness-coff-check.json; live usa módulo ASLR, no VA fija.
- main.cpp8787/freeze_heartbeat.c178: flag paused entra antes del pause-loop;
  exigir simultáneamente open excluye otras pausas. Handle existente de
  TaskRamCapture solo QUERY_INFORMATION|VM_READ, hash/PID/HWND fijados. Sin
  WriteProcessMemory. Espera condición open=paused1, luego ambos0 y slot11;
  timeout1s,poll1ms. Confirmación de guardado continúa por .pst+.thumb completa.
- Host5RED(7fallos con subcasos)→6OK0.012s; wrapper10OK0.030s. Cubren flags
  parciales/ajenos/corruptos, timeout y RVA duplicado/ausente/desalineado.
  Dictamen interno útil para eliminar sleep25ms, fiabilidad live aún no probada.
  Toma block4-recovery-ready iniciada, pendiente resultado/finalize/revisión;
  ninguna aceptación anticipada. Preparación/consulta/ahorro no medidos.

### Resultado: flujo completo, captura rechazada por paso de audio al load

- recovery-ready completó315.414s,150saves/configs restaurados; trial complete.
  Menúready tras7.480/8.075ms y closed19.437/19.017ms después(save/load).
  SAVED/LOADEDslot11, recovered side2gf8499/t43.533, retirada gf8919/t50.549,
  fin y selector root13. Es evidencia de trace, sin aceptación visual.
- Finalize REJECTED:2099latidos/7tardíos,jitter11.67ms,3stalls;
  audio12559pares/0descartes/rate44050/residuo29.86ms/ventana24.67ms>1frame.
  Los rechazos se conservan. No se hizo revisión de gameplay como aceptado.
- Replay read-only analyze_recovery_ready.py: exceso productor32.498ms y paso
  wall/audio30.704ms localizado a gf8496..8502(load); native poll23.1ms.
  Otros stalls no producen paso persistente comparable. Reloj global afín no
  representa esa carga; no resolver repitiendo igual o ampliando umbral.
- Plan propuesto pendiente plans/pending/savestate-recording-audio.md: demostrar
  offline marcadores/semántica de pausa y negativos antes de integrar soporte;
  sin inventar audio ni modificar runtime/guardados. Resultado de herramienta:
  útil para detectar límite real, no captura aceptada ni ahorro demostrado.
