---
id: character-import-digest
title: "Runbook de importación: gates"
tags: ["digest", "bag1"]
summary: "Perfiles de datos, inventario por personaje y aceptación dentro de alcance; comandos en la fuente."
related: ["CHARACTER_IMPORT.md", "IMPORT_STANDARD.md"]
created: "2026-11-02"
updated: "2026-11-15"
doc_kind: digest
source: "CHARACTER_IMPORT.md"
source_sha256: "db72c0045f55fb4c4e1ac2656aa8a7249861a23479c5fc330ceec47cfcf3cd5e"
---

- Fuente canónica: [CHARACTER_IMPORT](../../CHARACTER_IMPORT.md); entrada mínima:
  [IMPORT_STANDARD](../../IMPORT_STANDARD.md). No leer ambos completos por defecto.
- Perfiles de datos; identificar ID/layout, contrato por significado/beats/eventos
  y predecesores. No clonar Heat ni generalizar DBI/cues/escenario.
- Lecciones Gas-O: mismo proceso con datos propios, no sus constantes/adaptadores.
  Retrato/nombre del personaje por versión y lado al compartir casilla; preservar
  identidad BAG2. Comet/Frida es caso futuro, no soporte actual.
  CAUGHT se exige en cada importado BAG1 y nativo BAG2, lados/variantes/compañeros;
  es requisito de aceptación, no cobertura ya alcanzada.
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
