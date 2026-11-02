---
name: "bag1-import"
description: "Importar o corregir contenido BAG1 en BAG2JP con inventario específico, pipeline compartido y aceptación por evidencia."
---

# BAG1 a BAG2JP

Seguir `AGENTS.md`, `NOTES.md` y el estado local; para importación leer el índice
`IMPORT_STANDARD.md`. No cargar todas las notas. Usar bag-character-pipeline,
bag-animation-matching y bag-reference-cache en su fase correspondiente.

- Reglas/contratos: `CHARACTER_IMPORT.md` y `notes/character-pipeline.md`.
- Bytes exactos, DFS y staging: `notes/character-alternate-entries.md`.
- Calibración/matriz/final/retorno: `notes/character-import-testing.md`.
- Adaptadores históricos Heat: `notes/bag1-character.md` y `notes/bag1-stage-song.md`.
- Estado Strike: `notes/strike-recovery.md`; no aceptación final.

No clonar build_heat_test ni aplicar patch_heat_dbi a otro personaje sin evidencia.
Igual número de request no significa igual rol. Identificar tablas del disco real,
conservar imports/mods existentes, no truncar entradas, no auto-deploy desde prepare.
No inferir existencia de VM, herramienta conectada o captura vigente por una ruta.
Usar las herramientas disponibles del harness actual, no nombres históricos de otro.
Fuentes propias en mods-src; framework fijado y parches reproducibles. Solo experimental,
tarjetas/config aisladas y proceso propio; GPU del juego separada de modelos locales.
Histórico de esta skill en `agent-skills/archive/`; no es receta operativa.
