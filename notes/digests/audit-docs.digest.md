---
id: audit-docs-digest
title: "Checker documental: capacidades y límites"
tags: ["digest", "documentation", "testing"]
summary: "Inventario read-only de Markdown propio; estructura y procedencia, no certificación semántica."
related: ["MAINTENANCE_GUIDE.md", "notes/documentation-audit.md"]
created: "2026-11-02"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: digest
source: "tools/workflow/audit_docs.py"
source_sha256: "59f10909119645f23374b491c7287d573c96ee4872da5092ee8edca2cada3e08"
---

# Checker

`inventory`/`check`, `--root` opcional, `--output <report.json>` opcional.
Sin red ni ejecución de ejemplos. Excluye generated/build/terceros y conserva
archivos propios ocultos. Archivo de salida solo JSON, no Markdown.

Comprueba frontmatter local, arrays/fechas/IDs duplicados, fences, enlaces de
archivo y paths literales seleccionados; digests requieren source/hash vigente
dentro de root. El histórico emite advertencias sin certificar sus afirmaciones.

Reporta hashes por documento, bytes activos/totales y conjuntos de contexto
explícitos. Inventario vacío no produce check verde. No es YAML/CommonMark completo,
no verifica todas las anclas/opciones CLI y no mide tokens facturados ni gameplay.
32 regresiones en `tools/workflow/test_audit_docs.py`. Abrir fuente solo para
cambiar el checker o investigar un desacuerdo del informe.
