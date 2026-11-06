---
id: character-import-digest
title: "Runbook de importación: gates"
tags: ["digest", "bag1"]
summary: "Perfiles de datos, inventario por personaje y aceptación dentro de alcance; comandos en la fuente."
related: ["CHARACTER_IMPORT.md", "IMPORT_STANDARD.md"]
created: "2026-11-02"
updated: "2026-11-06"
doc_kind: digest
source: "CHARACTER_IMPORT.md"
source_sha256: "71e34c3d8cadf5d2b4b24cedc0f91e5894911a80f51a5915a534577550c5c743"
---

- Fuente canónica: [CHARACTER_IMPORT](../../CHARACTER_IMPORT.md); entrada mínima:
  [IMPORT_STANDARD](../../IMPORT_STANDARD.md). No leer ambos completos por defecto.
- Perfiles de datos; identificar ID/layout, contrato por significado/beats/eventos
  y predecesores. No clonar Heat ni generalizar DBI/cues/escenario.
- `init-profile` produce schema 1, plan/prepare requieren schema 2 y gates
  (también evidencia gameplay); no simular capacidades/aceptación para pasar.
- Construir candidatos preservando imports previos; DFS con offsets reales,
  payload exacto/alt_size. Capacidad DUMMY: chequeo manual independiente obligatorio.
- Build no sincroniza; experimental solo. Cuatro casos lado/traje y capacidades
  aplicables, sonido, final y retorno con mods. Cache/código/tests host no bastan.
- Evidencia con inputs/runtime/hashes, restauración, checkpoint y snapshot.
- Seams auditados 06-11: modelo 0x3C→0x48, TIM/CLUT, adaptadores de motions y
  rebase banco+eventos; comandos y límites en «Verified conversion seams».
  `rebuild_animation_payload` presupone bytes originales cero; no eludir su
  rechazo ni aplicarlo a un manifest con expected_sha256 de originales no cero.
