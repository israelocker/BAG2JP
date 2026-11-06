---
id: tool-evidence-dumpsxiso
title: "Evidencias: dumpsxiso"
tags: ["tools", "evidence"]
summary: "Historial de dumpsxiso; ayuda comprobada, extracción BAG pendiente."
related: ["notes/assets.md"]
created: "2026-11-06"
updated: "2026-11-06"
doc_kind: evidence
---

# dumpsxiso — historial

Aplicar [criterios y plantilla](../assets.md#clasificación-y-medición-obligatorias).

## 20261106-dumpsxiso-001 — antecedente de instalación
- Tipo: arranque histórico; transcrito el 2026-11-06, no reejecutado.
- Versión: 2.30 Windows; comando exacto en
  `D:/Dev/Tools/ps1-community/smoke-results.json`, objeto `dumpsxiso`.
- Entradas: `--help`, sin disco; región/módulo no aplican.
- Observado: salida 0. Ninguna extracción real ni contraste independiente.
- Evidencia: reporte anterior, manifiesto de instalación en la misma raíz y
  `_work/tool-install/dumpsxiso-help.log`; manifiesto conserva hash del paquete.
- Dictamen: **inconcluso** para utilidad BAG2JP; solo ayuda CLI.
- Medición: tiempos y ahorro no medidos; referencia no ensayada.
- Siguiente: comparar extracción autorizada de copias raw/CUE con sectores y LBA
  del extractor local, sin confundir datos de 2048 bytes con XA/STR raw.
