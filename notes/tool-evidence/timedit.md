---
id: tool-evidence-timedit
title: "Evidencias: TIMedit"
tags: ["tools", "evidence"]
summary: "Historial de TIMedit; ventana vacía comprobada, TIM BAG no evaluados."
related: ["notes/assets.md"]
created: "2026-11-06"
updated: "2026-11-06"
doc_kind: evidence
---

# TIMedit — historial

Aplicar [criterios y plantilla](../assets.md#clasificación-y-medición-obligatorias).

## 20261106-timedit-001 — antecedente de instalación
- Tipo: arranque GUI histórico; transcrito el 2026-11-06, no reejecutado.
- Versión: 0.10a Windows, ejecutable
  `D:/Dev/Tools/ps1-community/timedit-0.10a/timedit.exe`.
- Entrada: ventana vacía en carpeta de prueba; ningún TIM ni región/módulo.
- Observado: ventana visible a los 3 segundos, cerrada únicamente la instancia
  de prueba; salida 0. No se editaron assets ni se contrastaron CLUT/STP.
- Evidencia: `D:/Dev/Tools/ps1-community/smoke-results.json`, objeto `TIMedit`,
  incluye SHA-256 del ejecutable. Es hash local, no autenticación upstream.
- Dictamen: **inconcluso** para utilidad; abrir la GUI no valida texturas.
- Medición: 3 segundos es espera de observación, no benchmark; ahorro no medido.
- Siguiente: inspeccionar una copia TIM con hash y contrastar píxeles/CLUT/STP.
