---
id: project-digest
title: "Build: ruta compacta"
tags: ["digest", "build"]
summary: "Build fijado con staging explícito y evidencia por hash."
related: ["notes/project.md"]
created: "2026-11-02"
updated: "2026-11-15"
doc_kind: digest
source: "notes/project.md"
source_sha256: "dcc3ec4740ea91be60cbb722dec19cb23e678f24e6d56d8998d4257de5e47f53"
---

Preflight diagnostica, no sincroniza. Build WSL con dos jobs, copiar solo fuentes/
recursos propios y verificar hash del exe/paquete. No tocar estable. Snapshot no
incluye automáticamente toda evidencia local. [Fuente](../project.md).
Actualizar snapshot solo en hitos verificados según AGENTS, no por Markdown o
checkpoints intermedios. El inventario/limpieza del13-11 es histórico y acotado;
no autoriza borrar más grabaciones, backups, fuentes, sesiones ni saves.
