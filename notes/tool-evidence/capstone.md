---
id: tool-evidence-capstone
title: "Capstone: evidencia de uso"
tags: ["tools", "evidence", "disassembly"]
summary: "Historial de ensayos Capstone; cada resultado conserva alcance y límites de validación."
related: ["notes/assets.md"]
created: "2026-11-06"
updated: "2026-11-06"
doc_kind: evidence
---

# Capstone: evidencia de uso

## 20261106-capstone-001 — referencias candidatas de escenario Strike
- Propósito: extracción mecánica complementaria a Ghidra MCP, no sustitución
  ni prueba de que bytes arbitrarios sean código ejecutado.
- Versión/comando: Capstone5.0.7 en `py -3.13`;
  `py -3.13 _work/strike_match_stage_refs.py`. MIPS32 little endian.
- Input: `assets/archive/system/005.dbi`,61687bytes, SHA256
  `bc5f3045084e4b3e19009910441627977863c8b5791b5cdb716a766e68b28fb2`;
  payload tras12bytes, baseJP documentada8008f890, no módulo cargado confirmado
  en Ghidra durante este ensayo. Ejecutable principalSLPM_862.19, payload2048,
  base de cabecera80010000, tamaño315392; hash en registro Ghidra009.
- Evidencia: `_work/strike-match-stage-refs.txt`. Primer recorrido produjo0
  candidatos al detenerse en datos inválidos; con `skipdata=True` produjo11
  lecturas candidatas `lw -0x6e00(...)`, principalmente consultas de stageID.
  `skipdata` puede interpretar datos como instrucciones; no valida flujo.
- Scans adicionales inline: JAL3318c en96d40/975d4/9de48 y326d4 en99018/99028;
  offsets de tipo+a0 en ejecutable; destinos JAL1f000..22410 y10000..12500.
  Ghidra MCP descartó candidatos concretos como inicialización, texto, cámara
  y entradas (Ghidra009). Ninguno identifica el descarte de estructuras.
- Dictamen: **irrelevante** para la condición buscada, extracción reproducible
  pero demasiado amplia. Tiempo/ahorro y retrabajo no medidos. Sin parches.
  Siguiente: usar flujo/callsite verificado antes de nuevas búsquedas por offsets.

## 20261106-capstone-002 — decodificar bytes MCP del guard de escenario
- Capstone5.0.7, `py -3.13`; mismo005.dbi/hash/base de001 para inventario JAL
  acotado22410..2b000 y2b000..36000. Destino30458 elegido para lectura MCP.
  Ghidra010 registra errores de decompilación y posterior lectura de memoria.
- Input principal:2048bytes de `_work/strike-ghidra-30458-read.log`,
  dirección80030458, comparados íntegramente conSLPM_862.19 JP/hash deGhidra010.
  Output `_work/strike-30458-asm.txt`; se contrastaron palabras30574/578/588/
  590/594/5d4/5d8 con el ejecutable. Sin modificar análisis ni runtime en este paso.
- Resultado: **útil**, separa guard de profundidad/GTE de comparaciones X/Y
  en función que consume visibilidad para dibujar escenario. No prueba causalidad
  visual. Tiempo/ahorro y retrabajo no medidos; A/B pendiente.

## 20261106-capstone-003 — código de render runtime desde volcado RAM

- Propósito: leer render/emisores ausentes del programa Ghidra (región runtime).
- Comando: `py -3.13 _work/disasm_ram.py <dump> <start> <size> <out>` (Capstone
  MIPS32 LE, skipdata) sobre `viewer-run/20261106T055110/bag2jp_ram_6000.bin` en
  `8008ef3c`, `8008e780`, `80027fc8`.
- Evidencia: `_work/strike-8008ef3c-disasm.txt`, `_work/strike-8008e780-disasm.txt`,
  `_work/strike-80027fc8-disasm.txt`.
- Validación: cadena coherente con el decompile Ghidra de `0x8002c404` (despacha a
  `8008ef3c`); índice OT = (sz0+sz1)>>3<<2 con base OT-0x180, leído a mano.
- Resultado: útil; establece orden de profundidad por polígono. Tiempo/ahorro no
  medidos. Específico del volcado: identidad del módulo no hasheada.

## 20261106-capstone-004 — candidato compartido Gas-O y regresión callbacks

- Propósito: regenerar escenario experimental197 con el perfil existente y
  verificar invariantes sin desplegar. Capstone5.0.7, WSL Ubuntu Python3.
- Comando: `wsl.exe -d Ubuntu --exec python3 /mnt/d/Dev/Recomp/BAG2JP/tools/bag1import/build_stage_package.py --root /mnt/d/Dev/Recomp/BAG2JP --profile gaso --output /mnt/d/Dev/Recomp/BAG2JP/_work/stage_import/gaso/resume-audit/gaso_197.dfs`.
  Tests: `wsl.exe -d Ubuntu --exec python3 -m unittest tools.test.test_stage_port`.
- Entradas: perfil `tools/bag1import/profiles/stages/gaso.json`, DBI USA de
  ST_GAS SHA256 `0d3a49731d5d44f62e108ce925aa37fafc044896a3e7ce5ab80f1efdc430a320`,
  ejecutable/chart JP y stock197 según perfil. Hashes fuente/región/miembros en
  `_work/gaso/stage-profile-audit.json`; tablas del ejecutable contrastadas por
  MCP (ghidra-019), no identidad de overlay cargado.
- Resultado:545948bytes, SHA256 `9cda85c90e63de117f8d20fffd2be35ab6600b836598a79845d268bf6885e188`,
  relocaciones JAL80/pairs343/data0, unknown vacío. Modelo `{1:32,3:1}`.
- Tests: baseline3 verdes; ensayo negativo inicial usó callback fuera de imagen
  y falló por struct.error (no prueba válida). Corregido a +4bytes en imagen,
  rojo por ValueError no lanzado; validación de tabla añadida →4verdes.
  Conservación de assets nativos/cola stock añadida →5verdes,0.378s,exit0.
- Dictamen: **útil** como generación y guard estructural, no demuestra destinos
  semánticos ni escenario aceptado. Sin runtime/build/deploy. Tiempo total,
  retrabajo y ahorro desconocidos. Siguiente: auditar mappings e integrar después
  del gate regional; conservar candidato previo de `_work/stage_import/gaso/candidate/`.

## 20261107-capstone-005 - mapeo BAG1 de dobles de baile
- Propósito: verificar en código BAG1 qué petición/animación es el doble (compás 7) de cada nivel; Ghidra MCP no aplicable (proyecto solo carga BAG2 SLPM_862.19, sin herramienta para cambiar de programa).
- Versión/comando: Capstone 5.0.7, `py -3.13 _work/gaso/bag1_table_users.py _work/bag1/scus.bin 0x80055830`, `_work/gaso/bag1_disasm.py` (base 0x80010000), `_work/gaso/scan_grid_tables.py`.
- Entradas: `_work/bag1/scus.bin` (ejecutable BAG1 USA), regiones 0x800243f4, 0x80030090, tablas 0x80055830/0x80055854.
- Observado: 0x800243f4 decodifica petición r>=29 a compás 7 nivel 35-r; tabla alt de 15 filas (anim, alt, prevA, prevB). No hay tabla literal de rejilla.
- Validación independiente: matriz de poses (`_work/gaso/double_entry_matrix.py`) en Gas-O, Heat y Strike apunta al mismo desplazamiento; prueba en juego doble Gas-O 20261107T002631063982Z.
- Dictamen: útil; encontró un error compartido de `anim_remap.py`.
- Medición: tiempo y ahorro desconocidos.
- Siguiente: revisión humana del baile; reconstruir Heat/Strike con la corrección si el propietario lo aprueba.
