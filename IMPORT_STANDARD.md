---
id: character-import-standard
title: "Inicio mínimo de importación BAG1 a BAG2JP"
tags: ["bag1", "workflow", "index"]
summary: "Ruta de lectura por fase; no duplica el runbook ni convierte candidatos en importaciones aceptadas."
related: ["CHARACTER_IMPORT.md", "notes/character-pipeline.md", "notes/character-alternate-entries.md", "notes/character-import-testing.md"]
created: "2026-10-31"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: index
---

# Importación: empezar por la fase necesaria

Seguir AGENTS → NOTES → `_work/current-state.json`. Leer `active_task.gaps`
además de `gaps`: el estado global Heat no describe necesariamente Strike.
Si falta el estado local, consultar la nota canónica del personaje; no reconstruir
hechos a partir de un resumen de chat. No leer todas las notas al empezar.

| Necesidad | Fuente canónica |
|---|---|
| Reglas, perfil y aceptación | [CHARACTER_IMPORT.md](CHARACTER_IMPORT.md) |
| Contrato semántico, transiciones y cache | [Pipeline](notes/character-pipeline.md) |
| Reconstrucción DFS, payload y staging | [Entradas alternativas](notes/character-alternate-entries.md) |
| Calibración, lado/traje y canción completa | [Pruebas](notes/character-import-testing.md) |
| Estado/evidencia Strike | [Strike](notes/strike-recovery.md) |
| Historia Heat y adaptadores específicos | [Heat](notes/bag1-character.md) |

## Barreras que no se omiten

- Inventariar IDs, tablas, esqueletos y miembros del personaje/región reales.
- No copiar el pipeline Heat ni sus parches DBI por analogía.
- Mantener desconocidos sin resolver; igualar requests no prueba roles.
- Preservar imports/mods anteriores, saves y ajustes. Experimental únicamente.
- Candidato y cache hit no implican aceptación. Exigir los cuatro casos
  P1/A, P1/B, P2/A, P2/B y capacidades aplicables, final y retorno.
- Sincronizar explícitamente fuentes/recursos antes de build; preflight no copia.
- Validar bytes de DUMMY independientemente del guard defectuoso del generador.
- No prometer tiempos ni porcentajes de ahorro sin medición comparable.

Este índice no es un generador automático. El CLI `character_workflow.py` tiene
`status --profile <profile.json>`; no tiene acciones `read-state` o `compact-status`.
Comandos detallados, formatos y límites están en las fuentes enlazadas.
