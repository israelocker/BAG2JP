---
id: tool-evidence-pcsx-redux
title: "Evidencias: PCSX-Redux"
tags: ["tools", "evidence"]
summary: "Historial de PCSX-Redux existente; no se ejecutó ni validó para este flujo."
related: ["notes/assets.md"]
created: "2026-11-06"
updated: "2026-11-06"
doc_kind: evidence
---

# PCSX-Redux — historial

Aplicar [criterios y plantilla](../assets.md#clasificación-y-medición-obligatorias).
Complementario; no sustituye PSXRecomp nativo ni la aceptación en el juego.

## 20261106-pcsx-redux-001 — instalación existente, no uso
- Tipo: antecedente de inventario, transcrito el 2026-11-06.
- Ejecutable: `D:/Dev/Tools/pcsx-redux/pcsx-redux.exe`; versión funcional no
  comprobada. Hash inventariado en
  `D:/Dev/Tools/ps1-community/installation-manifest.json`.
- Entradas/comando: ninguno; no juego, región/módulo ni sesión de prueba.
- Observado: preservado; sin arrancar, actualizar, activar servidores o modificar
  tarjetas/configuración. No hay comprobación funcional ni contraste.
- Dictamen: **no ejecutado**; no inferir utilidad ni irrelevancia de su existencia.
- Medición: tiempos y ahorro no medidos.
- Siguiente: solo diagnóstico complementario pertinente/autorizado, con sesiones
  y tarjetas aisladas; comparar observación con referencia nativa.

## 20261120-pcsx-redux-002 - BAG1 USA, traza del resolver de movimientos
- Propósito: confirmar en el juego original la escalera de peticiones de BAG1,
  la tabla de fallos y el FINISH (análisis estático en
  `_work/move-roles/bag1/bag1-move-roles-report.md`).
- Comando: `pcsx-redux.exe -testmode -stdout -lua_stdout -debugger -interpreter
  -bios openbios.bin -iso "Bust A Groove (USA).cue" -run -dofile <lua>` con
  `SESSION_OUT`/`SESSION_FRAMES` (y `INJECT_CMD` en la última pasada). Scripts
  `_work/move-roles/bag1/redux/{smoke,trace2,trace3,trace4}.lua`; sin tarjetas.
- Región: SCUS principal; breakpoints de ejecución en 0x80030090 (resolver),
  0x80022130 (comando), 0x80022290 (esperado), 0x800222e0 (puerta FINISH),
  0x800220f4 (fallo), 0x800209a0 (entrada CPU), 0x800227b0 (tabla de fallos).
- Observado (demo de atracción, 5 ciclos con parejas distintas):
  intro 106→105→106→0; pasos 1,3,6,10,15,20,27 = esperado del juego ±0/+1;
  slot reproducido `*(bailarín)+0x43f0`: 1→1, 3→3, 6→7, 10→13, 15→21, 20→30,
  27→41, 34→49. Tabla de fallos 0x80054bc4 indexada por id de personaje BAG1
  (Heat 0, Frida 2, Kitty-N 7, Hiro 8, Gas-O 9): 7/7 aciertos. Fallo del compás
  7 en la demo = CPU sin entrada (s1=-1 en 0x800209a4), no rechazo del FINISH.
- Entrada simulada `INJECT_CMD=34` tras la petición 27: el juego esperaba 34,
  pasó la puerta (contador 33), reprodujo el slot 49 durante 238 fotogramas
  (8 tiempos) y mostró «FREEZE!!» (`trace4c`, `finish_sheet.png`).
- Validación independiente: capturas PPM revisadas (`clap_heat.png`,
  `cycles.png`, `finish_sheet.png`) y contraste con el desensamblado Capstone.
- Dictamen: **útil**. Sustituyó a Ghidra porque el proyecto Ghidra solo carga BAG2.
- Medición: ~3,5 min de emulación por cada 12 000 fotogramas; ahorro no medido.
- Límites: un solo FINISH (nivel 1) observado; resto de niveles por fórmula. El
  aplauso de «A» es compatible con las capturas, pero no es concluyente.
