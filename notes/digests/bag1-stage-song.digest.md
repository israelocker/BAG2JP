---
id: bag1-stage-song-digest
title: "Escenario/canción: ruta de referencia"
tags: ["digest", "stage"]
summary: "Heat/Strike: porter por perfiles, receta stage/audio y evidencia histórica con límites; no relocador universal ni campaña aceptada."
related: ["notes/bag1-stage-song.md"]
created: "2026-11-02"
updated: "2026-11-06"
doc_kind: digest
source: "notes/bag1-stage-song.md"
source_sha256: "8ea4579dd1b2e234535d040ca1e2b2bc1f0e6646e0b41a293515edf09975e3f0"
---

Leer primero «Receta reutilizable» de la [fuente](../bag1-stage-song.md).
`build_stage_package.py --root <project> --profile strike --output <new.dfs>`
crea DFS+JSON, no despliega. Perfiles Heat/Strike tienen símbolos/callbacks y
paquetes distintos: no es un relocador universal. Modelo, atlas, cámara, chart y
SFX requieren inventario específico; el reporte fijo de banco stock es obsoleto
cuando native_sfx_bank0=true. Strike usa bank0 nativo y banks1..3 stock.
La fuente conserva runs de canción/selector/SFX y regresiones con restauración,
no una nueva aceptación en esta auditoría. JP start920 no USA955; duración lógica
129 s no duración WAV132,053333 s. FLAC44100 estéreo y ruta son por perfil.
Grid/fondo negro aceptados por propietario; escucha/fidelidad/campaña final no
se infieren de logs ni de Ending View. Historia anterior queda fechada debajo.
