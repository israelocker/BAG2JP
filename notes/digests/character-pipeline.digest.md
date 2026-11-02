---
id: character-pipeline-digest
title: "Shared character pipeline digest"
tags: ["digest", "character", "workflow"]
summary: "Pipeline único, perfiles de datos, referencias por hash y límites de implementación/aceptación."
related: ["notes/character-pipeline.md", "notes/character-alternate-entries.md", "notes/character-import-testing.md"]
created: "2026-11-02"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: digest
source: "notes/character-pipeline.md"
source_sha256: "137f452c86a9fac21bf2728d4f51bd507ad37d563edee701c88fc15669606c26"
---

# Pipeline compartido: resumen

- Etapas: inventario → contrato → predecesores/cobertura → candidato → aceptación.
- Perfiles contienen datos/capacidades/excepciones; no comandos ni pipelines clonados.
- Roles se igualan por significado, beats y eventos, no por número de request.
- Cache exige hashes motion/profile/catalog/runtime/evidencia. Un hit no prueba gameplay.
- Herramientas compartidas validan perfiles, referencias, políticas y contenedores;
  conversores/auditores Heat y Strike todavía incluyen adaptadores específicos.
- No hay solver universal de asignación/optimización de grafo implementado.
- Strike ID=1 verificado, integrado en DUMMY, P1/A y P2/B completan canción/retorno.
  Texturas, cobertura P1/B/P2/A y fever propio siguen pendientes de aceptación.
- Integración exacta/staging: `notes/character-alternate-entries.md`.
- Harness/calibración/matriz/diagnóstico: `notes/character-import-testing.md`.
- GPU: un modelo local a la vez, separado de pruebas del juego.
