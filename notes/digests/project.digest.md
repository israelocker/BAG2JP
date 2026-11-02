---
id: project-digest
title: "Build: ruta compacta"
tags: ["digest", "build"]
summary: "Build fijado con staging explícito y evidencia por hash."
related: ["notes/project.md"]
created: "2026-11-02"
updated: "2026-11-02"
doc_kind: digest
source: "notes/project.md"
source_sha256: "b74669c00a49d676c49c1cfda5572af45af08728577bb728852a940885823ca4"
---

Preflight diagnostica, no sincroniza. Build WSL con dos jobs, copiar solo fuentes/
recursos propios y verificar hash del exe/paquete. No tocar estable. Snapshot no
incluye automáticamente toda evidencia local. [Fuente](../project.md).
