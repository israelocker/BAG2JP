---
id: character-import-standard
title: "Inicio mínimo de importación BAG1 a BAG2JP"
tags: ["bag1", "workflow", "index"]
summary: "Ruta de lectura por fase; no duplica el runbook ni convierte candidatos en importaciones aceptadas."
related: ["CHARACTER_IMPORT.md", "notes/character-pipeline.md", "notes/character-alternate-entries.md", "notes/character-import-testing.md"]
created: "2026-10-31"
updated: "2026-11-15"
edited: "2026-11-15"
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
| Lecciones Gas-O: proceso común frente a excepciones | [Retrospectiva incorporada](notes/character-pipeline.md#lecciones-de-gas-o-incorporadas-2026-11-15) |
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
- Validar CAUGHT en cada importado BAG1 y en todos los nativos BAG2: lados,
  variantes y compañeros. El fallo cerrado protege candidatos incompletos, no
  satisface el resultado final. Método y límites en el pipeline y las pruebas.
- Sincronizar explícitamente fuentes/recursos antes de build; preflight no copia.
- Validar bytes de DUMMY independientemente del guard defectuoso del generador.
- Al importar escenarios BAG1 a BAG2, no basta con la geometría, texturas y audio: es obligatorio importar y cablear las interacciones y eventos del escenario que avanzan con el puntaje (niveles de puntuación / eventos dinámicos del entorno, como ocurrió en Heat con la rotura de ventanas y en Strike con su progresión; directiva del propietario 2026-11-06).
- Importar cada personaje, canción y escenario BAG1 desde **ambos discos**, USA
  (`_work/bag1_disc_full`) y Japón (`_work/bag1jp_disc_full`, sin la censura
  americana), y ofrecer las dos variantes en la elección de versión del juego.
  Comparar miembro a miembro; si una región es idéntica, reutilizar sus bytes y no
  duplicar payload. Heat y Strike siguen solo con fuentes USA: pendiente tras Gas-O
  (directiva del propietario 2026-11-06, regla permanente).
- No prometer tiempos ni porcentajes de ahorro sin medición comparable.

Este índice no es un generador automático. El CLI `character_workflow.py` tiene
`status --profile <profile.json>`; no tiene acciones `read-state` o `compact-status`.
Comandos detallados, formatos y límites están en las fuentes enlazadas.
