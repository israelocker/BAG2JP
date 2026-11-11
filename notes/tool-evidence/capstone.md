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

## 20261111-capstone-009 — 2026-11-11 UTC — selector de impacto BAG2 JP

- Uso real: Capstone5.0.7 MIPS32LE; `dis_005_dispatch.py` en `_work/gaso/` con
  rangos8009cf00:8009d140,8009e000:8009e140 y después8009b400:8009b7a0,
  8009b2c0:8009b400. Las salidas iniciales compartían destino; conservar la salida
  consolidada no sobrescribible `hit-selector-verified.asm`, no depender de aquel
  archivo temporal para evidencia completa. No se perdió fuente de juego.
- Input `assets/archive/system/005.dbi`,61687bytes, SHA256
  bc5f3045084e4b3e19009910441627977863c8b5791b5cdb716a766e68b28fb2,
  payload tras12bytes y base JP8008f890. No usar base USA8008f6c0.
- Barridos previos `request_tables.py`, `hit_reaction_tables.py`,
  `hit_reaction_bag2.py`, `hit_table_refs.py`, `hit_table_refs2.py`,
  `bag2_controller_callers.py`, `bag2_dispatcher_ptr.py` no localizaron emisor en main:
  resultados negativos/no pertinentes, no ausencia global de llamadas. Font/ISO9660
  y patrón de argumentos UI descartados. `find_dispatcher_overlay.py` encontró
  JAL8002a090 en005 y008;008 no seguido. `find_request_writers.py` y
  `find_hit_table_005.py` delimitaron selector/tabla en005.
- Contraste independiente `py -3.13 _work/gaso/audit_hit_selector.py`: SHA completos,
  asserts de opcode/inmediato sin decoder y tabla36bytes idéntica al MCP main.
  Informe `full-fidelity-source-audit/hit-selector-contract.json`; consulta Ghidra
  complementaria documentada en ghidra056. No sustituye Ghidra ni verifica el overlay
  en RAM de una partida activa.
- Observado:8009b5ac lee tabla80051458[ID*2],8009b5b4 guarda petición; entrada9
  Bi-O=[202,1].8009d0c0 la despacha y consume.8009b2cc/b444 emiten123 en otras
  condiciones. Evitar cambiar global78 o confundir peticiones con slots.
- Dictamen: **útil** para delimitar esta ruta, no exhaustivo para reflejos, parejas
  o CAUGHT de rivales solo-BAG2. Auditoría consolidada0.012145s; exploración,
  preparación, retrabajo y ahorro no medidos. Ningún parche ni aceptación en juego.
  Siguiente: enlace CAUGHT por contexto; reutilizar listing/hashes si no cambian.

## 2026-11-11 — native-timing-contract: contraste de reloj/contadores y005
- Capstone5.0.7/Python3.13, nativeJP SLPS_012.32 payload+800/base80010000; BAG2 main raw80010000 y005 payload+12/base8008f890; hashes en `_work/gaso/native-timing-contract.json`. Scripts exactos: `py -3.13 _work/gaso/audit_native_timing.py`, `py -3.13 _work/gaso/scan_bag2_clock_candidates.py`. El primero protegido contra repetición; el segundo0.249s, diez clears candidatos en main/ninguno005: todos irrelevantes, NO ausencia del reloj.
- Lecturas inline `py -3.13 -c` con `Cs(CS_ARCH_MIPS,CS_MODE_LITTLE_ENDIAN|CS_MODE_MIPS32)` de005 generaron `_work/gaso/native-timing-audit/bag2-hit-duration-path.lst` (bfc0..c14c), `bag2-hit-table-uses.lst` (inmediato1458 y contexto), `bag2-duration-unit-defs.lst` (destino fp en99e90..d198), `bag2-pending-duration-stores.lst` (sw,+1c,excluye sp dentro de99e90..d198), `bag2-request202-sites.lst` (inmediato ca, dos sitios gráficos irrelevantes). En el primer scan de ca, PowerShell expandió `$zero` del texto Python entrecomillado; resultó búsqueda amplia de inmediato, NO dos escritores req202. Se detectó y no se usó como evidencia del routing; scripts siguientes usaron literal PowerShell sin expansión.
- Native flag10 setters11 candidatos, contexto1ef9c y dispatcher1ef34; reloj1f32c contrastados con nuevas decompilaciones Ghidra.005 c144/b5f0/b5b4 contrastados con Ghidra y palabras originales. Resultado Útil acotado al contrato estático; búsqueda general del equivalente por clears fue Irrelevante/Inconclusa. Tiempos inline/primer audit y manual desconocidos, ahorro no medido. No cambios al juego. Siguiente: alinear datos/fase originales, no convertir los grupos4 en segundos inventados.

## 2026-11-11 — sequence-residency: generadores de tabla
- Capstone5.0.7/Python3.13; nativeJP9676a28c… payload+800/base80010000;005bc5f3045… payload+12/base8008f890. Búsquedas inline acotadas de inmediato e750/-18b0 (native) y e2f0/-1d10 (main/005), salidas `_work/gaso/native-timing-audit/native-sequence-table-uses.lst` y `bag2-sequence-table-uses.lst`. El primer intento005 supuso una ruta _work/system incorrecta y falló StopIteration antes de generar evidencia; se corrigió a assets/archive/system/005.dbi leyendo el wrapper verificado. La búsqueda amplia de usos produjo ruido; no repetir.
- Native230f4..2312c contrasta acumulador/rounding de chart JP612/8204/320;005997ec contrastado con headless Ghidra. Audit `py -3.13 _work/gaso/audit_sequence_chart.py` verifica perfil/exe/payload/DBI y llama convertidor real; comparación aritmética persistida en sequence-phase-comparison.json,321 entradas/56 diferencias+1. No ejecución del juego ni prueba de temporizadores iguales.
- Resultado Útil acotado a fórmulas/datos/fase normal; no nuevas equivalencias funcmatch (no se usó para overlays). Tiempo inline/revisión manual desconocidos; ahorro no medido. Siguiente: conservar estos datos y no inventar duraciones fijas.
