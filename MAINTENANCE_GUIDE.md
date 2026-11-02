---
id: documentation-maintenance
title: "Mantenimiento documental verificable"
tags: ["documentation", "maintenance"]
summary: "Validación estructural, evidencia por tipo y actualización de resúmenes sin reejecutar gameplay innecesariamente."
related: ["NOTES.md", "docs/coding-standards.md", "notes/documentation-audit.md"]
created: "2026-11-02"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: requirements
---

# Mantenimiento de documentación

1. Identificar fuente canónica del tema en `NOTES.md`. Actualizarla, no crear
   otra versión `clean`/`optimized`. Conservar hechos históricos únicos aparte.
2. Marcar cada afirmación como hecho con evidencia/alcance, requisito,
   propuesta o histórico. No convertir una intención en funcionalidad.
3. Actualizar fecha, resumen y enlaces afectados. Un digest declara `source`
   y `source_sha256`; revisar su contenido antes de renovar el hash.
4. Ejecutar desde el repositorio:

```powershell
py -3.13 tools/workflow/test_audit_docs.py
py -3.13 tools/workflow/audit_docs.py check --output _work/docs-audit/current.json
```

El checker no ejecuta ejemplos ni visita URLs. Verifica estructura, rutas locales
y hashes declarados; no certifica semántica, opciones CLI o aceptación en juego.
Las referencias externas/temporales se contrastan en el task que las necesita.

Solo los cambios de comportamiento requieren sus tests y aceptación real.
Una edición de Markdown no exige arrancar el juego. No usar `--fix` masivo
ni regenerar resúmenes a ciegas. Los scripts antiguos de mantenimiento se
conservan, pero no sustituyen revisión ni prueban ahorro de tokens.

## Medición

`audit_docs.py inventory` registra bytes UTF-8 de conjuntos concretos de inicio
general/importación. No son tokens facturados. Comparar el mismo conjunto antes
y después; no comparar arbitrariamente una nota con todo el repositorio.
Las cifras aproximadas de AGENTS son objetivos históricos, no medición vigente.

Original preservado, **no receta activa**:
[guía anterior](docs/archive/MAINTENANCE_GUIDE-20261101.md).
