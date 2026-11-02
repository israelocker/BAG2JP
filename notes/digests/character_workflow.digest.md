---
id: character-workflow-digest
title: "Helper de perfil/cache: límites reales"
tags: ["digest", "workflow"]
summary: "CLI contrastado, schema de inicio y gates de prepare; no importador automático."
related: ["CHARACTER_IMPORT.md", "notes/character-pipeline.md"]
created: "2026-11-02"
updated: "2026-11-02"
doc_kind: digest
source: "tools/bag1import/character_workflow.py"
source_sha256: "b1ef179841f711e8e0167458ff6d898e7913570752c731ef8faac3aacbe96d34"
---

Parser actual: `init-profile`, `validate-profile`, `plan`, `prepare`, `status`,
`acceptance-plan`, `cache-record`, `cache-check`; `--profile` obligatorio.
No existen acciones read-state/compact-status.

`init-profile` genera schema 1 con IDs por investigar. `plan`/`prepare` requieren
schema 2 y gaps resueltos, incluido `gameplay_evidence`. No inventar evidencia
para forzar primer candidato. `prepare` crea workspace/manifest, no despliega.
`status` puede guardar estado: no usarlo como probe read-only sobre el task ajeno.

Cache valida inputs y evidencia por hash. Hit no significa aceptación del paquete
ni sonido. No hay solver semántico/optimización de grafo implementado aquí.
