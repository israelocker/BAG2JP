---
id: tool-evidence-spimdisasm
title: "Evidencias: spimdisasm"
tags: ["tools", "evidence"]
summary: "Historial de spimdisasm; ayuda comprobada, desensamblado PSX pendiente."
related: ["notes/assets.md"]
created: "2026-11-06"
updated: "2026-11-06"
doc_kind: evidence
---

# spimdisasm — historial

Aplicar [criterios y plantilla](../assets.md#clasificación-y-medición-obligatorias).

## 20261106-spimdisasm-001 — antecedente de instalación
- Tipo: arranque histórico; transcrito el 2026-11-06, no reejecutado.
- Versión: 1.42.4, Python 3.13 aislado; comando exacto en
  `D:/Dev/Tools/ps1-community/smoke-results.json`, objeto `spimdisasm`.
- Entradas: `--help`, sin binario; región/base/módulo no aplican.
- Observado: salida 0; no hubo desensamblado ni contraste de instrucciones.
- Evidencia: reporte anterior, `installation-manifest.json` y
  `_work/tool-install/spimdisasm-help.log`; procedencia en reporte PyPI conservado.
- Dictamen: **inconcluso** para utilidad BAG2JP; solo ayuda CLI.
- Medición: tiempos y ahorro no medidos; sin referencia comparable.
- Siguiente: rango MIPS I identificado con hash, base y región; contrastar Ghidra.
