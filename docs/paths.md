---
id: project-paths
title: "Rutas locales y propiedad de archivos"
tags: ["paths", "config"]
summary: "Rutas del entorno autorizado y diferencia entre origen, build, instalado y datos generados."
related: ["AGENTS.md", "notes/project.md", "system_config.md"]
created: "2026-11-02"
updated: "2026-11-15"
edited: "2026-11-15"
doc_kind: reference
---

# Rutas del entorno BAG2JP

Rutas de esta máquina, no defaults portables. Autoridad operativa para los
consumidores migrados: configuración común/local y resolutor `project_config.py`,
con los límites de permisos de AGENTS; esta tabla es el registro humano.

| Propósito | Ruta |
|---|---|
| Canónico | `D:/Dev/Recomp/BAG2JP` |
| Build | `D:/Dev/Recomp/BAG2JP-codex-build/BAG2JP` |
| Experimental | `D:/Games/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb` |
| Estable protegida | `D:/Games/Bust A Groove 2 (Japan)/BAG2JP-win` |
| Runner externo | `D:/Dev/Tools/winshot/bag2_run.ps1` |
| Python workflow/build | `D:/Dev/Tools/ghidra-mcp-python/python.exe` |
| Python capturas/host tests | `py -3.13` |

Desde 2026-11-15, las ubicaciones de build, instalaciones, runner, intérpretes y
herramientas viven en el archivo local ignorado `config/project.local.toml`,
resueltas y validadas por `tools/workflow/project_config.py`. `repo_root` es
derivado y no se configura; `py -3.13` es el intérprete elegido en la línea de
comandos, no un campo. Esta tabla sigue siendo el registro humano y el mapa de
equivalencia de cada valor se conserva en `_work/configuration/` (evidencia no
versionada, comprobar antes de reutilizarla en otro clone). El checker de
manifiestos ya deriva sus cuatro copias de esa configuración y comprobó 4/4 en
esta máquina. `paths.tools_root`, `tools.ffmpeg_review` y `tools.ffmpeg_wgc` no
tienen valor verificado y permanecen sin configurar. Campos, unidades y
consumidores: [diccionario de datos](data-dictionary.md).

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
