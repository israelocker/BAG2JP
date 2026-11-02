---
id: agent-handoff
title: "Retomar sin repetir trabajo"
tags: ["handoff", "workflow"]
summary: "Estado y evidencia por task; no contiene otra tabla mutable del estado de todo el proyecto."
related: ["AGENTS.md", "NOTES.md", "notes/documentation-audit.md", "notes/strike-recovery.md"]
created: "2026-10-31"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: requirements
---

# Retomar

Aplicar el inicio de AGENTS. Leer `active_task` y gaps en estado local, y solo
la fuente del tema en NOTES. Si no existe `_work/current-state.json`, usar la
nota persistente; no regenerarlo con un perfil Heat sobre el estado Strike.

Antes de repetir un check: ¿cambió su input/runtime o hay nueva evidencia?
Si no, reutilizar el resultado con alcance/hash. Si hay contradicción entre
resumen y evidencia, verificar la fuente, no confiar en el texto más reciente.

Guardar por task: siguiente paso concreto, pendientes, commits, archivos propios
sin commit, hashes/evidencia y estado de procesos. No copiar tablas de estado
en CONTRIBUTING/índices/varios resúmenes. Preservar configuración y trabajo ajeno.

Histórico separado: [handoff anterior](archive/agent-handoff-before-audit.md).
Sus «Strike inventory only», latencias objetivo y próximos pasos ya no son
estado actual certificado.
