---
id: tool-evidence-timedit
title: "Evidencias: TIMedit"
tags: ["tools", "evidence"]
summary: "Historial de TIMedit; ventana vacía comprobada, TIM BAG no evaluados."
related: ["notes/assets.md"]
created: "2026-11-06"
updated: "2026-11-13"
doc_kind: evidence
---

# TIMedit — historial

## 2026-11-13 — HUD BAG2: omisión justificada del GUI

- Necesidad: copiar índices nativos exactos de G/A/S/guion/O conservando las paletas
  corporales. No se abrió TIMedit: una vista con la primera CLUT del TIM no representa
  la CLUT compartida que usa el HUD y no demuestra exclusión UV del modelo.
- Alternativa ejecutada: compositor 4bpp determinista, ocho variantes regionales/lado/
  traje, pruebas píxel a píxel/paletas y 18 contenedores auditados. Fuentes identificadas
  en `tools/bag1import/profiles/gaso.json`; hashes de candidatos en
  `_work/gaso/hud/bag2-font/corrected/audit.json`.
- Resultado: no evaluado con TIMedit en este ensayo; no se atribuyen ahorros. Exclusión
  corporal y CLUT efectiva en juego siguen pendientes. Siguiente: auditoría del renderer,
  no una previsualización engañosa de color.

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

## 20261113-timedit-002 — omisión motivada, nombre HUD Gas-O

- Pertinente por tratarse de TIM4bpp. No se abrió la GUI: la pregunta de seguridad
  (nibbles/rectángulo/CLUT/copia colateral) se verifica determinísticamente con
  `py -3.13 -m unittest tools.test.test_tim_label tools.test.test_gaso_hud`:
  12tests verdes, ocho packs regionales y cinco mutantes con fallo de aserción.
- Inputs/hashes: `_work/gaso/hud/final-source-hashes.json`; arte fuente member5
  USA1e403c65097b…, JPb7fd7a8d6699…; mismo arte por ambos trajes/lados.
  Preview generado con Pillow instalado usando la paleta stock de referencia,
  no un volcado de CLUT efectivo del juego. No prueba color/legibilidad reales.
- No cuenta como uso de TIMedit ni como ahorro medido. La GUI no resolvería qué
  CLUT compartido selecciona el runtime; sigue pendiente comprobarlo. Sin partida,
  sin editar originales; candidato en `_work/gaso/hud/final-build/`.
