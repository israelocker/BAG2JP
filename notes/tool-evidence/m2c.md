---
id: tool-evidence-m2c
title: "Evidencias: m2c"
tags: ["tools", "evidence"]
summary: "Historial de m2c; ayuda comprobada, C de funciones BAG no evaluado."
related: ["notes/assets.md"]
created: "2026-11-06"
updated: "2026-11-06"
doc_kind: evidence
---

# m2c — historial

Aplicar [criterios y plantilla](../assets.md#clasificación-y-medición-obligatorias).

## 20261106-m2c-001 — antecedente de instalación
- Tipo: arranque histórico; transcrito el 2026-11-06, no reejecutado.
- Versión: commit `c632946b8cfbe8fce442b522dba92dfa72f1f317`, Python 3.13
  aislado; comando exacto en `D:/Dev/Tools/ps1-community/smoke-results.json`.
- Entradas: `--help`, sin función; región/base/módulo no aplican.
- Observado: salida 0; ningún C generado ni comparación independiente.
- Evidencia: objeto `m2c` del reporte, manifiesto en la misma raíz y
  `_work/tool-install/m2c-help.log`.
- Dictamen: **inconcluso** para utilidad BAG2JP; solo ayuda CLI.
- Medición: tiempos y ahorro no medidos; sin referencia comparable.
- Siguiente: función MIPS delimitada y con hash; revisar tipos, control de flujo
  y accesos con Ghidra. C legible no demuestra equivalencia ni fuente original.
