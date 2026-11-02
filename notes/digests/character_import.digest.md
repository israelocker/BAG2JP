---
id: character-import-digest
title: "Runbook de importación: gates"
tags: ["digest", "bag1"]
summary: "Perfiles de datos, inventario por personaje y aceptación dentro de alcance; comandos en la fuente."
related: ["CHARACTER_IMPORT.md", "IMPORT_STANDARD.md"]
created: "2026-11-02"
updated: "2026-11-02"
doc_kind: digest
source: "CHARACTER_IMPORT.md"
source_sha256: "ff23496979f97b0bf6145892b8181fccbbf4b6deb6af8796087e94b2f2559fbc"
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
