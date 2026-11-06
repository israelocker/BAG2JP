---
id: tool-evidence-ghidra-psx-psyq
title: "Evidencias: Ghidra, PSX y PsyQ"
tags: ["tools", "evidence"]
summary: "Historial de Ghidra MCP y soporte PSX/PsyQ; no certifica identificación automática."
related: ["notes/assets.md", "AGENTS.md"]
created: "2026-11-06"
updated: "2026-11-06"
doc_kind: evidence
---

# Ghidra / PSX / PsyQ — historial

Aplicar [criterios y plantilla](../assets.md#clasificación-y-medición-obligatorias).
El loader y los datos PsyQ se anotan por separado en cada ensayo cuando se utilicen;
su presencia no demuestra que una firma se haya aplicado correctamente.

## 20261106-ghidra-001 — antecedente de conexión y lectura
- Tipo: uso MCP histórico; transcrito el 2026-11-06, no reejecutado.
- Versión: Ghidra 12.1.4, loader PSX y datos PsyQ existentes.
- Entradas: ejecutable principal BAG2 JP `SLPM_862.19`, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
- Observado: backend inicialmente cerrado; el agente abrió la instalación y
  proyecto existentes, luego `get_program_info` y decompilación de `0x80035d98`
  respondieron. Advertencia de instrucción inválida al final, no ocultada.
- Evidencia: `_work/process-audit/ghidra-status.json` conserva fallo y recuperación.
- Contraste: identificación/hash y lectura MCP; no prueba semántica de overlays.
- Dictamen: **útil / buenos resultados** para verificar conexión/leer el programa;
  fidelidad de decompilación y eficacia de firmas PsyQ no evaluadas aquí.
- Medición: tiempos/ahorro no medidos. Siguiente: reutilizar sesión, validar cada rango.

## 20261106-ghidra-002 — comprobación para este registro
- Tipo: uso MCP real, 2026-11-06 UTC; tarea: crear historiales de herramientas.
- Versión/entrada: misma instalación y SHA-256 anteriores; ejecutable principal
  BAG2 JP, no overlay. No se aplicaron firmas ni se modificó análisis.
- Consultas: `get_program_info()` seguido de
  `list_functions({filter: "InitHeap", offset: 0, limit: 5})`.
- Observado: formato PSX, lenguaje PSX little-endian 32 bits, 1324 funciones;
  un resultado `InitHeap` en `0x80049f44`, `has_more: false`.
- Evidencia: `_work/tool-evidence/ghidra-mcp.json`, SHA-256
  `67eb2333eb700a07ce090d6f87ed2f6647f166245931af9cc417a0ee9f5107ba`;
  hash del programa igual al
  antecedente. Contraste limitado al dato previo y respuesta actual de MCP.
- Dictamen: **útil / buenos resultados** para disponibilidad y consulta del símbolo,
  no validación independiente de la función ni benchmark de decompilación.
- Medición: ejecución/preparación/revisión/ahorro no medidos.
- Siguiente: mantener sesión; evaluar semántica y firmas solo en una tarea pertinente.
