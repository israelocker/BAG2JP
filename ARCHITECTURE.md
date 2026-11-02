---
id: architecture
title: "Arquitectura: límites y fuentes comprobables"
tags: ["architecture", "reference"]
summary: "Mapa del repositorio y build separado; no especifica APIs del framework sin consultar su fuente fijada."
related: ["AGENTS.md", "docs/paths.md", "notes/character-alternate-entries.md", "notes/project.md"]
created: "2026-11-02"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: reference
---

# Arquitectura

## Fuentes contrastadas

- `tools/workflow/bag2_workflow.py`: repositorio canónico, build separado,
  instalación experimental, pins y diagnóstico de drift. El helper no sincroniza.
- `patches/BAG2JP-CMakeLists.txt`, `patches/BAG2JP-game.toml`: cambios reproducibles
  del título. Consultar el árbol efectivo de build y pins antes de una edición.
- `mods-src/`: fuentes/manifest de mods del título. Framework/launcher se
  mantienen fijados; cambios locales de framework se conservan como patches.
- `tools/bag1import/`, `tools/test/`: conversión/candidatos y harness de evidencia.
- `notes/`: estado/recetas; `notes/archive/` y `docs/archive/`: histórico sin
  autoridad operativa. No son entradas adicionales de contexto por defecto.

## Integración BAG1 comprobada

El plugin `mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_versions.c` selecciona
versiones por entrada mediante tabla DF2_ en RAM. El índice conserva metadatos
stock y alternativos; overlay del paquete aporta bytes en DUMMY sin sobrescribir
el disco original. La receta y límites están en
[entradas alternativas](notes/character-alternate-entries.md).

El build nativo consume fuentes de otro directorio, no directamente de mods-src.
El hash del ejecutable desplegado identifica el runtime probado. Un paquete
puede estar presente sin estar seleccionado: comprobar estado y logs del run.

## Lo que este mapa no certifica

No se afirma ausencia universal de interpretación/emulación por llamarlo
«recompilación estática». No se inventa un esquema de manifest ni una API de
plugins. Consultar los headers/parser del framework fijado para cada cambio.
Tampoco se acredita funcionamiento online por una prueba local de dos jugadores.

El [documento anterior](docs/archive/ARCHITECTURE-before-audit.md) conserva
diagramas/ejemplos históricos; no usar sus estructuras/API como contrato vigente.
