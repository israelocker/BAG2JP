---
id: character-import-testing-digest
title: "Pruebas de importación: matriz y grabación"
tags: ["digest", "bag1", "testing"]
summary: "Gates de prueba, CAUGHT universal exigido y grabación WGC con audio por proceso explícito; no equivale a aceptación."
related: ["notes/character-import-testing.md", "notes/character-pipeline.md"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: digest
source: "notes/character-import-testing.md"
source_sha256: "9805c699d539d8980df2604fb3d83048e1ae98a4941bad0f2f8c5bd4c21753af"
---

# Pruebas: lectura por fase

- Leer la sección necesaria de [la fuente](../character-import-testing.md).
- Proteger settings/tarjetas y proceso del owner. Calibración ligada al exe y
  entradas; no forzar hashes. Host/flujo no prueban fidelidad ni aceptación humana.
- Matriz P1/P2×A/B, mixtos/espejo y dos escenarios dentro del alcance. CAUGHT en
  todos los importados/nativos y compañeros es requisito, aún no cobertura.
- Casilla compartida: retrato/nombre por versión/lado; cambio/vuelta a BAG2,
  preview/cancelación/confirmación, stage select y retorno, también HD si activo.
- Nombre encima de puntuación: validación aparte, visible/completo/legible durante
  el flujo grabado, versión y lado correctos; vuelta a BAG2 restaura su nombre.
- «Grabación: procedimiento vigente tras Gas-O» sustituye recetas antiguas:
  WGC verificado y `--audio-backend process` explícito (default CLI aún dump),
  flags por harness, trace/heartbeat, tags únicos, guardar desde escenario a retorno.
- Handshake observable para menú/save/load; cerrar grabador antes que juego.
  No rescatar ni relajar gates; diagnosticar offline antes de otra toma.
- Registrar features/flags efectivos y rutas reales de tarjetas sin sobrescribir
  cambios concurrentes; distinguir reloj musical/global/QPC/video. Primera
  presentación del selector también se revisa, no solo el estado estabilizado.
- Manifest accepted=true solo acepta captura. Revisar pixels BAG2JP y cada evento,
  audio objetivo más escucha humana. Latencia no calibrada; no garantía ±2 frames.
- Comandos, backends, límites del harness y fallos conocidos en la fuente.
