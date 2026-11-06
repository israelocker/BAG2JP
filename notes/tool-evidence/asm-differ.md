---
id: tool-evidence-asm-differ
title: "Evidencias: asm-differ"
tags: ["tools", "evidence"]
summary: "Historial de asm-differ; ayuda requiere configuración, comparación pendiente."
related: ["notes/assets.md"]
created: "2026-11-06"
updated: "2026-11-06"
doc_kind: evidence
---

# asm-differ — historial

Aplicar [criterios y plantilla](../assets.md#clasificación-y-medición-obligatorias).

## 20261106-asm-differ-001 — antecedente con fallo y comprobación acotada
- Tipo: arranque histórico; transcrito el 2026-11-06, no reejecutado.
- Versión: commit `0dd09af8f8008f1f880327cf0aca3b26d2562ea2`, Python 3.13.
- Entradas: `--help`, sin binarios; región/módulo no aplican.
- Observado: primera salida 1, `Unable to find diff_settings.py in the same
  directory.` La fuente carga configuración antes del parser. Con fixture
  de configuración de ayuda, salida 0; el fixture prohíbe comparaciones reales.
- Evidencia: `D:/Dev/Tools/ps1-community/smoke-results.json` conserva el fallo;
  `asm-differ-smoke.json` en esa misma raíz conserva la comprobación posterior.
  Logs: `_work/tool-install/asm-differ-help.log` y
  `_work/tool-install/asm-differ-help-configured.log`.
- Contraste: lectura del requisito de configuración, no comparación MIPS real.
- Dictamen: **inconcluso** para utilidad; precondición identificada, no evidencia
  suficiente para calificar la herramienta como contraproducente.
- Medición: tiempos, retrabajo y ahorro no medidos.
- Siguiente: configurar por tarea y verificar backend GNU objdump MIPS (pendiente).
  Comparar MIPS con MIPS, no con el ejecutable host recompilado.
