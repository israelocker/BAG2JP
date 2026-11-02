---
id: project-paths
title: "Rutas locales y propiedad de archivos"
tags: ["paths", "config"]
summary: "Rutas del entorno autorizado y diferencia entre origen, build, instalado y datos generados."
related: ["AGENTS.md", "notes/project.md", "system_config.md"]
created: "2026-11-02"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: reference
---

# Rutas del entorno BAG2JP

Rutas de esta máquina, no defaults portables. Autoridad: AGENTS y constantes
de `tools/workflow/bag2_workflow.py` contrastadas en el preflight de la auditoría.

| Propósito | Ruta |
|---|---|
| Canónico | `D:/Dev/Recomp/BAG2JP` |
| Build | `D:/Dev/Recomp/BAG2JP-codex-build/BAG2JP` |
| Experimental | `D:/Games/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb` |
| Estable protegida | `D:/Games/Bust A Groove 2 (Japan)/BAG2JP-win` |
| Runner externo | `D:/Dev/Tools/winshot/bag2_run.ps1` |
| Python workflow/build | `D:/Dev/Tools/ghidra-mcp-python/python.exe` |
| Python capturas/host tests | `py -3.13` |

`mods-src/` es origen canónico; build consume `src/` y
`mods/preloaded/packages/`. Salidas: `build-win-codex/BAG2JP.exe` y
`build-win-codex/mods/bundled/`. Su sincronización es explícita, no automática.

`_work/` y assets pesados están ignorados por Git. Evidencia conservada allí no
está garantizada en un clone/snapshot: comprobar existencia y hash al reutilizar.
Las dos grafías históricas `_work/character_import` y `_work/character-import`
existen para Strike; no renombrar datos a ciegas ni copiar esas rutas como estándar.

No duplicar rutas/configuración personal dentro de perfiles reutilizables. Para
otro equipo, validar ubicaciones efectivas antes de sustituirlas. El hecho de que
una herramienta esté instalada no demuestra que su servicio esté ejecutándose.
