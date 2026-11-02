---
id: agent-handoff
title: "BAG2JP Agent Handoff"
tags: ["handoff", "resume", "context"]
summary: "Guía para retomar el trabajo entre agentes sin reconstruir el proyecto desde cero"
related: ["AGENTS.md", "NOTES.md", "CHARACTER_IMPORT.md", "IMPORT_STANDARD.md", "_work/current-state.json"]
created: "2026-10-31"
updated: "2026-11-01"
---

# BAG2JP Agent Handoff

## Cómo Retomar el Trabajo

**Repositorio canónico**: `D:/Dev/Recomp/BAG2JP`

**Orden de lectura para un chat nuevo**:

1. `AGENTS.md` - Políticas y workflow del proyecto
2. `NOTES.md` - Índice actual con summaries de frontmatter
3. `_work/current-state.json` - Estado compacto con campo `gaps` (qué necesita atención)
4. Nota temática de la tarea específica (solo si es necesaria)

**Este archivo NO sustituye** `notes/bag1-character.md`, `notes/bag1-stage-song.md` ni `notes/character-pipeline.md`. Abrir solo la nota relevante para la tarea actual.

## Estado del Proyecto (Resumen)

| Área | Estado |
|------|--------|
| Heat BAG1 import | Completado con adaptaciones documentadas |
| Stage Heat port | Completado y verificado |
| Online/netplay | Configurado, pendiente test 2 PCs reales |
| Audio latency | buffer_ms 90, objetivo 50 ms |
| Ending View | HD menu implementado, aceptación parcial |
| Character pipeline | Compartido, Heat validado, Strike inventory only |

## Próximos Pasos Identificados

1. Próximo character import (después de completar Heat workflow y validación)
2. Cambios que requieran aprobación explícita del owner
3. Test de online entre 2 PCs reales en redes diferentes
4. Remover song-start stall en audio (buffer 50 ms objetivo)

## Comandos de Inicio Rápido

```powershell
# Verificar estado actual
py tools/bag1import/character_workflow.py validate-profile --profile tools/bag1import/profiles/heat.json
py tools/bag1import/character_workflow.py plan --profile tools/bag1import/profiles/heat.json

# Medir contexto de inicio
py tools/workflow/measure_context.py

# Ejecutar mantenimiento completo
py tools/workflow/maintenance_check.py
```

## Reglas de Retomada

- **No reconstruir** el proyecto desde conversaciones anteriores
- **No presuponer** orquestación simultánea entre agentes
- **Leer solo** lo necesario: índice + estado + nota relevante
- **Verificar** rutas y hashes antes de copiar archivos
- **Medir** duración real sin prometer ahorros no medidos

## Referencias Rápidas

- `CHARACTER_IMPORT.md` - Manual canónico de importación
- `IMPORT_STANDARD.md` - Guía de tarea estándar para importación
- `NOTES.md` - Índice con summaries por nota
- `_work/current-state.json` - Estado actual compacto
- `tools/workflow/bag2_workflow.py` - Helper de workflow (preflight, build, test, report)
