---
id: model-routing
title: "Recursos y contexto mínimo"
tags: ["workflow", "context", "resources"]
summary: "Aplicación de preferencias del propietario sin porcentajes de ahorro ni telemetría inventados."
related: ["AGENTS.md", "MAINTENANCE_GUIDE.md", "notes/documentation-audit.md"]
created: "2026-11-02"
updated: "2026-11-04"
edited: "2026-11-04"
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

- `opencode stats --days 14 --project . --models --tools --cost`: tokens reales
  por proyecto según OpenCode (entrada, salida, caché, herramientas).
- `/context`, `/context-breakdown`, `/context-diff` (plugin
  `opencode-context-indicator`): reparto del contexto por categoría y salidas
  duplicadas; estimación heurística, no tokenizer.
- `/dcp stats` (plugin `@tarquinen/opencode-dcp`): ahorro de la poda en la sesión.

## Optimización de OpenCode (configurada 2026-11-04)

Se aplica sola en cada sesión nueva; no requiere pasos del agente.

- `.opencode/opencode.json` (versionado): `policies` ocultan skills y MCP ajenos
  al port (Sanity, Fastly, Bright Data, Auth0, SEO, marketing…) y
  `compaction.buffer: 750000` adelanta la compactación en modelos de 1M (~250k).
- Global `~/.config/opencode/opencode.json` (fuera de Git): plugins fijados
  `@tarquinen/opencode-dcp@3.2.0` (poda de salidas obsoletas) y
  `opencode-context-indicator@1.8.2` (medición). Verificados activos en 2.2.5.
- Descartados por incompatibles con la API V2 de plugins: `openslimedit@1.0.4`,
  `@ramtinj95/opencode-tokenscope@1.8.1`, `opencode-context-usage@0.3.1`.
  Probar candidatos nuevos con `D:/Dev/Tools/opencode-plugin-test/test_plugin.ps1
  -WaitSeconds 90 <pkg@ver>` antes de instalarlos.
- Si el agente ve recordatorios de DCP, comprimir solo rangos cerrados; mantener
  sin comprimir la tarea activa. Ajustar DCP solo con cifras de `/dcp stats`.

Los antiguos objetivos «60–90%», «8 KB» o «30–45 minutos» sin comparación no son
resultados. Registrar método, conjunto y alcance antes/después, sin inventar ahorro.
