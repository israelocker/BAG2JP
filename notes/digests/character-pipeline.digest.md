---
id: character-pipeline-digest
title: "Shared character pipeline digest"
tags: ["digest", "character", "workflow"]
summary: "Pipeline único, perfiles de datos, referencias por hash y límites de implementación/aceptación."
related: ["notes/character-pipeline.md", "notes/character-alternate-entries.md", "notes/character-import-testing.md"]
created: "2026-11-02"
updated: "2026-11-06"
edited: "2026-11-06"
doc_kind: digest
source: "notes/character-pipeline.md"
source_sha256: "a0eb797ebe523b3200a01ba26e5b9303888dbbcf2c2c83776cffde8ddfbdcc2a"
---

# Pipeline compartido: resumen

- 04-11/06-11: checklist de lecciones verificadas (carpeta=traje/sufijo=lado, alineación DFS 4 B, copias de atlas MoveImage del DBI BAG2, esqueleto por traje, neutral/política de slots, RAM 8 MB, voces rebasadas + anunciador, escala del bailarín, rostro/iluminación, hashes del manifest, eventos del escenario por puntaje, pruebas de aceptación). Ver «Lecciones verificadas» de la fuente.
- Etapas: inventario → contrato → predecesores/cobertura → candidato → aceptación.
- Perfiles contienen datos/capacidades/excepciones; no comandos ni pipelines clonados.
- Roles se igualan por significado, beats y eventos, no por número de request.
- Cache exige hashes motion/profile/catalog/runtime/evidencia. Un hit no prueba gameplay.
- Herramientas compartidas validan perfiles, referencias, políticas y contenedores;
  conversores/auditores Heat y Strike todavía incluyen adaptadores específicos.
- No hay solver universal de asignación/optimización de grafo implementado.
- Usar `funcmatch.py` para buscar candidatos entre ejecutables principales cuando
  corresponda; experimental, necesita pruebas profundas. Entradas/base fijas,
  sin overlays; confirmar cada coincidencia en Ghidra antes de confiar en ella.
- Strike ID=1: el ledger y plan de disparo conservan pruebas posteriores de los
  cuatro casos P1/P2 × A/B; no convertirlas en aceptación global. El override
  nativo de iluminación fue descartado por el propietario el 05-11 y debe seguir
  inactivo. Stage/audio y Ending View tienen recetas propias; campaña pendiente.
- Manifest: sha256 del overlay = payload; expected_sha256 = bytes originales
  reemplazados, no payload; disc_sha256 = disco. Staging y capacidad requieren
  comprobación independiente aunque el generador canónico ya use bytes.
- Integración exacta/staging: `notes/character-alternate-entries.md`.
- Harness/calibración/matriz/diagnóstico: `notes/character-import-testing.md`.
- GPU: un modelo local a la vez, separado de pruebas del juego.
