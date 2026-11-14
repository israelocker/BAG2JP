---
id: gaso-import-digest
title: "Gas-O: centrado final BAG1 experimental"
tags: ["digest", "gaso", "bag1", "evidence"]
summary: "Candidato GO+2s ±870 (ff800b28) en experimental; partida WGC aceptada: cuerpos cerca de los puntos medios de barra, final ±870/Z0, fever y selector. Pendiente conformidad del propietario. Sin Bloque2, commit ni snapshot."
related: ["notes/gaso-import.md", "_work/current-state.json"]
created: "2026-11-14"
updated: "2026-11-14"
doc_kind: digest
source: "notes/gaso-import.md"
source_sha256: "f214384b0a3de13bcd3d088924ac94d6f868b40763d2fe0cbcaecc351a5b1ae1"
---

# Gas-O: lectura vigente

Derivado de la sección «Referencia GO + 2 s: candidato ±870»; verificar hash de la fuente
antes de reutilizar. La nota canónica conserva la cronología.

- **Vigente:** el propietario fijó la referencia inicial en GO + 2 s (cámara asentada
  T=[0,692,3028]). Medición `go-plus2-measure` aceptada; modelo GTE 0.75/OFX256 da ±870
  (zoom128: ±435). Solo cambia `B1HOME_WIDE`; radio 199, guardas y cámara nativa intactos.
- 23 tests PASS, 11/11 mutantes; dos Goldfish triados (`triage-go-plus2-anchor.md`).
  EXE `ff800b28…` desplegado EXE-only en experimental; calibración `go-plus2-cal` aceptada.
- `go-plus2-autoplay` **accepted=true** (1999 heartbeats, 1 stall, 11975 pares audio sin
  descartes; 150 saves/configs restaurados). GO+2 s: cuerpos ~215/~735 px frente a 235/727;
  la muestra RAM más cercana llega +0.88 s tarde (estimación visual, ±2 fotogramas).
- RAM: homes ±870, radio 199; final anim67/68 [-870,312,0]/[870,520,0]; INT_MAX, fever y
  selector observados. Hojas `go-plus2-match/` sin recortes visibles.
- **Conformidad del propietario** (2026-11-14) y commit local WIP del árbol completo.
  Snapshot tras el Bloque 2. Siguiente: Bloque 2 (ataques/CAUGHT/dueto/cierre). Histórico: READY ±1300 quedaba hacia el borde exterior a GO+2 s; ±700 hacia dentro.
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
