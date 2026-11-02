---
id: bag1-character-heat
title: "Heat: adaptadores y evidencia histórica"
tags: ["bag1", "heat", "reference"]
summary: "Ubica adaptadores Heat y hallazgos históricos sin tratarlos como reglas universales o aceptación actual de todo el personaje."
related: ["notes/character-pipeline.md", "notes/character-alternate-entries.md", "notes/strike-recovery.md"]
created: "2026-10-29"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: reference
---

# Heat no es la plantilla de todos los personajes

Código existente contrastado por ruta y función:
- `tools/bag1import/model_bag1_to_bag2.py`: adaptación del layout de modelo.
- `tools/bag1import/anim_remap.py`: política/dispatch Heat; no solver genérico.
- `tools/bag1import/patch_heat_dbi.py`: adaptación específica de huesos/accesorio.
- `tools/bag1import/audit_animation_roles.py`: auditor Heat, no aceptación universal.
- `tools/bag1import/preserve_announcer.py` y `restore_heat_winner.py`: adaptación
  de audio/nombre con límites propios. No sustituir bancos por número sin loader.

Para nuevas importaciones usar [pipeline](character-pipeline.md) y
[entradas alternativas](character-alternate-entries.md). No copiar el parche de
cabeza a Strike: el inventario Strike demuestra enlaces coincidentes y conserva DBI stock.

## Evidencia, no una nueva aceptación

Los resultados Heat anteriores (pasos, defensa, fever, voces, popups y cache)
están preservados en [registro histórico](archive/bag1-character-before-audit.md).
Consultar la sección concreta y verificar sus inputs/runtime/hashes antes de reutilizar.
No se reejecutaron esas capturas durante esta auditoría documental.

Las partidas nuevas Strike vs Heat en [Strike](strike-recovery.md) acreditan su
flujo indicado; no certifican automáticamente todo el movimiento/audio Heat.
El estado global Heat conserva gaps de transiciones/dueto; no etiquetar el conjunto
como «completo» porque una versión resumida antigua lo hacía.
