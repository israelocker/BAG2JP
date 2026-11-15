---
id: tool-evidence-ffmpeg-skill
title: "Evidencias: ffmpeg-skill"
tags: ["tools", "evidence", "ffmpeg", "video", "audio"]
summary: "Historial de instalación y uso del skill FFmpeg local en BAG2JP; obligatorio cuando sea pertinente."
related: ["notes/assets.md", "AGENTS.md", "tools/ffmpeg-skill/SKILL.md"]
created: "2026-11-10"
updated: "2026-11-14"
doc_kind: evidence
---

# ffmpeg-skill - historial

## 2026-11-14 — wider-home: revisión grabada del candidato effb8edd

- Entrada: `_work/recordings/wider-home-autoplay/raw.mkv` y owner.mp4, manifest aceptado;
  runtimeeffb8edd971992655aa06ce88d05b21e65dc83b73e742265f5ebc45597612216.
  FFmpeg local2024-09-19-git-0d5b68c27c-full_build-www.gyan.dev, sin cambiar capturaWGC8.1.
- `py -3.13 _work/gaso/drift/end-center/review_wider_home_evidence.py` llama al skill
  look.py con tiempos derivados de load_clock, --no-timecode --width480 --at<T> --json-brief.
  Primer ensayo falló al ordenar un sufijo temporal negativo (heartbeat anterior al inicio
  del video); corregido el inicio a t>=0.15s y ordenado por tiempo numérico. Segundo intento
  exit0,19.42s. Originales intactos; --overwrite solo en PNG de este ensayo propio.
- Vistas las cuatro hojas: overview,13 frames iniciales gf7123..7135,13 de cierre
  gf15360..15372 y13 de fase liberada gf15606..15618. Hoja compacta owner añade selector.
  Confirma separación mayor/retorno final suave, pero Heat empieza aún hacia dentro de la
  mitad de su barra: requisito visual parcial, no alineación exacta aprobada.
- `loudness.py _work/recordings/wider-home-autoplay/owner.mp4 --measure-only --json-brief`:
  exit0,5.39s,-15.3LUFS,-2.2dBTP,LRA7.1LU. Sin modificación ni juicio de calidad subjetiva.
  Contraste independiente: RAM homes±700/radio199/final±700,Z0; trace anim67/68,fever/selector.
  Precisión±2frames estimada por latencia no calibrada. Ahorro/manual no medidos.
  Siguiente:mostrar candidato y límite de alineación al owner; no nueva partida automática.

## 2026-11-14 — referencias de barras para posiciones iniciales más abiertas

- Propósito: contrastar petición del owner con captura existente, no grabar otra partida.
  FFmpeg `2024-09-19-git-0d5b68c27c-full_build-www.gyan.dev` en
  `D:/ffmpeg/bin/ffmpeg.exe` elegido por el skill (`-version` verificado); no se cambió el
  backend WGC ni su FFmpeg8.1. Comandos `py -3.13 .agents/skills/ffmpeg-skill/scripts/probe.py
  _work/recordings/dance-center-autoplay2/raw.mkv --json-brief` y `look.py <mismo_input>
  --at 0.10 --at 1.546 --at 139.117 --no-timecode --width 960
  -o _work/gaso/drift/end-center/wider-home-reference.png --json-brief`.
- Probe:1920x1080,60fps,169.884s,H264,yuv444p; raw sin audio, como corresponde al video
  previo al mux. Audio de la evidencia aceptada anterior no se reanalizó ni retocó.
- Evidencia: tres PNG960x540 vistos; posición hacia el interior de las barras en
  t0.100 y139.117. `audit_wider_home.py` añade solo guías sobre copia de t0.100;
  `wider-home-score-guides.png` revisado visualmente. Centros aproximados del interior
  de barras x235/727, no calibración 3D ni simulación de nuevos bailarines.
- Independencia: `manifest.json` previo accepted=true; homes ±520 del muestreo previo
  y tabla nativa verificada por MCP/bytes. Hashes en `wider-home-audit.json`.
  Dictamen útil para evidenciar el problema; posición 3D nueva sigue pendiente.
  No se alteraron videos originales ni puertas. Tiempo/manual/ahorro no medidos.

## 2026-11-14 — dance-center-autoplay2: inspección visual y loudness bajo WGC

- Herramienta: `.agents/skills/ffmpeg-skill` (`look.py --tiles 4x3 --width 1280`, `loudness.py --measure-only`) + `bag2_record.py frames` + hoja comparativa Pillow (`_work/gaso/drift/end-center/dance-center-autoplay2-sheet.jpg`).
- Entradas: `_work/recordings/dance-center-autoplay2/review.mkv` y `owner.mp4` (exe `5258009e…`, `manifest.json` `accepted: true`).
- Evidencia: `loudness.py` midió `-15.2 LUFS`, `-2.0 dBTP`, `LRA 7.1 LU`. Las 12 miniaturas (`look.py --tiles 4x3`) y los fotogramas de `gf 7120, 11000, 15240, 15360, 15420, 16100` muestran ambos bailarines centrados cerca de sus columnas iniciales durante todo el baile y alineados simétricamente en `(±520, 0)` al `FREEZE!!` / `2 PLAYER WIN`, seguido por solo fever P2 y vuelta al selector.
- Límites: precisión ±2 fotogramas estimada; calidad subjetiva del audio queda al juicio humano. Tiempo/ahorro no medidos.

## 2026-11-13 — Revisión crítica de cámara95: NO supera aceptación

- Herramienta: skill local v3.6.0 (instalación registrada commit
  `641564b101f49789b45e22c83a34718a62f3f9fd`), scripts de `.agents/skills/ffmpeg-skill`;
  FFmpeg instalado `D:/ffmpeg/bin/ffmpeg.EXE`, sin actualización.
- Entrada: `_work/recordings/gaso-cam95-autoplay/review.mkv`, SHA256
  `8988a7013d2d8e6a044e0bc1ddd43ac6358913a993aedaf5336fcca3f0961d5f`.
  `probe.py <entrada> --json-brief`: 1920x1080/60fps, H264444, FLAC estéreo44100,
  191.834s. `look.py <entrada> --tiles 4x3 --width 1280`: overview inspeccionado.
- Contraste fino: `bag2_record.py frames --tag gaso-cam95-autoplay --frame 6590
  --span 35 --step 1`; 71 fotogramas consecutivos revisados en
  `intro-frame-sheet.jpg` (8.287–9.453s). A 8.536–8.8s siguen silueta exterior y
  vacío negro: FALLA encuadre inicial. No sustituir esa evidencia por simulación.
- Resultado: útil; detectó falso positivo de la predicción offline. Grabación aceptada
  por sincronía, no por calidad de cámara. No se certifica resto del flujo ni audio
  subjetivo; ±2 fotogramas es estimación, latencia de pantalla sin calibrar.
- Tiempo/ahorro/retrabajo: desconocidos. Siguiente: aislar cámara inicial antes de otra
  partida autorizada. No se editó ni volvió a finalizar la grabación.

## 2026-11-10 - ffmpeg-skill-001 - instalación e integración al proyecto

- Purpose: instalar el skill local de FFmpeg y documentar su uso obligatorio cuando sea pertinente para evidencia de video/audio del proyecto.
- Instalación: `npx ffmpeg-skill --dir ./tools` desde la raíz del proyecto; copia en `tools/ffmpeg-skill` (v3.2.3).
- Verificación inicial: `python tools/ffmpeg-skill/scripts/_contract.py doctor`; resultado: 84 capacidades disponibles, 0 requeridas faltantes, 1 opcional faltante (parakeet). FFmpeg `2024-09-19-git-0d5b68c27c-full_build` con libass, vidstab, zimg, etc.
- Integración: añadido a `notes/assets.md` como herramienta obligatoria cuando sea pertinente; no sustituye las pruebas de juego ni demuestra fidelidad por sí solo.
- Uso previsto: recortes precisos, montajes, extracción/medición de audio, hojas de fotogramas, comparación visual, exportación y comprobación de archivos generados. No aplicar normalización, silencio removal ni cambios de velocidad a evidencia original sin autorización.
- Límite: revisada documentación y metadatos; no auditado todo el código ni probada compatibilidad con todos los flujos.
- Next: primer ensayo acotado sobre una comparación visual y una extracción de audio, registrando hashes y resultados.

## 20261112-ffmpeg-skill-002 — 2026-11-12 — completar la copia cargada como skill y usarla en evidencia de juego

- Tipo: uso real + corrección de ffmpeg-skill-001 (ubicación).
- Versión, entorno y comando: kajisho5/ffmpeg-skill v3.6.0, commit `641564b101f49789b45e22c83a34718a62f3f9fd`, clonado en `_work/downloads/ffmpeg-skill-20261112/repo` y copiado (robocopy sin sobrescribir) a `.agents/skills/ffmpeg-skill/` con autorización del owner; `py -3.13 .agents/skills/ffmpeg-skill/scripts/_contract.py doctor`.
- Hallazgo: la copia que el agente carga como skill (`.agents/skills/ffmpeg-skill`) tenía solo 72 archivos (SKILL.md, `_common/`, evals, brand) y ningún script ejecutable; esos 72 eran idénticos byte a byte a v3.6.0. La copia completa v3.2.3 de ffmpeg-skill-001 sigue en `tools/ffmpeg-skill` (46 scripts, sin seguimiento en Git). Hay dos copias; retirar una requiere decisión del owner.
- Resultado: doctor v3.6.0 «85 capabilities available, 0 required missing, 1 optional missing» (parakeet). `probe.py` y `look.py --tiles 3x2` sobre `_work/recordings/rec-smoke-2/owner.mp4` (SHA-256 `f6cfd79b322f20574f14b56b9e5a6a4dd586ce8743dd1293f2c03e8d94abf54d`): 19.99 s, H.264 1256x952; la hoja muestra imagen real del juego, no negra.
- Contraste independiente: fotograma extraído a t=10.000 s muestra `gf 15534`; el ajuste del reloj da 15534.71.
- Dictamen: útil para inspeccionar grabaciones (probe, hojas, fotogramas). No graba: la captura la hace `tools/test/bag2_record.py` (log `bag2-record.md`).
- Medición: no medido.
- Decisión: usar `.agents/skills/ffmpeg-skill` v3.6.0 en el flujo `bag2-game-recording`; pendiente decisión del owner sobre `tools/ffmpeg-skill`.

## 2026-11-12 - CAUGHT retire: inspección del vídeo rechazado

- v3.6.0, `py -3.13 .agents/skills/ffmpeg-skill/scripts/probe.py
  _work/recordings/gaso-retire-heat-bag1/raw.mkv --json`: 309,5s,1920x1080,
  H.264 yuv444p,60fps, vídeo crudo sin audio. SHA `60076242…92243`.
- `look.py` (dry-run y ejecución) con `--at 131.7 --at 132.82 --at 133.2
  --at 134.5 --at 136.22 --at 137.0 --width 960 -o _work/gaso/retire-overview.png`.
  Inspeccionados 133,2s y136,22s: Heat dentro del tanque; no ventana superpuesta
  ni imagen negra en esos fotogramas. Trace gf8088 anim1 y gf8292 anim89
  confirma que la segunda toma no reutilizó CAUGHT; no inferido solo de la pose.
- Resultado útil como diagnóstico; NO validación aceptada (manifest rechazado
  por audio). Tiempo/retrabajo/ahorro no medidos. Próximo: inspeccionar captura
  nueva si pasa el manifiesto, y no reutilizar estos frames como aceptación.

## 2026-11-12 - active-reuse: detectar oclusión pese a manifiesto temporal verde

- v3.6.0 `probe.py` sobre `gaso-active-reuse-heat-bag1/raw.mkv`; `look.py` con
  dry-run y ejecución a0,5/1,9/2,94/3,4/6,35/10,1/167/170s, width640;
  JSON/logs `_work/gaso/reuse-{raw-probe,look,look-plan}.json`.
- Revisada `reuse-overview-grid.png`: en los ocho tiempos aparece otro juego,
  no BAG2JP. Resultado útil: invalida la evidencia visual aunque el manifiesto
  del grabador diga accepted=true por sincronización. No se entrega ese contenido
  ajeno como vídeo del ataque; dictamen `_work/gaso/reuse-visual-review.json`.
- Tiempo/manual/ahorro no medidos. Siguiente: repetir solo con captura visible
  válida; no más inspección de la aplicación ajena para este objetivo.

## 2026-11-12 - ventana temporal de prueba: verificar los píxeles de Always on Top

- v3.6.0 `probe.py _work/gaso/window-focus-native-v3/capture/raw.mkv --json`:
 3,184s,640x420,60fps,H.264. `look.py ... --at 1 --width 640 -o .../visible.png`
  (dry-run y ejecución). Evidencia JSON y comandos guardados en esa carpeta.
- Imagen inspeccionada: fondo verde y texto RECORDING WINDOW TEST, ventana
  seleccionada encima de una competidora roja propia. Primera apertura de PNG
  supuso sufijo `_1.000s`; con un único --at el nombre es `visible.png`, corregido
  leyendo la ruta del resultado, sin regenerar. Resultado útil para comprobar
  contenido real del ensayo Win32; no hay prueba del ataque/juego aquí.
- Tiempo/ahorro no medidos. Siguiente: repetir evidencia BAG2JP con el guard
  compartido tras la revisión y mantener inspección visual (API no prueba píxeles).
- Contraste final tras separar teclado de topmost: `window-focus-native-v6`,
  `probe.py`3,184s/640x420/60fps; `look.py --at 1 --width 640 -o visible.png`
  (dry-run y ejecución) muestra ventana verde propia correcta con teclado aún
  en otra ventana. Metadatos Win32 focus_acquired=false y guard passed=true;
  topmost/foco previo restaurados. No es vídeo ni aceptación de BAG2JP.
- Integración real nueva `gaso-topmost-reuse-heat-bag1`: inspección temprana una
  sola vez, mientras se graba, con `look.py raw.mkv --at 1 --width 640
  -o _work/gaso/topmost-early-check.png` (dry-run+ejecución). Imagen revisada:
  BAG2JP con Gas-O y Heat visibles en GasOBAG1, no la aplicación que tapaba el
  ensayo anterior. Demuestra ese instante de contenido, no aceptación temporal
  ni toda la partida; pendiente cierre/manifest e inspección de ataques.
- **Revisión visual de la partida aceptada, sin abrir 75 PNG sueltos**: los
  stills de `bag2_record.py frames` (25 por evento, `review.mkv`, etiquetados por
  tiempo) se combinaron en láminas de contacto con `_work/gaso/make_sheets.py`
  (Pillow): `_work/gaso/sheets/{first-catch,second-catch,retire}.png` y recortes
  `key-catches.png`/`key-rival.png` (mitad izquierda/rival) a mayor tamaño.
  Orden cronológico reparado: el nombre `NN.NNNs.png` ordena 10.x antes que 9.x,
  se corrigió ordenando por el valor numérico de segundos (no por nombre).
  Hallazgo útil con las láminas: el impacto y el agarre/lanzamiento del clip
  CAUGHT se leen claramente con 3-6 fotogramas por fila, sin saturar de imágenes
  la conversación. Límite: el montaje es una ayuda de revisión; los píxeles
  individuales siguen siendo la referencia.
- `loudness.py owner.mp4 --measure-only --json` → `input_i=-16.41 LUFS`,
  `input_tp=-2.06 dBTP`, `input_lra=4.30` (`_work/gaso/topmost-owner-loudness.json`).
  Medición objetiva de nivel del audio entregado; la calidad subjetiva es juicio
  humano, no lo decide la herramienta.

## 2026-11-13 - caught-tank-liquid: comparación de cerca con BAG1

- Comandos: `ffmpeg -ss <t> -i review.mkv -vf crop=iw*0.34:ih*0.82:iw*0.50:ih*0.04,fps=5,scale,tile=6x2` (hojas a 5 fps),
  la misma sin `fps` y `tile=8x3` (fotogramas consecutivos de inicio y corte), `crop=360:760:900:60` sobre
  `raw.mkv` BAG1 en 31,0 s y `hstack` para el lado a lado; Pillow para percentiles de color.
- Evidencia: `_work/gaso/liquid-review/` (liquid2..6 hold sheets, liquid5b-onset-consecutive,
  liquid6-cut1-consecutive, liquid6-vs-bag1). Mediana del tanque BAG1 (47,90,44); BAG2 antes (31,109,50),
  final (54,91,56); blancos BAG1 (153,185,150) usados para despejar el color de la mezcla al 50 %.
- Resultado: útil y decisivo: detectó burbujas oscuras (mezcla promedio), burbujas tipo gema (relleno aditivo)
  y saturación verde, cada una corregida con una iteración. Límite: fondos distintos entre juegos; la mediana
  es orientativa; juicio visual final del propietario.

## 2026-11-13 - liquid7c: comparación de proporciones y anillos

- Misma instalación FFmpeg/Pillow; no actualización. Entradas: review.mkv de
  gaso-liquid7c-heat-bag1 (manifest accepted=true, runtimeca4a31c6 JP) y referencia
  BAG1 raw.mkv de20261112T163101 a31s; hashes de captura en sus manifests/sesiones.
- Comandos relevantes: `ffmpeg -ss 3.9 -i review.mkv -frames:v 1`;
  `crop=900:1080:900:0,scale=400:480`, `hstack=3` con comparación previa;
  onset `-ss 2.90 -t 0.40 -vf crop=700:1080:1000:0,scale=140:216,tile=12x2
  -frames:v 1`; cut `-ss 5.10 -t 0.60` con tile12x3. Zoom onset select n4..8.
- Evidencia: liquid-review/measure-l7.png, phone-3-proportions.jpg,
  phone-4-bubbles.jpg, l7-onset-sheet.png, l7-onset-zoom.png, l7-clear-sheet.png,
  l7-bubble-grid.png. Fallos conservados en el historial: extracción tile sin
  frames:v1 intentó múltiples salidas con un nombre; corregido. Recortes iniciales
  de rejilla omitían tanque; lecturas paralelas a creación de imágenes dieron
  file-not-found o imagen anterior; se releyeron después de finalizar. No usar
  esas primeras rejillas como medida. El comparativo ampliado no normaliza el
  tamaño de las burbujas entre juegos y no es una medición de radio relativo.
- Contraste independiente: eventos sitúan tanque1 en2,954s; host emite anillo
  ovalado18×22, consistente cualitativamente con el zoom. Una hoja pequeña
  parecía carecer de verde en onset; zoom confirma cristal presente. Corte limpio.
- Resultado: útil para detectar ovalado residual; no prueba redondez, coincidencia
  perfecta ni audio subjetivo. Precisión estimada±2frames, no calibrada. Tiempo
  manual/ahorro no medidos; en continuación se reutilizan imágenes, sin nueva
  ejecución FFmpeg/grabación hasta tener cambio verificable que inspeccionar.

## 2026-11-13 - bubble-aspect: inspección de captura aceptada16:9

- Mismo skill localv3.6.0/FFmpeg ya instalado. Entrada JP/exp-8mb752e21f0,
  review.mkv SHA24efff99c7914d8fd239c80f126d2f2b0ff54173b6a33aaa0234b07a6609ec25,
  taggaso-bubble-aspect-heat-bag1, manifest accepted=true; referencia BAG1
  full-bag1-31.0.png y liquid7c3.9s reutilizados, sin reextracción/hash pesado.
- `probe.py review.mkv --json-brief`:170,7s,1920×1080/H.264yuv444p,60fps,
  FLAC estéreo. `look.py ... --at 3.83 --width 1920 -o new-frame.png` (plan
  --dry-run --json seguido de ejecución --json). `look.py` repetido con --at
  para secuencias; frames exactos vía `bag2_record.py frames --frame7190/7329/
  7620 --span8/10 --step1`; final look --at160.5 --at170.0. Salidas aspect-review.
- Fallos/contraste: stills del grabador1280×720, primeras hojas usaron crop1920
  y omitieron actor; rehechas con dimensiones medidas. Orden léxico ponía10s
  antes de9s: rehecho numérico. Primer cálculo wall-start de events.csv no es
  video_time del fit; se usó events.json para alinear spawns2,884/2,813 y
  holds3,9/3,83 (~1,016s). Extra aligned-new3.76 no se usa para comparación.
- Look: onset/clear/release2-consecutive.jpg revisados frame a frame; ambos
  cortes limpios, caída90 persiste. phone-proportions.jpg y phone-bubbles.jpg
  muestran burbuja más redonda pero borde aún más definido que nativo. Celdas
  de zoom tienen mismo crop280×200 y resize1,5×, sin estirar formas; no igualan
  tamaño relativo por personaje. end-flow.jpg prueba selector de regreso.
- Límites: fronteras visibles~3-4 frames tras etiqueta del log, latencia no
  calibrada; ±2 era estimación, no garantía. Audio subjetivo requiere humano.
  4:3 rechazado no usado como evidencia visual válida. Herramienta útil para
  detectar diferencias residuales; tiempo/manual/ahorro no medidos.

## 2026-11-13 inspección del candidato hold

- Herramientas instaladas FFmpeg y scripts ffmpeg-skill (sin actualización).
  `probe.py .../gaso-caught-hold-heat-bag1/review.mkv --json-brief`;
  `look.py ... --at 3.1 --at 4.5 --at 5.25 --at 6.5 --at 8.5 --at 9.9
  --at 12 --at 170 --width 960 -o _work/gaso/slide/hold-look.png --json`;
  plan dry-run previo retenido. JPEG compacto `hold-contact.jpg` revisado.
- `cut.py .../owner.mp4 --start 1.5 --end 12.5 --accurate
  -o _work/gaso/slide/gaso-hold-attacks.mp4 --json-brief`, salida0; originales
  preservados. Pérdida de deriva contrastada con RAM, no solo posición en pantalla
  (la cámara se mueve). Pose/salida revisadas con frames del recorder.
- Útil; queda oscilación raíz2 unidades y transición inicial10. No certificado
  fijo perfecto. Audio subjetivo requiere humano; tiempo/ahorro desconocidos.

## 2026-11-13 inspección clamp e165817c

- Probe/look sobre toma aceptada `gaso-clamp-last-heat-bag1/review.mkv`:
  3,3/4,6/6,7/9,2/10,2/12/160,5/170s,width960,contacto `clamp-contact.jpg`.
  Frames del recorder confirman entradas/cortes/caída; cámara móvil, posición
  mundial contrastada en RAM. Cut owner.mp4 start1.5/end12.5/accurate:
  `_work/gaso/slide/gaso-clamp-attacks.mp4`, salida0, originales preservados.
  Sin publicación externa. Útil; re-hit(-4,+3) no resuelto, audio subjetivo
  pendiente. Tiempo/ahorro no medidos.

## 2026-11-13 revisión re-hit modo0 (ffmpeg directo, no scripts de la skill)

- ffmpeg/ffprobe directos: hoja de calibración (xstack; drawtext falló por
  fontconfig y se omitió), recortes de Heat en stills 1280x720, corte A/B
  `rehit-ab-native-vs-mode0.mp4` y corte de ataques. No se usó look.py/check.py
  porque bastaban recortes fijos; la comparación de audio se hizo con numpy
  sobre los dumps alineados por frame (`compare_rehit_audio.py`).
- Resultado: útil; detectó diferencia de audio objetiva en el re-hit.
## 2026-11-13 - gaso-combined-ae-f2: inspección de toma combinada A-E/F

- Herramienta: `.agents/skills/ffmpeg-skill` v3.6.0 (`probe.py`, `loudness.py --measure-only`)
  y `ffmpeg` para hojas de contacto (`_work/gaso/combined-ae/build_f2_sheets.py`) sobre
  `_work/recordings/gaso-combined-ae-f2/owner.mp4` (`165f2984...`, manifest `accepted: true`).
- Resultados: `probe.py` confirma `1920x1080` H.264 46.032 avg fps / 60 r_frame_rate, AAC 44100 Hz
  estéreo, 192.867 s; `loudness.py --measure-only` mide `-15.23 LUFS`, `-0.58 dBTP`, `LRA 7.80 LU`
  sin modificar el archivo. Hojas `intro.jpg`, `tank1.jpg`, `tank2.jpg`, `lvl2.jpg`, `songend.jpg`
  verifican descenso de cámara intro, HUD `GAS-O`, dos capturas con tanque/líquido/burbujas,
  iluminación nivel 2 y regreso al selector.
- Límites: latencia de pantalla sin calibrar y calidad subjetiva del audio de tanque pendiente
  de escucha humana. Tiempo manual/ahorro no medidos.

## 20261114-ffmpeg-skill-leash-release-review — 2026-11-14 UTC — radio BAG1 y liberación nativa
- Tipo: uso real diagnóstico; skill local3.6.0, Python3.13; no reparación del rechazo.
- Comandos: `py -3.13 .agents/skills/ffmpeg-skill/scripts/probe.py _work/recordings/bag1-leash-autoplay/raw.mkv --json-brief`; `look.py` mismo input `--at 16 --at 30 --at 50 --at 70 --at 90 --at 110 --at 130 --at 150 --at 170 --at 182 --width 640 -o _work/gaso/drift/leash-sample.png --json`, precedido del plan `--dry-run --json`.
- Entradas: raw.mkv SHA-2564ff430ee0473c282a0c8cebae67d31a80c2dd10b8e36459eb37095fb9fed31e2, exe16768892; JP005/partida Gas-O BAG1 vs Heat BAG1.
- Resultado: probe1920x1080,60fps,192.35s,H264444,sin audio en raw (esperado); extracción10PNG exit0, plan/result en `_work/gaso/drift/leash-sample-{plan,result}.json`, probe `leash-probe.json`.
- Contraste: manifest accepted=false por audio; PNG no inspeccionados como aceptación. La extracción precedió a conocerse el rechazo. No corrección de sync para eludir el grabador.
- Dictamen: útil para preparación de inspección, inconcluso para gameplay; no se afirma Look/PASS.
- Medición: ejecución/preparación/revisión/retrabajo no medidos; ahorro no medido.
- Siguiente: reutilizar técnica para nueva toma válida; no volver a analizar visualmente esta captura como prueba aceptable.

## 20261114-ffmpeg-skill-release-accepted — 2026-11-14 UTC — intro, muestras y cola de la toma aceptada
- Tipo: uso real de inspección; skill local 3.6.0, Python3.13; la grabación ya estaba aceptada por `bag2_record`.
- Comandos: `probe.py _work/recordings/bag1-release-autoplay/raw.mkv --json-brief`;
  `look.py` mismo input `--at 16 --at 30 --at 50 --at 70 --at 90 --at 110 --at 130 --at 150 --at 170 --at 182 --width 640 -o _work/gaso/drift/release-sample.png`
  (con plan `--dry-run --json`) y `--at 186 --at 189 --at 191 --at 193 -o _work/gaso/drift/release-tail.png`.
- Entrada: `raw.mkv` SHA-256 `94204911…`, runtime `3b43cff8…`, partida Gas-O BAG1 A vs Heat BAG1 A.
- Resultado: probe 1920x1080, 60 fps, 193.367 s, H264; 10 PNG de baile y 4 de cola, exit0.
  Hojas propias: `release-spacing-sheet.jpg` (`0798a33c…`), `release-tail-sheet.jpg` (`cfefc9cd…`),
  comparadas con `baseline-spacing-small.jpg`.
- Contraste: separación sostenida en 16–182 s, fin con `PLAYER 2 WIN` y regreso a Character Select
  en 189/191/193 s; la liberación se revisó además con 24 PNG de `bag2_record.py` en gf15681.
  Camera_speed 2.1 y hooks de cámara no se tocaron.
- Dictamen: útil; permite revisar video aceptado sin modificar el original. No mide píxeles ni
  demuestra sincronización por sí solo.
- Límites: ±2 fotogramas; audio subjetivo humano; PNG escalados a 640 px de ancho no sirven para
  medición fina de píxeles.
- Medición: ejecución/preparación/revisión no medidas; ahorro no medido.
- Siguiente: conformidad del owner; reutilizar el mismo flujo en la próxima toma autorizada.

## 20261114-ffmpeg-center-calibration — 2026-11-14 UTC — revisión del catálogo
- Tipo: uso real; skill local3.6.0/Python3.13. Runtime `893833b1…` JP.
- Comandos: `probe.py _work/recordings/bag1-center-calibration/review.mkv --json-brief`;
  `look.py` mismo input `--tiles 4x2 --width 1280 -o _work/gaso/drift/end-center/calibration-sheet.jpg`,
  primero `--dry-run --json`, después ejecución.
- Resultado: video59.85s/1920x1080/60fps/H264+FLACstereo; hoja1290x366 revisada,
  junto a `calibration-edges.jpg`1600x780 de las diez capturas requeridas.
- Evidencia/hash de input: manifiesto aceptado en `_work/recordings/bag1-center-calibration/manifest.json`.
- Contraste: ocho transiciones con retratos correctos y ventana sin cubrir; catálogo ligado al runtime.
- Dictamen: útil para revisión visual de navegación, no prueba de centrado. Preparación/ejecución/revisión
  y ahorro no medidos. No se modificó el original; precisión ±2frames estimada/audio subjetivo humano.
- Siguiente: inspeccionar la grabación de partida solo tras su aceptación técnica.

## 20261114-ffmpeg-block4-selector — 2026-11-14 UTC — primer nombre tras retorno

- Uso real del skill local: `py -3.13 .agents/skills/ffmpeg-skill/scripts/probe.py
  _work/recordings/block4-selector-cal/owner.mp4 --json-brief` y mismo probe para
  `block4-selector-return/owner.mp4`; manifest de ambas capturas accepted=true.
- Entrada del primer retorno: runtime23bbdabd,203.433991s,1920x1080,media31.939fps
  (WGC VFR, no confundir con59.9408Hz del juego). No se conformó ni retocó el original.
  `look.py <owner.mp4> --at 27 --at 75 --at 130 --at 164.4 --at 168.7 --at 173.3
  --at 180 --at 188.9 --at 193 --at 196 --at 199 --at 202 --no-timecode --width480
  -o _work/gaso/block2/block4-selector-return-overview.png --json-brief`, precedido
  por dry-run. `--at` produce PNGs separados (no una hoja aunque se indique tiles);
  composición PIL ordenada numéricamente, sin alterar fotogramas.
- Hoja revisada: READY/baile/final, victoria Heat y dueto natural fever2; al retornar
  retrato Gas-O, pero nombre BI-O en gf17557 y GAS-O desde196s. Hallazgo útil que
  impide cerrar la corrección parcial y motivó localizar el consumidor nativo.
- FFmpeg resuelto por skill: D:/ffmpeg/bin/ffmpeg.exe, instalación2024-09-19-git-0d5b68c27c
  previamente verificada, distinta del backendWGC8.1. Tiempos por --at en VFR pueden
  saltar al siguiente fotograma disponible; se mantiene límite estimado±2frames.
  Audio subjetivo no evaluado. Ahorro no medido. Siguiente: revisar nueva toma e709c2f8.

### Resultado del nuevo consumidor (e709c2f8)

- Nueva captura `block4-consumer-return` accepted=true, owner.mp4 analizado con
  probe.py y look.py (`--at168/180/188/193/194/195/196/199/202 --no-timecode --width480`;
  dry-run y ejecución separados). Hoja `block4-consumer-review.png` revisada:
  primera muestra del selector gf17532/t193.400 ya GAS-O (retrato/nombre/fondo),
  Heat preservado; sin BI-O transitorio hasta202s.
- `bag2_record.py frames --tag block4-consumer-return --frame17532 --span18 --step1`
  reutiliza look.py sobre review.mkv.37muestras ordenadas por tiempo; recorte PIL
  de ambos nombres en `block4-consumer-first-name-frames.png`, todas GAS-O/Heat.
  No confundir muestras solicitadas con imágenes únicas: WGC VFR puede repetirlas.
- Dictamen: útil, permite aceptar técnicamente la corrección para esta pareja;
  conformidad del propietario/matriz de lados siguen aparte. Precisión±2frames
  estimada, audio subjetivo no juzgado; ahorro no medido.

## 20261115-ffmpeg-recovery-calibration — inspección del guard1

- Herramienta existente v3.6.0: `scripts/probe.py
  _work/recordings/block4-recovery-cal2/owner.mp4 --json-brief`;
  salida `_work/gaso/block2/recovery-cal2-probe.json`.
- Video54.384s,1920x1080,H.264; grabador aceptó reloj/audio sin alterar
  gates. Imágenes de navegación contrastadas aparte en hoja PIL reducida.
  Útil para verificar formato, no demuestra recuperación ni audio subjetivo.
  Tiempo/ahorro no medidos; siguiente: inspección de la toma save/load.

### Diagnóstico de la primera toma save/load (rechazada)

- probe.py owner.mp4:43.05s. look.py raw.mkv --at38 --width960, dry-run
  y ejecución, salida recovery-load-menu.png. Inspección: menú SAVE STATES
  abierto en slot01 vacío, no CAUGHT avanzando. Coincide con ausencia SAVED/.pst
  y heartbeat congelado. Fuente framework distingue event-drain y pause-loop;
  corrección limitada al wrapper. Útil para diagnóstico de entrada, **no**
  validación de juego porque manifest accepted=false. Tiempo/ahorro no medidos.

### Tercera toma: evidencia diagnóstica aceptada, no recuperación

- probe.py owner.mp4 y look.py raw.mkv --at38 --width960 (dry-run+ejecución)
  en block4-recovery-load3. Still recovery-load3-menu.png inspeccionado: F7,
  slot01 vacío, no se guardó. Coincide con log sin SAVED/.pst y trial saving.
  Manifest accepted=true pero flujo pedido no realizado; no confundir ambos.
- Útil para refutar la fiabilidad del margen25ms y detener repeticiones sin
  señal de disponibilidad. Sin juicio de audio subjetivo ni aceptación CAUGHT.
  Tiempo/ahorro no medidos. Próximo paso interno de sincronización del menú.
