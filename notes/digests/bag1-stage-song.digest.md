---
id: bag1-stage-song-digest
title: "Escenario/canción: ruta de referencia"
tags: ["digest", "stage"]
summary: "Heat/Strike: perfiles, receta stage/audio, requisito de eventos por puntaje y límites históricos; no relocador universal ni campaña aceptada."
related: ["notes/bag1-stage-song.md"]
created: "2026-11-02"
updated: "2026-11-06"
edited: "2026-11-06"
doc_kind: digest
source: "notes/bag1-stage-song.md"
source_sha256: "a14049afa7534e87fb21ecdc7894032d22c6ffe93ee44195e31bf8cdcbb8547a"
---

Leer primero «Receta reutilizable» de la [fuente](../bag1-stage-song.md).
Requisito obligatorio (2026-11-06): no basta importar geometría y texturas;
deben importarse las interacciones/eventos del escenario con el puntaje
(level/prev_level en BAG1 y adaptación en BAG2); reportado pendiente en Strike.
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
