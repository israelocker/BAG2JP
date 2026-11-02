---
id: model-routing
title: "Recursos y contexto mínimo"
tags: ["workflow", "context", "resources"]
summary: "Aplicación de preferencias del propietario sin porcentajes de ahorro ni telemetría inventados."
related: ["AGENTS.md", "MAINTENANCE_GUIDE.md", "notes/documentation-audit.md"]
created: "2026-11-02"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: requirements
---

# Recursos

Aplicar el routing definido por el propietario en AGENTS; no repetir aquí sus
tablas. Hashes, existencia, conteos, extracción y comparación exacta se resuelven
con scripts deterministas, no pidiendo inferencias a un modelo.

Modelos locales: solo trabajo acotado y revisable si mejora el coste total.
Juicio difícil, semántica y aceptación permanecen con el agente principal.
Un modelo GPU a la vez y separado de pruebas del juego. No cambiar proveedor,
instalar dependencias o abrir agentes simplemente para usar todos los recursos.

## Qué se mide realmente

- `audit_docs.py inventory`: bytes UTF-8 de archivos y conjuntos de contexto
  explícitos; incluye archivos que faltan en el conjunto, no los cuenta como cero
  sin avisar. No estima tokens del modelo ni coste de una sesión.
- `measure_context.py`: suma histórica de archivos con un conjunto fijo que
  incluye importación aunque la tarea no sea de importación. No mide contexto
  efectivo del harness ni prueba ahorro frente a leer todo notes.
- `token-report.py`: estimación por longitud/4, no telemetría de facturación
  ni conteo real de tokens. Su nombre no certifica medición de sesiones.
- `generate_digests.py`: extrae encabezados y decide frescura por mtime; no
  verifica semántica y puede sobrescribir resúmenes manuales. No recomendar `--all`.

Los antiguos objetivos «60–90%», «8 KB» o «30–45 minutos» sin comparación no son
resultados. Registrar método, conjunto y alcance antes/después, sin inventar ahorro.
