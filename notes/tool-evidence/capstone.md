---
id: tool-evidence-capstone
title: "Capstone: evidencia de uso"
tags: ["tools", "evidence", "disassembly"]
summary: "Historial de ensayos Capstone; cada resultado conserva alcance y límites de validación."
related: ["notes/assets.md"]
created: "2026-11-06"
updated: "2026-11-14"
doc_kind: evidence
---

# Capstone: evidencia de uso

## 2026-11-13 — Contraste del hook HUD overlay005

- Propósito: contrastar registros y palabras del consumidor nativo del HUD con el
  análisis Ghidra, sin alterar el juego ni el proyecto.
- Entrada: `assets/archive/system/005.dbi`, SHA256
  `bc5f3045084e4b3e19009910441627977863c8b5791b5cdb716a766e68b28fb2`;
  overlay japonés, payload `0x8008f890` tras 12 bytes, función `0x80093de0`.
- Fallo: import en `D:/Dev/Tools/ghidra-mcp-python/python.exe` dio
  `ModuleNotFoundError: capstone`. No se instaló nada. Se usó el entorno registrado
  `wsl.exe -d Ubuntu --exec python3` con Capstone MIPS32 little-endian.
- Evidencia: `s1` sprite, `s2` registro de textura, `s3` descriptor y `s4=8005e6cc+lado`
  en `80093f6c`; guardas `3c0400ff`, `0c012649`, `a6220012` contrastadas además por
  lectura `struct` de las palabras. Harness carga ese overlay y verifica X/UV/W/H,
  preservando CPU, CLUT, Y y descriptores. Suite actual: 18 tests host verdes.
- Resultado: útil como contraste estático; no prueba la identidad del pack residente,
  ejecución del dispatcher ni exclusión UV. Versión puntual, duración y ahorro no
  medidos en este ensayo; no se atribuye una versión por memoria.
- Siguiente: conservar estas palabras y completar auditoría UV; no repetir desensamblado
  sin cambios de entradas ni evidencia contradictoria.

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

## 20261110-capstone-006 — 2026-11-10 UTC — emisores leídos por Ghidra MCP
- Tipo: uso real complementario, no sustitución de Ghidra. Capstone 5.0.7,
  WSL Ubuntu, MIPS32 LE. Comando desde raíz canónica:
  `wsl.exe -d Ubuntu --exec python3 _work/gaso/disassemble_sign_emitter.py <MCP-json>`.
- Entradas: lecturas del main BAG2 JP SLPM_862.19, SHA-256 completo
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`:
  `sign-emitter-ghidra.json` (80027FC8,512), `sign-quad-emitter-ghidra.json`
  (800281BC,1024), `sign-ft4-emitter-ghidra.json` (800285BC,1536) y
  `sign-ft4-emitter-tail-ghidra.json` (80028BD8,1536), bajo `_work/gaso/`.
  Hashes completos en `_work/gaso/sign-diagnostic-hashes.json` / ghidra-043.
- Fallo conservado: decoder sin `skipdata` se detuvo en NCLIP `0x4B400006`;
  `skipdata=True` conserva esas palabras como `.byte`, no como instrucciones
  supuestamente decodificadas. La primera salida fue demasiado extensa; las
  siguientes quedaron en `.asm` / `sign-ft4-emitter-tail-disasm.log`.
- Observado: FT4 `0x80028BDC..0x80028CB4`, registros nativos de 20 bytes,
  paquetes de 40 bytes (tag + 9 palabras GP0); orden de esquinas e índice OT
  basado en dos profundidades. El nombre del archivo `quad-emitter` no prueba
  que todo su contenido sea de quads; varios tramos son triángulos.
- Contraste: bytes MCP y comparación independiente con ejecutables originales
  en `sign-emitter-comparison.json`; correspondencias UV/paquetes y reproyección
  geométrica en `sign-camera-fit.json` (no prueba de frame exacto).
- Dictamen: **útil** para interpretar formatos/orden local; **inconcluso** para
  causa de A. No cambiar sesgos OT basándose solo en este resultado. Ejecución,
  preparación, retrabajo y ahorro no medidos; reutilizar las salidas mientras
  permanezcan iguales los inputs. Sin parche ni aceptación de juego.

## 20261110-capstone-007 — 2026-11-10 UTC — candidato Gas-O: geometría/DFS
- Tipo: uso real del conversor compartido, Capstone5.0.7 en WSL Ubuntu;
  no sustituye las lecturas Ghidra documentadas en ghidra-042/043.
- Comando: `wsl.exe -d Ubuntu --cd /mnt/d/Dev/Recomp/BAG2JP --exec python3
  tools/bag1import/build_stage_package.py --root /mnt/d/Dev/Recomp/BAG2JP
  --profile gaso --output /mnt/d/Dev/Recomp/BAG2JP/_work/stage_import/gaso/sign-subdivision/gaso_197.dfs`.
- Input: stage BAG1 `_work/bag1_disc_full/STAGEE/ST_GAS.DFS`, SHA256
  `5da6d4a2ca56713bd88d71edcd377f4c4a0cb5fe3286184b37e73f9559f3efa9`;
  perfil actual Gas-O con subdivisión guardada solo en nodo23/quad1 y30/quad5.
  DBI BAG1 base801E17B0 → BAG2 base801DAF10, escenario alternativo197.
- Salida: DFS514264 bytes, SHA256
  `a94237b824ab794a4c8842bf08658093405aa0a711adeb546bc298915dc7979f`,
  reporte adyacente `gaso_197.json`: unmapped_calls vacío, relocaciones
  JAL80/pares343/datos0, modelo32 nodos tipo1 +1tipo3, marcado experimental.
- Contraste independiente: diez tests host de stage_port/stage_geometry pasan,
  identidad de casos Heat/Strike, primitivas/transforms no elegidos preservados;
  repack posterior verifica60 variantes y capacidad byte a byte. No es
  aceptación visual ni prueba de todos los caminos de ejecución MIPS.
- Dictamen: **útil** para construir el candidato sin recrear assets. Sin fallo
  nuevo del decoder; las limitaciones de capstone-006 siguen vigentes. Tiempo
  del conversor y ahorro no medidos; build Windows posterior39.996s es otra fase,
   no una medida atribuible a Capstone. Siguiente: aceptación de intro en juego.

## 20261110-capstone-008 — 2026-11-10 UTC — tercer panel durante cámara tardía
- Tipo/comando: Capstone5.0.7, mismo build_stage_package de007, ahora output
  `_work/stage_import/gaso/sign-subdivision-v2/gaso_197.dfs`, raíz y perfil iguales.
  Input native ST_GAS.DFS SHA256
  `5da6d4a2ca56713bd88d71edcd377f4c4a0cb5fe3286184b37e73f9559f3efa9`;
  mismas bases DBI801E17B0→801DAF10 y región destino BAG2JP, sin nueva inferencia
  regional a partir del nombre de la carpeta fuente.
- Motivo: candidato007 compila/carga y termina canción, pero falla visualmente
  en cámara tardía. Nuevo diagnóstico de RAM identifica nodo26/quad1:1.428 píxeles
  interiores del cartel tapados por superficie situada detrás, reproyección
  máxima0.861px. No es un fallo demostrado del decoder/relocator.
- Cambio de perfil: añadir únicamente división2x2 guardada de esa primitiva;
  reutilizar el mismo motor y los otros dos ajustes. Sin nuevos parches MIPS.
- Salida:514396 bytes SHA256
  `0a99486052f49e8f817e2cae709219c6367bfcf5c55ef44226bdc68eb94bd302`,
  JAL80/pares343/datos0, unmapped_calls vacío, modelo32 tipo1+1 tipo3.
  Quince tests host pasan0.394s (antes12!=21 en nodo26), y repack verifica60
  variantes/capacidad independiente. Payload376287abd3ee2a13944deeafb0415da9b0f163a185dd3cad1540259596232f7e.
- Dictamen: **útil** para conversión reproducible; aceptación visual nueva
  pendiente. Tiempo Capstone/preparación/retrabajo/ahorro no medidos. Reutilizar
   análisis MIPS de006; no repetir decompilación sin bytes/código nuevos.

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

## 20261111-capstone-010 - 2026-11-11 UTC - FUN_8002a090 callers and controller seam
- Use: Capstone 5.0.7 MIPS32LE via `py -3.13` (not available with `-I`). Scripts in
  `_work/gaso/`: `dis_controller_callers.py 8002a000 8002b5bc` (main SHA 143b4bf8…),
  `dis_005_loop.py`, `callchain_005.py 80099e90 7`, `callee_closure.py 8002a090 8002d06c`
  (005.dbi SHA bc5f3045…, payload+12, base 8008f890).
- Result: 7 controller calls inside FUN_8002a090; 4 dispatcher calls in 005; consumer
  8009d0a8 = 86a60018 in FUN_80099e90 (reached by pointer); closure 189 functions, 18
  unresolved indirect jumps (no static proof of non-reentry). Cross-checked with
  Ghidra MCP read_memory (ghidra-064). No patch; time and savings not measured.

## 2026-11-11 — native-timing-contract: contraste de reloj/contadores y005
- Capstone5.0.7/Python3.13, nativeJP SLPS_012.32 payload+800/base80010000; BAG2 main raw80010000 y005 payload+12/base8008f890; hashes en `_work/gaso/native-timing-contract.json`. Scripts exactos: `py -3.13 _work/gaso/audit_native_timing.py`, `py -3.13 _work/gaso/scan_bag2_clock_candidates.py`. El primero protegido contra repetición; el segundo0.249s, diez clears candidatos en main/ninguno005: todos irrelevantes, NO ausencia del reloj.
- Lecturas inline `py -3.13 -c` con `Cs(CS_ARCH_MIPS,CS_MODE_LITTLE_ENDIAN|CS_MODE_MIPS32)` de005 generaron `_work/gaso/native-timing-audit/bag2-hit-duration-path.lst` (bfc0..c14c), `bag2-hit-table-uses.lst` (inmediato1458 y contexto), `bag2-duration-unit-defs.lst` (destino fp en99e90..d198), `bag2-pending-duration-stores.lst` (sw,+1c,excluye sp dentro de99e90..d198), `bag2-request202-sites.lst` (inmediato ca, dos sitios gráficos irrelevantes). En el primer scan de ca, PowerShell expandió `$zero` del texto Python entrecomillado; resultó búsqueda amplia de inmediato, NO dos escritores req202. Se detectó y no se usó como evidencia del routing; scripts siguientes usaron literal PowerShell sin expansión.
- Native flag10 setters11 candidatos, contexto1ef9c y dispatcher1ef34; reloj1f32c contrastados con nuevas decompilaciones Ghidra.005 c144/b5f0/b5b4 contrastados con Ghidra y palabras originales. Resultado Útil acotado al contrato estático; búsqueda general del equivalente por clears fue Irrelevante/Inconclusa. Tiempos inline/primer audit y manual desconocidos, ahorro no medido. No cambios al juego. Siguiente: alinear datos/fase originales, no convertir los grupos4 en segundos inventados.

## 2026-11-11 — sequence-residency: generadores de tabla
- Capstone5.0.7/Python3.13; nativeJP9676a28c… payload+800/base80010000;005bc5f3045… payload+12/base8008f890. Búsquedas inline acotadas de inmediato e750/-18b0 (native) y e2f0/-1d10 (main/005), salidas `_work/gaso/native-timing-audit/native-sequence-table-uses.lst` y `bag2-sequence-table-uses.lst`. El primer intento005 supuso una ruta _work/system incorrecta y falló StopIteration antes de generar evidencia; se corrigió a assets/archive/system/005.dbi leyendo el wrapper verificado. La búsqueda amplia de usos produjo ruido; no repetir.
- Native230f4..2312c contrasta acumulador/rounding de chart JP612/8204/320;005997ec contrastado con headless Ghidra. Audit `py -3.13 _work/gaso/audit_sequence_chart.py` verifica perfil/exe/payload/DBI y llama convertidor real; comparación aritmética persistida en sequence-phase-comparison.json,321 entradas/56 diferencias+1. No ejecución del juego ni prueba de temporizadores iguales.
- Resultado Útil acotado a fórmulas/datos/fase normal; no nuevas equivalencias funcmatch (no se usó para overlays). Tiempo inline/revisión manual desconocidos; ahorro no medido. Siguiente: conservar estos datos y no inventar duraciones fijas.

## 2026-11-12 - caught-retire-contract: slot-table users (Goldfish S2)
- Capstone 5.0.7/Python 3.13: `py -3.13 _work/gaso/scan_slot_users.py` over `_work/mainexe/slpm.bin` (sha256 `143b4bf866bf6e47…`, base 0x80010000); output `_work/gaso/slot_users.txt` (`a432c2ed…`): 130 loads/stores at displacements 0x820/824/828/82c/154c/1550 (count 23, raw 29, length 18, meta 17, current 37, previous 6).
- Displacement-only matching includes unrelated structs; grouped and checked in Ghidra (ghidra entry caught-retire-contract-20261112). Outcome useful: only the controller indexes tables by previous. Time under 1 s; manual review about 5 min. Next: rerun only if the executable changes.

## 2026-11-12 - caught-secondary-effect: candidatos y contraste acotado

- Capstone5.0.7/Python3.13: `py -3.13 _work/gaso/scan_hit_secondary.py`;
  main raw143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b
  base80010000,005bc5f3045084e4b3e19009910441627977863c8b5791b5cdb716a766e68b28fb2
  payload+12/base8008f890. Ocho candidatos en stars-secondary-scan.json, hashes
  verificados por el script. Búsqueda de displacement1720/1723/1724 y JAL19d70/
  1a8fc, NO xrefs exhaustivos: el código usa también base actor+15a0 y offset184.
- Decode inline19e20..19e90 ubicó prologue19e34 y lh184(s1) donde
  s1=actor+15a0; headless/MCP19e34 contrastados. 19888/196d4 resultó otro efecto,
  irrelevante al selector1; no se confunde con identificación de estrellas.
- Palabras overlay b5d0=90500001,b5d8=12000005,b5e4=0c00675c,
  b5e8=02002821,c144=aea2001c extraídas independientemente en reporte agregado.
  El delay-slot vuelve a cargar a1: enganchar solo antes del JAL y cambiar a1
  sería insuficiente. No se implementó hook ni se deshabilitó un efecto.
- Resultado útil acotado; identidad visual pendiente. Tiempo/manual/ahorro no
  medidos. Reutilizar extracción mientras hashes sigan iguales, no repetir scan.

## 2026-11-13 deslizamiento del rival atrapado (Gas-O CAUGHT)

- Propósito: localizar las escrituras de la base del bailarín `+0x14b8/+0x14c0`
  y de la raíz `+0x810`. Ghidra no tiene función definida en
  0x8002a090..0x8002b5bc.
- Comando: Python capstone MIPS32 LE sobre `_work/mainexe/slpm.bin` (base
  0x80010000). Escaneo de imm16 en lw/sw/addiu y prólogos; volcado en
  `_work/gaso/slide/dis-8002a090.txt`.
- Resultado: útil. 19 sw a 0x14b8, casi todos dentro de 0x8002a090. Interpola
  la base de la pareja en los estados 10/14 (`jal 0x800436e4`). Un falso
  positivo con offset de pila (0x80023c04) se comprobó y descartó en Ghidra.
- Validación independiente: Ghidra decompila `FUN_8002ccc8` y
  `FUN_8002c404`, que coinciden en los offsets. Tiempo y ahorro no medidos.

## 2026-11-13 escrituras de 0x810/0x818 en el ejecutable principal

- Propósito: localizar quién mueve la raíz del rival (`+0x810/+0x818`) entre
  los dos golpes del especial de Gas-O.
- Intento fallido: capstone lineal sin `skipdata` se detuvo tras 160
  instrucciones y devolvió 0 coincidencias; ese resultado no se usó.
- Comando válido: capstone MIPS32 LE con `skipdata=True` sobre
  `_work/mainexe/slpm.bin` (base 0x80010000), 78.848 instrucciones, filtros
  `0x810(`/`0x818(` y `0x800(`.
- Resultado: 55 referencias; solo dos stores de posición:
  `8002b320 sw $v0,0x810($s3)` (bloque de personaje 0x0a con interpolación de
  pareja) y `8002d934 sw $v0,0x810($s1)` (inicialización/spawn de actor). El
  resto son lecturas, incluido 8002ccc8. Ninguno explica el cambio observado
  de -2 en X al re-hit.
- Validación independiente: decompile de 8002a090 y 8002ccc8 en Ghidra
  concuerda (lecturas de 0x810, escritura solo en el bloque 0x0a). Los stores
  en el overlay de Heat (`heat_p1.bin`) y en `mods-src` tampoco aparecen.
- Límite: quedan escrituras por copia de bloque o por overlay no extraído; el
  autor real sigue sin identificar. Tiempo/ahorro desconocidos.

## 20261113-capstone-hud — consumidor de descriptor Gas-O

- Capstone5.0.7/Python3.13, Cs(MIPS, MIPS32|LITTLE_ENDIAN), rangos
  80093de0..80093e34 y80094378..800943cc. Entrada assets/archive/system/005.dbi
  JP SHA bc5f3045084e4b3e19009910441627977863c8b5791b5cdb716a766e68b28fb2;
  dirección de cada byte=8008f884+offsetDBI (incluye header12bytes).
- Primer sitio verifica prologue80093de0 y lui a1,800a/addiu a1,-1960,
  tabla8009e6a0. Segundo sitio contenía d6e6 en addiu desde lui8006, no800a:
  falso positivo de búsqueda de inmediatos descartado, no descriptor HUD.
- Ghidra headless80093de0 confirma la tabla y construcción del sprite.
  Independencia: dos descriptores stock idénticos y tests regionales del TIM.
- Útil para delimitar consumidor/descartar falso positivo; no mide CLUT ni
  resultado en pantalla. Tiempo/manual/ahorro desconocidos. No repetir rangos
  sin cambio de datos; evidencia contextual en notes/gaso-import.md, sección HUD.

## 20261113-capstone-fan — instrucciones nativas y dos rutas del nivel

- Capstone5.0.7 en Python3.13, MIPS32|LITTLE_ENDIAN. USA stage member0 SHA
  0d3a49731d5d44f62e108ce925aa37fafc044896a3e7ce5ab80f1efdc430a320,
  base801e17b0 tras header12. Rango801e23d0..801e25c4: mult speed/delta,
  bias15 si negativo, SRA4 y matrices. JP member0 SHA
  fdb6129c1aeba87c94116c6c27c1f2c94cfd6e55bed989b3604e8f5930222356:
  SRA a0,v1,4 en offsetCB8, sin atribuirle una VA USA.
- Main USA headerless `_work/bag1/scus.bin` SHA46cf25699eccd91057c61fe3c68ccd708e2c2c6ea348593e6c7b3ce3171b61c9:
  barrido de SW immediate74e8 delimitó writes34818/34824/348e0 y fallback1aa68;
  SW1578 llevó a1da9c, diferencia de contadores, más reset1dc48. Datos iniciales0
  NO prueban duración del frame. No se buscó equivalente main para un parche;
  por eso funcmatch no aplicaba al objetivo de overlay.
- Candidato v1, rango801dbaf0..801dbba8: LUI801e en ruta tomada pero8007 en
  fallthrough801dbb40, seguido de LB0108. Confirma hallazgo Goldfish independiente
  del SRA. Candidato v2 corrige ese LUI con guard y conserva división nativa.
- Útil. Validación independiente: Ghidra exports y144 casos por variante en
  intérprete PSXRecomp. No render/juego/RPM medidos. Tiempo/manual/ahorro no
  medidos; logs/candidatos `_work/gaso/stage-fan/`.

## 20261113-capstone-ap2 - causa de ataques en autoplay 2P

- Capstone 5.0.7 en WSL `python3`, MIPS32|LITTLE_ENDIAN. Overlay
  `assets/archive/system/005.dbi` SHA
  `bc5f3045084e4b3e19009910441627977863c8b5791b5cdb716a766e68b28fb2`,
  datos `bytes[12:]`, base 0x8008f890; rango 0x8009a980..0x8009ba20.
- Evidencia: los hooks AP2 (0x8009ADB4/0x8009ADC8) fuerzan el bloque CPU por
  compás 0x8009add0..0x8009b080. En 0x8009afd8 carga stock `0x1b($s3)`; con
  stock y RNG favorable, 0x8009b074/78 guarda comando 0x6e (ataque). El
  productor 0x8009b5b4 escribe 202 (CAUGHT Gas-O), coincidente con el log
  `gaso_caught: request 202` de `gaso-cam95-autoplay`.
- Validación independiente: sitio y palabras a confirmar en Ghidra al
  implementar el hook en 0x8009afe0; aún sin prueba en juego.
- Dictamen: útil (causa raíz localizada); falso el comentario de
  `bag2jp_mods.c` que afirma que el 2P autoplay nunca ataca.
- Medición: tiempo y ahorro no medidos.

## 20261113-capstone-cam - renderers BAG1/BAG2 y cola del bloque de ataque

- Capstone 5.0.7 en WSL `python3` (skipdata). Entradas: BAG2 main
  0x80027cf8..0x80029a00, overlay `003.dbi` (datos `bytes[12:]`, base
  0x8008f890), BAG1 `_work/bag1/scus.bin` 0x8002d400..0x80030000, y `005.dbi`
  0x8009aea0..0x8009b0a0. Listados en `_work/gaso/cam-ws/{bag2_render,bag1_render,
  bag2_003_draw,bag1_draw}.txt` y `_work/gaso/ap2_attack_block.txt`.
- Evidencia: transformación RTPT sin límite de profundidad; emisores con NCLIP y
  OT `((z1+z2)>>3)<<2` sobre `otbase-0x180`, sin comprobación de rango, iguales en
  ambos juegos. Cola de ataque: 0x8009b074/78 guarda 0x6e; los caminos sin stock,
  tirada fallida y `$v0=0` forzado convergen en 0x8009b084. `$s3/$s5` se fijan en
  0x8009ad24..0x8009ad40.
- Validación independiente: `test_ap2_no_attack.py` lee las palabras del sitio
  desde `005.dbi`; prueba de profundidad `depth_probe.py`. Ninguna prueba en juego.
- Dictamen: útil para descartar el OT como causa y fijar el sitio del hook.
- Medición: tiempo y ahorro no medidos.

## 20261114-capstone-drift
- Purpose: BAG1 equivalents of the BAG2 re-anchor/leash for the drift question.
- Command: WSL python3 capstone over `_work/bag1/scus.bin` (base 0x80010000): 0x80031560..0x8003161c,
  0x80031f60..0x800320c0, 0x8003161c..0x80031760, 0x80030860..0x80030a80; immediate scan for
  0x439c/0x43a4/0x36f4/0x36fc.
- Evidence: re-anchor 0x80031574 (caller 0x80031fdc); leash 0x8003161c is a spring
  (base -= (root-home)>>5 beyond radius); init 0x800320c0 radius 0x1e0; home +-0x310
  (+-0x210/+-0x100/+-0x590 special cases); position table x 0x600>>12 at 0x80030860.
- Validation: BAG2 side via Ghidra MCP (ghidra-psx-psyq.md 20261114-ghidra-drift); funcmatch found no
  byte match (different code).
- Outcome: useful. Time ~20 min.

## 20261114-capstone-leash-release-review — 2026-11-14 UTC — radio BAG1 y liberación nativa
- Tipo: uso real; Windows `py -3.13`, Capstone5.0.7; DBI JP005, payload tras12bytes, base0x8008F890.
- Entradas: `assets/archive/system/005.dbi` SHA-256 `bc5f3045084e4b3e19009910441627977863c8b5791b5cdb716a766e68b28fb2`; main raw `143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b`.
- Invocación inline Python: `capstone.Cs(CS_ARCH_MIPS, CS_MODE_MIPS32+CS_MODE_LITTLE_ENDIAN)`, `disasm(data[12:], 0x8008F890)`, búsqueda de `lui`7fff/8000 y stores de radio.
- Primer intento SIN skipdata: se detuvo tras43 instrucciones, cero candidatos; INCOMPLETO, no prueba ausencia. Salida `overlay-leash-scan.txt`.
- Corrección `md.skipdata=True`:15418 entradas decodificadas/24 candidatos; `overlay-leash-scan-skipdata.txt`; lectura acotada8009C9B0..8009CB8C en `overlay-release-context.txt` confirmó escritor INT_MAX y transición fase4->5.
- Otros resultados negativos no concluyentes: grep de constante completa en generado (inmediato partido), primera ruta errónea del helper histórico de Ghidra; no se ejecutó headless ni se cambió el proyecto.
- Contraste independiente: test original005 fija palabras en CAC4/C8, CAD4/D8, CB0C/10/1C/44; watchdog observó INT_MAX antes de re-clamp. Hashes de todas las salidas en `_work/goldfish/bag1-leash-verdict.json`.
- Dictamen: útil para localizar escritor de overlay; no prueba coreografía ni efectos en pareja. Escaneo fallido retenido.

## 20261114-capstone-dance-centering — 2026-11-14 UTC — tick_loop y ataque en 005.dbi tras caída de Ghidra MCP
- Tipo: uso real; Windows `py -3.13`, Capstone 5.0.7 (`CS_ARCH_MIPS, CS_MODE_MIPS32+CS_MODE_LITTLE_ENDIAN`), tras caída de servidor MCP Ghidra (`decompile_function_by_address`, `MCP server process exited with code 1`).
- Entradas: `assets/disc_files/SLPM_862.19` (base `0x80010000`, `0x800` header) y `assets/archive/system/005.dbi` (SHA-256 `bc5f3045084e4b3e19009910441627977863c8b5791b5cdb716a766e68b28fb2`, payload `bytes[12:]` en `0x8008F890`).
- Confirmado en `SLPM_862.19`: `0x8002BA00..0x8002BA4C` (`zoom_scale`: `0x8002BA38 sw v0, 0x38(s2)`), `0x8002D794..0x8002D828` (`0x8002D7A0 lhu v0, 4(s3)`, `0x8002D7C0 0x1000`, `0x8002D7F4 lbu v0, 3(s0)`, `0x8002D804 lbu v0, 0xc(s3)`, `0x8002D810 addiu a0, s3, 0x28`, `0x8002D814 addiu a1, s0, 0x810`, `0x8002D818 lw a2, 0x38(s3)`, `0x8002D820 addiu a3, s0, 0x14b8`, `0x8002D824 jal 0x8002c404`), y `0x8002D8CC..D4` (`0x80089200` `B1LEASH_STAGE_PTR`).
- Confirmado en `005.dbi`: `0x8009A548` (`sh v0, -0x1886(v1)` -> `0x8005E77A` P2 activo), `0x8009A560` (`sh v0, -0x18b8(v1)` -> `0x8005E748` P1 activo), `0x8009A5A0` (`addiu s3, v0, -0x7f8` -> `0x8005F808`).
- Validación independiente: palabras exactas fijadas en `tools/test/test_bag1_leash.py` (`20` tests host verdes); estado `(0,0)` en baile normal y no-cero en ataques comprobado en `20261113T190419608874Z-gaso-combined-ae-f2/bag2jp_watch.log`. Tiempo/ahorro no medidos. Siguiente: validación en juego autorizada con `BAG2JP.exe` `0665a9c3…`.
- Medición: ejecución/preparación/retrabajo/referencia no medidos; ahorro no medido.
- Siguiente: reutilizar bytes y fingerprints mientras005 no cambie; no repetir búsqueda por inercia.
