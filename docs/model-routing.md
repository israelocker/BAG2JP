---
id: model-routing
title: "Recursos y contexto mínimo"
tags: ["workflow", "context", "resources"]
summary: "Aplicación de preferencias del propietario sin porcentajes de ahorro ni telemetría inventados."
related: ["AGENTS.md", "MAINTENANCE_GUIDE.md", "notes/documentation-audit.md"]
created: "2026-11-02"
updated: "2026-11-15"
edited: "2026-11-15"
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

## Optimización de OpenCode (observación histórica 2026-11-04)

Configuración observada en esa fecha, no garantía sobre el harness o catálogo de
una sesión posterior. No instalar, cambiar plugins/configuración ni ejecutar
acciones de gestión de contexto a partir de esta nota. Prevalecen las herramientas,
modos y permisos explícitos de la sesión; un recordatorio no es autorización.

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
- En aquella configuración se describió poda/compactación por rangos. Su uso está
  sujeto al modo y autorización del harness actual; no asumir ejecución automática
  ni permiso de comprimir por ver metadatos. Cualquier ajuste sigue requiriendo
  alcance autorizado y medición real, no esta observación histórica.

Los antiguos objetivos «60–90%», «8 KB» o «30–45 minutos» sin comparación no son
resultados. Registrar método, conjunto y alcance antes/después, sin inventar ahorro.

## Equipos de agentes (2026-11-19)
Para trabajo con varias líneas paralelas o secuenciales usar la skill compartida `team-orchestration-opencode` (adapta wshobson/agents agent-teams a `subagent`, plan en `_work/<tema>/plan.md` y enrutado: Opus/Sonnet investigan, Sonnet/GPT-6.1-terra implementan, Haiku/DeepSeek Flash buscan, modelos locales hacen lo mecánico de uno en uno). AGENTS.md prevalece; los subagentes no prueban en juego, no despliegan ni hacen commit.

### Reparto fijo de modelos (owner 2026-11-19)
Cada lanzamiento de subagente indica su modelo y el informe dice qué modelo hizo qué. Capacidades según conocimiento general, no medidas en el proyecto.

| Rol | Principal | Alternativa |
|---|---|---|
| Coordinación y aceptación | claude-agent/opus | — |
| Ingeniería inversa difícil (Ghidra, formatos) | openai/gpt-6.1-sol (high) | claude-agent/opus (high) |
| Implementación con especificación conocida | claude-agent/sonnet (medium) | openai/gpt-6.1-terra (medium) |
| Trabajo mecánico en bloque | claude-agent/haiku | ollama/qwen3-coder:30b (serie) |
| Búsqueda / resumen / conteo | claude-agent/haiku | ollama/qwen3-coder:30b |
| Revisión Goldfish (otra familia que el autor) | openai/gpt-6.1-sol | claude-agent/sonnet, u opus si el autor fue Sonnet |

Prueba GPT principal (owner 2026-11-21): 3–4 tareas midiendo tiempo, retrabajo y errores antes de fijarlo. Si GPT falla (sin tokens, error de conexión), se usa la alternativa automáticamente y el informe lo declara. deepseek-flash dio ECONNREFUSED repetidos el 2026-11-21: queda fuera hasta nueva prueba.
| Inspección de imágenes/fotogramas | claude-agent/sonnet | nvidia/nemotron-3.5-super-vl |

Excluidos: `google/antigravity-*` (Gemini y Claude vía Antigravity) y `deepseek/deepseek-v4-pro` (sin tokens de pago), por decisión del owner; gratuitos `opencode/*-free` y `nvidia/*` solo para tareas no sensibles tras prueba; versiones antiguas de Claude y Fable sin evaluar. Ollama: un modelo GPU a la vez y nunca durante pruebas de juego.
