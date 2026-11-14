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

## 20261106-dumpsxiso-002 — extracción completa BAG1 USA para Gas-O

- Propósito: el extracto local `_work/bag1_disc` carecía de `PLAYER3E/P_GAS_*3`
  y `PLAYER4/P_GAS_*4` (traje B), aunque la tabla de modelos BAG1 (0x80059918)
  los referencia.
- Comando: `dumpsxiso.exe -x _work/bag1_disc_full -s _work/bag1_disc_full/layout.xml
  "D:/Games/Bust A Groove (USA)/ISO/Bust A Groove (USA).bin"` (v2.30 win64). Log
  `_work/bag1_disc_full-dumpsxiso.log`. Salida 0 en 0,78 s; carpeta nueva, imagen
  solo leída.
- Validación independiente: los 112 ficheros de `_work/bag1_disc` existen y son
  idénticos byte a byte en la nueva extracción; una búsqueda de nombres en el `.bin`
  confirma `P_GAS_A3/B3/A4/B4.DFS`. Tamaños A3 226432, B3 229132, A4/B4 330924
  (A4 == B4); A1 ≠ A3.
- Dictamen: **útil**; resolvió un hueco de inventario sin reconstruir el disco.
  Sectores XA raw no evaluados.
- Siguiente: usar `_work/bag1_disc_full` como fuente de Gas-O; no sustituir las
  rutas de Heat/Strike ya aceptadas.

## 20261106-dumpsxiso-003 — extracción completa BAG1 Japón (regla de dos regiones)

- Propósito: el propietario exige importar también desde el disco japonés, que no
  tiene la censura americana (personajes, canciones y escenarios).
- Comando: `dumpsxiso.exe -x _work/bag1jp_disc_full -s _work/bag1jp_disc_full/layout.xml
  "D:/Games/Bust A Groove (Japan)/Bust A Move - Dance & Rhythm Action (Japan).bin"`
  (v2.30 win64, `D:/Dev/Tools/ps1-community/mkpsxiso-2.30/mkpsxiso-2.30-win64`). Log
  `_work/bag1jp_disc_full-dumpsxiso.log`. Salida 0 en 0,48 s; carpeta nueva, imagen solo leída.
- Resultado: carpetas BIN1, DFS1, PLAYER1-4, STAGE, STR, XA (sin sufijo de idioma);
  DANCEXA1-4. Gas-O: P_GAS_A1/A3 225428, B1/B3 225476, A2/B2 330812, A4/B4 330924,
  ST_GAS 250932, STR/GAS_END.STR.
- Validación independiente: `_work/gaso/compare_regions.py` separa los miembros DFS con
  `rebuild_dfs_members.read_members` y compara contra la extracción USA; cada DFS
  se dividió sin error (`_work/gaso/region-comparison.json`).
- Dictamen: **útil**. Diferencias localizadas en los miembros 1/2/3/5 de los packs,
  el nodo 26 del modelo A2/B2 y el DBI del escenario. Falta confirmar visualmente qué
  representan.
- Siguiente: renderizar los TIM y el nodo 26 que difieren; verificar el canal XA de
  Chemical Love en ambas regiones.
