---
id: project-builds-folder
title: "Proyecto: entorno y build vigentes"
tags: ["project", "build", "saves"]
summary: "Comandos del helper verificados y límites del staging; historial de releases separado."
related: ["AGENTS.md", "docs/paths.md", "notes/character-alternate-entries.md"]
created: "2026-10-26"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: reference
---

# Build y conservación

Fuente: `tools/workflow/bag2_workflow.py`, contrastada con preflight durante
la auditoría. Rutas efectivas en [paths](../docs/paths.md), políticas en AGENTS.

```powershell
$PY='D:/Dev/Tools/ghidra-mcp-python/python.exe'
& $PY tools/workflow/bag2_workflow.py preflight --tag <task>
& $PY tools/workflow/bag2_workflow.py build --tag <task>
```

Build usa WSL Ubuntu y el script local llvm-mingw fijado con dos jobs. Conservar
el proceso y leer el resultado, no iniciar builds paralelos para compensar una
espera. Logs/métricas quedan en `_work/workflow/`.

El helper compara fuentes, recursos, pins y exe desplegado; **no sincroniza**.
Antes de compilar usar el staging explícito de
[integración](character-alternate-entries.md). No copiar drift ajeno.
Un test solo se acredita con su resultado y alcance: build verde ≠ gameplay.

Saves/config son del usuario. No usar plantillas como estado vivo ni modificar
la instalación estable. Runner externo: `D:/Dev/Tools/winshot/bag2_run.ps1`;
reporter: `tools/test/bag2_report.py`. Para la navegación soportada usar el
harness con [gates observados](character-import-testing.md).

## Snapshot

`BAG2JP-project-snapshot.tar.gz` se conserva fuera de Git y se obtiene del árbol
de build sin directorios de compilación. Incluir docs/herramientas canónicas
actualizadas; verificar hashes internos antes de reemplazar el snapshot y
conservar el anterior. El snapshot no garantiza todos los assets/evidencias de
`_work/`: comprobarlos por separado. No extraerlo sobre un árbol con cambios.

[Historial anterior](archive/project-before-audit.md): versiones, paths VM y
configuraciones de octubre no describen automáticamente la instalación actual.
