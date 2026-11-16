---
id: character-workflow-digest
title: "Helper de perfil/cache: límites reales"
tags: ["digest", "workflow"]
summary: "CLI contrastado, schema de inicio y gates de prepare; no importador automático."
related: ["CHARACTER_IMPORT.md", "notes/character-pipeline.md"]
created: "2026-11-02"
updated: "2026-11-16"
doc_kind: digest
source: "tools/bag1import/character_workflow.py"
source_sha256: "982e90ec1c918fe785d13ff96ea73edcb0132a5c1dc9bb5cbf295c38472d6819"
---

Parser actual: `init-profile`, `validate-profile`, `plan`, `prepare`, `status`,
`acceptance-plan`, `cache-record`, `cache-check`; `--profile` obligatorio.
No existen acciones read-state/compact-status.

`init-profile` genera schema 1 con IDs por investigar. `plan`/`prepare` requieren
schema 2 y gaps resueltos, incluido `gameplay_evidence`. No inventar evidencia
para forzar primer candidato. `prepare` crea workspace/manifest, no despliega.
`status` no escribe estado; `plan` sí y `prepare` crea manifiesto/estado.

S5b1: todos los lectores de perfiles/firma/cache/plan/prepare/CLI usan
`inputs.bag1_reference_runtime` de un snapshot central único. El campo histórico
del perfil no es operativo ni obligatorio aquí; init-profile conserva su argumento
explícito. Operaciones puras solo exigen runtime, no workspace/stable.
Hash/cache dependen de bytes, no ubicación equivalente; runtime real e inputs
config protegidos. 68 tests host (67 PASS/1 skip), 3 mutantes AssertionError.
Goldfish limitado: 2 intentos locales, segundo no utilizable; no dos conformes.
No certifica otros lectores ni migra catálogo/assets/destinos cache/init.

S5b2: rutas declaradas de perfil/catálogo/assets con primer componente `_work` se
resuelven contra `paths.work_root`; el resto sigue relativo al repo. Rechaza
absolutas/ancladas, `..`, alias de puntos/espacios y resolución física fuera del
proyecto o de la raíz. `load_profile`, `_workspace_inputs`, `_profile_signature` y
`validate-profile` comparten el helper; `init_profile`, perfiles, cachés y lectores de
paquete sin migrar. 81 tests acotados (80 PASS, 1 skip), 5 mutantes causales.
Goldfish S5b2 utilizable con hallazgos: 4 confirmados y corregidos, 1 refutado.

Cache valida inputs y evidencia por hash. Hit no significa aceptación del paquete
ni sonido. No hay solver semántico/optimización de grafo implementado aquí.
